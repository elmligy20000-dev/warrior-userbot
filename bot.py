from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest
from telethon.tl.types import ChatAdminRights
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

# ===== بيانات البوت =====
API_ID = 20867472
API_HASH = 'abedd7fb77eaf1f88bd3f286ea952253'
BOT_TOKEN = '8603695783:AAG97upYHXXICtlowOe5zJWt_5aSpeFTKTA'
ADMIN_ID = 932862531
DEVELOPER_USERNAME = 'Programmer_error'
DEVELOPER_LINK = f'https://t.me/{DEVELOPER_USERNAME}'
REQUIRED_CHANNELS = ['Programmer_error1']
FORCE_SUB_CHANNEL = "@Programmer_error1"
FORCE_SUB_GROUP = "@Programmer_error2"
DB_FILE = 'database.json'
BACKUP_FILE = 'sessions_backup.json'
FREE_TRIAL_DAYS = 0

# الايموجي البريميوم
SPARK = '<b><tg-emoji emoji-id="5884015001206791984">✨</tg-emoji></b>'
DICE = '<b><tg-emoji emoji-id="5886716969427672960">🎲</tg-emoji></b>'
SUN = '<b><tg-emoji emoji-id="5884250988184870485">🔅</tg-emoji></b>'
BOLT = '<b><tg-emoji emoji-id="5886360482847137476">⚡️</tg-emoji></b>'
SIGNAL = '<b><tg-emoji emoji-id="5886386768046988787">📶</tg-emoji></b>'
GHOST = '<b><tg-emoji emoji-id="5883969276984959097">👾</tg-emoji></b>'
ROCKET = '<b><tg-emoji emoji-id="5886426509379378198">🚀</tg-emoji></b>'
USER = '<b><tg-emoji emoji-id="5886695331382435915">👤</tg-emoji></b>'
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
FIST = '<b><tg-emoji emoji-id="5888528603812995132">👊</tg-emoji></b>'
LOCK = '<b><tg-emoji emoji-id="5886403208292071168">🔒</tg-emoji></b>'
UNLOCK = '<b><tg-emoji emoji-id="5886403208292071170">🔓</tg-emoji></b>'
FOLDER = '<b><tg-emoji emoji-id="5886403208292071172">📁</tg-emoji></b>'
SETTINGS = '<b><tg-emoji emoji-id="5886403208292071174">⚙️</tg-emoji></b>'
STORAGE = '<b><tg-emoji emoji-id="5886403208292071176">🗃️</tg-emoji></b>'
PLUS = '<b><tg-emoji emoji-id="5886403208292071178">➕</tg-emoji></b>'
WRITING = '<b><tg-emoji emoji-id="5886403208292071180">✍️</tg-emoji></b>'
PC = '<b><tg-emoji emoji-id="5886664420502805908">💻</tg-emoji></b>'
PLANET = '<b><tg-emoji emoji-id="5886449487454416104">🪐</tg-emoji></b>'
CAT = '<b><tg-emoji emoji-id="5886470240736387171">🐈</tg-emoji></b>'

bot = TelegramClient('bot', API_ID, API_HASH)
db = {'users': {}, 'codes': {}, 'stats': {'total_sent': 0}, 'login_notifications': True, 'pending_crypto': {}}
waiting_for = {}
active_clients = {}
running_tasks = {}
user_clients = {}

STEALTH_MODES = {
    'fast': {'group_delay': [2, 5], 'name': 'سريع'},
    'balanced': {'group_delay': [5, 10], 'name': 'متوازن'},
    'safe': {'group_delay': [10, 20], 'name': 'آمن جدا'}
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
        if user.get('account', {}).get('session'):
            acc = user['account']
            backup[uid] = {
                'phone': acc['phone'],
                'session': acc['session'],
                'name': acc['name'],
                'user_id': uid,
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
            'publish_interval': '5-10', 'flood_protection': 2, 'stealth_mode': 'balanced',
            'auto_reply': True, 'auto_reply_msg': '', 'auto_reply_entities': [],
            'welcome_msg': '', 'welcome_entities': [], 'welcome_enabled': True,
            'welcome_sent': [], 'is_trial': False, 'used_trial': False,
            # ===== قسم السجل =====
            'log_enabled': False, # تفعيل/تعطيل السجل
            'log_group': None # ايدي جروب السجل -100...
        }
        save_db()

    # تحديث الداتا القديمة عشان محدش ياخد KeyError
    if 'welcome_enabled' not in db['users'][uid]:
        db['users'][uid]['welcome_enabled'] = True
    if 'welcome_sent' not in db['users'][uid]:
        db['users'][uid]['welcome_sent'] = []
    if 'used_trial' not in db['users'][uid]:
        db['users'][uid]['used_trial'] = False
    if 'auto_reply_entities' not in db['users'][uid]:
        db['users'][uid]['auto_reply_entities'] = []
    if 'welcome_entities' not in db['users'][uid]:
        db['users'][uid]['welcome_entities'] = []
    if 'log_enabled' not in db['users'][uid]:
        db['users'][uid]['log_enabled'] = False
    if 'log_group' not in db['users'][uid]:
        db['users'][uid]['log_group'] = None

    if len(db['users'][uid]['messages']) > 2:
        db['users'][uid]['messages'] = db['users'][uid]['messages'][:2]
    elif len(db['users'][uid]['messages']) < 2:
        while len(db['users'][uid]['messages']) < 2:
            db['users'][uid]['messages'].append({'text': '', 'entities': [], 'file_id': None, 'type': 'text'})

    if isinstance(db['users'][uid]['messages'][0], str):
        old_msgs = db['users'][uid]['messages']
        db['users'][uid]['messages'] = [
            {'text': old_msgs[0] if len(old_msgs) > 0 else '', 'entities': [], 'file_id': None, 'type': 'text'},
            {'text': old_msgs[1] if len(old_msgs) > 1 else '', 'entities': [], 'file_id': None, 'type': 'text'}
        ]
    return db['users'][uid]

def is_subscribed(uid):
    if uid == ADMIN_ID:
        return True
    user = get_user_data(uid)
    sub_end = user.get('sub_end')
    if not sub_end:
        return False
    try:
        return datetime.fromisoformat(sub_end) > datetime.now()
    except:
        return False

def get_remaining_days(uid):
    user = get_user_data(uid)
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
            not_joined.append(('قناة السورس', FORCE_SUB_CHANNEL))
        except:
            pass

    if FORCE_SUB_GROUP:
        try:
            await bot.get_permissions(FORCE_SUB_GROUP, uid)
        except UserNotParticipantError:
            not_joined.append(('جروب الدعم', FORCE_SUB_GROUP))
        except:
            pass

    return len(not_joined) == 0, not_joined

def get_account(uid):
    user = get_user_data(uid)
    acc = user.get('account')
    if not acc:
        return None
    return get_account_defaults(acc)

def get_account_defaults(acc):
    if not acc:
        return None
    defaults = {
        'active': False, 'groups': [], 'name': 'حسابك',
        'phone': '', 'session': '', 'sent_count': 0,
        'last_error': None, 'created_at': datetime.now().isoformat(),
        'replied_to': []
    }
    for k, v in defaults.items():
        if k not in acc:
            acc[k] = v
    return acc

def gen_code(days=30):
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=12))
    db['codes'][code] = days
    save_db()
    return code

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

