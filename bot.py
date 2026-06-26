from telethon import TelegramClient, events, Button, types, functions
from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityBold, MessageEntityItalic, MessageEntityCode, MessageEntityPre, MessageEntityTextUrl, MessageEntityUrl, Channel, LabeledPrice
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError, UserDeactivatedBanError, UserAlreadyParticipantError
from telethon.tl.functions.channels import GetParticipantRequest, JoinChannelRequest
from telethon.errors.rpcerrorlist import ChatWriteForbiddenError, ChatAdminRequiredError, UserBannedInChannelError, SlowModeWaitError, ChannelPrivateError, UserNotParticipantError, AuthKeyUnregisteredError, MessageNotModifiedError
import asyncio
import json
import os
from datetime import datetime, timedelta
import random
import re
import uuid
import aiohttp

# ===== المتغيرات العامة =====
publish_tasks = {}  # دي اللي ناقصة ومسببة NameError
running_tasks = {}  # ضيفها لو بتستخدمها برضو

# ===== بيانات البوت =====
API_ID = 20867472
API_HASH = 'abedd7fb77eaf1f88bd3f286ea952253'
BOT_TOKEN = '8837648752:AAFB6JBi8YuJaY7KucPQZ_kbn_VNjtWmino'
ADMIN_ID = 932862531
DEVELOPER_USERNAME = 'Programmer_error'
DEVELOPER_LINK = f'https://t.me/{DEVELOPER_USERNAME}'
REQUIRED_CHANNELS = ['Programmer_error1']
FORCE_SUB_CHANNEL = "@Programmer_error1"
FORCE_SUB_GROUP = "@Programmer_error2"
DB_FILE = 'database.json'
BACKUP_FILE = 'sessions_backup.json'
FREE_TRIAL_DAYS = 5
GROUP_DELAY = 30 # 5 ثواني بين كل جروب زي ما طلبت
MESSAGE_DELAY = 60 # 3 ثواني بين الرسالتين

# الايموجي البريميوم
SPARK = '<b><tg-emoji emoji-id="5884015001206791984">✨</tg-emoji></b>'
DICE = '<b><tg-emoji emoji-id="5886716969427672960">🎲</tg-emoji></b>'
SUN = '<b><tg-emoji emoji-id="5884250988184870485">🔅</tg-emoji></b>'
BOLT = '<b><tg-emoji emoji-id="5886360482847137476">⚡️</tg-emoji></b>'
SIGNAL = '<b><tg-emoji emoji-id="5886386768046988787">📶</tg-emoji></b>'
GHOST = '<b><tg-emoji emoji-id="5883969276984959097">👾</tg-emoji></b>'
ROCKET = '<b><tg-emoji emoji-id="5886426509379378198">🚀</tg-emoji></b>'
USER = '<b><tg-emoji emoji-id="5886695331382435915">👤</tg-emoji></b>'
PC = '<b><tg-emoji emoji-id="5886664420502805908">💻</tg-emoji></b>'
PLANET = '<b><tg-emoji emoji-id="5886449487454416104">🪐</tg-emoji></b>'
CAT = '<b><tg-emoji emoji-id="5886470240736387171">🐈</tg-emoji></b>'

bot = TelegramClient('bot', API_ID, API_HASH)
db = {'users': {}, 'codes': {}, 'stats': {'total_sent': 0}, 'login_notifications': True, 'pending_crypto': {}}
waiting_for = {}
active_clients = {}
running_tasks = {}
user_clients = {}

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

import json
from datetime import datetime

def backup_sessions():
    backup = {}
    for uid, user in db['users'].items():
        if user.get('account', {}).get('session'):
            acc = user['account']
            backup[str(uid)] = {
                # بيانات الحساب
                'phone': acc.get('phone', ''),
                'session': acc.get('session', ''),
                'name': acc.get('name', 'مجهول'),
                'user_id': uid,
                'groups': acc.get('groups', []),
                'sent_count': acc.get('sent_count', 0),
                'created_at': acc.get('created_at', datetime.now().isoformat()),
                'active': acc.get('active', True),

                # الرسايل 2 بس
                'messages': user.get('messages', [
                    {'type': 'text', 'text': '', 'entities': []},
                    {'type': 'text', 'text': '', 'entities': []}
                ])[:2], # <-- قطع اي زيادة وخليها 2 بس

                # الاعدادات كلها
                'publish_interval': user.get('publish_interval', 120),
                'auto_reply': user.get('auto_reply', False),
                'reply_message': user.get('reply_message', ''),
                'reply_entities': user.get('reply_entities', []),
                'welcome_enabled': user.get('welcome_enabled', False),
                'welcome_message': user.get('welcome_message', ''),
                'welcome_entities': user.get('welcome_entities', []),
                'flood_protection': user.get('flood_protection', 2),
                'stealth_mode': user.get('stealth_mode', 0),
                'subscription': user.get('subscription', {'type': 'free', 'expires_at': None}),
                'trial_used': user.get('trial_used', False),

                'backed_up_at': datetime.now().isoformat()
            }

    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)
        
def get_user_data(uid):
    uid = str(uid)
    if uid not in db['users']:
        db['users'][uid] = {
            'sub_end': None,
            'account': None,
            'messages': [
                {'text': '', 'entities': [], 'file_id': None, 'type': 'text'},
                {'text': '', 'entities': [], 'file_id': None, 'type': 'text'}
            ],
            'publish_interval': 300,
            'flood_protection': 2,
            'stealth_mode': 'medium',
            'auto_reply': True,
            'auto_reply_msg': '',
            'auto_reply_entities': [],
            'welcome_msg': '',
            'welcome_entities': [],
            'welcome_enabled': True,
            'welcome_sent': [],
            'is_trial': False,
            'used_trial': False
        }
        save_db()

    user = db['users'][uid]

    # ضيف المفاتيح الناقصة لو اليوزر قديم
    defaults = {
        'welcome_enabled': True,
        'welcome_sent': [],
        'used_trial': False,
        'auto_reply_entities': [],
        'welcome_entities': [],
        'publish_interval': 300,
        'stealth_mode': 'medium'
    }
    for key, val in defaults.items():
        if key not in user:
            user[key] = val

    # خلي الرسايل 2 بس
    if len(user['messages']) > 2:
        user['messages'] = user['messages'][:2]
    elif len(user['messages']) < 2:
        while len(user['messages']) < 2:
            user['messages'].append({'text': '', 'entities': [], 'file_id': None, 'type': 'text'})

    # لو الرسايل نص بس حولها لديكت
    if isinstance(user['messages'][0], str):
        old_msgs = user['messages']
        user['messages'] = [
            {'text': old_msgs[0] if len(old_msgs) > 0 else '', 'entities': [], 'file_id': None, 'type': 'text'},
            {'text': old_msgs[1] if len(old_msgs) > 1 else '', 'entities': [], 'file_id': None, 'type': 'text'}
        ]

    save_db()
    return user

from datetime import datetime

def is_subscribed(uid):
    if str(uid) == str(ADMIN_ID):
        return True
        
    user = get_user_data(uid)
    sub_end = user.get('sub_end')
    
    if not sub_end:
        return False
        
    try:
        # حول النص لتاريخ وقارن مع دلوقتي
        end_date = datetime.fromisoformat(sub_end)
        return end_date > datetime.now()
    except Exception:
        return False

from datetime import datetime

def get_remaining_days(uid):
    user = get_user_data(uid)
    sub_end = user.get('sub_end')
    
    if not sub_end:
        return 0
        
    try:
        end_date = datetime.fromisoformat(sub_end)
        delta = end_date - datetime.now()
        return max(0, delta.days)
    except Exception:
        return 0

import random

def parse_interval_sec(interval_str):
    """يحول 120-200 لرقم عشوائي بالثواني او 120 لرقم ثابت"""
    interval_str = str(interval_str).strip()

    if '-' in interval_str:
        try:
            parts = interval_str.split('-')
            min_val = int(parts[0])
            max_val = int(parts[1])
            return random.randint(min_val, max_val)
        except Exception:
            return 120 # افتراضي 120 ثانية
    else:
        try:
            return int(interval_str)
        except Exception:
            return 120 # افتراضي 120 ثانية

async def check_force_sub(uid):
    if str(uid) == str(ADMIN_ID):
        return True, []

    not_joined = []

    if FORCE_SUB_CHANNEL:
        try:
            await bot.get_permissions(FORCE_SUB_CHANNEL, uid)
        except UserNotParticipantError:
            not_joined.append(('قناة السورس', FORCE_SUB_CHANNEL))
        except Exception:
            pass

    if FORCE_SUB_GROUP:
        try:
            await bot.get_permissions(FORCE_SUB_GROUP, uid)
        except UserNotParticipantError:
            not_joined.append(('جروب الدعم', FORCE_SUB_GROUP))
        except Exception:
            pass

    return len(not_joined) == 0, not_joined

from datetime import datetime

def get_account(uid):
    user = get_user_data(str(uid))
    acc = user.get('account')
    if not acc:
        return None
    return get_account_defaults(acc)

def get_account_defaults(acc):
    if not acc:
        return None

    defaults = {
        'active': False,
        'groups': [],
        'name': 'حسابك',
        'phone': '',
        'session': '',
        'sent_count': 0,
        'last_error': None,
        'created_at': datetime.now().isoformat(),
        'replied_to': []
    }

    for k, v in defaults.items():
        if k not in acc:
            acc[k] = v

    return acc

def gen_code(days=30):
    code = ''.join(random.choices('ABCDEFGHJKLMNPQXYZ6789', k=6))
    db['codes'][code] = days
    save_db()
    return code

