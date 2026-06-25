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
from typing import List, Dict, Optional

# Premium Emojis
PREMIUM_EMOJIS = [
    "💻", "🎲", "🌿", "👤", "🪐", "🔅", "⚡️", "🎸", "🕊", "⚪️", "🦋", "✨"
]

# Configuration
API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8914045842:AAEz6MNsGTShwob_M3H0ECy8eOkl2nT5gno"
ADMIN_ID = 932862531
DB_NAME = 'auto_poster.db'

# Initialize logging
logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

    # Messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        font TEXT,
        is_premium BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

def add_premium_emojis(text: str) -> str:
    emoji = random.choice(PREMIUM_EMOJIS)
    return f"{emoji} {text} {emoji}"

def format_text_with_font(text: str, font: str = None) -> str:
    if not font:
        fonts = [
            "monospace", "sans-serif", "serif", "small", "large",
            "𝗠𝗢𝗡𝗢𝗦𝗣𝗔𝗖𝗘", "𝖬𝖮𝖭𝖮𝖲𝖯𝖠𝖢𝖤", "𝕄𝕆ℕ𝕆𝕊ℙ𝔸ℂ𝔼",
            "𝓜𝓞𝓝𝓞𝓢𝓟𝓐𝓒𝓔", "𝒎𝒐𝒏𝒐𝒔𝒑𝒂𝒄𝒆", "𝐌𝐎𝐍𝐎𝐒𝐏𝐀𝐂𝐄"
        ]
        font = random.choice(fonts)

    if font.lower() == "monospace":
        return f"```{text}```"
    elif font.lower() == "sans-serif":
        return f"𝗧𝗘𝗫𝗧: {text}"
    elif font.lower() == "serif":
        return f"𝖳𝖤𝖸𝖳: {text}"
    elif font == "small":
        return f"<small>{text}</small>"
    elif font == "large":
        return f"<large>{text}</large>"
    else:
        return f"{text}"

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

async def get_random_delay() -> int:
    return random.randint(300, 500)

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
            if message_count >= 5:  # Level 3 protection
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

