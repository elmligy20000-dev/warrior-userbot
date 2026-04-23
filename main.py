import asyncio
import json
import os
import pytz
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
from telethon.errors import UserNotParticipantError, FloodWaitError

# --- الإعدادات الأساسية ---
API_ID = 33595004
API_HASH = 'cbd1066ed026997f2f4a7c4323b7bda7'
BOT_TOKEN = '8676300768:AAFa3i3qwy0vsfa-NAOKWrBgyKWTxXYIjEs'
ADMIN_ID = 154919127
DEVELOPER_USERNAME = "devazf"
MANDATORY_CHANNEL = "@vip6705"
DB_FILE = 'poster_data.json'

# --- أسعار الاشتراك ---
PRICE_PACKAGES = {
    '1_day': {'days': 1, 'price': '0.5$ - 25 جنية', 'label': 'يوم'},
    '7_days': {'days': 7, 'price': '2$ - 70 جنية', 'label': '7 أيام'},
    '15_days': {'days': 15, 'price': '3$ - 100 جنية', 'label': '15 يوم'},
    '30_days': {'days': 30, 'price': '5$ - 120 جنية', 'label': '30 يوم'}
}

PAYMENT_INFO = {
    'vodafone': '01105802898',
    'ltc': 'LZgafAodZxDmjM9Ri51ygZ6dU8UbxE2cPH',
    'ton': 'UQAarGycIaNnngwNAQ1Tek32I3MGroiaeF6p6MxEadimfszt',
    'usdt': 'TWunFGpcDDc63GTDdNxyDHjZ4VdPS6AsMh'
}

# --- نظام الحفظ ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'welcome_enabled' not in data:
                data['welcome_enabled'] = True
            if 'welcome_text' not in data:
                data['welcome_text'] = '🌟 **أهلاً بيك في بوت النشر المطور**\n\n🚀 أسرع بوت نشر تلقائي على تليجرام\n⚡ نشر في مئات الجروبات بضغطة زر\n💎 مميزات احترافية\n\n👇 اختار من الأزرار تحت'
            if 'welcome_photo' not in data:
                data['welcome_photo'] = 'https://telegra.ph/file/8f8b4e1c4e8e8.jpg'
            return data
    return {
        'session': None,
        'groups': {},
        'messages': ['', '', '', ''],
        'current_msg': 0,
        'msg_stats': [0, 0, 0, 0],
        'sleep_time': 60,
        'msg_delay': 5,
        'send_all': False,
        'subs': {str(ADMIN_ID): '2099-01-01'},
        'admins': [ADMIN_ID],
        'auto_reply': True,
        'auto_reply_text': f'تفضل خاص @{DEVELOPER_USERNAME}',
        'pending': {},
        'welcomed': [],
        'welcome_enabled': True,
        'welcome_text': '🌟 **أهلاً بيك في بوت النشر المطور**\n\n🚀 أسرع بوت نشر تلقائي على تليجرام\n⚡ نشر في مئات الجروبات بضغطة زر\n💎 مميزات احترافية\n\n👇 اختار من الأزرار تحت',
        'welcome_photo': 'https://telegra.ph/file/8f8b4e1c4e8e8e8e8.jpg'
    }

def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()
bot = TelegramClient('PosterBot', API_ID, API_HASH)
is_posting = False
waiting_for = {}

# --- دوال مساعدة ---
def is_admin(uid):
    return uid in db['admins']

def is_sub(uid):
    if is_admin(uid):
        return True
    if str(uid) in db['subs']:
        try:
            expiry = datetime.strptime(db['subs'][str(uid)], '%Y-%m-%d')
            return expiry > datetime.now()
        except:
            pass
    return False

def get_time():
    tz = pytz.timezone('Africa/Cairo')
    return datetime.now(tz).strftime('\n🕐 %I:%M %p - %d/%m/%Y')

# --- القوائم ---
def main_menu(uid):
    btns = [
        [Button.inline("🔑 ربط حساب", b"login")],
        [Button.inline("⚙️ الإعدادات", b"settings")],
        [Button.inline("🚀 بدء النشر", b"start")]
    ]
    if not is_sub(uid):
        btns.append([Button.inline("💳 اشترك", b"pay_menu")])
    if is_admin(uid):
        btns.append([Button.inline("👑 لوحة الأدمن", b"admin")])
    return btns

