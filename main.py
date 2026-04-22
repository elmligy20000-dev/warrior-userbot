import import asyncio
import os
import random
import json
import time
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError

API_ID = 33595004
API_HASH = 'cbd1066ed026997f2f4a7c4323b7bda7'
DB_FILE = 'warrior_userbot_db.json'
DEVELOPER = 'devazf'
DELETE_AFTER = 15
COOLDOWN = 3
SUBSCRIPTION_PRICE = 5

DISCOUNT_CODES = {
    'WARRIOR50': {'percent': 50, 'price': 2.5, 'uses': 0, 'max_uses': 100},
    'AZEF30': {'percent': 30, 'price': 3.5, 'uses': 0, 'max_uses': 50},
    'FREE7': {'percent': 100, 'price': 0, 'days': 7, 'uses': 0, 'max_uses': 20},
    'VIP20': {'percent': 20, 'price': 4, 'uses': 0, 'max_uses': 200}
}

ROASTS = [
    "يا كسمك {mention} شكلك نايم على وشك 😂",
    "يا كسمك {mention} انت لسه عايش؟ كنت فاكرك انقرضت 🌚",
    "يا كسمك {mention} كفاية نوم قوم شوف حياتك 😴",
    "يا كسمك {mention} انت محتاج ابديت للـ software بتاعك 🤖",
    "يا كسمك {mention} فينك مختفي؟ ولا الشبكة قطعت عندك 📡",
    "يا كسمك {mention} شكلك بتشحن لسه 1% 🔋",
    "يا كسمك {mention} انت لو بنزين كان خلص من زمان ⛽",
    "يا كسمك {mention} صاحي ولا عامل نفسك ميت؟ 💀",
    "يا كسمك {mention} انت محتاج فورمات 😂",
    "يا كسمك {mention} فينك يا عم الحج مختفي فين 🌚",
    "يا كسمك {mention} شكلك مضيع الباسورد بتاع حياتك 🔐",
    "يا كسمك {mention} انت لو WiFi كان الباسورد بتاعك 12345 📶",
    "يا كسمك {mention} دماغك دي شغالة بويندوز XP ولا ايه 🖥️",
    "يا كسمك {mention} انت فصلت ولا الشاحن باظ؟ 🔌",
    "يا كسمك {mention} شكلك عامل وضع الطيران على مخك ✈️",
    "يا كسمك {mention} انت محتاج ريستارت للحياة 😂",
    "يا كسمك {mention} شكلك لسه على اصدار 2010 📅",
    "يا كسمك {mention} انت لو تطبيق كان مسحته من زمان 📱",
    "يا كسمك {mention} فينك يا اسطورة الاختفاء 🥷",
    "يا كسمك {mention} انت لو لمبة كان اتحرقت من زمان 💡",
    "يا كسمك {mention} شكلك سايب مخك في الشاحن 🧠",
    "يا كسمك {mention} انت محتاج تحديث ضروري ⚠️",
    "يا كسمك {mention} فينك يا ملك اللاج 🎮",
    "يا كسمك {mention} انت شغال على باقة 2G ولا ايه 📶",
    "يا كسمك {mention} شكلك ناسي تاكل النهاردة 🍔",
    "يا كسمك {mention} انت لو عربية كان الكاوتش نام 🛞",
    "يا كسمك {mention} فينك يا كينج التطنيش 👑",
    "يا كسمك {mention} انت محتاج حد يصحيك بكوز ماية 🪣",
    "يا كسمك {mention} شكلك عامل ميوت للحياة 🔇",
    "يا كسمك {mention} انت لو مسلسل كان اتلغى من اول حلقة 📺",
    "يا كسمك {mention} فينك يا زعيم الغياب 🌚",
    "يا كسمك {mention} انت شكلك ناسي الباسورد بتاع الواتس 🔑",
    "يا كسمك {mention} انت محتاج حد يعملك منشن عشان تصحى 😂",
    "يا كسمك {mention} شكلك بتحمل لسه... 0% 📊",
    "يا كسمك {mention} انت لو بطارية كان خلصت من بدري 🪫",
    "يا كسمك {mention} فينك يا عم الناس ولا انت مش من الناس 😂",
    "يا كسمك {mention} انت لو نوتفكيشن كان عملتلك ميوت 🔕",
    "يا كسمك {mention} شكلك دخلت الثلاجة ونسيت تطلع 🧊",
    "يا كسمك {mention} انت محتاج حد يرنك جرس 🔔",
    "يا كسمك {mention} فينك يا اسطورة الـ AFK 🎮"
]

login_state = {}
add_roast_state = {}
delete_roast_state = {}
last_roast_time = {}
saved_roasts = {}
client = None
db = None

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'all_roasts' in data:
                    global ROASTS
                    ROASTS = data['all_roasts']
                if 'saved_roasts' in data:
                    global saved_roasts
                    saved_roasts = data['saved_roasts']
                if 'discount_codes' in data:
                    global DISCOUNT_CODES
                    DISCOUNT_CODES.update(data['discount_codes'])
                return data
        except:
            pass
    return {
        'owner_id': None,
        'session': None,
        'all_roasts': ROASTS,
        'roast_counts': {},
        'saved_roasts': {},
        'discount_codes': DISCOUNT_CODES,
        'subscriptions': {},
        'stats': {'total_roasts': 0}
    }

def save_db(db):
    db['all_roasts'] = ROASTS
    db['saved_roasts'] = saved_roasts
    db['discount_codes'] = DISCOUNT_CODES
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

async def delete_after_delay(client, msg, delay):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

def check_cooldown(user_id):
    global last_roast_time
    now = time.time()
    if user_id not in last_roast_time:
        last_roast_time[user_id] = 0
    if now - last_roast_time[user_id] < COOLDOWN:
        return False, COOLDOWN - (now - last_roast_time[user_id])
    last_roast_time[user_id] = now
    return True, 0