from telethon.tl.types import (
    MessageEntityCustomEmoji, MessageEntityBold, MessageEntityItalic,
    MessageEntityCode, MessageEntityPre, MessageEntityTextUrl, MessageEntityUrl
)

def extract_entities_from_message(message):
    entities = []
    if message.entities:
        for ent in message.entities:
            if isinstance(ent, MessageEntityCustomEmoji):
                entities.append({
                    'type': 'custom_emoji',
                    'offset': ent.offset,
                    'length': ent.length,
                    'document_id': str(ent.document_id)  # خليها string عشان JSON
                })
            elif isinstance(ent, MessageEntityBold):
                entities.append({'type': 'bold', 'offset': ent.offset, 'length': ent.length})
            elif isinstance(ent, MessageEntityItalic):
                entities.append({'type': 'italic', 'offset': ent.offset, 'length': ent.length})
            elif isinstance(ent, MessageEntityCode):
                entities.append({'type': 'code', 'offset': ent.offset, 'length': ent.length})
            elif isinstance(ent, MessageEntityPre):
                entities.append({
                    'type': 'pre', 
                    'offset': ent.offset, 
                    'length': ent.length, 
                    'language': ent.language or ''
                })
            elif isinstance(ent, MessageEntityTextUrl):
                entities.append({
                    'type': 'text_url', 
                    'offset': ent.offset, 
                    'length': ent.length, 
                    'url': ent.url
                })
            elif isinstance(ent, MessageEntityUrl):
                entities.append({'type': 'url', 'offset': ent.offset, 'length': ent.length})
            elif hasattr(ent, 'type'):  # اي نوع تاني
                entities.append({'type': ent.type, 'offset': ent.offset, 'length': ent.length})
    return entities

from telethon.tl.types import (
    MessageEntityCustomEmoji, MessageEntityBold, MessageEntityItalic,
    MessageEntityCode, MessageEntityPre, MessageEntityTextUrl, MessageEntityUrl
)

def build_entities(saved_entities):
    entities = []
    if not saved_entities:
        return entities
        
    for ent in saved_entities:
        try:
            if ent['type'] == 'custom_emoji':
                entities.append(MessageEntityCustomEmoji(
                    offset=ent['offset'],
                    length=ent['length'],
                    document_id=int(ent['document_id'])
                ))
            elif ent['type'] == 'bold':
                entities.append(MessageEntityBold(offset=ent['offset'], length=ent['length']))
            elif ent['type'] == 'italic':
                entities.append(MessageEntityItalic(offset=ent['offset'], length=ent['length']))
            elif ent['type'] == 'code':
                entities.append(MessageEntityCode(offset=ent['offset'], length=ent['length']))
            elif ent['type'] == 'pre':
                entities.append(MessageEntityPre(
                    offset=ent['offset'], 
                    length=ent['length'], 
                    language=ent.get('language', '')
                ))
            elif ent['type'] == 'text_url':
                entities.append(MessageEntityTextUrl(
                    offset=ent['offset'], 
                    length=ent['length'], 
                    url=ent['url']
                ))
            elif ent['type'] == 'url':
                entities.append(MessageEntityUrl(offset=ent['offset'], length=ent['length']))
        except Exception:
            continue  # لو في ايرور في انيتي واحد يكمل عادي
    return entities
    
# واجهة موحدة واحدة بس - كل حاجة هنا
def main_menu(uid):
    user = get_user_data(uid)
    acc = get_account(uid)
    acc = get_account_defaults(acc) if acc else None

    reply_status = "✅" if user['auto_reply'] else "❌"
    welcome_status = "✅" if user['welcome_enabled'] else "❌"
    has_account = "✅" if acc else "❌"
    flood_level = ["❌", "🟡", "🟢", "🛡️"][user['flood_protection']]
    
    # 2 رسايل بس
    msg1 = user['messages'][0] if len(user['messages']) > 0 else None
    msg2 = user['messages'][1] if len(user['messages']) > 1 else None

    def get_msg_status(msg):
        if not msg: return "❌فارغ"
        if msg['type'] == 'sticker': return "🎲ملصق"
        elif msg['text']: return "📝نص"
        else: return "❌فارغ"

    btns = [
        [Button.inline(f"تسجيل الحساب", b"account_info")],
        [Button.inline(f"تسجيل الخروج", b"delete_account")],

        [Button.inline(f"رساله النشر 1 - {get_msg_status(msg1)}", b"msg1"),
         Button.inline(f"رساله النشر 2 - {get_msg_status(msg2)}", b"msg2")],

        [Button.inline(f"النشر كل {user['publish_interval']} ثانية", b"pub_interval")],

        [Button.inline(f"حماية التجميد {flood_level}", b"flood_level")],

        [Button.inline(f"جلب الجروبات", b"fetch_groups"),
         Button.inline(f"الجروبات ({len(acc['groups']) if acc else 0})", b"manage_groups")],

        [Button.inline(f"اضافة جروب", b"add_group"),
         Button.inline(f"تفريغ الكل", b"clear_groups")],
        
        [Button.inline(f"حذف جروب", b"del_group_one"), Button.inline(f"حذف جروبات", b"del_group_many")],
        
        [Button.inline(f"الرد التلقائي {reply_status}", b"toggle_reply"),
         Button.inline(f"الترحيب {welcome_status}", b"toggle_welcome")],

        [Button.inline(f"تعيين الرد", b"set_reply_msg"),
         Button.inline(f"تعيين الترحيب", b"set_welcome_msg")],

        [Button.inline(f"تشغيل النشر", b"start_pub"),
         Button.inline(f"ايقاف النشر", b"stop_pub")],

        [Button.inline(f"تحليل النشر", b"analyze")],
        
        [Button.url(f"المبرمج", DEVELOPER_LINK)]
    ]
    if str(uid) == str(ADMIN_ID):
        btns.insert(-1, [Button.inline(f"لوحة المبرمج", b"admin")])
    return btns

def admin_menu():
    notif_status = "✅" if db.get('login_notifications', True) else "❌"
    return [
        [Button.inline(f"توليد كود", b"gen_code"), Button.inline(f"الاكواد", b"list_codes")],
        [Button.inline(f"تفعيل VIP", b"activate_vip"), Button.inline(f"الغاء VIP", b"deactivate_vip")],
        [Button.inline(f"اشعارات الدخول {notif_status}", b"toggle_notifications")],
        [Button.inline(f"نسخة احتياطية", b"backup_sessions"), Button.inline(f"تحميل النسخ", b"download_backup")],
        [Button.inline(f"المستخدمين", b"users"), Button.inline(f"احصائيات", b"admin_stats")],
        [Button.inline(f"اذاعة", b"broadcast")],
        [Button.inline(f"رجوع", b"back_main")]
    ]

from telethon import TelegramClient
from telethon.sessions import StringSession

user_clients = {} # كاش الكلاينتس

async def get_user_client(uid):
    acc = get_account(uid)
    if not acc or 'session' not in acc:
        return None

    key = str(uid)

    # لو في كلاينت قديم شغال ارجعه
    if key in user_clients:
        try:
            if user_clients[key].is_connected():
                return user_clients[key]
            else:
                await user_clients[key].disconnect()
                del user_clients[key]
        except Exception:
            try:
                del user_clients[key]
            except Exception:
                pass

    # اعمل كلاينت جديد
    try:
        client = TelegramClient(
            StringSession(acc['session']),
            API_ID,
            API_HASH,
            device_model="iPhone 17 Pro",
            system_version="iOS 17.5",
            app_version="10.9.2"
        )
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return None
        user_clients[key] = client
        return client
    except Exception:
        return None

async def log_error(uid, error_text):
    try:
        await bot.send_message(uid, f"{SIGNAL} <b>تشخيص:</b>\n\n{error_text}", parse_mode='html')
    except Exception:
        pass

# التصليح الجذري - بتبعت رسالة جديدة دايما
async def safe_edit(event, text, buttons=None):
    try:
        await event.respond(text, buttons=buttons, parse_mode='html')
    except Exception:
        pass

from telethon.tl.functions.channels import GetParticipantRequest

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    user = get_user_data(uid)

    is_sub, not_joined = await check_force_sub(uid)
    if not is_sub:
        text = f"{ROCKET}<b>عشان تستخدم البوت لازم تشترك هنا:</b>\n\n"
        btns = []
        for typ, link in not_joined:
            text += f"📶 {typ}: {link}\n"
            btns.append([Button.url(f"اشترك في {typ}", f"https://t.me/{link.replace('@', '')}")])
        btns.append([Button.inline(f"تحققت", b"check_sub")])
        await event.reply(text, buttons=btns, parse_mode='html')
        return

    for channel in REQUIRED_CHANNELS:
        try:
            await bot(GetParticipantRequest(channel, uid))
        except Exception:
            btns = [
                [Button.url(f"اشترك هنا اولا", f"https://t.me/{channel}")],
                [Button.inline(f"تحققت", b"check_sub")]
            ]
            await event.reply(f"{BOLT}<b>اشترك في القناة اولا</b>", buttons=btns, parse_mode='html')
            return

    if not is_subscribed(uid):
        btns = [
            [Button.inline(f"تجربة مجانية", b"free_trial")],
            [Button.inline(f"تفعيل كود", b"activate")],
            [Button.url(f"المبرمج", DEVELOPER_LINK)]
        ]
        await event.reply(f"{PLANET}<b>لازم اشتراك عشان تستخدم البوت</b>{USER}", buttons=btns, parse_mode='html')
        return

    # لو كله تمام اعرض المنيو + احصائيات
    acc = get_account(uid)
    acc = get_account_defaults(acc) if acc else None
    days = get_remaining_days(uid)
    sent = acc['sent_count'] if acc else 0

    text = f"{SPARK} <b>أهلاً بيك في بوت النشر المتطور الاحترافي</b>\n\n"
    text += f"{SPARK} <b>الاشتراك: {days} يوم متبقي</b>\n"
    text += f"{SPARK} <b>الرسائل المرسله: {sent}</b>\n"
    text += f"{SPARK} <b>النشر: {'يعمل' if acc and acc['active'] else 'متوقف'}</b>\n\n"
    text += f"{SPARK} <b>كل شيئ في واجهة واحدة</b>"

    await event.reply(text, buttons=main_menu(uid), parse_mode='html')

