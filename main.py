import asyncio
import json
import os
import pytz
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
from telethon.errors import UserNotParticipantError, FloodWaitError, PhoneCodeInvalidError

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
    '1_day': {'days': 1, 'price': '0.5$ - 25 جنية', 'label': 'يوم واحد'},
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
            defaults = {
                'welcome_enabled': True,
                'welcome_text': '🌟 **أهلاً بيك في بوت النشر المطور**\n\n🚀 أسرع بوت نشر تلقائي على تليجرام\n⚡ نشر في مئات الجروبات بضغطة زر\n💎 مميزات احترافية\n\n👇 اختار من الأزرار تحت',
                'welcome_photo': 'https://telegra.ph/file/8f8b4e1c4e8e8.jpg',
                'trial_users': [],
                'stats': {'total_sent': 0, 'start_time': str(datetime.now())},
                'banned_groups': []
            }
            for key, val in defaults.items():
                if key not in data:
                    data[key] = val
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
        'welcome_photo': 'https://telegra.ph/file/8f8b4e1c4e8e8e8e8.jpg',
        'trial_users': [],
        'stats': {'total_sent': 0, 'start_time': str(datetime.now())},
        'banned_groups': []
    }

def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()
bot = TelegramClient('PosterBot', API_ID, API_HASH)
is_posting = False
waiting_for = {}
login_sessions = {}

# --- دوال مساعدة ---
def is_admin(uid):
    return uid in db['admins']

def is_main_admin(uid):
    return uid == ADMIN_ID

def is_sub(uid):
    if is_admin(uid):
        return True
    if str(uid) in db['subs']:
        try:
            expiry = datetime.strptime(db['subs'][str(uid)], '%Y-%m-%d %H:%M')
            return expiry > datetime.now()
        except:
            try:
                expiry = datetime.strptime(db['subs'][str(uid)], '%Y-%m-%d')
                return expiry > datetime.now()
            except:
                pass
    if str(uid) in db['trial_users']:
        return True
    return False

def get_time():
    tz = pytz.timezone('Africa/Cairo')
    return datetime.now(tz).strftime('\n🕐 %I:%M %p - %d/%m/%Y')

def get_uptime():
    start = datetime.strptime(db['stats']['start_time'], '%Y-%m-%d %H:%M:%S.%f')
    diff = datetime.now() - start
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    return f"{days} يوم, {hours} ساعة, {minutes} دقيقة"

# --- القوائم ---
def main_menu(uid):
    btns = [
        [Button.inline("🔑 ربط حساب", b"login")],
        [Button.inline("⚙️ الإعدادات", b"settings")],
        [Button.inline("📊 الإحصائيات", b"stats")]
    ]

    if not is_sub(uid) and str(uid) not in db['trial_users']:
        btns.append([Button.inline("🎁 تجربة مجانية 1 ساعة", b"free_trial")])

    if not is_sub(uid):
        btns.append([Button.inline("💳 اشترك الآن", b"pay_menu")])

    if is_admin(uid):
        btns.append([Button.inline("👑 لوحة الأدمن", b"admin")])

    btns.append([Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER_USERNAME}")])
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
        [Button.inline("🗑️ حذف جروب", b"delete_group"), Button.inline("🚫 الجروبات المحظورة", b"banned")],
        [Button.inline(f"📩 رسالة 1 ({db['msg_stats'][0]})", b"msg_0"), Button.inline(f"📩 رسالة 2 ({db['msg_stats'][1]})", b"msg_1")],
        [Button.inline(f"📩 رسالة 3 ({db['msg_stats'][2]})", b"msg_2"), Button.inline(f"📩 رسالة 4 ({db['msg_stats'][3]})", b"msg_3")],
        [Button.inline(f"⏱️ وقت الجروب: {db['sleep_time']}ث", b"set_sleep"), Button.inline(f"⏱️ وقت الرسالة: {db['msg_delay']}ث", b"set_delay")],
        [Button.inline(mode, b"toggle_mode"), Button.inline(f"💬 الرد: {reply}", b"toggle_reply")],
    ]

    if is_admin(uid):
        btns.append([Button.inline(f"👋 الترحيب: {welcome}", b"toggle_welcome"), Button.inline("🖼️ صورة الترحيب", b"change_photo")])
        btns.append([Button.inline("✏️ نص الترحيب", b"edit_welcome"), Button.inline("💬 نص الرد", b"edit_reply")])

    btns.append([Button.inline("🔴 إيقاف النشر", b"stop"), Button.inline("🟢 بدء النشر", b"start")])
    btns.append([Button.inline("🔙 رجوع", b"back")])

    return btns