def check_subscription(db, user_id):
    if db.get('owner_id') and user_id == db['owner_id']:
        return True, "مالك البوت"

    uid_str = str(user_id)
    if uid_str not in db.get('subscriptions', {}):
        return False, "غير مشترك"

    sub_data = db['subscriptions'][uid_str]
    if 'paid_until' not in sub_data:
        return False, "غير مشترك"

    paid_until = datetime.fromisoformat(sub_data['paid_until'])
    if datetime.now() > paid_until:
        return False, "الاشتراك انتهى"

    days_left = (paid_until - datetime.now()).days
    return True, f"{days_left} يوم متبقي"

async def load_userbot_client():
    global client, db
    if db.get('session'):
        try:
            if client:
                await client.disconnect()
            client = TelegramClient(StringSession(db['session']), API_ID, API_HASH)
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                if not db.get('owner_id'):
                    db['owner_id'] = me.id
                    save_db(db)
                print(f"✅ اليوزربوت اشتغل على: {me.first_name}")
                return True
            else:
                db['session'] = None
                db['owner_id'] = None
                save_db(db)
                client = None
                return False
        except Exception as e:
            print(f"❌ خطأ في تحميل اليوزربوت: {e}")
            client = None
            return False
    return False

async def setup_userbot_handlers():
    global client, db
    
    if not client or not await client.is_user_authorized():
        return

    @client.on(events.NewMessage(pattern=r'\.Azef$', outgoing=True))
    async def roast_user(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        can_roast, wait_time = check_cooldown(sender_id)
        if not can_roast:
            return await event.delete()
        await event.delete()
        if not event.is_reply:
            return await client.send_message(event.chat_id, "❌ اعمل ريبلاي على رسالة أو استخدم `.Azef @username`")
        reply_msg = await event.get_reply_message()
        user = await reply_msg.get_sender()
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        roast = random.choice(ROASTS).format(mention=mention)
        msg = await client.send_message(event.chat_id, roast, parse_mode='md')
        uid_str = str(user.id)
        db['roast_counts'][uid_str] = db['roast_counts'].get(uid_str, 0) + 1
        db['stats']['total_roasts'] += 1
        save_db(db)
        asyncio.create_task(delete_after_delay(client, msg, DELETE_AFTER))

    @client.on(events.NewMessage(pattern=r'\.Azef @', outgoing=True))
    async def roast_user_mention(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        can_roast, wait_time = check_cooldown(sender_id)
        if not can_roast:
            return await event.delete()
        await event.delete()
        username = event.text.split('@', 1)[1].strip()
        try:
            user = await client.get_entity(username)
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            roast = random.choice(ROASTS).format(mention=mention)
            msg = await client.send_message(event.chat_id, roast, parse_mode='md')
            uid_str = str(user.id)
            db['roast_counts'][uid_str] = db['roast_counts'].get(uid_str, 0) + 1
            db['stats']['total_roasts'] += 1
            save_db(db)
            asyncio.create_task(delete_after_delay(client, msg, DELETE_AFTER))
        except:
            await client.send_message(event.chat_id, "❌ معرفتش ألاقي اليوزر ده")

    @client.on(events.NewMessage(pattern=r'\.Azef_all', outgoing=True))
    async def roast_all(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        can_roast, wait_time = check_cooldown(sender_id)
        if not can_roast:
            return await event.delete()
        await event.delete()
        if not event.is_group:
            return await client.send_message(event.chat_id, "❌ الأمر ده في الجروبات بس")
        participants = await client.get_participants(event.chat_id)
        roast_targets = [p for p in participants if not p.bot and p.id!= sender_id]
        if not roast_targets:
            return await client.send_message(event.chat_id, "😂 مفيش حد أحفل عليه")
        targets = random.sample(roast_targets, min(3, len(roast_targets)))
        for user in targets:
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            roast = random.choice(ROASTS).format(mention=mention)
            msg = await client.send_message(event.chat_id, roast, parse_mode='md')
            uid_str = str(user.id)
            db['roast_counts'][uid_str] = db['roast_counts'].get(uid_str, 0) + 1
            db['stats']['total_roasts'] += 1
            asyncio.create_task(delete_after_delay(client, msg, DELETE_AFTER))
            await asyncio.sleep(1)
        save_db(db)

    @client.on(events.NewMessage(pattern=r'\.Azef_spam', outgoing=True))
    async def roast_spam(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        await event.delete()
        parts = event.text.split(' ', 1)
        if len(parts) < 2:
            return await client.send_message(event.chat_id, "❌ استخدم: `.Azef_spam @username`")
        username = parts[1].strip()
        try:
            user = await client.get_entity(username)
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            for i in range(5):
                roast = random.choice(ROASTS).format(mention=mention)
                msg = await client.send_message(event.chat_id, roast, parse_mode='md')
                asyncio.create_task(delete_after_delay(client, msg, DELETE_AFTER))
                await asyncio.sleep(1.5)
            uid_str = str(user.id)
            db['roast_counts'][uid_str] = db['roast_counts'].get(uid_str, 0) + 5
            db['stats']['total_roasts'] += 5
            save_db(db)
        except:
            await client.send_message(event.chat_id, "❌ معرفتش ألاقي اليوزر ده")

    @client.on(events.NewMessage(pattern=r'\.Azef_rand', outgoing=True))
    async def roast_random(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        can_roast, wait_time = check_cooldown(sender_id)
        if not can_roast:
            return await event.delete()
        await event.delete()
        if not event.is_group:
            return await client.send_message(event.chat_id, "❌ الأمر ده في الجروبات بس")
        participants = await client.get_participants(event.chat_id)
        targets = [p for p in participants if not p.bot and p.id!= sender_id]
        if not targets:
            return await client.send_message(event.chat_id, "😂 مفيش حد أحفل عليه")
        user = random.choice(targets)
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        roast = random.choice(ROASTS).format(mention=mention)
        msg = await client.send_message(event.chat_id, roast, parse_mode='md')
        uid_str = str(user.id)
        db['roast_counts'][uid_str] = db['roast_counts'].get(uid_str, 0) + 1
        db['stats']['total_roasts'] += 1
        save_db(db)
        asyncio.create_task(delete_after_delay(client, msg, DELETE_AFTER))

    @client.on(events.NewMessage(pattern=r'\.Azef_top', outgoing=True))
    async def roast_top(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        await event.delete()
        if not db.get('roast_counts'):
            return await client.send_message(event.chat_id, "😂 لسه محدش اتحفل عليه")
        sorted_counts = sorted(db['roast_counts'].items(), key=lambda x: x[1], reverse=True)[:5]
        msg = "🏆 **توب المحفلين**\n\n"
        for i, (uid, count) in enumerate(sorted_counts, 1):
            try:
                user = await client.get_entity(int(uid))
                msg += f"{i}. {user.first_name} - {count} مرة 😂\n"
            except:
                msg += f"{i}. ID:{uid} - {count} مرة 😂\n"
        top_msg = await client.send_message(event.chat_id, msg)
        asyncio.create_task(delete_after_delay(client, top_msg, 20))

    @client.on(events.NewMessage(pattern=r'\.Azef_list', outgoing=True))
    async def roast_list(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        await event.edit(f"📊 **عدد التحفيلات:** {len(ROASTS)}\n⚔️ **إجمالي:** {db['stats']['total_roasts']}")

    @client.on(events.NewMessage(pattern=r'\.add_Azef', outgoing=True))
    async def add_roast(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        if not is_subscribed:
            await event.edit(f"❌ **غير مشترك**\n\n{sub_msg}\n\nراسل @{DEVELOPER} للتفعيل")
            return
        parts = event.text.split(' ', 1)
        if len(parts) < 2:
            return await event.edit("❌ استخدم: `.add_Azef النص`\nمثال: `.add_Azef يا كسمك {mention} شكلك تعبان`")
        new_roast = parts[1].strip()
        if '{mention}' not in new_roast:
            return await event.edit("❌ لازم تحط `{mention}` في النص")
        if not new_roast.startswith('يا كسمك'):
            return await event.edit("❌ لازم التحفيلة تبدأ بـ `يا كسمك`")
        ROASTS.append(new_roast)
        save_db(db)
        await event.edit(f"✅ ضفت التحفيلة\nالعدد دلوقتي: {len(ROASTS)}")

    @client.on(events.NewMessage(pattern=r'\.logout', outgoing=True))
    async def logout_cmd(event):
        if event.sender_id!= db.get('owner_id'):
            return await event.edit("❌ **الأمر ده للمالك بس**")
        await event.delete()
        db['session'] = None
        db['owner_id'] = None
        save_db(db)
        await client.disconnect()
        global client
        client = None
        await client.send_message('me', "🔐 **تم تسجيل الخروج**\n\nالحساب اتفصل من البوت\n\nروح لبوت التحكم عشان تضيف حساب جديد")

    @client.on(events.NewMessage(pattern=r'\.discount', outgoing=True))
    async def discount_cmd(event):
        parts = event.text.split(' ', 1)
        if len(parts) < 2:
            msg = "🎟️ **أكواد الخصم المتاحة**\n━━━━━━━━━━━━━━━━━━━━\n\n"
            for code, data in DISCOUNT_CODES.items():
                if data['uses'] < data['max_uses']:
                    if 'days' in data:
                        msg += f"**{code}**\n💰 {data['percent']}% - {data['days']} أيام مجانا\n\n"
                    else:
                        msg += f"**{code}**\n💰 {data['percent']}% - ${data['price']}\n\n"
            msg += f"━━━━━━━━━━━━━━━━━━━━\n💎 السعر العادي: ${SUBSCRIPTION_PRICE}/شهر"
            return await event.edit(msg)
        code = parts[1].strip().upper()
        if code not in DISCOUNT_CODES:
            return await event.edit(f"❌ كود **{code}** مش موجود\n\nالأكواد المتاحة:\n" + "\n".join([f"• {c}" for c in DISCOUNT_CODES.keys()]))
        code_data = DISCOUNT_CODES[code]
        if code_data['uses'] >= code_data['max_uses']:
            return await event.edit(f"❌ كود **{code}** خلص\n\nاستخداماته خلصت")
        if 'days' in code_data:
            await event.edit(f"✅ **كود خصم مفعل**\n\n🎟️ الكود: {code}\n💰 الخصم: {code_data['percent']}%\n📅 المدة: {code_data['days']} أيام مجانا\n\nراسل @{DEVELOPER} للتفعيل")
        else:
            await event.edit(f"✅ **كود خصم مفعل**\n\n🎟️ الكود: {code}\n💰 الخصم: {code_data['percent']}%\n💵 السعر: ${code_data['price']} بدل ${SUBSCRIPTION_PRICE}\n\nراسل @{DEVELOPER} للتفعيل")

    @client.on(events.NewMessage(pattern=r'\.codes', outgoing=True))
    async def codes_cmd(event):
        msg = "🎟️ **أكواد الخصم المتاحة**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for code, data in DISCOUNT_CODES.items():
            if data['uses'] < data['max_uses']:
                if 'days' in data:
                    msg += f"**{code}**\n💰 {data['percent']}% - {data['days']} أيام مجانا\nمتبقي: {data['max_uses'] - data['uses']}\n\n"
                else:
                    msg += f"**{code}**\n💰 {data['percent']}% - ${data['price']}\nمتبقي: {data['max_uses'] - data['uses']}\n\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n💎 السعر: ${SUBSCRIPTION_PRICE}/شهر"
        await event.edit(msg)

    @client.on(events.NewMessage(pattern=r'\.activate', outgoing=True))
    async def activate_cmd(event):
        if event.sender_id!= db.get('owner_id'):
            return await event.edit("❌ **الأمر ده للمالك بس**")
        parts = event.text.split(' ', 2)
        if len(parts) < 2:
            return await event.edit("❌ استخدم: `.activate @username CODE`\nأو `.activate @username` بدون كود")
        username = parts[1].strip()
        code = parts[2].strip().upper() if len(parts) > 2 else None
        try:
            user = await client.get_entity(username)
            uid_str = str(user.id)
            if uid_str not in db['subscriptions']:
                db['subscriptions'][uid_str] = {}
            if code:
                if code not in DISCOUNT_CODES:
                    return await event.edit(f"❌ كود **{code}** مش موجود")
                code_data = DISCOUNT_CODES[code]
                if code_data['uses'] >= code_data['max_uses']:
                    return await event.edit(f"❌ كود **{code}** خلص")
                if 'days' in code_data:
                    db['subscriptions'][uid_str]['paid_until'] = (datetime.now() + timedelta(days=code_data['days'])).isoformat()
                    DISCOUNT_CODES[code]['uses'] += 1
                    save_db(db)
                    await event.edit(f"✅ **تم التفعيل بكود {code}**\n\n👤 {user.first_name}\n📅 لمدة {code_data['days']} أيام مجانا\n🎟️ الخصم: {code_data['percent']}%")
                else:
                    db['subscriptions'][uid_str]['paid_until'] = (datetime.now() + timedelta(days=30)).isoformat()
                    DISCOUNT_CODES[code]['uses'] += 1
                    save_db(db)
                    await event.edit(f"✅ **تم التفعيل بكود {code}**\n\n👤 {user.first_name}\n📅 لمدة 30 يوم\n💰 السعر: ${code_data['price']} (خصم {code_data['percent']}%)")
            else:
                db['subscriptions'][uid_str]['paid_until'] = (datetime.now() + timedelta(days=30)).isoformat()
                save_db(db)
                await event.edit(f"✅ **تم التفعيل**\n\n👤 {user.first_name}\n📅 لمدة 30 يوم\n💰 السعر: $5")
            await client.send_message(user.id, "✅ **تم تفعيل اشتراكك**\n\n⚔️ بوت تحفيل المحارب\n⏰ هنبعتلك تنبيه قبل ما يخلص\n\nاستمتع بالتحفيل 😂")
        except:
            await event.edit("❌ معرفتش ألاقي اليوزر ده")

    @client.on(events.NewMessage(pattern=r'\.start', outgoing=True))
    async def start_cmd(event):
        sender_id = event.sender_id
        is_subscribed, sub_msg = check_subscription(db, sender_id)
        await event.edit(
            "⚔️ **بوت تحفيل المحارب V9**\n\n"
            "**الأوامر:**\n"
            "`.Azef @username` - تحفيل على حد\n"
            "`.Azef` + ريبلاي - تحفيل على الرسالة\n"
            "`.Azef_all` - تحفيل جماعي\n"
            "`.Azef_spam @user` - تحفيل 5 مرات\n"
            "`.Azef_rand` - تحفيل عشوائي\n"
            "`.Azef_top` - توب المحفلين\n"
            "`.add_Azef النص` - ضيف تحفيلة\n"
            "`.Azef_list` - عدد التحفيلات\n\n"
            f"📊 إجمالي: {db['stats']['total_roasts']}\n"
            f"👨‍💻 المبرمج: @{DEVELOPER}"
        )

async def run_warrior_userbot():
    global db
    db = load_db()
    
    await load_userbot_client()

    BOT_TOKEN = os.environ.get('ROAST_BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ ضيف ROAST_BOT_TOKEN في Variables")
        return

    control_bot = TelegramClient('control_bot', API_ID, API_HASH)

    @control_bot.on(events.NewMessage(pattern='/start'))
    async def start_control(event):
        user_id = event.sender_id
        is_subscribed, sub_status = check_subscription(db, user_id)

        if db.get('owner_id') and user_id == db['owner_id']:
            if client and await client.is_user_authorized():
                me = await client.get_me()
                active_subs = len([s for s in db.get('subscriptions', {}).values() if datetime.fromisoformat(s['paid_until']) > datetime.now()])
                
                await event.reply(
                    "⚔️ **بوت تحفيل المحارب V9**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👑 **لوحة المطور المتقدمة**\n\n"
                    f"✅ **الحساب:** {me.first_name}\n"
                    f"📱 **الرقم:** `{me.phone}`\n"
                    f"🆔 **ID:** `{me.id}`\n"
                    f"👤 **اليوزر:** @{me.username or 'مفيش'}\n\n"
                    f"📊 **الإحصائيات:**\n"
                    f"├ إجمالي التحفيلات: `{db['stats']['total_roasts']}`\n"
                    f"├ عدد التحفيلات: `{len(ROASTS)}`\n"
                    f"├ المشتركين النشطين: `{active_subs}`\n"
                    f"└ إجمالي المشتركين: `{len(db.get('subscriptions', {}))}`\n\n"
                    f"🎛️ **لوحة التحكم:**",
                    buttons=[
                        [Button.inline("📊 الإحصائيات", b"show_stats"), Button.inline("👥 المشتركين", b"show_subs")],
                        [Button.inline("🎟️ أكواد الخصم", b"show_codes"), Button.inline("📋 الأوامر", b"show_commands")],
                        [Button.inline("➕ إضافة تحفيلة", b"add_roast_btn"), Button.inline("🗑️ حذف تحفيلة", b"delete_roast_btn")],
                        [Button.inline("📜 عرض التحفيلات", b"list_roasts"), Button.inline("⚠️ مسح الكل", b"clear_all_roasts")],
                        [Button.inline("🔄 إعادة تشغيل", b"restart_bot"), Button.inline("🔐 تسجيل خروج", b"logout_btn")],
                        [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
                    ]
                )
            else:
                await event.reply(
                    "⚔️ **بوت تحفيل المحارب V9**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "👑 **لوحة المطور**\n\n"
                    "❌ **مفيش حساب متصل**\n\n"
                    "ضيف حسابك عشان تفعل البوت\n"
                    "هيشتغل تلقائي بعد الإضافة ✅",
                    buttons=[
                        [Button.inline("📱 إضافة حساب", b"add_account")],
                        [Button.inline("🎟️ أكواد الخصم", b"show_codes")],
                        [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
                    ]
                )
        else:
            if is_subscribed:
                await event.reply(
                    "⚔️ **بوت تحفيل المحارب V9**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👋 أهلاً بيك يا محارب!\n"
                    f"✅ **حالة الاشتراك:** نشط\n"
                    f"⏰ **المتبقي:** {sub_status}\n\n"
                    "🎯 **البوت شغال في الخاص والجروبات**\n"
                    "⚡ **تقدر تحفل على أي حد**\n\n"
                    "📱 **استخدم الأوامر في أي شات:**\n"
                    "`.Azef @username` للتحفيل\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "👨‍💻 **المبرمج:** @devazf",
                    buttons=[
                        [Button.inline("📋 عرض الأوامر", b"user_commands")],
                        [Button.inline("🎟️ أكواد الخصم", b"show_codes")],
                        [Button.url("💬 راسل المبرمج", f"https://t.me/{DEVELOPER}")]
                    ]
                )
            else:
                await event.reply(
                    "⚔️ **بوت تحفيل المحارب V9**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "👋 أهلاً بيك يا محارب!\n\n"
                    "❌ **حالة الاشتراك:** غير مفعل\n\n"
                    "💎 **مميزات البوت:**\n"
                    "• تحفيل في الخاص والجروبات\n"
                    "• +40 تحفيلة جاهزة\n"
                    "• أوامر متقدمة (سبام، عشوائي)\n"
                    "• حذف تلقائي بعد 15 ثانية\n"
                    "• إحصائيات وتوب المحفلين\n\n"
                    "💰 **الاشتراك الشهري:** $5\n"
                    "🎟️ **أو استخدم كود خصم**\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "📞 **للتفعيل:**\n"
                    f"راسل المبرمج @{DEVELOPER}\n"
                    "أو استخدم كود خصم من الزر تحت\n\n"
                    "👨‍💻 **المبرمج:** @devazf",
                    buttons=[
                        [Button.inline("🎟️ أكواد الخصم", b"show_codes")],
                        [Button.inline("💳 طرق الدفع", b"payment_methods")],
                        [Button.url("💬 راسل المبرمج للتفعيل", f"https://t.me/{DEVELOPER}")]
                    ]
                )

    @control_bot.on(events.CallbackQuery(data=b"add_account"))
    async def add_account(event):
        login_state[event.sender_id] = {'step': 'phone'}
        await event.edit(
            "📱 **إضافة حساب**\n\n"
            "ابعت رقمك مع كود الدولة\n"
            "مثال: `+201234567890`\n\n"
            "⚠️ **بعد الإضافة البوت هيشتغل تلقائي**\n"
            "من غير Restart ولا تعديل كود ✅",
            buttons=[[Button.inline("❌ إلغاء", b"cancel")]]
        )

    @control_bot.on(events.NewMessage(func=lambda e: e.sender_id in login_state))
    async def handle_login(event):
        global db
        state = login_state[event.sender_id]
        if state['step'] == 'phone':
            phone = event.text.strip()
            if not phone.startswith('+'):
                return await event.reply("❌ لازم الرقم يبدأ بـ +\nمثال: +201234567890")
            try:
                temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
                await temp_client.connect()
                await temp_client.send_code_request(phone)
                state['phone'] = phone
                state['step'] = 'code'
                state['client'] = temp_client
                await event.reply(f"✅ **بعتلك كود على {phone}**\n\nابعت الكود هنا (5 أرقام)\nمثال: `12345`")
            except Exception as e:
                await event.reply(f"❌ خطأ: {str(e)}")
                del login_state[event.sender_id]
        elif state['step'] == 'code':
            code = event.text.strip().replace(' ', '')
            temp_client = state['client']
            try:
                await temp_client.sign_in(state['phone'], code)
                session_str = temp_client.session.save()
                me = await temp_client.get_me()

                db['session'] = session_str
                db['owner_id'] = me.id
                save_db(db)

                await temp_client.disconnect()
                del login_state[event.sender_id]

                success = await load_userbot_client()
                if success:
                    await setup_userbot_handlers()

                await event.reply(
                    f"✅ **تم إضافة الحساب بنجاح**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 **الاسم:** {me.first_name}\n"
                    f"📱 **الرقم:** {me.phone}\n"
                    f"🆔 **ID:** `{me.id}`\n"
                    f"👤 **اليوزر:** @{me.username or 'مفيش'}\n\n"
                    f"⚔️ **البوت اشتغل خلاص**\n"
                    f"✅ **تم تعيينك كمالك تلقائي**\n\n"
                    f"روح أي جروب واكتب `.Azef @username`\n\n"
                    f"**البوت شغال دلوقتي من غير Restart** ✅"
                )

            except SessionPasswordNeededError:
                state['step'] = 'password'
                await event.reply("🔒 **حسابك عليه تحقق بخطوتين**\n\nابعت كلمة السر بتاعت التحقق بخطوتين")
            except PhoneCodeInvalidError:
                await event.reply("❌ الكود غلط، حاول تاني")
            except Exception as e:
                await event.reply(f"❌ خطأ: {str(e)}")
                del login_state[event.sender_id]
        elif state['step'] == 'password':
            password = event.text.strip()
            temp_client = state['client']
            try:
                await temp_client.sign_in(password=password)
                session_str = temp_client.session.save()
                me = await temp_client.get_me()

                db['session'] = session_str
                db['owner_id'] = me.id
                save_db(db)

                await temp_client.disconnect()
                del login_state[event.sender_id]

                success = await load_userbot_client()
                if success:
                    await setup_userbot_handlers()

                await event.reply(
                    f"✅ **تم إضافة الحساب بنجاح**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 **الاسم:** {me.first_name}\n"
                    f"📱 **الرقم:** {me.phone}\n"
                    f"🆔 **ID:** `{me.id}`\n"
                    f"👤 **اليوزر:** @{me.username or 'مفيش'}\n\n"
                    f"⚔️ **البوت اشتغل خلاص**\n"
                    f"✅ **تم تعيينك كمالك تلقائي**\n\n"
                    f"روح أي جروب واكتب `.Azef @username`\n\n"
                    f"**البوت شغال دلوقتي من غير Restart** ✅"
                )
            except Exception as e:
                await event.reply(f"❌ كلمة السر غلط: {str(e)}")

    @control_bot.on(events.CallbackQuery(data=b"cancel"))
    async def cancel_login(event):
        if event.sender_id in login_state:
            del login_state[event.sender_id]
        await event.edit("❌ تم الإلغاء")

    @control_bot.on(events.CallbackQuery(data=b"show_stats"))
    async def show_stats(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return

        active_subs = len([s for s in db.get('subscriptions', {}).values() if datetime.fromisoformat(s['paid_until']) > datetime.now()])
        expired_subs = len(db.get('subscriptions', {})) - active_subs
        top_users = sorted(db.get('roast_counts', {}).items(), key=lambda x: x[1], reverse=True)[:3]

        msg = "📊 **إحصائيات مفصلة**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += f"📈 **التحفيلات:**\n"
        msg += f"├ الإجمالي: `{db['stats']['total_roasts']}`\n"
        msg += f"├ المتاحة: `{len(ROASTS)}`\n"
        msg += f"└ المضافة: `{len([r for r in ROASTS if r not in ROASTS[:40]])}`\n\n"
        msg += f"👥 **المشتركين:**\n"
        msg += f"├ النشطين: `{active_subs}`\n"
        msg += f"├ المنتهين: `{expired_subs}`\n"
        msg += f"└ الإجمالي: `{len(db.get('subscriptions', {}))}`\n\n"

        if top_users:
            msg += f"🏆 **توب المحفلين:**\n"
            for i, (uid, count) in enumerate(top_users, 1):
                try:
                    user = await control_bot.get_entity(int(uid))
                    msg += f"{i}. {user.first_name}: `{count}`\n"
                except:
                    pass

        await event.edit(msg, buttons=[[Button.inline("⬅️ رجوع", b"back_to_main")]])

    @control_bot.on(events.CallbackQuery(data=b"restart_bot"))
    async def restart_bot(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        await event.edit("🔄 **جاري إعادة التشغيل...**")
        await asyncio.sleep(1)
        if client:
            await client.disconnect()
        await load_userbot_client()
        await setup_userbot_handlers()
        await event.edit("✅ **تم إعادة التشغيل بنجاح**", buttons=[[Button.inline("⬅️ رجوع", b"back_to_main")]])

    @control_bot.on(events.CallbackQuery(data=b"show_subs"))
    async def show_subs(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        subs = db.get('subscriptions', {})
        if not subs:
            return await event.edit("❌ مفيش مشتركين لسه", buttons=[[Button.inline("⬅️ رجوع", b"back_to_main")]])

        msg = "👥 **قائمة المشتركين**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for uid, data in subs.items():
            try:
                user = await control_bot.get_entity(int(uid))
                paid_until = datetime.fromisoformat(data['paid_until'])
                days_left = (paid_until - datetime.now()).days
                status = "✅" if days_left > 0 else "❌"
                msg += f"{status} **{user.first_name}**\n"
                msg += f"🆔 `{uid}`\n"
                msg += f"⏰ متبقي: {days_left} يوم\n\n"
            except:
                continue

        await event.edit(msg, buttons=[[Button.inline("⬅️ رجوع", b"back_to_main")]])

    @control_bot.on(events.CallbackQuery(data=b"show_codes"))
    async def show_codes(event):
        msg = "🎟️ **أكواد الخصم المتاحة**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for code, data in DISCOUNT_CODES.items():
            if data['uses'] < data['max_uses']:
                if 'days' in data:
                    msg += f"**{code}**\n"
                    msg += f"💰 {data['percent']}% خصم\n"
                    msg += f"📅 {data['days']} أيام مجانا\n"
                    msg += f"📊 متبقي: {data['max_uses'] - data['uses']}\n\n"
                else:
                    msg += f"**{code}**\n"
                    msg += f"💰 {data['percent']}% خصم\n"
                    msg += f"💵 ${data['price']} بدل $5\n"
                    msg += f"📊 متبقي: {data['max_uses'] - data['uses']}\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💎 **السعر العادي:** ${SUBSCRIPTION_PRICE}/شهر\n\n"
        msg += "استخدم: `.discount CODE` في أي جروب"
        await event.edit(msg, buttons=[[Button.inline("⬅️ رجوع", b"back_to_start")]])

    @control_bot.on(events.CallbackQuery(data=b"show_commands"))
    async def show_commands(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        await event.edit(
            "📋 **قايمة الأوامر الكاملة**\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "**الأوامر الأساسية:**\n"
            "`.Azef @username` - تحفيل على حد\n"
            "`.Azef` + ريبلاي - تحفيل على الرسالة\n"
            "`.Azef_all` - تحفيل جماعي على 3\n\n"
            "**الأوامر المتقدمة:**\n"
            "`.Azef_spam @user` - تحفيل 5 مرات\n"
            "`.Azef_rand` - تحفيل عشوائي\n"
            "`.Azef_top` - توب المحفلين\n\n"
            "**أوامر الإدارة:**\n"
            "`.add_Azef النص` - ضيف تحفيلة\n"
            "`.Azef_list` - عدد التحفيلات\n"
            "`.discount CODE` - تفعيل كود خصم\n"
            "`.login` - تسجيل دخول\n"
            "`.logout` - تسجيل خروج\n"
            "`.activate @user CODE` - تفعيل بكود\n"
            "`.codes` - عرض الأكواد\n\n"
            "⚠️ **ملاحظات:**\n"
            f"• التحفيلة تتمسح بعد {DELETE_AFTER} ثانية\n"
            f"• كولداون {COOLDOWN} ثواني\n\n"
            f"📊 إجمالي: {db['stats']['total_roasts']}",
            buttons=[
                [Button.inline("⬅️ رجوع", b"back_to_main")],
                [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
            ]
        )

    @control_bot.on(events.CallbackQuery(data=b"back_to_main"))
    async def back_to_main(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        if client and await client.is_user_authorized():
            me = await client.get_me()
            active_subs = len([s for s in db.get('subscriptions', {}).values() if datetime.fromisoformat(s['paid_until']) > datetime.now()])
            await event.edit(
                "⚔️ **بوت تحفيل المحارب V9**\n\n"
                f"✅ **الحساب متصل:** {me.first_name}\n"
                f"📱 **الرقم:** {me.phone}\n\n"
                f"📊 إجمالي: {db['stats']['total_roasts']}\n"
                f"📝 التحفيلات: {len(ROASTS)}\n"
                f"👥 النشطين: {active_subs}",
                buttons=[
                    [Button.inline("📊 الإحصائيات", b"show_stats"), Button.inline("👥 المشتركين", b"show_subs")],
                    [Button.inline("🎟️ أكواد الخصم", b"show_codes"), Button.inline("📋 الأوامر", b"show_commands")],
                    [Button.inline("➕ إضافة تحفيلة", b"add_roast_btn"), Button.inline("🗑️ حذف تحفيلة", b"delete_roast_btn")],
                    [Button.inline("📜 عرض التحفيلات", b"list_roasts"), Button.inline("⚠️ مسح الكل", b"clear_all_roasts")],
                    [Button.inline("🔄 إعادة تشغيل", b"restart_bot"), Button.inline("🔐 تسجيل خروج", b"logout_btn")],
                    [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
                ]
            )
        else:
            await event.edit(
                "⚔️ **بوت تحفيل المحارب V9**\n\n"
                "❌ **مفيش حساب متصل**\n\n"
                "اضغط الزر تحت عشان تضيف حسابك",
                buttons=[
                    [Button.inline("📱 إضافة حساب", b"add_account")],
                    [Button.inline("🎟️ أكواد الخصم", b"show_codes")],
                    [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
                ]
            )

    @control_bot.on(events.CallbackQuery(data=b"logout_btn"))
    async def logout_button(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        db['session'] = None
        db['owner_id'] = None
        save_db(db)
        global client
        if client:
            await client.disconnect()
        client = None
        await event.edit("✅ **تم تسجيل الخروج**\n\nالحساب اتفصل من البوت\n\nاضغط /start عشان تضيف حساب جديد")

    @control_bot.on(events.CallbackQuery(data=b"add_roast_btn"))
    async def add_roast_button(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        add_roast_state[event.sender_id] = True
        await event.edit(
            "➕ **إضافة تحفيلة جديدة**\n\n"
            "ابعت التحفيلة الجديدة\n"
            "**مهم:** لازم تحط `{mention}` في النص\n\n"
            "مثال:\n"
            "`يا كسمك {mention} انت شكلك نايم`\n\n"
            "⚠️ لازم تبدأ بـ يا كسمك {mention}",
            buttons=[[Button.inline("❌ إلغاء", b"cancel_add_roast")]]
        )

    @control_bot.on(events.CallbackQuery(data=b"cancel_add_roast"))
    async def cancel_add_roast(event):
        if event.sender_id in add_roast_state:
            del add_roast_state[event.sender_id]
        await event.edit("❌ تم الإلغاء")

    @control_bot.on(events.NewMessage(func=lambda e: e.sender_id in add_roast_state))
    async def handle_add_roast(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        new_roast = event.text.strip()
        if '{mention}' not in new_roast:
            return await event.reply("❌ لازم تحط `{mention}` في النص\nمثال: `يا كسمك {mention} انت تعبان`")
        if not new_roast.startswith('يا كسمك'):
            return await event.reply("❌ لازم التحفيلة تبدأ بـ `يا كسمك`\nمثال: `يا كسمك {mention} انت تعبان`")
        ROASTS.append(new_roast)
        save_db(db)
        del add_roast_state[event.sender_id]
        await event.reply(f"✅ **تم إضافة التحفيلة**\n\n📝 **النص:** {new_roast}\n📊 **العدد دلوقتي:** {len(ROASTS)}")

    @control_bot.on(events.CallbackQuery(data=b"delete_roast_btn"))
    async def delete_roast_button(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        if not ROASTS:
            return await event.edit("❌ **مفيش تحفيلات**\n\nضيف تحفيلات الأول من زر ➕", buttons=[[Button.inline("⬅️ رجوع", b"back_to_main")]])
        delete_roast_state[event.sender_id] = True
        msg = "🗑️ **حذف تحفيلة**\n\nابعت رقم التحفيلة اللي عايز تحذفها\n\n⚠️ **تقدر تحذف أي تحفيلة حتى الأساسية**\n\n"
        for i, roast in enumerate(ROASTS, 1):
            preview = roast[:50] + "..." if len(roast) > 50 else roast
            msg += f"**{i}.** {preview}\n"
        await event.edit(msg, buttons=[[Button.inline("❌ إلغاء", b"cancel_delete_roast")]])

    @control_bot.on(events.CallbackQuery(data=b"cancel_delete_roast"))
    async def cancel_delete_roast(event):
        if event.sender_id in delete_roast_state:
            del delete_roast_state[event.sender_id]
        await event.edit("❌ تم الإلغاء")

    @control_bot.on(events.NewMessage(func=lambda e: e.sender_id in delete_roast_state))
    async def handle_delete_roast(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        try:
            num = int(event.text.strip())
            if num < 1 or num > len(ROASTS):
                return await event.reply(f"❌ الرقم غلط\n\nاختار رقم من 1 لـ {len(ROASTS)}")
            roast_to_delete = ROASTS[num - 1]
            ROASTS.pop(num - 1)
            save_db(db)
            del delete_roast_state[event.sender_id]
            await event.reply(f"✅ **تم حذف التحفيلة**\n\n📝 **النص المحذوف:**\n{roast_to_delete}\n\n📊 **العدد دلوقتي:** {len(ROASTS)}")
        except ValueError:
            await event.reply("❌ ابعت رقم صحيح")
        except Exception as e:
            await event.reply(f"❌ خطأ: {str(e)}")

    @control_bot.on(events.CallbackQuery(data=b"list_roasts"))
    async def list_roasts(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        if not ROASTS:
            return await event.edit("📜 **التحفيلات**\n\n❌ مفيش تحفيلات خالص\nضيف تحفيلات من زر ➕", buttons=[[Button.inline("⬅️ رجوع", b"back_to_main")]])
        msg = "📜 **كل التحفيلات**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, roast in enumerate(ROASTS, 1):
            preview = roast[:60] + "..." if len(roast) > 60 else roast
            msg += f"**{i}.** {preview}\n\n"
            if len(msg) > 3500:
                msg += f"... و {len(ROASTS) - i} تاني"
                break
        await event.edit(msg, buttons=[[Button.inline("🗑️ حذف تحفيلة", b"delete_roast_btn")], [Button.inline("⚠️ مسح الكل", b"clear_all_roasts")], [Button.inline("⬅️ رجوع", b"back_to_main")]])

    @control_bot.on(events.CallbackQuery(data=b"clear_all_roasts"))
    async def clear_all_roasts(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        await event.edit("⚠️ **تحذير خطير**\n\nانت هتمسح **كل التحفيلات**\n\nهل انت متأكد؟", buttons=[[Button.inline("✅ ايوة امسح الكل", b"confirm_clear_all")], [Button.inline("❌ لا إلغاء", b"cancel_clear")]])

    @control_bot.on(events.CallbackQuery(data=b"confirm_clear_all"))
    async def confirm_clear_all(event):
        if not db.get('owner_id') or event.sender_id!= db['owner_id']:
            return
        global ROASTS
        ROASTS = []
        save_db(db)
        await event.edit("✅ **تم مسح كل التحفيلات**\n\n📊 العدد دلوقتي: 0\n\n⚠️ البوت مش هيحفل على حد دلوقتي\nضيف تحفيلات جديدة من زر ➕", buttons=[[Button.inline("⬅️ رجوع", b"back_to_main")]])

    @control_bot.on(events.CallbackQuery(data=b"cancel_clear"))
    async def cancel_clear(event):
        await event.edit("❌ تم الإلغاء")

    @control_bot.on(events.CallbackQuery(data=b"user_commands"))
    async def user_commands(event):
        await event.edit(
            "📋 **الأوامر المتاحة للمشتركين**\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "**الأساسية:**\n"
            "`.Azef @username` - تحفيل على حد\n"
            "`.Azef` + ريبلاي - تحفيل على الرسالة\n"
            "`.Azef_all` - تحفيل جماعي\n\n"
            "**المتقدمة:**\n"
            "`.Azef_spam @user` - تحفيل 5 مرات\n"
            "`.Azef_rand` - تحفيل عشوائي\n"
            "`.Azef_top` - توب المحفلين\n"
            "`.Azef_list` - عدد التحفيلات\n\n"
            "⚠️ **ملاحظات:**\n"
            f"• التحفيلة تتمسح بعد {DELETE_AFTER} ثانية\n"
            f"• كولداون {COOLDOWN} ثواني\n"
            "• شغال في الخاص والجروبات\n\n"
            "━━━━━━━━━━━━━━━━━━━━",
            buttons=[[Button.inline("⬅️ رجوع", b"back_to_start")]]
        )

    @control_bot.on(events.CallbackQuery(data=b"back_to_start"))
    async def back_to_start(event):
        await start_control(event)

    @control_bot.on(events.CallbackQuery(data=b"payment_methods"))
    async def payment_methods(event):
        await event.edit(
            "💳 **طرق الدفع المتاحة**\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "**الطرق:**\n"
            "• USDT (TRC20)\n"
            "• PayPal\n"
            "• Vodafone Cash (مصر)\n"
            "• فودافون كاش\n\n"
            "💰 **السعر:** $5/شهر\n"
            "🎟️ **أو استخدم كود خصم**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📞 **للتفعيل راسل:**\n"
            f"@{DEVELOPER}\n\n"
            "هيتم تفعيلك في نفس اليوم ✅",
            buttons=[
                [Button.inline("🎟️ أكواد الخصم", b"show_codes")],
                [Button.inline("⬅️ رجوع", b"back_to_start")],
                [Button.url("💬 راسل المبرمج", f"https://t.me/{DEVELOPER}")]
            ]
        )

    await control_bot.start(bot_token=BOT_TOKEN)
    print("✅ بوت التحكم اشتغل")

    await setup_userbot_handlers()

    if client and await client.is_user_authorized():
        me = await client.get_me()
        print(f"⚔️ اليوزربوت V9 شغال على: {me.first_name}")
        await client.run_until_disconnected()
    else:
        print("⏳ مستني تضيف حساب من بوت التحكم")
        await control_bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(run_warrior_userbot())