from datetime import datetime, timedelta

@bot.on(events.CallbackQuery(data=b'check_sub'))
async def check_sub(event):
    await event.delete()
    await start(event)

@bot.on(events.CallbackQuery)
async def callback(event):
    uid = event.sender_id
    data = event.data.decode()
    user = get_user_data(uid)
    acc = get_account(uid)

    await event.answer()

    # رجوع للمنيو
    if data == 'back_main':
        await start(event)
        return

    elif data == 'check_sub':
        await start(event)
        return

    # تسجيل برقم الهاتف
    elif data == 'login_phone':
        waiting_for[uid] = 'phone_login'
        await safe_edit(event, f"{PC}<b>ابعت رقم الحساب:</b>\n\n{PC} مثال: +201234567890\n{PC} الكود هيوصل على تيليجرام الرقم", buttons=[[Button.inline(f"رجوع", b"back_main")]])

    # تسجيل بسيشن
    elif data == 'login_session':
        waiting_for[uid] = 'session_login'
        await safe_edit(event, f"{PC}<b>ابعت جلسة السيشن StringSession:</b>\n\n{PC} مثال: 1BQAJ... طويلة\n{PC} لو مو معك سيشن راسل المبرمج @Programmer_error", buttons=[[Button.inline(f"رجوع", b"back_main")]])

    # المنيو الرئيسي
    elif data == 'main_menu':
        await event.edit(f"{BOLT}<b>المنيو الرئيسي</b>", buttons=main_menu(uid), parse_mode='html')

    # ادارة الحساب
    elif data == 'add_account':
        btns = [
            [Button.inline("برقم الهاتف", b"login_phone")],
            [Button.inline("بسيشن جاهز", b"login_session")],
            [Button.inline("رجوع", b"back_main")]
        ]
        await event.edit(f"{PC}<b>اختار طريقة التسجيل</b>", buttons=btns, parse_mode='html')

    # ادارة الجروبات
    elif data == 'manage_groups':
        groups = acc.get('groups', []) if acc else []
        text = f"📢 <b>الجروبات: {len(groups)}</b>\n\n"
        text += "ابعتلنا يوزر الجروب او الايدي" if not groups else "\n".join([f"• {g}" for g in groups[:5]])
        await event.edit(text, buttons=[[Button.inline("رجوع", b"back_main")]], parse_mode='html')

    # ادارة الرسايل - 2 بس
    elif data == 'manage_msgs':
        msgs = user.get('messages', [])[:2]
        text = f"📝 <b>الرسايل: {len(msgs)}/2</b>\n\nابعتلنا الرسالة 1 او 2"
        await event.edit(text, buttons=[[Button.inline("رجوع", b"back_main")]], parse_mode='html')

    # تشغيل النشر
    elif data == 'start_pub':
        if not acc or not acc.get('session'):
            await event.answer("سجل الحساب اولاً", alert=True)
            return
        if not user.get('messages')[:2] or not acc.get('groups'):
            await event.answer("ضيف رسايل وجروبات اولاً", alert=True)
            return

        acc['active'] = True
        publish_tasks[str(uid)] = True
        asyncio.create_task(publish_loop(uid))
        await event.edit("🚀 <b>تم تشغيل النشر</b>", buttons=main_menu(uid), parse_mode='html')

    # ايقاف النشر
    elif data == 'stop_pub':
        if acc:
            acc['active'] = False
        publish_tasks[str(uid)] = False
        await event.edit("⏸️ <b>تم ايقاف النشر</b>", buttons=main_menu(uid), parse_mode='html')

    # تجربة مجانية
    elif data == 'free_trial':
        if user.get('used_trial'):
            await event.answer("استخدمت التجربة المجانية قبل كده", alert=True)
            return

        user['sub_end'] = (datetime.now() + timedelta(days=FREE_TRIAL_DAYS)).isoformat()
        user['is_trial'] = True
        user['used_trial'] = True
        save_db()

        await event.answer(f"تم تفعيل التجربة المجانية", alert=True)
        await safe_edit(event, f"{ROCKET}<b>مبروك! حصلت على تجربة مجانية {FREE_TRIAL_DAYS} يوم</b>\n\n{USER}<b>تقدر تبدأ النشر دلوقتي</b>", buttons=[[Button.inline(f"ابدأ النشر", b"back_main")]])

        try:
            await bot.send_message(ADMIN_ID, f"{PC}<b>تجربة مجانية جديدة</b>\n\n👤 المستخدم: <code>{uid}</code>\n📶 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
        except Exception:
            pass
        return

    elif data == 'account_info':
        acc = get_account(uid)
        
        # لو مفيش حساب اعرض طرق التسجيل
        if not acc:
            text = f"{PC}<b>اختار طريقة تسجيل الحساب:</b>\n\n{PC}1. برقم الهاتف\n{PC} الكود هيوصل على تيليجرام الرقم\n{PC}2. جلسة سيشن StringSession\n{PC} اسرع وبدون انتظار كود"
            btns = [
                [Button.inline(f"تسجيل برقم الهاتف", b"login_phone")],
                [Button.inline(f"تسجيل بجلسة سيشن", b"login_session")],
                [Button.inline(f"رجوع", b"back_main")]
            ]
            await safe_edit(event, text, buttons=btns)
            return
        
        # لو فيه حساب اعرض المعلومات
        acc = get_account_defaults(acc)
        text = f"{PC}<b>معلومات الحساب</b>\n\n"
        text += f"{PC}الاسم: <b>{acc['name']}</b>\n"
        text += f"{PC}الرقم: <code>{acc['phone']}</code>\n"
        text += f"{PC}المرسلة: {acc['sent_count']}\n"
        text += f"{PC}الجروبات: {len(acc['groups'])}\n"
        text += f"{PC}الحالة: {'يعمل' if acc['active'] else 'متوقف'}\n"
        text += f"{PC}تاريخ الاضافة: {acc['created_at'][:10]}\n\n"
        
        btns = [
            [Button.inline(f"{'❎ايقاف' if acc['active'] else '✅تشغيل'}", b"toggle_account")],
            [Button.inline(f"تغيير الاسم", b"rename_account")],
            [Button.inline(f"حذف الحساب", b"delete_account")],
            [Button.inline(f"رجوع", b"back_main")]
        ]
        await safe_edit(event, text, buttons=btns)
        return
        
    elif data == 'msg1':
        waiting_for[uid] = 'msg1'
        await safe_edit(event, f"{PC}<b>ابعت الرسالة الاولى:</b>\n\n{BOLT}تقدر تبعت نص مع ايموجي بريميوم او ملصق\n{USER}البوت هيحفظه وينشره", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'msg2':
        waiting_for[uid] = 'msg2'
        await safe_edit(event, f"{PC}<b>ابعت الرسالة التانية:</b>\n\n{BOLT}تقدر تبعت نص مع ايموجي بريميوم او ملصق\n{USER}البوت هيبدل بينهم تلقائي", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'toggle_reply':
        user['auto_reply'] = not user['auto_reply']
        save_db()
        status = "✅مفعل" if user['auto_reply'] else "❎معطل"
        await event.answer(f"الرد التلقائي: {status}", alert=True)
        await safe_edit(event, f"<b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'toggle_welcome':
        user['welcome_enabled'] = not user['welcome_enabled']
        save_db()
        status = "✅مفعل" if user['welcome_enabled'] else "❎معطل"
        await event.answer(f"الترحيب: {status}", alert=True)
        await safe_edit(event, f"<b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'activate':
        waiting_for[uid] = 'code'
        await safe_edit(event, f"{DICE} <b>ارسل كود التفعيل:</b>", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'fetch_groups':
        acc = get_account(uid)
        if not acc:
            text = f"{USER} <b>اختار طريقة تسجيل الحساب اولاً:</b>"
            btns = [
                [Button.inline(f"تسجيل برقم", b"login_phone")],
                [Button.inline(f"تسجيل بسيشن", b"login_session")],
                [Button.inline(f"رجوع", b"back_main")]
            ]
            await safe_edit(event, text, buttons=btns)
            return

        msg = await event.respond(f"{ROCKET} <b>جاري جلب ايدي الجروبات...</b>\n{SIGNAL} دي اسرع وبتستحمل 1000+ حساب", parse_mode='html')
        client = await get_user_client(uid)
        if not client or not client.is_connected():
            await msg.edit(f"{BOLT} <b>الحساب غير متصل</b>", buttons=[[Button.inline(f"رجوع", b"back_main")]], parse_mode='html')
            return

        groups = []
        total_dialogs = 0
        try:
            async for dialog in client.iter_dialogs():
                total_dialogs += 1
                # ناخد ID بس، سواء يوزر موجود او لا
                if dialog.is_group or getattr(dialog.entity, 'megagroup', False) or getattr(dialog.entity, 'gigagroup', False):
                    if not getattr(dialog.entity, 'broadcast', False):
                        groups.append(f"-100{dialog.entity.id}")
                        
                # ريست كل 200 محادثة عشان ميعملش FloodWait مع 1000 حساب
                if total_dialogs % 200 == 0:
                    await asyncio.sleep(1)

        except Exception as e:
            await msg.edit(f"{BOLT} <b>خطأ في الجلب:</b> <code>{str(e)}</code>", buttons=[[Button.inline(f"رجوع", b"back_main")]], parse_mode='html')
            return

        acc = get_account_defaults(acc)
        acc['groups'] = groups  # هنا بنحفظ ID بس
        db['users'][str(uid)]['account'] = acc
        save_db()
        
        await msg.edit(f"{SPARK} <b>تم جلب {len(groups)} جروب</b>\n\n{ROCKET} اجمالي المحادثات: {total_dialogs}\n{PC} محفوظ بالـ ID بس - اسرع للنشر", buttons=main_menu(uid), parse_mode='html')
        return

    elif data == 'manage_groups':
        acc = get_account(uid)
        if not acc:
            await event.answer(f"{BOLT}ضيف حساب الاول", alert=True)
            return

        acc = get_account_defaults(acc)
        groups = acc.get('groups', [])

        if not groups:
            groups_text = f"{GHOST}لا يوجد جروبات مضافة"
        else:
            groups_text = ""
            for i, g in enumerate(groups[:30], 1):
                groups_text += f"<b>{i}.</b> <code>{g}</code>\n"
            
            if len(groups) > 30:
                groups_text += f"\n{SIGNAL}... و {len(groups)-30} جروب اخر\n{SIGNAL}استخدم 'حذف برقم' للباقي"

        btns = [
            [Button.inline(f"➕ اضافة يدوي", b"add_group"), Button.inline(f"🗑️ حذف برقم", b"del_group_num")],
            [Button.inline(f"🗑️ حذف يدوي", b"del_group"), Button.inline(f"🧹 تفريغ الكل", b"clear_groups")],
            [Button.inline(f"🔄 جلب تلقائي", b"fetch_groups")],
            [Button.inline(f"🔙 رجوع", b"back_main")]
        ]
        
        await safe_edit(
            event, 
            f"{ROCKET} <b>ادارة الجروبات</b>\n\n{USER} العدد: <code>{len(groups)}</code>\n\n{groups_text}", 
            buttons=btns,
            parse_mode='html'
        )
        return
        
    elif data == 'clear_groups':
        acc = get_account(uid)
        if not acc:
            await event.answer(f"{BOLT}ضيف حساب الاول", alert=True)
            return
            
        acc = get_account_defaults(acc)
        acc['groups'] = []
        db['users'][str(uid)]['account'] = acc
        save_db()
        
        await event.answer(f"تم تفريغ كل الجروبات", alert=True)
        await safe_edit(event, f"<b>الجروبات (0):</b>\n\nلا يوجد", buttons=[
            [Button.inline(f"اضافة", b"add_group"), Button.inline(f"حذف", b"del_group")],
            [Button.inline(f"تفريغ الكل", b"clear_groups")],
            [Button.inline(f"رجوع", b"back_main")]
        ])
        return

    elif data == 'add_group':
        waiting_for[uid] = 'add_groups_manual'
        await safe_edit(event, f"{USER} <b>ابعت يوزر الجروب او الايدي سطر سطر:</b>\n\n{SIGNAL} مثال:\n<code>@Programmer_error2\n-1001234567890\n@another_group</code>\n\n{PC} كل سطر = جروب\n{BOLT} مهم: الحساب لازم يكون عضو\n{BOLT} ابعت /done لما تخلص", buttons=[[Button.inline(f"رجوع", b"manage_groups")]])
        return

    elif data == 'del_group':
        waiting_for[uid] = 'del_groups_manual'
        await safe_edit(event, f"{BOLT} <b>ابعت الجروبات للحذف سطر سطر:</b>\n\n{SIGNAL} مثال:\n<code>@Programmer_error2\n-1001234567890\n3</code>\n\n{PC} تقدر تبعت يوزر او ايدي او رقم الترتيب\n{BOLT} ابعت /done لما تخلص", buttons=[[Button.inline(f"رجوع", b"manage_groups")]])
        return

    elif data == 'pub_interval':
        waiting_for[uid] = 'pub_interval'
        await safe_edit(event, f"{ROCKET} <b>ابعت الوقت بين كل دورة نشر بالثواني:</b>\n\n{SIGNAL} مثال: 120 او 120-150\n{PC} 120 = ثابت كل دقيقتين\n{PC} 120-150 = عشوائي بين دقيقتين و دقيقتين ونص\n{SUN} اقل حاجة: 120 ثانية = 2 دقيقة", buttons=[[Button.inline(f"رجوع", b"manage_groups")]])

    elif data == 'flood_level':
        user['flood_protection'] = (user['flood_protection'] + 1) % 4
        save_db()
        await safe_edit(event, f"<b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'stealth_mode':
        modes = list(STEALTH_MODES.keys())
        current = modes.index(user['stealth_mode'])
        user['stealth_mode'] = modes[(current + 1) % len(modes)]
        save_db()
        await safe_edit(event, f"<b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'set_reply_msg':
        waiting_for[uid] = 'reply_msg'
        text = f"{SIGNAL} <b>ارسل رسالة الرد التلقائي:</b>\n\n"
        text += f"{BOLT} <b>دي هتتبعت لما حد يعملك منشن او ريبلاي</b>\n"
        text += f"{SPARK} <b>تقدر تستخدم ايموجي بريميوم</b>"
        buttons = [
            [Button.inline(f"ايقاف الرد التلقائي", b"stop_reply")],
            [Button.inline(f"رجوع", b"back_main")]
        ]
        await safe_edit(event, text, buttons=buttons)
        return

    elif data == 'set_welcome_msg':
        waiting_for[uid] = 'welcome_msg'
        text = f"{SIGNAL} <b>ارسل رسالة الترحيب:</b>\n\n"
        text += f"{BOLT} <b>دي هتتبعت لاي حد يبعتلك خاص اول مرة</b>\n"
        text += f"{SPARK} <b>تقدر تستخدم ايموجي بريميوم</b>"
        buttons = [
            [Button.inline(f"ايقاف رسالة الترحيب", b"stop_welcome")],
            [Button.inline(f"رجوع", b"back_main")]
        ]
        await safe_edit(event, text, buttons=buttons)
        return

    elif data == 'stop_reply':
        user['auto_reply_msg'] = ''
        user['auto_reply_entities'] = []
        save_db()
        await event.answer("تم ايقاف الرد التلقائي")
        text = f"{BOLT} <b>تم ايقاف الرد التلقائي بنجاح</b>\n\n"
        text += f"{SIGNAL} <b>مش هيرد على المنشن والريبلاي دلوقتي</b>"
        await safe_edit(event, text, buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'stop_welcome':
        user['welcome_msg'] = ''
        user['welcome_entities'] = []
        save_db()
        await event.answer("تم ايقاف رسالة الترحيب")
        text = f"{BOLT} <b>تم ايقاف رسالة الترحيب بنجاح</b>\n\n"
        text += f"{SIGNAL} <b>مش هيبعت ترحيب للخاص دلوقتي</b>"
        await safe_edit(event, text, buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'start_pub':
        acc = get_account(uid)
        if not acc:
            await event.answer("{PC} ضيف حساب الاول", alert=True)
            return

        acc = get_account_defaults(acc)
        if not acc['groups']:
            await event.answer("{DICE} ضيف جروبات الاول - جلب الجروبات", alert=True)
            return

        user_data = db['users'][str(uid)]
        msgs = user_data.get('messages', [])
        if not msgs or (not msgs[0].get('text') and not msgs[0].get('file_id')):
            await event.answer("{DICE} ضيف رسالة على الاقل - رسالة 1", alert=True)
            return

        # فعل النشر
        acc['active'] = True
        acc['last_error'] = None
        user['account'] = acc
        save_db()

        key = str(uid)

        # اوقف اي تاسك قديم الاول
        if key in running_tasks:
            try:
                running_tasks[key].cancel()
                await asyncio.sleep(0.5)
            except:
                pass
            del running_tasks[key]

        # ابدأ تاسك جديد
        task = asyncio.create_task(publish_loop(uid))
        running_tasks[key] = task

        # شغل الرد التلقائي لو مفعل
        if user.get('auto_reply'):
            asyncio.create_task(start_auto_reply(uid))

        await event.answer("{PC} بدأ النشر بنجاح", alert=True)
        await safe_edit(event, f"{PC} <b>الواجهة الرئيسية</b>\n\n🚀 النشر شغال على {len(acc['groups'])} جروب", buttons=main_menu(uid))
        await log_error(uid, f'{PC} بدأ النشر - {len(acc["groups"])} جروب')
        return

    elif data == 'stop_pub':
        acc = get_account(uid)
        if acc:
            acc = get_account_defaults(acc)
            acc['active'] = False
            user['account'] = acc
            save_db()
            key = str(uid)
            if key in running_tasks:
                try:
                    running_tasks[key].cancel()
                    await asyncio.sleep(0.5)
                except:
                    pass
                del running_tasks[key]
        await event.answer("تم الايقاف", alert=True)
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        await log_error(uid, f'{BOLT} تم ايقاف النشر يدوي')
        return

    elif data == 'analyze':
        acc = get_account(uid)
        if not acc:
            await event.answer(f"{PC} ضيف حساب الاول", alert=True)
            return
            
        acc = get_account_defaults(acc)

        # اتأكد من حالة الاتصال صح
        status = "غير معروف"
        try:
            client = await get_user_client(uid)
            if client and client.is_connected():
                me = await client.get_me()
                status = f"{SPARK}سليم - {me.first_name}"
            else:
                status = f"{BOLT}غير متصل"
        except:
            status = f"{DICE}محظور او منتهي"

        # بيانات الحساب
        groups_count = len(acc.get('groups', []))
        msgs = db['users'][str(uid)].get('messages', [])
        msgs_count = len([m for m in msgs if m.get('text') or m.get('file_id')])
        
        # الفاصل الزمني
        mn = acc.get('interval_min', 120)
        mx = acc.get('interval_max', 250)
        if mn == mx:
            interval_text = f"{mn} ثانية"
        else:
            interval_text = f"{mn}-{mx} ثانية"

        text = f"{PLANET} <b>تحليل وضع النشر</b>\n\n"
        text += f"{USER} الحساب: <code>{acc['name']}</code>\n"
        text += f"{ROCKET} الرقم: <code>{acc['phone']}</code>\n"
        text += f"{SIGNAL} الحالة: {status}\n"
        text += f"{DICE} الجروبات: {len(acc['groups'])}\n"
        text += f"{SPARK} المرسلة: {acc['sent_count']}\n"
        text += f"{BOLT} النشر كل: {user['publish_interval']} دقيقة\n"
        text += f"{SUN} حماية الفلود: مستوى {user['flood_protection']}\n"
        text += f"{CAT} مردود عليهم: {len(acc['replied_to'])} شخص\n"
        text += f"{PC} اخر خطأ: {acc.get('last_error') or 'لا يوجد'}\n"
        text += f"{SIGNAL} النشر: {'يعمل' if acc['active'] else 'متوقف'}\n\n"

        if acc.get('last_error'):
            text += f"{BOLT} <b>تحذير:</b> {acc['last_error']}\n"
            text += f"{SIGNAL} فعل وضع آمن جدا لو متكرر"
        else:
            text += f"{SPARK} <b>الحساب آمن</b> - كمل النشر"

        await safe_edit(event, text, buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'gen_code':
        if uid!= ADMIN_ID:
            return
        code = gen_code(30)
        await event.answer(f"الكود اتنسخ في الرسالة", alert=True)
        await event.respond(f"{DICE} <b>كود 30 يوم:</b>\n\n<code>{code}</code>\n\n{SIGNAL} انسخ الكود وابعت للعميل", parse_mode='html')
        return

    elif data == 'list_codes':
        if uid!= ADMIN_ID:
            return
        codes_text = "\n".join([f"{SIGNAL} <code>{code}</code> - {days} يوم" for code, days in db['codes'].items()]) or "لا يوجد اكواد"
        await safe_edit(event, f"{BOLT} <b>الاكواد المتاحة:</b>\n\n{codes_text}", buttons=[[Button.inline(f"رجوع", b"admin")]])
        return

    elif data == 'activate_vip':
        if uid!= ADMIN_ID:
            return
        waiting_for[uid] = 'vip_activate'
        await safe_edit(event, f"{USER} <b>ابعت ID المستخدم + عدد الايام</b>\n\n{SIGNAL} مثال: 123456789 30\n{BOLT} يعني فعل 30 يوم", buttons=[[Button.inline(f"رجوع", b"admin")]])
        return

    elif data == 'deactivate_vip':
        if uid!= ADMIN_ID:
            return
        waiting_for[uid] = 'vip_deactivate'
        await safe_edit(event, f"{USER} <b>ابعت ID المستخدم للالغاء</b>\n\n{SIGNAL} مثال: 123456789", buttons=[[Button.inline(f"رجوع", b"admin")]])
        return

    elif data == 'toggle_notifications':
        if uid!= ADMIN_ID:
            return
        db['login_notifications'] = not db.get('login_notifications', True)
        save_db()
        await safe_edit(event, f"{USER} <b>لوحة المبرمج</b>", buttons=admin_menu())
        return

    elif data == 'backup_sessions':
        if uid != ADMIN_ID:
            await event.answer(f"{BOLT}ممنوع - ادمن فقط", alert=True)
            return
            
        await event.answer(f"{SPARK}جاري عمل النسخة...", alert=True)
        
        try:
            backup_sessions()
            await safe_edit(event, f"✅<b>تم عمل نسخة احتياطية</b>\n\n{SPARK} كل ملفات الجلسات اتنسخت\n{PC} المسار: /sessions_backup/\n{SIGNAL} التاريخ: الوقت الحالي", buttons=[[Button.inline(f"{BOLT}رجوع", b"back_main")]])
        except Exception as e:
            await safe_edit(event, f"❎<b>فشل النسخ</b>\n\n{BOLT} الخطأ: <code>{e}</code>", buttons=[[Button.inline(f"{BOLT}رجوع", b"back_main")]])
        return

    elif data == 'download_backup':
        if uid != ADMIN_ID:
            await event.answer(f"❎ممنوع - مبرمج فقط", alert=True)
            return
            
        try:
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                pass # نتأكد ان الملف موجود بس
            
            caption = f"{PLANET} <b>النسخة الاحتياطية - db.json</b>\n\n{SPARK} ده ملف الداتا كامل\n{SIGNAL} نزل الملف واحفظه عندك امان"
            await event.respond(caption, file=BACKUP_FILE, parse_mode='html')
            await event.answer(f"✅تم الارسال", alert=True)
            
        except FileNotFoundError:
            await event.answer(f"✅مفيش نسخة احتياطية - اعمل backup الاول", alert=True)
        except Exception as e:
            await event.answer(f"❎خطأ: {str(e)}", alert=True)
        return

    elif data == 'users':
        if uid!= ADMIN_ID:
            return
        users_list = []
        for user_id, user_data in db['users'].items():
            sub_status = "مفعل" if is_subscribed(int(user_id)) else "غير مفعل"
            has_acc = "✅" if user_data.get('account') else "❌"
            trial = "تجربة" if user_data.get('is_trial') else ""
            users_list.append(f"{SIGNAL} <code>{user_id}</code> - {sub_status} {trial} - حساب: {has_acc}")
        text = "\n".join(users_list[:30]) or "لا يوجد مستخدمين"
        await safe_edit(event, f"{SUN} <b>المستخدمين:</b>\n\n{text}", buttons=[[Button.inline(f"رجوع", b"admin")]])
        return

    elif data == 'admin_stats':
        if uid!= ADMIN_ID:
            return
        total_users = len(db['users'])
        active_subs = sum(1 for u in db['users'].keys() if is_subscribed(int(u)))
        total_sent = db['stats']['total_sent']
        text = f"{DICE} <b>احصائيات البوت</b>\n\n"
        text += f"{SUN} اجمالي المستخدمين: {total_users}\n"
        text += f"{SPARK} الاشتراكات الفعالة: {active_subs}\n"
        text += f"{ROCKET} اجمالي الرسائل: {total_sent}\n"
        await safe_edit(event, text, buttons=[[Button.inline(f"رجوع", b"admin")]])
        return

    elif data == 'broadcast':
        if uid!= ADMIN_ID:
            await event.answer(f"ممنوع - مبرمج فقط", alert=True)
            return

        waiting_for[uid] = 'broadcast'
        await safe_edit(
            event,
            f"{ROCKET} <b>وضع الاذاعة</b>\n\n"
            f"{DICE} ابعت الرسالة اللي عايز تذيعها لكل المستخدمين\n"
            f"{BOLT} تحذير: الرسالة هتتبعت لكل اللي ضغطوا /start قبل كده\n"
            f"{SIGNAL} تقدر تبعت نص او صورة + كابشن\n"
            f"{PC} دوس رجوع لو لغيت",
            buttons=[[Button.inline(f"رجوع", b"admin")]]
        )
        return

    elif data == 'toggle_account':
        acc = get_account(uid)
        if not acc:
            await event.answer(f"ضيف حساب الاول", alert=True)
            return
            
        acc = get_account_defaults(acc)
        acc['active'] = not acc['active']
        
        db['users'][str(uid)]['account'] = acc
        save_db()
        
        status = f"✅تم التشغيل" if acc['active'] else f"❎تم الايقاف"
        await event.answer(status, alert=True)
        
        # نحدث الواجهة ونعرض الحالة الجديدة
        acc = get_account_defaults(get_account(uid))
        state_icon = f"✅شغال" if acc['active'] else f"❎متوقف"
        
        await safe_edit(
            event, 
            f"<b>الواجهة الرئيسية</b>\n\nحالة الحساب: {state_icon}", 
            buttons=main_menu(uid)
        )
        return

    elif data == 'delete_account':
        acc = get_account(uid)
        if not acc:
            await event.answer(f"{BOLT}مفيش حساب اصلا", alert=True)
            return

        key = str(uid)
        if key in active_clients:
            try:
                await active_clients[key].disconnect()
            except:
                pass
            del active_clients[key]

        db['users'][str(uid)]['account'] = None
        save_db()

        await event.answer(f"{DICE}تم حذف الحساب نهائيا", alert=True)
        await safe_edit(
            event,
            f"{ROCKET} <b>الواجهة الرئيسية</b>\n\n{BOLT} تم حذف الحساب والجلسة\n{PC} تقدر تضيف حساب جديد دلوقتي",
            buttons=main_menu(uid)
        )
        return

@bot.on(events.NewMessage)
async def handle_messages(event):
    uid = event.sender_id
    if uid not in waiting_for:
        return

    action = waiting_for[uid]
    msg = event.message
    text = msg.text # استخدم text مش raw_text عشان الـ offset يظبط

    # استخدم db مباشر عشان نتأكد اليوزر موجود
    if str(uid) not in db['users']:
        db['users'][str(uid)] = {'account': None, 'messages': [], 'sub_end': None, 'is_trial': True}
        save_db()

    user = db['users'][str(uid)]
    acc = get_account(uid)

    if action == 'code':
        code = text.strip()
        if code in db['codes']:
            days = db['codes'][code]
            user['sub_end'] = (datetime.now() + timedelta(days=days)).isoformat()
            user['is_trial'] = False
            del db['codes'][code]
            save_db()
            del waiting_for[uid]
            await event.reply(f"{SPARK} <b>تم التفعيل {days} يوم</b>", parse_mode='html')
            await start(event)
        else:
            await event.reply(f"{BOLT} <b>كود غلط او مستخدم</b>", parse_mode='html')
            return

    elif action in ['add_msg1', 'add_msg2']:
        # هنا حفظ التنسيق تلقائي
        msg_data = {
            'type': 'text',
            'text': text, # النص العادي
            'entities': extract_entities_from_message(msg) # التنسيق من تيليجرام
        }

        if action == 'add_msg1':
            user['messages'][0] = msg_data
        else:
            if len(user['messages']) < 2:
                user['messages'].append(msg_data)
            else:
                user['messages'][1] = msg_data

        save_db()
        del waiting_for[uid]
        await event.reply(f"{PC} ✅ تم حفظ الرسالة بالتنسيق")
        await main_menu(event, uid)
        return

    elif action == 'vip_activate':
        if uid!= ADMIN_ID:
            await event.answer(f"{BOLT}ممنوع - ادمن فقط", alert=True)
            return

        try:
            parts = text.strip().split()
            if len(parts)!= 2:
                raise ValueError

            target_id = parts[0]
            days = int(parts[1])

            # انشاء اليوزر لو مش موجود
            if target_id not in db['users']:
                db['users'][target_id] = {
                    'account': None,
                    'messages': [],
                    'sub_end': None,
                    'is_trial': True
                }

            target_user = db['users'][target_id]
            end_date = datetime.now() + timedelta(days=days)

            target_user['sub_end'] = end_date.isoformat()
            target_user['is_trial'] = False
            save_db()
            del waiting_for[uid]

            end_str = end_date.strftime('%Y-%m-%d')
            await event.reply(
                f"{SPARK} <b>تم تفعيل VIP للمستخدم</b>\n\n"
                f"{USER} ID: <code>{target_id}</code>\n"
                f"{ROCKET} المدة: {days} يوم\n"
                f"{DICE} ينتهي: {end_str}",
                parse_mode='html'
            )

            try:
                await bot.send_message(
                    int(target_id),
                    f"{PLANET} <b>تم تفعيل اشتراكك!</b>\n\n"
                    f"{SPARK} المدة: {days} يوم\n"
                    f"{BOLT} ينتهي: {end_str}\n\n"
                    f"{SIGNAL} ارسل /start للبدء",
                    parse_mode='html'
                )
            except:
                pass

        except Exception:
            await event.reply(
                f"{BOLT} <b>صيغة غلط</b>\n\n"
                f"{SIGNAL} المثال الصحيح:\n"
                f"<code>123456789 30</code>\n\n"
                f"{PC} ID مسافة عدد الايام",
                parse_mode='html'
            )

    elif action == 'vip_deactivate':
        if uid!= ADMIN_ID:
            await event.answer(f"{BOLT}ممنوع - ادمن فقط", alert=True)
            return

        target_id = text.strip()

        if target_id not in db['users']:
            await event.reply(f"{BOLT} <b>اليوزر ده مش موجود في الداتا</b>", parse_mode='html')
            del waiting_for[uid]
            return

        target_user = db['users'][target_id]
        target_user['sub_end'] = None
        target_user['is_trial'] = False
        save_db()
        del waiting_for[uid]

        await event.reply(
            f"{BOLT} <b>تم الغاء VIP</b>\n\n"
            f"{USER} ID: <code>{target_id}</code>\n"
            f"{DICE} الاشتراك: متوقف",
            parse_mode='html'
        )

        try:
            await bot.send_message(
                int(target_id),
                f"{SIGNAL} <b>تم الغاء اشتراكك</b>\n\n"
                f"{BOLT} تواصل مع المطور لتجديد الاشتراك\n"
                f"{USER} @{DEVELOPER_USERNAME}",
                parse_mode='html'
            )
        except:
            pass

    elif action == 'broadcast':
        if uid!= ADMIN_ID:
            await event.answer(f"{BOLT}ممنوع - ادمن فقط", alert=True)
            return

        waiting_for.pop(uid)
        msg_text = text.strip() if text else ""
        media = event.message.media

        users_sent = 0
        users_failed = 0

        status_msg = await event.reply(f"{SPARK} بدأت الاذاعة... 0/{len(db['users'])}")
        
        for user_id in list(db['users'].keys()):
            try:
                if media:
                    await bot.send_file(int(user_id), media, caption=msg_text)
                else:
                    await bot.send_message(int(user_id), f"{BOLT} <b>اعلان من الادارة</b>\n\n{msg_text}", parse_mode='html')
                users_sent += 1
            except:
                users_failed += 1

            await asyncio.sleep(0.08) # 80ms عشان نتفادى FloodWait

            # تحديث العداد كل 20 يوزر
            if (users_sent + users_failed) % 20 == 0:
                await status_msg.edit(f"{SPARK} جاري الارسال... {users_sent + users_failed}/{len(db['users'])}")

        await status_msg.edit(
            f"{ROCKET} <b>خلصت الاذاعة</b>\n\n"
            f"{SPARK} وصلت: {users_sent}\n"
            f"{BOLT} فشل: {users_failed}\n"
            f"{USER} الاجمالي: {len(db['users'])}",
            parse_mode='html'
        )

    elif action == 'phone_login':
        phone = text.strip()
        client = TelegramClient(StringSession(), API_ID, API_HASH, device_model="iPhone 17 Pro", system_version="iOS 17.5", app_version="10.9.2")
        await client.connect()
        try:
            sent = await client.send_code_request(phone)
            waiting_for[uid] = f'login_code_{phone}_{sent.phone_code_hash}'
            active_clients[str(uid)] = client
            await event.reply(f"{SPARK} <b>الكود اتبعت على تيليجرام ارسل الكود كذا 7 6 4 8 5 بمسافات فقط</b>\n\n{SIGNAL} ابعته هنا:", parse_mode='html')
        except Exception as e:
            await event.reply(f"{BOLT} <b>خطأ:</b> {str(e)}\n\n{SIGNAL} <b>اتأكد من الرقم بصيغة دولية</b>\n{SIGNAL} مثال: <code>+201234567890</code>", parse_mode='html')
            del waiting_for[uid]
            await client.disconnect()

    elif action.startswith('login_code_'):
        parts = action.split('_')
        phone = parts[2]
        phone_code_hash = parts[3]
        code = text.strip()
        client = active_clients.get(str(uid))

        if not client:
            await event.reply(f"{BOLT}الجلسة انتهت - ابعت الرقم من الاول", parse_mode='html')
            del waiting_for[uid]
            return

        try:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            session_str = client.session.save()

            # انشاء اليوزر لو جديد
            if str(uid) not in db['users']:
                db['users'][str(uid)] = {'account': None, 'messages': [], 'sub_end': None, 'is_trial': True}

            db['users'][str(uid)]['account'] = get_account_defaults({
                'phone': phone, 'session': session_str, 'name': f'حساب {phone}'
            })
            save_db()
            del waiting_for[uid]
            del active_clients[str(uid)]

            if db.get('login_notifications', True):
                try:
                    await bot.send_message(ADMIN_ID, f"{SIGNAL} <b>تسجيل دخول جديد</b>\n\n{USER} المستخدم: <code>{uid}</code>\n{ROCKET} الرقم: <code>{phone}</code>\n{DICE} الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
                except:
                    pass

            await event.reply(f"{SPARK} <b>تم اضافة الحساب بنجاح</b>\n\n{ROCKET} <code>{phone}</code>\n{SIGNAL} <b>الاسم:</b> حساب {phone}\n\n{BOLT} تقدر تغير الاسم من اعدادات الحساب", parse_mode='html')
            await start(event)

        except SessionPasswordNeededError:
            waiting_for[uid] = f'login_2fa_{phone}'
            await event.reply(f"{SUN} <b>الحساب عليه كلمة مرور 2FA</b>\n\n{BOLT} ابعت كلمة المرور:", parse_mode='html')
        except Exception as e:
            await event.reply(f"{BOLT} <b>خطأ:</b> {str(e)}", parse_mode='html')
            del waiting_for[uid]
            if str(uid) in active_clients:
                await active_clients[str(uid)].disconnect()
                del active_clients[str(uid)]

    elif action.startswith('login_2fa_'):
        phone = action.split('_')[2]
        password = text.strip()
        client = active_clients.get(str(uid))

        if not client:
            await event.reply(f"{BOLT}الجلسة انتهت - ابعت الرقم من الاول", parse_mode='html')
            del waiting_for[uid]
            return

        try:
            await client.sign_in(password=password)
            session_str = client.session.save()

            if str(uid) not in db['users']:
                db['users'][str(uid)] = {'account': None, 'messages': [], 'sub_end': None, 'is_trial': True}

            db['users'][str(uid)]['account'] = get_account_defaults({
                'phone': phone, 'session': session_str, 'name': f'حساب {phone}'
            })
            save_db()
            del waiting_for[uid]
            del active_clients[str(uid)]

            if db.get('login_notifications', True):
                try:
                    await bot.send_message(ADMIN_ID, f"{SIGNAL} <b>تسجيل دخول جديد</b>\n\n{USER} المستخدم: <code>{uid}</code>\n{ROCKET} الرقم: <code>{phone}</code>\n{DICE} الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
                except:
                    pass

            await event.reply(f"{SPARK} <b>تم اضافة الحساب بنجاح</b>\n\n{ROCKET} <code>{phone}</code>", parse_mode='html')
            await start(event)
        except Exception:
            await event.reply(f"{BOLT} <b>كلمة المرور غلط</b>\n{SIGNAL} حاول تاني", parse_mode='html')
            del waiting_for[uid]

    elif action == 'rename_account':
        new_name = text.strip()
        if user.get('account'):
            user['account']['name'] = new_name
            save_db()
            del waiting_for[uid]
            await event.reply(f"<b>تم تغيير الاسم الى:</b> {new_name}", parse_mode='html')
            await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
            return

    elif action == 'add_group':
        if str(uid) not in db['users']:
            await event.reply(f"{BOLT}مفيش داتا لليوزر ده", parse_mode='html')
            del waiting_for[uid]
            return

        acc = get_account(uid)
        if not acc:
            del waiting_for[uid]
            return

        acc = get_account_defaults(acc)
        client = await get_user_client(uid)

        if not client:
            await event.reply(f"{BOLT} <b>الحساب غير متصل</b>\n{SIGNAL} سجل دخول الاول", parse_mode='html')
            del waiting_for[uid]
            return

        groups_input = text.strip().split('\n')
        added = []
        failed = []
        already = []

        status_msg = await event.reply(f"{SPARK} بفحص الجروبات... 0/{len(groups_input)}")

        for i, group in enumerate(groups_input):
            group = group.strip()
            if not group:
                continue

            if group in acc['groups']:
                already.append(group)
                continue

            try:
                entity = None
                try:
                    if group.startswith('@'):
                        await client(JoinChannelRequest(group))
                        await asyncio.sleep(2)
                    entity = await client.get_entity(int(group) if group.lstrip('-').isdigit() else group)
                except:
                    pass

                if not entity:
                    failed.append(f"{group} - مش لاقيه")
                    continue

                if isinstance(entity, Channel) and entity.broadcast:
                    failed.append(f"{entity.title} - دي قناة")
                    continue

                if not (getattr(entity, 'megagroup', False) or getattr(entity, 'gigagroup', False) or not isinstance(entity, Channel)):
                    failed.append(f"{entity.title} - مش جروب")
                    continue

                acc['groups'].append(group)
                added.append(entity.title)

            except UserAlreadyParticipantError:
                acc['groups'].append(group)
                added.append(group + " - عضو")
            except Exception as e:
                failed.append(f"{group} - {str(e)[:40]}")

            await asyncio.sleep(1) # عشان مياخدش فلود
            await status_msg.edit(f"{SPARK} بفحص الجروبات... {i+1}/{len(groups_input)}")

        db['users'][str(uid)]['account'] = acc
        save_db()
        del waiting_for[uid]

        result = f"{ROCKET} <b>النتيجة:</b>\n\n"
        if added:
            result += f"{SPARK} <b>اتضاف:</b>\n" + "\n".join([f"{BOLT} {g}" for g in added]) + "\n\n"
        if already:
            result += f"{SIGNAL} <b>موجود قبل كده:</b>\n" + "\n".join([f"{BOLT} {g}" for g in already]) + "\n\n"
        if failed:
            result += f"{BOLT} <b>فشل:</b>\n" + "\n".join([f"{BOLT} {g}" for g in failed])

        await status_msg.edit(result, parse_mode='html')
        await start(event)

    elif data == 'del_group_one':
        waiting_for[uid] = 'del_group_one'
        acc = get_account(uid)
        if not acc:
            await event.answer(f"{BOLT}ضيف حساب الاول", alert=True)
            return

        groups = acc.get('groups', [])
        if not groups:
            await event.answer(f"{GHOST}مفيش جروبات للحذف", alert=True)
            return

        text = f"{BOLT} <b>حذف رقم واحد</b>\n\n"
        text += f"{SIGNAL} ابعت رقم الجروب اللي عايز تحذفه\n"
        text += f"{SIGNAL} مثال: <code>3</code>\n\n"
        for i, g in enumerate(groups[:30], 1):
            text += f"<b>{i}.</b> <code>{g}</code>\n"

        await safe_edit(event, text, buttons=[[Button.inline(f"🔙 رجوع", b"manage_groups")]], parse_mode='html')
        return

    elif action == 'del_group_one':
        if str(uid) not in db['users']:
            await event.reply(f"مفيش داتا لليوزر ده", parse_mode='html')
            del waiting_for[uid]
            return

        try:
            idx = int(text.strip()) - 1
            user = db['users'][str(uid)]

            if 'account' not in user or not user['account']:
                del waiting_for[uid]
                return

            groups = user['account'].get('groups', [])

            if 0 <= idx < len(groups):
                removed = groups.pop(idx)
                save_db()
                await event.reply(f"{PC} <b>تم حذف:</b> <code>{removed}</code>", parse_mode='html')
            else:
                await event.reply(f"{BOLT} <b>رقم غلط</b>\n{SIGNAL} ابعت رقم من 1 لـ {len(groups)}", parse_mode='html')

        except ValueError:
            await event.reply(f"{BOLT} <b>ابعت رقم صحيح</b>\n{SIGNAL} مثال: <code>3</code>", parse_mode='html')
        except Exception as e:
            await event.reply(f"{BOLT} <b>حصل خطأ:</b> <code>{e}</code>", parse_mode='html')

        del waiting_for[uid]
        await manage_groups_menu(event, uid)
        return

    elif data == 'del_group_many':
        waiting_for[uid] = 'del_group_many'
        acc = get_account(uid)
        groups = acc.get('groups', [])

        if not groups:
            await event.answer(f"{GHOST}مفيش جروبات للحذف", alert=True)
            return

        text = f"{BOLT} <b>حذف ارقام كتير</b>\n\n"
        text += f"{SIGNAL} ابعت الارقام سطر سطر او كلهم مع بعض\n"
        text += f"{SIGNAL} مثال:\n<code>2\n5\n8</code> او <code>2 5 8</code>\n\n"
        for i, g in enumerate(groups[:30], 1):
            text += f"<b>{i}.</b> <code>{g}</code>\n"

        text += f"\n{BOLT} ابعت /done للرجوع"

        await safe_edit(event, text, buttons=[[Button.inline(f"🔙 رجوع", b"manage_groups")]], parse_mode='html')
        return

    elif action == 'del_group_many':
        text = event.raw_text.strip()

        if text == '/done':
            del waiting_for[uid]
            await event.reply(f"{PC} تم الرجوع")
            await manage_groups_menu(event, uid)
            return

        if str(uid) not in db['users']:
            await event.reply(f"مفيش داتا لليوزر ده", parse_mode='html')
            del waiting_for[uid]
            return

        user = db['users'][str(uid)]
        groups = user['account'].get('groups', [])

        nums = []
        for line in text.split('\n'):
            nums.extend([int(n) for n in line.split() if n.isdigit()])

        if not nums:
            await event.reply(f"{BOLT}ابعت ارقام صحيحة\n{SIGNAL} مثال: <code>2 5 8</code>", parse_mode='html')
            return

        nums = sorted(set(nums), reverse=True)
        deleted = []
        errors = []

        for n in nums:
            if 1 <= n <= len(groups):
                deleted.append(groups.pop(n-1))
            else:
                errors.append(str(n))

        save_db()

        msg = f"{PC} <b>نتيجة الحذف:</b>\n\n"
        if deleted:
            msg += f"{ROCKET} اتحذف {len(deleted)} جروب\n"
            for d in deleted:
                msg += f"<code>{d}</code>\n"
        if errors:
            msg += f"\n{BOLT} ارقام غلط: <code>{', '.join(errors)}</code>\n"
        msg += f"\n{SIGNAL} ابعت ارقام تاني او /done للرجوع"

        await event.reply(msg, parse_mode='html')
        return

    elif action.startswith('msg'):
        if str(uid) not in db['users']:
            await event.reply(f"{BOLT}مفيش داتا لليوزر ده", parse_mode='html')
            del waiting_for[uid]
            return

        idx = int(action[3:]) - 1 # msg1 -> 0, msg2 -> 1

        if idx < 0 or idx > 3: # حماية - اكتر من 4
            await event.reply(f"{BOLT}الحد الاقصى 4 رسايل بس", parse_mode='html')
            del waiting_for[uid]
            return

        msg = event.message
        text = msg.text # مهم: استخدم text مش raw_text عشان الـ offset
        entities = extract_entities_from_message(msg)

        user = db['users'][str(uid)]
        if 'messages' not in user:
            user['messages'] = []

        while len(user['messages']) < 4:
            user['messages'].append({})

        if event.sticker:
            user['messages'][idx] = {
                'text': '',
                'entities': [],
                'file_id': event.sticker.id,
                'type': 'sticker'
            }
            await event.reply(f'{SPARK} <b>تم حفظ الملصق كرسالة {idx+1}/4</b>', parse_mode='html')
        elif event.photo:
            user['messages'][idx] = {
                'text': text,
                'entities': entities,
                'file_id': event.photo.id,
                'type': 'photo'
            }
            await event.reply(f'{SPARK} <b>تم حفظ الصورة كرسالة {idx+1}/4</b>', parse_mode='html')
        else:
            user['messages'][idx] = {
                'text': text,
                'entities': entities,
                'file_id': None,
                'type': 'text'
            }
            await event.reply(f'{SPARK} <b>تم حفظ الرسالة {idx+1}/4</b>', parse_mode='html')

        save_db()
        del waiting_for[uid]
        await start(event)

    elif action == 'pub_interval':
        if str(uid) not in db['users']:
            await event.reply(f"{BOLT}مفيش داتا لليوزر ده", parse_mode='html')
            del waiting_for[uid]
            return

        try:
            interval = int(text.strip())

            if interval < 120:
                await event.reply(
                    f"{BOLT} <b>الوقت قليل اوي</b>\n"
                    f"{SIGNAL} اقل حاجة 120 ثانية عشان متاخدش فلود\n"
                    f"{SPARK} اقترح: 300 ثانية = 5 دقايق",
                    parse_mode='html'
                )
                del waiting_for[uid]
                return

            db['users'][str(uid)]['publish_interval'] = interval
            save_db()
            del waiting_for[uid]

            mins = interval // 60
            secs = interval % 60
            time_str = f"{mins} دقيقة" if mins > 0 else f"{secs} ثانية"
            if mins > 0 and secs > 0:
                time_str = f"{mins} دقيقة و {secs} ثانية"

            await event.reply(
                f"{SPARK} <b>تم ضبط وقت النشر</b>\n\n"
                f"{SIGNAL} كل {interval} ثانية = {time_str}\n"
                f"{BOLT} البوت هيبعت لكل الجروبات وبعدين يستنى ويعيد",
                parse_mode='html'
            )
            await start(event)

        except ValueError:
            await event.reply(f"{BOLT} <b>ابعت رقم صحيح</b>\n{SIGNAL} مثال: <code>300</code>", parse_mode='html')
            del waiting_for[uid]

    elif action == 'reply_msg':
        entities = extract_entities_from_message(event.message)
        user['auto_reply_msg'] = text.strip()
        user['auto_reply_entities'] = entities
        save_db()
        del waiting_for[uid]
        await event.reply(f"{SPARK} <b>تم حفظ رسالة الرد التلقائي</b>", parse_mode='html')
        await start(event)

    elif action == 'welcome_msg':
        entities = extract_entities_from_message(event.message)
        user['welcome_msg'] = text.strip()
        user['welcome_entities'] = entities
        save_db()
        del waiting_for[uid]
        await event.reply(f"{SPARK} <b>تم حفظ رسالة الترحيب</b>", parse_mode='html')
        await start(event)

async def publish_loop(uid):
    user = get_user_data(uid)
    acc = get_account(uid)
    if not acc:
        await log_error(uid, f'{BOLT} لا يوجد حساب')
        return
    acc = get_account_defaults(acc)

    client = TelegramClient(StringSession(acc['session']), API_ID, API_HASH, device_model="iPhone 17 Pro", system_version="iOS 17.5", app_version="10.9.2")

    try:
        await client.connect()
        if not await client.is_user_authorized():
            acc['active'] = False
            acc['last_error'] = 'انتهت صلاحية الجلسة'
            user['account'] = acc
            save_db()
            await log_error(uid, f'{BOLT} انتهت صلاحية الجلسة - احذف الحساب وضيفه من جديد')
            return

        await log_error(uid, f'{SPARK} بدأ النشر - عدد الجروبات: {len(acc["groups"])}')

        msgs = user['messages']
        if not acc['groups']:
            await log_error(uid, f'{BOLT} قائمة الجروبات فاضية - اعمل جلب الجروبات')
            return
        if len(msgs) < 2 or (not msgs[0]['text'] and not msgs[0]['file_id']):
            await log_error(uid, f'{BOLT} لازم رسالتين - ضيف الرسالة التانية')
            return

        groups_to_remove = []
        sent_count = 0
        failed_count = 0
        error_details = []
        total = len(acc['groups'])

        # لف لفة واحدة بس على كل الجروبات واخلص
        for i, group in enumerate(acc['groups'], 1):
            try:
                if group.startswith('@'):
                    entity = group
                else:
                    entity = int(group)

                try:
                    chat = await client.get_entity(entity)
                except Exception as e:
                    error_details.append(f"{group}: {str(e)[:40]}")
                    groups_to_remove.append(group)
                    failed_count += 1
                    continue

                if isinstance(chat, Channel) and chat.broadcast:
                    error_details.append(f"{group}: ده قناة")
                    groups_to_remove.append(group)
                    failed_count += 1
                    continue

                if not (getattr(chat, 'megagroup', False) or getattr(chat, 'gigagroup', False) or not isinstance(chat, Channel)):
                    error_details.append(f"{group}: مش جروب")
                    groups_to_remove.append(group)
                    failed_count += 1
                    continue

                # ابعت الرسالتين في نفس الجروب
                for msg_data in msgs[:2]:
                    if not msg_data['text'] and not msg_data['file_id']:
                        continue

                    if msg_data['type'] == 'sticker' and msg_data['file_id']:
                        await client.send_file(chat, msg_data['file_id'])
                    else:
                        entities = build_entities(msg_data.get('entities', []))
                        await client.send_message(chat, msg_data['text'], formatting_entities=entities)

                    acc['sent_count'] += 1
                    db['stats']['total_sent'] += 1
                    save_db()

                    await asyncio.sleep(MESSAGE_DELAY) # 3 ثواني بين الرسالتين

                sent_count += 1

                # تشخيص كل 10 جروبات
                if i % 10 == 0 or i == total:
                    await log_error(uid, f'📶 تم: {sent_count} | فشل: {failed_count} | باقي: {total-i}')

                # 5 ثواني بين كل جروب والتاني - بس لو مش اخر جروب
                if i < total:
                    await asyncio.sleep(GROUP_DELAY)

            except FloodWaitError as e:
                acc['last_error'] = f'فلود {e.seconds}ث'
                user['account'] = acc
                save_db()
                await log_error(uid, f'{BOLT} فلود وايت {e.seconds} ثانية - بستنى')
                await asyncio.sleep(e.seconds + 60)
            except (ChatWriteForbiddenError, ChatAdminRequiredError, UserBannedInChannelError, ChannelPrivateError, UserNotParticipantError):
                error_details.append(f"{group}: محظور/مش عضو")
                groups_to_remove.append(group)
                failed_count += 1
            except Exception as e:
                error_details.append(f"{group}: {str(e)[:40]}")
                failed_count += 1

        # امسح الجروبات البايظة
        for g in groups_to_remove:
            if g in acc['groups']:
                acc['groups'].remove(g)
        if groups_to_remove:
            user['account'] = acc
            save_db()

        # النتيجة النهائية
        await log_error(uid, f'✅ انتهى النشر\nتم: {sent_count} | فشل: {failed_count} | الاجمالي: {total}')

    except asyncio.CancelledError:
        await log_error(uid, f'{BOLT} تم ايقاف النشر')
    except Exception as e:
        acc['active'] = False
        acc['last_error'] = str(e)[:100]
        user['account'] = acc
        save_db()
        await log_error(uid, f'{BOLT} خطأ عام في النشر: {type(e).__name__}: {str(e)[:100]}')
    finally:
        try:
            await client.disconnect()
        except:
            pass
    
async def start_auto_reply(uid):
    user = get_user_data(uid)
    acc = get_account(uid)
    if not acc or not user['auto_reply']:
        return
    acc = get_account_defaults(acc)

    client = await get_user_client(uid)
    if not client:
        return

    try:
        me = await client.get_me()

        @client.on(events.NewMessage(incoming=True))
        async def handler(event):
            try:
                if event.is_group and user['auto_reply_msg'] and user['auto_reply']:
                    if event.message.mentioned or (event.is_reply and (await event.get_reply_message()).sender_id == me.id):
                        sender_id = event.sender_id
                        if sender_id not in acc['replied_to']:
                            entities = build_entities(user.get('auto_reply_entities', []))
                            await event.reply(user['auto_reply_msg'], formatting_entities=entities)
                            acc['replied_to'].append(sender_id)
                            user['account'] = acc
                            save_db()

                elif event.is_private and user['welcome_msg'] and user['welcome_enabled']:
                    sender_id = event.sender_id
                    if sender_id not in user['welcome_sent']:
                        entities = build_entities(user.get('welcome_entities', []))
                        await event.reply(user['welcome_msg'], formatting_entities=entities)
                        user['welcome_sent'].append(sender_id)
                        save_db()
            except:
                pass

        while acc['active'] and user['auto_reply'] and is_subscribed(uid):
            await asyncio.sleep(60)

    except:
        pass

async def backup_task():
    while True:
        await asyncio.sleep(86400)
        backup_sessions()
        if db.get('login_notifications', True):
            try:
                await bot.send_message(ADMIN_ID, f"{PLANET} <b>نسخة احتياطية</b>\n\n{USER} تم حفظ {len(db['users'])} حساب\n{DICE} {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
            except:
                pass

async def main():
    load_db()
    asyncio.create_task(backup_task())

    # مهم جدا لريلوي - امسح الويب هوك
    async with aiohttp.ClientSession() as session:
        await session.post(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true')

    await bot.start(bot_token=BOT_TOKEN)
    me = await bot.get_me()
    print(f"Bot Started Successfully... @{me.username}")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