def admin_panel(uid):
    return [
        [Button.inline("➕ إضافة اشتراك", b"add_sub"), Button.inline("➖ إزالة اشتراك", b"remove_sub")],
        [Button.inline("👥 قائمة المشتركين", b"list_subs"), Button.inline("📋 الطلبات المعلقة", b"pending")],
        [Button.inline("📢 إذاعة", b"broadcast"), Button.inline("🔄 إعادة تشغيل", b"restart")],
        [Button.inline("🔙 رجوع", b"back")]
    ]

def pay_menu():
    btns = []
    for key, pkg in PRICE_PACKAGES.items():
        btns.append([Button.inline(f"{pkg['label']} - {pkg['price']}", f"pay_{key}".encode())])
    btns.append([Button.inline("🔙 رجوع", b"back")])
    return btns

def payment_methods(pkg_key):
    pkg = PRICE_PACKAGES[pkg_key]
    return [
        [Button.inline(f"📱 فودافون كاش", f"method_vodafone_{pkg_key}".encode())],
        [Button.inline(f"💎 USDT TRC20", f"method_usdt_{pkg_key}".encode())],
        [Button.inline(f"💎 Litecoin", f"method_ltc_{pkg_key}".encode())],
        [Button.inline(f"💎 Toncoin", f"method_ton_{pkg_key}".encode())],
        [Button.inline("🔙 رجوع", b"pay_menu")]
    ]