def settings_menu(uid):
    status = "🟢 مربوط" if db['session'] else "🔴 غير مربوط"
    mode = "📤 الكل" if db['send_all'] else "🔄 تدوير"
    reply = "✅ مفعل" if db['auto_reply'] else "❌ معطل"
    welcome = "✅ مفعل" if db['welcome_enabled'] else "❌ معطل"

    btns = [
        [Button.inline(status, b"none")],
        [Button.inline(f"👥 الجروبات: {len(db['groups'])}", b"show_groups")],
        [Button.inline("📥 جلب تلقائي", b"fetch"), Button.inline("➕ إضافة جروب", b"add_group")],
        [Button.inline("🗑️ حذف جروب", b"delete_group")],
        [Button.inline(f"📩 رسالة 1 ({db['msg_stats'][0]})", b"msg_0"), Button.inline(f"📩 رسالة 2 ({db['msg_stats'][1]})", b"msg_1")],
        [Button.inline(f"📩 رسالة 3 ({db['msg_stats'][2]})", b"msg_2"), Button.inline(f"📩 رسالة 4 ({db['msg_stats'][3]})", b"msg_3")],
        [Button.inline(f"⏱️ وقت الجروب: {db['sleep_time']}ث", b"set_sleep"), Button.inline(f"⏱️ وقت الرسالة: {db['msg_delay']}ث", b"set_delay")],
        [Button.inline(mode, b"toggle_mode"), Button.inline(f"💬 الرد: {reply}", b"toggle_reply")],
    ]

    # أزرار الترحيب تظهر للأدمن فقط
    if is_admin(uid):
        btns.append([Button.inline(f"👋 الترحيب: {welcome}", b"toggle_welcome"), Button.inline("🖼️ صورة الترحيب", b"change_photo")])
        btns.append([Button.inline("✏️ نص الترحيب", b"edit_welcome")])

    btns.append([Button.inline("🔴 إيقاف", b"stop"), Button.inline("🟢 بدء", b"start")])
    btns.append([Button.inline("🔙 رجوع", b"back")])

    return btns

def pay_menu():
    btns = []
    for key, pkg in PRICE_PACKAGES.items():
        btns.append([Button.inline(f"{pkg['label']} - {pkg['price']}", f"pay_{key}".encode())])
    btns.append([Button.inline("🔙 رجوع", b"back")])
    return btns

# --- أوامر البوت ---
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id

    # اشتراك إجباري
    if MANDATORY_CHANNEL and not is_admin(uid):
        try:
            await bot.get_permissions(MANDATORY_CHANNEL, uid)
        except UserNotParticipantError:
            btns = [[Button.url("📢 اشترك الآن", f"https://t.me/{MANDATORY_CHANNEL.replace('@', '')}")]]
            return await event.reply(f"⚠️ **لازم تشترك في القناة أولاً**\n\n{MANDATORY_CHANNEL}\n\nبعد الاشتراك ارجع اعمل /start", buttons=btns)
        except:
            pass

    # الترحيب بالصورة للأدمن فقط
    if db['welcome_enabled'] and is_admin(uid) and str(uid) not in db['welcomed']:
        db['welcomed'].append(str(uid))
        save_db()

        welcome_btns = [
            [Button.inline("⚙️ الإعدادات", b"settings")],
            [Button.inline("🚀 بدء النشر", b"start")],
            [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER_USERNAME}")]
        ]

        try:
            await bot.send_file(
                uid,
                file=db['welcome_photo'],
                caption=f"{db['welcome_text']}{get_time()}",
                buttons=welcome_btns
            )
            return
        except:
            await event.reply(f"{db['welcome_text']}{get_time()}", buttons=welcome_btns)
            return

    if not is_sub(uid):
        btns = [[Button.inline("💳 اشترك الآن", b"pay_menu")]]
        return await event.reply(f"⚠️ **اشتراكك غير مفعل**\n🆔 ايديك: `{uid}`{get_time()}", buttons=btns)

    await event.reply(f"🚀 **بوت النشر التلقائي**{get_time()}", buttons=main_menu(uid))

