import os
import asyncio
from telethon import TelegramClient, events, Button
from pyrogram import Client as PyroClient
from pyrogram import filters
from datetime import datetime
import sqlite3

API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8914045842:AAEz6MNsGTShwob_M3H0ECy8eOkl2nT5gno"
ADMINS = 932862531

# Emoji Premium
🎲 = "<tg-emoji emoji-id='5886716969427672960'>🎲</tg-emoji>"
🌿 = "<tg-emoji emoji-id='5886462183377739675'>🌿</tg-emoji>"
👤 = "<tg-emoji emoji-id='5886695331382435915'>👤</tg-emoji>"
🪐 = "<tg-emoji emoji-id='5886449487454416104'>🪐</tg-emoji>"
🔅 = "<tg-emoji emoji-id='5884250988184870485'>🔅</tg-emoji>"
⚡ = "<tg-emoji emoji-id='5886360482847137476'>⚡️</tg-emoji>"
🎸 = "<tg-emoji emoji-id='5886232789174460116'>🎸</tg-emoji>"
🕊 = "<tg-emoji emoji-id='5886408161279090563'>🕊</tg-emoji>"
⚪ = "<tg-emoji emoji-id='5886505777295793908'>⚪️</tg-emoji>"
🦋 = "<tg-emoji emoji-id='5886242543045189717'>🦋</tg-emoji>"
✨ = "<tg-emoji emoji-id='5884015001206791984'>✨</tg-emoji>"
⚡️ = "<tg-emoji emoji-id='5886672924538051950'>⚡️</tg-emoji>"

