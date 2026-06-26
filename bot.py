from telethon import TelegramClient, events, Button, types, functions
from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityBold, MessageEntityItalic, MessageEntityCode, MessageEntityPre, MessageEntityTextUrl, MessageEntityUrl, Channel, LabeledPrice
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError, UserDeactivatedBanError, UserAlreadyParticipantError, DocumentInvalidError
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
MAX_ACCOUNTS_PER_USER = 5

# الايموجي
COIN = '<b><tg-emoji emoji-id="5888778978931516532">🪙</tg-emoji></b>'
BRIEFCASE = '<b><tg-emoji emoji-id="5888519365338341318">💼</tg-emoji></b>'
SWAP = '<b><tg-emoji emoji-id="5888728865253106531">↕️</tg-emoji></b>'
WAVE = '<b><tg-emoji emoji-id="5888462401187093796">👋</tg-emoji></b>'
CAT_FACE = '<b><tg-emoji emoji-id="5888786503714217834">😺</tg-emoji></b>'
PARTY = '<b><tg-emoji emoji-id="5886658755440943371">🥳</tg-emoji></b>'
COIN2 = '<b><tg-emoji emoji-id="5888833838548787248">🪙</tg-emoji></b>'
BED = '<b><tg-emoji emoji-id="5888647432673173244">🛏️</tg-emoji></b>'
PARACHUTE = '<b><tg-emoji emoji-id="5888847655458578303">🪂</tg-emoji></b>'
MASK = '<b><tg-emoji emoji-id="5888495828917559128">🎭</tg-emoji></b>'
DISCO = '<b><tg-emoji emoji-id="5889018182840100211">🪩</tg-emoji></b>'
SHOPPING = '<b><tg-emoji emoji-id="5888535956797006002">🛒</tg-emoji></b>'
MEDAL = '<b><tg-emoji emoji-id="5888688827567973439">🏅</tg-emoji></b>'
ID_CARD = '<b><tg-emoji emoji-id="5888971608214740766">🪪</tg-emoji></b>'
BRIEFCASE2 = '<b><tg-emoji emoji-id="5888875817559138298">💼</tg-emoji></b>'
MEDAL2 = '<b><tg-emoji emoji-id="5888496159630040589">🏅</tg-emoji></b>'
MEDAL3 = '<b><tg-emoji emoji-id="5888767623037984662">🏅</tg-emoji></b>'
FIST = '<b><tg-emoji emoji-id="5888528603812995132">👊</tg-emoji></b>'
USER = '<b><tg-emoji emoji-id="5886695331382435915">👤</tg-emoji></b>'
PC = '<b><tg-emoji emoji-id="5886664420502805908">💻</tg-emoji></b>'
LOCK = '<b><tg-emoji emoji-id="5886403208292071168">🔒</tg-emoji></b>'
UNLOCK = '<b><tg-emoji emoji-id="5886403208292071170">🔓</tg-emoji></b>'
FOLDER = '<b><tg-emoji emoji-id="5886403208292071172">📁</tg-emoji></b>'
SETTINGS = '<b><tg-emoji emoji-id="5886403208292071174">⚙️</tg-emoji></b>'
STORAGE = '<b><tg-emoji emoji-id="5886403208292071176">🗃️</tg-emoji></b>'
PLUS = '<b><tg-emoji emoji-id="5886403208292071178">➕</tg-emoji></b>'
WRITING = '<b><tg-emoji emoji-id="5886403208292071180">✍️</tg-emoji></b>'

bot = TelegramClient('bot', API_ID, API_HASH)
db = {'users': {}, 'codes': {}, 'stats': {'total_sent': 0, 'active_vip': 0}, 'login_notifications': True, 'pending_crypto': {}}
waiting_for = {}
active_clients = {}
running_tasks = {}
user_clients = {}
typing_status = {}

STEALTH_MODES = {
    'fast': {'group_delay': [1, 3], 'name': 'سريع'},
    'balanced': {'group_delay': [3, 7], 'name': 'متوازن'},
    'safe': {'group_delay': [7, 15], 'name': 'آمن جدا'}
}

FLOOD_PROTECTION_LEVELS = {
    0: {'name': 'بدون حماية', 'delay': 0, 'max_retries': 3},
    1: {'name': 'حماية أساسية', 'delay': 5, 'max_retries': 5},
    2: {'name': 'حماية متقدمة', 'delay': 15, 'max_retries': 10},
    3: {'name': 'حماية قصوى', 'delay': 30, 'max_retries': 20}
}

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

def backup_sessions():
    backup = {}
    for uid, user in db['users'].items():
        if user.get('accounts'):
            for acc_id, acc in user['accounts'].items():
                if acc.get('session'):
                    backup[f"{uid}_{acc_id}"] = {
                        'phone': acc['phone'],
                        'session': acc['session'],
                        'name': acc['name'],
                        'user_id': uid,
                        'account_id': acc_id,
                        'backed_up_at': datetime.now().isoformat()
                    }
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)

def get_user_data(uid):
    uid = str(uid)
    if uid not in db['users']:
        db['users'][uid] = {
            'sub_end': None,
            'accounts': {},
            'messages': [
                {'text': '', 'entities': [], 'file_id': None, 'type': 'text'},
                {'text': '', 'entities': [], 'file_id': None, 'type': 'text'}
            ],
            'publish_interval': '5-10',
            'flood_protection': 2,
            'stealth_mode': 'balanced',
            'auto_reply': True,
            'auto_reply_msg': '',
            'auto_reply_entities': [],
            'welcome_msg': '',
            'welcome_entities': [],
            'welcome_enabled': True,
            'welcome_sent': [],
            'storage_enabled': False,
            'storage_group': None,
            'smart_reply_enabled': False,
            'smart_replies': {},
            'vip': False,
            'vip_code': None
        }
        save_db()
    user = db['users'][uid]

    # Ensure all required fields exist
    if 'welcome_enabled' not in user:
        user['welcome_enabled'] = True
    if 'welcome_sent' not in user:
        user['welcome_sent'] = []
    if 'storage_enabled' not in user:
        user['storage_enabled'] = False
    if 'storage_group' not in user:
        user['storage_group'] = None
    if 'smart_reply_enabled' not in user:
        user['smart_reply_enabled'] = False
    if 'smart_replies' not in user:
        user['smart_replies'] = {}
    if 'vip' not in user:
        user['vip'] = False
    if 'vip_code' not in user:
        user['vip_code'] = None

    if len(user['messages']) > 2:
        user['messages'] = user['messages'][:2]
    elif len(user['messages']) < 2:
        while len(user['messages']) < 2:
            user['messages'].append({'text': '', 'entities': [], 'file_id': None, 'type': 'text'})

    if isinstance(user['messages'][0], str):
        old_msgs = user['messages']
        user['messages'] = [
            {'text': old_msgs[0] if len(old_msgs) > 0 else '', 'entities': [], 'file_id': None, 'type': 'text'},
            {'text': old_msgs[1] if len(old_msgs) > 1 else '', 'entities': [], 'file_id': None, 'type': 'text'}
        ]

    return user

def is_subscribed(uid):
    if uid == ADMIN_ID:
        return True
    user = get_user_data(uid)
    if user.get('vip', False):
        return True
    sub_end = user.get('sub_end')
    if not sub_end:
        return False
    try:
        return datetime.fromisoformat(sub_end) > datetime.now()
    except:
        return False

def get_remaining_days(uid):
    user = get_user_data(uid)
    if user.get('vip', False):
        return "VIP نشط"
    sub_end = user.get('sub_end')
    if not sub_end:
        return 0
    try:
        delta = datetime.fromisoformat(sub_end) - datetime.now()
        return max(0, delta.days)
    except:
        return 0

def parse_interval(interval_str):
    """يحول 5-10 لرقم عشوائي او 5 لرقم ثابت"""
    interval_str = str(interval_str).strip()
    if '-' in interval_str:
        try:
            parts = interval_str.split('-')
            min_val = int(parts[0])
            max_val = int(parts[1])
            return random.randint(min_val, max_val)
        except:
            return 5
    else:
        try:
            return int(interval_str)
        except:
            return 5

async def check_force_sub(uid):
    if uid == ADMIN_ID:
        return True, []

    not_joined = []

    if FORCE_SUB_CHANNEL:
        try:
            await bot.get_permissions(FORCE_SUB_CHANNEL, uid)
        except UserNotParticipantError:
            not_joined.append(('قناة', FORCE_SUB_CHANNEL))
        except:
            pass

    if FORCE_SUB_GROUP:
        try:
            await bot.get_permissions(FORCE_SUB_GROUP, uid)
        except UserNotParticipantError:
            not_joined.append(('جروب', FORCE_SUB_GROUP))
        except:
            pass

    return len(not_joined) == 0, not_joined

async def show_force_sub_menu(event, not_joined):
    text = f"{COIN} اشترك في القنوات التالية لاستخدام البوت:\n\n"
    btns = []
    for typ, link in not_joined:
        text += f"{MEDAL} {typ}: {link}\n"
        btns.append([Button.url(f"اشترك في {typ}", f"https://t.me/{link.replace('@', '')}")])
    btns.append([Button.inline("تحققت من الاشتراك", b"check_sub")])
    await event.respond(text, buttons=btns, parse_mode='html')

async def show_required_channels_menu(event):
    btns = [
        [Button.url("اشترك هنا اولا", f"https://t.me/{REQUIRED_CHANNELS[0]}")],
        [Button.inline("تحققت", b"check_sub")]
    ]
    await event.respond(f"{DISCO} اشترك في القناة اولا", buttons=btns, parse_mode='html')

def get_account(uid, account_id=None):
    user = get_user_data(uid)
    if not account_id:
        if not user['accounts']:
            return None
        account_id = next(iter(user['accounts']))
    return get_account_defaults(user['accounts'].get(account_id)) if account_id in user['accounts'] else None

