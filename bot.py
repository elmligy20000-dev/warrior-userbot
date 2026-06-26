import asyncio
import random
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types
from telethon.tl.custom import Button
from telethon.sessions import StringSession
import sqlite3
import os
import re
import sys
from typing import List, Dict, Optional

# Premium Emojis with tg-emoji format
PREMIUM_EMOJIS = [
    '<tg-emoji emoji-id="5886664420502805908">💻</tg-emoji>',
    '<tg-emoji emoji-id="5886716969427672960">🎲</tg-emoji>',
    '<tg-emoji emoji-id="5886462183377739675">🌿</tg-emoji>',
    '<tg-emoji emoji-id="5886695331382435915">👤</tg-emoji>',
    '<tg-emoji emoji-id="5886449487454416104">🪐</tg-emoji>',
    '<tg-emoji emoji-id="5884250988184870485">🔅</tg-emoji>',
    '<tg-emoji emoji-id="5886360482847137476">⚡️</tg-emoji>',
    '<tg-emoji emoji-id="5886232789174460116">🎸</tg-emoji>',
    '<tg-emoji emoji-id="5886408161279090563">🕊</tg-emoji>',
    '<tg-emoji emoji-id="5886505777295793908">⚪️</tg-emoji>',
    '<tg-emoji emoji-id="5886242543045189717">🦋</tg-emoji>',
    '<tg-emoji emoji-id="5884015001206791984">✨</tg-emoji>',
    '<tg-emoji emoji-id="5886672924538051950">⚡️</tg-emoji>'
]

# Configuration
API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8914045842:AAEz6MNsGTShwob_M3H0ECy8eOkl2nT5gno"
ADMIN_ID = 932862531
ADMIN_USERNAME = 'Programmer_error'  # Replace with your admin username
DEVELOPER_USERNAMES = ['Programmer_error', 'BRXLI']  # Add developer usernames here
DB_NAME = 'auto_poster.db'

# Initialize logging
logging.basicConfig(
    format='<b>[%(levelname) 5s/%(asctime)s]</b> <b>%(name)s:</b> <b>%(message)s</b>',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_vip BOOLEAN DEFAULT FALSE,
        vip_expiry DATETIME,
        is_banned BOOLEAN DEFAULT FALSE,
        activation_code TEXT,
        is_developer BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Groups table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY,
        group_name TEXT,
        group_username TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        is_banned BOOLEAN DEFAULT FALSE,
        last_post_time DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        added_by INTEGER
    )
    ''')

    # VIP Codes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vip_codes (
        code TEXT PRIMARY KEY,
        duration_days INTEGER,
        is_used BOOLEAN DEFAULT FALSE,
        used_by INTEGER,
        used_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Activation codes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activation_codes (
        code TEXT PRIMARY KEY,
        is_used BOOLEAN DEFAULT FALSE,
        used_by INTEGER,
        used_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        font TEXT,
        is_premium BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        added_by INTEGER
    )
    ''')

    # Flood protection table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flood_protection (
        group_id INTEGER PRIMARY KEY,
        last_message_time DATETIME,
        message_count INTEGER DEFAULT 0,
        cooldown_until DATETIME
    )
    ''')

    # Bot settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT
    )
    ''')

    # Insert default settings if not exists
    cursor.execute('''
    INSERT OR IGNORE INTO bot_settings (setting_key, setting_value)
    VALUES ('min_post_delay', '300'), ('max_post_delay', '500')
    ''')

    conn.commit()
    conn.close()

init_db()