# Database setup
conn = sqlite3.connect('bot_sessions.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        is_premium INTEGER DEFAULT 0,
        session_string TEXT,
        session_type TEXT,
        hack_commands_enabled INTEGER DEFAULT 0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_settings (
        setting TEXT PRIMARY KEY,
        value TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS hack_commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command_name TEXT UNIQUE,
        command_description TEXT,
        command_code TEXT
    )
''')
conn.commit()

# Default settings
cursor.execute("INSERT OR IGNORE INTO bot_settings VALUES ('mode', 'free')")
cursor.execute("INSERT OR IGNORE INTO bot_settings VALUES ('status', 'running')")
conn.commit()

# Default hack commands
default_commands = [
    ("get_contacts", "استخراج جهات الاتصال", "client.get_contacts()"),
    ("get_dialogs", "استخراج المحادثات", "client.get_dialogs()"),
    ("get_messages", "استخراج الرسائل من محادثة", "client.get_messages(chat_id, limit=100)"),
    ("send_message", "إرسال رسالة", "client.send_message(chat_id, 'Hello!')"),
    ("get_profile", "استخراج معلومات الحساب", "client.get_me()")
]

for cmd in default_commands:
    cursor.execute("INSERT OR IGNORE INTO hack_commands VALUES (NULL, ?, ?, ?)", cmd)
conn.commit()

# Clients
telethon_client = TelegramClient('telethon_session', API_ID, API_HASH)
pyrogram_client = PyroClient('pyrogram_session', api_id=API_ID, api_hash=API_HASH)

# Helper functions
def is_admin(user_id):
    return user_id in ADMINS

def is_premium(user_id):
    cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

def hack_commands_enabled(user_id):
    cursor.execute("SELECT hack_commands_enabled FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

def get_bot_mode():
    cursor.execute("SELECT value FROM bot_settings WHERE setting = 'mode'")
    result = cursor.fetchone()
    return result[0] if result else 'free'

def get_bot_status():
    cursor.execute("SELECT value FROM bot_settings WHERE setting = 'status'")
    result = cursor.fetchone()
    return result[0] if result else 'running'

def set_bot_mode(mode):
    cursor.execute("UPDATE bot_settings SET value = ? WHERE setting = 'mode'", (mode,))
    conn.commit()

def set_bot_status(status):
    cursor.execute("UPDATE bot_settings SET value = ? WHERE setting = 'status'", (status,))
    conn.commit()

def toggle_hack_commands(user_id):
    current_status = hack_commands_enabled(user_id)
    new_status = 0 if current_status else 1
    cursor.execute("UPDATE users SET hack_commands_enabled = ? WHERE user_id = ?", (new_status, user_id))
    conn.commit()
    return new_status

# Start command
@telethon_client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if get_bot_status() == 'stopped' and not is_admin(user_id):
        return await event.respond(f"{✨} البوت متوقف حالياً.")

    buttons = [
        [Button.inline(f"استخراج جلسة تيليثون", b"get_telethon_session")],
        [Button.inline(f"استخراج جلسة بايوجرام", b"get_pyrogram_session")],
        [Button.inline(f"تحويل تيليثون لبايوجرام", b"telethon_to_pyro")],
        [Button.inline(f"تحويل بايوجرام لتيليثون", b"pyro_to_telethon")],
        [Button.inline(f"لوحة التحكم", b"control_panel")]
    ]

    if is_admin(user_id):
        buttons.append([Button.inline(f"لوحة الأدمن", b"admin_panel")])

    if hack_commands_enabled(user_id):
        buttons.append([Button.inline(f"أوامر الاختراق", b"hack_commands")])

    await event.respond(
        f"{✨} مرحبا بك في بوت استخراج الجلسات!\n\n"
        f"{🌿} اختر أحد الخيارات التالية:",
        buttons=buttons
    )

# Session extraction handlers
@telethon_client.on(events.CallbackQuery(data=b"get_telethon_session"))
async def get_telethon_session(event):
    user_id = event.sender_id
    if get_bot_mode() == 'paid' and not is_premium(user_id):
        return await event.edit(f"{✨} هذه الميزة متاحة للمشتركين فقط.")

    await event.edit(f"{💻} جاري استخراج جلسة تيليثون...\n\n"
                    f"{👤} الرجاء إرسال رقم هاتفك بالصيغة الدولية (مثال: +9665xxxxxxxx)")

    phone = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    phone = phone.text.strip()

    try:
        client = TelegramClient(f'session_{user_id}', API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await event.edit(f"{✨} تم إرسال الكود إلى رقمك، الرجاء إرساله هنا.")

            code = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
            code = code.text.strip()

            await client.sign_in(phone, code)
            session_string = client.session.save()
            await client.disconnect()

            cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                          (user_id, is_premium(user_id), session_string, 'telethon', hack_commands_enabled(user_id)))
            conn.commit()

            await event.edit(f"{💻} تم استخراج الجلسة بنجاح!\n\n"
                           f"{👤} جلستك:\n`{session_string}`")
        else:
            session_string = client.session.save()
            await client.disconnect()

            cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                          (user_id, is_premium(user_id), session_string, 'telethon', hack_commands_enabled(user_id)))
            conn.commit()

            await event.edit(f"{💻} تم استخراج الجلسة بنجاح!\n\n"
                           f"{👤} جلستك:\n`{session_string}`")
    except Exception as e:
        await event.edit(f"{⚡} حدث خطأ: {str(e)}")

@telethon_client.on(events.CallbackQuery(data=b"get_pyrogram_session"))
async def get_pyrogram_session(event):
    user_id = event.sender_id
    if get_bot_mode() == 'paid' and not is_premium(user_id):
        return await event.edit(f"{✨} هذه الميزة متاحة للمشتركين فقط.")

    await event.edit(f"{💻} جاري استخراج جلسة بايروغرام...\n\n"
                    f"{👤} الرجاء إرسال رقم هاتفك بالصيغة الدولية (مثال: +9665xxxxxxxx)")

    phone = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    phone = phone.text.strip()

    try:
        client = PyroClient(f'pyro_session_{user_id}', API_ID, API_HASH, phone_number=phone)
        await client.connect()
        sent_code = await client.send_code(phone)
        await event.edit(f"{✨} تم إرسال الكود إلى رقمك، الرجاء إرساله هنا.")

        code = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
        code = code.text.strip()

        await client.sign_in(phone, sent_code.phone_code_hash, code)
        session_string = await client.export_session_string()
        await client.disconnect()

        cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                      (user_id, is_premium(user_id), session_string, 'pyrogram', hack_commands_enabled(user_id)))
        conn.commit()

        await event.edit(f"{💻} تم استخراج الجلسة بنجاح!\n\n"
                       f"{👤} جلستك:\n`{session_string}`")
    except Exception as e:
        await event.edit(f"{⚡} حدث خطأ: {str(e)}")

# Session conversion handlers
@telethon_client.on(events.CallbackQuery(data=b"telethon_to_pyro"))
async def telethon_to_pyro(event):
    user_id = event.sender_id
    if get_bot_mode() == 'paid' and not is_premium(user_id):
        return await event.edit(f"{✨} هذه الميزة متاحة للمشتركين فقط.")

    cursor.execute("SELECT session_string FROM users WHERE user_id = ? AND session_type = 'telethon'", (user_id,))
    result = cursor.fetchone()

    if not result:
        return await event.edit(f"{⚡} لا توجد جلسة تيليثون محفوظة لديك.")

    session_string = result[0]
    await event.edit(f"{💻} جاري تحويل الجلسة...")

    try:
        from telethon.sessions import StringSession
        telethon_client_temp = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await telethon_client_temp.connect()
        pyro_client_temp = PyroClient(":memory:", api_id=API_ID, api_hash=API_HASH, session_string=session_string)
        await pyro_client_temp.start()
        new_session_string = await pyro_client_temp.export_session_string()
        await telethon_client_temp.disconnect()
        await pyro_client_temp.stop()

        cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                      (user_id, is_premium(user_id), new_session_string, 'pyrogram', hack_commands_enabled(user_id)))
        conn.commit()

        await event.edit(f"{💻} تم تحويل الجلسة بنجاح!\n\n"
                       f"{👤} جلستك الجديدة:\n`{new_session_string}`")
    except Exception as e:
        await event.edit(f"{⚡} حدث خطأ: {str(e)}")

@telethon_client.on(events.CallbackQuery(data=b"pyro_to_telethon"))
async def pyro_to_telethon(event):
    user_id = event.sender_id
    if get_bot_mode() == 'paid' and not is_premium(user_id):
        return await event.edit(f"{✨} هذه الميزة متاحة للمشتركين فقط.")

    cursor.execute("SELECT session_string FROM users WHERE user_id = ? AND session_type = 'pyrogram'", (user_id,))
    result = cursor.fetchone()

    if not result:
        return await event.edit(f"{⚡} لا توجد جلسة بايروغرام محفوظة لديك.")

    session_string = result[0]
    await event.edit(f"{💻} جاري تحويل الجلسة...")

    try:
        pyro_client_temp = PyroClient(":memory:", api_id=API_ID, api_hash=API_HASH, session_string=session_string)
        await pyro_client_temp.start()
        from telethon.sessions import StringSession
        telethon_client_temp = TelegramClient(StringSession(), API_ID, API_HASH)
        await telethon_client_temp.connect()
        if not await telethon_client_temp.is_user_authorized():
            await telethon_client_temp.sign_in(bot_token=BOT_TOKEN)
        new_session_string = telethon_client_temp.session.save()
        await telethon_client_temp.disconnect()
        await pyro_client_temp.stop()

        cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                      (user_id, is_premium(user_id), new_session_string, 'telethon', hack_commands_enabled(user_id)))
        conn.commit()

        await event.edit(f"{💻} تم تحويل الجلسة بنجاح!\n\n"
                       f"{👤} جلستك الجديدة:\n`{new_session_string}`")
    except Exception as e:
        await event.edit(f"{⚡} حدث خطأ: {str(e)}")

# Control panel
@telethon_client.on(events.CallbackQuery(data=b"control_panel"))
async def control_panel(event):
    user_id = event.sender_id
    if get_bot_status() == 'stopped' and not is_admin(user_id):
        return await event.edit(f"{✨} البوت متوقف حالياً.")

    buttons = [
        [Button.inline(f"عرض الجلسات المحفوظة", b"show_sessions")],
        [Button.inline(f"حذف الجلسة", b"delete_session")],
        [Button.inline(f"تفعيل/تعطيل أوامر الاختراق", b"toggle_hack_commands")],
        [Button.inline(f"العودة للقائمة الرئيسية", b"start")]
    ]

    await event.edit(
        f"{🌿} لوحة التحكم:\n\n"
        f"{👤} اختر أحد الخيارات التالية:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(data=b"toggle_hack_commands"))
async def toggle_hack_commands_handler(event):
    user_id = event.sender_id
    new_status = toggle_hack_commands(user_id)
    status_text = "مفعل" if new_status else "معطل"
    await event.edit(f"{⚡} تم {'تفعيل' if new_status else 'تعطيل'} أوامر الاختراق.\n\n{🌿} الحالة الحالية: {status_text}")

@telethon_client.on(events.CallbackQuery(data=b"show_sessions"))
async def show_sessions(event):
    user_id = event.sender_id
    cursor.execute("SELECT session_type, session_string FROM users WHERE user_id = ?", (user_id,))
    sessions = cursor.fetchall()

    if not sessions:
        return await event.edit(f"{⚡} لا توجد جلسات محفوظة لديك.")

    message = f"{💻} جلساتك المحفوظة:\n\n"
    for idx, (session_type, session_string) in enumerate(sessions, 1):
        message += f"{👤} {idx}. نوع الجلسة: {session_type}\n{session_string}\n\n"

    await event.edit(message)

@telethon_client.on(events.CallbackQuery(data=b"delete_session"))
async def delete_session(event):
    user_id = event.sender_id
    cursor.execute("SELECT session_type FROM users WHERE user_id = ?", (user_id,))
    sessions = cursor.fetchall()

    if not sessions:
        return await event.edit(f"{⚡} لا توجد جلسات محفوظة لديك.")

    buttons = []
    for session_type in sessions:
        buttons.append([Button.inline(f"حذف جلسة {session_type[0]}", f"confirm_delete_{session_type[0]}".encode())])

    buttons.append([Button.inline(f"إلغاء", b"control_panel")])

    await event.edit(
        f"{🌿} اختر الجلسة التي تريد حذفها:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(pattern=b"confirm_delete_(.*)"))
async def confirm_delete(event):
    session_type = event.data_match.group(1).decode()
    user_id = event.sender_id

    buttons = [
        [Button.inline(f"تأكيد الحذف", f"delete_{session_type}".encode())],
        [Button.inline(f"إلغاء", b"control_panel")]
    ]

    await event.edit(
        f"{⚡} هل أنت متأكد من حذف جلسة {session_type}؟",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(pattern=b"delete_(.*)"))
async def delete(event):
    session_type = event.data_match.group(1).decode()
    user_id = event.sender_id

    cursor.execute("DELETE FROM users WHERE user_id = ? AND session_type = ?", (user_id, session_type))
    conn.commit()

    await event.edit(f"{⚡} تم حذف جلسة {session_type} بنجاح.")

# Hack commands
@telethon_client.on(events.CallbackQuery(data=b"hack_commands"))
async def hack_commands_panel(event):
    user_id = event.sender_id
    if not hack_commands_enabled(user_id):
        return await event.edit(f"{⚡} أوامر الاختراق معطلة. يرجى تفعيلها من لوحة التحكم.")

    cursor.execute("SELECT id, command_name, command_description FROM hack_commands")
    commands = cursor.fetchall()

    buttons = []
    for cmd_id, cmd_name, cmd_desc in commands:
        buttons.append([Button.inline(f"{cmd_name} - {cmd_desc}", f"execute_command_{cmd_id}".encode())])

    buttons.append([Button.inline(f"العودة للقائمة الرئيسية", b"start")])

    await event.edit(
        f"{🎲} أوامر الاختراق:\n\n"
        f"{👤} اختر أمر لتنفيذه على جلستك:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(pattern=b"execute_command_(\d+)"))
async def execute_hack_command(event):
    user_id = event.sender_id
    cmd_id = int(event.data_match.group(1))

    cursor.execute("SELECT session_string, session_type FROM users WHERE user_id = ?", (user_id,))
    session_data = cursor.fetchone()

    if not session_data:
        return await event.edit(f"{⚡} لا توجد جلسة محفوظة لديك.")

    session_string, session_type = session_data

    cursor.execute("SELECT command_name, command_code FROM hack_commands WHERE id = ?", (cmd_id,))
    command_data = cursor.fetchone()

    if not command_data:
        return await event.edit(f"{⚡} الأمر غير موجود.")

    cmd_name, cmd_code = command_data
    await event.edit(f"{🎲} جاري تنفيذ الأمر: {cmd_name}...")

    try:
        if session_type == 'telethon':
            from telethon.sessions import StringSession
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            result = eval(f"await {cmd_code}")
            await client.disconnect()
        else:
            client = PyroClient(":memory:", api_id=API_ID, api_hash=API_HASH, session_string=session_string)
            await client.start()
            result = eval(f"await {cmd_code}")
            await client.stop()

        await event.edit(f"{🎲} نتيجة تنفيذ الأمر:\n\n```{str(result)[:4000]}```")
    except Exception as e:
        await event.edit(f"{⚡} حدث خطأ أثناء التنفيذ: {str(e)}")

# Admin panel
@telethon_client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية للوصول إلى هذه اللوحة.", alert=True)

    buttons = [
        [Button.inline(f"تشغيل/إيقاف البوت", b"toggle_bot_status")],
        [Button.inline(f"تغيير وضع البوت (مجاني/مدفوع)", b"toggle_bot_mode")],
        [Button.inline(f"إدارة المشتركين", b"manage_subscribers")],
        [Button.inline(f"إدارة أوامر الاختراق", b"manage_hack_commands")],
        [Button.inline(f"إحصائيات البوت", b"bot_stats")],
        [Button.inline(f"العودة للقائمة الرئيسية", b"start")]
    ]

    status = "شغال" if get_bot_status() == 'running' else "متوقف"
    mode = "مدفوع" if get_bot_mode() == 'paid' else "مجاني"

    await event.edit(
        f"{🪐} لوحة الأدمن:\n\n"
        f"{🔅} حالة البوت: {status}\n"
        f"{🔅} وضع البوت: {mode}\n\n"
        f"{🌿} اختر أحد الخيارات التالية:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(data=b"toggle_bot_status"))
async def toggle_bot_status(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    current_status = get_bot_status()
    new_status = 'stopped' if current_status == 'running' else 'running'
    set_bot_status(new_status)

    await event.edit(f"{🔅} تم تغيير حالة البوت إلى: {'متوقف' if new_status == 'stopped' else 'شغال'}")

@telethon_client.on(events.CallbackQuery(data=b"toggle_bot_mode"))
async def toggle_bot_mode(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    current_mode = get_bot_mode()
    new_mode = 'paid' if current_mode == 'free' else 'free'
    set_bot_mode(new_mode)

    await event.edit(f"{🔅} تم تغيير وضع البوت إلى: {'مدفوع' if new_mode == 'paid' else 'مجاني'}")

@telethon_client.on(events.CallbackQuery(data=b"manage_subscribers"))
async def manage_subscribers(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    buttons = [
        [Button.inline(f"إضافة مشترك", b"add_subscriber")],
        [Button.inline(f"إزالة مشترك", b"remove_subscriber")],
        [Button.inline(f"قائمة المشتركين", b"list_subscribers")],
        [Button.inline(f"العودة للوحة الأدمن", b"admin_panel")]
    ]

    await event.edit(
        f"{👤} إدارة المشتركين:\n\n"
        f"{🌿} اختر أحد الخيارات التالية:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(data=b"add_subscriber"))
async def add_subscriber(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    await event.edit(f"{👤} أرسل معرف المستخدم الذي تريد إضافته كمشترك (مثال: 123456789)")

    user = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    try:
        subscriber_id = int(user.text.strip())
        cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (subscriber_id,))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO users (user_id, is_premium) VALUES (?, 1)", (subscriber_id,))
        conn.commit()
        await event.edit(f"{👤} تم إضافة المستخدم {subscriber_id} كمشترك بنجاح.")
    except ValueError:
        await event.edit(f"{⚡} معرف المستخدم غير صالح.")

@telethon_client.on(events.CallbackQuery(data=b"remove_subscriber"))
async def remove_subscriber(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    await event.edit(f"{👤} أرسل معرف المستخدم الذي تريد إزالته من المشتركين (مثال: 123456789)")

    user = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    try:
        subscriber_id = int(user.text.strip())
        cursor.execute("UPDATE users SET is_premium = 0 WHERE user_id = ?", (subscriber_id,))
        conn.commit()
        await event.edit(f"{👤} تم إزالة المستخدم {subscriber_id} من المشتركين.")
    except ValueError:
        await event.edit(f"{⚡} معرف المستخدم غير صالح.")

@telethon_client.on(events.CallbackQuery(data=b"list_subscribers"))
async def list_subscribers(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    cursor.execute("SELECT user_id FROM users WHERE is_premium = 1")
    subscribers = cursor.fetchall()

    if not subscribers:
        return await event.edit(f"{👤} لا يوجد مشتركين حالياً.")

    message = f"{👤} قائمة المشتركين ({len(subscribers)}):\n\n"
    for subscriber in subscribers:
        message += f"{subscriber[0]}\n"

    await event.edit(message)

@telethon_client.on(events.CallbackQuery(data=b"manage_hack_commands"))
async def manage_hack_commands(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    buttons = [
        [Button.inline(f"إضافة أمر جديد", b"add_hack_command")],
        [Button.inline(f"تعديل أمر موجود", b"edit_hack_command")],
        [Button.inline(f"حذف أمر", b"delete_hack_command")],
        [Button.inline(f"قائمة الأوامر", b"list_hack_commands")],
        [Button.inline(f"العودة للوحة الأدمن", b"admin_panel")]
    ]

    await event.edit(
        f"{🎲} إدارة أوامر الاختراق:\n\n"
        f"{🌿} اختر أحد الخيارات التالية:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(data=b"add_hack_command"))
async def add_hack_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    await event.edit(f"{🎲} أرسل اسم الأمر الجديد:")

    command_name = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    command_name = command_name.text.strip()

    await event.edit(f"{🎲} أرسل وصف الأمر:")

    command_description = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    command_description = command_description.text.strip()

    await event.edit(f"{🎲} أرسل كود الأمر (استخدم 'client' كمتغير للعميل):")

    command_code = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    command_code = command_code.text.strip()

    try:
        cursor.execute("INSERT INTO hack_commands VALUES (NULL, ?, ?, ?)",
                      (command_name, command_description, command_code))
        conn.commit()
        await event.edit(f"{🎲} تم إضافة الأمر بنجاح!")
    except Exception as e:
        await event.edit(f"{⚡} حدث خطأ: {str(e)}")

@telethon_client.on(events.CallbackQuery(data=b"edit_hack_command"))
async def edit_hack_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    cursor.execute("SELECT id, command_name FROM hack_commands")
    commands = cursor.fetchall()

    if not commands:
        return await event.edit(f"{⚡} لا توجد أوامر لتعديلها.")

    buttons = []
    for cmd_id, cmd_name in commands:
        buttons.append([Button.inline(f"{cmd_name}", f"select_edit_command_{cmd_id}".encode())])

    buttons.append([Button.inline(f"إلغاء", b"manage_hack_commands")])

    await event.edit(
        f"{🎲} اختر الأمر الذي تريد تعديله:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(pattern=b"select_edit_command_(\d+)"))
async def select_edit_command(event):
    cmd_id = int(event.data_match.group(1))
    user_id = event.sender_id

    cursor.execute("SELECT command_name, command_description, command_code FROM hack_commands WHERE id = ?", (cmd_id,))
    command_data = cursor.fetchone()

    if not command_data:
        return await event.edit(f"{⚡} الأمر غير موجود.")

    command_name, command_description, command_code = command_data

    await event.edit(
        f"{🎲} تعديل الأمر: {command_name}\n\n"
        f"اختر ما تريد تعديله:",
        buttons=[
            [Button.inline(f"تعديل الاسم", f"edit_command_name_{cmd_id}".encode())],
            [Button.inline(f"تعديل الوصف", f"edit_command_desc_{cmd_id}".encode())],
            [Button.inline(f"تعديل الكود", f"edit_command_code_{cmd_id}".encode())],
            [Button.inline(f"إلغاء", b"manage_hack_commands")]
        ]
    )

@telethon_client.on(events.CallbackQuery(pattern=b"edit_command_name_(\d+)"))
async def edit_command_name(event):
    cmd_id = int(event.data_match.group(1))
    user_id = event.sender_id

    await event.edit(f"{🎲} أرسل الاسم الجديد للأمر:")

    new_name = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    new_name = new_name.text.strip()

    cursor.execute("UPDATE hack_commands SET command_name = ? WHERE id = ?", (new_name, cmd_id))
    conn.commit()

    await event.edit(f"{🎲} تم تحديث اسم الأمر بنجاح!")

@telethon_client.on(events.CallbackQuery(pattern=b"edit_command_desc_(\d+)"))
async def edit_command_desc(event):
    cmd_id = int(event.data_match.group(1))
    user_id = event.sender_id

    await event.edit(f"{🎲} أرسل الوصف الجديد للأمر:")

    new_desc = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    new_desc = new_desc.text.strip()

    cursor.execute("UPDATE hack_commands SET command_description = ? WHERE id = ?", (new_desc, cmd_id))
    conn.commit()

    await event.edit(f"{🎲} تم تحديث وصف الأمر بنجاح!")

@telethon_client.on(events.CallbackQuery(pattern=b"edit_command_code_(\d+)"))
async def edit_command_code(event):
    cmd_id = int(event.data_match.group(1))
    user_id = event.sender_id

    await event.edit(f"{🎲} أرسل الكود الجديد للأمر (استخدم 'client' كمتغير للعميل):")

    new_code = await telethon_client.wait_for(events.NewMessage(from_users=user_id))
    new_code = new_code.text.strip()

    cursor.execute("UPDATE hack_commands SET command_code = ? WHERE id = ?", (new_code, cmd_id))
    conn.commit()

    await event.edit(f"{🎲} تم تحديث كود الأمر بنجاح!")

@telethon_client.on(events.CallbackQuery(data=b"delete_hack_command"))
async def delete_hack_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    cursor.execute("SELECT id, command_name FROM hack_commands")
    commands = cursor.fetchall()

    if not commands:
        return await event.edit(f"{⚡} لا توجد أوامر لحذفها.")

    buttons = []
    for cmd_id, cmd_name in commands:
        buttons.append([Button.inline(f"{cmd_name}", f"confirm_delete_command_{cmd_id}".encode())])

    buttons.append([Button.inline(f"إلغاء", b"manage_hack_commands")])

    await event.edit(
        f"{🎲} اختر الأمر الذي تريد حذفه:",
        buttons=buttons
    )

@telethon_client.on(events.CallbackQuery(pattern=b"confirm_delete_command_(\d+)"))
async def confirm_delete_command(event):
    cmd_id = int(event.data_match.group(1))
    user_id = event.sender_id

    cursor.execute("SELECT command_name FROM hack_commands WHERE id = ?", (cmd_id,))
    command_name = cursor.fetchone()[0]

    await event.edit(
        f"{⚡} هل أنت متأكد من حذف الأمر: {command_name}?",
        buttons=[
            [Button.inline(f"تأكيد الحذف", f"delete_command_{cmd_id}".encode())],
            [Button.inline(f"إلغاء", b"manage_hack_commands")]
        ]
    )

@telethon_client.on(events.CallbackQuery(pattern=b"delete_command_(\d+)"))
async def delete_command(event):
    cmd_id = int(event.data_match.group(1))
    user_id = event.sender_id

    cursor.execute("DELETE FROM hack_commands WHERE id = ?", (cmd_id,))
    conn.commit()

    await event.edit(f"{⚡} تم حذف الأمر بنجاح!")

@telethon_client.on(events.CallbackQuery(data=b"list_hack_commands"))
async def list_hack_commands(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    cursor.execute("SELECT id, command_name, command_description FROM hack_commands")
    commands = cursor.fetchall()

    if not commands:
        return await event.edit(f"{⚡} لا توجد أوامر حالياً.")

    message = f"{🎲} قائمة أوامر الاختراق ({len(commands)}):\n\n"
    for cmd_id, cmd_name, cmd_desc in commands:
        message += f"{cmd_id}. {cmd_name} - {cmd_desc}\n"

    await event.edit(message)

@telethon_client.on(events.CallbackQuery(data=b"bot_stats"))
async def bot_stats(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.answer("ليس لديك صلاحية.", alert=True)

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
    premium_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM hack_commands")
    total_commands = cursor.fetchone()[0]

    status = "شغال" if get_bot_status() == 'running' else "متوقف"
    mode = "مدفوع" if get_bot_mode() == 'paid' else "مجاني"

    await event.edit(
        f"{🪐} إحصائيات البوت:\n\n"
        f"{🔅} حالة البوت: {status}\n"
        f"{🔅} وضع البوت: {mode}\n"
        f"{👤} إجمالي المستخدمين: {total_users}\n"
        f"{✨} المشتركين: {premium_users}\n"
        f"{🎲} أوامر الاختراق: {total_commands}"
    )

# Run the bot
async def main():
    await telethon_client.start(bot_token=BOT_TOKEN)
    print("Bot is running...")
    await telethon_client.run_until_disconnected()

if __name__ == '__main__':
    from telethon.sessions import StringSession
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