def get_account_defaults(acc):
    if not acc:
        return None
    defaults = {
        'active': False,
        'groups': [],
        'name': 'حساب جديد',
        'phone': '',
        'session': '',
        'sent_count': 0,
        'last_error': None,
        'created_at': datetime.now().isoformat(),
        'replied_to': [],
        'flood_count': 0,
        'last_flood_time': None,
        'storage_enabled': False,
        'storage_group': None
    }
    for k, v in defaults.items():
        if k not in acc:
            acc[k] = v
    return acc

def extract_entities_from_message(message):
    entities = []
    if message.entities:
        for ent in message.entities:
            if isinstance(ent, MessageEntityCustomEmoji):
                entities.append({
                    'type': 'custom_emoji',
                    'offset': ent.offset,
                    'length': ent.length,
                    'document_id': ent.document_id
                })
            elif isinstance(ent, MessageEntityBold):
                entities.append({'type': 'bold', 'offset': ent.offset, 'length': ent.length})
            elif isinstance(ent, MessageEntityItalic):
                entities.append({'type': 'italic', 'offset': ent.offset, 'length': ent.length})
            elif isinstance(ent, MessageEntityCode):
                entities.append({'type': 'code', 'offset': ent.offset, 'length': ent.length})
            elif isinstance(ent, MessageEntityPre):
                entities.append({'type': 'pre', 'offset': ent.offset, 'length': ent.length, 'language': ent.language})
            elif isinstance(ent, MessageEntityTextUrl):
                entities.append({'type': 'text_url', 'offset': ent.offset, 'length': ent.length, 'url': ent.url})
            elif isinstance(ent, MessageEntityUrl):
                entities.append({'type': 'url', 'offset': ent.offset, 'length': ent.length})
    return entities

def build_entities(saved_entities):
    entities = []
    for ent in saved_entities:
        if ent['type'] == 'custom_emoji':
            entities.append(MessageEntityCustomEmoji(
                offset=ent['offset'],
                length=ent['length'],
                document_id=ent['document_id']
            ))
        elif ent['type'] == 'bold':
            entities.append(MessageEntityBold(offset=ent['offset'], length=ent['length']))
        elif ent['type'] == 'italic':
            entities.append(MessageEntityItalic(offset=ent['offset'], length=ent['length']))
        elif ent['type'] == 'code':
            entities.append(MessageEntityCode(offset=ent['offset'], length=ent['length']))
        elif ent['type'] == 'pre':
            entities.append(MessageEntityPre(offset=ent['offset'], length=ent['length'], language=ent.get('language', '')))
        elif ent['type'] == 'text_url':
            entities.append(MessageEntityTextUrl(offset=ent['offset'], length=ent['length'], url=ent['url']))
        elif ent['type'] == 'url':
            entities.append(MessageEntityUrl(offset=ent['offset'], length=ent['length']))
    return entities

def welcome_menu(uid):
    user = get_user_data(uid)
    if user.get('vip', False):
        return main_menu(uid)
    else:
        text = f"{DISCO} مرحبا بك في بوت النشر التلقائي {DISCO}\n\n"
        text += f"{USER} البوت يسمح لك بنشر رسائل تلقائية في الجروبات\n"
        text += f"{COIN} مميزات البوت:\n"
        text += f"{MEDAL} نشر رسالتين عشوائي في كل دورة\n"
        text += f"{BRIEFCASE} إدارة حسابات متعددة\n"
        text += f"{SETTINGS} إعدادات متقدمة للنشر\n"
        text += f"{STORAGE} تخزين الرسائل والردود الذكية\n"
        text += f"{PARTY} مميزات VIP:\n"
        text += f"{MEDAL2} عدد حسابات غير محدود\n"
        text += f"{COIN2} دعم فني مباشر\n"
        text += f"{DISCO} أولوية في التحديثات\n\n"
        text += f"{LOCK} البوت مدفوع بكود تفعيل من المطور\n"
        text += f"{USER} للاشتراك في VIP أرسل كود التفعيل\n"

        btns = [
            [Button.inline("تفعيل كود VIP", b"activate_vip")],
            [Button.url(f"المطور {DEVELOPER_USERNAME}", DEVELOPER_LINK)]
        ]
        return text, btns

def main_menu(uid):
    user = get_user_data(uid)
    accounts_count = len(user['accounts'])

    text = f"{DISCO} لوحة التحكم الرئيسية {DISCO}\n\n"
    text += f"{USER} الاشتراك: {get_remaining_days(uid)}\n"
    text += f"{COIN} الحسابات: {accounts_count}/{MAX_ACCOUNTS_PER_USER if not user.get('vip', False) else '∞'}\n\n"
    text += f"{MEDAL} اختر حساب للنشر:"

    btns = []
    for acc_id, acc in user['accounts'].items():
        status = "يعمل" if acc['active'] else "متوقف"
        btns.append([Button.inline(f"{acc['name']} ({status})", f"account_menu_{acc_id}")])

    if accounts_count < MAX_ACCOUNTS_PER_USER or user.get('vip', False):
        btns.append([Button.inline(f"{PLUS} إضافة حساب جديد", b"add_account")])

    btns.append([Button.inline(f"{SETTINGS} الإعدادات العامة", b"general_settings")])
    btns.append([Button.inline(f"{STORAGE} التخزين والردود الذكية", b"storage_settings")])
    if uid == ADMIN_ID:
        btns.append([Button.inline(f"{USER} لوحة المبرمج", b"admin")])
    btns.append([Button.url(f"المطور {DEVELOPER_USERNAME}", DEVELOPER_LINK)])

    return text, btns

def account_menu(uid, account_id):
    user = get_user_data(uid)
    acc = get_account(uid, account_id)
    if not acc:
        return None, None

    msg1 = user['messages'][0]
    msg2 = user['messages'][1]

    def get_msg_status(msg):
        if msg['type'] == 'sticker': return "ملصق"
        elif msg['text']: return "نص"
        else: return "فارغ"

    text = f"{DISCO} إعدادات الحساب: {acc['name']}\n\n"
    text += f"{USER} الرقم: {acc['phone']}\n"
    text += f"{COIN} الرسائل المرسلة: {acc['sent_count']}\n"
    text += f"{BRIEFCASE} الجروبات: {len(acc['groups'])}\n"
    text += f"{MEDAL} الحالة: {'يعمل' if acc['active'] else 'متوقف'}\n"
    text += f"{SHOPPING} حماية الفلود: مستوى {user['flood_protection']}\n"
    text += f"{PARACHUTE} وضع التخفي: {STEALTH_MODES[user['stealth_mode']]['name']}\n\n"
    text += f"{MEDAL3} الرسائل:\n"
    text += f"1. {get_msg_status(msg1)}\n"
    text += f"2. {get_msg_status(msg2)}\n"

    btns = [
        [Button.inline("رسالة 1", b"msg1"), Button.inline("رسالة 2", b"msg2")],
        [Button.inline(f"وقت النشر ({user['publish_interval']} دقيقة)", b"pub_interval")],
        [Button.inline(f"جلب الجروبات ({len(acc['groups'])})", b"fetch_groups")],
        [Button.inline("إدارة الجروبات", b"manage_groups")],
        [Button.inline(f"{'ايقاف' if acc['active'] else 'تشغيل'} النشر", b"toggle_pub")],
        [Button.inline("تحليل الحساب", b"analyze_account")],
        [Button.inline("تغيير الاسم", b"rename_account"), Button.inline("حذف الحساب", b"delete_account")],
        [Button.inline("رجوع للقائمة الرئيسية", b"back_main")]
    ]

    return text, btns

def general_settings_menu(uid):
    user = get_user_data(uid)
    reply_status = "✅" if user['auto_reply'] else "❌"
    welcome_status = "✅" if user['welcome_enabled'] else "❌"
    flood_level = FLOOD_PROTECTION_LEVELS[user['flood_protection']]['name']
    stealth = STEALTH_MODES[user['stealth_mode']]['name']

    text = f"{SETTINGS} الإعدادات العامة\n\n"
    text += f"{SHOPPING} حماية الفلود: {flood_level}\n"
    text += f"{PARACHUTE} وضع التخفي: {stealth}\n"
    text += f"{USER} الرد التلقائي: {reply_status}\n"
    text += f"{COIN} رسالة الترحيب: {welcome_status}\n"

    btns = [
        [Button.inline("حماية الفلود", b"flood_level")],
        [Button.inline("وضع التخفي", b"stealth_mode")],
        [Button.inline(f"{'تعطيل' if user['auto_reply'] else 'تفعيل'} الرد التلقائي", b"toggle_reply")],
        [Button.inline(f"{'تعطيل' if user['welcome_enabled'] else 'تفعيل'} الترحيب", b"toggle_welcome")],
        [Button.inline("تعيين الرد التلقائي", b"set_reply_msg")],
        [Button.inline("تعيين رسالة الترحيب", b"set_welcome_msg")],
        [Button.inline("رجوع للقائمة الرئيسية", b"back_main")]
    ]

    return text, btns

def storage_settings_menu(uid):
    user = get_user_data(uid)
    storage_status = "✅" if user['storage_enabled'] else "❌"
    smart_reply_status = "✅" if user['smart_reply_enabled'] else "❌"

    text = f"{STORAGE} إعدادات التخزين والردود الذكية\n\n"
    text += f"{FOLDER} تخزين الرسائل: {storage_status}\n"
    text += f"{LOCK} جروب التخزين: {'غير محدد' if not user['storage_group'] else user['storage_group']}\n"
    text += f"{USER} الردود الذكية: {smart_reply_status}\n"

    btns = [
        [Button.inline(f"{'تعطيل' if user['storage_enabled'] else 'تفعيل'} التخزين", b"toggle_storage")],
        [Button.inline("تعيين جروب التخزين", b"set_storage_group")],
        [Button.inline(f"{'تعطيل' if user['smart_reply_enabled'] else 'تفعيل'} الردود الذكية", b"toggle_smart_reply")],
        [Button.inline("إدارة الردود الذكية", b"manage_smart_replies")],
        [Button.inline("رجوع للقائمة الرئيسية", b"back_main")]
    ]

    return text, btns

