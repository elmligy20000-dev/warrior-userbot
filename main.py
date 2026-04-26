import asyncio
import json
import base64
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import *
from telethon.tl.types import MessageEntityCustomEmoji
import io

API_ID = 33595004
API_HASH = "cbd1066ed026997f2f4a7c4323b7bda7"
BOT_TOKEN = "8676300768:AAGhhZ9l8GmcNaJ0ioaa7rXZuYNhyjoANMM"
ADMIN_ID = 154919127
ADMIN_USERNAME = "@Devazf"

REQUIRED_CHANNELS = ['@vip6705']
DB_FILE = 'database.json'

bot = TelegramClient('bot', API_ID, API_HASH)
db = {'users': {}, 'generated_codes': {}, 'stats': {'total_sent': 0, 'total_groups': 0}}
waiting_for = {}
active_clients = {}

def load_db():
    global db
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except:
        save_db()

def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def get_user_data(uid):
    uid = str(uid)
    if uid not in db['users']:
        db['users'][uid] = {
            'subscription_end': None,
            'trial_end': None,
            'accounts': {},
            'current_account': None
        }
    return db['users'][uid]

def is_trial(uid):
    user = get_user_data(uid)
    if 'trial_end' not in user:
        return False
    return datetime.now() < datetime.fromisoformat(user['trial_end'])

def get_trial_hours_left(uid):
    user = get_user_data(uid)
    if 'trial_end' not in user:
        return 0
    end = datetime.fromisoformat(user['trial_end'])
    if datetime.now() >= end:
        return 0
    delta = end - datetime.now()
    return round(delta.total_seconds() / 3600, 1)

def start_trial(uid):
    user = get_user_data(uid)
    if 'trial_end' in user:
        return False
    user['trial_end'] = (datetime.now() + timedelta(hours=12)).isoformat()
    save_db()
    return True

def is_subscribed(uid):
    if uid == ADMIN_ID:
        return True
    user = get_user_data(uid)
    sub_end = user.get('subscription_end')
    if sub_end and datetime.fromisoformat(sub_end) > datetime.now():
        return True
    return is_trial(uid)

def get_sub_days_left(uid):
    if uid == ADMIN_ID:
        return 9999
    user = get_user_data(uid)
    sub_end = user.get('subscription_end')
    if not sub_end:
        return 0
    delta = datetime.fromisoformat(sub_end) - datetime.now()
    return max(0, delta.days)

def add_subscription_days(uid, days):
    user = get_user_data(uid)
    now = datetime.now()
    current_end = user.get('subscription_end')
    if current_end and datetime.fromisoformat(current_end) > now:
        new_end = datetime.fromisoformat(current_end) + timedelta(days=days)
    else:
        new_end = now + timedelta(days=days)
    user['subscription_end'] = new_end.isoformat()
    save_db()
    return new_end

def generate_code(days):
    import random
    import string
    code = 'AZEF-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
    db['generated_codes'][code] = days
    save_db()
    return code

def get_all_codes():
    return db.get('generated_codes', {})

async def check_subscription_channels(uid):
    not_joined = []
    for channel in REQUIRED_CHANNELS:
        try:
            await bot.get_permissions(channel, uid)
        except UserNotParticipantError:
            not_joined.append(channel)
        except:
            pass
    return len(not_joined) == 0, not_joined

def get_account(uid):
    user = get_user_data(uid)
    acc_id = user.get('current_account')
    if not acc_id or acc_id not in user['accounts']:
        return None
    return user['accounts'][acc_id]

def get_main_menu(uid):
    btns = [
        [Button.inline("📱 الحسابات", b"accounts")],
        [Button.inline("🔄 تبديل حساب", b"switch_account")],
        [Button.inline("📊 الإحصائيات", b"stats")],
        [Button.inline("🚀 تشغيل الكل", b"restart_all"), Button.inline("🛑 ايقاف الكل", b"stop_all")]
    ]
    if uid == ADMIN_ID:
        btns.append([Button.inline("👑 لوحة الادمن", b"admin_panel")])
    return btns

async def account_menu(uid, acc_id):
    user = get_user_data(uid)
    acc = user['accounts'][acc_id]
    status = "🟢 يعمل" if acc['is_posting'] else "🔴 متوقف"
    auto_status = "✅" if acc['auto_reply_enabled'] else "❌"
    freeze_status = "✅" if acc.get('freeze_protection', True) else "❌"
    return [
        [Button.inline(f"▶️ تشغيل" if not acc['is_posting'] else "⏸️ ايقاف", f"toggle_{acc_id}".encode())],
        [Button.inline("⚙️ الإعدادات", f"settings_{acc_id}".encode())],
        [Button.inline("👥 الجروبات", f"groups_{acc_id}".encode())],
        [Button.inline(f"💬 رد تلقائي {auto_status}", f"auto_reply_{acc_id}".encode())],
        [Button.inline(f"🧊 حماية تجميد {freeze_status}", f"freeze_{acc_id}".encode())],
        [Button.inline("🗑️ حذف الحساب", f"del_acc_{acc_id}".encode())],
        [Button.inline("🔙 رجوع", b"back")]
    ]