@bot.on(events.CallbackQuery)
async def callbacks(event):
    uid = event.sender_id
    data = event.data

    if data == b"back":
        await event.edit("🔙 القائمة الرئيسية", buttons=main_menu(uid))
        return

    if data == b"pay_menu":
        await event.edit("💳 **اختر الباقة:**", buttons=pay_menu())
        return

    if data.startswith(b'pay_'):
        pkg_key = data.decode().replace('pay_', '')
        pkg = PRICE_PACKAGES.get(pkg_key)
        if not pkg:
            return await event.answer("❌ باقة خاطئة", alert=True)

        waiting_for[uid] = f'proof_{pkg_key}'
        msg = f"💳 **الدفع**\n💵 {pkg['price']}\n\n📱 فودافون: `{PAYMENT_INFO['vodafone']}`\n💵 USDT: `{PAYMENT_INFO['usdt']}`\n\n📸 ابعت سكرين التحويل"
        await event.edit(msg)
        return

    if data == b"settings":
        if not is_sub(uid):
            return await event.answer("❌ لازم تشترك", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=settings_menu(uid))
        return

    if data == b"fetch":
        if not db['session']:
            return await event.answer("❌ اربط حساب أول", alert=True)

        await event.answer("⏳ جاري الجلب...", alert=False)
        client = TelegramClient(StringSession(db['session']), API_ID, API_HASH)
        await client.connect()

        groups = {}
        async for dialog in client.iter_dialogs():
            if isinstance(dialog.entity, (Channel, Chat)) and getattr(dialog.entity, 'megagroup', False):
                gid = f"-100{dialog.entity.id}"
                groups[gid] = dialog.entity.title

        await client.disconnect()
        db['groups'] = groups
        save_db()
        await event.edit(f"✅ تم جلب {len(groups)} جروب", buttons=settings_menu(uid))
        return

    if data == b"show_groups":
        if not db['groups']:
            return await event.answer("❌ مفيش جروبات", alert=True)
        text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(db['groups'].values())])
        await event.answer(text[:200], alert=True)
        return

    if data == b"add_group":
        waiting_for[uid] = 'add_group'
        await event.edit("➕ ابعت رابط الجروب أو الايدي\n❌ /cancel للالغاء")
        return

    if data == b"delete_group":
        if not db['groups']:
            return await event.answer("❌ مفيش جروبات مضافة", alert=True)
        waiting_for[uid] = 'delete_group'
        groups_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(db['groups'].values())])
        await event.edit(f"🗑️ **حذف جروب**\n\nاختر رقم الجروب:\n{groups_list}\n\n❌ /cancel للالغاء")
        return

    if data.startswith(b'msg_'):
        idx = int(data.decode().split('_')[1])
        waiting_for[uid] = f'set_msg_{idx}'
        current = db['messages'][idx] or 'فاضي'
        await event.edit(f"✏️ **الرسالة {idx+1}**\nالحالية: {current}\n\nابعت النص الجديد:")
        return

    if data == b"set_sleep":
        waiting_for[uid] = 'set_sleep'
        await event.edit(f"⏱️ الوقت الحالي: {db['sleep_time']}ث\nابعت الوقت الجديد بالثواني:")
        return

    if data == b"set_delay":
        waiting_for[uid] = 'set_delay'
        await event.edit(f"⏱️ الوقت الحالي: {db['msg_delay']}ث\nابعت الوقت الجديد:")
        return

    if data == b"toggle_mode":
        db['send_all'] = not db['send_all']
        save_db()
        await event.answer("✅ تم التغيير", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=settings_menu(uid))
        return

    if data == b"toggle_reply":
        db['auto_reply'] = not db['auto_reply']
        save_db()
        await event.answer("✅ تم التغيير", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=settings_menu(uid))
        return

    if data == b"toggle_welcome":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        db['welcome_enabled'] = not db['welcome_enabled']
        save_db()
        status = "مفعل ✅" if db['welcome_enabled'] else "معطل ❌"
        await event.answer(f"الترحيب: {status}", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=settings_menu(uid))
        return

    if data == b"change_photo":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        waiting_for[uid] = 'change_photo'
        await event.edit(f"🖼️ **الصورة الحالية:**\n{db['welcome_photo']}\n\n📸 ابعت صورة جديدة أو رابط مباشر\n❌ /cancel للالغاء")
        return

    if data == b"edit_welcome":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        waiting_for[uid] = 'edit_welcome'
        await event.edit(f"✏️ **النص الحالي:**\n{db['welcome_text']}\n\nابعت النص الجديد:")
        return

    if data == b"start":
        await start_posting(event)
        return

    if data == b"stop":
        global is_posting
        is_posting = False
        await event.answer("🔴 تم الإيقاف", alert=True)
        return

    if data == b"login":
        waiting_for[uid] = 'phone'
        await event.edit("📱 ابعت رقمك مع كود الدولة\nمثال: +201234567890")
        return

