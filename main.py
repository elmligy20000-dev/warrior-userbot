import asyncio
import os
import random
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

API_ID = 33595004
API_HASH = 'cbd1066ed026997f2f4a7c4323b7bda7'
OWNER_ID = 154919127 # الـ ID بتاعك
DB_FILE = 'warrior_userbot_db.json'
SESSION_FILE = 'warrior_session.txt'
DEVELOPER = 'devazf'

# غيرت كل التحفيلات لـ "يا كسمك"
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

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'custom_roasts' in data:
                    ROASTS.extend(data['custom_roasts'])
                return data
        except:
            pass
    return {
        'session': None,
        'custom_roasts': [],
        'stats': {'total_roasts': 0}
    }

def save_db(db):
    db['custom_roasts'] = [r for r in ROASTS if not any(r.startswith(base.split('{mention}')[0]) for base in [
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
    ])]
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

async def run_warrior_userbot():
    db = load_db()

    if db.get('session'):
        client = TelegramClient(StringSession(db['session']), API_ID, API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            print("✅ تم الاتصال بالحساب المحفوظ")
        else:
            db['session'] = None
            save_db(db)
            client = None
    else:
        client = None

    BOT_TOKEN = os.environ.get('ROAST_BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ ضيف ROAST_BOT_TOKEN في Variables عشان بوت التحكم")
        return

    control_bot = TelegramClient('control_bot', API_ID, API_HASH)

    @control_bot.on(events.NewMessage(pattern='/start'))
    async def start_control(event):
        if event.sender_id!= OWNER_ID:
            return await event.reply("🌚 البوت ده خاص بصاحبي بس")

        if client and await client.is_user_authorized():
            me = await client.get_me()
            await event.reply(
                "⚔️ **بوت تحفيل المحارب**\n\n"
                f"✅ **الحساب متصل:** {me.first_name}\n"
                f"📱 **الرقم:** {me.phone}\n\n"
                "**الأوامر شغالة من حسابك في أي جروب**\n\n"
                "`.Azef @username` - تحفيل على حد\n"
                "`.Azef` + ريبلاي - تحفيل على الرسالة\n"
                "`.Azef_all` - تحفيل جماعي\n"
                "`.Azef_list` - عدد التحفيلات\n\n"
                f"📊 إجمالي التحفيلات: {db['stats']['total_roasts']}\n"
                f"📝 عدد التحفيلات: {len(ROASTS)}",
                buttons=[
                    [Button.inline("➕ إضافة تحفيلة", b"add_roast_btn")],
                    [Button.inline("🔄 تغيير الحساب", b"change_account")],
                    [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
                ]
            )
        else:
            await event.reply(
                "⚔️ **بوت تحفيل المحارب**\n\n"
                "❌ **مفيش حساب متصل**\n\n"
                "اضغط الزر تحت عشان تضيف حسابك",
                buttons=[
                    [Button.inline("📱 إضافة حساب", b"add_account")],
                    [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
                ]
            )

    @control_bot.on(events.CallbackQuery(data=b"add_roast_btn"))
    async def add_roast_button(event):
        if event.sender_id!= OWNER_ID:
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
        if event.sender_id!= OWNER_ID:
            return

        new_roast = event.text.strip()

        if '{mention}' not in new_roast:
            return await event.reply(
                "❌ **غلط**\n\n"
                "لازم تحط `{mention}` في النص\n"
                "مثال: `يا كسمك {mention} انت تعبان`"
            )

        if not new_roast.startswith('يا كسمك'):
            return await event.reply(
                "❌ **غلط**\n\n"
                "لازم التحفيلة تبدأ بـ `يا كسمك`\n"
                "مثال: `يا كسمك {mention} انت تعبان`"
            )

        ROASTS.append(new_roast)
        save_db(db)
        del add_roast_state[event.sender_id]

        await event.reply(
            f"✅ **تم إضافة التحفيلة**\n\n"
            f"📝 **النص:** {new_roast}\n"
            f"📊 **العدد دلوقتي:** {len(ROASTS)}\n\n"
            "ارجع ابعت /start عشان تشوف القايمة"
        )

    @control_bot.on(events.CallbackQuery(data=b"add_account"))
    async def add_account(event):
        if event.sender_id!= OWNER_ID:
            return

        login_state[event.sender_id] = {'step': 'phone'}
        await event.edit(
            "📱 **إضافة حساب**\n\n"
            "ابعت رقمك مع كود الدولة\n"
            "مثال: `+201234567890`\n\n"
            "⚠️ لازم الرقم اللي هتحفل بيه",
            buttons=[[Button.inline("❌ إلغاء", b"cancel")]]
        )

    @control_bot.on(events.CallbackQuery(data=b"change_account"))
    async def change_account(event):
        if event.sender_id!= OWNER_ID:
            return

        db['session'] = None
        save_db(db)
        global client
        if client:
            await client.disconnect()
        client = None

        await event.edit(
            "✅ **تم حذف الحساب القديم**\n\n"
            "اضغط الزر عشان تضيف حساب جديد",
            buttons=[[Button.inline("📱 إضافة حساب", b"add_account")]]
        )

    @control_bot.on(events.CallbackQuery(data=b"cancel"))
    async def cancel_login(event):
        if event.sender_id in login_state:
            del login_state[event.sender_id]
        await event.edit("❌ تم الإلغاء")

    @control_bot.on(events.NewMessage(func=lambda e: e.sender_id in login_state))
    async def handle_login(event):
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

                await event.reply(
                    f"✅ **بعتلك كود على {phone}**\n\n"
                    "ابعت الكود هنا (5 أرقام)\n"
                    "مثال: `12345`"
                )
            except Exception as e:
                await event.reply(f"❌ خطأ: {str(e)}")
                del login_state[event.sender_id]

        elif state['step'] == 'code':
            code = event.text.strip().replace(' ', '')
            temp_client = state['client']

            try:
                await temp_client.sign_in(state['phone'], code)
                session_str = temp_client.session.save()
                db['session'] = session_str
                save_db(db)

                me = await temp_client.get_me()
                await event.reply(
                    f"✅ **تم إضافة الحساب بنجاح**\n\n"
                    f"👤 **الاسم:** {me.first_name}\n"
                    f"📱 **الرقم:** {me.phone}\n"
                    f"🆔 **اليوزر:** @{me.username}\n\n"
                    "⚔️ **البوت اشتغل خلاص**\n"
                    "روح أي جروب واكتب `.Azef @username`\n\n"
                    "اعد تشغيل البوت عشان يشتغل"
                )
                await temp_client.disconnect()
                del login_state[event.sender_id]

            except SessionPasswordNeededError:
                state['step'] = 'password'
                await event.reply(
                    "🔒 **حسابك عليه تحقق بخطوتين**\n\n"
                    "ابعت كلمة السر بتاعت التحقق بخطوتين"
                )
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
                db['session'] = session_str
                save_db(db)

                me = await temp_client.get_me()
                await event.reply(
                    f"✅ **تم إضافة الحساب بنجاح**\n\n"
                    f"👤 **الاسم:** {me.first_name}\n"
                    f"📱 **الرقم:** {me.phone}\n"
                    f"🆔 **اليوزر:** @{me.username}\n\n"
                    "⚔️ **البوت اشتغل خلاص**\n"
                    "روح أي جروب واكتب `.Azef @username`\n\n"
                    "اعد تشغيل البوت عشان يشتغل"
                )
                await temp_client.disconnect()
                del login_state[event.sender_id]
            except Exception as e:
                await event.reply(f"❌ كلمة السر غلط: {str(e)}")

    await control_bot.start(bot_token=BOT_TOKEN)
    print("✅ بوت التحكم اشتغل")

    if client and await client.is_user_authorized():
        @client.on(events.NewMessage(pattern='\.Azef', outgoing=True))
        async def roast_user(event):
            await event.delete()

            if event.is_reply:
                reply_msg = await event.get_reply_message()
                user = await reply_msg.get_sender()
                mention = f"[{user.first_name}](tg://user?id={user.id})"
                roast = random.choice(ROASTS).format(mention=mention)
                await client.send_message(event.chat_id, roast, parse_mode='md')
                db['stats']['total_roasts'] += 1
                save_db(db)
                return

            parts = event.text.split(' ', 1)
            if len(parts) < 2:
                return await client.send_message(event.chat_id, "❌ استخدم: `.Azef @username` أو اعمل ريبلاي")

            username = parts[1].strip()
            try:
                user = await client.get_entity(username)
                mention = f"[{user.first_name}](tg://user?id={user.id})"
                roast = random.choice(ROASTS).format(mention=mention)
                await client.send_message(event.chat_id, roast, parse_mode='md')
                db['stats']['total_roasts'] += 1
                save_db(db)
            except:
                await client.send_message(event.chat_id, "❌ معرفتش ألاقي اليوزر ده")

        @client.on(events.NewMessage(pattern='\.Azef_all', outgoing=True))
        async def roast_all(event):
            await event.delete()

            if not event.is_group:
                return await client.send_message(event.chat_id, "❌ الأمر ده في الجروبات بس")

            participants = await client.get_participants(event.chat_id)
            roast_targets = [p for p in participants if not p.bot and p.id!= OWNER_ID]

            if not roast_targets:
                return await client.send_message(event.chat_id, "😂 مفيش حد أحفل عليه")

            targets = random.sample(roast_targets, min(3, len(roast_targets)))

            for user in targets:
                mention = f"[{user.first_name}](tg://user?id={user.id})"
                roast = random.choice(ROASTS).format(mention=mention)
                await client.send_message(event.chat_id, roast, parse_mode='md')
                await asyncio.sleep(1)

            db['stats']['total_roasts'] += len(targets)
            save_db(db)

        @client.on(events.NewMessage(pattern='\.Azef_list', outgoing=True))
        async def roast_list(event):
            await event.edit(f"📊 **عدد التحفيلات:** {len(ROASTS)}\n⚔️ **إجمالي:** {db['stats']['total_roasts']}")

        @client.on(events.NewMessage(pattern='\.add_Azef', outgoing=True))
        async def add_roast(event):
            parts = event.text.split(' ', 1)
            if len(parts) < 2:
                return await event.edit("❌ استخدم: `.add_Azef النص`\nمثال: `.add_Azef يا كسمك {mention} شكلك تعبان`")

            new_roast = parts[1].strip()
            if '{mention}' not in new_roast:
                return await event.edit("❌ لازم تحط `{mention}` في النص عشان المنشن يشتغل")

            if not new_roast.startswith('يا كسمك'):
                return await event.edit("❌ لازم التحفيلة تبدأ بـ `يا كسمك`")

            ROASTS.append(new_roast)
            save_db(db)
            await event.edit(f"✅ ضفت التحفيلة\nالعدد دلوقتي: {len(ROASTS)}")

        @client.on(events.NewMessage(pattern='\.start', outgoing=True))
        async def start(event):
            await event.edit(
                "⚔️ **بوت تحفيل المحارب - وضع اليوزر بوت**\n\n"
                "**الأوامر:**\n"
                "`.Azef @username` - تحفيل على حد\n"
                "`.Azef` + ريبلاي - تحفيل على الرسالة\n"
                "`.Azef_all` - تحفيل جماعي\n"
                "`.add_Azef النص` - ضيف تحفيلة\n"
                "`.Azef_list` - عدد التحفيلات\n\n"
                f"📊 إجمالي التحفيلات: {db['stats']['total_roasts']}\n"
                f"👨‍💻 المبرمج: @{DEVELOPER}"
            )

        me = await client.get_me()
        print(f"⚔️ اليوزر بوت شغال على: {me.first_name}")
        await client.run_until_disconnected()
    else:
        print("⏳ مستني تضيف حساب من بوت التحكم")
        await control_bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(run_warrior_userbot())