# --- أوامر البوت ---
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id

    if MANDATORY_CHANNEL and not is_admin(uid):
        try:
            await bot.get_permissions(MANDATORY_CHANNEL, uid)
        except UserNotParticipantError:
            btns = [[Button.url("📢 اشترك الآن", f"https://t.me/{MANDATORY_CHANNEL.replace('@', '')}")]]
            return await event.reply(f"⚠️ **لازم تشترك في القناة أولاً**\n\n{MANDATORY_CHANNEL}\n\nبعد الاشتراك ارجع اعمل /start", buttons=btns)
        except:
            pass

    if db['welcome_enabled'] and is_admin(uid) and str(uid) not in db['welcomed']:
        db['welcomed'].append(str(uid))
        save_db()

        welcome_btns = [
            [Button.inline("⚙️ الإعدادات", b"settings")],
            [Button.inline("🚀 بدء النشر", b"start")],
            [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER_USERNAME}")]
        ]

        try:
            await bot.send_file(uid, file=db['welcome_photo'], caption=f"{db['welcome_text']}{get_time()}", buttons=welcome_btns)
            return
        except:
            await event.reply(f"{db['welcome_text']}{get_time()}", buttons=welcome_btns)
            return

    if not is_sub(uid):
        btns = []
        if str(uid) not in db['trial_users']:
            btns.append([Button.inline("🎁 تجربة مجانية 1 ساعة", b"free_trial")])
        btns.append([Button.inline("💳 اشترك الآن", b"pay_menu")])
        btns.append([Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER_USERNAME}")])
        return await event.reply(f"⚠️ **اشتراكك غير مفعل**\n🆔 ايديك: `{uid}`{get_time()}", buttons=btns)

    await event.reply(f"🚀 **بوت النشر التلقائي المطور**{get_time()}", buttons=main_menu(uid))

@bot.on(events.NewMessage(pattern='/activate'))
async def activate_sub(event):
    if not is_admin(event.sender_id):
        return

    try:
        parts = event.raw_text.split()
        user_id = parts[1]
        pkg_key = parts[2]
        pkg = PRICE_PACKAGES[pkg_key]

        expiry = datetime.now() + timedelta(days=pkg['days'])
        db['subs'][user_id] = expiry.strftime('%Y-%m-%d')

        if user_id in db['pending']:
            del db['pending'][user_id]
        if user_id in db['trial_users']:
            db['trial_users'].remove(user_id)

        save_db()
        await event.reply(f"✅ تم تفعيل اشتراك `{user_id}`\n📦 {pkg['label']}\n📅 ينتهي: {expiry.strftime('%Y-%m-%d')}")

        try:
            await bot.send_message(int(user_id), f"🎉 **تم تفعيل اشتراكك!**\n📦 الباقة: {pkg['label']}\n⏰ المدة: {pkg['days']} يوم\n📅 ينتهي: {expiry.strftime('%Y-%m-%d')}{get_time()}")
        except:
            pass
    except:
        await event.reply("❌ الاستخدام: `/activate user_id package_key`\nمثال: `/activate 123456789 7_days`")

@bot.on(events.CallbackQuery)
async def callbacks(event):
    global is_posting
    uid = event.sender_id
    data = event.data

    if data == b"back":
        await event.edit("🔙 القائمة الرئيسية", buttons=main_menu(uid))
        return

    if data == b"free_trial":
        if str(uid) in db['trial_users']:
            return await event.answer("❌ استخدمت التجربة قبل كده", alert=True)
        if is_sub(uid):
            return await event.answer("✅ انت مشترك بالفعل", alert=True)

        expiry = datetime.now() + timedelta(hours=1)
        db['trial_users'].append(str(uid))
        db['subs'][str(uid)] = expiry.strftime('%Y-%m-%d %H:%M')
        save_db()
        await event.edit(f"🎁 **تم تفعيل التجربة المجانية**\n⏰ صالحة لمدة ساعة\n\nارجع اعمل /start", buttons=main_menu(uid))
        return

    if data == b"pay_menu":
        await event.edit("💳 **اختر الباقة المناسبة:**", buttons=pay_menu())
        return

    if data.startswith(b'pay_'):
        pkg_key = data.decode().replace('pay_', '')
        await event.edit(f"💳 **اختر طريقة الدفع:**", buttons=payment_methods(pkg_key))
        return

    if data.startswith(b'method_'):
        parts = data.decode().split('_')
        method = parts[1]
        pkg_key = '_'.join(parts[2:])
        pkg = PRICE_PACKAGES[pkg_key]

        waiting_for[uid] = f'proof_{pkg_key}_{method}'

        if method == 'vodafone':
            info = f"📱 **فودافون كاش**\n💵 المبلغ: {pkg['price']}\n📞 الرقم: `{PAYMENT_INFO['vodafone']}`"
        elif method == 'usdt':
            info = f"💵 **USDT TRC20**\n💵 المبلغ: {pkg['price']}\n📬 المحفظة:\n`{PAYMENT_INFO['usdt']}`"
        elif method == 'ltc':
            info = f"💎 **Litecoin**\n💵 المبلغ: {pkg['price']}\n📬 المحفظة:\n`{PAYMENT_INFO['ltc']}`"
        elif method == 'ton':
            info = f"💎 **Toncoin**\n💵 المبلغ: {pkg['price']}\n📬 المحفظة:\n`{PAYMENT_INFO['ton']}`"

        msg = f"{info}\n\n📸 **بعد التحويل:**\nابعت سكرين + رقم/هاش العملية\n\n⏰ مدة الباقة: {pkg['label']}"
        await event.edit(msg, buttons=[[Button.inline("🔙 رجوع", b"pay_menu")]])
        return

    if data == b"settings":
        if not is_sub(uid):
            return await event.answer("❌ لازم تشترك أول", alert=True)
        await event.edit("⚙️ **الإعدادات المتقدمة**", buttons=settings_menu(uid))
        return

    if data == b"stats":
        total_sent = db['stats']['total_sent']
        uptime = get_uptime()
        active_groups = len([g for g in db['groups'] if g not in db['banned_groups']])

        msg = f"📊 **إحصائيات البوت**\n\n"
        msg += f"⏱️ مدة التشغيل: `{uptime}`\n"
        msg += f"📤 إجمالي الرسائل: `{total_sent}`\n"
        msg += f"👥 الجروبات النشطة: `{active_groups}`\n"
        msg += f"🚫 الجروبات المحظورة: `{len(db['banned_groups'])}`\n"
        msg += f"💬 المشتركين: `{len(db['subs'])}`\n{get_time()}"

        await event.answer(msg, alert=True)
        return

    if data == b"fetch":
        if not db['session']:
            return await event.answer("❌ اربط حساب أول", alert=True)

        await event.answer("⏳ جاري الجلب...", alert=False)
        try:
            client = TelegramClient(StringSession(db['session']), API_ID, API_HASH)
            await client.connect()

            groups = {}
            async for dialog in client.iter_dialogs():
                if isinstance(dialog.entity, (Channel, Chat)) and getattr(dialog.entity, 'megagroup', False):
                    gid = f"-100{dialog.entity.id}"
                    if gid not in db['banned_groups']:
                        groups[gid] = dialog.entity.title

            await client.disconnect()
            db['groups'] = groups
            save_db()
            await event.edit(f"✅ تم جلب {len(groups)} جروب", buttons=settings_menu(uid))
        except Exception as e:
            await event.edit(f"❌ خطأ: {e}", buttons=settings_menu(uid))
        return

    if data == b"show_groups":
        if not db['groups']:
            return await event.answer("❌ مفيش جروبات", alert=True)
        active = [name for gid, name in db['groups'].items() if gid not in db['banned_groups']]
        text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(active[:30])])
        if len(active) > 30:
            text += f"\n\n... و {len(active)-30} جروب تاني"
        await event.answer(text, alert=True)
        return

    if data == b"add_group":
        waiting_for[uid] = 'add_group'
        await event.edit("➕ **إضافة جروب يدوي**\n\nابعت رابط الجروب أو الايدي:\n`https://t.me/groupname` أو `-1001234567890`\n\n❌ /cancel للالغاء")
        return

    if data == b"delete_group":
        if not db['groups']:
            return await event.answer("❌ مفيش جروبات مضافة", alert=True)
        waiting_for[uid] = 'delete_group'
        groups_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(db['groups'].values())])
        await event.edit(f"🗑️ **حذف جروب**\n\nاختر رقم الجروب:\n{groups_list[:3000]}\n\n❌ /cancel للالغاء")
        return

    if data == b"banned":
        if not db['banned_groups']:
            return await event.answer("✅ مفيش جروبات محظورة", alert=True)
        text = "\n".join([f"{i+1}. {gid}" for i, gid in enumerate(db['banned_groups'][:20])])
        await event.answer(f"🚫 **الجروبات المحظورة:**\n{text}", alert=True)
        return

    if data.startswith(b'msg_'):
        idx = int(data.decode().split('_')[1])
        waiting_for[uid] = f'set_msg_{idx}'
        current = db['messages'][idx] or 'فاضي'
        await event.edit(f"✏️ **الرسالة {idx+1}**\n\nالحالية:\n{current[:500]}\n\nابعت النص الجديد:")
        return

    if data == b"set_sleep":
        waiting_for[uid] = 'set_sleep'
        await event.edit(f"⏱️ **وقت الانتظار بين الجروبات**\n\nالحالي: {db['sleep_time']} ثانية\n\nابعت الوقت الجديد (بالثواني):")
        return

    if data == b"set_delay":
        waiting_for[uid] = 'set_delay'
        await event.edit(f"⏱️ **وقت الانتظار بين الرسائل**\n\nالحالي: {db['msg_delay']} ثانية\n\nابعت الوقت الجديد:")
        return

    if data == b"toggle_mode":
        db['send_all'] = not db['send_all']
        save_db()
        mode = "وضع الكل 📤" if db['send_all'] else "وضع التدوير 🔄"
        await event.answer(f"✅ {mode}", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=settings_menu(uid))
        return

    if data == b"toggle_reply":
        db['auto_reply'] = not db['auto_reply']
        save_db()
        status = "مفعل ✅" if db['auto_reply'] else "معطل ❌"
        await event.answer(f"الرد التلقائي: {status}", alert=True)
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

    if data == b"edit_reply":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        waiting_for[uid] = 'edit_reply'
        await event.edit(f"💬 **نص الرد الحالي:**\n{db['auto_reply_text']}\n\nابعت النص الجديد:")
        return

    if data == b"start":
        await start_posting(event)
        return

    if data == b"stop":
        is_posting = False
        await event.answer("🔴 تم إيقاف النشر", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=settings_menu(uid))
        return

    if data == b"login":
        if uid in login_sessions:
            del login_sessions[uid]
        waiting_for[uid] = 'phone'
        await event.edit("📱 **ربط حساب**\n\nابعت رقمك مع كود الدولة\nمثال: `+201234567890`\n\n❌ /cancel للالغاء")
        return

    if data == b"admin":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        await event.edit("👑 **لوحة تحكم الأدمن**", buttons=admin_panel(uid))
        return

    if data == b"add_sub":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        waiting_for[uid] = 'add_sub_id'
        await event.edit("➕ **إضافة اشتراك**\n\nابعت ايدي المستخدم:")
        return

    if data == b"remove_sub":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        waiting_for[uid] = 'remove_sub'
        await event.edit("➖ **إزالة اشتراك**\n\nابعت ايدي المستخدم:")
        return

    if data == b"list_subs":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        subs_list = "\n".join([f"{i+1}. `{uid}` - {date}" for i, (uid, date) in enumerate(db['subs'].items())])
        await event.answer(f"👥 **المشتركين: {len(db['subs'])}**\n\n{subs_list[:3800]}", alert=True)
        return

    if data == b"pending":
        if not is_admin(uid):
            return await event.answer("❌ للادمن فقط", alert=True)
        if not db['pending']:
            return await event.answer("✅ مفيش طلبات معلقة", alert=True)
        text = "\n\n".join([f"👤 `{uid}`\n📦 {PRICE_PACKAGES[d['pkg']]['label']}\n💳 {d['method']}\n📝 {d['text'][:100]}" for uid, d in db['pending'].items()])
        await event.answer(f"📋 **الطلبات المعلقة:**\n\n{text[:3800]}", alert=True)
        return

    if data == b"broadcast":
        if not is_main_admin(uid):
            return await event.answer("❌ للمطور فقط", alert=True)
        waiting_for[uid] = 'broadcast'
        await event.edit("📢 **إذاعة للجميع**\n\nابعت الرسالة اللي عايز تبعتها لكل المشتركين:")
        return

    if data == b"restart":
        if not is_main_admin(uid):
            return await event.answer("❌ للمطور فقط", alert=True)
        await event.answer("🔄 جاري إعادة التشغيل...", alert=True)
        os._exit(0)
        return

