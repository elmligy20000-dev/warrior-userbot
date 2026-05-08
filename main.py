import telebot
from telebot import types
import json, os, time
from datetime import datetime

# ========== الإعدادات - غير دول ==========
TOKEN = os.environ.get('TOKEN')
OWNER_ID = 8085768728 # ايديك من @userinfobot
SECRET_GROUP_LINK = "https://t.me/+eDUHBBpm3fg4N2Jk" # رابط الجروب السري
PUBLIC_GROUP_LINK = "https://t.me/esuuugg" # رابط الجروب العام اللي بتجمع فيه الدعوات
REQUIRED_INVITES = 50 # عدد الدعوات المطلوب
MAIN_GROUP_ID = -1003969652936 # ايدي الجروب العام من @RawDataBot
# ======================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "invites_data.json"

RANKS = {0: "مبتدئ 🐣", 10: "نشيط ⚡", 25: "محترف 🔥", 50: "أسطورة 👑", 100: "امبراطور 💎"}

def get_rank(count):
    rank = "مبتدئ 🐣"
    for req, r in RANKS.items():
        if count >= req: rank = r
    return rank

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "banned": [], "stats": {"total_joins": 0}}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = load_data()

# ========== دالة الترحيب الموحدة ==========
def send_welcome(inviter_id, inviter_name, new_user_id):
    if inviter_id == new_user_id or inviter_id in data["banned"]: return
    if bot.get_chat_member(MAIN_GROUP_ID, new_user_id).user.is_bot: return

    data["stats"]["total_joins"] += 1

    if inviter_id not in data["users"]:
        data["users"][inviter_id] = {
            "count": 0, "name": inviter_name,
            "got_link": False, "invited": [], "join_date": str(datetime.now())
        }

    if new_user_id in data["users"][inviter_id]["invited"]:
        return

    data["users"][inviter_id]["invited"].append(new_user_id)
    data["users"][inviter_id]["count"] = len(data["users"][inviter_id]["invited"])
    save_data(data)

    count = data["users"][inviter_id]["count"]
    remaining = max(0, REQUIRED_INVITES - count)

    # لو وصل للعدد المطلوب
    if count >= REQUIRED_INVITES and not data["users"][inviter_id]["got_link"]:
        data["users"][inviter_id]["got_link"] = True
        save_data(data)

        text = f"✅ «الطالب™» {inviter_name} «اضاف «{count}»\n🔥√\n\n√ وتم تسجيلة في الجروب السري 👨‍💻\n\n👇 انضم هنـا ليتم قبولك فالجروب السري ➡️\n\n{SECRET_GROUP_LINK}\n\n📚 لو عيز تتسجل انتا كمان ضيفه {REQUIRED_INVITES} هـنـا\n\n√ ليتم قبولك في الجروب السري ➡️"

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("اضغط هنا للدخول للجروب السري", url=SECRET_GROUP_LINK))
        markup.add(types.InlineKeyboardButton(f"ضيف {REQUIRED_INVITES} عشان تتسجل", url=PUBLIC_GROUP_LINK))

        bot.send_message(MAIN_GROUP_ID, text, reply_markup=markup)

        try:
            bot.send_message(inviter_id, f"🎊 مبروك يا {inviter_name}\nوصلت {count} دعوة\n\nادخل الجروب السري من هنا:\n{SECRET_GROUP_LINK}")
        except: pass

    # لو لسه موصلش
    else:
        text = f"✅ «الطالب™» {inviter_name} «اضاف «{count}»\n🔥\n\n⏳ فاضلك {remaining} دعوة وتدخل الجروب السري\n\n📚 لو عيز تتسجل انتا كمان ضيفه {REQUIRED_INVITES} هـنـا"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"ضيف {REQUIRED_INVITES} عشان تتسجل هنا", url=PUBLIC_GROUP_LINK))

        bot.send_message(MAIN_GROUP_ID, text, reply_markup=markup)

# ========== 1. لو العضو دخل بلينك دعوة ==========
@bot.chat_member_handler()
def track_invites_chat_member(message: types.ChatMemberUpdated):
    if message.chat.id!= MAIN_GROUP_ID: return
    old, new = message.old_chat_member, message.new_chat_member

    # عضو جديد دخل
    if old.status in ['left', 'kicked'] and new.status == 'member':
        inviter_id = str(message.from_user.id)
        new_user_id = str(new.user.id)
        send_welcome(inviter_id, message.from_user.first_name, new_user_id)

    # لو عضو خرج نقص من اللي ضافه
    elif old.status == 'member' and new.status in ['left', 'kicked']:
        user_id = str(new.user.id)
        for inviter_id, info in data["users"].items():
            if user_id in info["invited"]:
                info["invited"].remove(user_id)
                info["count"] = len(info["invited"])
                if info["count"] < REQUIRED_INVITES:
                    info["got_link"] = False
                save_data(data)
                break

