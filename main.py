import telebot
from telebot import types
import json, os, time, threading
from datetime import datetime, timedelta

# ========== الإعدادات - غير دول ==========
TOKEN = os.environ.get('TOKEN') # حطه في Variables في Railway
OWNER_ID = 6409691924 # ايديك من @userinfobot
SECRET_GROUP_LINK = "https://t.me/+VrkIJm9y324zZWM0" # رابط الجروب السري
PUBLIC_GROUP_USERNAME = "O_YGOWW" # يوزر الجروب العام بدون @
REQUIRED_INVITES = 50 # عدد الدعوات المطلوب
MAIN_GROUP_ID = -1003548020892 # ايدي الجروب العام من @RawDataBot
# ======================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "invites_data.json"

ADD_MEMBERS_DIRECT = f"https://t.me/{PUBLIC_GROUP_USERNAME}"

RANKS = {0: "مبتدئ 🐣", 10: "نشيط ⚡", 25: "محترف 🔥", 50: "أسطورة 👑", 100: "امبراطور 💎", 200: "فرعون 🏛️"}

# بفر لتجميع الإضافات - مفتاح: inviter_id, قيمة: {count, timer, names}
pending_invites = {}

def get_rank(count):
    rank = "مبتدئ 🐣"
    for req, r in RANKS.items():
        if count >= req: rank = r
    return rank

def load_data():
    default = {
        "users": {}, "banned": [], "support": {},
        "stats": {"total_joins": 0, "total_messages": 0},
        "broadcast": {"waiting": False},
        "antispam": {}
    }
    if not os.path.exists(DATA_FILE):
        return default
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        loaded = json.load(f)
        for k, v in default.items():
            if k not in loaded: loaded[k] = v
        return loaded

def save_data(data_to_save):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

data = load_data()

def check_spam(user_id):
    now = time.time()
    user_id = str(user_id)
    if user_id not in data["antispam"]:
        data["antispam"][user_id] = []
    data["antispam"][user_id] = [t for t in data["antispam"][user_id] if now - t < 10]
    data["antispam"][user_id].append(now)
    if len(data["antispam"][user_id]) > 5:
        return False
    return True

# ========== إرسال رسالة الترحيب المجمعة ==========
def send_batch_welcome(inviter_id):
    global data, pending_invites

    if inviter_id not in pending_invites:
        return

    batch = pending_invites.pop(inviter_id)
    added_count = batch["count"]
    inviter_name = batch["name"]

    if inviter_id not in data["users"]:
        data["users"][inviter_id] = {
            "count": 0, "name": inviter_name,
            "got_link": False, "invited": [],
            "join_date": str(datetime.now()),
            "last_active": str(datetime.now())
        }

    total_count = data["users"][inviter_id]["count"]
    remaining = max(0, REQUIRED_INVITES - total_count)
    data["users"][inviter_id]["last_active"] = str(datetime.now())
    save_data(data)

    print(f"[LOG] إرسال ملخص: {inviter_name} ضاف {added_count} = المجموع {total_count}")

    # لو وصل للعدد المطلوب
    if total_count >= REQUIRED_INVITES and not data["users"][inviter_id]["got_link"]:
        data["users"][inviter_id]["got_link"] = True
        save_data(data)

        text = f"✅ «الطالب™» {inviter_name} «اضاف «{total_count}»\n🔥√\n\n√ وتم تسجيلة في الجروب السري 👨‍💻\n\n👇 انضم هنـا ليتم قبولك فالجروب السري ➡️\n\n{SECRET_GROUP_LINK}\n\n📚 لو عيز تتسجل انتا كمان ضيفه {REQUIRED_INVITES} هـنـا\n\n√ ليتم قبولك في الجروب السري ➡️"

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔥 اضغط هنا للدخول للجروب السري", url=SECRET_GROUP_LINK))
        markup.add(types.InlineKeyboardButton(f"👥 إضافة أعضاء", url=ADD_MEMBERS_DIRECT))

        bot.send_message(MAIN_GROUP_ID, text, reply_markup=markup)

        try:
            bot.send_message(inviter_id, f"🎊 مبروك يا {inviter_name}\nوصلت {total_count} دعوة {get_rank(total_count)}\n\nادخل الجروب السري من هنا:\n{SECRET_GROUP_LINK}")
        except: pass

    else:
        # رسالة واحدة للكل
        if added_count == 1:
            text = f"✅ «الطالب™» {inviter_name} «اضاف «{total_count}»\n🔥\n\n⏳ فاضلك {remaining} دعوة وتدخل الجروب السري\n\n📚 لو عيز تتسجل انتا كمان ضيفه {REQUIRED_INVITES} هـنـا"
        else:
            text = f"✅ «الطالب™» {inviter_name} «اضاف «{added_count}» عضو\n🔥\n\n📊 إجمالي دعواتك: {total_count}\n⏳ فاضلك {remaining} دعوة وتدخل الجروب السري\n\n📚 لو عيز تتسجل انتا كمان ضيفه {REQUIRED_INVITES} هـنـا"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"👥 إضافة أعضاء", url=ADD_MEMBERS_DIRECT))

        bot.send_message(MAIN_GROUP_ID, text, reply_markup=markup)