@bot.on(events.NewMessage)
async def handle_msg(event):
    uid = event.sender_id
    text = event.raw_text.strip()

    if text == "/cancel":
        if uid in waiting_for:
            del waiting_for[uid]
        return await event.reply("✅ تم الإلغاء")

    step = waiting_for.get(uid)

    if step == 'change_photo' and is_admin(uid):
        if event.photo:
            path = await event.download_media(file="welcome.jpg")
            db['welcome_photo'] = path
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم تحديث الصورة\n📁 {path}")
        elif text.startswith('http'):
            db['welcome_photo'] = text
            save_db()
            del waiting_for[uid]
            await event.reply("✅ تم تحديث رابط الصورة")
        else:
            await event.reply("❌ ابعت صورة أو رابط")
        return

    if step == 'edit_welcome' and is_admin(uid):
        db['welcome_text'] = text
        save_db()
        del waiting_for[uid]
        await event.reply(f"✅ تم تحديث نص الترحيب:\n{text}")
        return

    if step == 'add_group':
        try:
            if text.startswith('https://t.me/'):
                username = text.split('/')[-1]
                entity = await bot.get_entity(username)
                gid = f"-100{entity.id}"
                name = entity.title
            else:
                gid = text
                entity = await bot.get_entity(int(gid))
                name = entity.title

            db['groups'][gid] = name
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم إضافة: {name}")
        except:
            await event.reply("❌ خطأ. تأكد ان البوت في الجروب")
        return

    if step == 'delete_group':
        try:
            idx = int(text) - 1
            groups_list = list(db['groups'].items())
            if 0 <= idx < len(groups_list):
                gid, name = groups_list[idx]
                del db['groups'][gid]
                save_db()
                del waiting_for[uid]
                await event.reply(f"✅ تم حذف: {name}")
            else:
                await event.reply("❌ رقم غلط")
        except:
            await event.reply("❌ ابعت رقم صحيح")
        return

    if step and step.startswith('set_msg_'):
        idx = int(step.split('_')[2])
        db['messages'][idx] = text
        save_db()
        del waiting_for[uid]
        await event.reply(f"✅ تم حفظ الرسالة {idx+1}")
        return

    if step == 'set_sleep':
        try:
            db['sleep_time'] = int(text)
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم التحديث: {text}ث")
        except:
            await event.reply("❌ رقم صحيح فقط")
        return

    if step == 'set_delay':
        try:
            db['msg_delay'] = int(text)
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم التحديث: {text}ث")
        except:
            await event.reply("❌ رقم صحيح فقط")
        return

    if step and step.startswith('proof_'):
        pkg_key = step.replace('proof_', '')
        db['pending'][str(uid)] = {'pkg': pkg_key, 'text': text, 'time': str(datetime.now())}
        save_db()
        del waiting_for[uid]
        await event.reply("✅ تم الإرسال. هيتم المراجعة قريباً")
        await bot.send_message(ADMIN_ID, f"💳 **طلب اشتراك جديد**\n👤 {uid}\n📦 {PRICE_PACKAGES[pkg_key]['label']}\n📝 {text}")
        return

# --- النشر التلقائي ---
async def start_posting(event):
    global is_posting
    uid = event.sender_id

    if not db['session']:
        return await event.answer("❌ اربط حساب أول", alert=True)
    if not db['groups']:
        return await event.answer("❌ ضيف جروبات أول", alert=True)
    if not any(db['messages']):
        return await event.answer("❌ ضيف رسائل أول", alert=True)

    if is_posting:
        return await event.answer("⚠️ النشر شغال بالفعل", alert=True)

    is_posting = True
    await event.answer("🚀 بدأ النشر", alert=True)

    client = TelegramClient(StringSession(db['session']), API_ID, API_HASH)
    await client.start()

    msgs = [m for m in db['messages'] if m]

    while is_posting:
        for gid in db['groups']:
            if not is_posting:
                break

            try:
                if db['send_all']:
                    for i, msg in enumerate(msgs):
                        await client.send_message(int(gid), msg)
                        db['msg_stats'][i] += 1
                        await asyncio.sleep(db['msg_delay'])
                else:
                    msg = msgs[db['current_msg']]
                    await client.send_message(int(gid), msg)
                    db['msg_stats'][db['current_msg']] += 1
                    db['current_msg'] = (db['current_msg'] + 1) % len(msgs)

                save_db()
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except:
                pass

            await asyncio.sleep(db['sleep_time'])

    await client.disconnect()
    await bot.send_message(uid, "🔴 توقف النشر")

# --- الرد التلقائي ---
@bot.on(events.NewMessage(incoming=True))
async def auto_reply(event):
    if not db['auto_reply'] or not db['session']:
        return
    if not event.is_group:
        return

    try:
        me = await bot.get_me()
        if f"@{me.username}" in (event.raw_text or "").lower():
            await event.reply(db['auto_reply_text'])
    except:
        pass

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ البوت شغال")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
