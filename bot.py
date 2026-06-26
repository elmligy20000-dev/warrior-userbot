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

# Configuration
API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8914045842:AAEz6MNsGTShwob_M3H0ECy8eOkl2nT5gno"
ADMIN_ID = 932862531
DEVELOPER_ID = 932862531  # Replace with developer ID if different
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
        session TEXT,
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

    # Posting settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posting_settings (
        id INTEGER PRIMARY KEY,
        min_delay INTEGER DEFAULT 300,
        max_delay INTEGER DEFAULT 500,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Auto reply settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auto_reply (
        id INTEGER PRIMARY KEY,
        enabled BOOLEAN DEFAULT FALSE,
        mention_reply TEXT,
        reply_reply TEXT,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Welcome message settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS welcome_settings (
        id INTEGER PRIMARY KEY,
        enabled BOOLEAN DEFAULT FALSE,
        message TEXT,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
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

    # Initialize default settings if not exists
    cursor.execute('SELECT COUNT(*) FROM posting_settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO posting_settings (min_delay, max_delay) VALUES (300, 500)')

    cursor.execute('SELECT COUNT(*) FROM auto_reply')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO auto_reply (enabled, mention_reply, reply_reply) VALUES (0, "نعم، كيف يمكنني مساعدتك؟", "شكرا لتواصلك معي!")')

    cursor.execute('SELECT COUNT(*) FROM welcome_settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO welcome_settings (enabled, message) VALUES (0, "مرحبا بك في البوت!")')

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

def format_text_with_font(text: str, font: str = None) -> str:
    if not font:
        return text

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
        return text

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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT min_delay, max_delay FROM posting_settings WHERE id = 1')
    result = cursor.fetchone()
    conn.close()

    if result:
        return random.randint(result['min_delay'], result['max_delay'])
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

async def get_all_messages() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT text FROM messages')
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

async def get_user_session(user_id: int) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT session FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['session'] if result else None

async def save_user_session(user_id: int, session: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE users
        SET session = ?
        WHERE user_id = ?
        ''', (session, user_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving session: {e}")
        return False
    finally:
        conn.close()

async def get_posting_settings() -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT min_delay, max_delay FROM posting_settings WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    return {'min_delay': result['min_delay'], 'max_delay': result['max_delay']} if result else {'min_delay': 300, 'max_delay': 500}

async def update_posting_settings(min_delay: int, max_delay: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE posting_settings
        SET min_delay = ?, max_delay = ?, last_updated = ?
        WHERE id = 1
        ''', (min_delay, max_delay, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating posting settings: {e}")
        return False
    finally:
        conn.close()

async def get_auto_reply_settings() -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT enabled, mention_reply, reply_reply FROM auto_reply WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    return {
        'enabled': result['enabled'],
        'mention_reply': result['mention_reply'],
        'reply_reply': result['reply_reply']
    } if result else {
        'enabled': False,
        'mention_reply': '',
        'reply_reply': ''
    }

async def update_auto_reply_settings(enabled: bool, mention_reply: str, reply_reply: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE auto_reply
        SET enabled = ?, mention_reply = ?, reply_reply = ?, last_updated = ?
        WHERE id = 1
        ''', (enabled, mention_reply, reply_reply, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating auto reply settings: {e}")
        return False
    finally:
        conn.close()

async def get_welcome_settings() -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT enabled, message FROM welcome_settings WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    return {
        'enabled': result['enabled'],
        'message': result['message']
    } if result else {
        'enabled': False,
        'message': ''
    }

async def update_welcome_settings(enabled: bool, message: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE welcome_settings
        SET enabled = ?, message = ?, last_updated = ?
        WHERE id = 1
        ''', (enabled, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating welcome settings: {e}")
        return False
    finally:
        conn.close()

async def get_all_user_groups(user_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT group_id, group_name, group_username, is_active, is_banned
    FROM groups
    WHERE group_id IN (
        SELECT group_id FROM group_members WHERE user_id = ?
    )
    ''', (user_id,))
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return groups

async def fetch_user_groups(user_id: int) -> bool:
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                await add_group(dialog.id, dialog.name, dialog.entity.username)
        return True
    except Exception as e:
        logger.error(f"Error fetching groups: {e}")
        return False

# Auto poster main function
async def auto_poster():
    while True:
        try:
            groups = await get_active_groups()
            messages = await get_all_messages()

            if not groups or not messages:
                await asyncio.sleep(60)
                continue

            for group_id in groups:
                try:
                    if not await check_group_status(group_id):
                        await ban_group(group_id)
                        continue

                    if not await check_flood_protection(group_id):
                        continue

                    message = random.choice(messages)

                    try:
                        await client.send_message(group_id, message)
                        logger.info(f"Posted to group {group_id}: {message[:50]}...")
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

# Main control panel
@client.on(events.NewMessage(pattern='/start'))
async def main_panel(event):
    user_id = event.sender_id

    # Check if user has a session
    session = await get_user_session(user_id)
    if not session:
        await event.respond(
            "مرحبا بك في بوت النشر المتطور\n\n"
            "يرجى ارسال جلسة السيشن الخاصة بك لتسجيل الدخول",
            buttons=[
                [Button.inline("ارسال جلسة السيشن", b'send_session')],
                [Button.url("مراسلة المبرمج", f"tg://user?id={DEVELOPER_ID}")]
            ]
        )
        return

    # Register user if not exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO users (user_id, username, first_name, last_name, session)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
    username = excluded.username,
    first_name = excluded.first_name,
    last_name = excluded.last_name,
    session = excluded.session
    ''', (
        user_id,
        event.sender.username,
        event.sender.first_name,
        event.sender.last_name,
        session
    ))
    conn.commit()
    conn.close()

    is_vip = await is_user_vip(user_id)

    buttons = [
        [Button.inline("التحكم بالنشر", b'posting_control')],
        [Button.inline("ادارة الجروبات", b'group_management')],
        [Button.inline("ادارة الرسائل", b'message_management')],
        [Button.inline("الرد التلقائي", b'auto_reply_control')],
        [Button.inline("الترحيب بالخاص", b'welcome_control')]
    ]

    if is_vip:
        buttons.append([Button.inline("تفعيل كود VIP", b'activate_vip')])

    buttons.append([Button.url("مراسلة المبرمج", f"tg://user?id={DEVELOPER_ID}")])

    await event.respond(
        "مرحبا بك في لوحة التحكم الرئيسية\n\n"
        "يمكنك التحكم الكامل في البوت من هنا",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'send_session'))
async def send_session_prompt(event):
    await event.edit("يرجى ارسال جلسة السيشن الخاصة بك")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_session(new_event):
        session = new_event.text.strip()
        if len(session) < 20:
            await new_event.reply("جلسة السيشن غير صالحة")
            return

        try:
            test_client = TelegramClient(StringSession(session), API_ID, API_HASH)
            await test_client.connect()
            if await test_client.is_user_authorized():
                await save_user_session(event.sender_id, session)
                await new_event.reply("تم تسجيل الدخول بنجاح")
                await main_panel(new_event)
            else:
                await new_event.reply("جلسة السيشن غير صالحة")
            await test_client.disconnect()
        except Exception as e:
            await new_event.reply(f"حدث خطأ: {e}")

        client.remove_event_handler(handle_session)

@client.on(events.CallbackQuery(data=b'posting_control'))
async def posting_control(event):
    settings = await get_posting_settings()

    buttons = [
        [Button.inline("تغيير وقت النشر", b'change_post_delay')],
        [Button.inline("عرض الاعدادات الحالية", b'show_posting_settings')],
        [Button.inline("رجوع", b'main_panel')]
    ]

    await event.edit(
        "التحكم بالنشر التلقائي\n\n"
        "هنا يمكنك التحكم في وقت النشر التلقائي",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'change_post_delay'))
async def change_post_delay(event):
    await event.edit(
        "يرجى ارسال وقت التأخير بالثواني\n"
        "مثال: 300-600\n"
        "او 300 للوقت الثابت"
    )

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_delay_change(new_event):
        text = new_event.text.strip()
        if '-' in text:
            try:
                min_delay, max_delay = map(int, text.split('-'))
                if min_delay >= max_delay or min_delay < 10 or max_delay > 3600:
                    raise ValueError
                if await update_posting_settings(min_delay, max_delay):
                    await new_event.reply(f"تم تحديث وقت النشر بنجاح: {min_delay}-{max_delay} ثانية")
                else:
                    await new_event.reply("فشل تحديث وقت النشر")
            except ValueError:
                await new_event.reply("تنسيق غير صحيح. يرجى استخدام التنسيق: 300-600")
        else:
            try:
                delay = int(text)
                if delay < 10 or delay > 3600:
                    raise ValueError
                if await update_posting_settings(delay, delay):
                    await new_event.reply(f"تم تحديث وقت النشر بنجاح: {delay} ثانية")
                else:
                    await new_event.reply("فشل تحديث وقت النشر")
            except ValueError:
                await new_event.reply("يرجى ارسال رقم صحيح بين 10 و 3600")

        await posting_control(new_event)
        client.remove_event_handler(handle_delay_change)

@client.on(events.CallbackQuery(data=b'show_posting_settings'))
async def show_posting_settings(event):
    settings = await get_posting_settings()

    if settings['min_delay'] == settings['max_delay']:
        delay_text = f"{settings['min_delay']} ثانية"
    else:
        delay_text = f"{settings['min_delay']}-{settings['max_delay']} ثانية"

    await event.edit(
        f"اعدادات النشر الحالية:\n\n"
        f"وقت التأخير: {delay_text}",
        buttons=[[Button.inline("رجوع", b'posting_control')]]
    )

@client.on(events.CallbackQuery(data=b'group_management'))
async def group_management(event):
    buttons = [
        [Button.inline("جلب جميع الجروبات", b'fetch_all_groups')],
        [Button.inline("عرض الجروبات المضافة", b'list_groups')],
        [Button.inline("اضافة جروبات", b'add_groups')],
        [Button.inline("حذف جروب", b'remove_group')],
        [Button.inline("رجوع", b'main_panel')]
    ]

    await event.edit(
        "ادارة الجروبات\n\n"
        "هنا يمكنك ادارة الجروبات للنشر التلقائي",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'fetch_all_groups'))
async def fetch_all_groups(event):
    await event.edit("جاري جلب جميع الجروبات...")

    if await fetch_user_groups(event.sender_id):
        await event.edit("تم جلب جميع الجروبات بنجاح", buttons=[[Button.inline("رجوع", b'group_management')]])
    else:
        await event.edit("فشل جلب الجروبات", buttons=[[Button.inline("رجوع", b'group_management')]])

@client.on(events.CallbackQuery(data=b'list_groups'))
async def list_groups(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT group_id, group_name, group_username, is_active, is_banned FROM groups')
    groups = cursor.fetchall()
    conn.close()

    if not groups:
        await event.edit("لا توجد جروبات مضافة", buttons=[[Button.inline("رجوع", b'group_management')]])
        return

    groups_text = "الجروبات المضافة:\n\n"
    for group in groups:
        status = "نشط" if group['is_active'] and not group['is_banned'] else "غير نشط"
        if group['is_banned']:
            status = "محظور"
        groups_text += f"{group['group_name']} ({group['group_id']}) - {status}\n"
        if group['group_username']:
            groups_text += f"@{group['group_username']}\n"
        groups_text += "\n"

    # Split into multiple messages if too long
    if len(groups_text) > 4000:
        chunks = [groups_text[i:i+4000] for i in range(0, len(groups_text), 4000)]
        for chunk in chunks:
            await event.reply(chunk)
        await event.edit("تم ارسال جميع الجروبات", buttons=[[Button.inline("رجوع", b'group_management')]])
    else:
        await event.edit(groups_text, buttons=[[Button.inline("رجوع", b'group_management')]])

@client.on(events.CallbackQuery(data=b'add_groups'))
async def add_groups_prompt(event):
    await event.edit(
        "يرجى ارسال معرفات الجروبات التي تريد اضافتها\n"
        "كل جروب في سطر منفصل\n"
        "يمكنك ارسال معرفات او روابط الجروبات"
    )

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_add_groups(new_event):
        text = new_event.text.strip()
        group_ids = text.split('\n')
        success = 0
        failed = 0

        for group_id in group_ids:
            group_id = group_id.strip()
            if not group_id:
                continue

            try:
                if group_id.startswith('https://t.me/'):
                    group = await client.get_entity(group_id)
                    group_id = group.id
                    group_name = group.title
                    group_username = group.username
                else:
                    group_id = int(group_id)
                    group = await client.get_entity(group_id)
                    group_name = group.title
                    group_username = group.username

                if await add_group(group_id, group_name, group_username):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                logger.error(f"Error adding group {group_id}: {e}")

        await new_event.reply(
            f"تمت اضافة الجروبات:\n"
            f"الناجحة: {success}\n"
            f"الفاشلة: {failed}"
        )

        await group_management(new_event)
        client.remove_event_handler(handle_add_groups)

@client.on(events.CallbackQuery(data=b'remove_group'))
async def remove_group_prompt(event):
    await event.edit(
        "يرجى ارسال معرف الجروب الذي تريد حذفه\n"
        "يمكنك ارسال معرف او رابط الجروب"
    )

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_remove_group(new_event):
        text = new_event.text.strip()

        try:
            if text.startswith('https://t.me/'):
                group = await client.get_entity(text)
                group_id = group.id
            else:
                group_id = int(text)

            if await remove_group(group_id):
                await new_event.reply(f"تم حذف الجروب ({group_id}) بنجاح")
            else:
                await new_event.reply("فشل حذف الجروب")
        except Exception as e:
            await new_event.reply(f"حدث خطأ: {e}")

        await group_management(new_event)
        client.remove_event_handler(handle_remove_group)

@client.on(events.CallbackQuery(data=b'message_management'))
async def message_management(event):
    buttons = [
        [Button.inline("اضافة رسالة", b'add_message')],
        [Button.inline("عرض الرسائل", b'list_messages')],
        [Button.inline("حذف رسالة", b'delete_message')],
        [Button.inline("رجوع", b'main_panel')]
    ]

    await event.edit(
        "ادارة الرسائل\n\n"
        "هنا يمكنك ادارة الرسائل للنشر التلقائي",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_message'))
async def add_message_prompt(event):
    buttons = [
        [Button.inline("رسالة عادية", b'add_regular_message')],
        [Button.inline("رسالة بتنسيق خاص", b'add_formatted_message')],
        [Button.inline("رجوع", b'message_management')]
    ]

    await event.edit(
        "اختر نوع الرسالة التي تريد اضافتها",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'add_regular_message'))
async def add_regular_message(event):
    await event.edit("يرجى ارسال الرسالة التي تريد اضافتها")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_add_message(new_event):
        text = new_event.text.strip()
        if await add_message(text, is_premium=False):
            await new_event.reply("تم اضافة الرسالة بنجاح")
        else:
            await new_event.reply("فشل اضافة الرسالة")

        await message_management(new_event)
        client.remove_event_handler(handle_add_message)

@client.on(events.CallbackQuery(data=b'add_formatted_message'))
async def add_formatted_message(event):
    buttons = [
        [Button.inline("خط عادي", b'font_normal')],
        [Button.inline("خط مونوسبيس", b'font_monospace')],
        [Button.inline("خط سانز سيريف", b'font_sans')],
        [Button.inline("رجوع", b'add_message')]
    ]

    await event.edit(
        "اختر نوع التنسيق للرسالة",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=re.compile(b'font_(.*)')))
async def handle_font_selection(event):
    font = event.data_match.group(1).decode('utf-8')
    await event.edit(f"يرجى ارسال الرسالة بتنسيق {font}")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_formatted_message(new_event):
        text = new_event.text.strip()
        if await add_message(text, is_premium=True, font=font):
            await new_event.reply("تم اضافة الرسالة بنجاح")
        else:
            await new_event.reply("فشل اضافة الرسالة")

        await message_management(new_event)
        client.remove_event_handler(handle_formatted_message)

@client.on(events.CallbackQuery(data=b'list_messages'))
async def list_messages(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, text FROM messages')
    messages = cursor.fetchall()
    conn.close()

    if not messages:
        await event.edit("لا توجد رسائل مضافة", buttons=[[Button.inline("رجوع", b'message_management')]])
        return

    messages_text = "الرسائل المضافة:\n\n"
    for msg in messages:
        messages_text += f"({msg['id']}) {msg['text'][:50]}...\n\n"

    if len(messages_text) > 4000:
        chunks = [messages_text[i:i+4000] for i in range(0, len(messages_text), 4000)]
        for chunk in chunks:
            await event.reply(chunk)
        await event.edit("تم ارسال جميع الرسائل", buttons=[[Button.inline("رجوع", b'message_management')]])
    else:
        await event.edit(messages_text, buttons=[[Button.inline("رجوع", b'message_management')]])

@client.on(events.CallbackQuery(data=b'delete_message'))
async def delete_message_prompt(event):
    await event.edit("يرجى ارسال رقم الرسالة التي تريد حذفها")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_delete_message(new_event):
        try:
            message_id = int(new_event.text.strip())
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM messages WHERE id = ?', (message_id,))
            conn.commit()
            deleted = cursor.rowcount
            conn.close()

            if deleted > 0:
                await new_event.reply("تم حذف الرسالة بنجاح")
            else:
                await new_event.reply("لم يتم العثور على الرسالة")
        except ValueError:
            await new_event.reply("يرجى ارسال رقم صحيح")
        except Exception as e:
            await new_event.reply(f"حدث خطأ: {e}")

        await message_management(new_event)
        client.remove_event_handler(handle_delete_message)

@client.on(events.CallbackQuery(data=b'auto_reply_control'))
async def auto_reply_control(event):
    settings = await get_auto_reply_settings()

    buttons = [
        [Button.inline("تفعيل/تعطيل الرد التلقائي", b'toggle_auto_reply')],
        [Button.inline("تعديل رد المنشن", b'edit_mention_reply')],
        [Button.inline("تعديل رد الريبلاي", b'edit_reply_reply')],
        [Button.inline("عرض الاعدادات الحالية", b'show_auto_reply_settings')],
        [Button.inline("رجوع", b'main_panel')]
    ]

    status = "مفعل" if settings['enabled'] else "معطل"
    await event.edit(
        f"التحكم بالرد التلقائي\n\n"
        f"الحالة الحالية: {status}",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'toggle_auto_reply'))
async def toggle_auto_reply(event):
    settings = await get_auto_reply_settings()
    new_status = not settings['enabled']

    if await update_auto_reply_settings(new_status, settings['mention_reply'], settings['reply_reply']):
        status = "مفعل" if new_status else "معطل"
        await event.edit(f"تم تحديث الحالة: {status}", buttons=[[Button.inline("رجوع", b'auto_reply_control')]])
    else:
        await event.answer("فشل تحديث الحالة", alert=True)

@client.on(events.CallbackQuery(data=b'edit_mention_reply'))
async def edit_mention_reply(event):
    await event.edit("يرجى ارسال الرد الجديد للمنشن")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_edit_mention_reply(new_event):
        text = new_event.text.strip()
        settings = await get_auto_reply_settings()
        if await update_auto_reply_settings(settings['enabled'], text, settings['reply_reply']):
            await new_event.reply("تم تحديث رد المنشن بنجاح")
        else:
            await new_event.reply("فشل تحديث رد المنشن")

        await auto_reply_control(new_event)
        client.remove_event_handler(handle_edit_mention_reply)

@client.on(events.CallbackQuery(data=b'edit_reply_reply'))
async def edit_reply_reply(event):
    await event.edit("يرجى ارسال الرد الجديد للريبلاي")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_edit_reply_reply(new_event):
        text = new_event.text.strip()
        settings = await get_auto_reply_settings()
        if await update_auto_reply_settings(settings['enabled'], settings['mention_reply'], text):
            await new_event.reply("تم تحديث رد الريبلاي بنجاح")
        else:
            await new_event.reply("فشل تحديث رد الريبلاي")

        await auto_reply_control(new_event)
        client.remove_event_handler(handle_edit_reply_reply)

@client.on(events.CallbackQuery(data=b'show_auto_reply_settings'))
async def show_auto_reply_settings(event):
    settings = await get_auto_reply_settings()

    status = "مفعل" if settings['enabled'] else "معطل"
    await event.edit(
        f"اعدادات الرد التلقائي:\n\n"
        f"الحالة: {status}\n"
        f"رد المنشن: {settings['mention_reply']}\n"
        f"رد الريبلاي: {settings['reply_reply']}",
        buttons=[[Button.inline("رجوع", b'auto_reply_control')]]
    )

@client.on(events.CallbackQuery(data=b'welcome_control'))
async def welcome_control(event):
    settings = await get_welcome_settings()

    buttons = [
        [Button.inline("تفعيل/تعطيل الترحيب", b'toggle_welcome')],
        [Button.inline("تعديل رسالة الترحيب", b'edit_welcome_message')],
        [Button.inline("عرض الاعدادات الحالية", b'show_welcome_settings')],
        [Button.inline("رجوع", b'main_panel')]
    ]

    status = "مفعل" if settings['enabled'] else "معطل"
    await event.edit(
        f"التحكم برسائل الترحيب\n\n"
        f"الحالة الحالية: {status}",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b'toggle_welcome'))
async def toggle_welcome(event):
    settings = await get_welcome_settings()
    new_status = not settings['enabled']

    if await update_welcome_settings(new_status, settings['message']):
        status = "مفعل" if new_status else "معطل"
        await event.edit(f"تم تحديث الحالة: {status}", buttons=[[Button.inline("رجوع", b'welcome_control')]])
    else:
        await event.answer("فشل تحديث الحالة", alert=True)

@client.on(events.CallbackQuery(data=b'edit_welcome_message'))
async def edit_welcome_message(event):
    await event.edit("يرجى ارسال رسالة الترحيب الجديدة")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_edit_welcome_message(new_event):
        text = new_event.text.strip()
        settings = await get_welcome_settings()
        if await update_welcome_settings(settings['enabled'], text):
            await new_event.reply("تم تحديث رسالة الترحيب بنجاح")
        else:
            await new_event.reply("فشل تحديث رسالة الترحيب")

        await welcome_control(new_event)
        client.remove_event_handler(handle_edit_welcome_message)

@client.on(events.CallbackQuery(data=b'show_welcome_settings'))
async def show_welcome_settings(event):
    settings = await get_welcome_settings()

    status = "مفعل" if settings['enabled'] else "معطل"
    await event.edit(
        f"اعدادات الترحيب:\n\n"
        f"الحالة: {status}\n"
        f"الرسالة: {settings['message']}",
        buttons=[[Button.inline("رجوع", b'welcome_control')]]
    )

@client.on(events.CallbackQuery(data=b'activate_vip'))
async def activate_vip_prompt(event):
    await event.edit("يرجى ارسال كود VIP لتفعيله")

    @client.on(events.NewMessage(from_users=event.sender_id))
    async def handle_vip_activation(new_event):
        code = new_event.text.strip()
        if await redeem_vip_code(new_event.sender_id, code):
            await new_event.reply("تم تفعيل VIP بنجاح")
            await main_panel(new_event)
        else:
            await new_event.reply("الكود غير صالح او مستخدم بالفعل")

        client.remove_event_handler(handle_vip_activation)

# Auto reply to mentions and replies
@client.on(events.NewMessage())
async def auto_reply(event):
    if event.is_private:
        return

    settings = await get_auto_reply_settings()
    if not settings['enabled']:
        return

    if event.is_reply:
        reply_to = await event.get_reply_message()
        if reply_to and reply_to.sender_id == (await client.get_me()).id:
            await event.reply(settings['reply_reply'])

    if f"@{client.me.username}" in event.text:
        await event.reply(settings['mention_reply'])

# Auto welcome in private
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def auto_welcome(event):
    if event.text == '/start':
        return

    settings = await get_welcome_settings()
    if settings['enabled']:
        await event.reply(settings['message'])

# Main function
async def main():
    await client.start()
    logger.info("Bot started successfully!")
    await auto_poster()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