# ========== تسجيل الإضافة في البفر ==========
def queue_invite(inviter_id, inviter_name, new_user_id):
    global data, pending_invites

    if inviter_id == new_user_id or inviter_id in data["banned"]:
        return

    try:
        new_user = bot.get_chat_member(MAIN_GROUP_ID, new_user_id).user
        if new_user.is_bot: return
    except: return

    data["stats"]["total_joins"] += 1

    if inviter_id not in data["users"]:
        data["users"][inviter_id] = {
            "count": 0, "name": inviter_name,
            "got_link": False, "invited": [],
            "join_date": str(datetime.now()),
            "last_active": str(datetime.now())
        }

    if new_user_id in data["users"][inviter_id]["invited"]:
        return

    data["users"][inviter_id]["invited"].append(new_user_id)
    data["users"][inviter_id]["count"] = len(data["users"][inviter_id]["invited"])
    save_data(data)

    # ضيف للبفر
    if inviter_id not in pending_invites:
        pending_invites[inviter_id] = {"count": 0, "name": inviter_name, "timer": None}

    pending_invites[inviter_id]["count"] += 1

    # الغي التايمر القديم لو موجود
    if pending_invites[inviter_id]["timer"]:
        pending_invites[inviter_id]["timer"].cancel()

    # اعمل تايمر جديد 3 ثواني - لو مفيش اضافات تاني هيبعت الرسالة
    timer = threading.Timer(3.0, send_batch_welcome, args=[inviter_id])
    pending_invites[inviter_id]["timer"] = timer
    timer.start()

    print(f"[LOG] تم تجميع: {inviter_name} = +1 (المجموع المؤقت {pending_invites[inviter_id]['count']})")

@bot.chat_member_handler()
def track_invites_chat_member(message: types.ChatMemberUpdated):
    global data
    if message.chat.id!= MAIN_GROUP_ID: return
    old, new = message.old_chat_member, message.new_chat_member

    if old.status in ['left', 'kicked'] and new.status == 'member':
        inviter_id = str(message.from_user.id)
        new_user_id = str(new.user.id)
        queue_invite(inviter_id, message.from_user.first_name, new_user_id)

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