async def settings_menu(uid):
    acc = get_account(uid)
    if not acc:
        return [[Button.inline("🔙 رجوع", b"back")]]
    status = "🟢 يعمل" if acc['is_posting'] else "🔴 متوقف"
    auto = "✅ مفعل" if acc['send_all'] else "❌ معطل"
    flood = "✅ مفعل" if acc['flood_protection'] else "❌ معطل"
    auto_reply = "✅ مفعل" if acc.get('auto_reply_enabled') else "❌ معطل"
    freeze = "✅ مفعل" if acc.get('freeze_protection', True) else "❌ معطل"
    return [
        [Button.inline(f"▶️ النشر: {status}", b"toggle_posting")],
        [Button.inline(f"🔄 ارسال الكل: {auto}", b"toggle_auto")],
        [Button.inline(f"🛡️ حماية فلود: {flood}", b"toggle_flood")],
        [Button.inline(f"💬 رد تلقائي: {auto_reply}", b"toggle_auto_reply")],
        [Button.inline(f"🧊 حماية تجميد: {freeze}", b"toggle_freeze")],
        [Button.inline("📝 تعيين نص الرد", b"set_reply_text")],
        [Button.inline("⏱️ وقت الانتظار", b"set_sleep"), Button.inline("⏱️ بين الرسائل", b"set_msg_delay")],
        [Button.inline("📝 الرسائل", b"messages"), Button.inline("👁️ معاينة", b"preview_msgs")],
        [Button.inline("✏️ تعديل الاسم", b"edit_name"), Button.inline("🗑️ حذف الحساب", b"delete_account")],
        [Button.inline("🔙 رجوع", b"back")]
    ]

async def groups_menu(uid):
    acc = get_account(uid)
    count = len(acc['groups']) if acc else 0
    banned = len(acc['banned_groups']) if acc else 0
    return [
        [Button.inline(f"📋 عرض الجروبات ({count})", b"view_groups")],
        [Button.inline("🔄 جلب الجروبات", b"fetch_groups")],
        [Button.inline("➕ اضافة جروب", b"add_group"), Button.inline("🗑️ حذف جروب", b"delete_group")],
        [Button.inline(f"🚫 المحظورة ({banned})", b"banned_groups")],
        [Button.inline("🔙 رجوع", b"settings")]
    ]

async def admin_panel():
    total_users = len(db['users'])
    total_codes = len(db.get('generated_codes', {}))
    total_sent = db['stats']['total_sent']
    btns = [
        [Button.inline("🎫 توليد كود", b"gen_code")],
        [Button.inline("📋 الاكواد المتاحة", b"view_codes")],
        [Button.inline("👥 المشتركين", b"view_subs")],
        [Button.inline("💾 نسخة احتياطية", b"backup_sessions")],
        [Button.inline("🔙 رجوع", b"back")]
    ]
    text = f"👑 **لوحة الادمن**\n\n👥 المستخدمين: {total_users}\n🎫 الاكواد: {total_codes}\n📨 الرسائل: {total_sent}"
    return btns, text