# واجهة موحدة واحدة بس - كل حاجة هنا
def main_menu(uid):
    user = get_user_data(uid)
    acc = get_account(uid)
    acc = get_account_defaults(acc) if acc else None

    reply_status = "✅" if user['auto_reply'] else "❌"
    welcome_status = "✅" if user['welcome_enabled'] else "❌"
    log_status = "✅" if user['log_enabled'] else "❌" # جديد
    log_group = f"({user['log_group']})" if user['log_group'] else "غير محدد" # جديد
    has_account = "✅" if acc else "❌"
    pub_status = "يعمل" if acc and acc['active'] else "متوقف"
    flood_level = ["❌", "🟡", "🟢", "🛡️"][user['flood_protection']]
    stealth = STEALTH_MODES[user['stealth_mode']]['name']

    msg1 = user['messages'][0]
    msg2 = user['messages'][1]

    def get_msg_status(msg):
        if msg['type'] == 'sticker': return "ملصق"
        elif msg['text']: return "نص"
        else: return "فارغ"

    btns = [
        [Button.inline(f"{has_account} الحساب: {acc['name'] if acc else 'غير مضاف'}", b"login_session")],
        [Button.inline(f"رسالة 1 - {get_msg_status(msg1)}", b"msg1"), Button.inline(f"رسالة 2 - {get_msg_status(msg2)}", b"msg2")],
        [Button.inline(f"النشر كل {user['publish_interval']} دقيقة", b"pub_interval")],
        [Button.inline(f"{flood_level} حماية التجميد", b"flood_level"), Button.inline(f"{stealth} التخفي", b"stealth_mode")],
        [Button.inline(f"جلب الجروبات", b"fetch_groups"), Button.inline(f"الجروبات ({len(acc['groups']) if acc else 0})", b"manage_groups")],
        [Button.inline(f"{reply_status} الرد التلقائي", b"toggle_reply"), Button.inline(f"{welcome_status} الترحيب", b"toggle_welcome")],
        [Button.inline(f"تعيين الرد", b"set_reply_msg"), Button.inline(f"تعيين الترحيب", b"set_welcome_msg")],
        # ===== قسم السجل الجديد =====
        [Button.inline(f"📝 جروب السجل", b"log_menu")],
        # =====
        [Button.inline(f"تشغيل النشر", b"start_pub"), Button.inline(f"ايقاف النشر", b"stop_pub")],
        [Button.inline(f"تحليل النشر", b"analyze"), Button.inline(f"نصائح الحماية", b"tips")],
        [Button.url(f"المبرمج", DEVELOPER_LINK)]
    ]
    if uid == ADMIN_ID:
        btns.insert(-1, [Button.inline(f"لوحة المبرمج", b"admin")])
    return btns

def admin_menu():
    notif_status = "✅" if db.get('login_notifications', True) else "❌"
    return [
        [Button.inline(f"توليد كود", b"gen_code"), Button.inline(f"الاكواد", b"list_codes")],
        [Button.inline(f"تفعيل VIP", b"activate_vip"), Button.inline(f"الغاء VIP", b"deactivate_vip")],
        [Button.inline(f"{notif_status} اشعارات الدخول", b"toggle_notifications")],
        [Button.inline(f"نسخة احتياطية", b"backup_sessions"), Button.inline(f"تحميل النسخ", b"download_backup")],
        [Button.inline(f"المستخدمين", b"users"), Button.inline(f"احصائيات", b"admin_stats")],
        [Button.inline(f"اذاعة", b"broadcast")],
        [Button.inline(f"رجوع", b"back_main")]
    ]

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
        except:
            try:
                del user_clients[key]
            except:
                pass

    # اعمل كلاينت جديد
    try:
        client = TelegramClient(StringSession(acc['session']), API_ID, API_HASH, device_model="iPhone 17 Pro", system_version="iOS 17.5", app_version="10.9.2")
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return None
        user_clients[key] = client
        return client
    except:
        return None

async def log_error(uid, error_text):
    try:
        await bot.send_message(uid, f"{SIGNAL} <b>تشخيص:</b>\n\n{error_text}", parse_mode='html')
    except:
        pass

# التصليح الجذري - بتبعت رسالة جديدة دايما
async def safe_edit(event, text, buttons=None):
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
        text = f"{BOLT} <b>عشان تستخدم البوت لازم تشترك هنا:</b>\n\n"
        btns = []
        for typ, link in not_joined:
            text += f"{SIGNAL} {typ}: {link}\n"
            btns.append([Button.url(f"اشترك في {typ}", f"https://t.me/{link.replace('@', '')}")])
        btns.append([Button.inline(f"تحققت", b"check_sub")])
        await event.reply(text, buttons=btns, parse_mode='html')
        return

    for channel in REQUIRED_CHANNELS:
        try:
            await bot(GetParticipantRequest(channel, uid))
        except:
            btns = [
                [Button.url(f"اشترك هنا اولا", f"https://t.me/{channel}")],
                [Button.inline(f"تحققت", b"check_sub")]
            ]
            await event.reply(f"{SPARK} <b>اشترك في القناة اولا</b>", buttons=btns, parse_mode='html')
            return

    if not is_subscribed(uid):
        btns = [
            [Button.inline(f"تفعيل كود", b"activate")], 
            [Button.inline(f"المميزات", b"features")],
            [Button.url(f"المبرمج", DEVELOPER_LINK)]
        ]

        welcome_text = f"""
{PC} <b>مرحباً بك في بوت النشر الاحترافي</b>

{PC} <b>أداء فائق • سرعة عالية • استقرار عالي</b>

{PC} <b>حماية متقدمة ضد الفلود والتجميد بأحدث تقنيات التخفي</b>

{PC} <b>دعم كامل لـ StringSession والإيموجي البريميوم</b>

{PC} <b>تم تصميم البوت لتقديم تجربة نشر احترافية بأعلى مستوى</b>

{PC} <b>لشراء كود التفعيل أو طلب سورس مماثل ، تواصل مع المبرمج</b>
"""
        await event.reply(welcome_text, buttons=btns, parse_mode='html')
        return

    days = get_remaining_days(uid)
    acc = get_account(uid)
    acc = get_account_defaults(acc) if acc else None
    sent = acc['sent_count'] if acc else 0

    text = f"{SPARK} <b>أهلاً بيك في بوت النشر المتطور الاحترافي</b> {GHOST}\n\n"
    text += f"{BOLT} <b>الاشتراك: {days} يوم متبقي</b>\n"
    text += f"{ROCKET} <b>الرسائل المرسله: {sent}</b>\n"
    text += f"{SIGNAL} <b>النشر: {'يعمل' if acc and acc['active'] else 'متوقف'}</b>\n\n"
    text += f"{USER} <b>كل حاجة في واجهة واحدة</b>"

    await event.respond(text, buttons=main_menu(uid), parse_mode='html')