def admin_menu():
    notif_status = "✅" if db.get('login_notifications', True) else "❌"
    vip_status = "✅" if db.get('vip_enabled', True) else "❌"
    return [
        [Button.inline("إدارة الأكواد", b"manage_codes")],
        [Button.inline("المستخدمين", b"users")],
        [Button.inline("إحصائيات", b"admin_stats")],
        [Button.inline("نسخة احتياطية", b"backup_sessions")],
        [Button.inline("تحميل النسخ", b"download_backup")],
        [Button.inline("إرسال إشعار عام", b"broadcast")],
        [Button.inline(f"{notif_status} إشعارات الدخول", b"toggle_notifications")],
        [Button.inline(f"{vip_status} نظام VIP", b"toggle_vip_system")],
        [Button.inline("رجوع", b"back_main")]
    ]

def manage_codes_menu():
    return [
        [Button.inline("إنشاء كود VIP", b"generate_vip_code")],
        [Button.inline("إلغاء تفعيل كود", b"deactivate_vip_code")],
        [Button.inline("عرض الأكواد النشطة", b"list_active_codes")],
        [Button.inline("رجوع", b"admin")]
    ]

async def get_user_client(uid, account_id, show_typing=False):
    user = get_user_data(uid)
    if account_id not in user['accounts']:
        return None

    acc = user['accounts'][account_id]
    if not acc or 'session' not in acc:
        return None

    key = f"{uid}_{account_id}"

    if key in user_clients:
        try:
            if user_clients[key].is_connected():
                if show_typing:
                    await start_typing_simulation(uid, account_id)
                return user_clients[key]
            else:
                await user_clients[key].disconnect()
                del user_clients[key]
        except:
            try:
                del user_clients[key]
            except:
                pass

    try:
        client = TelegramClient(StringSession(acc['session']), API_ID, API_HASH,
                              device_model="iPhone 17 Pro", system_version="iOS 17.5", app_version="10.9.2")
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return None

        if show_typing:
            await start_typing_simulation(uid, account_id)

        user_clients[key] = client
        return client
    except:
        return None

async def start_typing_simulation(uid, account_id):
    key = f"{uid}_{account_id}"
    if key in typing_status and typing_status[key]:
        return

    typing_status[key] = True
    client = await get_user_client(uid, account_id)
    if not client:
        typing_status[key] = False
        return

    try:
        while typing_status[key]:
            await asyncio.sleep(3)
            if key in typing_status and typing_status[key]:
                await client(functions.messages.SetTypingRequest(
                    peer=await client.get_input_entity('me'),
                    action=types.SendMessageTypingAction()
                ))
    except:
        pass
    finally:
        typing_status[key] = False

async def stop_typing_simulation(uid, account_id):
    key = f"{uid}_{account_id}"
    typing_status[key] = False

async def log_error(uid, error_text, account_id=None):
    try:
        if account_id:
            await bot.send_message(uid, f"{MEDAL2} تشخيص الحساب {account_id}:\n\n{error_text}", parse_mode='html')
        else:
            await bot.send_message(uid, f"{MEDAL2} تشخيص:\n\n{error_text}", parse_mode='html')
    except:
        pass

async def safe_edit(event, text, buttons=None):
    try:
        await event.edit(text, buttons=buttons, parse_mode='html')
    except MessageNotModifiedError:
        pass
    except Exception:
        try:
            await event.respond(text, buttons=buttons, parse_mode='html')
        except:
            pass

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    user = get_user_data(uid)

    is_sub, not_joined = await check_force_sub(uid)
    if not is_sub:
        await show_force_sub_menu(event, not_joined)
        return

    for channel in REQUIRED_CHANNELS:
        try:
            await bot(GetParticipantRequest(channel, uid))
        except:
            await show_required_channels_menu(event)
            return

    if not is_subscribed(uid):
        text, btns = welcome_menu(uid)
    else:
        text, btns = main_menu(uid)
    try:
        await event.respond(text, buttons=btns, parse_mode='html')
    except DocumentInvalidError:
        # Fallback to simple text if document error occurs
        await event.respond(text.replace(DISCO, '').replace(COIN, '').replace(MEDAL, '').replace(USER, ''), buttons=btns)