async def ensure_client_connected(uid, acc_id):
    client_key = f"{uid}_{acc_id}"
    user = get_user_data(uid)
    acc = user['accounts'][acc_id]

    if client_key in active_clients:
        client = active_clients[client_key]
        try:
            if await client.is_user_authorized():
                return client
        except:
            pass

    try:
        client = TelegramClient(StringSession(acc['session']), API_ID, API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            active_clients[client_key] = client
            return client
        else:
            await client.disconnect()
            return None
    except:
        return None

async def start_posting_uid(uid, acc_id):
    user = get_user_data(uid)
    acc = user['accounts'][acc_id]
    client_key = f"{uid}_{acc_id}"

    client = await ensure_client_connected(uid, acc_id)
    if not client:
        acc['is_posting'] = False
        save_db()
        return

    while acc['is_posting']:
        if acc.get('flood_until'):
            flood_until = datetime.fromisoformat(acc['flood_until'])
            if datetime.now() < flood_until:
                await asyncio.sleep(60)
                continue
            else:
                acc['flood_until'] = None
                save_db()

        groups = [g for g in acc['groups'] if g not in acc['banned_groups']]
        if not groups:
            await asyncio.sleep(60)
            continue

        messages = [m for m in acc['messages'] if m]
        if not messages:
            await asyncio.sleep(60)
            continue

        for group in groups:
            if not acc['is_posting']:
                break

            try:
                if acc['send_all']:
                    for i, msg in enumerate(acc['messages']):
                        if not msg or not acc['is_posting']:
                            continue
                        entities = []
                        entities_json = acc['messages_entities'][i]
                        if entities_json:
                            entities_data = json.loads(entities_json)
                            for e in entities_data:
                                if e['type'] == 'MessageEntityCustomEmoji':
                                    entities.append(MessageEntityCustomEmoji(
                                        offset=e['offset'],
                                        length=e['length'],
                                        document_id=int(e['document_id'])
                                    ))
                        await client.send_message(group, msg, entities=entities if entities else None)
                        acc['msg_stats'][i] += 1
                        db['stats']['total_sent'] += 1
                        save_db()
                        await asyncio.sleep(acc['msg_delay'])
                else:
                    msg_idx = acc['current_msg']
                    msg = acc['messages'][msg_idx]
                    entities = []
                    entities_json = acc['messages_entities'][msg_idx]
                    if entities_json:
                        entities_data = json.loads(entities_json)
                        for e in entities_data:
                            if e['type'] == 'MessageEntityCustomEmoji':
                                entities.append(MessageEntityCustomEmoji(
                                    offset=e['offset'],
                                    length=e['length'],
                                    document_id=int(e['document_id'])
                                ))
                    await client.send_message(group, msg, entities=entities if entities else None)
                    acc['msg_stats'][msg_idx] += 1
                    acc['current_msg'] = (msg_idx + 1) % len(messages)
                    db['stats']['total_sent'] += 1
                    save_db()

            except FloodWaitError as e:
                if acc['flood_protection']:
                    acc['flood_until'] = (datetime.now() + timedelta(seconds=e.seconds)).isoformat()
                    save_db()
                    break
            except (ChatWriteForbiddenError, UserBannedInChannelError):
                if group not in acc['banned_groups']:
                    acc['banned_groups'].append(group)
                    save_db()
            except Exception:
                pass

            await asyncio.sleep(acc['sleep_time'])

        await asyncio.sleep(5)

async def generate_backup_file():
    backup_data = []
    for uid, user_data in db['users'].items():
        for acc_id, acc in user_data['accounts'].items():
            session_encoded = base64.b64encode(acc['session'].encode()).decode()
            backup_data.append({
                'user_id': uid,
                'account_name': acc['name'],
                'phone': acc['phone'],
                'session': session_encoded
            })
    return json.dumps(backup_data, ensure_ascii=False, indent=2)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    user = get_user_data(uid)

    is_joined, not_joined = await check_subscription_channels(uid)
    if not is_joined:
        btns = []
        for ch in not_joined:
            btns.append([Button.url(f"📢 {ch}", f"https://t.me/{ch.replace('@', '')}")])
        btns.append([Button.inline("✅ تحققت من الاشتراك", b"check_channels")])
        await event.reply("🔒 **لازم تشترك في القنوات دي الاول:**", buttons=btns)
        return

    if not is_subscribed(uid):
        trial_used = 'trial_end' in user
        btns = [
            [Button.inline("🔑 ادخال كود التفعيل", b"activate_code")]
        ]
        if not trial_used:
            btns.insert(0, [Button.inline("🎁 تجربة مجانية 12 ساعة", b"start_trial")])
        btns.append([Button.url("👨‍💻 المطور", f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")])

        text = "🔒 **البوت باشتراك مدفوع**\n\n"
        if not trial_used:
            text += "🎁 تقدر تجرب البوت مجانا لمدة 12 ساعة"
        else:
            text += "❌ خلصت التجربة المجانية"

        await event.reply(text, buttons=btns)
        return

    if is_trial(uid):
        hours = get_trial_hours_left(uid)
        await event.reply(f"🎁 **تجربة مجانية فعالة**\n\n⏰ فاضل: {hours} ساعة", buttons=get_main_menu(uid))
    else:
        days_left = get_sub_days_left(uid)
        await event.reply(f"🔥 **Source Azef**\n\n✅ اشتراكك فعال - فاضل {days_left} يوم", buttons=get_main_menu(uid))

@bot.on(events.NewMessage(pattern='/admin'))
async def admin_cmd(event):
    if event.sender_id!= ADMIN_ID:
        return
    btns, text = await admin_panel()
    await event.reply(text, buttons=btns)

@bot.on(events.NewMessage(pattern='/backup'))
async def backup_cmd(event):
    if event.sender_id!= ADMIN_ID:
        return
    await event.reply("⏳ جاري تجهيز النسخة الاحتياطية...")
    backup = await generate_backup_file()
    file = io.BytesIO(backup.encode('utf-8'))
    file.name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    await bot.send_file(event.chat_id, file, caption="💾 **نسخة احتياطية من الجلسات**\n\n⚠️ احفظ الملف ده في مكان آمن\n🔐 الجلسات مشفرة بـ base64")

@bot.on(events.CallbackQuery)
async def callback(event):
    uid = event.sender_id
    data = event.data
    user = get_user_data(uid)
    acc = get_account(uid)
    if data == b"check_channels":
        is_joined, not_joined = await check_subscription_channels(uid)
        if not is_joined:
            return await event.answer("❌ لسه مشتركتش في كل القنوات", alert=True)
        await event.delete()
        await start(event)
        return
    if not is_subscribed(uid) and data not in [b"activate_code", b"back", b"admin_panel", b"gen_code", b"view_codes", b"view_subs", b"check_channels", b"start_trial"] and not data.startswith(b'gen_'):
        return await event.answer("🔒 لازم تشترك الأول", alert=True)
    if data == b"back":
        if is_subscribed(uid):
            if is_trial(uid):
                hours = get_trial_hours_left(uid)
                await event.edit(f"🎁 **تجربة مجانية فعالة**\n\n⏰ فاضل: {hours} ساعة", buttons=get_main_menu(uid))
            else:
                days_left = get_sub_days_left(uid)
                await event.edit(f"🔥 **Source Azef**\n\n✅ اشتراكك فعال - فاضل {days_left} يوم", buttons=get_main_menu(uid))
        else:
            btns = [
                [Button.inline("🔑 ادخال كود التفعيل", b"activate_code")],
                [Button.url("👨‍💻 المطور", f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
            ]
            await event.edit("🔒 **البوت باشتراك مدفوع**", buttons=btns)
        return
    if data == b"activate_code":
        waiting_for[uid] = 'enter_code'
        await event.edit("🔑 **تفعيل الاشتراك**\n\nابعت كود التفعيل اللي اشتريته:\nمثال: `AZEF-1234-5678`", buttons=[[Button.inline("🔙 رجوع", b"back")]])
        return
    if data == b"start_trial":
        if start_trial(uid):
            await event.answer("🎁 تم تفعيل التجربة", alert=True)
            await event.edit(f"🎁 **مبروك التجربة المجانية**\n\n⏰ المدة: 12 ساعة\n📱 تقدر تضيف لحد 2 حساب\n\nابعت /start للبدء", buttons=[[Button.inline("🚀 ابدأ", b"back")]])
        else:
            await event.answer("❌ استخدمت التجربة قبل كده", alert=True)
        return
    if data == b"admin_panel":
        if uid!= ADMIN_ID:
            return await event.answer("❌ للادمن فقط", alert=True)
        btns, text = await admin_panel()
        await event.edit(text, buttons=btns)
        return
    if data == b"gen_code":
        if uid!= ADMIN_ID:
            return await event.answer("❌ للادمن فقط", alert=True)
        btns = [
            [Button.inline("يوم 1", b"gen_1"), Button.inline("3 ايام", b"gen_3")],
            [Button.inline("اسبوع", b"gen_7"), Button.inline("شهر", b"gen_30")],
            [Button.inline("🔙 رجوع", b"admin_panel")]
        ]
        await event.edit("🎫 **توليد كود**\n\nاختر مدة الاشتراك:", buttons=btns)
        return
    if data.startswith(b'gen_'):
        if uid!= ADMIN_ID:
            return
        days = int(data.decode().split('_')[1])
        code = generate_code(days)
        await event.answer("✅ تم التوليد", alert=True)
        await event.edit(f"✅ **تم توليد كود جديد**\n\n🔑 الكود: `{code}`\n📅 المدة: {days} يوم\n\nابعته للعميل عشان يفعله", buttons=[[Button.inline("🔙 رجوع", b"gen_code")]])
        return
    if data == b"view_codes":
        if uid!= ADMIN_ID:
            return
        codes = get_all_codes()
        if not codes:
            text = "📋 **الاكواد المتاحة**\n\nمفيش اكواد حاليا"
        else:
            text = "📋 **الاكواد المتاحة**\n\n"
            for code, days in codes.items():
                text += f"`{code}` - {days} يوم\n"
        await event.edit(text, buttons=[[Button.inline("🔙 رجوع", b"admin_panel")]])
        return
    if data == b"view_subs":
        if uid!= ADMIN_ID:
            return
        subs = []
        for user_id, user_data in db['users'].items():
            if is_subscribed(int(user_id)):
                if is_trial(int(user_id)):
                    hours = get_trial_hours_left(int(user_id))
                    subs.append(f"`{user_id}` - تجربة فاضل {hours} ساعة")
                else:
                    days = get_sub_days_left(int(user_id))
                    subs.append(f"`{user_id}` - فاضل {days} يوم")
        text = "👥 **المشتركين الفعالين**\n\n" + "\n".join(subs) if subs else "👥 **المشتركين الفعالين**\n\nمفيش مشتركين حاليا"
        await event.edit(text, buttons=[[Button.inline("🔙 رجوع", b"admin_panel")]])
        return
    if data == b"backup_sessions":
        if uid!= ADMIN_ID:
            return
        await event.answer("⏳ جاري تجهيز النسخة...", alert=True)
        backup = await generate_backup_file()
        file = io.BytesIO(backup.encode('utf-8'))
        file.name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        await bot.send_file(uid, file, caption="💾 **نسخة احتياطية من الجلسات**\n\n⚠️ احفظ الملف ده في مكان آمن\n🔐 الجلسات مشفرة بـ base64")
        await event.edit("✅ **تم ارسال النسخة الاحتياطية**", buttons=[[Button.inline("🔙 رجوع", b"admin_panel")]])
        return
    if data == b"add_account":
        if is_trial(uid) and len(user['accounts']) >= 2:
            return await event.answer("❌ التجربة المجانية = حسابين فقط", alert=True)
        waiting_for[uid] = 'phone'
        await event.edit("📱 **اضافة حساب جديد**\n\nابعت رقم الهاتف مع كود الدولة:\nمثال: `+201234567890`\n\n⚠️ لازم يكون الرقم مسجل في تليجرام", buttons=[[Button.inline("🔙 الغاء", b"back")]])
        return
    if data == b"switch_account":
        if not user['accounts']:
            return await event.answer("❌ مفيش حسابات", alert=True)
        btns = []
        for acc_id, acc_data in user['accounts'].items():
            status = "🟢" if acc_data['is_posting'] else "🔴"
            current = "⭐" if user['current_account'] == acc_id else ""
            btns.append([Button.inline(f"{current} {status} {acc_data['name']}", f"select_acc_{acc_id}".encode())])
        btns.append([Button.inline("🔙 رجوع", b"back")])
        await event.edit("📱 **اختر الحساب:**", buttons=btns)
        return
    if data.startswith(b'select_acc_'):
        acc_id = data.decode().split('_')[2]
        user['current_account'] = acc_id
        save_db()
        await event.answer("✅ تم التبديل", alert=True)
        if is_trial(uid):
            hours = get_trial_hours_left(uid)
            await event.edit(f"🎁 **تجربة مجانية فعالة**\n\n⏰ فاضل: {hours} ساعة", buttons=get_main_menu(uid))
        else:
            days_left = get_sub_days_left(uid)
            await event.edit(f"🔥 **Source Azef**\n\n✅ اشتراكك فعال - فاضل {days_left} يوم", buttons=get_main_menu(uid))
        return
    if data == b"stats":
        total_sent = db['stats']['total_sent']
        total_users = len(db['users'])
        total_accs = sum(len(u['accounts']) for u in db['users'].values())
        if is_trial(uid):
            hours = get_trial_hours_left(uid)
            sub_text = f"⏰ تجربة: فاضل `{hours}` ساعة"
        else:
            days_left = get_sub_days_left(uid)
            sub_text = f"⏰ اشتراكك: فاضل `{days_left}` يوم"
        await event.edit(f"📊 **الإحصائيات**\n\n📨 إجمالي الرسائل: `{total_sent}`\n👥 عدد المستخدمين: `{total_users}`\n📱 عدد الحسابات: `{total_accs}`\n{sub_text}", buttons=[[Button.inline("🔙 رجوع", b"back")]])
        return
    if data == b"restart_all":
        count = 0
        for acc_id, acc_data in user['accounts'].items():
            if not acc_data['is_posting']:
                acc_data['is_posting'] = True
                asyncio.create_task(start_posting_uid(uid, acc_id))
                count += 1
        save_db()
        await event.answer(f"✅ تم تشغيل {count} حساب", alert=True)
        return
    if data == b"stop_all":
        count = 0
        for acc_id, acc_data in user['accounts'].items():
            if acc_data['is_posting']:
                acc_data['is_posting'] = False
                count += 1
        save_db()
        await event.answer(f"🛑 تم ايقاف {count} حساب", alert=True)
        return
    if data.startswith(b'toggle_'):
        acc_id = data.decode().split('_')[1]
        if acc_id not in user['accounts']:
            return await event.answer("❌ الحساب مش موجود", alert=True)
        acc = user['accounts'][acc_id]
        if acc['is_posting']:
            acc['is_posting'] = False
            await event.answer("🛑 تم الايقاف", alert=True)
        else:
            acc['is_posting'] = True
            asyncio.create_task(start_posting_uid(uid, acc_id))
            await event.answer("🚀 بدأ النشر", alert=True)
        save_db()
        await event.edit(f"📱 **{acc['name']}**", buttons=await account_menu(uid, acc_id))
        return
    if data.startswith(b'settings_'):
        acc_id = data.decode().split('_')[1]
        user['current_account'] = acc_id
        save_db()
        await event.edit("⚙️ **الإعدادات**", buttons=await settings_menu(uid))
        return
    if data.startswith(b'groups_'):
        acc_id = data.decode().split('_')[1]
        user['current_account'] = acc_id
        save_db()
        await event.edit("👥 **ادارة الجروبات**", buttons=await groups_menu(uid))
        return
    if data.startswith(b'auto_reply_'):
        acc_id = data.decode().split('_')[2]
        acc = user['accounts'][acc_id]
        acc['auto_reply_enabled'] = not acc.get('auto_reply_enabled', False)
        save_db()
        if acc['auto_reply_enabled']:
            client = await ensure_client_connected(uid, acc_id)
            if client:
                await event.answer("✅ تم تفعيل الرد التلقائي", alert=True)
            else:
                await event.answer("❌ الجلسة منتهية", alert=True)
                acc['auto_reply_enabled'] = False
                save_db()
        else:
            await event.answer("🔕 تم الايقاف", alert=True)
        await event.edit(f"📱 **{acc['name']}**", buttons=await account_menu(uid, acc_id))
        return
    if data.startswith(b'freeze_'):
        acc_id = data.decode().split('_')[1]
        acc = user['accounts'][acc_id]
        acc['freeze_protection'] = not acc.get('freeze_protection', True)
        save_db()
        await event.answer("✅ تم التبديل", alert=True)
        await event.edit(f"📱 **{acc['name']}**", buttons=await account_menu(uid, acc_id))
        return
    if data.startswith(b'del_acc_'):
        acc_id = data.decode().split('_')[2]
        del user['accounts'][acc_id]
        user['current_account'] = None
        save_db()
        await event.answer("✅ تم الحذف", alert=True)
        if is_trial(uid):
            hours = get_trial_hours_left(uid)
            await event.edit(f"🎁 **تجربة مجانية فعالة**\n\n⏰ فاضل: {hours} ساعة", buttons=get_main_menu(uid))
        else:
            days_left = get_sub_days_left(uid)
            await event.edit(f"🔥 **Source Azef**\n\n✅ اشتراكك فعال - فاضل {days_left} يوم", buttons=get_main_menu(uid))
        return

    if not acc and data not in [b"back", b"add_account", b"switch_account", b"stats", b"restart_all", b"stop_all"]:
        return await event.answer("❌ اختار حساب الأول", alert=True)

    if data == b"settings":
        await event.edit("⚙️ **الإعدادات**", buttons=await settings_menu(uid))
        return
    if data == b"groups":
        await event.edit("👥 **ادارة الجروبات**", buttons=await groups_menu(uid))
        return
    if data == b"toggle_posting":
        if acc['is_posting']:
            acc['is_posting'] = False
            await event.answer("🛑 تم الايقاف", alert=True)
        else:
            acc['is_posting'] = True
            asyncio.create_task(start_posting_uid(uid, user['current_account']))
            await event.answer("🚀 بدأ النشر", alert=True)
        save_db()
        await event.edit("⚙️ **الإعدادات**", buttons=await settings_menu(uid))
        return
    if data == b"toggle_auto":
        acc['send_all'] = not acc['send_all']
        save_db()
        await event.answer("✅ تم التبديل", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=await settings_menu(uid))
        return
    if data == b"toggle_flood":
        acc['flood_protection'] = not acc['flood_protection']
        save_db()
        await event.answer("✅ تم التبديل", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=await settings_menu(uid))
        return
    if data == b"toggle_auto_reply":
        acc['auto_reply_enabled'] = not acc.get('auto_reply_enabled', False)
        save_db()
        if acc['auto_reply_enabled']:
            client = await ensure_client_connected(uid, user['current_account'])
            if client:
                await event.answer("✅ تم تفعيل الرد التلقائي", alert=True)
            else:
                await event.answer("❌ الجلسة منتهية - سجل دخول تاني", alert=True)
                acc['auto_reply_enabled'] = False
                save_db()
        else:
            await event.answer("🔕 تم ايقاف الرد التلقائي", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=await settings_menu(uid))
        return
    if data == b"toggle_freeze":
        acc['freeze_protection'] = not acc.get('freeze_protection', True)
        save_db()
        await event.answer("✅ تم التبديل", alert=True)
        await event.edit("⚙️ **الإعدادات**", buttons=await settings_menu(uid))
        return
    if data == b"set_reply_text":
        waiting_for[uid] = 'set_reply'
        await event.edit(f"💬 **تعيين نص الرد التلقائي**\n\nابعت النص اللي عايز البوت يرد بيه لما حد يمنشنك:\n\nالحالي: `{acc.get('custom_reply_text', 'تفضل خاص')}`", buttons=[[Button.inline("🔙 الغاء", b"settings")]])
        return
    if data == b"fetch_groups":
        client_key = f"{uid}_{user['current_account']}"
        if client_key not in active_clients:
            client = TelegramClient(StringSession(acc['session']), API_ID, API_HASH)
            await client.connect()
            if not await client.is_user_authorized():
                return await event.answer("❌ الجلسة منتهية", alert=True)
            active_clients[client_key] = client
        else:
            client = active_clients[client_key]
        await event.answer("⏳ جاري جلب الجروبات...", alert=True)
        groups = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                groups.append(dialog.id)
        acc['groups'] = groups
        db['stats']['total_groups'] += len(groups)
        save_db()
        await event.edit(f"✅ **تم جلب الجروبات**\n\n📊 العدد: {len(groups)} جروب", buttons=await groups_menu(uid))
        return
    if data == b"view_groups":
        if not acc['groups']:
            text = "📋 **الجروبات**\n\nمفيش جروبات - دوس جلب الجروبات"
        else:
            text = f"📋 **الجروبات**\n\nالعدد: {len(acc['groups'])}\n\n"
            for i, gid in enumerate(acc['groups'][:20], 1):
                banned = "🚫" if gid in acc['banned_groups'] else "✅"
                text += f"{i}. {banned} `{gid}`\n"
            if len(acc['groups']) > 20:
                text += f"\n... و {len(acc['groups']) - 20} جروب تاني"
        await event.edit(text, buttons=[[Button.inline("🔙 رجوع", b"groups")]])
        return
    if data == b"add_group":
        waiting_for[uid] = 'add_group'
        await event.edit("➕ **اضافة جروب**\n\nابعت ايدي الجروب او اليوزر:\nمثال: `-100123456789` او `@groupusername`", buttons=[[Button.inline("🔙 الغاء", b"groups")]])
        return
    if data == b"delete_group":
        waiting_for[uid] = 'delete_group'
        await event.edit("🗑️ **حذف جروب**\n\nابعت رقم الجروب من القايمة:\nمثال: `1` لحذف اول جروب", buttons=[[Button.inline("🔙 الغاء", b"groups")]])
        return
    if data == b"banned_groups":
        if not acc['banned_groups']:
            text = "🚫 **الجروبات المحظورة**\n\nمفيش جروبات محظورة"
        else:
            text = f"🚫 **الجروبات المحظورة**\n\nالعدد: {len(acc['banned_groups'])}\n\n"
            for i, gid in enumerate(acc['banned_groups'][:20], 1):
                text += f"{i}. `{gid}`\n"
        await event.edit(text, buttons=[[Button.inline("🔙 رجوع", b"groups")]])
        return
    if data == b"messages":
        waiting_for[uid] = 'select_msg'
        btns = []
        for i in range(5):
            msg = acc['messages'][i]
            preview = msg[:20] + "..." if len(msg) > 20 else msg or "فاضي"
            btns.append([Button.inline(f"📝 رسالة {i+1}: {preview}", f"msg_{i}".encode())])
        btns.append([Button.inline("🔙 رجوع", b"settings")])
        await event.edit("📝 **ادارة الرسائل**\n\nاختار رسالة للتعديل:", buttons=btns)
        return
    if data == b"preview_msgs":
        text = "👁️ **معاينة الرسائل**\n\n"
        for i, msg in enumerate(acc['messages'], 1):
            if msg:
                count = acc['msg_stats'][i-1]
                text += f"**{i}.** {msg}\n📊 اتبعتت: {count} مرة\n\n"
            else:
                text += f"**{i}.** *فاضية*\n\n"
        await event.edit(text, buttons=[[Button.inline("🔙 رجوع", b"settings")]])
        return
    if data.startswith(b'msg_'):
        msg_idx = int(data.decode().split('_')[1])
        waiting_for[uid] = f'edit_msg_{msg_idx}'
        await event.edit(f"📝 **تعديل الرسالة {msg_idx + 1}**\n\nالحالي:\n{acc['messages'][msg_idx] or '*فاضية*'}\n\nابعت الرسالة الجديدة:", buttons=[[Button.inline("🔙 الغاء", b"messages")]])
        return
    if data == b"set_sleep":
        waiting_for[uid] = 'set_sleep'
        await event.edit(f"⏱️ **وقت الانتظار**\n\nالحالي: {acc['sleep_time']} ثانية\n\nابعت الوقت الجديد بالثواني:\nمثال: `300` = 5 دقايق", buttons=[[Button.inline("🔙 الغاء", b"settings")]])
        return
    if data == b"set_msg_delay":
        waiting_for[uid] = 'set_msg_delay'
        await event.edit(f"⏱️ **وقت بين الرسائل**\n\nالحالي: {acc['msg_delay']} ثانية\n\nابعت الوقت الجديد:\nمثال: `2` = ثانيتين", buttons=[[Button.inline("🔙 الغاء", b"settings")]])
        return
    if data == b"edit_name":
        waiting_for[uid] = 'edit_name'
        await event.edit(f"✏️ **تعديل الاسم**\n\nالحالي: {acc['name']}\n\nابعت الاسم الجديد:", buttons=[[Button.inline("🔙 الغاء", b"settings")]])
        return
    if data == b"delete_account":
        del user['accounts'][user['current_account']]
        user['current_account'] = None
        save_db()
        await event.answer("✅ تم الحذف", alert=True)
        if is_trial(uid):
            hours = get_trial_hours_left(uid)
            await event.edit(f"🎁 **تجربة مجانية فعالة**\n\n⏰ فاضل: {hours} ساعة", buttons=get_main_menu(uid))
        else:
            days_left = get_sub_days_left(uid)
            await event.edit(f"🔥 **Source Azef**\n\n✅ اشتراكك فعال - فاضل {days_left} يوم", buttons=get_main_menu(uid))
        return
    if data.startswith(b'acc_'):
        acc_id = data.decode().split('_')[1]
        await event.edit(f"📱 **{user['accounts'][acc_id]['name']}**", buttons=await account_menu(uid, acc_id))
        return
    if data == b"accounts":
        btns = []
        for acc_id, acc_data in user['accounts'].items():
            status = "🟢" if acc_data['is_posting'] else "🔴"
            btns.append([Button.inline(f"{status} {acc_data['name']}", f"acc_{acc_id}".encode())])
        btns.append([Button.inline("➕ اضافة حساب جديد", b"add_account")])
        btns.append([Button.inline("🔙 رجوع", b"back")])
        await event.edit("📱 **الحسابات**", buttons=btns)
        return

@bot.on(events.NewMessage)
async def handle_waiting_messages(event):
    uid = event.sender_id
    if uid not in waiting_for:
        return

    action = waiting_for[uid]
    text = event.raw_text
    user = get_user_data(uid)
    acc = get_account(uid)

    if isinstance(action, dict):
        if action.get('type') == 'code':
            phone = action['phone']
            phone_hash = action['phone_hash']
            session_str = action['session']
            code = text.strip().replace(' ', '')
            try:
                client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
                await client.connect()
                await client.sign_in(phone, code, phone_code_hash=phone_hash)
                session = client.session.save()
                me = await client.get_me()
                await client.disconnect()
                user = get_user_data(uid)
                acc_id = str(len(user['accounts']) + 1)
                user['accounts'][acc_id] = {
                    'name': me.first_name or f"حساب {acc_id}",
                    'username': me.username,
                    'phone': phone,
                    'session': session,
                    'is_posting': False,
                    'messages': ['', '', '', '', ''],
                    'messages_entities': ['', '', '', '', ''],
                    'groups': [],
                    'banned_groups': [],
                    'sleep_time': 300,
                    'msg_delay': 2,
                    'send_all': False,
                    'flood_protection': True,
                    'flood_until': None,
                    'current_msg': 0,
                    'msg_stats': [0, 0, 0, 0, 0],
                    'auto_reply_enabled': False,
                    'custom_reply_text': 'تفضل خاص',
                    'freeze_protection': True
                }
                user['current_account'] = acc_id
                save_db()
                del waiting_for[uid]
                await event.reply(f"✅ **تم اضافة الحساب بنجاح**\n\n📱 {me.first_name}\n🆔 @{me.username or 'بدون'}\n\nتقدر تبدأ النشر دلوقتي", buttons=await account_menu(uid, acc_id))
            except SessionPasswordNeededError:
                waiting_for[uid] = {
                    'type': 'password',
                    'phone': phone,
                    'session': session_str
                }
                await event.reply("🔐 الحساب محمي بـ 2FA\n\nابعت كلمة السر:")
            except PhoneCodeInvalidError:
                await event.reply("❌ الكود غلط\n\nابعت الكود الصح:")
            except Exception as e:
                error_msg = str(e)
                if "PHONE_CODE_EXPIRED" in error_msg:
                    await event.reply("❌ الكود انتهت صلاحيته\n\nاطلب كود جديد من /start")
                    del waiting_for[uid]
                else:
                    await event.reply(f"❌ خطأ: {error_msg}")
            return
        if action.get('type') == 'password':
            phone = action['phone']
            session_str = action['session']
            password = text.strip()
            try:
                client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
                await client.connect()
                await client.sign_in(password=password)
                session = client.session.save()
                me = await client.get_me()
                await client.disconnect()
                user = get_user_data(uid)
                acc_id = str(len(user['accounts']) + 1)
                user['accounts'][acc_id] = {
                    'name': me.first_name or f"حساب {acc_id}",
                    'username': me.username,
                    'phone': phone,
                    'session': session,
                    'is_posting': False,
                    'messages': ['', '', '', '', ''],
                    'messages_entities': ['', '', '', '', ''],
                    'groups': [],
                    'banned_groups': [],
                    'sleep_time': 300,
                    'msg_delay': 2,
                    'send_all': False,
                    'flood_protection': True,
                    'flood_until': None,
                    'current_msg': 0,
                    'msg_stats': [0, 0, 0, 0, 0],
                    'auto_reply_enabled': False,
                    'custom_reply_text': 'تفضل خاص',
                    'freeze_protection': True
                }
                user['current_account'] = acc_id
                save_db()
                del waiting_for[uid]
                await event.reply(f"✅ **تم اضافة الحساب بنجاح**\n\n📱 {me.first_name}\n🆔 @{me.username or 'بدون'}\n\nتقدر تبدأ النشر دلوقتي", buttons=await account_menu(uid, acc_id))
            except Exception as e:
                await event.reply(f"❌ كلمة السر غلط: {e}\n\nابعت كلمة السر تاني:")
            return

    if action == 'enter_code':
        code = text.strip().upper()
        codes_db = get_all_codes()
        if code in codes_db:
            days = codes_db[code]
            new_end = add_subscription_days(uid, days)
            del waiting_for[uid]
            del db['generated_codes'][code]
            save_db()
            await event.reply(f"✅ **تم التفعيل بنجاح**\n\n📅 الصلاحية: {days} يوم\n📆 ينتهي: {new_end.strftime('%Y-%m-%d')}\n\nابعت /start للبدء")
        else:
            await event.reply("❌ كود غلط او مستخدم قبل كده")
        return
    if not is_subscribed(uid):
        return
    if action == 'phone':
        try:
            phone = text.strip()
            if not phone.startswith('+'):
                phone = '+' + phone
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            sent = await client.send_code_request(phone)
            session_str = client.session.save()
            await client.disconnect()
            waiting_for[uid] = {
                'type': 'code',
                'phone': phone,
                'phone_hash': sent.phone_code_hash,
                'session': session_str
            }
            await event.reply("✅ تم ارسال الكود\n\nابعت الكود اللي وصلك:")
        except PhoneNumberInvalidError:
            await event.reply("❌ رقم الهاتف غلط\nاكتب الرقم كامل مع كود الدولة مثلا: +201234567890")
        except PhoneNumberBannedError:
            await event.reply("❌ الرقم ده محظور من تليجرام")
        except Exception as e:
            error_msg = str(e)
            if "FLOOD" in error_msg:
                await event.reply("❌ محاولات كتير. استنى شوية وجرب تاني")
            else:
                await event.reply(f"❌ خطأ: {error_msg}")
            if uid in waiting_for:
                del waiting_for[uid]
        return
    if action == 'set_reply':
        acc['custom_reply_text'] = text
        save_db()
        del waiting_for[uid]
        await event.reply("✅ تم حفظ نص الرد", buttons=await settings_menu(uid))
        return
    if action == 'set_sleep':
        try:
            sleep_time = int(text)
            if sleep_time < 10:
                return await event.reply("❌ اقل حاجة 10 ثواني")
            acc['sleep_time'] = sleep_time
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم التعيين: {sleep_time} ثانية", buttons=await settings_menu(uid))
        except:
            await event.reply("❌ رقم غلط")
        return
    if action == 'set_msg_delay':
        try:
            delay = int(text)
            if delay < 1:
                return await event.reply("❌ اقل حاجة ثانية واحدة")
            acc['msg_delay'] = delay
            save_db()
            del waiting_for[uid]
            await event.reply(f"✅ تم التعيين: {delay} ثانية", buttons=await settings_menu(uid))
        except:
            await event.reply("❌ رقم غلط")
        return
    if action == 'edit_name':
        acc['name'] = text
        save_db()
        del waiting_for[uid]
        await event.reply("✅ تم تغيير الاسم", buttons=await settings_menu(uid))
        return
    if action == 'add_group':
        try:
            group = text.strip()
            if group.startswith('@'):
                entity = await bot.get_entity(group)
                gid = entity.id
            else:
                gid = int(group)
            if gid not in acc['groups']:
                acc['groups'].append(gid)
                if gid in acc['banned_groups']:
                    acc['banned_groups'].remove(gid)
                save_db()
                del waiting_for[uid]
                await event.reply(f"✅ تم اضافة الجروب `{gid}`", buttons=await groups_menu(uid))
            else:
                await event.reply("❌ الجروب مضاف قبل كده")
        except:
            await event.reply("❌ ايدي غلط او البوت مش في الجروب")
        return
    if action == 'delete_group':
        try:
            idx = int(text) - 1
            if 0 <= idx < len(acc['groups']):
                gid = acc['groups'].pop(idx)
                save_db()
                del waiting_for[uid]
                await event.reply(f"✅ تم حذف الجروب `{gid}`", buttons=await groups_menu(uid))
            else:
                await event.reply("❌ رقم غلط")
        except:
            await event.reply("❌ ابعت رقم صحيح")
        return
    if action.startswith('edit_msg_'):
        msg_idx = int(action.split('_')[2])
        entities_data = []
        if event.entities:
            for entity in event.entities:
                if isinstance(entity, MessageEntityCustomEmoji):
                    entities_data.append({
                        'type': 'MessageEntityCustomEmoji',
                        'offset': entity.offset,
                        'length': entity.length,
                        'document_id': str(entity.document_id)
                    })
        acc['messages'][msg_idx] = text
        acc['messages_entities'][msg_idx] = json.dumps(entities_data) if entities_data else ''
        save_db()
        del waiting_for[uid]
        await event.reply(f"✅ تم حفظ الرسالة {msg_idx + 1}", buttons=await settings_menu(uid))
        return

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ البوت شغال")
    for uid, user_data in db['users'].items():
        for acc_id, acc in user_data['accounts'].items():
            if acc.get('auto_reply_enabled', False):
                try:
                    await ensure_client_connected(int(uid), acc_id)
                except:
                    pass
    await bot.run_until_disconnected()

if __name__ == '__main__':
    load_db()
    asyncio.run(main())
