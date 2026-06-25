import os
import asyncio
import logging
from telethon import TelegramClient, events, functions, types, Button
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneCodeInvalidError, PhoneNumberInvalidError
from datetime import datetime
import sqlite3
import re
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_NAME = 'cleaner_bot.db'

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        phone TEXT,
        session TEXT,
        is_admin INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        ban_reason TEXT,
        created_at TEXT,
        last_active TEXT,
        stats_cleaned_chats INTEGER DEFAULT 0,
        stats_left_groups INTEGER DEFAULT 0,
        stats_left_channels INTEGER DEFAULT 0,
        stats_joined_groups INTEGER DEFAULT 0,
        stats_joined_channels INTEGER DEFAULT 0
    )
    ''')

    # Admin settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_settings (
        id INTEGER PRIMARY KEY,
        required_channel TEXT,
        required_group TEXT,
        broadcast_message_id INTEGER DEFAULT 0
    )
    ''')

    # Insert default admin settings if not exists
    cursor.execute('SELECT COUNT(*) FROM admin_settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO admin_settings (required_channel, required_group)
        VALUES (?,?)
        ''', ('', ''))
        conn.commit()

    conn.close()

init_db()

# Bot configuration
API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
ADMIN_ID = 932862531
DEVELOPER_ID = 932862531

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
# Helper functions
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def is_user_admin(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result['is_admin'] == 1

def is_user_banned(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result['is_banned'] == 1

def get_admin_settings() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_settings WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else {}

def update_user_stats(user_id: int, stat_type: str, increment: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'UPDATE users SET stats_{stat_type} = stats_{stat_type} + ? WHERE user_id = ?', (increment, user_id))
    conn.commit()
    conn.close()

async def check_subscription(user_id: int) -> Tuple[bool, str]:
    settings = get_admin_settings()
    if not settings['required_channel'] and not settings['required_group']:
        return True, ""

    client = await bot.get_entity(user_id)
    if not client:
        return False, "لا يمكن التحقق من اشتراكك"

    try:
        if settings['required_channel']:
            try:
                channel = await bot.get_entity(settings['required_channel'])
                if not await bot(functions.channels.GetParticipantRequest(
                    channel=channel,
                    participant=user_id
                )):
                    return False, f"يجب الاشتراك في القناة: @{settings['required_channel']}"
            except Exception as e:
                logger.error(f"Error checking channel subscription: {e}")
                return False, f"حدث خطأ أثناء التحقق من القناة: @{settings['required_channel']}"

        if settings['required_group']:
            try:
                group = await bot.get_entity(settings['required_group'])
                if not await bot(functions.messages.GetFullChatRequest(chat_id=group.id)):
                    return False, f"يجب الانضمام إلى المجموعة: @{settings['required_group']}"
            except Exception as e:
                logger.error(f"Error checking group subscription: {e}")
                return False, f"حدث خطأ أثناء التحقق من المجموعة: @{settings['required_group']}"

        return True, ""
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False, "حدث خطأ أثناء التحقق من الاشتراك"

async def get_user_client(user_id: int) -> Optional[TelegramClient]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT session FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or not result['session']:
        return None

    try:
        client = TelegramClient(
            StringSession(result['session']),
            API_ID,
            API_HASH,
            device_model="iPhone 17 Pro"
        )
        await client.connect()
        if not await client.is_user_authorized():
            return None
        return client
    except Exception as e:
        logger.error(f"Error creating client for user {user_id}: {e}")
        return None

async def add_user(user_id: int, username: str = None, phone: str = None, session: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, phone, session, created_at, last_active)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, username, phone, session, now, now))

    if cursor.rowcount == 0:
        cursor.execute('''
        UPDATE users SET username = ?, phone = ?, session = ?, last_active = ?
        WHERE user_id = ?
        ''', (username, phone, session, now, user_id))

    conn.commit()
    conn.close()

async def update_session(user_id: int, session: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET session = ? WHERE user_id = ?', (session, user_id))
    conn.commit()
    conn.close()

def create_main_keyboard(user_id: int) -> list:
    keyboard = [
        [Button.inline("📥 إضافة حساب", b"add_account")],
        [Button.inline("🧹 التنظيف الذكي", b"smart_clean")],
        [Button.inline("📋 جلب البيانات", b"fetch_data")],
        [Button.inline("🔗 الانضمام التلقائي", b"auto_join")],
        [Button.inline("👤 معلومات حسابي", b"account_info")],
        [Button.inline("👨‍💻 المطور", b"developer")]
    ]

    if is_user_admin(user_id):
        keyboard.append([Button.inline("👑 لوحة التحكم", b"admin_panel")])

    return keyboard

# Bot handlers
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    if is_user_banned(user_id):
        await event.respond("❌ تم حظرك من استخدام البوت\nالسبب: " + (await get_ban_reason(user_id)))
        return

    is_subscribed, message = await check_subscription(user_id)
    if not is_subscribed:
        keyboard = [
            [Button.url("📢 الاشتراك في القناة", f"https://t.me/{get_admin_settings()['required_channel']}")],
            [Button.url("👥 الانضمام إلى المجموعة", f"https://t.me/{get_admin_settings()['required_group']}")],
            [Button.inline("✅ تم الاشتراك", b"check_subscription")]
        ]
        await event.respond(message, buttons=keyboard)
        return

    await add_user(user_id, event.sender.username)

    await event.respond(
        "🌟 **مرحبا بك في بوت التنظيف الاحترافي** 🌟\n\n"
        "يمكنك استخدام البوت لتنظيف حساباتك وإدارتها بسهولة.\n"
        "اختر أحد الخيارات أدناه للبدء:",
        buttons=create_main_keyboard(user_id)
    )

@bot.on(events.CallbackQuery(data=b"check_subscription"))
async def check_subscription_handler(event):
    user_id = event.sender_id
    is_subscribed, message = await check_subscription(user_id)
    if is_subscribed:
        await event.edit(
            "✅ تم التحقق من الاشتراك بنجاح!",
            buttons=create_main_keyboard(user_id)
        )
    else:
        keyboard = [
            [Button.url("📢 الاشتراك في القناة", f"https://t.me/{get_admin_settings()['required_channel']}")],
            [Button.url("👥 الانضمام إلى المجموعة", f"https://t.me/{get_admin_settings()['required_group']}")],
            [Button.inline("✅ تم الاشتراك", b"check_subscription")]
        ]
        await event.edit(message, buttons=keyboard)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    if is_user_banned(user_id):
        await event.answer("تم حظرك من استخدام البوت", alert=True)
        return

    is_subscribed, message = await check_subscription(user_id)
    if not is_subscribed:
        keyboard = [
            [Button.url("📢 الاشتراك في القناة", f"https://t.me/{get_admin_settings()['required_channel']}")],
            [Button.url("👥 الانضمام إلى المجموعة", f"https://t.me/{get_admin_settings()['required_group']}")],
            [Button.inline("✅ تم الاشتراك", b"check_subscription")]
        ]
        await event.edit(message, buttons=keyboard)
        return

    data = event.data

    if data == b"add_account":
        await add_account_handler(event)
    elif data == b"smart_clean":
        await smart_clean_handler(event)
    elif data == b"fetch_data":
        await fetch_data_handler(event)
    elif data == b"auto_join":
        await auto_join_handler(event)
    elif data == b"account_info":
        await account_info_handler(event)
    elif data == b"admin_panel" and is_user_admin(user_id):
        await admin_panel_handler(event)
    elif data == b"developer":
        await developer_handler(event)
    elif data.startswith(b"clean_"):
        await clean_action_handler(event, data)
    elif data.startswith(b"fetch_"):
        await fetch_action_handler(event, data)
    elif data.startswith(b"join_"):
        await join_action_handler(event, data)
    elif data == b"back_to_main":
        await start_handler(event)

async def developer_handler(event):
    developer_keyboard = [
        [Button.url("👨‍💻 تواصل مع المطور", "https://t.me/shmrye")],
        [Button.inline("🔙 رجوع", b"back_to_main")]
    ]
    await event.edit(
        "👨‍💻 **المطور**\n\n"
        "البوت من تطوير @shmrye\n"
        "لأي استفسار أو اقتراح تواصل معي.",
        buttons=developer_keyboard
    )

async def add_account_handler(event):
    keyboard = [
        [Button.inline("📱 إضافة برقم هاتف", b"add_phone")],
        [Button.inline("🔑 إضافة بسيشن جاهز", b"add_session")],
        [Button.inline("🔙 رجوع", b"back_to_main")]
    ]
    await event.edit(
        "📥 **إضافة حساب**\n\n"
        "اختر طريقة إضافة الحساب:",
        buttons=keyboard
    )

async def add_phone_handler(event):
    await event.edit("📱 **إضافة برقم هاتف**\n\n"
                    "يرجى إرسال رقم هاتفك بالصيغة الدولية (مثال: +966512345678)")

    phone_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
    phone = phone_event.text.strip()

    if not re.match(r'^\+\d{8,15}$', phone):
        await event.respond("❌ رقم الهاتف غير صالح. يجب أن يكون بالصيغة الدولية.")
        return

    try:
        client = TelegramClient(
            StringSession(),
            API_ID,
            API_HASH,
            device_model="iPhone 17 Pro"
        )
        await client.connect()

        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await event.edit("🔑 **إدخال رمز التحقق**\n\n"
                           "تم إرسال رمز التحقق إلى رقم هاتفك. يرجى إرساله هنا.")

            code_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
            code = code_event.text.strip()

            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                await event.edit("🔒 **إدخال كلمة مرور التحقق الثنائي**\n\n"
                               "يرجى إرسال كلمة مرور التحقق الثنائي.")

                password_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
                password = password_event.text.strip()
                await client.sign_in(password=password)

            session = client.session.save()
            await update_session(event.sender_id, session)
            await event.edit("✅ تم إضافة الحساب بنجاح!")
            await client.disconnect()
            return

    except PhoneCodeInvalidError:
        await event.respond("❌ رمز التحقق غير صالح.")
    except PhoneNumberInvalidError:
        await event.respond("❌ رقم الهاتف غير صالح.")
    except Exception as e:
        logger.error(f"Error adding account by phone: {e}")
        await event.respond("❌ حدث خطأ أثناء إضافة الحساب.")

async def add_session_handler(event):
    await event.edit("🔑 **إضافة بسيشن جاهز**\n\n"
                    "يرجى إرسال Session String الخاص بك.")

    session_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
    session = session_event.text.strip()

    try:
        client = TelegramClient(
            StringSession(session),
            API_ID,
            API_HASH,
            device_model="iPhone 17 Pro"
        )
        await client.connect()

        if not await client.is_user_authorized():
            await event.respond("❌ Session String غير صالح.")
            return

        await update_session(event.sender_id, session)
        await event.edit("✅ تم إضافة الحساب بنجاح!")
        await client.disconnect()
    except Exception as e:
        logger.error(f"Error adding account by session: {e}")
        await event.respond("❌ حدث خطأ أثناء إضافة الحساب.")

async def smart_clean_handler(event):
    keyboard = [
        [Button.inline("🗑 حذف محادثات الخاص", b"clean_private_chats")],
        [Button.inline("🤖 حذف محادثات البوتات", b"clean_bot_chats")],
        [Button.inline("🚪 مغادرة الجروبات", b"clean_groups")],
        [Button.inline("📢 مغادرة القنوات", b"clean_channels")],
        [Button.inline("🧹 تنظيف الكل", b"clean_all")],
        [Button.inline("🔙 رجوع", b"back_to_main")]
    ]
    await event.edit(
        "🧹 **التنظيف الذكي**\n\n"
        "اختر ما تريد تنظيفه:",
        buttons=keyboard
    )

async def clean_action_handler(event, action):
    user_id = event.sender_id
    client = await get_user_client(user_id)
    if not client:
        await event.answer("❌ لم يتم إضافة حساب بعد. يرجى إضافة حساب أولاً.", alert=True)
        return

    try:
        if action == b"clean_private_chats":
            await event.edit("🗑 **حذف محادثات الخاص**\n\nجاري حذف المحادثات...")
            await delete_private_chats(client, user_id)
            await event.edit("✅ تم حذف محادثات الخاص بنجاح!")

        elif action == b"clean_bot_chats":
            await event.edit("🤖 **حذف محادثات البوتات**\n\nجاري حذف المحادثات...")
            await delete_bot_chats(client, user_id)
            await event.edit("✅ تم حذف محادثات البوتات بنجاح!")

        elif action == b"clean_groups":
            await event.edit("🚪 **مغادرة الجروبات**\n\nجاري مغادرة الجروبات...")
            await leave_groups(client, user_id)
            await event.edit("✅ تم مغادرة الجروبات بنجاح!")

        elif action == b"clean_channels":
            await event.edit("📢 **مغادرة القنوات**\n\nجاري مغادرة القنوات...")
            await leave_channels(client, user_id)
            await event.edit("✅ تم مغادرة القنوات بنجاح!")

        elif action == b"clean_all":
            await event.edit("🧹 **تنظيف الكل**\n\nجاري تنفيذ جميع عمليات التنظيف...")
            await delete_private_chats(client, user_id)
            await delete_bot_chats(client, user_id)
            await leave_groups(client, user_id)
            await leave_channels(client, user_id)
            await event.edit("✅ تم تنفيذ جميع عمليات التنظيف بنجاح!")

    except Exception as e:
        logger.error(f"Error in clean action {action}: {e}")
        await event.edit(f"❌ حدث خطأ أثناء التنفيذ: {str(e)}")
    finally:
        await client.disconnect()

async def delete_private_chats(client: TelegramClient, user_id: int):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_user and not dialog.entity.bot:
            try:
                await client.delete_dialog(dialog.id)
                update_user_stats(user_id, "cleaned_chats")
                await asyncio.sleep(1)  # Avoid flood wait
            except Exception as e:
                logger.error(f"Error deleting private chat {dialog.id}: {e}")

async def delete_bot_chats(client: TelegramClient, user_id: int):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_user and dialog.entity.bot:
            try:
                await client.delete_dialog(dialog.id)
                update_user_stats(user_id, "cleaned_chats")
                await asyncio.sleep(1)  # Avoid flood wait
            except Exception as e:
                logger.error(f"Error deleting bot chat {dialog.id}: {e}")

async def leave_groups(client: TelegramClient, user_id: int):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_group:
            try:
                # Check if user is admin
                participants = await client.get_participants(dialog.id)
                user = await client.get_me()
                is_admin = any(p.id == user.id and p.status in (
                    types.ChannelParticipantAdmin(),
                    types.ChannelParticipantCreator()
                ) for p in participants)

                if not is_admin:
                    await client(LeaveChannelRequest(dialog.id))
                    update_user_stats(user_id, "left_groups")
                    await asyncio.sleep(1)  # Avoid flood wait
            except Exception as e:
                logger.error(f"Error leaving group {dialog.id}: {e}")

async def leave_channels(client: TelegramClient, user_id: int):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_channel:
            try:
                # Check if user is admin
                participants = await client.get_participants(dialog.id)
                user = await client.get_me()
                is_admin = any(p.id == user.id and p.status in (
                    types.ChannelParticipantAdmin(),
                    types.ChannelParticipantCreator()
                ) for p in participants)

                if not is_admin:
                    await client(LeaveChannelRequest(dialog.id))
                    update_user_stats(user_id, "left_channels")
                    await asyncio.sleep(1)  # Avoid flood wait
            except Exception as e:
                logger.error(f"Error leaving channel {dialog.id}: {e}")

async def fetch_data_handler(event):
    keyboard = [
        [Button.inline("📢 جلب القنوات", b"fetch_channels")],
        [Button.inline("👥 جلب الجروبات", b"fetch_groups")],
        [Button.inline("🤖 جلب البوتات", b"fetch_bots")],
        [Button.inline("📋 جلب الكل", b"fetch_all")],
        [Button.inline("🔙 رجوع", b"back_to_main")]
    ]
    await event.edit(
        "📋 **جلب البيانات**\n\n"
        "اختر ما تريد جلبه:",
        buttons=keyboard
    )

async def fetch_action_handler(event, action):
    user_id = event.sender_id
    client = await get_user_client(user_id)
    if not client:
        await event.answer("❌ لم يتم إضافة حساب بعد. يرجى إضافة حساب أولاً.", alert=True)
        return

    try:
        if action == b"fetch_channels":
            await event.edit("📢 **جلب القنوات**\n\nجاري جلب القنوات...")
            channels = await fetch_channels(client)
            await send_large_list(event, channels, "القنوات المشتركة فيها")

        elif action == b"fetch_groups":
            await event.edit("👥 **جلب الجروبات**\n\nجاري جلب الجروبات...")
            groups = await fetch_groups(client)
            await send_large_list(event, groups, "الجروبات المشتركة فيها")

        elif action == b"fetch_bots":
            await event.edit("🤖 **جلب البوتات**\n\nجاري جلب البوتات...")
            bots = await fetch_bots(client)
            await send_large_list(event, bots, "البوتات التي كلمتها")

        elif action == b"fetch_all":
            await event.edit("📋 **جلب الكل**\n\nجاري جلب جميع البيانات...")
            channels = await fetch_channels(client)
            groups = await fetch_groups(client)
            bots = await fetch_bots(client)

            all_data = "📢 **القنوات المشتركة فيها**\n" + "\n".join(channels) + "\n\n"
            all_data += "👥 **الجروبات المشتركة فيها**\n" + "\n".join(groups) + "\n\n"
            all_data += "🤖 **البوتات التي كلمتها**\n" + "\n".join(bots)

            await send_large_text(event, all_data, "جميع البيانات")

    except Exception as e:
        logger.error(f"Error in fetch action {action}: {e}")
        await event.edit(f"❌ حدث خطأ أثناء التنفيذ: {str(e)}")
    finally:
        await client.disconnect()

async def fetch_channels(client: TelegramClient) -> List[str]:
    channels = []
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_channel:
            channels.append(f"{dialog.name} (ID: {dialog.id})")
    return channels

async def fetch_groups(client: TelegramClient) -> List[str]:
    groups = []
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_group:
            groups.append(f"{dialog.name} (ID: {dialog.id})")
    return groups

async def fetch_bots(client: TelegramClient) -> List[str]:
    bots = []
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_user and dialog.entity.bot:
            bots.append(f"{dialog.name} (ID: {dialog.id})")
    return bots

async def send_large_list(event, items: List[str], title: str):
    if len(items) <= 50:
        text = f"📋 **{title}**\n\n" + "\n".join(items)
        await event.edit(text)
    else:
        text = f"📋 **{title}** (عدد العناصر: {len(items)})\n\n"
        text += "تم تصدير البيانات إلى ملف نصي بسبب كثرتها."
        await event.edit(text)

        file_name = f"{title.replace(' ', '_')}_{event.sender_id}.txt"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write("\n".join(items))

        await event.client.send_file(event.chat_id, file_name, caption=f"📄 ملف {title}")
        os.remove(file_name)

async def send_large_text(event, text: str, title: str):
    if len(text) <= 4096:
        await event.edit(text)
    else:
        file_name = f"{title.replace(' ', '_')}_{event.sender_id}.txt"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(text)

        await event.edit(f"تم تصدير البيانات إلى ملف نصي بسبب كثرتها.")
        await event.client.send_file(event.chat_id, file_name, caption=f"📄 ملف {title}")
        os.remove(file_name)

async def auto_join_handler(event):
    keyboard = [
        [Button.inline("📢 انضمام للقنوات باليوزر", b"join_channels_username")],
        [Button.inline("👥 انضمام للجروبات برابط الدعوة", b"join_groups_link")],
        [Button.inline("🆔 انضمام بالايدي", b"join_by_id")],
        [Button.inline("🔙 رجوع", b"back_to_main")]
    ]
    await event.edit(
        "🔗 **الانضمام التلقائي**\n\n"
        "اختر طريقة الانضمام:",
        buttons=keyboard
    )

async def join_action_handler(event, action):
    user_id = event.sender_id
    client = await get_user_client(user_id)
    if not client:
        await event.answer("❌ لم يتم إضافة حساب بعد. يرجى إضافة حساب أولاً.", alert=True)
        return

    try:
        if action == b"join_channels_username":
            await event.edit("📢 **انضمام للقنوات باليوزر**\n\n"
                           "يرجى إرسال يوزرات القنوات مفصولة بسطر جديد (مثال: channel1\nchannel2)")

            usernames_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
            usernames = [u.strip() for u in usernames_event.text.split('\n') if u.strip()]

            if not usernames:
                await event.respond("❌ لم يتم إرسال أي يوزرات.")
                return

            await event.edit(f"🔗 جاري الانضمام إلى {len(usernames)} قناة...")
            joined = 0
            for username in usernames:
                try:
                    await client(JoinChannelRequest(username))
                    joined += 1
                    update_user_stats(user_id, "joined_channels")
                    await asyncio.sleep(2)  # Avoid flood wait
                except Exception as e:
                    logger.error(f"Error joining channel {username}: {e}")

            await event.edit(f"✅ تم الانضمام إلى {joined} قناة من {len(usernames)}")

        elif action == b"join_groups_link":
            await event.edit("👥 **انضمام للجروبات برابط الدعوة**\n\n"
                           "يرجى إرسال روابط الدعوة مفصولة بسطر جديد (مثال: https://t.me/joinchat/AAAAAE...\nhttps://t.me/...)")

            links_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
            links = [l.strip() for l in links_event.text.split('\n') if l.strip()]

            if not links:
                await event.respond("❌ لم يتم إرسال أي روابط.")
                return

            await event.edit(f"🔗 جاري الانضمام إلى {len(links)} مجموعة...")
            joined = 0
            for link in links:
                try:
                    # Extract hash from invite link
                    hash_match = re.search(r't\.me\/joinchat\/([a-zA-Z0-9_-]+)', link)
                    if not hash_match:
                        hash_match = re.search(r'\+([a-zA-Z0-9_-]+)', link)

                    if hash_match:
                        hash = hash_match.group(1)
                        await client(ImportChatInviteRequest(hash))
                        joined += 1
                        update_user_stats(user_id, "joined_groups")
                        await asyncio.sleep(2)  # Avoid flood wait
                except Exception as e:
                    logger.error(f"Error joining group with link {link}: {e}")

            await event.edit(f"✅ تم الانضمام إلى {joined} مجموعة من {len(links)}")

        elif action == b"join_by_id":
            await event.edit("🆔 **انضمام بالايدي**\n\n"
                           "يرجى إرسال ايدي الجروبات/القنوات مفصولة بسطر جديد (مثال: -100123456789\n-100987654321)")

            ids_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
            ids = [i.strip() for i in ids_event.text.split('\n') if i.strip()]

            if not ids:
                await event.respond("❌ لم يتم إرسال أي ايدي.")
                return

            await event.edit(f"🔗 جاري الانضمام إلى {len(ids)} مجموعة/قناة...")
            joined = 0
            for id_str in ids:
                try:
                    id = int(id_str)
                    if id < 0:
                        id = -1000000000000 - id  # Convert to Telegram's format
                    await client(JoinChannelRequest(id))
                    joined += 1
                    if id_str.startswith('-100'):
                        update_user_stats(user_id, "joined_channels")
                    else:
                        update_user_stats(user_id, "joined_groups")
                    await asyncio.sleep(2)  # Avoid flood wait
                except Exception as e:
                    logger.error(f"Error joining with ID {id_str}: {e}")

            await event.edit(f"✅ تم الانضمام إلى {joined} مجموعة/قناة من {len(ids)}")

    except Exception as e:
        logger.error(f"Error in join action {action}: {e}")
        await event.edit(f"❌ حدث خطأ أثناء التنفيذ: {str(e)}")
    finally:
        await client.disconnect()

async def account_info_handler(event):
    user_id = event.sender_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        await event.answer("❌ لم يتم العثور على معلومات الحساب.", alert=True)
        return

    client = await get_user_client(user_id)
    session_info = "غير متاح"
    phone = user['phone'] or "غير متاح"

    if client:
        try:
            me = await client.get_me()
            session_info = f"📱 **معلومات الحساب**\n"
            session_info += f"الاسم: {me.first_name}\n"
            session_info += f"اسم المستخدم: @{me.username}\n" if me.username else ""
            session_info += f"رقم الهاتف: {phone}\n"
            session_info += f"ايدي الحساب: {me.id}\n"
            session_info += f"نوع الحساب: {'بوت' if me.bot else 'مستخدم'}\n"
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
        finally:
            await client.disconnect()

    stats = f"📊 **إحصائيات التنظيف**\n"
    stats += f"المحادثات المحذوفة: {user['stats_cleaned_chats']}\n"
    stats += f"الجروبات المغادرة: {user['stats_left_groups']}\n"
    stats += f"القنوات المغادرة: {user['stats_left_channels']}\n"
    stats += f"الجروبات المنضم إليها: {user['stats_joined_groups']}\n"
    stats += f"القنوات المنضم إليها: {user['stats_joined_channels']}\n"

    keyboard = [
        [Button.inline("🔙 رجوع", b"back_to_main")]
    ]

    await event.edit(
        f"👤 **معلومات حسابي**\n\n"
        f"{session_info}\n"
        f"{stats}",
        buttons=keyboard
    )

async def admin_panel_handler(event):
    keyboard = [
        [Button.inline("📊 إحصائيات المستخدمين", b"admin_stats")],
        [Button.inline("👥 عرض آخر 50 مستخدم", b"admin_last_users")],
        [Button.inline("🔍 بحث عن مستخدم", b"admin_search_user")],
        [Button.inline("⛔ حظر/فك حظر مستخدم", b"admin_ban_user")],
        [Button.inline("📢 إرسال رسالة للجميع", b"admin_broadcast")],
        [Button.inline("💾 سحب نسخة احتياطية", b"admin_backup")],
        [Button.inline("⚙️ إعدادات الاشتراك", b"admin_subscription_settings")],
        [Button.inline("🔙 رجوع", b"back_to_main")]
    ]
    await event.edit(
        "👑 **لوحة تحكم الأدمن**\n\n"
        "اختر أحد الخيارات أدناه:",
        buttons=keyboard
    )

async def admin_stats_handler(event):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE last_active >= datetime("now", "-7 days")')
    active_users = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(stats_cleaned_chats) FROM users')
    total_cleaned = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(stats_left_groups) FROM users')
    total_left_groups = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(stats_left_channels) FROM users')
    total_left_channels = cursor.fetchone()[0] or 0

    conn.close()

    stats = f"📊 **إحصائيات النظام**\n\n"
    stats += f"إجمالي المستخدمين: {total_users}\n"
    stats += f"المستخدمين النشطين (7 أيام): {active_users}\n"
    stats += f"إجمالي المحادثات المحذوفة: {total_cleaned}\n"
    stats += f"إجمالي الجروبات المغادرة: {total_left_groups}\n"
    stats += f"إجمالي القنوات المغادرة: {total_left_channels}\n"

    await event.edit(stats)

async def admin_last_users_handler(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT user_id, username, last_active, stats_cleaned_chats
    FROM users
    ORDER BY last_active DESC
    LIMIT 50
    ''')
    users = cursor.fetchall()
    conn.close()

    text = "👥 **آخر 50 مستخدم**\n\n"
    for user in users:
        username = f"@{user['username']}" if user['username'] else "غير معروف"
        text += f"🆔 {user['user_id']} | {username} | آخر نشاط: {user['last_active']} | محادثات محذوفة: {user['stats_cleaned_chats']}\n"

    await event.edit(text)