@bot.on(events.CallbackQuery)
async def callback(event):
    uid = event.sender_id
    try:
        data = event.data.decode()
    except DocumentInvalidError:
        await event.answer("حدث خطأ في معالجة الطلب", alert=True)
        return

    user = get_user_data(uid)

    await event.answer()

    if data == 'back_main':
        if not is_subscribed(uid):
            text, btns = welcome_menu(uid)
        else:
            text, btns = main_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'check_sub':
        is_sub, not_joined = await check_force_sub(uid)
        if not is_sub:
            await show_force_sub_menu(event, not_joined)
            return

        for channel in REQUIRED_CHANNELS:
            try:
                await bot(GetParticipantRequest(channel, uid))
            except:
                await show_required_channels_menu(event)
                return

        if not is_subscribed(uid):
            text, btns = welcome_menu(uid)
        else:
            text, btns = main_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'activate_vip':
        if is_subscribed(uid):
            await event.answer("لديك اشتراك نشط بالفعل", alert=True)
            return

        waiting_for[uid] = 'activate_vip_code'
        await safe_edit(event, f"{COIN} أرسل كود VIP للتفعيل:", buttons=[[Button.inline("رجوع", b"back_main")]])
        return

    elif data.startswith('account_menu_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        text, btns = account_menu(uid, account_id)
        if text and btns:
            await safe_edit(event, text, buttons=btns)
        return

    elif data == 'add_account':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        if len(user['accounts']) >= MAX_ACCOUNTS_PER_USER and not user.get('vip', False):
            await event.answer(f"لا يمكنك إضافة أكثر من {MAX_ACCOUNTS_PER_USER} حسابات", alert=True)
            return

        waiting_for[uid] = 'add_account_session'
        await safe_edit(event, f"{USER} أرسل جلسة الحساب (String Session):\n\n{MEDAL} للحصول على الجلسة:\n1. استخدم بوت @SessionStringBot\n2. أرسل /get\n3. انسخ الجلسة وأرسلها هنا\n\n{COIN} هام: لا ترسل أي بيانات حساسة غير الجلسة", buttons=[[Button.inline("رجوع", b"back_main")]])
        return

    elif data == 'general_settings':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        text, btns = general_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'storage_settings':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        text, btns = storage_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'msg1':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'msg1'
        await safe_edit(event, f"{MEDAL} أرسل الرسالة الأولى:\n\n{COIN} يمكنك إرسال نص أو ملصق\n{DISCO} البوت سيحفظها وينشرها تلقائياً", buttons=[[Button.inline("رجوع", b"back_main")]])
        return

    elif data == 'msg2':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'msg2'
        await safe_edit(event, f"{MEDAL} أرسل الرسالة الثانية:\n\n{COIN} يمكنك إرسال نص أو ملصق\n{DISCO} البوت سيبدل بينها تلقائياً", buttons=[[Button.inline("رجوع", b"back_main")]])
        return

    elif data == 'toggle_reply':
        user['auto_reply'] = not user['auto_reply']
        save_db()
        status = "مفعل" if user['auto_reply'] else "معطل"
        await event.answer(f"الرد التلقائي: {status}", alert=True)
        text, btns = general_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'toggle_welcome':
        user['welcome_enabled'] = not user['welcome_enabled']
        save_db()
        status = "مفعل" if user['welcome_enabled'] else "معطل"
        await event.answer(f"رسالة الترحيب: {status}", alert=True)
        text, btns = general_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'set_reply_msg':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'reply_msg'
        text = f"{MEDAL} أرسل رسالة الرد التلقائي:\n\n"
        text += f"{COIN} هذه الرسالة سترسل عند المنشن أو الرد عليك\n"
        text += f"{DISCO} يمكنك استخدام تنسيقات النص"
        buttons = [
            [Button.inline("إيقاف الرد التلقائي", b"stop_reply")],
            [Button.inline("رجوع", b"general_settings")]
        ]
        await safe_edit(event, text, buttons=buttons)
        return

    elif data == 'set_welcome_msg':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'welcome_msg'
        text = f"{MEDAL} أرسل رسالة الترحيب:\n\n"
        text += f"{COIN} هذه الرسالة سترسل لأي شخص يرسل لك رسالة خاصة لأول مرة\n"
        text += f"{DISCO} يمكنك استخدام تنسيقات النص"
        buttons = [
            [Button.inline("إيقاف رسالة الترحيب", b"stop_welcome")],
            [Button.inline("رجوع", b"general_settings")]
        ]
        await safe_edit(event, text, buttons=buttons)
        return

    elif data == 'stop_reply':
        user['auto_reply_msg'] = ''
        user['auto_reply_entities'] = []
        save_db()
        await event.answer("تم إيقاف الرد التلقائي")
        text = f"{COIN} تم إيقاف الرد التلقائي بنجاح\n\n"
        text += f"{MEDAL} لن يتم الرد على المنشن والريبلاي الآن"
        await safe_edit(event, text, buttons=[[Button.inline("رجوع", b"general_settings")]])
        return

    elif data == 'stop_welcome':
        user['welcome_msg'] = ''
        user['welcome_entities'] = []
        save_db()
        await event.answer("تم إيقاف رسالة الترحيب")
        text = f"{COIN} تم إيقاف رسالة الترحيب بنجاح\n\n"
        text += f"{MEDAL} لن يتم إرسال رسائل ترحيب للخاص الآن"
        await safe_edit(event, text, buttons=[[Button.inline("رجوع", b"general_settings")]])
        return

    elif data == 'fetch_groups':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'select_account_for_fetch'
        accounts_btns = []
        for acc_id, acc in user['accounts'].items():
            accounts_btns.append([Button.inline(f"{acc['name']}", f"fetch_groups_{acc_id}")])
        accounts_btns.append([Button.inline("رجوع", b"back_main")])
        await safe_edit(event, f"{BRIEFCASE} اختر الحساب لجلب الجروبات:", buttons=accounts_btns)
        return

    elif data.startswith('fetch_groups_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        waiting_for[uid] = f'fetch_groups_{account_id}'
        await safe_edit(event, f"{BRIEFCASE} جاري جلب الجروبات...\n\n{MEDAL} قد يستغرق هذا بعض الوقت حسب عدد الجروبات", buttons=[[Button.inline("إلغاء", b"back_main")]])
        return

    elif data == 'manage_groups':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'select_account_for_manage'
        accounts_btns = []
        for acc_id, acc in user['accounts'].items():
            accounts_btns.append([Button.inline(f"{acc['name']} ({len(acc['groups'])})", f"manage_groups_{acc_id}")])
        accounts_btns.append([Button.inline("رجوع", b"back_main")])
        await safe_edit(event, f"{FOLDER} اختر الحساب لإدارة الجروبات:", buttons=accounts_btns)
        return

    elif data.startswith('manage_groups_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        acc = get_account(uid, account_id)
        if not acc:
            await event.answer("الحساب غير موجود", alert=True)
            return

        groups_text = '\n'.join([f"{i+1}. {g}" for i, g in enumerate(acc['groups'][:20])])
        if len(acc['groups']) > 20:
            groups_text += f"\n{MEDAL}... و {len(acc['groups'])-20} آخرين"

        btns = [
            [Button.inline("إضافة جروب", f"add_group_{account_id}")],
            [Button.inline("حذف جروب", f"del_group_{account_id}")],
            [Button.inline("حذف الكل", f"clear_groups_{account_id}")],
            [Button.inline("رجوع", f"account_menu_{account_id}")]
        ]
        await safe_edit(event, f"{FOLDER} الجروبات ({len(acc['groups'])}):\n\n{groups_text or 'لا يوجد جروبات'}", buttons=btns)
        return

    elif data.startswith('add_group_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        waiting_for[uid] = f'add_group_{account_id}'
        await safe_edit(event, f"{USER} أرسل يوزر الجروب أو الرابط أو الايدي:\n\n{MEDAL} مثال: @group_username أو https://t.me/group_username أو -1001234567890\n\n{COIN} يمكنك إرسال أكثر من جروب في رسالة واحدة (سطر لكل جروب)\n\n{BRIEFCASE} الحد الأقصى: 1000 جروب", buttons=[[Button.inline("رجوع", f"manage_groups_{account_id}")]])
        return

    elif data.startswith('del_group_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        waiting_for[uid] = f'del_group_{account_id}'
        await safe_edit(event, f"{COIN} أرسل يوزر الجروب أو الرابط أو الايدي للحذف:\n\n{MEDAL} مثال: @group_username أو https://t.me/group_username أو -1001234567890\n\n{COIN} يمكنك إرسال أكثر من جروب في رسالة واحدة (سطر لكل جروب)", buttons=[[Button.inline("رجوع", f"manage_groups_{account_id}")]])
        return

    elif data.startswith('clear_groups_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        acc = get_account(uid, account_id)
        if acc:
            acc['groups'] = []
            save_db()
            await event.answer("تم حذف جميع الجروبات", alert=True)
            await safe_edit(event, f"{FOLDER} الجروبات (0):\n\nلا يوجد جروبات", buttons=[
                [Button.inline("إضافة جروب", f"add_group_{account_id}")],
                [Button.inline("حذف جروب", f"del_group_{account_id}")],
                [Button.inline("حذف الكل", f"clear_groups_{account_id}")],
                [Button.inline("رجوع", f"account_menu_{account_id}")]
            ])
        return

    elif data == 'pub_interval':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'pub_interval'
        await safe_edit(event, f"{BRIEFCASE} أرسل الوقت بين كل دورة نشر (بالدقائق):\n\n{MEDAL} مثال: 5 أو 5-10\n{COIN} 5 = ثابت كل 5 دقائق\n{COIN} 5-10 = عشوائي بين 5 و 10 دقائق\n\n{SHOPPING} الحد الأدنى: 1 دقيقة", buttons=[[Button.inline("رجوع", b"back_main")]])
        return

    elif data == 'flood_level':
        user['flood_protection'] = (user['flood_protection'] + 1) % 4
        save_db()
        text, btns = general_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'stealth_mode':
        modes = list(STEALTH_MODES.keys())
        current = modes.index(user['stealth_mode'])
        user['stealth_mode'] = modes[(current + 1) % len(modes)]
        save_db()
        text, btns = general_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'toggle_pub':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'select_account_for_toggle'
        accounts_btns = []
        for acc_id, acc in user['accounts'].items():
            status = "يعمل" if acc['active'] else "متوقف"
            accounts_btns.append([Button.inline(f"{acc['name']} ({status})", f"toggle_pub_{acc_id}")])
        accounts_btns.append([Button.inline("رجوع", b"back_main")])
        await safe_edit(event, f"{COIN} اختر الحساب لتشغيل/إيقاف النشر:", buttons=accounts_btns)
        return

    elif data.startswith('toggle_pub_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        acc = get_account(uid, account_id)
        if acc:
            acc['active'] = not acc['active']
            acc['last_error'] = None
            save_db()

            if acc['active']:
                key = f"{uid}_{account_id}"
                if key in running_tasks:
                    try:
                        running_tasks[key].cancel()
                        await asyncio.sleep(0.5)
                    except:
                        pass
                    del running_tasks[key]

                task = asyncio.create_task(publish_loop(uid, account_id))
                running_tasks[key] = task

                if user['auto_reply']:
                    asyncio.create_task(start_auto_reply(uid, account_id))

                await event.answer("تم تشغيل النشر", alert=True)
                await log_error(uid, f'{DISCO} بدأ النشر - عدد الجروبات: {len(acc["groups"])}', account_id)
            else:
                key = f"{uid}_{account_id}"
                if key in running_tasks:
                    try:
                        running_tasks[key].cancel()
                        await asyncio.sleep(0.5)
                    except:
                        pass
                    del running_tasks[key]
                await stop_typing_simulation(uid, account_id)
                await event.answer("تم إيقاف النشر", alert=True)
                await log_error(uid, f'{COIN} تم إيقاف النشر يدوياً', account_id)

            text, btns = account_menu(uid, account_id)
            await safe_edit(event, text, buttons=btns)
        return

    elif data == 'analyze_account':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'select_account_for_analyze'
        accounts_btns = []
        for acc_id, acc in user['accounts'].items():
            accounts_btns.append([Button.inline(f"{acc['name']}", f"analyze_account_{acc_id}")])
        accounts_btns.append([Button.inline("رجوع", b"back_main")])
        await safe_edit(event, f"{ID_CARD} اختر الحساب للتحليل:", buttons=accounts_btns)
        return

    elif data.startswith('analyze_account_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        acc = get_account(uid, account_id)
        if not acc:
            await event.answer("الحساب غير موجود", alert=True)
            return

        status = "غير معروف"
        try:
            client = await get_user_client(uid, account_id)
            if client and client.is_connected():
                me = await client.get_me()
                status = f"سليم - {me.first_name}"
            else:
                status = "غير متصل"
        except:
            status = "محظور أو منتهي"

        flood_protection = FLOOD_PROTECTION_LEVELS[user['flood_protection']]['name']
        stealth_mode = STEALTH_MODES[user['stealth_mode']]['name']

        text = f"{ID_CARD} تحليل وضع النشر\n\n"
        text += f"{USER} الحساب: {acc['name']}\n"
        text += f"{COIN} الرقم: {acc['phone']}\n"
        text += f"{MEDAL} الحالة: {status}\n"
        text += f"{BRIEFCASE} الجروبات: {len(acc['groups'])}\n"
        text += f"{DISCO} الرسائل المرسلة: {acc['sent_count']}\n"
        text += f"{BRIEFCASE2} النشر كل: {user['publish_interval']} دقيقة\n"
        text += f"{PARACHUTE} وضع التخفي: {stealth_mode}\n"
        text += f"{SHOPPING} حماية الفلود: {flood_protection}\n"
        text += f"{CAT_FACE} المردود عليهم: {len(acc['replied_to'])} شخص\n"
        text += f"{PC} عدد مرات الفلود: {acc.get('flood_count', 0)}\n"
        text += f"{LOCK} آخر خطأ: {acc.get('last_error') or 'لا يوجد'}\n"
        text += f"{MEDAL} النشر: {'يعمل' if acc['active'] else 'متوقف'}\n\n"

        if acc.get('last_error'):
            text += f"{COIN} تحذير: {acc['last_error']}\n"
            text += f"{MEDAL2} فعل وضع الحماية القصوى إذا تكرر الخطأ"
        else:
            text += f"{DISCO} الحساب آمن - يمكنك متابعة النشر"

        await safe_edit(event, text, buttons=[[Button.inline("رجوع", f"account_menu_{account_id}")]])
        return

    elif data == 'rename_account':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'select_account_for_rename'
        accounts_btns = []
        for acc_id, acc in user['accounts'].items():
            accounts_btns.append([Button.inline(f"{acc['name']}", f"rename_account_{acc_id}")])
        accounts_btns.append([Button.inline("رجوع", b"back_main")])
        await safe_edit(event, f"{USER} اختر الحساب لتغيير اسمه:", buttons=accounts_btns)
        return

    elif data.startswith('rename_account_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        waiting_for[uid] = f'rename_account_{account_id}'
        await safe_edit(event, f"{USER} أرسل الاسم الجديد للحساب:", buttons=[[Button.inline("رجوع", f"account_menu_{account_id}")]])
        return

    elif data == 'delete_account':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'select_account_for_delete'
        accounts_btns = []
        for acc_id, acc in user['accounts'].items():
            accounts_btns.append([Button.inline(f"{acc['name']}", f"delete_account_{acc_id}")])
        accounts_btns.append([Button.inline("رجوع", b"back_main")])
        await safe_edit(event, f"{COIN} اختر الحساب للحذف:", buttons=accounts_btns)
        return

    elif data.startswith('delete_account_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        account_id = data.split('_')[2]
        acc = get_account(uid, account_id)
        if acc:
            key = f"{uid}_{account_id}"
            if key in active_clients:
                try:
                    await active_clients[key].disconnect()
                except:
                    pass
                del active_clients[key]

            if key in running_tasks:
                try:
                    running_tasks[key].cancel()
                    await asyncio.sleep(0.5)
                except:
                    pass
                del running_tasks[key]

            if key in typing_status:
                typing_status[key] = False

            del user['accounts'][account_id]
            save_db()

            await event.answer("تم حذف الحساب", alert=True)
            if not is_subscribed(uid):
                text, btns = welcome_menu(uid)
            else:
                text, btns = main_menu(uid)
            await safe_edit(event, text, buttons=btns)
        return

    elif data == 'toggle_storage':
        user['storage_enabled'] = not user['storage_enabled']
        save_db()
        status = "مفعل" if user['storage_enabled'] else "معطل"
        await event.answer(f"تخزين الرسائل: {status}", alert=True)
        text, btns = storage_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'set_storage_group':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'set_storage_group'
        await safe_edit(event, f"{FOLDER} أرسل يوزر أو رابط أو ايدي جروب التخزين:\n\n{MEDAL} مثال: @storage_group أو https://t.me/storage_group أو -1001234567890", buttons=[[Button.inline("رجوع", b"storage_settings")]])
        return

    elif data == 'toggle_smart_reply':
        user['smart_reply_enabled'] = not user['smart_reply_enabled']
        save_db()
        status = "مفعل" if user['smart_reply_enabled'] else "معطل"
        await event.answer(f"الردود الذكية: {status}", alert=True)
        text, btns = storage_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'manage_smart_replies':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'manage_smart_replies'
        replies = user['smart_replies']
        if not replies:
            text = f"{USER} لا توجد ردود ذكية مضافة\n\n{MEDAL} أضف ردود ذكية للتعرف على الرسائل والرد تلقائياً"
        else:
            text = f"{USER} الردود الذكية ({len(replies)}):\n\n"
            for i, (keyword, reply) in enumerate(replies.items(), 1):
                text += f"{i}. الكلمة المفتاحية: {keyword}\n   الرد: {reply[:30]}{'...' if len(reply) > 30 else ''}\n\n"

        btns = [
            [Button.inline("إضافة رد ذكي", b"add_smart_reply")],
            [Button.inline("حذف رد ذكي", b"del_smart_reply")],
            [Button.inline("رجوع", b"storage_settings")]
        ]
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'add_smart_reply':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'add_smart_reply_keyword'
        await safe_edit(event, f"{USER} أرسل الكلمة المفتاحية للرد الذكي:\n\n{MEDAL} مثال: مرحباً أو كيف حالك", buttons=[[Button.inline("رجوع", b"manage_smart_replies")]])
        return

    elif data == 'del_smart_reply':
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        waiting_for[uid] = 'del_smart_reply'
        replies = user['smart_replies']
        if not replies:
            await event.answer("لا توجد ردود ذكية للحذف", alert=True)
            return

        btns = []
        for keyword in replies.keys():
            btns.append([Button.inline(f"{keyword}", f"del_smart_reply_{keyword}")])
        btns.append([Button.inline("رجوع", b"manage_smart_replies")])
        await safe_edit(event, f"{COIN} اختر الرد الذكي للحذف:", buttons=btns)
        return

    elif data.startswith('del_smart_reply_'):
        if not is_subscribed(uid):
            await event.answer("يجب تفعيل الاشتراك أولا", alert=True)
            return

        keyword = data.split('_', 3)[3]
        if keyword in user['smart_replies']:
            del user['smart_replies'][keyword]
            save_db()
            await event.answer(f"تم حذف الرد الذكي: {keyword}", alert=True)
        text, btns = storage_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'admin':
        if uid != ADMIN_ID:
            return
        await safe_edit(event, f"{USER} لوحة المبرمج", buttons=admin_menu())
        return

    elif data == 'manage_codes':
        if uid != ADMIN_ID:
            return
        await safe_edit(event, f"{COIN} إدارة أكواد VIP", buttons=manage_codes_menu())
        return

    elif data == 'generate_vip_code':
        if uid != ADMIN_ID:
            return

        waiting_for[uid] = 'generate_vip_code_days'
        await safe_edit(event, f"{COIN} أرسل عدد أيام صلاحية الكود:", buttons=[[Button.inline("رجوع", b"manage_codes")]])
        return

    elif data == 'deactivate_vip_code':
        if uid != ADMIN_ID:
            return

        waiting_for[uid] = 'deactivate_vip_code'
        active_codes = [code for code, data in db['codes'].items() if data['active']]
        if not active_codes:
            await event.answer("لا توجد أكواد نشطة", alert=True)
            return

        btns = []
        for code in active_codes:
            btns.append([Button.inline(f"{code} ({db['codes'][code]['days']} يوم)", f"deactivate_code_{code}")])
        btns.append([Button.inline("رجوع", b"manage_codes")])
        await safe_edit(event, f"{COIN} اختر الكود لإلغاء تفعيله:", buttons=btns)
        return

    elif data.startswith('deactivate_code_'):
        if uid != ADMIN_ID:
            return

        code = data.split('_')[2]
        if code in db['codes'] and db['codes'][code]['active']:
            db['codes'][code]['active'] = False
            db['codes'][code]['used_by'] = None
            db['codes'][code]['used_at'] = None
            save_db()
            await event.answer(f"تم إلغاء تفعيل الكود: {code}", alert=True)
        await safe_edit(event, f"{COIN} إدارة أكواد VIP", buttons=manage_codes_menu())
        return

    elif data == 'list_active_codes':
        if uid != ADMIN_ID:
            return

        active_codes = [code for code, data in db['codes'].items() if data['active']]
        if not active_codes:
            await event.answer("لا توجد أكواد نشطة", alert=True)
            return

        text = f"{COIN} الأكواد النشطة ({len(active_codes)}):\n\n"
        for code in active_codes:
            text += f"{MEDAL} {code} - {db['codes'][code]['days']} يوم\n"

        await safe_edit(event, text, buttons=[[Button.inline("رجوع", b"manage_codes")]])
        return

    elif data == 'users':
        if uid != ADMIN_ID:
            return

        users_list = []
        for user_id, user_data in db['users'].items():
            sub_status = "VIP" if user_data.get('vip', False) else ("مفعل" if is_subscribed(int(user_id)) else "غير مفعل")
            accounts_count = len(user_data.get('accounts', {}))
            users_list.append(f"{MEDAL} {user_id} - {sub_status} - حسابات: {accounts_count}")
        text = "\n".join(users_list[:50]) or "لا يوجد مستخدمين"
        btns = [
            [Button.inline("المزيد", b"more_users")],
            [Button.inline("رجوع", b"admin")]
        ]
        await safe_edit(event, f"{COIN} المستخدمين ({len(db['users'])}):\n\n{text}", buttons=btns)
        return

    elif data == 'more_users':
        if uid != ADMIN_ID:
            return

        users_list = []
        for user_id, user_data in list(db['users'].items())[50:100]:
            sub_status = "VIP" if user_data.get('vip', False) else ("مفعل" if is_subscribed(int(user_id)) else "غير مفعل")
            accounts_count = len(user_data.get('accounts', {}))
            users_list.append(f"{MEDAL} {user_id} - {sub_status} - حسابات: {accounts_count}")
        text = "\n".join(users_list) or "لا يوجد المزيد"
        btns = [
            [Button.inline("رجوع", b"users")]
        ]
        await safe_edit(event, f"{COIN} المستخدمين (51-100):\n\n{text}", buttons=btns)
        return

    elif data == 'admin_stats':
        if uid != ADMIN_ID:
            return

        total_users = len(db['users'])
        active_vip = sum(1 for u in db['users'].values() if u.get('vip', False))
        active_subs = sum(1 for u in db['users'].keys() if is_subscribed(int(u)) and not db['users'][str(u)].get('vip', False))
        total_accounts = sum(len(u.get('accounts', {})) for u in db['users'].values())
        total_sent = db['stats']['total_sent']
        active_codes = len([code for code, data in db['codes'].items() if data['active']])

        text = f"{BRIEFCASE} إحصائيات البوت\n\n"
        text += f"{COIN} إجمالي المستخدمين: {total_users}\n"
        text += f"{DISCO} مستخدمي VIP: {active_vip}\n"
        text += f"{MEDAL} الاشتراكات الفعالة: {active_subs}\n"
        text += f"{USER} إجمالي الحسابات: {total_accounts}\n"
        text += f"{COIN2} إجمالي الرسائل المرسلة: {total_sent}\n"
        text += f"{BRIEFCASE2} إجمالي الجروبات: {sum(len(u.get('accounts', {}).get(a, {}).get('groups', [])) for u in db['users'].values() for a in u.get('accounts', {}))}\n"
        text += f"{ID_CARD} أكواد VIP النشطة: {active_codes}"

        await safe_edit(event, text, buttons=[[Button.inline("رجوع", b"admin")]])
        return

    elif data == 'backup_sessions':
        if uid != ADMIN_ID:
            return

        backup_sessions()
        await event.answer("تم عمل نسخة احتياطية لكل الجلسات", alert=True)
        return

    elif data == 'download_backup':
        if uid != ADMIN_ID:
            return

        try:
            with open(BACKUP_FILE, 'rb') as f:
                await event.respond(f"{ID_CARD} النسخة الاحتياطية:", file=f)
        except:
            await event.answer("لا توجد نسخة احتياطية", alert=True)
        return

    elif data == 'broadcast':
        if uid != ADMIN_ID:
            return

        waiting_for[uid] = 'broadcast'
        await safe_edit(event, f"{COIN} أرسل رسالة الإشعار العام:", buttons=[[Button.inline("رجوع", b"admin")]])
        return

    elif data == 'toggle_notifications':
        if uid != ADMIN_ID:
            return

        db['login_notifications'] = not db.get('login_notifications', True)
        save_db()
        await safe_edit(event, f"{USER} لوحة المبرمج", buttons=admin_menu())
        return

    elif data == 'toggle_vip_system':
        if uid != ADMIN_ID:
            return

        db['vip_enabled'] = not db.get('vip_enabled', True)
        save_db()
        await safe_edit(event, f"{USER} لوحة المبرمج", buttons=admin_menu())
        return

@bot.on(events.NewMessage)
async def handle_messages(event):
    uid = event.sender_id
    if uid not in waiting_for:
        return

    action = waiting_for[uid]
    text = event.raw_text.strip()
    user = get_user_data(uid)

    if action == 'activate_vip_code':
        if text in db['codes'] and db['codes'][text]['active']:
            user['vip'] = True
            user['sub_end'] = (datetime.now() + timedelta(days=db['codes'][text]['days'])).isoformat()
            user['vip_code'] = text
            db['codes'][text]['active'] = False
            db['codes'][text]['used_by'] = uid
            db['codes'][text]['used_at'] = datetime.now().isoformat()
            db['stats']['active_vip'] = db['stats'].get('active_vip', 0) + 1
            save_db()

            del waiting_for[uid]
            await event.reply(f"{PARTY} تم تفعيل VIP بنجاح!\n\n{COIN} صلاحية الاشتراك: {db['codes'][text]['days']} يوم\n{USER} يمكنك الآن استخدام جميع مميزات البوت", parse_mode='html')
            text, btns = main_menu(uid)
            await event.respond(text, buttons=btns, parse_mode='html')

            if db.get('login_notifications', True):
                try:
                    await bot.send_message(ADMIN_ID, f"{MEDAL} تم تفعيل VIP لمستخدم\n\n{USER} المستخدم: {uid}\n{COIN} الكود: {text}\n{BRIEFCASE} الأيام: {db['codes'][text]['days']}\n{LOCK} الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
                except:
                    pass
        else:
            await event.reply(f"{COIN} كود غير صالح أو منتهي الصلاحية\n\n{MEDAL} تأكد من صحة الكود وحاول مرة أخرى", parse_mode='html')

    elif action == 'add_account_session':
        try:
            session_str = text.strip()
            if not session_str:
                raise ValueError("الجلسة فارغة")

            # Test the session
            test_client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await test_client.connect()
            if not await test_client.is_user_authorized():
                raise ValueError("الجلسة غير صالحة")

            me = await test_client.get_me()
            phone = me.phone
            await test_client.disconnect()

            # Check if account already exists
            for acc_id, acc in user['accounts'].items():
                if acc['phone'] == phone:
                    await event.reply(f"{COIN} هذا الحساب مضاف بالفعل", parse_mode='html')
                    del waiting_for[uid]
                    return

            # Add new account
            account_id = str(uuid.uuid4())
            user['accounts'][account_id] = get_account_defaults({
                'phone': phone,
                'session': session_str,
                'name': f'حساب {phone[-4:]}'
            })
            save_db()

            del waiting_for[uid]
            await event.reply(f"{DISCO} تم إضافة الحساب بنجاح\n\n{USER} الرقم: {phone}\n{COIN} الاسم: حساب {phone[-4:]}", parse_mode='html')

            if db.get('login_notifications', True):
                try:
                    await bot.send_message(ADMIN_ID, f"{MEDAL} حساب جديد مضاف\n\n{USER} المستخدم: {uid}\n{COIN} الرقم: {phone}\n{BRIEFCASE} الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
                except:
                    pass

            if not is_subscribed(uid):
                text, btns = welcome_menu(uid)
            else:
                text, btns = main_menu(uid)
            await event.respond(text, buttons=btns, parse_mode='html')
        except Exception as e:
            await event.reply(f"{COIN} خطأ في إضافة الحساب: {str(e)}\n\n{MEDAL} تأكد من صحة الجلسة وحاول مرة أخرى", parse_mode='html')
            del waiting_for[uid]

    elif action.startswith('fetch_groups_'):
        account_id = action.split('_')[2]
        acc = get_account(uid, account_id)
        if not acc:
            del waiting_for[uid]
            return

        msg = await event.reply(f"{BRIEFCASE} جاري جلب الجروبات...\n\n{MEDAL} قد يستغرق هذا بعض الوقت حسب عدد الجروبات", parse_mode='html')

        client = await get_user_client(uid, account_id)
        if not client:
            await msg.edit(f"{COIN} الحساب غير متصل\n\n{MEDAL} تأكد من صحة الجلسة وحاول مرة أخرى", buttons=[[Button.inline("رجوع", b"back_main")]], parse_mode='html')
            del waiting_for[uid]
            return

        groups = []
        try:
            async for dialog in client.iter_dialogs():
                if (dialog.is_group or getattr(dialog.entity, 'megagroup', False) or getattr(dialog.entity, 'gigagroup', False)) and not getattr(dialog.entity, 'broadcast', False):
                    group_info = f"{dialog.entity.title} ({dialog.entity.id})"
                    if dialog.entity.username:
                        group_info += f" (@{dialog.entity.username})"
                    groups.append(group_info)

                    # Limit to 1000 groups
                    if len(groups) >= 1000:
                        break
        except Exception as e:
            await msg.edit(f"{COIN} خطأ في جلب الجروبات: {str(e)}", buttons=[[Button.inline("رجوع", b"back_main")]], parse_mode='html')
            del waiting_for[uid]
            return

        acc['groups'] = []
        for group in groups:
            # Extract ID from the string
            match = re.search(r'\((-?\d+)\)', group)
            if match:
                group_id = match.group(1)
                acc['groups'].append(group_id)

        save_db()
        del waiting_for[uid]

        groups_text = '\n'.join(groups[:20])
        if len(groups) > 20:
            groups_text += f"\n{MEDAL}... و {len(groups)-20} آخرين"

        await msg.edit(f"{DISCO} تم جلب {len(groups)} جروب\n\n{groups_text}", buttons=[[Button.inline("رجوع", f"account_menu_{account_id}")]], parse_mode='html')

    elif action.startswith('add_group_'):
        account_id = action.split('_')[2]
        acc = get_account(uid, account_id)
        if not acc:
            del waiting_for[uid]
            return

        client = await get_user_client(uid, account_id)
        if not client:
            await event.reply(f"{COIN} الحساب غير متصل\n\n{MEDAL} تأكد من صحة الجلسة وحاول مرة أخرى", parse_mode='html')
            del waiting_for[uid]
            return

        groups_to_add = text.split('\n')
        added_count = 0
        failed_count = 0
        failed_groups = []

        for group in groups_to_add:
            group = group.strip()
            if not group:
                continue

            try:
                # Extract ID or username from the input
                group_id = None
                if group.startswith('@'):
                    group_id = group
                elif group.startswith('https://t.me/'):
                    group_id = '@' + group.split('https://t.me/')[1].split('/')[0]
                elif group.lstrip('-').isdigit():
                    group_id = int(group)
                else:
                    failed_groups.append(f"{group}: صيغة غير صحيحة")
                    failed_count += 1
                    continue

                if group_id in acc['groups']:
                    failed_groups.append(f"{group}: موجود بالفعل")
                    failed_count += 1
                    continue

                try:
                    entity = await client.get_entity(group_id)
                    if isinstance(entity, Channel) and entity.broadcast:
                        failed_groups.append(f"{group}: قناة وليست جروب")
                        failed_count += 1
                        continue

                    if not (getattr(entity, 'megagroup', False) or getattr(entity, 'gigagroup', False) or not isinstance(entity, Channel)):
                        failed_groups.append(f"{group}: ليس جروب")
                        failed_count += 1
                        continue

                    # Add the group ID to the list
                    if isinstance(group_id, int):
                        acc['groups'].append(str(group_id))
                    else:
                        acc['groups'].append(group_id)

                    added_count += 1
                except UserAlreadyParticipantError:
                    if isinstance(group_id, int):
                        acc['groups'].append(str(group_id))
                    else:
                        acc['groups'].append(group_id)
                    added_count += 1
                except Exception as e:
                    failed_groups.append(f"{group}: {str(e)[:40]}")
                    failed_count += 1

            except Exception as e:
                failed_groups.append(f"{group}: {str(e)[:40]}")
                failed_count += 1

        save_db()
        del waiting_for[uid]

        result_text = f"{DISCO} تمت إضافة الجروبات:\n\n"
        result_text += f"{BRIEFCASE} المضافة: {added_count}\n"
        result_text += f"{COIN} الفاشلة: {failed_count}\n\n"

        if failed_groups:
            result_text += f"{MEDAL} الأخطاء:\n" + '\n'.join(failed_groups[:5])
            if len(failed_groups) > 5:
                result_text += f"\n{MEDAL}... و {len(failed_groups)-5} آخرين"

        await event.reply(result_text, buttons=[[Button.inline("رجوع", f"manage_groups_{account_id}")]], parse_mode='html')

    elif action.startswith('del_group_'):
        account_id = action.split('_')[2]
        acc = get_account(uid, account_id)
        if not acc:
            del waiting_for[uid]
            return

        groups_to_remove = text.split('\n')
        removed_count = 0
        failed_count = 0
        failed_groups = []

        for group in groups_to_remove:
            group = group.strip()
            if not group:
                continue

            try:
                # Check if the group exists in the list
                if group in acc['groups']:
                    acc['groups'].remove(group)
                    removed_count += 1
                else:
                    # Try to match by ID
                    found = False
                    for g in acc['groups']:
                        if str(g) == str(group) or (g.startswith('@') and g[1:] == group) or (group.startswith('@') and g == group[1:]):
                            acc['groups'].remove(g)
                            removed_count += 1
                            found = True
                            break

                    if not found:
                        failed_groups.append(f"{group}: غير موجود")
                        failed_count += 1
            except Exception as e:
                failed_groups.append(f"{group}: {str(e)[:40]}")
                failed_count += 1

        save_db()
        del waiting_for[uid]

        result_text = f"{COIN} تم حذف الجروبات:\n\n"
        result_text += f"{BRIEFCASE} المحذوفة: {removed_count}\n"
        result_text += f"{MEDAL} الفاشلة: {failed_count}\n\n"

        if failed_groups:
            result_text += f"{SHOPPING} الأخطاء:\n" + '\n'.join(failed_groups[:5])
            if len(failed_groups) > 5:
                result_text += f"\n{SHOPPING}... و {len(failed_groups)-5} آخرين"

        await event.reply(result_text, buttons=[[Button.inline("رجوع", f"manage_groups_{account_id}")]], parse_mode='html')

    elif action == 'msg1':
        entities = extract_entities_from_message(event.message)
        if event.sticker:
            user['messages'][0] = {'text': '', 'entities': [], 'file_id': event.sticker.id, 'type': 'sticker'}
            await event.reply(f'{DISCO} تم حفظ الملصق كرسالة 1', parse_mode='html')
        else:
            user['messages'][0] = {'text': text, 'entities': entities, 'file_id': None, 'type': 'text'}
            await event.reply(f'{DISCO} تم حفظ الرسالة 1', parse_mode='html')
        save_db()
        del waiting_for[uid]
        if not is_subscribed(uid):
            text, btns = welcome_menu(uid)
        else:
            text, btns = main_menu(uid)
        await event.respond(text, buttons=btns, parse_mode='html')

    elif action == 'msg2':
        entities = extract_entities_from_message(event.message)
        if event.sticker:
            user['messages'][1] = {'text': '', 'entities': [], 'file_id': event.sticker.id, 'type': 'sticker'}
            await event.reply(f'{DISCO} تم حفظ الملصق كرسالة 2', parse_mode='html')
        else:
            user['messages'][1] = {'text': text, 'entities': entities, 'file_id': None, 'type': 'text'}
            await event.reply(f'{DISCO} تم حفظ الرسالة 2', parse_mode='html')
        save_db()
        del waiting_for[uid]
        if not is_subscribed(uid):
            text, btns = welcome_menu(uid)
        else:
            text, btns = main_menu(uid)
        await event.respond(text, buttons=btns, parse_mode='html')

    elif action == 'pub_interval':
        if not re.match(r'^(\d+|\d+-\d+)$', text):
            await event.reply(f"{COIN} صيغة غير صحيحة\n\n{MEDAL} مثال: 5 أو 5-10", parse_mode='html')
            return

        user['publish_interval'] = text
        save_db()
        del waiting_for[uid]
        await event.reply(f"{DISCO} تم تعيين وقت النشر: كل {text} دقيقة", parse_mode='html')
        if not is_subscribed(uid):
            text, btns = welcome_menu(uid)
        else:
            text, btns = main_menu(uid)
        await event.respond(text, buttons=btns, parse_mode='html')

    elif action.startswith('rename_account_'):
        account_id = action.split('_')[2]
        new_name = text.strip()
        if new_name:
            acc = get_account(uid, account_id)
            if acc:
                acc['name'] = new_name
                save_db()
                del waiting_for[uid]
                await event.reply(f"{DISCO} تم تغيير اسم الحساب إلى: {new_name}", parse_mode='html')
                text, btns = account_menu(uid, account_id)
                await safe_edit(event, text, buttons=btns)
        else:
            await event.reply(f"{COIN} الاسم لا يمكن أن يكون فارغاً", parse_mode='html')

    elif action == 'reply_msg':
        entities = extract_entities_from_message(event.message)
        user['auto_reply_msg'] = text
        user['auto_reply_entities'] = entities
        save_db()
        del waiting_for[uid]
        await event.reply(f"{DISCO} تم حفظ رسالة الرد التلقائي", parse_mode='html')
        text, btns = general_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)

    elif action == 'welcome_msg':
        entities = extract_entities_from_message(event.message)
        user['welcome_msg'] = text
        user['welcome_entities'] = entities
        save_db()
        del waiting_for[uid]
        await event.reply(f"{DISCO} تم حفظ رسالة الترحيب", parse_mode='html')
        text, btns = general_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)

    elif action == 'set_storage_group':
        try:
            group_id = None
            if text.startswith('@'):
                group_id = text
            elif text.startswith('https://t.me/'):
                group_id = '@' + text.split('https://t.me/')[1].split('/')[0]
            elif text.lstrip('-').isdigit():
                group_id = int(text)
            else:
                raise ValueError("صيغة غير صحيحة")

            # Test if the group is accessible
            client = await get_user_client(uid, next(iter(user['accounts'])))
            if client:
                try:
                    entity = await client.get_entity(group_id)
                    if not (getattr(entity, 'megagroup', False) or getattr(entity, 'gigagroup', False) or not isinstance(entity, Channel)):
                        raise ValueError("يجب أن يكون جروب وليس قناة")
                except:
                    raise ValueError("لا يمكن الوصول إلى الجروب")

            user['storage_group'] = str(group_id)
            save_db()
            del waiting_for[uid]
            await event.reply(f"{DISCO} تم تعيين جروب التخزين: {text}", parse_mode='html')
            text, btns = storage_settings_menu(uid)
            await safe_edit(event, text, buttons=btns)
        except Exception as e:
            await event.reply(f"{COIN} خطأ: {str(e)}\n\n{MEDAL} تأكد من صحة الرابط أو الايدي وحاول مرة أخرى", parse_mode='html')

    elif action == 'add_smart_reply_keyword':
        if not text:
            await event.reply(f"{COIN} الكلمة المفتاحية لا يمكن أن تكون فارغة", parse_mode='html')
            return

        waiting_for[uid] = f'add_smart_reply_{text}'
        await safe_edit(event, f"{USER} أرسل الرد على الكلمة المفتاحية: {text}", buttons=[[Button.inline("رجوع", b"manage_smart_replies")]])

    elif action.startswith('add_smart_reply_'):
        keyword = action.split('_', 3)[3]
        if not text:
            await event.reply(f"{COIN} الرد لا يمكن أن يكون فارغاً", parse_mode='html')
            return

        user['smart_replies'][keyword] = text
        save_db()
        del waiting_for[uid]
        await event.reply(f"{DISCO} تم إضافة الرد الذكي:\n\nالكلمة: {keyword}\nالرد: {text}", parse_mode='html')
        text, btns = storage_settings_menu(uid)
        await safe_edit(event, text, buttons=btns)

    elif action == 'generate_vip_code_days':
        try:
            days = int(text)
            if days <= 0:
                raise ValueError("عدد الأيام يجب أن يكون أكبر من صفر")

            code = str(uuid.uuid4())[:8].upper()
            db['codes'][code] = {
                'days': days,
                'active': True,
                'created_at': datetime.now().isoformat(),
                'created_by': uid,
                'used_by': None,
                'used_at': None
            }
            save_db()

            del waiting_for[uid]
            await event.reply(f"{PARTY} تم إنشاء كود VIP بنجاح!\n\n{COIN} الكود: {code}\n{USER} الأيام: {days}\n{LOCK} صلاحية الكود: غير محدودة حتى الاستخدام", parse_mode='html')
            await safe_edit(event, f"{COIN} إدارة أكواد VIP", buttons=manage_codes_menu())
        except ValueError:
            await event.reply(f"{COIN} عدد الأيام يجب أن يكون رقم صحيح أكبر من صفر", parse_mode='html')

    elif action == 'deactivate_vip_code':
        if text in db['codes'] and db['codes'][text]['active']:
            db['codes'][text]['active'] = False
            db['codes'][text]['used_by'] = None
            db['codes'][text]['used_at'] = None
            save_db()

            del waiting_for[uid]
            await event.reply(f"{COIN} تم إلغاء تفعيل الكود: {text}", parse_mode='html')
            await safe_edit(event, f"{COIN} إدارة أكواد VIP", buttons=manage_codes_menu())
        else:
            await event.reply(f"{COIN} كود غير صالح أو غير نشط", parse_mode='html')

    elif action == 'broadcast':
        if uid != ADMIN_ID:
            return

        msg_text = text
        count = 0
        for user_id in db['users'].keys():
            try:
                await bot.send_message(int(user_id), f"{COIN} إشعار من الإدارة:\n\n{msg_text}", parse_mode='html')
                count += 1
            except:
                pass

        del waiting_for[uid]
        await event.reply(f"{DISCO} تم إرسال الإشعار العام\n\n{MEDAL} وصلت إلى: {count} مستخدم", parse_mode='html')

async def publish_loop(uid, account_id):
    user = get_user_data(uid)
    acc = get_account(uid, account_id)
    if not acc:
        await log_error(uid, f'{COIN} الحساب غير موجود', account_id)
        return

    key = f"{uid}_{account_id}"
    client = await get_user_client(uid, account_id, show_typing=True)

    if not client:
        acc['active'] = False
        acc['last_error'] = 'فشل الاتصال بالحساب'
        save_db()
        await log_error(uid, f'{COIN} فشل الاتصال بالحساب', account_id)
        return

    try:
        if not await client.is_user_authorized():
            acc['active'] = False
            acc['last_error'] = 'انتهت صلاحية الجلسة'
            save_db()
            await log_error(uid, f'{COIN} انتهت صلاحية الجلسة - احذف الحساب وأضفه مرة أخرى', account_id)
            return

        await log_error(uid, f'{DISCO} بدأ النشر - عدد الجروبات: {len(acc["groups"])}', account_id)
        stealth = STEALTH_MODES[user['stealth_mode']]
        flood_protection = FLOOD_PROTECTION_LEVELS[user['flood_protection']]
        msg_index = random.randint(0, 1)  # Choose randomly between 0 and 1

        while acc['active'] and is_subscribed(uid):
            msgs = user['messages']
            if not acc['groups']:
                await log_error(uid, f'{COIN} قائمة الجروبات فارغة - قم بجلب الجروبات', account_id)
                acc['active'] = False
                save_db()
                return

            # Check if at least one message is set
            if not any(msg['text'] or msg['file_id'] for msg in msgs):
                await log_error(uid, f'{COIN} لا توجد رسائل مضبوطة - قم بتعيين الرسائل', account_id)
                acc['active'] = False
                save_db()
                return

            # Choose a random message (0 or 1)
            msg_index = random.randint(0, 1)
            msg_data = msgs[msg_index]
            if not msg_data['text'] and not msg_data['file_id']:
                # Skip empty messages
                continue

            groups_to_remove = []
            sent_count = 0
            failed_count = 0
            error_details = []

            for group in acc['groups']:
                try:
                    # Check flood protection
                    if acc['flood_count'] >= flood_protection['max_retries']:
                        last_flood = datetime.fromisoformat(acc['last_flood_time']) if acc['last_flood_time'] else datetime.now()
                        wait_time = (datetime.now() - last_flood).total_seconds()
                        if wait_time < flood_protection['delay'] * 60:
                            await asyncio.sleep((flood_protection['delay'] * 60) - wait_time)
                        acc['flood_count'] = 0
                        save_db()

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
                        error_details.append(f"{group}: قناة وليست جروب")
                        groups_to_remove.append(group)
                        failed_count += 1
                        continue

                    if not (getattr(chat, 'megagroup', False) or getattr(chat, 'gigagroup', False) or not isinstance(chat, Channel)):
                        error_details.append(f"{group}: ليس جروب")
                        groups_to_remove.append(group)
                        failed_count += 1
                        continue

                    # Simulate typing before sending message
                    await client(functions.messages.SetTypingRequest(
                        peer=chat,
                        action=types.SendMessageTypingAction()
                    ))
                    await asyncio.sleep(random.uniform(1, 3))

                    if msg_data['type'] == 'sticker' and msg_data['file_id']:
                        await client.send_file(chat, msg_data['file_id'])
                    else:
                        entities = build_entities(msg_data.get('entities', []))
                        await client.send_message(chat, msg_data['text'], formatting_entities=entities)

                    acc['sent_count'] += 1
                    db['stats']['total_sent'] += 1
                    sent_count += 1
                    save_db()

                    # Store the message if storage is enabled
                    if user['storage_enabled'] and user['storage_group']:
                        try:
                            storage_group = await client.get_entity(user['storage_group'])
                            if msg_data['type'] == 'sticker' and msg_data['file_id']:
                                await client.send_file(storage_group, msg_data['file_id'], caption=f"رسالة مرسلة إلى: {group}")
                            else:
                                await client.send_message(storage_group, f"رسالة مرسلة إلى: {group}\n\n{msg_data['text']}", formatting_entities=entities)
                        except Exception as e:
                            await log_error(uid, f'{COIN} خطأ في تخزين الرسالة: {str(e)}', account_id)

                    delay = random.randint(*stealth['group_delay'])
                    if user['flood_protection'] >= 1:
                        delay += random.randint(1, 5)
                    if user['flood_protection'] >= 2:
                        delay += random.randint(5, 15)
                    if user['flood_protection'] >= 3:
                        delay += random.randint(15, 30)

                    await asyncio.sleep(delay)

                except (ChatWriteForbiddenError, ChatAdminRequiredError, UserBannedInChannelError, ChannelPrivateError, UserNotParticipantError):
                    error_details.append(f"{group}: محظور/غير عضو")
                    groups_to_remove.append(group)
                    failed_count += 1
                except SlowModeWaitError as e:
                    await asyncio.sleep(e.seconds + 5)
                except FloodWaitError as e:
                    acc['flood_count'] = acc.get('flood_count', 0) + 1
                    acc['last_flood_time'] = datetime.now().isoformat()
                    acc['last_error'] = f'فلود {e.seconds} ثانية'
                    save_db()
                    await log_error(uid, f'{COIN} فلود وايت {e.seconds} ثانية - الانتظار {flood_protection["delay"]} دقيقة', account_id)
                    await asyncio.sleep(e.seconds + (flood_protection['delay'] * 60))
                except UserDeactivatedBanError:
                    acc['active'] = False
                    acc['last_error'] = 'الحساب محظور من تيليجرام'
                    save_db()
                    await log_error(uid, f'{COIN} الحساب محظور من تيليجرام نهائياً', account_id)
                    return
                except AuthKeyUnregisteredError:
                    acc['active'] = False
                    acc['last_error'] = 'انتهت صلاحية الجلسة'
                    save_db()
                    await log_error(uid, f'{COIN} انتهت صلاحية الجلسة - احذف الحساب وأضفه مرة أخرى', account_id)
                    return
                except DocumentInvalidError:
                    # Skip this group if document error occurs
                    error_details.append(f"{group}: خطأ في المستند")
                    failed_count += 1
                    continue
                except Exception as e:
                    error_details.append(f"{group}: {str(e)[:40]}")
                    failed_count += 1

            for g in groups_to_remove:
                if g in acc['groups']:
                    acc['groups'].remove(g)
            if groups_to_remove:
                save_db()

            if sent_count == 0 and len(acc['groups']) > 0:
                error_msg = f"{COIN} فشل النشر في كل الجروبات:\n" + "\n".join(error_details[:5])
                await log_error(uid, error_msg, account_id)
                acc['active'] = False
                acc['last_error'] = 'فشل في كل الجروبات'
                save_db()
                return

            # Wait for the next publishing cycle
            interval = parse_interval(user['publish_interval'])
            await asyncio.sleep(interval * 60)

    except asyncio.CancelledError:
        await log_error(uid, f'{COIN} تم إيقاف النشر', account_id)
    except Exception as e:
        acc['active'] = False
        acc['last_error'] = str(e)[:100]
        save_db()
        await log_error(uid, f'{COIN} خطأ عام في النشر: {type(e).__name__}: {str(e)[:100]}', account_id)
    finally:
        await stop_typing_simulation(uid, account_id)
        try:
            await client.disconnect()
        except:
            pass

async def start_auto_reply(uid, account_id):
    user = get_user_data(uid)
    acc = get_account(uid, account_id)
    if not acc or not user['auto_reply']:
        return

    client = await get_user_client(uid, account_id)
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
                            save_db()

                            # Store the interaction if storage is enabled
                            if user['storage_enabled'] and user['storage_group']:
                                try:
                                    storage_group = await client.get_entity(user['storage_group'])
                                    await client.send_message(storage_group, f"تم الرد على منشن من: {event.sender_id}\n\nالرسالة الأصلية: {event.raw_text}")
                                except Exception as e:
                                    await log_error(uid, f'{COIN} خطأ في تخزين التفاعل: {str(e)}', account_id)

                elif event.is_private and user['welcome_msg'] and user['welcome_enabled']:
                    sender_id = event.sender_id
                    if sender_id not in user['welcome_sent']:
                        entities = build_entities(user.get('welcome_entities', []))
                        await event.reply(user['welcome_msg'], formatting_entities=entities)
                        user['welcome_sent'].append(sender_id)
                        save_db()

                        # Store the welcome message if storage is enabled
                        if user['storage_enabled'] and user['storage_group']:
                            try:
                                storage_group = await client.get_entity(user['storage_group'])
                                await client.send_message(storage_group, f"تم إرسال رسالة ترحيب إلى: {sender_id}")
                            except Exception as e:
                                await log_error(uid, f'{COIN} خطأ في تخزين الترحيب: {str(e)}', account_id)

                # Smart replies
                if event.is_group and user['smart_reply_enabled'] and user['smart_replies']:
                    message_text = event.raw_text.lower()
                    for keyword, reply in user['smart_replies'].items():
                        if keyword.lower() in message_text:
                            await event.reply(reply)
                            # Store the smart reply if storage is enabled
                            if user['storage_enabled'] and user['storage_group']:
                                try:
                                    storage_group = await client.get_entity(user['storage_group'])
                                    await client.send_message(storage_group, f"تم الرد الذكي على: {event.sender_id}\n\nالكلمة المفتاحية: {keyword}\nالرسالة الأصلية: {event.raw_text}")
                                except Exception as e:
                                    await log_error(uid, f'{COIN} خطأ في تخزين الرد الذكي: {str(e)}', account_id)
                            break

            except Exception as e:
                await log_error(uid, f'{COIN} خطأ في الرد التلقائي: {str(e)}', account_id)

        while acc['active'] and user['auto_reply'] and is_subscribed(uid):
            await asyncio.sleep(60)

    except Exception as e:
        await log_error(uid, f'{COIN} خطأ في بدء الرد التلقائي: {str(e)}', account_id)

async def backup_task():
    while True:
        await asyncio.sleep(86400)  # Every 24 hours
        backup_sessions()
        if db.get('login_notifications', True):
            try:
                await bot.send_message(ADMIN_ID, f"{ID_CARD} نسخة احتياطية تلقائية\n\n{USER} تم حفظ {len(db['users'])} مستخدم\n{BRIEFCASE} الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
            except:
                pass

async def main():
    load_db()
    asyncio.create_task(backup_task())

    # Delete webhook to ensure bot works properly
    async with aiohttp.ClientSession() as session:
        await session.post(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true')

    try:
        await bot.start(bot_token=BOT_TOKEN)
        me = await bot.get_me()
        print(f"Bot Started Successfully... @{me.username}")
        await bot.run_until_disconnected()
    except DocumentInvalidError:
        print("Error: Invalid document file. Please check your bot token and API credentials.")
    except Exception as e:
        print(f"Error starting bot: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