# ========== 2. لو حد ضاف عضو يدوي ==========
@bot.message_handler(content_types=['new_chat_members'])
def track_invites_new_member(message):
    if message.chat.id!= MAIN_GROUP_ID: return
    inviter_id = str(message.from_user.id)
    inviter_name = message.from_user.first_name

    for new_user in message.new_chat_members:
        if new_user.id == bot.get_me().id: continue # لو البوت نفسه
        send_welcome(inviter_id, inviter_name, str(new_user.id))

# ========== أوامر البوت ==========
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.from_user.id)
    user_data = data["users"].get(user_id, {"count": 0})
    count = user_data["count"]
    rank = get_rank(count)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"📊 دعواتي: {count}", callback_data="my_stats"),
        types.InlineKeyboardButton("🏆 التوب 10", callback_data="top10")
    )
    markup.add(types.InlineKeyboardButton(f"📥 ضيف {REQUIRED_INVITES} واتسجل", url=PUBLIC_GROUP_LINK))
    markup.add(types.InlineKeyboardButton("📞 تواصل مع الدعم", url=f"tg://user?id={OWNER_ID}"))

    if msg.from_user.id == OWNER_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel"))

    text = f"مرحباً {msg.from_user.first_name} 👋\n\n" \
           f"🎯 المطلوب: {REQUIRED_INVITES} دعوة\n" \
           f"📈 دعواتك: {count}\n" \
           f"🏅 رانك: {rank}\n" \
           f"⏳ المتبقي: {max(0, REQUIRED_INVITES - count)}\n\n" \
           f"ضيف ناس للجروب واستلم الجروب السري تلقائي ⚡"

    bot.send_message(msg.chat.id, text, reply_markup=markup)

# ========== الأزرار ==========
@bot.callback_query_handler(func=lambda c: True)
def handle_buttons(call):
    user_id = str(call.from_user.id)

    if call.data == "my_stats":
        user_data = data["users"].get(user_id, {"count": 0, "invited": []})
        count = user_data["count"]
        sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["count"], reverse=True)
        position = next((i+1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), "غير مصنف")

        text = f"📊 إحصائياتك\n\n" \
               f"👤 الاسم: {call.from_user.first_name}\n" \
               f"📥 الدعوات: {count}\n" \
               f"🏅 الرانك: {get_rank(count)}\n" \
               f"🥇 ترتيبك: {position}\n" \
               f"⏳ المتبقي للجروب السري: {max(0, REQUIRED_INVITES - count)}"
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup)

    elif call.data == "top10":
        sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["count"], reverse=True)[:10]
        text = "🏆 توب 10 أعضاء\n\n"
        if not sorted_users:
            text += "مفيش دعوات لسه 😢"
        else:
            for i, (uid, info) in enumerate(sorted_users, 1):
                text += f"{i}. {info['name']} - {info['count']} دعوة {get_rank(info['count'])}\n"
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup)

    elif call.data == "admin_panel":
        if call.from_user.id!= OWNER_ID:
            return bot.answer_callback_query(call.id, "❌ للمشرف فقط", show_alert=True)

        total_users = len(data["users"])
        total_invites = sum(u["count"] for u in data["users"].values())
        active = sum(1 for u in data["users"].values() if u["count"] >= REQUIRED_INVITES)

        text = f"👑 لوحة التحكم\n\n" \
               f"👥 إجمالي الأعضاء: {total_users}\n" \
               f"📨 إجمالي الدعوات: {total_invites}\n" \
               f"✅ وصلوا للهدف: {active}\n" \
               f"📊 دخل الجروب: {data['stats']['total_joins']}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_start"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "back_start":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)

# ========== أوامر الأدمن ==========
@bot.message_handler(commands=['add'])
def add_invites(msg):
    if msg.from_user.id!= OWNER_ID: return
    try:
        _, user_id, amount = msg.text.split()
        if user_id not in data["users"]:
            data["users"][user_id] = {"count": 0, "name": "Unknown", "got_link": False, "invited": []}
        data["users"][user_id]["count"] += int(amount)
        save_data(data)
        bot.reply_to(msg, f"✅ تم إضافة {amount} دعوة للعضو {user_id}")
    except:
        bot.reply_to(msg, "❌ استخدم: /add user_id 10")

@bot.message_handler(commands=['id'])
def get_id(msg):
    bot.reply_to(msg, f"🆔 ايدي الجروب: `{msg.chat.id}`\nايديك: `{msg.from_user.id}`", parse_mode="Markdown")

if __name__ == '__main__':
    print("✅ Bot Pro is running...")
    bot.remove_webhook()
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
    bot.infinity_polling(allowed_updates=['chat_member', 'message', 'callback_query'], skip_pending=True)