@bot.message_handler(content_types=['new_chat_members'])
def track_invites_new_member(message):
    if message.chat.id!= MAIN_GROUP_ID: return
    inviter_id = str(message.from_user.id)
    inviter_name = message.from_user.first_name

    for new_user in message.new_chat_members:
        if new_user.id == bot.get_me().id: continue
        queue_invite(inviter_id, inviter_name, str(new_user.id))

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
    markup.add(types.InlineKeyboardButton(f"👥 إضافة أعضاء", url=ADD_MEMBERS_DIRECT))
    markup.add(types.InlineKeyboardButton("📞 تواصل مع الدعم", callback_data="contact_support"))

    if msg.from_user.id == OWNER_ID:
        markup.add(
            types.InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel"),
            types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast_menu")
        )

    text = f"مرحباً {msg.from_user.first_name} 👋\n\n" \
           f"🎯 المطلوب: {REQUIRED_INVITES} دعوة\n" \
           f"📈 دعواتك: {count}\n" \
           f"🏅 رانك: {rank}\n" \
           f"⏳ المتبقي: {max(0, REQUIRED_INVITES - count)}\n\n" \
           f"دوس على الزرار وضيف أصحابك واستلم الجروب السري تلقائي ⚡"

    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def handle_buttons(call):
    global data
    user_id = str(call.from_user.id)

    if call.data == "my_stats":
        user_data = data["users"].get(user_id, {"count": 0})
        count = user_data["count"]
        sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["count"], reverse=True)
        position = next((i+1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), "غير مصنف")

        text = f"📊 إحصائياتك\n\n" \
               f"👤 الاسم: {call.from_user.first_name}\n" \
               f"📥 الدعوات: {count}\n" \
               f"🏅 الرانك: {get_rank(count)}\n" \
               f"🥇 ترتيبك: {position}\n" \
               f"⏳ المتبقي: {max(0, REQUIRED_INVITES - count)}\n" \
               f"📅 تاريخ الانضمام: {user_data.get('join_date', 'غير معروف')[:10]}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"👥 إضافة أعضاء", url=ADD_MEMBERS_DIRECT))
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_start"))

        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "top10":
        sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["count"], reverse=True)[:10]
        text = "🏆 توب 10 أعضاء\n\n"
        if not sorted_users:
            text += "مفيش دعوات لسه 😢"
        else:
            for i, (uid, info) in enumerate(sorted_users, 1):
                text += f"{i}. {info['name']} - {info['count']} دعوة {get_rank(info['count'])}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_start"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "contact_support":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📝 اكتب رسالتك للدعم الفني هنا\nسيتم الرد عليك في أقرب وقت 👨‍💻")
        data["support"][user_id] = "waiting"
        save_data(data)

    elif call.data == "admin_panel":
        if call.from_user.id!= OWNER_ID:
            return bot.answer_callback_query(call.id, "❌ للمشرف فقط", show_alert=True)

        total_users = len(data["users"])
        total_invites = sum(u["count"] for u in data["users"].values())
        active = sum(1 for u in data["users"].values() if u["count"] >= REQUIRED_INVITES)
        banned = len(data["banned"])

        text = f"👑 لوحة التحكم المتطورة\n\n" \
               f"👥 إجمالي الأعضاء: {total_users}\n" \
               f"📨 إجمالي الدعوات: {total_invites}\n" \
               f"✅ وصلوا للهدف: {active}\n" \
               f"🚫 المحظورين: {banned}\n" \
               f"📊 دخل الجروب: {data['stats']['total_joins']}\n" \
               f"💬 إجمالي الرسائل: {data['stats']['total_messages']}\n\n" \
               f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast_menu"),
            types.InlineKeyboardButton("📊 إحصائيات", callback_data="detailed_stats")
        )
        markup.add(
            types.InlineKeyboardButton("🚫 قائمة المحظورين", callback_data="banned_list"),
            types.InlineKeyboardButton("🔄 تصفير الكل", callback_data="reset_confirm")
        )
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_start"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "broadcast_menu":
        if call.from_user.id!= OWNER_ID: return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 بدء الإذاعة", callback_data="start_broadcast"))
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin_panel"))
        bot.edit_message_text("📢 نظام الإذاعة\n\nدوس بدء الإذاعة واكتب الرسالة اللي عايز تبعتها لكل الأعضاء",
                            call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "start_broadcast":
        if call.from_user.id!= OWNER_ID: return
        data["broadcast"]["waiting"] = True
        save_data(data)
        bot.send_message(call.message.chat.id, "📝 اكتب رسالة الإذاعة الآن\nيمكنك إرسال نص، صورة، فيديو، ملف\n\nلإلغاء اكتب /cancel")

    elif call.data == "detailed_stats":
        total = len(data["users"])
        avg = sum(u["count"] for u in data["users"].values()) / total if total > 0 else 0
        active_today = sum(1 for u in data["users"].values()
                          if "last_active" in u and
                          datetime.fromisoformat(u["last_active"]) > datetime.now() - timedelta(days=1))

        text = f"📊 إحصائيات مفصلة\n\n" \
               f"👥 إجمالي المسجلين: {total}\n" \
               f"📈 متوسط الدعوات: {avg:.1f}\n" \
               f"🔥 نشطين اليوم: {active_today}\n" \
               f"📊 إجمالي الدخول: {data['stats']['total_joins']}\n" \
               f"💬 رسائل الدعم: {data['stats']['total_messages']}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin_panel"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "banned_list":
        banned = data["banned"]
        text = f"🚫 المحظورين ({len(banned)})\n\n"
        if not banned:
            text += "لا يوجد محظورين"
        else:
            for uid in banned[:20]:
                text += f"• {uid}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin_panel"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "reset_confirm":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ أيوة صفر", callback_data="reset_yes"),
            types.InlineKeyboardButton("❌ لا", callback_data="admin_panel")
        )
        bot.edit_message_text("⚠️ تحذير: سيتم مسح كل البيانات!\nمتأكد عايز تصفر كل الدعوات؟",
                            call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "reset_yes":
        data = {"users": {}, "banned": [], "stats": {"total_joins": 0, "total_messages": 0}, "support": {}, "broadcast": {"waiting": False}, "antispam": {}}
        save_data(data)
        bot.answer_callback_query(call.id, "تم التصفير بنجاح", show_alert=True)
        handle_buttons(types.CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, data="admin_panel"))

    elif call.data == "back_start":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)