@bot.on(events.CallbackQuery)
async def callback(event):
    uid = event.sender_id
    data = event.data.decode()
    user = get_user_data(uid)
    acc = get_account(uid)

    await event.answer()

    if data == 'back_main':
        await start(event)
        return

    elif data == 'log_menu':
        log_status = "مفعل ✅" if user.get('log_enabled') else "معطل ❌"
        log_id = user.get('log_group_id', 'غير موجود')

        text = f"{SIGNAL} <b>اعدادات جروب السجل</b>\n\n"
        text += f"الحالة: <b>{log_status}</b>\n"
        text += f"الايدي: <code>{log_id}</code>\n\n"
        text += f"1- اعمل جروب سوبر جروب باي اسم\n"
        text += f"2- ضيف البوت ادمن فيه\n"
        text += f"3- دوس `تعيين الجروب` وابعت الايدي\n"

        buttons = []
        if not user.get('log_group_id'):
            buttons.append([Button.inline("تعيين جروب السجل ➕", data="set_log")])
        else:
            buttons.append([Button.inline(f"تفعيل/تعطيل {log_status.split()[0]}", data="toggle_log")])
            buttons.append([Button.inline("حذف الجروب 🗑️", data="del_log_id")])

        buttons.append([Button.inline("رجوع ⬅️", data="back_main")])
        await event.edit(text, buttons=buttons, parse_mode='html')
        return

    elif data == 'set_log':
        user['awaiting_log_id'] = True # 4 مسافات
        save_db()
        await event.edit(
            f"{SIGNAL} ابعتلي ايدي جروب السجل دلوقتي\n"
            f"ازاي تجيب الايدي؟\n"
            f"1- ضيف البوت @userinfobot في الجروب\n"
            f"2- ابعتلي الايدي اللي هيبعتهولك\n"
            f"او ابعت `-100` والارقام",
            buttons=[[Button.inline("الغاء ❌", data="log_menu")]],
            parse_mode='html'
        )
        return

    elif data == 'toggle_log': # 4 مسافات
        user['log_enabled'] = not user.get('log_enabled', False)
        save_db()
        await event.answer(f"تم {'التفعيل' if user['log_enabled'] else 'التعطيل'} ✅")
        await callback(type('obj', (object,), {'data': b'log_menu', 'sender_id': uid, 'edit': event.edit, 'answer': event.answer})())
        return
        
    elif data == 'del_log_id': # 4 مسافات
        user['log_group_id'] = None
        user['log_enabled'] = False
        save_db()
        await event.answer("تم الحذف ✅")
        await callback(type('obj', (object,), {'data': b'log_menu', 'sender_id': uid, 'edit': event.edit, 'answer': event.answer})())
        return
        
    elif data == 'check_sub':
        await start(event)
        return

    elif data == 'free_trial':
        if user.get('used_trial'):
            await event.answer("استخدمت التجربة المجانية قبل كده", alert=True)
            return

        user['sub_end'] = (datetime.now() + timedelta(days=FREE_TRIAL_DAYS)).isoformat()
        user['is_trial'] = True
        user['used_trial'] = True
        save_db()

        await event.answer(f"تم تفعيل التجربة المجانية", alert=True)
        await safe_edit(event, f"{SPARK} <b>مبروك! حصلت على تجربة مجانية {FREE_TRIAL_DAYS} يوم</b> {PLANET}\n\n{BOLT} <b>تقدر تبدأ النشر دلوقتي</b>", buttons=[[Button.inline(f"ابدأ النشر", b"back_main")]])

        try:
            await bot.send_message(ADMIN_ID, f"{CAT} <b>تجربة مجانية جديدة</b>\n\n{USER} المستخدم: <code>{uid}</code>\n{SIGNAL} الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
        except:
            pass
        return

    elif data == 'login_session':
        waiting_for[uid] = 'session_login'
        await safe_edit(event, f"{PC}<b>ابعت جلسة السيشن StringSession:</b>\n\n{PC} مثال: <code>1BQAJ... طويلة</code>\n{PC} لو مو معك سيشن راسل المبرمج @{DEVELOPER_USERNAME}\n\n{BOLT} ابعت السيشن سطر واحد بدون مسافات", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return
    
    elif data == 'account_info':
        acc = get_account(uid)

        # لو مفيش حساب اعرض طرق التسجيل
        if not acc:
            btns = [
                [Button.inline(f"تسجيل الجلسة", b"login_session")],
                [Button.url(f"شرح استخراج الجلسه", f"https://t.me/Solve_problems_z6ybot/8")],
                [Button.url(f"موقع الاستخراج", f"https://telegram.tools/session-string-generator#telethon")],
                [Button.inline(f"رجوع", b"back_main")]
            ]
            await safe_edit(event, text, buttons=btns)
            return
        # لو فيه حساب اعرض المعلومات
        acc = get_account_defaults(acc)
        text = f"{SPARK} <b>معلومات الحساب</b>\n\n"
        text += f"{USER} الاسم: <b>{acc['name']}</b>\n"
        text += f"{ROCKET} الرقم: <code>{acc['phone']}</code>\n"
        text += f"{DICE} المرسلة: {acc['sent_count']}\n"
        text += f"{PC} الجروبات: {len(acc['groups'])}\n"
        text += f"{SIGNAL} الحالة: {'يعمل' if acc['active'] else 'متوقف'}\n"
        text += f"{SUN} تاريخ الاضافة: {acc['created_at'][:10]}\n\n"
        btns = [
            [Button.inline(f"{'ايقاف' if acc['active'] else 'تشغيل'}", b"toggle_account")],
            [Button.inline(f"تغيير الاسم", b"rename_account")],
            [Button.inline(f"حذف الحساب", b"delete_account")],
            [Button.inline(f"رجوع", b"back_main")]
        ]
        await safe_edit(event, text, buttons=btns)
        return

    elif data == 'msg1':
        waiting_for[uid] = 'msg1'
        await safe_edit(event, f"{SIGNAL} <b>ابعت الرسالة الاولى:</b>\n\n{BOLT} تقدر تبعت نص مع ايموجي بريميوم او ملصق\n{SPARK} البوت هيحفظه وينشره", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'msg2':
        waiting_for[uid] = 'msg2'
        await safe_edit(event, f"{SIGNAL} <b>ابعت الرسالة التانية:</b>\n\n{BOLT} تقدر تبعت نص مع ايموجي بريميوم او ملصق\n{SPARK} البوت هيبدل بينهم تلقائي", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'toggle_reply':
        user['auto_reply'] = not user['auto_reply']
        save_db()
        status = "مفعل" if user['auto_reply'] else "معطل"
        await event.answer(f"الرد التلقائي: {status}", alert=True)
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'toggle_welcome':
        user['welcome_enabled'] = not user['welcome_enabled']
        save_db()
        status = "مفعل" if user['welcome_enabled'] else "معطل"
        await event.answer(f"الترحيب: {status}", alert=True)
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'features':
        text = f"{PC} <b>مميزات البوت المتطورة</b>\n\n"

        text += f"{PC} <b>النشر التلقائي:</b>\n"
        text += f"{PC} <b>> إضافة حساب بجلسة StringSession</b>\n"
        text += f"{PC} <b>> رسالتان للنشر (Premium)</b>\n"
        text += f"{PC} <b>> دعم الإيموجي البريميوم</b>\n"
        text += f"{PC} <b>> دعم النصوص والصور والفيديو والملفات</b>\n"
        text += f"{PC} <b>> حذف تلقائي للمجموعات المحظورة</b>\n"
        text += f"{PC} <b>> تخطي المجموعات غير الصالحة</b>\n"
        text += f"{PC} <b>> جدولة النشر بالثواني</b>\n"
        text += f"{PC} <b>> إيقاف واستكمال النشر</b>\n"
        text += f"{PC} <b>> إحصائيات مباشرة أثناء النشر</b>\n\n"

        text += f"{PC} <b>الحماية:</b>\n"
        text += f"{PC} <b>> 3 مستويات حماية ضد Flood</b>\n"
        text += f"{PC} <b>> 3 أوضاع تخفي احترافية</b>\n"
        text += f"{PC} <b>> تأخير عشوائي ذكي</b>\n"
        text += f"{PC} <b>> إعادة اتصال تلقائية للحسابات</b>\n"
        text += f"{PC} <b>> مراقبة حالة الحسابات</b>\n"
        text += f"{PC} <b>> استقرار عالي أثناء التشغيل</b>\n\n"

        text += f"{PC} <b>الردود الذكية:</b>\n"
        text += f"{PC} <b>> الرد على المنشن والريبلاي</b>\n"
        text += f"{PC} <b>> ترحيب تلقائي بالخاص</b>\n"
        text += f"{PC} <b>> كلمات مفتاحية</b>\n"
        text += f"{PC} <b>> ردود متعددة</b>\n"
        text += f"{PC} <b>> تخصيص الردود لكل حساب</b>\n\n"

        text += f"{PC} <b>إدارة الحسابات:</b>\n"
        text += f"{PC} <b>> تشغيل وإيقاف الحسابات</b>\n"
        text += f"{PC} <b>> فحص حالة كل حساب</b>\n"
        text += f"{PC} <b>> إعادة تشغيل الحسابات المتوقفة</b>\n"
        text += f"{PC} <b>> تسجيل جميع العمليات</b>\n"
        text += f"{PC} <b>> دعم Multi Sessions</b>\n\n"

        text += f"{PC} <b>الأداء:</b>\n"
        text += f"{PC} <b>> سرعة تنفيذ عالية</b>\n"
        text += f"{PC} <b>> استهلاك منخفض للموارد</b>\n"
        text += f"{PC} <b>> تشغيل بدون توقف</b>\n"
        text += f"{PC} <b>> تحديثات مستمرة</b>\n"
        text += f"{PC} <b>> واجهة عربية احترافية</b>\n"
        text += f"{PC} <b>> لوحة تحكم سهلة وسريعة</b>\n\n"

        text += f"{PC} <b>الاشتراك:</b>\n"
        text += f"{PC} <b>> شراء كود التفعيل من المبرمج</b>\n"
        text += f"{PC} <b>> تفعيل الاشتراك فورياً</b>\n"
        text += f"{PC} <b>> تجديد الاشتراك بسهولة</b>\n"
        text += f"{PC} <b>> دعم فني مباشر</b>\n"
        
        btns = [[Button.url(f"المبرمج", DEVELOPER_LINK)], [Button.inline(f"رجوع", b"back_main")]]
        await safe_edit(event, text, buttons=btns)

    elif data == 'activate':
        waiting_for[uid] = 'code'
        await safe_edit(event, f"{PC} <b>ارسل كود التفعيل:</b>", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'fetch_groups':
        acc = get_account(uid)
        if not acc:
            text = f"{USER} <b>سجل الحساب اولاً:</b>"
            btns = [
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
                # ناخد ID بس، اسرع ومبيعملش فلود زي اليوزر
                if dialog.is_group or getattr(dialog.entity, 'megagroup', False) or getattr(dialog.entity, 'gigagroup', False):
                    if not getattr(dialog.entity, 'broadcast', False):
                        groups.append(f"-100{dialog.entity.id}")
                        
                # ريست كل 200 محادثة عشان نتفادى FloodWait مع 1000 حساب
                if total_dialogs % 200 == 0:
                    await asyncio.sleep(2)
                    try:
                        await msg.edit(f"{ROCKET} <b>جاري الجلب...</b>\n{SIGNAL} تم فحص {total_dialogs} محادثة\n{SPARK} لقيت {len(groups)} جروب لحد دلوقتي", parse_mode='html')
                    except:
                        pass

        except FloodWaitError as e:
            await msg.edit(f"{BOLT} <b>تيليجرام عمل حظر مؤقت</b>\n\n{SIGNAL} استنى {e.seconds} ثانية وجرب تاني\n{PC} دي حماية من تيليجرام عشان العدد كبير", buttons=[[Button.inline(f"رجوع", b"back_main")]], parse_mode='html')
            return
        except Exception as e:
            await msg.edit(f"{BOLT} <b>خطأ في الجلب:</b> <code>{str(e)[:100]}</code>", buttons=[[Button.inline(f"رجوع", b"back_main")]], parse_mode='html')
            return

        acc = get_account_defaults(acc)
        acc['groups'] = groups  # بنحفظ ID بس - اسرع للنشر
        db['users'][str(uid)]['account'] = acc
        save_db()
        
        await msg.edit(f"{SPARK} <b>تم جلب {len(groups)} جروب</b>\n\n{ROCKET} اجمالي المحادثات: {total_dialogs}\n{PC} محفوظ بالـ ID بس - اسرع للنشر\n{SIGNAL} لو عايز يوزرات فعل الجلب اليدوي", buttons=main_menu(uid), parse_mode='html')
        return

    elif data == 'manage_groups':
        acc = get_account(uid)
        if not acc:
            await event.answer("ضيف حساب الاول", alert=True)
            return
        acc = get_account_defaults(acc)
        groups_text = '\n'.join([f"{i+1}. <code>{g}</code>" for i, g in enumerate(acc['groups'][:20])])
        if len(acc['groups']) > 20:
            groups_text += f"\n{SIGNAL}... و {len(acc['groups'])-20} اخرين"
        btns = [
            [Button.inline(f"اضافة", b"add_group"), Button.inline(f"حذف", b"del_group")],
            [Button.inline(f"تفريغ الكل", b"clear_groups")],
            [Button.inline(f"رجوع", b"back_main")]
        ]
        await safe_edit(event, f"{ROCKET} <b>الجروبات ({len(acc['groups'])}):</b>\n\n{groups_text or 'لا يوجد'}", buttons=btns)
        return

    elif data == 'clear_groups':
        acc = get_account(uid)
        if not acc:
            return
        acc = get_account_defaults(acc)
        acc['groups'] = []
        user['account'] = acc
        save_db()
        await event.answer("تم تفريغ كل الجروبات", alert=True)
        await safe_edit(event, f"{ROCKET} <b>الجروبات (0):</b>\n\nلا يوجد", buttons=[
            [Button.inline(f"اضافة", b"add_group"), Button.inline(f"حذف", b"del_group")],
            [Button.inline(f"تفريغ الكل", b"clear_groups")],
            [Button.inline(f"رجوع", b"back_main")]
        ])
        return

    elif data == 'add_group':
        waiting_for[uid] = 'add_group'
        await safe_edit(event, f"{USER} <b>ابعت يوزر الجروب او الايدي تقدر تبعت كل رابط او يوزر او ايدي فكل سطر:</b>\n\n{SIGNAL} مثال: @Programmer_error2 او -1001234567890\n\n{BOLT} <b>مهم:</b> الحساب لازم يكون عضو في الجروب", buttons=[[Button.inline(f"رجوع", b"manage_groups")]])
        return

    elif data == 'del_group':
        waiting_for[uid] = 'del_group'
        await safe_edit(event, f"{BOLT} <b>ابعت رقم الجروب للحذف:</b>", buttons=[[Button.inline(f"رجوع", b"manage_groups")]])
        return

    elif data == 'pub_interval':
        waiting_for[uid] = 'pub_interval'
        await safe_edit(event, f"{ROCKET} <b>ابعت الوقت بين كل دورة نشر:</b>\n\n{SIGNAL} مثال: 5 او 5-10\n{BOLT} 5 = ثابت كل 5 دقايق\n{BOLT} 5-10 = عشوائي بين 5 و 10 دقايق\n\n{SUN} اقل حاجة: 1 دقيقة", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'flood_level':
        user['flood_protection'] = (user['flood_protection'] + 1) % 4
        save_db()
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'stealth_mode':
        modes = list(STEALTH_MODES.keys())
        current = modes.index(user['stealth_mode'])
        user['stealth_mode'] = modes[(current + 1) % len(modes)]
        save_db()
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
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

    elif data == 'stop_welcome':
        user['welcome_msg'] = ''
        user['welcome_entities'] = []
        save_db()
        await event.answer("تم ايقاف رسالة الترحيب")
        text = f"{BOLT} <b>تم ايقاف رسالة الترحيب بنجاح</b>\n\n"
        text += f"{SIGNAL} <b>مش هيبعت ترحيب للخاص دلوقتي</b>"
        await safe_edit(event, text, buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'toggle_log':
        user['log_enabled'] = not user['log_enabled']
        save_db()
        status = "مفعل" if user['log_enabled'] else "معطل"
        await event.answer(f"السجل: {status}", alert=True)
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'set_log_group':
        waiting_for[uid] = 'set_log_group'
        await safe_edit(event, f"{FOLDER} <b>ابعت ايدي جروب السجل:</b>\n\n{BOLT} لازم البوت والحساب يكونو ادمن في الجروب\n{SIGNAL} مثال: <code>-1001234567890</code>", buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return
    
    elif data == 'start_pub':
        acc = get_account(uid)
        if not acc:
            await event.answer("ضيف حساب الاول", alert=True)
            return
        acc = get_account_defaults(acc)
        if not acc['groups']:
            await event.answer("ضيف جروبات الاول - جلب الجروبات", alert=True)
            return
        if not user['messages'][0]['text'] and not user['messages'][0]['file_id']:
            await event.answer("ضيف رسالة على الاقل - رسالة 1", alert=True)
            return

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
        if user['auto_reply']:
            asyncio.create_task(start_auto_reply(uid))

        await event.answer("بدأ النشر بنجاح", alert=True)
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        await log_error(uid, f'{SPARK} بدأ النشر - {len(acc["groups"])} جروب')
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
            await event.answer("ضيف حساب الاول", alert=True)
            return
        acc = get_account_defaults(acc)

        # اتأكد من حالة الاتصال صح
        status = "غير معروف"
        try:
            client = await get_user_client(uid)
            if client and client.is_connected():
                me = await client.get_me()
                status = f"سليم - {me.first_name}"
            else:
                status = "غير متصل"
        except:
            status = "محظور او منتهي"

        text = f"{PC} <b>تحليل حالة الحساب</b>\n\n"

        text += f"{PC} <b>الاسم:</b> <code>{acc['name']}</code>\n"
        text += f"{PC} <b>رقم الهاتف:</b> <code>{acc['phone']}</code>\n"
        text += f"{PC} <b>الحالة:</b> <code>{status}</code>\n"
        text += f"{PC} <b>عدد المجموعات:</b> <code>{len(acc['groups'])}</code>\n"
        text += f"{PC} <b>الرسائل المرسلة:</b> <code>{acc['sent_count']}</code>\n"
        text += f"{PC} <b>فاصل النشر:</b> <code>{user['publish_interval']} دقيقة</code>\n"
        text += f"{PC} <b>وضع التخفي:</b> <code>{STEALTH_MODES[user['stealth_mode']]['name']}</code>\n"
        text += f"{PC} <b>مستوى حماية الفلود:</b> <code>{user['flood_protection']}</code>\n"
        text += f"{PC} <b>الردود التلقائية:</b> <code>{len(acc['replied_to'])} مستخدم</code>\n"
        text += f"{PC} <b>آخر خطأ:</b> <code>{acc.get('last_error') or 'لا يوجد'}</code>\n"
        text += f"{PC} <b>حالة النشر:</b> <code>{'🟢 يعمل' if acc['active'] else '🔴 متوقف'}</code>\n\n"

        text += f"{PC} <b>تم تحديث بيانات التحليل بنجاح.</b>"

        if acc.get('last_error'):
            text += f"{PC} <b>تحذير:</b> {acc['last_error']}\n"
            text += f"{PC} فعل وضع آمن جدا لو متكرر"
        else:
            text += f"{PC} <b>الحساب آمن</b> - كمل النشر"

        await safe_edit(event, text, buttons=[[Button.inline(f"رجوع", b"back_main")]])
        return

    elif data == 'admin':
        if uid!= ADMIN_ID:
            return
        await safe_edit(event, f"{USER} <b>لوحة الادمن</b>", buttons=admin_menu())
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
        codes_text = "\n".join([f"{PC} <code>{code}</code> - {days} يوم" for code, days in db['codes'].items()]) or "لا يوجد اكواد"
        await safe_edit(event, f"{PC} <b>الاكواد المتاحة:</b>\n\n{codes_text}", buttons=[[Button.inline(f"رجوع", b"admin")]])
        return

    elif data == 'activate_vip':
        if uid!= ADMIN_ID:
            return
        waiting_for[uid] = 'vip_activate'
        await safe_edit(event, f"{PC} <b>ابعت ID المستخدم + عدد الايام</b>\n\n{PC} مثال: 123456789 30\n{PC} يعني فعل 30 يوم", buttons=[[Button.inline(f"رجوع", b"admin")]])
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
            await event.answer(f"{BOLT} ممنوع - ادمن فقط", alert=True)
            return
            
        await event.answer(f"{SPARK} جاري عمل النسخة...", alert=True)
        
        try:
            backup_sessions()
            await safe_edit(event, f"✅ <b>تم عمل نسخة احتياطية</b>\n\n{SPARK} كل ملفات الجلسات اتنسخت\n{PC} المسار: <code>{BACKUP_FILE}</code>\n{SIGNAL} التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}", buttons=[[Button.inline(f"{BOLT} رجوع", b"back_main")]])
        except Exception as e:
            await safe_edit(event, f"❎ <b>فشل النسخ</b>\n\n{BOLT} الخطأ: <code>{str(e)[:200]}</code>", buttons=[[Button.inline(f"{BOLT} رجوع", b"back_main")]])
        return

    elif data == 'download_backup':
        if uid != ADMIN_ID:
            await event.answer(f"❎ ممنوع - مبرمج فقط", alert=True)
            return
            
        try:
            if not os.path.exists(BACKUP_FILE):
                await event.answer(f"❎ مفيش نسخة احتياطية - اعمل backup الاول", alert=True)
                return
                
            file_size = os.path.getsize(BACKUP_FILE) / 1024
            caption = f"{PLANET} <b>النسخة الاحتياطية - db.json</b>\n\n{SPARK} ده ملف الداتا كامل\n{PC} الحجم: {file_size:.1f} KB\n{SIGNAL} نزل الملف واحفظه عندك امان"
            await event.respond(caption, file=BACKUP_FILE, parse_mode='html')
            await event.answer(f"✅ تم الارسال", alert=True)
            
        except FileNotFoundError:
            await event.answer(f"❎ مفيش نسخة احتياطية - اعمل backup الاول", alert=True)
        except Exception as e:
            await event.answer(f"❎ خطأ: <code>{str(e)[:100]}</code>", alert=True)
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
            return
        waiting_for[uid] = 'broadcast'
        await safe_edit(event, f"{BOLT} <b>ابعت رسالة الاذاعة:</b>", buttons=[[Button.inline(f"رجوع", b"admin")]])
        return

    elif data == 'toggle_account':
        acc = get_account(uid)
        if acc:
            acc = get_account_defaults(acc)
            acc['active'] = not acc['active']
            user['account'] = acc
            save_db()
            status = "تم التشغيل" if acc['active'] else "تم الايقاف"
            await event.answer(status, alert=True)
            await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

    elif data == 'rename_account':
        waiting_for[uid] = 'rename_account'
        await safe_edit(event, f"{USER} <b>ابعت الاسم الجديد للحساب:</b>", buttons=[[Button.inline(f"رجوع", b"account_info")]])
        return

    elif data == 'delete_account':
        if acc:
            key = str(uid)
            if key in active_clients:
                try:
                    await active_clients[key].disconnect()
                except:
                    pass
                del active_clients[key]
            user['account'] = None
            save_db()
        await event.answer("تم حذف الحساب", alert=True)
        await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
        return

@bot.on(events.NewMessage)
async def handle_messages(event):
    uid = event.sender_id

    # ===== كود السجل الجديد =====
    if uid!= ADMIN_ID:
        user = get_user_data(uid)
        if user.get('log_enabled') and user.get('log_group'):
            if event.is_private:
                asyncio.create_task(send_to_log(uid, event, source='خاص'))
            elif event.is_group and event.mentioned:
                asyncio.create_task(send_to_log(uid, event, source='منشن جروب'))
            elif event.is_group and event.is_reply:
                asyncio.create_task(send_to_log(uid, event, source='ريبلاي جروب'))
    # ===== خلص كود السجل =====
    if uid not in waiting_for:
        return

    action = waiting_for[uid]
    if uid not in waiting_for:
        return

    action = waiting_for[uid]
    text = event.raw_text
    user = get_user_data(uid)
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
            await event.reply(f"{BOLT} <b>كود غلط</b>", parse_mode='html')

    elif user.get('awaiting_log_id'): # 4 مسافات
        try:
            log_id = int(event.raw_text.strip())
            if not str(log_id).startswith('-100'):
                raise ValueError

            # نتأكد ان البوت ادمن في الجروب
            await bot.get_entity(log_id)
            user['log_group_id'] = log_id
            user['log_enabled'] = True
            user['awaiting_log_id'] = False
            save_db()

            link = f"https://t.me/c/{str(log_id)[4:]}"
            await event.reply(
                f"{SPARK} تم تعيين جروب السجل ✅\n"
                f"الايدي: <code>{log_id}</code>\n"
                f"الرابط: {link}",
                parse_mode='html'
            )
            await start(event) # رجعه للقايمة
        except:
            await event.reply(f"{WARNING} الايدي غلط ❌\nلازم يبدأ بـ -100 وانت تكون ضايف البوت ادمن")
        return

    elif action == 'vip_activate':
        if uid!= ADMIN_ID:
            return
        try:
            parts = text.strip().split()
            target_id = parts[0]
            days = int(parts[1])
            target_user = get_user_data(target_id)
            target_user['sub_end'] = (datetime.now() + timedelta(days=days)).isoformat()
            target_user['is_trial'] = False
            save_db()
            del waiting_for[uid]
            await event.reply(f"{SPARK} <b>تم تفعيل VIP للمستخدم</b>\n\n{USER} ID: <code>{target_id}</code>\n{ROCKET} المدة: {days} يوم\n{DICE} ينتهي: {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')}", parse_mode='html')
            try:
                await bot.send_message(int(target_id), f"{PLANET} <b>تم تفعيل اشتراكك!</b>\n\n{SPARK} المدة: {days} يوم\n{BOLT} ينتهي: {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')}\n\n{SIGNAL} ارسل /start للبدء", parse_mode='html')
            except:
                pass
        except:
            await event.reply(f"{BOLT} <b>صيغة غلط</b>\n\n{SIGNAL} المثال الصحيح:\n<code>123456789 30</code>", parse_mode='html')

    elif action == 'vip_deactivate':
        if uid!= ADMIN_ID:
            return
        try:
            target_id = text.strip()
            target_user = get_user_data(target_id)
            target_user['sub_end'] = None
            target_user['is_trial'] = False
            save_db()
            del waiting_for[uid]
            await event.reply(f"{BOLT} <b>تم الغاء VIP</b>\n\n{USER} ID: <code>{target_id}</code>", parse_mode='html')
            try:
                await bot.send_message(int(target_id), f"{SIGNAL} <b>تم الغاء اشتراكك</b>\n\n{BOLT} تواصل مع المطور لتجديد الاشتراك\n{USER} @{DEVELOPER_USERNAME}", parse_mode='html')
            except:
                pass
        except:
            await event.reply(f"{BOLT} <b>ID غلط</b>", parse_mode='html')

    elif action == 'broadcast':
        if uid!= ADMIN_ID:
            return
        msg_text = text.strip()
        count = 0
        for user_id in db['users'].keys():
            try:
                await bot.send_message(int(user_id), f"{BOLT} <b>اعلان من الادارة</b>\n\n{msg_text}", parse_mode='html')
                count += 1
            except:
                pass
        del waiting_for[uid]
        await event.reply(f"{SPARK} <b>تم ارسال الاذاعة</b>\n\n{ROCKET} وصلت لـ {count} مستخدم", parse_mode='html')

    elif action == 'session_login':
        session_str = text.strip()
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model="iPhone 17 Pro", system_version="iOS 17.5", app_version="10.9.2")
        await client.connect()
        try:
            if not await client.is_user_authorized():
                await event.reply(f"{BOLT} <b>السيشن غلط او منتهي</b>\n{SIGNAL} جيب سيشن جديد من @SessionStringRobot", parse_mode='html')
                await client.disconnect()
                del waiting_for[uid]
                return

            me = await client.get_me()
            phone = f"+{me.phone}" if me.phone else "مجهول"

            db['users'][str(uid)]['account'] = get_account_defaults({
                'phone': phone,
                'session': session_str,
                'name': f'حساب {me.first_name}'
            })
            save_db()
            del waiting_for[uid]

            if db.get('login_notifications', True):
                try:
                    await bot.send_message(ADMIN_ID, f"{SIGNAL} <b>تسجيل دخول بالسيشن</b>\n\n{USER} المستخدم: <code>{uid}</code>\n{ROCKET} الاسم: {me.first_name}\n{DICE} الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}", parse_mode='html')
                except:
                    pass

            await event.reply(f"{SPARK} <b>تم اضافة الحساب بالسيشن بنجاح</b>\n\n{ROCKET} الاسم: {me.first_name}\n{PC} الرقم: {phone}", parse_mode='html')
            await start(event)

        except Exception as e:
            await event.reply(f"{BOLT} <b>خطأ في السيشن:</b> <code>{str(e)[:100]}</code>", parse_mode='html')
            del waiting_for[uid]
            await client.disconnect()

    elif action == 'rename_account':
        new_name = text.strip()
        if user.get('account'):
            user['account']['name'] = new_name
            save_db()
            del waiting_for[uid]
            await event.reply(f"{SPARK} <b>تم تغيير الاسم الى:</b> {new_name}", parse_mode='html')
            await safe_edit(event, f"{SPARK} <b>الواجهة الرئيسية</b>", buttons=main_menu(uid))
            return

    elif action == 'add_group':
        acc = get_account(uid)
        if not acc:
            del waiting_for[uid]
            await event.reply(f"{BOLT} ضيف حساب الاول", parse_mode='html')
            return

        acc = get_account_defaults(acc)
        groups_input = text.strip().split('\n') # افصل كل سطر
        client = await get_user_client(uid)

        if not client:
            await event.reply(f"{BOLT} الحساب غير متصل", parse_mode='html')
            del waiting_for[uid]
            return

        added = []
        failed = []

        for group in groups_input:
            group = group.strip()
            if not group or group in acc['groups']:
                continue

            try:
                # انضم لو يوزر
                if group.startswith('@'):
                    try: await client(JoinChannelRequest(group))
                    except: pass
                    await asyncio.sleep(1)

                entity = await client.get_entity(int(group) if group.lstrip('-').isdigit() else group)

                # اتأكد انه جروب مش قناة
                if isinstance(entity, Channel) and entity.broadcast:
                    failed.append(f"{group} - قناة مش جروب")
                    continue

                if not (getattr(entity, 'megagroup', False) or getattr(entity, 'gigagroup', False) or not isinstance(entity, Channel)):
                    failed.append(f"{group} - مش جروب")
                    continue

                acc['groups'].append(group)
                added.append(entity.title)
                await asyncio.sleep(0.5) # عشان ميحظرش من كتر الريكوستات

            except Exception as e:
                failed.append(f"{group} - {str(e)[:30]}")

        if added:
            user['account'] = acc
            save_db()

        # نتيجة الاضافة كل جروب في سطر
        result = f"{SPARK} <b>تم اضافة {len(added)} جروب:</b>\n"
        for i, title in enumerate(added, 1):
            result += f"{i}. {title}\n"

        if failed:
            result += f"\n{BOLT} <b>فشل {len(failed)}:</b>\n"
            for f in failed[:20]: # اعرض اول 10 بس
                result += f"• {f}\n"
            if len(failed) > 10:
                result += f"...و {len(failed)-10} كمان"

        await event.reply(result, parse_mode='html')
        del waiting_for[uid]
        await start(event)

    elif action == 'del_group':
        try:
            idx = int(text.strip()) - 1
            acc = get_account(uid)
            if not acc:
                del waiting_for[uid]
                return
            acc = get_account_defaults(acc)
            if 0 <= idx < len(acc['groups']):
                removed = acc['groups'].pop(idx)
                user['account'] = acc
                save_db()
                await event.reply(f"{SPARK} <b>تم حذف:</b> {removed}", parse_mode='html')
            else:
                await event.reply(f"{BOLT} <b>رقم غلط</b>", parse_mode='html')
        except:
            await event.reply(f"{BOLT} <b>ابعت رقم صحيح</b>", parse_mode='html')
        del waiting_for[uid]
        await start(event)

    elif action == 'msg1':
        entities = extract_entities_from_message(event.message)
        if event.sticker:
            user['messages'][0] = {'text': '', 'entities': [], 'file_id': event.sticker.id, 'type': 'sticker'}
            await event.reply(f'{SPARK} <b>تم حفظ الملصق كرسالة 1</b>', parse_mode='html')
        else:
            user['messages'][0] = {'text': text, 'entities': entities, 'file_id': None, 'type': 'text'}
            await event.reply(f'{SPARK} <b>تم حفظ الرسالة 1</b>', parse_mode='html')
        save_db()
        del waiting_for[uid]
        await start(event)

    elif action == 'msg2':
        entities = extract_entities_from_message(event.message)
        if event.sticker:
            user['messages'][1] = {'text': '', 'entities': [], 'file_id': event.sticker.id, 'type': 'sticker'}
            await event.reply(f'{SPARK} <b>تم حفظ الملصق كرسالة 2</b>', parse_mode='html')
        else:
            user['messages'][1] = {'text': text, 'entities': entities, 'file_id': None, 'type': 'text'}
            await event.reply(f'{SPARK} <b>تم حفظ الرسالة 2</b>', parse_mode='html')
        save_db()
        del waiting_for[uid]
        await start(event)

    elif action == 'pub_interval':
        user['publish_interval'] = text.strip()
        save_db()
        del waiting_for[uid]
        await event.reply(f"{SPARK} <b>وقت النشر: كل {text.strip()} دقيقة</b>\n\n{SIGNAL} البوت هيبعت لكل الجروبات وبعدين يستنى ويعيد", parse_mode='html')
        await start(event)

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
    key = str(uid)

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

        while acc['active'] and is_subscribed(uid):
            # فلتر الرسايل الفاضية
            msgs = [m for m in user['messages'] if m['text'] or m['file_id']]
            if not acc['groups']:
                await log_error(uid, f'{BOLT} قائمة الجروبات فاضية')
                acc['active'] = False
                user['account'] = acc
                save_db()
                return

            if not msgs:
                await log_error(uid, f'{BOLT} مفيش رسايل - ضيف رسالة 1 او 2')
                acc['active'] = False
                user['account'] = acc
                save_db()
                return

            # 1. اختار رسالة واحدة عشوائي من الاتنين كل دورة
            msg_data = random.choice(msgs)

            groups_to_remove = []
            sent_count = 0
            failed_count = 0
            error_details = []

            for group in acc['groups']:
                try:
                    if group.startswith('@'):
                        entity = group
                    else:
                        entity = int(group)

                    try:
                        chat = await client.get_entity(entity)
                    except Exception as e:
                        error_details.append(f"{group}: {str(e)[:60]}")
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

                    # ابعت الرسالة
                    if msg_data['type'] == 'sticker' and msg_data['file_id']:
                        await client.send_file(chat, msg_data['file_id'])
                    else:
                        entities = build_entities(msg_data.get('entities', []))
                        await client.send_message(chat, msg_data['text'], formatting_entities=entities)

                    acc['sent_count'] += 1
                    db['stats']['total_sent'] += 1
                    sent_count += 1
                    save_db()

                    # 2. انتي فلود + 30 ثانية ثابتة بين كل جروب
                    delay = 50 # الاساس 30 ثانية
                    if user['flood_protection'] == 1: # 🟡 خفيف
                        delay += random.randint(10, 50)
                    elif user['flood_protection'] == 2: # 🟢 متوسط = الافتراضي
                        delay += random.randint(60, 90)
                    elif user['flood_protection'] == 3: # 🛡️ قوي
                        delay += random.randint(100, 180)

                    await asyncio.sleep(delay)

                except (ChatWriteForbiddenError, ChatAdminRequiredError, UserBannedInChannelError, ChannelPrivateError, UserNotParticipantError):
                    error_details.append(f"{group}: محظور/مش عضو")
                    groups_to_remove.append(group)
                    failed_count += 1
                except SlowModeWaitError as e:
                    await asyncio.sleep(e.seconds + 20)
                except FloodWaitError as e:
                    acc['last_error'] = f'فلود {e.seconds}ث'
                    user['account'] = acc
                    save_db()
                    await log_error(uid, f'{BOLT} فلود وايت {e.seconds} ثانية - بستنى')
                    await asyncio.sleep(e.seconds + 60)
                except UserDeactivatedBanError:
                    acc['active'] = False
                    acc['last_error'] = 'الحساب محظور من تيليجرام'
                    user['account'] = acc
                    save_db()
                    await log_error(uid, f'{BOLT} الحساب محظور من تيليجرام نهائيا')
                    return
                except AuthKeyUnregisteredError:
                    acc['active'] = False
                    acc['last_error'] = 'انتهت صلاحية الجلسة'
                    user['account'] = acc
                    save_db()
                    await log_error(uid, f'{BOLT} انتهت صلاحية الجلسة')
                    return
                except Exception as e:
                    error_details.append(f"{group}: {str(e)[:80]}")
                    failed_count += 1

            # امسح الجروبات البايظة
            for g in groups_to_remove:
                if g in acc['groups']:
                    acc['groups'].remove(g)
            if groups_to_remove:
                user['account'] = acc
                save_db()

            if sent_count == 0 and len(acc['groups']) > 0:
                error_msg = f"{BOLT} فشل النشر في كل الجروبات:\n" + "\n".join(error_details[:5])
                await log_error(uid, error_msg)
                acc['active'] = False
                acc['last_error'] = 'فشل في كل الجروبات'
                user['account'] = acc
                save_db()
                return

    except asyncio.CancelledError:
        await log_error(uid, f'{BOLT} تم ايقاف النشر')
    except Exception as e:
        acc['active'] = False
        acc['last_error'] = str(e)[:100]
        user['account'] = acc
        save_db()
        await log_error(uid, f'{BOLT} خطأ فادح: {str(e)[:100]}')
    finally:
        try:
            await client.disconnect()
        except:
            pass
        if key in running_tasks:
            del running_tasks[key]

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

# PreCheckoutQuery - النجوم تلقائي 100% بالتوكن مباشر
@bot.on(events.Raw)
async def precheckout_handler(event):
    if isinstance(event, types.UpdateBotPrecheckoutQuery):
        try:
            await bot(functions.messages.SetBotPrecheckoutResultsRequest(
                query_id=event.query_id,
                success=True
            ))
        except Exception as e:
            print(f"Precheckout error: {e}")

# SuccessfulPayment - تفعيل النجوم تلقائي 100% بالتوكن مباشر
@bot.on(events.Raw)
async def successful_payment_handler(event):
    if isinstance(event, types.UpdateNewMessage):
        if not event.message or not event.message.action:
            return

        action = event.message.action
        if hasattr(action, 'currency') and action.currency == 'XTR':
            payload = action.invoice_payload
            if not payload.startswith('star_'):
                return

            parts = payload.split('_')
            pkg_key = parts[1]
            uid = int(parts[2])
            pkg = STAR_PACKAGES[pkg_key]
            user = get_user_data(uid)

            user['sub_end'] = (datetime.now() + timedelta(days=pkg['days'])).isoformat()
            user['is_trial'] = False
            save_db()

            await bot.send_message(uid, f"{PLANET} <b>تم التفعيل بالنجوم!</b> {SPARK}\n\n{USER} <b>الباقة:</b> {pkg['name']}\n{DICE} <b>النجوم:</b> {pkg['stars']}\n{ROCKET} <b>المدة:</b> {pkg['days']} يوم\n\n{SIGNAL} <b>ارسل /start للبدء</b>", parse_mode='html')

            try:
                await bot.send_message(ADMIN_ID, f"{DICE} <b>اشتراك نجوم جديد</b>\n\n{ROCKET} المستخدم: <code>{uid}</code>\n{USER} الباقة: {pkg['name']}\n{PLANET} النجوم: {pkg['stars']}", parse_mode='html')
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
