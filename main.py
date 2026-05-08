import telebot
from telebot import types
import json, os, time
from datetime import datetime

# ========== الإعدادات - غير دول ==========
TOKEN = os.environ.get('TOKEN') # سيبه كده وحط التوكن في Railway Variables
OWNER_ID = 8085768728 # ايديك من @userinfobot
SECRET_GROUP_LINK = "https://t.me/+eDUHBBpm3fg4N2Jk" # رابط الجروب السري
REQUIRED_INVITES = 50 # عدد الدعوات المطلوب
MAIN_GROUP_ID = -1003969652936 #
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

# ========== تتبع الدعوات والترحيب ==========
@bot.chat_member_handler()
def track_invites(message: types.ChatMemberUpdated):
    if message.chat.id!= MAIN_GROUP_ID: return
    old, new = message.old_chat_member, message.new_chat_member

    # عضو جديد دخل
    if old.status in ['left', 'kicked'] and new.status == 'member':
        user_id = str(new.user.id)
        inviter_id = str(message.from_user.id)

        # منع الاحتيال
        if inviter_id == user_id or inviter_id in data["banned"]: return
        if new.user.is_bot: return

        data["stats"]["total_joins"] += 1

        if inviter_id not in data["users"]:
            data["users"][inviter_id] = {
                "count": 0, "name": message.from_user.first_name,
                "got_link": False, "invited": [], "join_date": str(datetime.now())
            }

        # لو العضو ده متسجل قبل كده عند نفس الشخص متتحسبش
        if user_id in data["users"][inviter_id]["invited"]:
            return

        data["users"][inviter_id]["invited"].append(user_id)
        data["users"][inviter_id]["count"] = len(data["users"][inviter_id]["invited"])
        save_data(data)

        count = data["users"][inviter_id]["count"]
        name = message.from_user.first_name
        remaining = max(0, REQUIRED_INVITES - count)

        # لو وصل للعدد المطلوب
        if count >= REQUIRED_INVITES and not data["users"][inviter_id]["got_link"]:
            data["users"][inviter_id]["got_link"] = True
            save_data(data)

            text = f"✅ «الطالب™» {name} «اضاف «{count}»\n🔥√\n\n√ وتم تسجيلة في الجروب السري 👨‍💻\n\n👇 انضم هنـا ليتم قبولك فالجروب السري ➡️\n\n{SECRET_GROUP_LINK}\n\n📚 لو عيز تتسجل انتا كمان ضيفه 40 هـنـا\n\n√ ليتم قبولك في الجروب السري ➡️"

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("اضغط هنا", url=SECRET_GROUP_LINK))

            bot.send_message(message.chat.id, text, reply_markup=markup)

            try:
                bot.send_message(inviter_id, f"🎊 مبروك يا {name}\nوصلت {count} دعوة\n\nادخل الجروب السري من هنا:\n{SECRET_GROUP_LINK}")
            except: pass

        # لو لسه موصلش
        else:
            text = f"✅ «الطالب™» {name} «اضاف «{count}»\n🔥\n\n⏳ فاضلك {remaining} دعوة وتدخل الجروب السري\n\n📚 لو عيز تتسجل انتا كمان ضيفه {REQUIRED_INVITES} هـنـا"
            bot.send_message(message.chat.id, text)

    # لو عضو خرج نقص من اللي ضافه - مكافحة الغش
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
    markup.add(
        types.InlineKeyboardButton("🎁 جوايزي", callback_data="rewards"),
        types.InlineKeyboardButton("📜 القوانين", callback_data="rules")
    )
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

    elif call.data == "rules":
        text = f"📜 قوانين الجروب\n\n1. ضيف {REQUIRED_INVITES} عضو حقيقي\n2. ممنوع الحسابات الوهمية\n3. لو العضو خرج هتنقص دعوة\n4. ممنوع سبام الدعوات\n\nالتزم بالقوانين عشان متاخدش بان 🚫"
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup)

    elif call.data == "rewards":
        count = data["users"].get(user_id, {}).get("count", 0)
        text = f"🎁 جوايزك\n\n"
        for req, rank in RANKS.items():
            status = "✅" if count >= req else "❌"
            text += f"{status} {req} دعوة = {rank}\n"
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup)

    elif call.data == "admin_panel":
        if call.from_user.id!= OWNER_ID:
            return bot.answer_callback_query(call.id, "❌ للمشرف فقط", show_alert=True)

        total_users = len(data["users"])
        total_invites = sum(u["count"] for u in data["users"].values())
        active = sum(1 for u in data["users"].values() if u["count"] >= REQUIRED_INVITES)

        text = f"👑 لوحة التحكم المتطورة\n\n" \
               f"👥 إجمالي الأعضاء: {total_users}\n" \
               f"📨 إجمالي الدعوات: {total_invites}\n" \
               f"✅ وصلوا للهدف: {active}\n" \
               f"📊 دخل الجروب: {data['stats']['total_joins']}\n\n" \
               f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        markup = types.InlineKeyboardMarkup(row_width=2)
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

@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.id!= OWNER_ID: return
    try:
        user_id = msg.text.split()[1]
        data["banned"].append(user_id)
        save_data(data)
        bot.reply_to(msg, f"🚫 تم حظر {user_id}")
    except:
        bot.reply_to(msg, "❌ استخدم: /ban user_id")

@bot.message_handler(commands=['id'])
def get_id(msg):
    bot.reply_to(msg, f"🆔 ايدي الجروب ده: `{msg.chat.id}`\nايديك انت: `{msg.from_user.id}`", parse_mode="Markdown")

if __name__ == '__main__':
    print("✅ Bot Pro is running...")
    bot.remove_webhook()
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
    # ده السطر اللي بيخلي البوت يستقبل دخول الأعضاء
    bot.infinity_polling(allowed_updates=['chat_member', 'message', 'callback_query'], skip_pending=True)