@bot.on(events.NewMessage)
async def handle_msg(event):
    global is_posting
    uid = event.sender_id
    text = event.raw_text.strip()

    if text == "/cancel":
        if uid in waiting_for:
            del waiting_for[uid]
        if uid in login_sessions:
            del login_sessions[uid]
        return await event.reply("✅ تم الإلغاء")

    step = waiting_for.get(uid)

    if step == 'phone':
        try:
            phone = text
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            await client.send_code_request(phone)
            login_sessions[uid] = {'phone': phone, 'client': client}
            waiting_for[uid] = 'code'
            await event.reply("📨 **تم إرسال الكود**\n\nابعت الكود اللي وصلك:\nمثال: `12345`")
        except Exception as e:
            await event.reply(f"❌ خطأ: {e}")
            if uid in login_sessions:
                del login_sessions[uid]
            del waiting_for[uid]
        return

    if step == 'code':
        try:
            code = text.replace(' ', '')
            session_data = login_sessions[uid]
            client = session_data['client']
            await client.sign_in(session_data['phone'], code)
            string_session = client.session.save()
            db['session'] = string_session
            save_db()
            await client.disconnect()
            del login_sessions[uid]
            del waiting_for[uid]
            await event.reply("✅ **تم ربط الحساب بنجاح!**\n\nتقدر دلوقتي تجلب الجروبات وتبدأ النشر")
        except PhoneCodeInvalidError:
            await event.reply("❌ الكود غلط. ابعت الكود الصحيح:")
        except Exception as e:
            if "2FA" in str(e) or "password" in str(e).lower():
                waiting_for[uid] = 'password'
                await event.reply("🔐 **الحساب محمي بكلمة سر**\n\nابعت كلمة السر:")
            else:
                await event.reply(f"❌ خطأ: {e}")
                if uid in login_sessions:
                    del login_sessions[uid]
                del waiting_for[uid]
        return

    if step == 'password':
        try:
            password = text
            session_data = login_sessions[uid]
            client = session_data['client']
            await client.sign_in(password=password)
            string_session = client.session.save()
            db['session'] = string_session
            save_db()
            await client.disconnect()
            del login_sessions[uid]
            del waiting_for[uid]
            await event.reply("✅ **تم ربط الحساب بنجاح!**")
        except Exception as e:
            await event.reply(f"❌ كلمة السر غلط: {e}")
        return

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
        await event.reply(f"✅ تم تحديث نص الترحيب")
        return

    if step == 'edit_reply' and is_admin(uid):
        db['auto_reply_text'] = text
        save_db()
        del waiting_for[uid]
        await event.reply(f"✅ تم تحديث نص الرد التلقائي")
        return

    if step == 'add_group':
        try:
            if text.startswith('https://t.me/'):
                username = text.split('/')[-1].split('?')[0]
                entity = await bot.get_entity(username)
                gid = f"-100{entity.id}"
                name = entity.title
            elif text.startswith('-100'):
                gid = text
                entity = await bot.get_entity(int(gid))
                name = entity.title
            else:
                return await event.reply("❌ رابط أو ايدي غير صحيح")

            if gid in db['banned_groups']:
                db['banned_groups'].remove(gid)

            db['groups'][gid] = name
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم إضافة: {name}")
        except Exception as e:
            await event.reply(f"❌ خطأ: {e}\nتأكد ان البوت والحساب المربوط في الجروب")
        return

    if step == 'delete_group':
        try:
            idx = int(text) - 1
            groups_list = list(db['groups'].items())
            if 0 <= idx < len(groups_list):
                gid, name = groups_list[idx]
                del db['groups'][gid]
                db['banned_groups'].append(gid)
                save_db()
                del waiting_for[uid]
                await event.reply(f"✅ تم حذف: {name}\n🚫 تم حظره من الجلب التلقائي")
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
            sleep_time = int(text)
            if sleep_time < 10:
                return await event.reply("❌ أقل وقت 10 ثواني")
            db['sleep_time'] = sleep_time
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم التحديث: {sleep_time} ثانية")
        except:
            await event.reply("❌ رقم صحيح فقط")
        return

    if step == 'set_delay':
        try:
            delay = int(text)
            if delay < 1:
                return await event.reply("❌ أقل وقت ثانية واحدة")
            db['msg_delay'] = delay
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم التحديث: {delay} ثانية")
        except:
            await event.reply("❌ رقم صحيح فقط")
        return

    if step and step.startswith('proof_'):
        parts = step.split('_')
        pkg_key = parts[1]
        method = parts[2]
        db['pending'][str(uid)] = {
            'pkg': pkg_key,
            'method': method,
            'text': text,
            'time': str(datetime.now()),
            'photo': event.photo.file_id if event.photo else None
        }
        save_db()
        del waiting_for[uid]
        await event.reply("✅ **تم استلام طلبك**\n\n⏳ هيتم مراجعة الدفع وتفعيل الاشتراك خلال دقائق")

        admin_msg = f"💳 **طلب اشتراك جديد**\n\n"
        admin_msg += f"👤 المستخدم: `{uid}`\n"
        admin_msg += f"📦 الباقة: {PRICE_PACKAGES[pkg_key]['label']}\n"
        admin_msg += f"💵 السعر: {PRICE_PACKAGES[pkg_key]['price']}\n"
        admin_msg += f"💳 الطريقة: {method}\n"
        admin_msg += f"📝 التفاصيل: {text[:200]}\n\n"
        admin_msg += f"لتفعيل: `/activate {uid} {pkg_key}`"

        try:
            if event.photo:
                await bot.send_file(ADMIN_ID, event.photo, caption=admin_msg)
            else:
                await bot.send_message(ADMIN_ID, admin_msg)
        except:
            pass
        return

    if step == 'add_sub_id' and is_admin(uid):
        waiting_for[uid] = f'add_sub_days_{text}'
        await event.reply(f"✅ الايدي: `{text}`\n\nابعت عدد الأيام:")
        return

    if step and step.startswith('add_sub_days_'):
        try:
            user_id = step.replace('add_sub_days_', '')
            days = int(text)
            expiry = datetime.now() + timedelta(days=days)
            db['subs'][user_id] = expiry.strftime('%Y-%m-%d')
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم إضافة اشتراك\n👤 `{user_id}`\n⏰ {days} يوم\n📅 ينتهي: {expiry.strftime('%Y-%m-%d')}")
            try:
                await bot.send_message(int(user_id), f"🎉 **تم تفعيل اشتراكك!**\n⏰ المدة: {days} يوم\n📅 ينتهي: {expiry.strftime('%Y-%m-%d')}{get_time()}")
            except:
                pass
        except:
            await event.reply("❌ رقم صحيح فقط")
        return

    if step == 'remove_sub' and is_admin(uid):
        if text in db['subs']:
            del db['subs'][text]
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم إزالة اشتراك `{text}`")
        else:
            await event.reply("❌ المستخدم مش مشترك")
        return

    if step == 'broadcast' and is_main_admin(uid):
        count = 0
        fail = 0
        await event.reply("📢 **جاري الإرسال للجميع...**")
        for user_id in db['subs'].keys():
            try:
                await bot.send_message(int(user_id), text)
                count += 1
                await asyncio.sleep(0.1)
            except:
                fail += 1
        del waiting_for[uid]
        await event.reply(f"✅ **تمت الإذاعة**\n\n📤 نجح: `{count}`\n❌ فشل: `{fail}`")
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

    try:
        client = TelegramClient(StringSession(db['session']), API_ID, API_HASH)
        await client.start()

        msgs = [m for m in db['messages'] if m]
        active_groups = [gid for gid in db['groups'] if gid not in db['banned_groups']]

        if not active_groups:
            await bot.send_message(uid, "❌ مفيش جروبات نشطة")
            is_posting = False
            return

        await bot.send_message(uid, f"🚀 **بدأ النشر**\n👥 الجروبات: `{len(active_groups)}`\n📩 الرسائل: `{len(msgs)}`\n⏱️ وقت الجروب: `{db['sleep_time']}ث`")

        while is_posting:
            for gid in active_groups:
                if not is_posting:
                    break

                try:
                    if db['send_all']:
                        for i, msg in enumerate(msgs):
                            await client.send_message(int(gid), msg)
                            db['msg_stats'][i] += 1
                            db['stats']['total_sent'] += 1
                            await asyncio.sleep(db['msg_delay'])
                    else:
                        msg = msgs[db['current_msg']]
                        await client.send_message(int(gid), msg)
                        db['msg_stats'][db['current_msg']] += 1
                        db['stats']['total_sent'] += 1
                        db['current_msg'] = (db['current_msg'] + 1) % len(msgs)

                    save_db()
                except FloodWaitError as e:
                    await bot.send_message(uid, f"⏳ حظر مؤقت {e.seconds} ثانية في جروب `{db['groups'].get(gid, gid)}`")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"Error posting to {gid}: {e}")

                await asyncio.sleep(db['sleep_time'])

        await client.disconnect()
    except Exception as e:
        await bot.send_message(uid, f"❌ خطأ في النشر: {e}")
    finally:
        is_posting = False
        await bot.send_message(uid, "🔴 توقف النشر")

# --- الرد التلقائي ---
@bot.on(events.NewMessage(incoming=True))
async def auto_reply(event):
    if not db['auto_reply'] or not db['session']:
        return
    if not event.is_group:
        return

    try:
        me = await event.client.get_me()
        if me and me.username and f"@{me.username.lower()}" in (event.raw_text or "").lower():
            await event.reply(db['auto_reply_text'])
    except:
        pass

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ البوت شغال")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
