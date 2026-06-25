import telebot
import requests
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
ADMIN_ID = 932862531 

API_KEYS = [
    "sk-fa39f1423fe44b488da7cd04fa30f04f",
    "sk-67f0479e08694544ac766dc7eb999cf1"
]
current_key_index = 0
chat_history = {}
waiting_for_key = {} # عشان نعرف الادمن بيكتب مفتاح ولا لا

def get_api_key():
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key

bot = telebot.TeleBot(TOKEN)

def main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🗑️ مسح المحادثة", callback_data="clear_chat"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("⚙️ لوحة المبرمج", callback_data="admin_panel"))
    return markup

def admin_panel_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 حالة البوت", callback_data="bot_status"),
        InlineKeyboardButton("🔑 ادارة المفاتيح", callback_data="keys_menu"),
        InlineKeyboardButton("👥 عدد المستخدمين", callback_data="users_count"),
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

def ask_deepseek(user_id, prompt):
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append({"role": "user", "content": prompt})
    messages = chat_history[user_id][-10:]

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {get_api_key()}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": messages, "max_tokens": 1200, "temperature": 0.7}

    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            reply = res.json()['choices'][0]['message']['content']
            chat_history[user_id].append({"role": "assistant", "content": reply})
            return reply
        else:
            return f"❌ خطأ API: {res.status_code}"
    except Exception as e:
        return f"❌ خطأ اتصال: {e}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 اهلاً بيك في بوت Error ذكاء اصطناعي متطور\nابعت سؤالك او استخدم الازرار:", reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.from_user.id

    # لو الادمن بيضيف مفتاح
    if user_id in waiting_for_key and waiting_for_key[user_id]:
        new_key = message.text.strip()
        if new_key.startswith("sk-"):
            if new_key not in API_KEYS:
                API_KEYS.append(new_key)
                bot.send_message(user_id, f"✅ تم اضافة المفتاح بنجاح\nالاجمالي: {len(API_KEYS)} مفاتيح", reply_markup=keys_menu())
            else:
                bot.send_message(user_id, "⚠️ المفتاح موجود اصلا", reply_markup=keys_menu())
        else:
            bot.send_message(user_id, "❌ المفتاح لازم يبدأ بـ sk-", reply_markup=keys_menu())
        waiting_for_key[user_id] = False
        return

    if user_id == ADMIN_ID and message.text.startswith('/'):
        return

    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_deepseek(user_id, message.text)
    bot.reply_to(message, reply, reply_markup=main_menu(user_id))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    msg_id = call.message_id

    if call.data == "back_main":
        bot.edit_message_text("القائمة الرئيسية:", user_id, msg_id, reply_markup=main_menu(user_id))

    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        bot.edit_message_text("⚙️ لوحة المبرمج المتطورة:", user_id, msg_id, reply_markup=admin_panel_menu())

    elif call.data == "keys_menu" and user_id == ADMIN_ID:
        bot.edit_message_text("🔑 ادارة المفاتيح:", user_id, msg_id, reply_markup=keys_menu())

    elif call.data == "bot_status" and user_id == ADMIN_ID:
        status = f"""📊 **حالة البوت المتطور**

🔑 المفاتيح: {len(API_KEYS)} شغال
👥 المستخدمين: {len(chat_history)}
🔄 المفتاح الحالي: {API_KEYS[current_key_index][:15]}...
💾 الذاكرة: {sum(len(v) for v in chat_history.values())} رسالة
🟢 الحالة: اونلاين"""
        bot.edit_message_text(status, user_id, msg_id, parse_mode="Markdown", reply_markup=admin_panel_menu())

    elif call.data == "users_count" and user_id == ADMIN_ID:
        bot.edit_message_text(f"👥 عدد المستخدمين النشطين: {len(chat_history)}", user_id, msg_id, reply_markup=admin_panel_menu())

    elif call.data == "show_keys" and user_id == ADMIN_ID:
        if not API_KEYS:
            text = "مفيش مفاتيح!"
        else:
            text = "📋 **المفاتيح الحالية:**\n" + "\n".join([f"{i+1}. `{k[:20]}...`" for i,k in enumerate(API_KEYS)])
        bot.edit_message_text(text, user_id, msg_id, parse_mode="Markdown", reply_markup=keys_menu())

    elif call.data == "add_key_btn" and user_id == ADMIN_ID:
        waiting_for_key[user_id] = True
        bot.edit_message_text("➕ ابعت المفتاح الجديد دلوقتي:\nلازم يبدأ بـ sk-", user_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("❌ الغاء", callback_data="keys_menu")))

    elif call.data == "del_key_btn" and user_id == ADMIN_ID:
        markup = InlineKeyboardMarkup(row_width=3)
        buttons = [InlineKeyboardButton(f"{i+1}", callback_data=f"del_{i}") for i in range(len(API_KEYS))]
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="keys_menu"))
        bot.edit_message_text("🗑️ اختار رقم المفتاح للحذف:", user_id, msg_id, reply_markup=markup)

    elif call.data.startswith("del_") and user_id == ADMIN_ID:
        num = int(call.data.split("_")[1])
        if 0 <= num < len(API_KEYS):
            API_KEYS.pop(num)
            bot.answer_callback_query(call.id, "تم الحذف ✅")
            bot.edit_message_text(f"تم حذف المفتاح. باقي: {len(API_KEYS)}", user_id, msg_id, reply_markup=keys_menu())

    elif call.data == "clear_chat":
        if user_id in chat_history:
            chat_history[user_id] = []
        bot.answer_callback_query(call.id, "✅ تم مسح الذاكرة")
        bot.send_message(user_id, "تم مسح المحادثة بنجاح 👌", reply_markup=main_menu(user_id))

print("البوت المتطور شغال 24/7...")
bot.infinity_polling()