# Client setup
client = TelegramClient('auto_poster', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Helper functions
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def add_premium_emojis_to_text(text: str) -> str:
    emoji = random.choice(PREMIUM_EMOJIS)
    lines = text.split('\n')
    decorated_lines = []
    for line in lines:
        if line.strip():
            decorated_lines.append(f"{emoji} {line.strip()} {emoji}")
    return '\n'.join(decorated_lines)

def format_text_with_font(text: str, font: str = None) -> str:
    if not font:
        fonts = [
            "monospace", "sans-serif", "serif", "small", "large",
            "𝗠𝗢𝗡𝗢𝗦𝗣𝗔𝗖𝗘", "𝖬𝖮𝖭𝖮𝖲𝖯𝖠𝖢𝖤", "𝕄𝕆ℕ𝕆𝕊ℙ𝔸ℂ𝔼",
            "𝓜𝓞𝓝𝓞𝓢𝓟𝓐𝓒𝓔", "𝒎𝒐𝒏𝒐𝒔𝒑𝒂𝒄𝒆", "𝐌𝐎𝐍𝐎𝐒𝐏𝐀𝐂𝐄"
        ]
        font = random.choice(fonts)

    if font.lower() == "monospace":
        return f"<code>{text}</code>"
    elif font.lower() == "sans-serif":
        return f"<b>𝗧𝗘𝗫𝗧: {text}</b>"
    elif font.lower() == "serif":
        return f"<b>𝖳𝖤𝖸𝖳: {text}</b>"
    elif font == "small":
        return f"<small>{text}</small>"
    elif font == "large":
        return f"<large>{text}</large>"
    else:
        return f"<b>{text}</b>"

async def check_group_status(group_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_banned FROM groups WHERE group_id = ?', (group_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result['is_banned']:
        return False

    try:
        chat = await client.get_entity(group_id)
        if isinstance(chat, types.ChatForbidden):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE groups SET is_banned = 1 WHERE group_id = ?', (group_id,))
            conn.commit()
            conn.close()
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking group {group_id}: {e}")
        return False

async def get_post_delay() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT setting_value FROM bot_settings WHERE setting_key = ?', ('min_post_delay',))
    min_delay = int(cursor.fetchone()['setting_value'])
    cursor.execute('SELECT setting_value FROM bot_settings WHERE setting_key = ?', ('max_post_delay',))
    max_delay = int(cursor.fetchone()['setting_value'])
    conn.close()
    return random.randint(min_delay, max_delay)

async def check_flood_protection(group_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT last_message_time, message_count, cooldown_until
    FROM flood_protection
    WHERE group_id = ?
    ''', (group_id,))

    result = cursor.fetchone()

    now = datetime.now()

    if result:
        last_time = datetime.strptime(result['last_message_time'], '%Y-%m-%d %H:%M:%S') if result['last_message_time'] else None
        cooldown_until = datetime.strptime(result['cooldown_until'], '%Y-%m-%d %H:%M:%S') if result['cooldown_until'] else None

        if cooldown_until and now < cooldown_until:
            conn.close()
            return False

        if last_time and (now - last_time) < timedelta(minutes=1):
            message_count = result['message_count'] + 1
            if message_count >= 5:
                cooldown_until = now + timedelta(minutes=5)
                cursor.execute('''
                UPDATE flood_protection
                SET message_count = ?, cooldown_until = ?
                WHERE group_id = ?
                ''', (message_count, cooldown_until.strftime('%Y-%m-%d %H:%M:%S'), group_id))
                conn.commit()
                conn.close()
                return False
            else:
                cursor.execute('''
                UPDATE flood_protection
                SET last_message_time = ?, message_count = ?
                WHERE group_id = ?
                ''', (now.strftime('%Y-%m-%d %H:%M:%S'), message_count, group_id))
                conn.commit()
        else:
            cursor.execute('''
            UPDATE flood_protection
            SET last_message_time = ?, message_count = 1
            WHERE group_id = ?
            ''', (now.strftime('%Y-%m-%d %H:%M:%S'), group_id))
            conn.commit()
    else:
        cursor.execute('''
        INSERT INTO flood_protection (group_id, last_message_time, message_count)
        VALUES (?, ?, 1)
        ''', (group_id, now.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

    conn.close()
    return True

async def get_active_groups() -> List[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT group_id FROM groups WHERE is_active = 1 AND is_banned = 0')
    groups = [row['group_id'] for row in cursor.fetchall()]
    conn.close()
    return groups

async def get_premium_messages() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT text FROM messages WHERE is_premium = 1')
    messages = [row['text'] for row in cursor.fetchall()]
    conn.close()
    return messages

async def get_regular_messages() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT text FROM messages WHERE is_premium = 0')
    messages = [row['text'] for row in cursor.fetchall()]
    conn.close()
    return messages

async def add_group(group_id: int, group_name: str, group_username: str = None, added_by: int = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO groups (group_id, group_name, group_username, added_by)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(group_id) DO UPDATE SET
        group_name = excluded.group_name,
        group_username = excluded.group_username,
        is_active = 1,
        is_banned = 0,
        added_by = excluded.added_by
        ''', (group_id, group_name, group_username, added_by))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding group: {e}")
        return False
    finally:
        conn.close()

async def remove_group(group_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('UPDATE groups SET is_active = 0 WHERE group_id = ?', (group_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error removing group: {e}")
        return False
    finally:
        conn.close()

async def ban_group(group_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('UPDATE groups SET is_banned = 1 WHERE group_id = ?', (group_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error banning group: {e}")
        return False
    finally:
        conn.close()

async def add_message(text: str, is_premium: bool = False, font: str = None, added_by: int = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        formatted_text = format_text_with_font(text, font)
        cursor.execute('''
        INSERT INTO messages (text, font, is_premium, added_by)
        VALUES (?, ?, ?, ?)
        ''', (formatted_text, font, is_premium, added_by))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        return False
    finally:
        conn.close()

async def generate_vip_code(duration_days: int) -> str:
    import secrets
    code = secrets.token_hex(8).upper()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO vip_codes (code, duration_days)
        VALUES (?, ?)
        ''', (code, duration_days))
        conn.commit()
        return code
    except Exception as e:
        logger.error(f"Error generating VIP code: {e}")
        return None
    finally:
        conn.close()

async def generate_activation_code() -> str:
    import secrets
    code = secrets.token_hex(6).upper()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO activation_codes (code)
        VALUES (?)
        ''', (code,))
        conn.commit()
        return code
    except Exception as e:
        logger.error(f"Error generating activation code: {e}")
        return None
    finally:
        conn.close()

async def redeem_activation_code(user_id: int, code: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM activation_codes WHERE code = ? AND is_used = 0', (code,))
        activation_code = cursor.fetchone()

        if not activation_code:
            return False

        cursor.execute('''
        UPDATE users
        SET activation_code = ?
        WHERE user_id = ?
        ''', (code, user_id))

        cursor.execute('''
        UPDATE activation_codes
        SET is_used = 1, used_by = ?, used_at = ?
        WHERE code = ?
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code))

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error redeeming activation code: {e}")
        return False
    finally:
        conn.close()

async def redeem_vip_code(user_id: int, code: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM vip_codes WHERE code = ? AND is_used = 0', (code,))
        vip_code = cursor.fetchone()

        if not vip_code:
            return False

        expiry_date = datetime.now() + timedelta(days=vip_code['duration_days'])

        cursor.execute('''
        UPDATE users
        SET is_vip = 1, vip_expiry = ?
        WHERE user_id = ?
        ''', (expiry_date.strftime('%Y-%m-%d %H:%M:%S'), user_id))

        cursor.execute('''
        UPDATE vip_codes
        SET is_used = 1, used_by = ?, used_at = ?
        WHERE code = ?
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code))

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error redeeming VIP code: {e}")
        return False
    finally:
        conn.close()

async def is_user_vip(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT is_vip, vip_expiry FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()

        if not result:
            return False

        if not result['is_vip']:
            return False

        if result['vip_expiry']:
            expiry_date = datetime.strptime(result['vip_expiry'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > expiry_date:
                cursor.execute('''
                UPDATE users SET is_vip = 0 WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                return False

        return True
    except Exception as e:
        logger.error(f"Error checking VIP status: {e}")
        return False
    finally:
        conn.close()

async def is_user_activated(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT activation_code FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()

        if not result or not result['activation_code']:
            return False

        return True
    except Exception as e:
        logger.error(f"Error checking activation status: {e}")
        return False
    finally:
        conn.close()

async def is_user_developer(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT is_developer FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()

        if not result:
            return False

        return result['is_developer']
    except Exception as e:
        logger.error(f"Error checking developer status: {e}")
        return False
    finally:
        conn.close()

async def add_developer(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE users
        SET is_developer = 1
        WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding developer: {e}")
        return False
    finally:
        conn.close()

async def remove_developer(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE users
        SET is_developer = 0
        WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error removing developer: {e}")
        return False
    finally:
        conn.close()

async def update_bot_setting(key: str, value: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT OR REPLACE INTO bot_settings (setting_key, setting_value)
        VALUES (?, ?)
        ''', (key, value))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating bot setting: {e}")
        return False
    finally:
        conn.close()

async def get_bot_setting(key: str) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT setting_value FROM bot_settings WHERE setting_key = ?', (key,))
        result = cursor.fetchone()
        return result['setting_value'] if result else None
    except Exception as e:
        logger.error(f"Error getting bot setting: {e}")
        return None
    finally:
        conn.close()

# Auto poster main function
async def auto_poster():
    while True:
        try:
            groups = await get_active_groups()
            premium_messages = await get_premium_messages()
            regular_messages = await get_regular_messages()

            if not groups or (not premium_messages and not regular_messages):
                await asyncio.sleep(60)
                continue

            for group_id in groups:
                try:
                    if not await check_group_status(group_id):
                        await ban_group(group_id)
                        continue

                    if not await check_flood_protection(group_id):
                        continue

                    messages_to_send = premium_messages if random.random() < 0.3 else regular_messages
                    if not messages_to_send:
                        messages_to_send = premium_messages if premium_messages else regular_messages

                    message = random.choice(messages_to_send)
                    formatted_message = add_premium_emojis_to_text(message)

                    try:
                        await client.send_message(group_id, formatted_message, parse_mode='html')
                        logger.info(f"Posted to group {group_id}: {formatted_message[:50]}...")
                    except Exception as e:
                        logger.error(f"Error posting to group {group_id}: {e}")
                        if "CHAT_WRITE_FORBIDDEN" in str(e) or "CHAT_ADMIN_REQUIRED" in str(e):
                            await ban_group(group_id)

                    delay = await get_post_delay()
                    await asyncio.sleep(delay)
                except Exception as e:
                    logger.error(f"Error in group {group_id} loop: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in auto_poster main loop: {e}")
            await asyncio.sleep(60)

# Admin panel
@client.on(events.NewMessage(pattern='/start', from_users=lambda u: u.username == ADMIN_USERNAME))
async def admin_activation(event):
    await event.respond(
        add_premium_emojis_to_text("<b>🔑 مرحبا بك في بوت النشر المتطور!</b>\n\n<b>يرجى إرسال كود التفعيل للدخول إلى لوحة التحكم:</b>")
    )

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_activation_code(new_event):
        code = new_event.text.strip()
        if code == "ADMIN123":  # Replace with your actual admin activation code
            await admin_panel(new_event)
        else:
            await new_event.reply(add_premium_emojis_to_text("<b>❌ كود التفعيل غير صحيح!</b>"))
        client.remove_event_handler(handle_activation_code)

async def admin_panel(event):
    buttons = [
        [Button.inline("الإحصائيات", b'stats')],
        [Button.inline("إدارة المجموعات", b'manage_groups')],
        [Button.inline("إدارة الرسائل", b'manage_messages')],
        [Button.inline("إدارة VIP", b'manage_vip')],
        [Button.inline("إدارة أكواد التفعيل", b'manage_activation_codes')],
        [Button.inline("الإذاعة", b'broadcast')],
        [Button.inline("إعدادات البوت", b'bot_settings')],
        [Button.inline("أدوات المطور", b'developer_tools')],
        [Button.inline("تحكم المطور", b'developer_control')]
    ]

    await event.respond(
        add_premium_emojis_to_text("<b>🎛 لوحة التحكم الإدارية</b>\n\n<b>مرحبًا بك في لوحة التحكم الإدارية للبوت المتطور للنشر التلقائي.</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'stats'))
async def show_stats(event):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM users')
    users_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM groups WHERE is_active = 1')
    active_groups_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM groups WHERE is_banned = 1')
    banned_groups_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM messages')
    messages_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM vip_codes WHERE is_used = 0')
    unused_vip_codes = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_vip = 1')
    vip_users_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM activation_codes WHERE is_used = 0')
    unused_activation_codes = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_developer = 1')
    developers_count = cursor.fetchone()['count']

    conn.close()

    stats_text = (
        "<b>📊 إحصائيات البوت</b>\n\n"
        f"<b>👥 المستخدمين:</b> <code>{users_count}</code>\n"
        f"<b>🏢 المجموعات النشطة:</b> <code>{active_groups_count}</code>\n"
        f"<b>🚫 المجموعات المحظورة:</b> <code>{banned_groups_count}</code>\n"
        f"<b>💬 الرسائل المخزنة:</b> <code>{messages_count}</code>\n"
        f"<b>🎟 أكواد VIP غير مستخدمة:</b> <code>{unused_vip_codes}</code>\n"
        f"<b>👑 مستخدمي VIP:</b> <code>{vip_users_count}</code>\n"
        f"<b>🔑 أكواد التفعيل غير مستخدمة:</b> <code>{unused_activation_codes}</code>\n"
        f"<b>🛠 المطورين:</b> <code>{developers_count}</code>"
    )

    buttons = [
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(add_premium_emojis_to_text(stats_text), buttons=buttons)

@client.on(events.CallbackQuery(data=b'manage_groups'))
async def manage_groups(event):
    buttons = [
        [Button.inline("إضافة مجموعة", b'add_group')],
        [Button.inline("إزالة مجموعة", b'remove_group')],
        [Button.inline("حظر مجموعة", b'ban_group')],
        [Button.inline("قائمة المجموعات", b'list_groups')],
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>🏢 إدارة المجموعات</b>\n\n<b>اختر الإجراء الذي تريد القيام به:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_group'))
async def add_group_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>📥 إضافة مجموعة</b>\n\n<b>أرسل معرف أو رابط المجموعة التي تريد إضافتها:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_group_add(new_event):
        text = new_event.text
        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
                group_name = group.title
                group_username = group.username
            else:
                group_id = int(text)
                group = await client.get_entity(group_id)
                group_name = group.title
                group_username = group.username

            if await add_group(group_id, group_name, group_username):
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إضافة المجموعة {group_name} ({group_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إضافة المجموعة.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await admin_panel(new_event)
        client.remove_event_handler(handle_group_add)

@client.on(events.CallbackQuery(data=b'remove_group'))
async def remove_group_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>📤 إزالة مجموعة</b>\n\n<b>أرسل معرف أو رابط المجموعة التي تريد إزالتها:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_group_remove(new_event):
        text = new_event.text
        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
            else:
                group_id = int(text)

            if await remove_group(group_id):
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إزالة المجموعة ({group_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إزالة المجموعة.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await admin_panel(new_event)
        client.remove_event_handler(handle_group_remove)

@client.on(events.CallbackQuery(data=b'ban_group'))
async def ban_group_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>🚫 حظر مجموعة</b>\n\n<b>أرسل معرف أو رابط المجموعة التي تريد حظرها:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_group_ban(new_event):
        text = new_event.text
        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
            else:
                group_id = int(text)

            if await ban_group(group_id):
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم حظر المجموعة ({group_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل حظر المجموعة.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await admin_panel(new_event)
        client.remove_event_handler(handle_group_ban)

@client.on(events.CallbackQuery(data=b'list_groups'))
async def list_groups(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT group_id, group_name, group_username FROM groups WHERE is_active = 1')
    groups = cursor.fetchall()
    conn.close()

    if not groups:
        await event.edit(add_premium_emojis_to_text("<b>❌ لا توجد مجموعات نشطة حاليًا.</b>"))
        return

    groups_text = "<b>📋 قائمة المجموعات النشطة</b>\n\n"
    for group in groups:
        groups_text += f"<b>🏢 {group['group_name']} ({group['group_id']})</b>\n"
        if group['group_username']:
            groups_text += f"<b>🔗 @{group['group_username']}</b>\n"
        groups_text += "\n"

    buttons = [
        [Button.inline("رجوع", b'manage_groups')]
    ]

    await event.edit(add_premium_emojis_to_text(groups_text), buttons=buttons)

@client.on(events.CallbackQuery(data=b'manage_messages'))
async def manage_messages(event):
    buttons = [
        [Button.inline("إضافة رسالة عادية", b'add_regular_message')],
        [Button.inline("إضافة رسالة بريميوم", b'add_premium_message')],
        [Button.inline("قائمة الرسائل", b'list_messages')],
        [Button.inline("حذف رسالة", b'delete_message')],
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>💬 إدارة الرسائل</b>\n\n<b>اختر الإجراء الذي تريد القيام به:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_regular_message'))
async def add_regular_message_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>➕ إضافة رسالة عادية</b>\n\n<b>أرسل الرسالة التي تريد إضافتها:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_regular_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=False, added_by=new_event.sender_id):
            await new_event.reply(add_premium_emojis_to_text("<b>✅ تم إضافة الرسالة بنجاح!</b>"))
        else:
            await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إضافة الرسالة.</b>"))

        await manage_messages(new_event)
        client.remove_event_handler(handle_regular_message)

@client.on(events.CallbackQuery(data=b'add_premium_message'))
async def add_premium_message_prompt(event):
    buttons = [
        [Button.inline("خط عادي", b'font_normal')],
        [Button.inline("خط مونوسبيس", b'font_monospace')],
        [Button.inline("خط سانز سيريف", b'font_sans')],
        [Button.inline("خط سيريف", b'font_serif')],
        [Button.inline("خط صغير", b'font_small')],
        [Button.inline("خط كبير", b'font_large')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>➕ إضافة رسالة بريميوم</b>\n\n<b>اختر نوع الخط للرسالة:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=re.compile(b'font_(.*)')))
async def handle_font_selection(event):
    font = event.data_match.group(1).decode('utf-8')
    await event.edit(add_premium_emojis_to_text(f"<b>➕ إضافة رسالة بريميوم</b>\n\n<b>أرسل الرسالة التي تريد إضافتها بخط {font}:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_premium_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=True, font=font, added_by=new_event.sender_id):
            await new_event.reply(add_premium_emojis_to_text("<b>✅ تم إضافة الرسالة البريميوم بنجاح!</b>"))
        else:
            await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إضافة الرسالة.</b>"))

        await manage_messages(new_event)
        client.remove_event_handler(handle_premium_message)

@client.on(events.CallbackQuery(data=b'list_messages'))
async def list_messages(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, text, is_premium FROM messages')
    messages = cursor.fetchall()
    conn.close()

    if not messages:
        await event.edit(add_premium_emojis_to_text("<b>❌ لا توجد رسائل مخزنة حاليًا.</b>"))
        return

    messages_text = "<b>📋 قائمة الرسائل</b>\n\n"
    for msg in messages:
        premium = "👑" if msg['is_premium'] else "📝"
        messages_text += f"<b>{premium} ({msg['id']}) {msg['text'][:50]}...</b>\n\n"

    buttons = [
        [Button.inline("رجوع", b'manage_messages')]
    ]

    await event.edit(add_premium_emojis_to_text(messages_text), buttons=buttons)

@client.on(events.CallbackQuery(data=b'delete_message'))
async def delete_message_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>🗑 حذف رسالة</b>\n\n<b>أرسل معرف الرسالة التي تريد حذفها:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_message_delete(new_event):
        try:
            message_id = int(new_event.text)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM messages WHERE id = ?', (message_id,))
            conn.commit()
            conn.close()

            if cursor.rowcount > 0:
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم حذف الرسالة ({message_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ الرسالة غير موجودة.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await manage_messages(new_event)
        client.remove_event_handler(handle_message_delete)

@client.on(events.CallbackQuery(data=b'manage_vip'))
async def manage_vip(event):
    buttons = [
        [Button.inline("توليد كود VIP", b'generate_vip_code')],
        [Button.inline("قائمة مستخدمي VIP", b'list_vip_users')],
        [Button.inline("حذف مستخدم VIP", b'remove_vip_user')],
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>👑 إدارة VIP</b>\n\n<b>اختر الإجراء الذي تريد القيام به:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'generate_vip_code'))
async def generate_vip_code_prompt(event):
    buttons = [
        [Button.inline("7 أيام", b'vip_7_days')],
        [Button.inline("30 يوم", b'vip_30_days')],
        [Button.inline("90 يوم", b'vip_90_days')],
        [Button.inline("365 يوم", b'vip_365_days')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>🎟 توليد كود VIP</b>\n\n<b>اختر مدة الكود:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=re.compile(br'vip_(\d+)_days')))
async def handle_vip_code_generation(event):
    duration = int(event.data_match.group(1).decode('utf-8'))
    code = await generate_vip_code(duration)

    if code:
        await event.edit(
            add_premium_emojis_to_text(
                f"<b>✅ تم توليد كود VIP</b>\n\n"
                f"<b>الكود:</b> <code>{code}</code>\n"
                f"<b>المدة:</b> {duration} أيام\n\n"
                "<b>يمكنك الآن إرسال هذا الكود للمستخدمين لتفعيل VIP.</b>"
            )
        )
    else:
        await event.edit(add_premium_emojis_to_text("<b>❌ فشل توليد الكود.</b>"))

@client.on(events.CallbackQuery(data=b'list_vip_users'))
async def list_vip_users(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT user_id, first_name, last_name, username, vip_expiry
    FROM users
    WHERE is_vip = 1
    ''')
    users = cursor.fetchall()
    conn.close()

    if not users:
        await event.edit(add_premium_emojis_to_text("<b>❌ لا يوجد مستخدمي VIP حاليًا.</b>"))
        return

    users_text = "<b>👑 قائمة مستخدمي VIP</b>\n\n"
    for user in users:
        name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip()
        if not name:
            name = user['username'] or "مستخدم غير معروف"
        expiry = datetime.strptime(user['vip_expiry'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        users_text += f"<b>👤 {name} ({user['user_id']})</b>\n<b>📅 انتهاء VIP:</b> {expiry}\n\n"

    buttons = [
        [Button.inline("رجوع", b'manage_vip')]
    ]

    await event.edit(add_premium_emojis_to_text(users_text), buttons=buttons)

@client.on(events.CallbackQuery(data=b'remove_vip_user'))
async def remove_vip_user_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>👑 حذف مستخدم VIP</b>\n\n<b>أرسل معرف المستخدم الذي تريد إزالة VIP منه:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_vip_remove(new_event):
        try:
            user_id = int(new_event.text)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_vip = 0, vip_expiry = NULL WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()

            if cursor.rowcount > 0:
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إزالة VIP من المستخدم ({user_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ المستخدم غير موجود أو ليس لديه VIP.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await manage_vip(new_event)
        client.remove_event_handler(handle_vip_remove)

@client.on(events.CallbackQuery(data=b'manage_activation_codes'))
async def manage_activation_codes(event):
    buttons = [
        [Button.inline("توليد كود تفعيل", b'generate_activation_code')],
        [Button.inline("قائمة أكواد التفعيل", b'list_activation_codes')],
        [Button.inline("حذف كود تفعيل", b'delete_activation_code')],
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>🎟 إدارة أكواد التفعيل</b>\n\n<b>اختر الإجراء الذي تريد القيام به:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'generate_activation_code'))
async def generate_activation_code_prompt(event):
    code = await generate_activation_code()

    if code:
        await event.edit(
            add_premium_emojis_to_text(
                f"<b>✅ تم توليد كود التفعيل</b>\n\n"
                f"<b>الكود:</b> <code>{code}</code>\n\n"
                "<b>يمكنك الآن إرسال هذا الكود للمستخدمين لتفعيل البوت.</b>"
            )
        )
    else:
        await event.edit(add_premium_emojis_to_text("<b>❌ فشل توليد الكود.</b>"))

@client.on(events.CallbackQuery(data=b'list_activation_codes'))
async def list_activation_codes(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT code, is_used, used_by, used_at
    FROM activation_codes
    ORDER BY created_at DESC
    ''')
    codes = cursor.fetchall()
    conn.close()

    if not codes:
        await event.edit(add_premium_emojis_to_text("<b>❌ لا توجد أكواد تفعيل حاليًا.</b>"))
        return

    codes_text = "<b>🔑 قائمة أكواد التفعيل</b>\n\n"
    for code in codes:
        status = "✅ غير مستخدم" if not code['is_used'] else f"❌ مستخدم بواسطة {code['used_by']}"
        used_at = code['used_at'] if code['used_at'] else "لم يستخدم بعد"
        codes_text += f"<b>🎟 الكود:</b> <code>{code['code']}</code>\n<b>📝 الحالة:</b> {status}\n<b>📅 تاريخ الاستخدام:</b> {used_at}\n\n"

    buttons = [
        [Button.inline("رجوع", b'manage_activation_codes')]
    ]

    await event.edit(add_premium_emojis_to_text(codes_text), buttons=buttons)

@client.on(events.CallbackQuery(data=b'delete_activation_code'))
async def delete_activation_code_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>🗑 حذف كود تفعيل</b>\n\n<b>أرسل الكود الذي تريد حذفه:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_activation_code_delete(new_event):
        code = new_event.text.strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM activation_codes WHERE code = ?', (code,))
        conn.commit()
        conn.close()

        if cursor.rowcount > 0:
            await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم حذف الكود ({code}) بنجاح!</b>"))
        else:
            await new_event.reply(add_premium_emojis_to_text("<b>❌ الكود غير موجود.</b>"))

        await manage_activation_codes(new_event)
        client.remove_event_handler(handle_activation_code_delete)

@client.on(events.CallbackQuery(data=b'broadcast'))
async def broadcast_prompt(event):
    await event.edit(
        add_premium_emojis_to_text("<b>📢 الإذاعة</b>\n\n<b>أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:</b>")
    )

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_broadcast(new_event):
        text = new_event.text
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = [row['user_id'] for row in cursor.fetchall()]
        conn.close()

        success = 0
        failed = 0

        for user_id in users:
            try:
                await client.send_message(user_id, add_premium_emojis_to_text(f"<b>{text}</b>"))
                success += 1
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send broadcast to {user_id}: {e}")

            await asyncio.sleep(0.5)

        await new_event.reply(
            add_premium_emojis_to_text(
                f"<b>✅ تم إرسال الإذاعة بنجاح!</b>\n"
                f"<b>📊 الإحصائيات:</b>\n"
                f"<b>✔️ ناجحة:</b> {success}\n"
                f"<b>❌ فاشلة:</b> {failed}"
            )
        )

        await admin_panel(new_event)
        client.remove_event_handler(handle_broadcast)

@client.on(events.CallbackQuery(data=b'bot_settings'))
async def bot_settings(event):
    min_delay = await get_bot_setting('min_post_delay')
    max_delay = await get_bot_setting('max_post_delay')

    buttons = [
        [Button.inline("تغيير تأخير النشر", b'change_post_delay')],
        [Button.inline("إعادة تشغيل البوت", b'restart_bot')],
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(
        add_premium_emojis_to_text(
            f"<b>⚙️ إعدادات البوت</b>\n\n"
            f"<b>⏱ التأخير الحالي للنشر:</b> {min_delay}-{max_delay} ثانية\n\n"
            "<b>اختر الإعداد الذي تريد تغييره:</b>"
        ),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'change_post_delay'))
async def change_post_delay(event):
    await event.edit(
        add_premium_emojis_to_text("<b>⏱ تغيير تأخير النشر</b>\n\n<b>أرسل التأخير الجديد بالثواني (مثال: 300 أو 300-500):</b>")
    )

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_delay_change(new_event):
        text = new_event.text
        try:
            if '-' in text:
                min_delay, max_delay = map(int, text.split('-'))
            else:
                min_delay = max_delay = int(text)

            if min_delay > max_delay:
                min_delay, max_delay = max_delay, min_delay

            await update_bot_setting('min_post_delay', str(min_delay))
            await update_bot_setting('max_post_delay', str(max_delay))

            await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم تحديث تأخير النشر إلى: {min_delay}-{max_delay} ثانية</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await bot_settings(new_event)
        client.remove_event_handler(handle_delay_change)

@client.on(events.CallbackQuery(data=b'restart_bot'))
async def restart_bot(event):
    await event.edit(add_premium_emojis_to_text("<b>🔄 إعادة تشغيل البوت</b>\n\n<b>جاري إعادة التشغيل...</b>"))
    await asyncio.sleep(2)
    await event.edit(add_premium_emojis_to_text("<b>✅ تم إعادة تشغيل البوت بنجاح!</b>"))
    await admin_panel(event)

@client.on(events.CallbackQuery(data=b'developer_tools'))
async def developer_tools(event):
    buttons = [
        [Button.inline("إضافة جلسة جديدة", b'add_session')],
        [Button.inline("اختبار الاتصال", b'test_connection')],
        [Button.inline("قاعدة البيانات", b'database_tools')],
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>🛠 أدوات المطور</b>\n\n<b>اختر الأداة التي تريد استخدامها:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_session'))
async def add_session_prompt(event):
    await event.edit(
        add_premium_emojis_to_text("<b>🔑 إضافة جلسة جديدة</b>\n\n<b>أرسل رقم الهاتف أو الجلسة الحالية (string session):</b>")
    )

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_session_add(new_event):
        text = new_event.text
        if len(text) > 20:
            try:
                new_client = TelegramClient(StringSession(text), API_ID, API_HASH)
                await new_client.connect()
                if await new_client.is_user_authorized():
                    await new_event.reply(add_premium_emojis_to_text("<b>✅ الجلسة صالحة ويمكن استخدامها.</b>"))
                else:
                    await new_event.reply(add_premium_emojis_to_text("<b>❌ الجلسة غير صالحة.</b>"))
                await new_client.disconnect()
            except Exception as e:
                await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ في الجلسة: {e}</b>"))
        else:
            try:
                new_client = TelegramClient('new_session', API_ID, API_HASH)
                await new_client.start(phone=text)
                session = new_client.session.save()
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إنشاء جلسة جديدة:</b>\n<code>{session}</code>"))
                await new_client.disconnect()
            except Exception as e:
                await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ في إنشاء الجلسة: {e}</b>"))

        await developer_tools(new_event)
        client.remove_event_handler(handle_session_add)

@client.on(events.CallbackQuery(data=b'test_connection'))
async def test_connection(event):
    await event.edit(add_premium_emojis_to_text("<b>📡 اختبار الاتصال</b>\n\n<b>جاري اختبار الاتصال...</b>"))
    try:
        me = await client.get_me()
        await event.edit(
            add_premium_emojis_to_text(
                f"<b>✅ الاتصال ناجح!</b>\n\n"
                f"<b>👤 البوت:</b> {me.first_name}\n"
                f"<b>🆔 المعرف:</b> {me.id}"
            )
        )
    except Exception as e:
        await event.edit(add_premium_emojis_to_text(f"<b>❌ فشل الاتصال: {e}</b>"))

@client.on(events.CallbackQuery(data=b'database_tools'))
async def database_tools(event):
    buttons = [
        [Button.inline("استعلام مخصص", b'custom_query')],
        [Button.inline("نسخ قاعدة البيانات", b'backup_db')],
        [Button.inline("استعادة قاعدة البيانات", b'restore_db')],
        [Button.inline("رجوع", b'developer_tools')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>🗃 قاعدة البيانات</b>\n\n<b>اختر الأداة التي تريد استخدامها:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'custom_query'))
async def custom_query_prompt(event):
    await event.edit(
        add_premium_emojis_to_text("<b>🔍 استعلام مخصص</b>\n\n<b>أرسل الاستعلام الذي تريد تنفيذه (احذر من الاستعلامات الخطيرة):</b>")
    )

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_custom_query(new_event):
        query = new_event.text
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                if results:
                    response = "<b>📋 النتائج:</b>\n\n"
                    for row in results:
                        response += str(dict(row)) + "\n"
                    await new_event.reply(add_premium_emojis_to_text(response))
                else:
                    await new_event.reply(add_premium_emojis_to_text("<b>✅ الاستعلام ناجح ولكن لم يتم إرجاع نتائج.</b>"))
            else:
                conn.commit()
                await new_event.reply(add_premium_emojis_to_text("<b>✅ تم تنفيذ الاستعلام بنجاح.</b>"))

            conn.close()
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ في الاستعلام: {e}</b>"))

        await database_tools(new_event)
        client.remove_event_handler(handle_custom_query)

@client.on(events.CallbackQuery(data=b'backup_db'))
async def backup_db(event):
    await event.edit(add_premium_emojis_to_text("<b>🔄 نسخ قاعدة البيانات</b>\n\n<b>جاري إنشاء النسخة الاحتياطية...</b>"))
    try:
        import shutil
        backup_name = f"{DB_NAME}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(DB_NAME, backup_name)
        await event.edit(add_premium_emojis_to_text(f"<b>✅ تم إنشاء النسخة الاحتياطية:</b> <code>{backup_name}</code>"))
    except Exception as e:
        await event.edit(add_premium_emojis_to_text(f"<b>❌ فشل إنشاء النسخة الاحتياطية: {e}</b>"))

@client.on(events.CallbackQuery(data=b'restore_db'))
async def restore_db_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>🔄 استعادة قاعدة البيانات</b>\n\n<b>أرسل اسم ملف النسخة الاحتياطية التي تريد استعادتها:</b>"))

    @client.on(events.NewMessage(from_users=lambda u: u.username == ADMIN_USERNAME))
    async def handle_restore_db(new_event):
        backup_name = new_event.text.strip()
        try:
            if not os.path.exists(backup_name):
                await new_event.reply(add_premium_emojis_to_text("<b>❌ الملف غير موجود.</b>"))
                return

            import shutil
            shutil.copy2(backup_name, DB_NAME)
            await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم استعادة قاعدة البيانات من {backup_name} بنجاح!</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ في الاستعادة: {e}</b>"))

        await database_tools(new_event)
        client.remove_event_handler(handle_restore_db)

@client.on(events.CallbackQuery(data=b'developer_control'))
async def developer_control(event):
    user_id = event.sender_id
    if not await is_user_developer(user_id):
        await event.answer("🚫 هذه الميزة متاحة للمطورين فقط!", alert=True)
        return

    buttons = [
        [Button.inline("إدارة المطورين", b'manage_developers')],
        [Button.inline("تنفيذ أمر بايثون", b'execute_python')],
        [Button.inline("إدارة النظام", b'system_control')],
        [Button.inline("رجوع", b'admin_panel')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>🛠 تحكم المطور</b>\n\n<b>مرحبًا بك في لوحة تحكم المطور.</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'manage_developers'))
async def manage_developers(event):
    buttons = [
        [Button.inline("إضافة مطور", b'add_developer')],
        [Button.inline("إزالة مطور", b'remove_developer')],
        [Button.inline("قائمة المطورين", b'list_developers')],
        [Button.inline("رجوع", b'developer_control')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>👥 إدارة المطورين</b>\n\n<b>اختر الإجراء الذي تريد القيام به:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_developer'))
async def add_developer_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>👥 إضافة مطور</b>\n\n<b>أرسل معرف المستخدم الذي تريد إضافته كمطور:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_add_developer(new_event):
        try:
            user_id = int(new_event.text)
            if await add_developer(user_id):
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إضافة المستخدم ({user_id}) كمطور بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إضافة المطور.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await manage_developers(new_event)
        client.remove_event_handler(handle_add_developer)

@client.on(events.CallbackQuery(data=b'remove_developer'))
async def remove_developer_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>👥 إزالة مطور</b>\n\n<b>أرسل معرف المستخدم الذي تريد إزالته من المطورين:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_remove_developer(new_event):
        try:
            user_id = int(new_event.text)
            if await remove_developer(user_id):
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إزالة المطور ({user_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إزالة المطور.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await manage_developers(new_event)
        client.remove_event_handler(handle_remove_developer)

@client.on(events.CallbackQuery(data=b'list_developers'))
async def list_developers(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, first_name, last_name, username FROM users WHERE is_developer = 1')
    developers = cursor.fetchall()
    conn.close()

    if not developers:
        await event.edit(add_premium_emojis_to_text("<b>❌ لا يوجد مطورين حاليًا.</b>"))
        return

    developers_text = "<b>👥 قائمة المطورين</b>\n\n"
    for dev in developers:
        name = f"{dev['first_name'] or ''} {dev['last_name'] or ''}".strip()
        if not name:
            name = dev['username'] or "مستخدم غير معروف"
        developers_text += f"<b>👤 {name} ({dev['user_id']})</b>\n"

    buttons = [
        [Button.inline("رجوع", b'manage_developers')]
    ]

    await event.edit(add_premium_emojis_to_text(developers_text), buttons=buttons)

@client.on(events.CallbackQuery(data=b'execute_python'))
async def execute_python_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>🐍 تنفيذ أمر بايثون</b>\n\n<b>أرسل الكود الذي تريد تنفيذه:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_execute_python(new_event):
        code = new_event.text
        try:
            old_stdout = sys.stdout
            redirected_output = sys.stdout = asyncio.StringIO()

            exec(code)

            sys.stdout = old_stdout
            output = redirected_output.getvalue()

            if output:
                await new_event.reply(add_premium_emojis_to_text(f"<b>📋 النتيجة:</b>\n<code>{output}</code>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>✅ تم تنفيذ الكود بنجاح بدون إخراج.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ في التنفيذ:</b>\n<code>{str(e)}</code>"))

        await developer_control(new_event)
        client.remove_event_handler(handle_execute_python)

@client.on(events.CallbackQuery(data=b'system_control'))
async def system_control(event):
    buttons = [
        [Button.inline("معلومات النظام", b'system_info')],
        [Button.inline("إعادة تشغيل النظام", b'restart_system')],
        [Button.inline("إيقاف النظام", b'shutdown_system')],
        [Button.inline("رجوع", b'developer_control')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>⚙️ إدارة النظام</b>\n\n<b>اختر الإجراء الذي تريد القيام به:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'system_info'))
async def system_info(event):
    import platform
    import psutil

    info = (
        f"<b>🖥 معلومات النظام</b>\n\n"
        f"<b>🐍 بايثون:</b> {platform.python_version()}\n"
        f"<b>💻 النظام:</b> {platform.system()} {platform.release()}\n"
        f"<b>📦 المعالج:</b> {platform.processor()}\n"
        f"<b>🧠 ذاكرة الوصول العشوائي:</b> {psutil.virtual_memory().percent}% مستخدمة\n"
        f"<b>💾 مساحة القرص:</b> {psutil.disk_usage('/').percent}% مستخدمة\n"
        f"<b>🔌 البوت:</b> قيد التشغيل منذ {datetime.now() - datetime.fromtimestamp(psutil.boot_time())}"
    )

    buttons = [
        [Button.inline("رجوع", b'system_control')]
    ]

    await event.edit(add_premium_emojis_to_text(info), buttons=buttons)

@client.on(events.CallbackQuery(data=b'restart_system'))
async def restart_system(event):
    await event.edit(add_premium_emojis_to_text("<b>🔄 إعادة تشغيل النظام</b>\n\n<b>جاري إعادة تشغيل النظام...</b>"))
    await asyncio.sleep(2)
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.CallbackQuery(data=b'shutdown_system'))
async def shutdown_system(event):
    await event.edit(add_premium_emojis_to_text("<b>⏹ إيقاف النظام</b>\n\n<b>جاري إيقاف النظام...</b>"))
    await asyncio.sleep(2)
    await client.disconnect()
    sys.exit(0)

# User commands
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
    username = excluded.username,
    first_name = excluded.first_name,
    last_name = excluded.last_name
    ''', (
        user_id,
        event.sender.username,
        event.sender.first_name,
        event.sender.last_name
    ))
    conn.commit()
    conn.close()

    if event.sender.username in DEVELOPER_USERNAMES and not await is_user_developer(user_id):
        await add_developer(user_id)

    if not await is_user_activated(user_id):
        await event.respond(
            add_premium_emojis_to_text("<b>🔑 مرحبا بك في بوت النشر المتطور!</b>\n\n<b>يرجى إرسال كود التفعيل للدخول إلى البوت:</b>")
        )
        return

    is_vip = await is_user_vip(user_id)
    is_developer = await is_user_developer(user_id)

    buttons = [
        [Button.inline("نشر تلقائي", b'auto_post')],
        [Button.inline("الرسائل", b'messages')],
        [Button.inline("VIP", b'vip')]
    ]

    if is_vip:
        buttons.append([Button.inline("لوحة التحكم", b'user_panel')])

    if is_developer:
        buttons.append([Button.inline("تحكم المطور", b'developer_control')])

    await event.respond(
        add_premium_emojis_to_text(
            "<b>🤖 بوت النشر التلقائي المتطور</b>\n\n"
            "<b>مرحبًا بك في بوت النشر التلقائي المتطور!</b>\n\n"
            "<b>يمكنك استخدام هذا البوت لنشر الرسائل تلقائيًا في المجموعات التي تريدها.</b>\n\n"
            "<b>🔹 ميزات البوت:</b>\n"
            "<b>✔ نشر تلقائي متطور</b>\n"
            "<b>✔ تخطي الباند والحظر</b>\n"
            "<b>✔ حماية من الفلود</b>\n"
            "<b>✔ رسائل بريميوم مع إيموجي وخطوط متنوعة</b>\n"
            "<b>✔ حذف تلقائي للمجموعات المحظورة</b>\n"
            "<b>✔ لوحة تحكم متطورة</b>\n\n"
            "<b>اختر الإجراء الذي تريد القيام به:</b>"
        ),
        buttons=buttons
    )

@client.on(events.NewMessage())
async def handle_activation(event):
    if not event.is_private:
        return

    user_id = event.sender_id
    if not await is_user_activated(user_id):
        code = event.text.strip()
        if await redeem_activation_code(user_id, code):
            await event.respond(
                add_premium_emojis_to_text("<b>✅ تم تفعيل البوت بنجاح!</b>\n\n<b>يمكنك الآن استخدام جميع ميزات البوت.</b>")
            )
            await start(event)
        else:
            await event.respond(add_premium_emojis_to_text("<b>❌ كود التفعيل غير صحيح!</b>"))

@client.on(events.CallbackQuery(data=b'user_panel'))
async def user_panel(event):
    user_id = event.sender_id
    if not await is_user_vip(user_id):
        await event.answer("🚫 هذه الميزة متاحة لمستخدمي VIP فقط!", alert=True)
        return

    buttons = [
        [Button.inline("إضافة مجموعة", b'user_add_group')],
        [Button.inline("إزالة مجموعة", b'user_remove_group')],
        [Button.inline("قائمة المجموعات", b'user_list_groups')],
        [Button.inline("إضافة رسالة", b'user_add_message')],
        [Button.inline("رجوع", b'start')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>🎛 لوحة التحكم</b>\n\n<b>مرحبًا بك في لوحة التحكم الخاصة بك.</b>\n\n<b>يمكنك إدارة المجموعات والرسائل الخاصة بك من هنا.</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'user_add_group'))
async def user_add_group_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>📥 إضافة مجموعة</b>\n\n<b>أرسل معرف أو رابط المجموعة التي تريد إضافتها:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_user_group_add(new_event):
        text = new_event.text
        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
                group_name = group.title
                group_username = group.username
            else:
                group_id = int(text)
                group = await client.get_entity(group_id)
                group_name = group.title
                group_username = group.username

            if await add_group(group_id, group_name, group_username, added_by=new_event.sender_id):
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إضافة المجموعة {group_name} ({group_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إضافة المجموعة.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await user_panel(new_event)
        client.remove_event_handler(handle_user_group_add)

@client.on(events.CallbackQuery(data=b'user_remove_group'))
async def user_remove_group_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>📤 إزالة مجموعة</b>\n\n<b>أرسل معرف أو رابط المجموعة التي تريد إزالتها:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_user_group_remove(new_event):
        text = new_event.text
        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
            else:
                group_id = int(text)

            if await remove_group(group_id):
                await new_event.reply(add_premium_emojis_to_text(f"<b>✅ تم إزالة المجموعة ({group_id}) بنجاح!</b>"))
            else:
                await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إزالة المجموعة.</b>"))
        except Exception as e:
            await new_event.reply(add_premium_emojis_to_text(f"<b>❌ خطأ: {e}</b>"))

        await user_panel(new_event)
        client.remove_event_handler(handle_user_group_remove)

@client.on(events.CallbackQuery(data=b'user_list_groups'))
async def user_list_groups(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT group_id, group_name, group_username FROM groups WHERE is_active = 1 AND added_by = ?', (event.sender_id,))
    groups = cursor.fetchall()
    conn.close()

    if not groups:
        await event.edit(add_premium_emojis_to_text("<b>❌ لا توجد مجموعات نشطة حاليًا.</b>"))
        return

    groups_text = "<b>📋 قائمة المجموعات النشطة</b>\n\n"
    for group in groups:
        groups_text += f"<b>🏢 {group['group_name']} ({group['group_id']})</b>\n"
        if group['group_username']:
            groups_text += f"<b>🔗 @{group['group_username']}</b>\n"
        groups_text += "\n"

    buttons = [
        [Button.inline("رجوع", b'user_panel')]
    ]

    await event.edit(add_premium_emojis_to_text(groups_text), buttons=buttons)

@client.on(events.CallbackQuery(data=b'user_add_message'))
async def user_add_message_prompt(event):
    buttons = [
        [Button.inline("رسالة عادية", b'user_regular_message')],
        [Button.inline("رسالة بريميوم", b'user_premium_message')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>💬 إضافة رسالة</b>\n\n<b>اختر نوع الرسالة التي تريد إضافتها:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'user_regular_message'))
async def user_add_regular_message(event):
    await event.edit(add_premium_emojis_to_text("<b>💬 إضافة رسالة عادية</b>\n\n<b>أرسل الرسالة التي تريد إضافتها:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_user_regular_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=False, added_by=new_event.sender_id):
            await new_event.reply(add_premium_emojis_to_text("<b>✅ تم إضافة الرسالة بنجاح!</b>"))
        else:
            await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إضافة الرسالة.</b>"))

        await user_panel(new_event)
        client.remove_event_handler(handle_user_regular_message)

@client.on(events.CallbackQuery(data=b'user_premium_message'))
async def user_add_premium_message(event):
    buttons = [
        [Button.inline("خط عادي", b'user_font_normal')],
        [Button.inline("خط مونوسبيس", b'user_font_monospace')],
        [Button.inline("خط سانز سيريف", b'user_font_sans')]
    ]

    await event.edit(
        add_premium_emojis_to_text("<b>💎 إضافة رسالة بريميوم</b>\n\n<b>اختر نوع الخط للرسالة:</b>"),
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=re.compile(b'user_font_(.*)')))
async def handle_user_font_selection(event):
    font = event.data_match.group(1).decode('utf-8')
    await event.edit(add_premium_emojis_to_text(f"<b>💎 إضافة رسالة بريميوم</b>\n\n<b>أرسل الرسالة التي تريد إضافتها بخط {font}:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_user_premium_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=True, font=font, added_by=new_event.sender_id):
            await new_event.reply(add_premium_emojis_to_text("<b>✅ تم إضافة الرسالة البريميوم بنجاح!</b>"))
        else:
            await new_event.reply(add_premium_emojis_to_text("<b>❌ فشل إضافة الرسالة.</b>"))

        await user_panel(new_event)
        client.remove_event_handler(handle_user_premium_message)

@client.on(events.CallbackQuery(data=b'auto_post'))
async def auto_post_info(event):
    await event.edit(
        add_premium_emojis_to_text(
            "<b>📢 النشر التلقائي</b>\n\n"
            "<b>البوت يقوم بالنشر التلقائي في المجموعات المضافة كل 5-8 دقائق.</b>\n\n"
            "<b>🔹 الميزات:</b>\n"
            "<b>✔ نشر تلقائي متطور</b>\n"
            "<b>✔ تخطي الباند والحظر</b>\n"
            "<b>✔ حماية من الفلود</b>\n"
            "<b>✔ رسائل متنوعة مع إيموجي وخطوط مختلفة</b>\n"
            "<b>✔ حذف تلقائي للمجموعات المحظورة</b>\n\n"
            "<b>لإضافة مجموعات للنشر التلقائي، استخدم لوحة التحكم.</b>"
        )
    )

@client.on(events.CallbackQuery(data=b'messages'))
async def messages_info(event):
    await event.edit(
        add_premium_emojis_to_text(
            "<b>💬 الرسائل</b>\n\n"
            "<b>يمكنك إضافة رسائل للنشر التلقائي.</b>\n\n"
            "<b>🔹 أنواع الرسائل:</b>\n"
            "<b>✔ رسائل عادية</b>\n"
            "<b>✔ رسائل بريميوم (مع خطوط وإيموجي متنوعة)</b>\n\n"
            "<b>لإضافة رسائل، استخدم لوحة التحكم.</b>"
        )
    )

@client.on(events.CallbackQuery(data=b'vip'))
async def vip_info(event):
    user_id = event.sender_id
    is_vip = await is_user_vip(user_id)

    if is_vip:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT vip_expiry FROM users WHERE user_id = ?', (user_id,))
        expiry = cursor.fetchone()['vip_expiry']
        conn.close()

        expiry_date = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')

        await event.edit(
            add_premium_emojis_to_text(
                "<b>👑 VIP</b>\n\n"
                "<b>✅ لديك اشتراك VIP نشط!</b>\n\n"
                f"<b>📅 انتهاء الاشتراك:</b> {expiry_date}\n\n"
                "<b>🔹 مزايا VIP:</b>\n"
                "<b>✔ الوصول إلى لوحة التحكم</b>\n"
                "<b>✔ إضافة مجموعات غير محدودة</b>\n"
                "<b>✔ رسائل بريميوم</b>\n"
                "<b>✔ أولوية في الدعم</b>"
            )
        )
    else:
        buttons = [
            [Button.inline("تفعيل VIP", b'activate_vip')]
        ]

        await event.edit(
            add_premium_emojis_to_text(
                "<b>👑 VIP</b>\n\n"
                "<b>للحصول على مزايا VIP، يمكنك تفعيل اشتراك VIP.</b>\n\n"
                "<b>🔹 مزايا VIP:</b>\n"
                "<b>✔ الوصول إلى لوحة التحكم</b>\n"
                "<b>✔ إضافة مجموعات غير محدودة</b>\n"
                "<b>✔ رسائل بريميوم</b>\n"
                "<b>✔ أولوية في الدعم</b>\n\n"
                "<b>للتفعيل، أرسل كود VIP إذا كان لديك أو اتصل بالدعم.</b>"
            ),
            buttons=buttons
        )

@client.on(events.CallbackQuery(data=b'activate_vip'))
async def activate_vip_prompt(event):
    await event.edit(add_premium_emojis_to_text("<b>🎟 تفعيل VIP</b>\n\n<b>أرسل كود VIP الذي حصلت عليه:</b>"))

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_vip_activation(new_event):
        code = new_event.text.strip()
        if await redeem_vip_code(new_event.sender_id, code):
            await new_event.reply(add_premium_emojis_to_text("<b>✅ تم تفعيل VIP بنجاح! يمكنك الآن استخدام جميع المزايا.</b>"))
        else:
            await new_event.reply(add_premium_emojis_to_text("<b>❌ الكود غير صالح أو مستخدم بالفعل.</b>"))

        await vip_info(new_event)
        client.remove_event_handler(handle_vip_activation)

# Auto reply to mentions and replies
@client.on(events.NewMessage())
async def auto_reply(event):
    if event.is_private:
        return

    if event.is_reply:
        reply_to = await event.get_reply_message()
        if reply_to.sender_id == (await client.get_me()).id:
            await event.reply(add_premium_emojis_to_text("<b>🤖 شكرًا لتواصلك معي!</b>"))

    if f"@{client.me.username}" in event.text:
        await event.reply(add_premium_emojis_to_text("<b>🤖 نعم، كيف يمكنني مساعدتك؟</b>"))

# Auto welcome in private
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def auto_welcome(event):
    user_id = event.sender_id
    if event.text == '/start':
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_exists = cursor.fetchone() is not None
    conn.close()

    if not user_exists:
        await start(event)
    else:
        await event.reply(
            add_premium_emojis_to_text(
                "<b>🤖 مرحبًا مجددًا!</b>\n\n"
                "<b>يمكنك استخدام الأوامر التالية:</b>\n"
                "<b>/start - عرض قائمة الأوامر</b>"
            )
        )

# Main function
async def main():
    await client.start()
    logger.info("Bot started successfully!")

    # Check if admin is in developers list
    if ADMIN_USERNAME not in DEVELOPER_USERNAMES:
        DEVELOPER_USERNAMES.append(ADMIN_USERNAME)

    # Add admin as developer if not exists
    admin = await client.get_entity(ADMIN_USERNAME)
    if admin and not await is_user_developer(admin.id):
        await add_developer(admin.id)

    await auto_poster()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