async def admin_search_user_handler(event):
    await event.edit("🔍 **بحث عن مستخدم**\n\n"
                   "يرجى إرسال ايدي المستخدم الذي تريد البحث عنه.")

    user_id_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
    try:
        user_id = int(user_id_event.text.strip())
    except ValueError:
        await event.respond("❌ ايدي المستخدم غير صالح.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        await event.respond("❌ لم يتم العثور على المستخدم.")
        return

    text = f"👤 **معلومات المستخدم**\n\n"
    text += f"ايدي: {user['user_id']}\n"
    text += f"اسم المستخدم: @{user['username']}\n" if user['username'] else ""
    text += f"رقم الهاتف: {user['phone']}\n" if user['phone'] else ""
    text += f"تم الإنشاء في: {user['created_at']}\n"
    text += f"آخر نشاط: {user['last_active']}\n"
    text += f"الحالة: {'محظور' if user['is_banned'] else 'نشط'}\n"
    if user['is_banned']:
        text += f"سبب الحظر: {user['ban_reason']}\n"
    text += f"\n📊 **إحصائيات**\n"
    text += f"محادثات محذوفة: {user['stats_cleaned_chats']}\n"
    text += f"جروبات مغادرة: {user['stats_left_groups']}\n"
    text += f"قنوات مغادرة: {user['stats_left_channels']}\n"
    text += f"جروبات منضم إليها: {user['stats_joined_groups']}\n"
    text += f"قنوات منضم إليها: {user['stats_joined_channels']}\n"

    await event.edit(text)

async def admin_ban_user_handler(event):
    await event.edit("⛔ **حظر/فك حظر مستخدم**\n\n"
                   "يرجى إرسال ايدي المستخدم الذي تريد حظره أو فك حظره.")

    user_id_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
    try:
        user_id = int(user_id_event.text.strip())
    except ValueError:
        await event.respond("❌ ايدي المستخدم غير صالح.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        await event.respond("❌ لم يتم العثور على المستخدم.")
        return

    if user['is_banned']:
        # Unban user
        await event.edit(f"✅ **فك حظر المستخدم**\n\n"
                       f"تم فك حظر المستخدم {user_id}.\n"
                       "هل تريد إضافة سبب للفك؟ (نعم/لا)")

        response_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
        if response_event.text.strip().lower() == "نعم":
            await event.edit("يرجى إرسال سبب الفك.")

            reason_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
            reason = reason_event.text.strip()

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_banned = 0, ban_reason = ? WHERE user_id = ?', (reason, user_id))
            conn.commit()
            conn.close()

            await event.edit(f"✅ تم فك حظر المستخدم {user_id}.\nالسبب: {reason}")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()

            await event.edit(f"✅ تم فك حظر المستخدم {user_id}.")
    else:
        # Ban user
        await event.edit(f"❌ **حظر المستخدم**\n\n"
                       f"هل تريد حظر المستخدم {user_id}؟ (نعم/لا)")

        response_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
        if response_event.text.strip().lower() == "نعم":
            await event.edit("يرجى إرسال سبب الحظر.")

            reason_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
            reason = reason_event.text.strip()

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?', (reason, user_id))
            conn.commit()
            conn.close()

            await event.edit(f"✅ تم حظر المستخدم {user_id}.\nالسبب: {reason}")

async def admin_broadcast_handler(event):
    await event.edit("📢 **إرسال رسالة للجميع**\n\n"
                   "يرجى إرسال الرسالة التي تريد إرسالها لجميع المستخدمين.")

    message_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
    message = message_event.text.strip()

    if not message:
        await event.respond("❌ الرسالة فارغة.")
        return

    await event.edit("⏳ جاري إرسال الرسالة لجميع المستخدمين...")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
    users = cursor.fetchall()
    conn.close()

    success = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(user['user_id'], message)
            success += 1
            await asyncio.sleep(0.5)  # Avoid flood wait
        except Exception as e:
            logger.error(f"Error sending broadcast to {user['user_id']}: {e}")
            failed += 1

    await event.edit(f"✅ تم إرسال الرسالة إلى {success} مستخدم.\n"
                   f"❌ فشل الإرسال إلى {failed} مستخدم.")

async def admin_backup_handler(event):
    await event.edit("💾 **سحب نسخة احتياطية**\n\n"
                   "جاري إنشاء نسخة احتياطية من قاعدة البيانات...")

    try:
        with open(DB_NAME, 'rb') as f:
            await event.client.send_file(event.chat_id, f, caption="📄 نسخة احتياطية لقاعدة البيانات")
        await event.edit("✅ تم إنشاء النسخة الاحتياطية بنجاح!")
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        await event.edit("❌ حدث خطأ أثناء إنشاء النسخة الاحتياطية.")

async def admin_subscription_settings_handler(event):
    settings = get_admin_settings()

    await event.edit(
        f"⚙️ **إعدادات الاشتراك**\n\n"
        f"القناة المطلوبة: @{settings['required_channel'] or 'غير محددة'}\n"
        f"المجموعة المطلوبة: @{settings['required_group'] or 'غير محددة'}\n\n"
        "اختر الإعداد الذي تريد تعديله:",
        buttons=[
            [Button.inline("📢 تعيين القناة المطلوبة", b"set_required_channel")],
            [Button.inline("👥 تعيين المجموعة المطلوبة", b"set_required_group")],
            [Button.inline("🗑 مسح الإعدادات", b"clear_subscription_settings")],
            [Button.inline("🔙 رجوع", b"admin_panel")]
        ]
    )

async def set_required_channel_handler(event):
    await event.edit("📢 **تعيين القناة المطلوبة**\n\n"
                   "يرجى إرسال يوزر القناة المطلوبة (مثال: channelusername)")

    channel_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
    channel = channel_event.text.strip()

    if not channel:
        await event.respond("❌ يوزر القناة غير صالح.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE admin_settings SET required_channel = ? WHERE id = 1', (channel,))
    conn.commit()
    conn.close()

    await event.edit(f"✅ تم تعيين القناة المطلوبة: @{channel}")

async def set_required_group_handler(event):
    await event.edit("👥 **تعيين المجموعة المطلوبة**\n\n"
                   "يرجى إرسال يوزر المجموعة المطلوبة (مثال: groupusername)")

    group_event = await bot.wait_for([events.NewMessage(from_users=event.sender_id)], timeout=300)
    group = group_event.text.strip()

    if not group:
        await event.respond("❌ يوزر المجموعة غير صالح.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE admin_settings SET required_group = ? WHERE id = 1', (group,))
    conn.commit()
    conn.close()

    await event.edit(f"✅ تم تعيين المجموعة المطلوبة: @{group}")

async def clear_subscription_settings_handler(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE admin_settings SET required_channel = "", required_group = "" WHERE id = 1')
    conn.commit()
    conn.close()

    await event.edit("✅ تم مسح إعدادات الاشتراك.")

@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel_handler(event):
    await event.respond("❌ تم إلغاء العملية.")

async def get_ban_reason(user_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ban_reason FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['ban_reason'] if result and result['ban_reason'] else "غير محدد"

def main():
    logger.info("Starting bot...")
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()
