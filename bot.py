import telebot
import requests
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
ADMIN_ID = 932862531 # ايديك انت

API_KEYS = [] # المفاتيح هتضاف من البوت
current_key_index = 0
chat_history = {}
waiting_for_key = {}

bot = telebot.TeleBot(TOKEN)

def get_api_key():
    global current_key_index
    if not API_KEYS:
        return None
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key

def main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🗑️ مسح المحادثة", callback_data="clear_chat"))
    markup.add(InlineKeyboardButton("🆔 ايديي", callback_data="show_id"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("⚙️ لوحة المبرمج", callback_data="admin_panel"))
    return markup

def admin_panel_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 حالة البوت", callback_data="bot_status"),
        InlineKeyboardButton("🔑 ادارة المفاتيح", callback_data="keys_menu"),
        InlineKeyboardButton("👥 المستخدمين", callback_data="users_count"),
        InlineKeyboardButton("🔙 رجوع", callback_data="back_main")
    )
    return markup

def keys_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ اضافة مفتاح", callback_data="add_key_btn"),
        InlineKeyboardButton("🗑️ حذف مفتاح", callback_data="del_key_btn"),
        InlineKeyboardButton("📋 عرض المفاتيح", callback_data="show_keys"),
        InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")
    )
    return markup

def ask_gemini(user_id, prompt):
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append({"role": "user", "parts": [{"text": prompt}]})
    contents = chat_history[user_id][-10:]

    api_key = get_api_key()
    if not api_key:
        return "❌ مفيش مفاتيح Gemini مضافة!\n\nالادمن يدوس: ⚙️ لوحة المبرمج → 🔑 ادارة المفاتيح → ➕ اضافة مفتاح\nهات المفتاح المجاني من: https://aistudio.google.com/app/apikey"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": contents, "generationConfig": {"maxOutputTokens": 1200}}

    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            reply = res.json()['candidates'][0]['content']['parts'][0]['text']
            chat_history[user_id].append({"role": "model", "parts": [{"text": reply}]})
            return reply
        else:
            err = res.json().get('error',{}).get('message','خطأ غير معروف')
            return f"❌ خطأ API: {res.status_code}\n{err}"
    except Exception as e:
        return f"❌ خطأ اتصال: {e}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 اهلاً بيك في بوت erroe الذكاء المتطور\nابعت سؤالك او استخدم الازرار:", reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.from_user.id

    # لو الادمن بيبعت مفتاح
    if user_id in waiting_for_key and waiting_for_key[user_id]:
        new_key = message.text.strip()
        if new_key.startswith("AIza"):
            if new_key not in API_KEYS:
                API_KEYS.append(new_key)
                bot.send_message(user_id, f"✅ تم اضافة مفتاح Gemini بنجاح!\nالاجمالي: {len(API_KEYS)} مفتاح", reply_markup=keys_menu())
            else:
                bot.send_message(user_id, "⚠️ المفتاح موجود اصلا", reply_markup=keys_menu())
        else:
            bot.send_message(user_id, "❌ مفتاح Gemini لازم يبدأ بـ AIza", reply_markup=keys_menu())
        waiting_for_key[user_id] = False
        return

    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_gemini(user_id, message.text)
    bot.reply_to(message, reply, reply_markup=main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    msg_id = call.message_id

    bot.answer_callback_query(call.id) # مهم عشان الايرور يختفي

    if call.data == "show_id":
        bot.send_message(user_id, f"🆔 ايديك: `{user_id}`\n🆔 ايدي الادمن: `{ADMIN_ID}`\nانت الادمن: {user_id == ADMIN_ID}", parse_mode="Markdown")

    elif call.data == "back_main":
        bot.edit_message_text("القائمة الرئيسية:", user_id, msg_id, reply_markup=main_menu(user_id))

    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        bot.edit_message_text("⚙️ لوحة المبرمج Gemini:", user_id, msg_id, reply_markup=admin_panel_menu())

    elif call.data == "keys_menu" and user_id == ADMIN_ID:
        bot.edit_message_text("🔑 ادارة المفاتيح:", user_id, msg_id, reply_markup=keys_menu())

    elif call.data == "bot_status" and user_id == ADMIN_ID:
        key_status = "❌ مفيش مفاتيح" if not API_KEYS else f"✅ {len(API_KEYS)} مفتاح شغال"
        status = f"""📊 **حالة البوت**

🔑 المفاتيح: {key_status}
👥 المستخدمين: {len(chat_history)}
💾 الرسائل المخزنة: {sum(len(v) for v in chat_history.values())}
🟢 الحالة: اونلاين"""
        bot.edit_message_text(status, user_id, msg_id, parse_mode="Markdown", reply_markup=admin_panel_menu())

    elif call.data == "users_count" and user_id == ADMIN_ID:
        bot.edit_message_text(f"👥 عدد المستخدمين: {len(chat_history)}", user_id, msg_id, reply_markup=admin_panel_menu())

    elif call.data == "show_keys" and user_id == ADMIN_ID:
        if not API_KEYS:
            text = "مفيش مفاتيح مضافة!\nدوس ➕ اضافة مفتاح وضيف مفتاح Gemini"
        else:
            text = "📋 **مفاتيح Gemini:**\n" + "\n".join([f"{i+1}. `{k[:25]}...`" for i,k in enumerate(API_KEYS)])
        bot.edit_message_text(text, user_id, msg_id, parse_mode="Markdown", reply_markup=keys_menu())

    elif call.data == "add_key_btn" and user_id == ADMIN_ID:
        waiting_for_key[user_id] = True
        bot.edit_message_text("➕ ابعت مفتاح Gemini دلوقتي:\nلازم يبدأ بـ AIza\nهاته من: https://aistudio.google.com/app/apikey", user_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("❌ الغاء", callback_data="keys_menu")))

    elif call.data == "del_key_btn" and user_id == ADMIN_ID:
        if not API_KEYS:
            bot.send_message(user_id, "مفيش مفاتيح للحذف")
            return
        markup = InlineKeyboardMarkup(row_width=3)
        buttons = [InlineKeyboardButton(f"{i+1}", callback_data=f"del_{i}") for i in range(len(API_KEYS))]
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="keys_menu"))
        bot.edit_message_text("🗑️ اختار رقم المفتاح للحذف:", user_id, msg_id, reply_markup=markup)

    elif call.data.startswith("del_") and user_id == ADMIN_ID:
        num = int(call.data.split("_")[1])
        if 0 <= num < len(API_KEYS):
            API_KEYS.pop(num)
            bot.send_message(user_id, f"تم حذف المفتاح. باقي: {len(API_KEYS)}", reply_markup=keys_menu())

    elif call.data == "clear_chat":
        if user_id in chat_history:
            chat_history[user_id] = []
        bot.send_message(user_id, "✅ تم مسح المحادثة 👌", reply_markup=main_menu(user_id))

print(f"البوت شغال - ADMIN_ID = {ADMIN_ID}")
bot.infinity_polling()