@bot.message_handler(func=lambda msg: msg.chat.type == 'private', content_types=['text', 'photo', 'document', 'voice', 'video', 'sticker'])
def handle_private(msg):
    global data
    user_id = str(msg.from_user.id)

    if not check_spam(user_id) and msg.from_user.id!= OWNER_ID:
        return bot.reply_to(msg, "⚠️ اهدى شوية! بتبعت رسايل كتير")

    if msg.from_user.id == OWNER_ID and msg.reply_to_message:
        try:
            target_id = msg.reply_to_message.text.split("ID: ")[1].split("\n")[0]
            bot.copy_message(target_id, msg.chat.id, msg.message_id)
            bot.reply_to(msg, "✅ تم إرسال ردك للعضو")
        except:
            bot.reply_to(msg, "❌ فشل الإرسال. اعمل Reply على رسالة العضو")
        return

    if msg.from_user.id == OWNER_ID and data["broadcast"]["waiting"]:
        if msg.text == "/cancel":
            data["broadcast"]["waiting"] = False
            save_data(data)
            return bot.reply_to(msg, "❌ تم إلغاء الإذاعة")

        data["broadcast"]["waiting"] = False
        save_data(data)
        threading.Thread(target=broadcast_message, args=(msg,)).start()
        bot.reply_to(msg, f"📢 جاري إرسال الإذاعة لـ {len(data['users'])} عضو...")
        return

    if user_id in data.get("support", {}):
        del data["support"][user_id]
        save_data(data)

    data["stats"]["total_messages"] += 1
    save_data(data)

    user_info = f"📨 رسالة جديدة من الدعم\n\n" \
                f"👤 الاسم: {msg.from_user.first_name}\n" \
                f"🆔 ID: {msg.from_user.id}\n" \
                f"🔗 يوزر: @{msg.from_user.username}\n" \
                f"📊 دعواته: {data['users'].get(user_id, {}).get('count', 0)}\n\n" \
                f"📝 الرسالة:"

    bot.send_message(OWNER_ID, user_info)
    bot.forward_message(OWNER_ID, msg.chat.id, msg.message_id)
    bot.reply_to(msg, "✅ تم إرسال رسالتك للمدير بنجاح\nسيتم الرد عليك قريباً ⏳")

def broadcast_message(msg):
    success = 0
    failed = 0
    for user_id in data["users"].keys():
        try:
            bot.copy_message(user_id, msg.chat.id, msg.message_id)
            success += 1
            time.sleep(0.05)
        except:
            failed += 1
    bot.send_message(OWNER_ID, f"✅ تمت الإذاعة\n\nنجح: {success}\nفشل: {failed}")

@bot.message_handler(commands=['add'])
def add_invites(msg):
    global data
    if msg.from_user.id!= OWNER_ID: return
    try:
        _, user_id, amount = msg.text.split()
        if user_id not in data["users"]:
            data["users"][user_id] = {"count": 0, "name": "Unknown", "got_link": False, "invited": [], "join_date": str(datetime.now())}
        data["users"][user_id]["count"] += int(amount)
        save_data(data)
        bot.reply_to(msg, f"✅ تم إضافة {amount} دعوة للعضو {user_id}")
    except:
        bot.reply_to(msg, "❌ استخدم: /add user_id 10")

@bot.message_handler(commands=['ban'])
def ban_user(msg):
    global data
    if msg.from_user.id!= OWNER_ID: return
    try:
        user_id = msg.text.split()[1]
        if user_id not in data["banned"]:
            data["banned"].append(user_id)
            save_data(data)
        bot.reply_to(msg, f"🚫 تم حظر {user_id}")
    except:
        bot.reply_to(msg, "❌ استخدم: /ban user_id")

@bot.message_handler(commands=['unban'])
def unban_user(msg):
    global data
    if msg.from_user.id!= OWNER_ID: return
    try:
        user_id = msg.text.split()[1]
        if user_id in data["banned"]:
            data["banned"].remove(user_id)
            save_data(data)
        bot.reply_to(msg, f"✅ تم فك حظر {user_id}")
    except:
        bot.reply_to(msg, "❌ استخدم: /unban user_id")

@bot.message_handler(commands=['id'])
def get_id(msg):
    bot.reply_to(msg, f"🆔 ايدي الجروب: `{msg.chat.id}`\nايديك: `{msg.from_user.id}`", parse_mode="Markdown")

if __name__ == '__main__':
    print("✅ Bot Pro Max is running...")
    bot.remove_webhook()
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
    bot.infinity_polling(allowed_updates=['chat_member', 'message', 'callback_query'], skip_pending=True, timeout=60)