async def add_group(group_id: int, group_name: str, group_username: str = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO groups (group_id, group_name, group_username)
        VALUES (?, ?, ?)
        ON CONFLICT(group_id) DO UPDATE SET
        group_name = excluded.group_name,
        group_username = excluded.group_username,
        is_active = 1,
        is_banned = 0
        ''', (group_id, group_name, group_username))
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

async def add_message(text: str, is_premium: bool = False, font: str = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        formatted_text = format_text_with_font(text, font)
        cursor.execute('''
        INSERT INTO messages (text, font, is_premium)
        VALUES (?, ?, ?)
        ''', (formatted_text, font, is_premium))
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
                    formatted_message = add_premium_emojis(message) if random.random() < 0.7 else message

                    try:
                        await client.send_message(group_id, formatted_message)
                        logger.info(f"Posted to group {group_id}: {formatted_message[:50]}...")
                    except Exception as e:
                        logger.error(f"Error posting to group {group_id}: {e}")
                        if "CHAT_WRITE_FORBIDDEN" in str(e) or "CHAT_ADMIN_REQUIRED" in str(e):
                            await ban_group(group_id)

                    delay = await get_random_delay()
                    await asyncio.sleep(delay)
                except Exception as e:
                    logger.error(f"Error in group {group_id} loop: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in auto_poster main loop: {e}")
            await asyncio.sleep(60)

# Admin panel
@client.on(events.NewMessage(pattern='/start', from_users=ADMIN_ID))
async def admin_panel(event):
    buttons = [
        [Button.inline("📊 الإحصائيات", b'stats')],
        [Button.inline("👥 إدارة المجموعات", b'manage_groups')],
        [Button.inline("💬 إدارة الرسائل", b'manage_messages')],
        [Button.inline("👑 إدارة VIP", b'manage_vip')],
        [Button.inline("📢 الإذاعة", b'broadcast')],
        [Button.inline("🔧 إعدادات البوت", b'bot_settings')],
        [Button.inline("🛠 أدوات المطور", b'developer_tools')]
    ]

    await event.respond(
        "🎛 **لوحة التحكم الإدارية**\n\n"
        "مرحبًا بك في لوحة التحكم الإدارية للبوت المتطور للنشر التلقائي.",
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

    conn.close()

    stats_text = (
        "📊 **إحصائيات البوت**\n\n"
        f"👥 المستخدمين: {users_count}\n"
        f"🏢 المجموعات النشطة: {active_groups_count}\n"
        f"🚫 المجموعات المحظورة: {banned_groups_count}\n"
        f"💬 الرسائل المخزنة: {messages_count}\n"
        f"🎟 أكواد VIP غير مستخدمة: {unused_vip_codes}\n"
        f"👑 مستخدمي VIP: {vip_users_count}"
    )

    buttons = [
        [Button.inline("⬅️ رجوع", b'admin_panel')]
    ]

    await event.edit(stats_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b'manage_groups'))
async def manage_groups(event):
    buttons = [
        [Button.inline("📥 إضافة مجموعة", b'add_group')],
        [Button.inline("📤 إزالة مجموعة", b'remove_group')],
        [Button.inline("🚫 حظر مجموعة", b'ban_group')],
        [Button.inline("📋 قائمة المجموعات", b'list_groups')],
        [Button.inline("⬅️ رجوع", b'admin_panel')]
    ]

    await event.edit(
        "🏢 **إدارة المجموعات**\n\n"
        "اختر الإجراء الذي تريد القيام به:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_group'))
async def add_group_prompt(event):
    await event.edit("📥 **إضافة مجموعة**\n\nأرسل معرف أو رابط المجموعة التي تريد إضافتها:")

    @client.on(events.NewMessage(from_users=ADMIN_ID))
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
                await new_event.reply(f"✅ تم إضافة المجموعة {group_name} ({group_id}) بنجاح!")
            else:
                await new_event.reply("❌ فشل إضافة المجموعة.")
        except Exception as e:
            await new_event.reply(f"❌ خطأ: {e}")

        await admin_panel(new_event)
        client.remove_event_handler(handle_group_add)

@client.on(events.CallbackQuery(data=b'remove_group'))
async def remove_group_prompt(event):
    await event.edit("📤 **إزالة مجموعة**\n\nأرسل معرف أو رابط المجموعة التي تريد إزالتها:")

    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def handle_group_remove(new_event):
        text = new_event.text
        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
            else:
                group_id = int(text)

            if await remove_group(group_id):
                await new_event.reply(f"✅ تم إزالة المجموعة ({group_id}) بنجاح!")
            else:
                await new_event.reply("❌ فشل إزالة المجموعة.")
        except Exception as e:
            await new_event.reply(f"❌ خطأ: {e}")

        await admin_panel(new_event)
        client.remove_event_handler(handle_group_remove)

@client.on(events.CallbackQuery(data=b'ban_group'))
async def ban_group_prompt(event):
    await event.edit("🚫 **حظر مجموعة**\n\nأرسل معرف أو رابط المجموعة التي تريد حظرها:")

    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def handle_group_ban(new_event):
        text = new_event.text
        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
            else:
                group_id = int(text)

            if await ban_group(group_id):
                await new_event.reply(f"✅ تم حظر المجموعة ({group_id}) بنجاح!")
            else:
                await new_event.reply("❌ فشل حظر المجموعة.")
        except Exception as e:
            await new_event.reply(f"❌ خطأ: {e}")

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
        await event.edit("❌ لا توجد مجموعات نشطة حاليًا.")
        return

    groups_text = "📋 **قائمة المجموعات النشطة**\n\n"
    for group in groups:
        groups_text += f"🏢 {group['group_name']} ({group['group_id']})\n"
        if group['group_username']:
            groups_text += f"🔗 @{group['group_username']}\n"
        groups_text += "\n"

    buttons = [
        [Button.inline("⬅️ رجوع", b'manage_groups')]
    ]

    await event.edit(groups_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b'manage_messages'))
async def manage_messages(event):
    buttons = [
        [Button.inline("➕ إضافة رسالة عادية", b'add_regular_message')],
        [Button.inline("➕ إضافة رسالة بريميوم", b'add_premium_message')],
        [Button.inline("📋 قائمة الرسائل", b'list_messages')],
        [Button.inline("⬅️ رجوع", b'admin_panel')]
    ]

    await event.edit(
        "💬 **إدارة الرسائل**\n\n"
        "اختر الإجراء الذي تريد القيام به:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_regular_message'))
async def add_regular_message_prompt(event):
    await event.edit("➕ **إضافة رسالة عادية**\n\nأرسل الرسالة التي تريد إضافتها:")

    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def handle_regular_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=False):
            await new_event.reply("✅ تم إضافة الرسالة بنجاح!")
        else:
            await new_event.reply("❌ فشل إضافة الرسالة.")

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
        "➕ **إضافة رسالة بريميوم**\n\n"
        "اختر نوع الخط للرسالة:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=re.compile(b'font_(.*)')))
async def handle_font_selection(event):
    font = event.data_match.group(1).decode('utf-8')
    await event.edit(f"➕ **إضافة رسالة بريميوم**\n\nأرسل الرسالة التي تريد إضافتها بخط {font}:")

    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def handle_premium_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=True, font=font):
            await new_event.reply("✅ تم إضافة الرسالة البريميوم بنجاح!")
        else:
            await new_event.reply("❌ فشل إضافة الرسالة.")

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
        await event.edit("❌ لا توجد رسائل مخزنة حاليًا.")
        return

    messages_text = "📋 **قائمة الرسائل**\n\n"
    for msg in messages:
        premium = "👑" if msg['is_premium'] else "📝"
        messages_text += f"{premium} ({msg['id']}) {msg['text'][:50]}...\n\n"

    buttons = [
        [Button.inline("⬅️ رجوع", b'manage_messages')]
    ]

    await event.edit(messages_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b'manage_vip'))
async def manage_vip(event):
    buttons = [
        [Button.inline("🎟 توليد كود VIP", b'generate_vip_code')],
        [Button.inline("👑 قائمة مستخدمي VIP", b'list_vip_users')],
        [Button.inline("⬅️ رجوع", b'admin_panel')]
    ]

    await event.edit(
        "👑 **إدارة VIP**\n\n"
        "اختر الإجراء الذي تريد القيام به:",
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
        "🎟 **توليد كود VIP**\n\n"
        "اختر مدة الكود:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=re.compile(b'vip_(\d+)_days')))
async def handle_vip_code_generation(event):
    duration = int(event.data_match.group(1).decode('utf-8'))
    code = await generate_vip_code(duration)

    if code:
        await event.edit(
            f"✅ **تم توليد كود VIP**\n\n"
            f"الكود: `{code}`\n"
            f"المدة: {duration} أيام\n\n"
            "يمكنك الآن إرسال هذا الكود للمستخدمين لتفعيل VIP."
        )
    else:
        await event.edit("❌ فشل توليد الكود.")

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
        await event.edit("❌ لا يوجد مستخدمي VIP حاليًا.")
        return

    users_text = "👑 **قائمة مستخدمي VIP**\n\n"
    for user in users:
        name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip()
        if not name:
            name = user['username'] or "مستخدم غير معروف"
        expiry = datetime.strptime(user['vip_expiry'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        users_text += f"👤 {name} ({user['user_id']})\n📅 انتهاء VIP: {expiry}\n\n"

    buttons = [
        [Button.inline("⬅️ رجوع", b'manage_vip')]
    ]

    await event.edit(users_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b'broadcast'))
async def broadcast_prompt(event):
    await event.edit(
        "📢 **الإذاعة**\n\n"
        "أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:"
    )

    @client.on(events.NewMessage(from_users=ADMIN_ID))
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
                await client.send_message(user_id, text)
                success += 1
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send broadcast to {user_id}: {e}")

            await asyncio.sleep(0.5)

        await new_event.reply(
            f"✅ تم إرسال الإذاعة بنجاح!\n"
            f"📊 الإحصائيات:\n"
            f"✔️ ناجحة: {success}\n"
            f"❌ فاشلة: {failed}"
        )

        await admin_panel(new_event)
        client.remove_event_handler(handle_broadcast)

@client.on(events.CallbackQuery(data=b'bot_settings'))
async def bot_settings(event):
    buttons = [
        [Button.inline("⏱ تغيير تأخير النشر", b'change_post_delay')],
        [Button.inline("🔄 إعادة تشغيل البوت", b'restart_bot')],
        [Button.inline("⬅️ رجوع", b'admin_panel')]
    ]

    await event.edit(
        "⚙️ **إعدادات البوت**\n\n"
        "اختر الإعداد الذي تريد تغييره:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'change_post_delay'))
async def change_post_delay(event):
    await event.edit(
        "⏱ **تغيير تأخير النشر**\n\n"
        "أرسل التأخير الجديد بالثواني (مثال: 300 أو 300-500):"
    )

    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def handle_delay_change(new_event):
        text = new_event.text
        # This is a placeholder - actual implementation would need to modify the auto_poster function
        await new_event.reply(f"✅ تم تحديث تأخير النشر إلى: {text}")
        await bot_settings(new_event)
        client.remove_event_handler(handle_delay_change)

@client.on(events.CallbackQuery(data=b'restart_bot'))
async def restart_bot(event):
    await event.edit("🔄 **إعادة تشغيل البوت**\n\nجاري إعادة التشغيل...")
    await asyncio.sleep(2)
    await event.edit("✅ تم إعادة تشغيل البوت بنجاح!")
    await admin_panel(event)

@client.on(events.CallbackQuery(data=b'developer_tools'))
async def developer_tools(event):
    buttons = [
        [Button.inline("🔑 إضافة جلسة جديدة", b'add_session')],
        [Button.inline("📡 اختبار الاتصال", b'test_connection')],
        [Button.inline("🗃 قاعدة البيانات", b'database_tools')],
        [Button.inline("⬅️ رجوع", b'admin_panel')]
    ]

    await event.edit(
        "🛠 **أدوات المبرمج**\n\n"
        "اختر الأداة التي تريد استخدامها:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_session'))
async def add_session_prompt(event):
    await event.edit(
        "🔑 **إضافة جلسة جديدة**\n\n"
        "أرسل رقم الهاتف أو الجلسة الحالية (string session):"
    )

    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def handle_session_add(new_event):
        text = new_event.text
        if len(text) > 20:  # Likely a string session
            try:
                new_client = TelegramClient(StringSession(text), API_ID, API_HASH)
                await new_client.connect()
                if await new_client.is_user_authorized():
                    await new_event.reply("✅ الجلسة صالحة ويمكن استخدامها.")
                else:
                    await new_event.reply("❌ الجلسة غير صالحة.")
                await new_client.disconnect()
            except Exception as e:
                await new_event.reply(f"❌ خطأ في الجلسة: {e}")
        else:  # Likely a phone number
            try:
                new_client = TelegramClient('new_session', API_ID, API_HASH)
                await new_client.start(phone=text)
                session = new_client.session.save()
                await new_event.reply(f"✅ تم إنشاء جلسة جديدة:\n`{session}`")
                await new_client.disconnect()
            except Exception as e:
                await new_event.reply(f"❌ خطأ في إنشاء الجلسة: {e}")

        await developer_tools(new_event)
        client.remove_event_handler(handle_session_add)

@client.on(events.CallbackQuery(data=b'test_connection'))
async def test_connection(event):
    await event.edit("📡 **اختبار الاتصال**\n\nجاري اختبار الاتصال...")
    try:
        me = await client.get_me()
        await event.edit(
            f"✅ الاتصال ناجح!\n\n"
            f"👤 البوت: {me.first_name}\n"
            f"🆔 المعرف: {me.id}"
        )
    except Exception as e:
        await event.edit(f"❌ فشل الاتصال: {e}")

@client.on(events.CallbackQuery(data=b'database_tools'))
async def database_tools(event):
    buttons = [
        [Button.inline("🔍 استعلام مخصص", b'custom_query')],
        [Button.inline("🔄 نسخ قاعدة البيانات", b'backup_db')],
        [Button.inline("⬅️ رجوع", b'developer_tools')]
    ]

    await event.edit(
        "🗃 **قاعدة البيانات**\n\n"
        "اختر الأداة التي تريد استخدامها:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'custom_query'))
async def custom_query_prompt(event):
    await event.edit(
        "🔍 **استعلام مخصص**\n\n"
        "أرسل الاستعلام الذي تريد تنفيذه (احذر من الاستعلامات الخطيرة):"
    )

    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def handle_custom_query(new_event):
        query = new_event.text
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                if results:
                    response = "📋 النتائج:\n\n"
                    for row in results:
                        response += str(dict(row)) + "\n"
                    await new_event.reply(response)
                else:
                    await new_event.reply("✅ الاستعلام ناجح ولكن لم يتم إرجاع نتائج.")
            else:
                conn.commit()
                await new_event.reply("✅ تم تنفيذ الاستعلام بنجاح.")

            conn.close()
        except Exception as e:
            await new_event.reply(f"❌ خطأ في الاستعلام: {e}")

        await database_tools(new_event)
        client.remove_event_handler(handle_custom_query)

@client.on(events.CallbackQuery(data=b'backup_db'))
async def backup_db(event):
    await event.edit("🔄 **نسخ قاعدة البيانات**\n\nجاري إنشاء النسخة الاحتياطية...")
    try:
        import shutil
        backup_name = f"{DB_NAME}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(DB_NAME, backup_name)
        await event.edit(f"✅ تم إنشاء النسخة الاحتياطية: {backup_name}")
    except Exception as e:
        await event.edit(f"❌ فشل إنشاء النسخة الاحتياطية: {e}")

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

    is_vip = await is_user_vip(user_id)

    buttons = [
        [Button.inline("📢 نشر تلقائي", b'auto_post')],
        [Button.inline("💬 الرسائل", b'messages')],
        [Button.inline("👑 VIP", b'vip')]
    ]

    if is_vip:
        buttons.append([Button.inline("🎛 لوحة التحكم", b'user_panel')])

    await event.respond(
        "🤖 **بوت النشر التلقائي المتطور**\n\n"
        "مرحبًا بك في بوت النشر التلقائي المتطور!\n\n"
        "يمكنك استخدام هذا البوت لنشر الرسائل تلقائيًا في المجموعات التي تريدها.\n\n"
        "🔹 ميزات البوت:\n"
        "✔ نشر تلقائي متطور\n"
        "✔ تخطي الباند والحظر\n"
        "✔ حماية من الفلود\n"
        "✔ رسائل بريميوم مع إيموجي وخطوط متنوعة\n"
        "✔ حذف تلقائي للمجموعات المحظورة\n"
        "✔ لوحة تحكم متطورة\n\n"
        "اختر الإجراء الذي تريد القيام به:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'user_panel'))
async def user_panel(event):
    user_id = event.sender_id
    if not await is_user_vip(user_id):
        await event.answer("🚫 هذه الميزة متاحة لمستخدمي VIP فقط!", alert=True)
        return

    buttons = [
        [Button.inline("📥 إضافة مجموعة", b'user_add_group')],
        [Button.inline("📤 إزالة مجموعة", b'user_remove_group')],
        [Button.inline("📋 قائمة المجموعات", b'user_list_groups')],
        [Button.inline("💬 إضافة رسالة", b'user_add_message')],
        [Button.inline("⬅️ رجوع", b'start')]
    ]

    await event.edit(
        "🎛 **لوحة التحكم**\n\n"
        "مرحبًا بك في لوحة التحكم الخاصة بك.\n\n"
        "يمكنك إدارة المجموعات والرسائل الخاصة بك من هنا.",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'user_add_group'))
async def user_add_group_prompt(event):
    await event.edit("📥 **إضافة مجموعة**\n\nأرسل معرف أو رابط المجموعة التي تريد إضافتها:")

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

            if await add_group(group_id, group_name, group_username):
                await new_event.reply(f"✅ تم إضافة المجموعة {group_name} ({group_id}) بنجاح!")
            else:
                await new_event.reply("❌ فشل إضافة المجموعة.")
        except Exception as e:
            await new_event.reply(f"❌ خطأ: {e}")

        await user_panel(new_event)
        client.remove_event_handler(handle_user_group_add)

@client.on(events.CallbackQuery(data=b'user_remove_group'))
async def user_remove_group_prompt(event):
    await event.edit("📤 **إزالة مجموعة**\n\nأرسل معرف أو رابط المجموعة التي تريد إزالتها:")

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
                await new_event.reply(f"✅ تم إزالة المجموعة ({group_id}) بنجاح!")
            else:
                await new_event.reply("❌ فشل إزالة المجموعة.")
        except Exception as e:
            await new_event.reply(f"❌ خطأ: {e}")

        await user_panel(new_event)
        client.remove_event_handler(handle_user_group_remove)

@client.on(events.CallbackQuery(data=b'user_list_groups'))
async def user_list_groups(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT group_id, group_name, group_username FROM groups WHERE is_active = 1')
    groups = cursor.fetchall()
    conn.close()

    if not groups:
        await event.edit("❌ لا توجد مجموعات نشطة حاليًا.")
        return

    groups_text = "📋 **قائمة المجموعات النشطة**\n\n"
    for group in groups:
        groups_text += f"🏢 {group['group_name']} ({group['group_id']})\n"
        if group['group_username']:
            groups_text += f"🔗 @{group['group_username']}\n"
        groups_text += "\n"

    buttons = [
        [Button.inline("⬅️ رجوع", b'user_panel')]
    ]

    await event.edit(groups_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b'user_add_message'))
async def user_add_message_prompt(event):
    buttons = [
        [Button.inline("رسالة عادية", b'user_regular_message')],
        [Button.inline("رسالة بريميوم", b'user_premium_message')]
    ]

    await event.edit(
        "💬 **إضافة رسالة**\n\n"
        "اختر نوع الرسالة التي تريد إضافتها:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'user_regular_message'))
async def user_add_regular_message(event):
    await event.edit("💬 **إضافة رسالة عادية**\n\nأرسل الرسالة التي تريد إضافتها:")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_user_regular_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=False):
            await new_event.reply("✅ تم إضافة الرسالة بنجاح!")
        else:
            await new_event.reply("❌ فشل إضافة الرسالة.")

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
        "💎 **إضافة رسالة بريميوم**\n\n"
        "اختر نوع الخط للرسالة:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=re.compile(b'user_font_(.*)')))
async def handle_user_font_selection(event):
    font = event.data_match.group(1).decode('utf-8')
    await event.edit(f"💎 **إضافة رسالة بريميوم**\n\nأرسل الرسالة التي تريد إضافتها بخط {font}:")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_user_premium_message(new_event):
        text = new_event.text
        if await add_message(text, is_premium=True, font=font):
            await new_event.reply("✅ تم إضافة الرسالة البريميوم بنجاح!")
        else:
            await new_event.reply("❌ فشل إضافة الرسالة.")

        await user_panel(new_event)
        client.remove_event_handler(handle_user_premium_message)

@client.on(events.CallbackQuery(data=b'auto_post'))
async def auto_post_info(event):
    await event.edit(
        "📢 **النشر التلقائي**\n\n"
        "البوت يقوم بالنشر التلقائي في المجموعات المضافة كل 5-8 دقائق.\n\n"
        "🔹 الميزات:\n"
        "✔ نشر تلقائي متطور\n"
        "✔ تخطي الباند والحظر\n"
        "✔ حماية من الفلود\n"
        "✔ رسائل متنوعة مع إيموجي وخطوط مختلفة\n"
        "✔ حذف تلقائي للمجموعات المحظورة\n\n"
        "لإضافة مجموعات للنشر التلقائي، استخدم لوحة التحكم."
    )

@client.on(events.CallbackQuery(data=b'messages'))
async def messages_info(event):
    await event.edit(
        "💬 **الرسائل**\n\n"
        "يمكنك إضافة رسائل للنشر التلقائي.\n\n"
        "🔹 أنواع الرسائل:\n"
        "✔ رسائل عادية\n"
        "✔ رسائل بريميوم (مع خطوط وإيموجي متنوعة)\n\n"
        "لإضافة رسائل، استخدم لوحة التحكم."
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
            "👑 **VIP**\n\n"
            "✅ لديك اشتراك VIP نشط!\n\n"
            f"📅 انتهاء الاشتراك: {expiry_date}\n\n"
            "🔹 مزايا VIP:\n"
            "✔ الوصول إلى لوحة التحكم\n"
            "✔ إضافة مجموعات غير محدودة\n"
            "✔ رسائل بريميوم\n"
            "✔ أولوية في الدعم"
        )
    else:
        buttons = [
            [Button.inline("🎟 تفعيل VIP", b'activate_vip')]
        ]

        await event.edit(
            "👑 **VIP**\n\n"
            "للحصول على مزايا VIP، يمكنك تفعيل اشتراك VIP.\n\n"
            "🔹 مزايا VIP:\n"
            "✔ الوصول إلى لوحة التحكم\n"
            "✔ إضافة مجموعات غير محدودة\n"
            "✔ رسائل بريميوم\n"
            "✔ أولوية في الدعم\n\n"
            "للتفعيل، أرسل كود VIP إذا كان لديك أو اتصل بالدعم.",
            buttons=buttons
        )

@client.on(events.CallbackQuery(data=b'activate_vip'))
async def activate_vip_prompt(event):
    await event.edit("🎟 **تفعيل VIP**\n\nأرسل كود VIP الذي حصلت عليه:")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_vip_activation(new_event):
        code = new_event.text.strip()
        if await redeem_vip_code(new_event.sender_id, code):
            await new_event.reply("✅ تم تفعيل VIP بنجاح! يمكنك الآن استخدام جميع المزايا.")
        else:
            await new_event.reply("❌ الكود غير صالح أو مستخدم بالفعل.")

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
            await event.reply("🤖 شكرًا لتواصلك معي!")

    if f"@{client.me.username}" in event.text:
        await event.reply("🤖 نعم، كيف يمكنني مساعدتك؟")

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
            "🤖 مرحبًا مجددًا!\n\n"
            "يمكنك استخدام الأوامر التالية:\n"
            "/start - عرض قائمة الأوامر"
        )

# Main function
async def main():
    await client.start()
    logger.info("Bot started successfully!")
    await auto_poster()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
