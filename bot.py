import os
import asyncio
import sqlite3
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import LeaveChannelRequest, GetParticipantRequest, JoinChannelRequest
from telethon.tl.functions.messages import DeleteHistoryRequest, ImportChatInviteRequest
from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantAdmin
from telethon.errors import UserNotParticipantError, InviteHashInvalidError
from dotenv import load_dotenv

load_dotenv()

API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
DEVELOPER = "Programmer_error"
FORCE_CHANNEL = "Programmer_error1"
FORCE_GROUP = "Programmer_error2"
ADMIN_ID = 932862531

# الايموجي البريميوم
PC = '<tg-emoji emoji-id="5886664420502805908">💻</tg-emoji>'
DICE = '<tg-emoji emoji-id="5886716969427672960">🎲</tg-emoji>'
LEAF = '<tg-emoji emoji-id="5886462183377739675">🌿</tg-emoji>'
USER = '<tg-emoji emoji-id="5886695331382435915">👤</tg-emoji>'
PLANET = '<tg-emoji emoji-id="5886449487454416104">🪐</tg-emoji>'
SPARK = '<tg-emoji emoji-id="5884250988184870485">🔅</tg-emoji>'
BOLT = '<tg-emoji emoji-id="5886360482847137476">⚡️</tg-emoji>'
GUITAR = '<tg-emoji emoji-id="5886232789174460116">🎸</tg-emoji>'
DOVE = '<tg-emoji emoji-id="5886408161279090563">🕊</tg-emoji>'
CIRCLE = '<tg-emoji emoji-id="5886505777295793908">⚪️</tg-emoji>'
BUTTERFLY = '<tg-emoji emoji-id="5886242543045189717">🦋</tg-emoji>'
STAR = '<tg-emoji emoji-id="5884015001206791984">✨</tg-emoji>'
LIGHTNING = '<tg-emoji emoji-id="5886672924538051950">⚡️</tg-emoji>'
LOCK = '<tg-emoji emoji-id="5886249404544443212">🔒</tg-emoji>'
CHECK = '<tg-emoji emoji-id="5886345304115969449">✅</tg-emoji>'
ROCKET = '<tg-emoji emoji-id="5886426509378198">🚀</tg-emoji>'
CAT = '<tg-emoji emoji-id="5886470240736387171">🐈</tg-emoji>'
SIGNAL = '<tg-emoji emoji-id="5886386768046988787">📶</tg-emoji>'

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}
waiting_state = {}
banned_users = set()

# قاعدة البيانات
conn = sqlite3.connect('database.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, phone TEXT, session TEXT, join_date TEXT)''')
cur.execute('''CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)''')
cur.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, total_clean INTEGER DEFAULT 0)''')
cur.execute('INSERT OR IGNORE INTO stats (id) VALUES (1)')
conn.commit()

for row in cur.execute('SELECT user_id FROM banned'):
    banned_users.add(row[0])

async def save_user(user_id, phone, session_str):
    cur.execute('INSERT OR REPLACE INTO users VALUES (?,?,?,?)',
                (user_id, phone, session_str, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_user_info(user_id):
    cur.execute('SELECT phone, session, join_date FROM users WHERE user_id=?', (user_id,))
    return cur.fetchone()

def ban_user(user_id):
    banned_users.add(user_id)
    cur.execute('INSERT OR REPLACE INTO banned VALUES (?)', (user_id,))
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
        [Button.url("📢 قناة السورس", f"https://t.me/{FORCE_CHANNEL}")],
        [Button.url("👥 جروب السورس", f"https://t.me/{FORCE_GROUP}")],
        [Button.inline("✅ تحققت", b"check_sub")]
    ]

def main_menu(user_id):
    buttons = [
        [Button.inline("➕ إضافة حساب برقم", b"add_phone")],
        [Button.inline("📋 إضافة حساب بسيشن", b"add_session")],
        [Button.inline("🧹 قائمة التنظيف", b"clean_menu")],
        [Button.inline("📥 جلب الروابط", b"fetch_menu")],
        [Button.inline("➡️ انضمام تلقائي", b"join_menu")],
        [Button.inline("👤 معلومات حسابي", b"my_info")],
        [Button.inline("⭐ المميزات", b"features")],
        [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([Button.inline("⚙️ لوحة الأدمن", b"admin_panel")])
    return buttons

def clean_menu_buttons():
    return [
        [Button.inline("💬 تنظيف الخاص", b"clean_private")],
        [Button.inline("👥 تنظيف الجروبات", b"clean_groups")],
        [Button.inline("📢 تنظيف القنوات", b"clean_channels")],
        [Button.inline("🤖 تنظيف البوتات", b"clean_bots")],
        [Button.inline("💣 تنظيف الكل", b"clean_all")],
        [Button.inline("🗑️ حذف الحساب", b"del_account")],
        [Button.inline("🔙 رجوع", b"back")]
    ]

def fetch_menu_buttons():
    return [
        [Button.inline("📢 جلب قنوات", b"fetch_channels")],
        [Button.inline("👥 جلب جروبات", b"fetch_groups")],
        [Button.inline("🤖 جلب بوتات", b"fetch_bots")],
        [Button.inline("📋 جلب الكل", b"fetch_all")],
        [Button.inline("🔙 رجوع", b"back")]
    ]

def join_menu_buttons():
    return [
        [Button.inline("📢 انضمام قنوات", b"join_channels")],
        [Button.inline("👥 انضمام جروبات", b"join_groups")],
        [Button.inline("🔙 رجوع", b"back")]
    ]

def admin_panel_buttons():
    return [
        [Button.inline("📊 احصائيات", b"admin_stats")],
        [Button.inline("👥 كل المستخدمين", b"admin_users")],
        [Button.inline("🔍 بحث مستخدم", b"admin_search")],
        [Button.inline("🚫 حظر مستخدم", b"admin_ban")],
        [Button.inline("✅ الغاء حظر", b"admin_unban")],
        [Button.inline("📢 اذاعة", b"admin_broadcast")],
        [Button.inline("💾 نسخة احتياطية", b"admin_backup")],
        [Button.inline("🔙 رجوع", b"back")]
    ]

async def check_account(event):
    uid = event.sender_id
    if uid in banned_users:
        await event.answer(f"{STAR}{LOCK} انت محظور{STAR}", alert=True)
        return None
    if not await check_subscription(uid):
        await event.edit(f"{STAR}{LOCK} <b>اشتراك إجباري</b> {LOCK}{STAR}", buttons=force_sub_buttons(), parse_mode='html')
        return None
    if uid not in user_sessions:
        await event.answer(f"{STAR}{USER} ضيف حسابك الأول{STAR}", alert=True)
        return None
    return user_sessions[uid]["client"]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    
    # تحقق الحظر الاول
    if uid in banned_users:
        return await event.respond(f"{STAR}{LOCK} انت محظور من البوت{STAR}")

    # اشعار دخول للادمن
    if uid!= ADMIN_ID:
        try:
            user = await event.get_sender()
            await bot.send_message(ADMIN_ID, f"{STAR}{DOVE} دخول جديد{STAR}\n{STAR}الاسم: {user.first_name}\nالايدي: {uid}\nاليوزر: @{user.username or 'لا يوجد'}{STAR}")
        except: pass

    # تحقق الاشتراك
    if not await check_subscription(uid):
        return await event.respond(
            f"{STAR}{PLANET} <b>مرحباً بك في بوت التنظيف الاحترافي</b> {PLANET}{STAR}\n\n"
            f"{STAR}اشترك في القناة والجروب لفتح البوت{STAR}",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    try:
        user = await event.get_sender()
        name_user = user.first_name if user.first_name else "مستخدم"

        welcome_text = (
            f"{STAR}{ROCKET} <b>أهلاً {name_user}</b> {ROCKET}{STAR}\n\n"
            f"{STAR}{PLANET} بوت تنظيف الحسابات الاحترافي{STAR}\n\n"
            f"{STAR}{BOLT} سريع وآمن 100%{STAR}\n\n"
            f"{STAR}{SIGNAL} ابدأ باضافة حسابك{STAR}"
        )

        await event.respond(welcome_text, buttons=main_menu(), parse_mode='html')
    except Exception as e:
        # لو حصل اي خطأ ابعت رسالة بسيطة عشان البوت ميقعش
        await event.respond(f"{STAR}البوت جاهز{STAR}", buttons=main_menu())
        
@bot.on(events.CallbackQuery(data=b"check_sub"))
async def check_sub(event):
    if await check_subscription(event.sender_id):
        await event.edit(f"{STAR}{CHECK} <b>تم التحقق</b> {CHECK}{STAR}", buttons=main_menu(event.sender_id), parse_mode='html')
    else:
        await event.answer(f"{STAR}{LOCK} لسه مشتركتش{STAR}", alert=True)

@bot.on(events.CallbackQuery(data=b"my_info"))
async def my_info(event):
    uid = event.sender_id
    if uid not in user_sessions:
        return await event.answer(f"{STAR}مفيش حساب مضاف{STAR}", alert=True)
    info = get_user_info(uid)
    phone = info[0] if info else "غير معروف"
    session = info[1] if info else "غير معروف"
    date = info[2] if info else "غير معروف"
    session_short = session[:25] + "..." if len(session) > 25 else session
    text = f"{STAR}{USER} <b>معلومات حسابك</b> {USER}{STAR}\n\n{STAR}الرقم: {phone}{STAR}\n{STAR}السيشن: `{session_short}`{STAR}\n{STAR}التاريخ: {date}{STAR}"
    await event.edit(text, buttons=[[Button.inline("🔙 رجوع", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"add_phone"))
async def add_phone(event):
    if not await check_subscription(event.sender_id): return
    waiting_state[event.sender_id] = "phone"
    await event.edit(f"{STAR}{USER} ابعت رقمك: +2010xxxxxxx{STAR}\n{STAR}او /cancel{STAR}")

@bot.on(events.CallbackQuery(data=b"add_session"))
async def add_session(event):
    if not await check_subscription(event.sender_id): return
    waiting_state[event.sender_id] = "session"
    await event.edit(f"{STAR}{PC} ابعت Session String{STAR}\n{STAR}او /cancel{STAR}")

@bot.on(events.NewMessage(func=lambda e: e.sender_id in waiting_state))
async def handle_input(event):
    uid = event.sender_id
    if event.text == '/cancel':
        del waiting_state[uid]
        await event.reply(f"{STAR}تم الإلغاء{STAR}", buttons=main_menu(uid))
        return
    state = waiting_state[uid]
    if state == "phone":
        del waiting_state[uid]
        await add_account_phone(event, event.text)
    elif state == "session":
        del waiting_state[uid]
        await add_account_session(event, event.text)

async def add_account_phone(event, phone):
    msg = await event.reply(f"{STAR}{SIGNAL} جاري ارسال الكود...{STAR}")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    client._init_request.app_version = "iPhone 17 Pro"
    client._init_request.device_model = "iPhone 17 Pro"
    client._init_request.system_version = "iOS 18.0"
    await client.connect()
    try:
        await client.send_code_request(phone)
        waiting_state[event.sender_id] = {"step": "code", "client": client, "phone": phone}
        await msg.edit(f"{STAR}ابعت كود التفعيل{STAR}")
    except Exception as e:
        await msg.edit(f"{STAR}خطأ: {e}{STAR}")

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
            await save_user(event.sender_id, phone, session_str)
            del waiting_state[event.sender_id]
            await event.reply(f"{STAR}{CHECK} تم الربط بنجاح{STAR}\n{STAR}الرقم: {phone}{STAR}", buttons=clean_menu_buttons())
        except:
            waiting_state[event.sender_id]["step"] = "password"
            await event.reply(f"{STAR}{LOCK} ابعت كلمة سر التحقق{STAR}")

@bot.on(events.NewMessage(func=lambda e: e.sender_id in waiting_state and isinstance(waiting_state[e.sender_id], dict) and waiting_state[e.sender_id].get("step")=="password"))
async def handle_password(event):
    data = waiting_state[event.sender_id]
    client, phone = data["client"], data["phone"]
    try:
        await client.sign_in(password=event.text)
        me = await client.get_me()
        session_str = client.session.save()
        user_sessions[event.sender_id] = {"client": client, "phone": phone, "user_id": me.id}
        await save_user(event.sender_id, phone, session_str)
        del waiting_state[event.sender_id]
        await event.reply(f"{STAR}{CHECK} تم الربط بنجاح{STAR}", buttons=clean_menu_buttons())
    except Exception as e:
        await event.reply(f"{STAR}خطأ: {e}{STAR}")

async def add_account_session(event, session_str):
    msg = await event.reply(f"{STAR}{PC} جاري فحص السيشن...{STAR}")
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        client._init_request.app_version = "iPhone 17 Pro"
        client._init_request.device_model = "iPhone 17 Pro"
        client._init_request.system_version = "iOS 18.0"
        await client.connect()
        if not await client.is_user_authorized():
            return await msg.edit(f"{STAR}السيشن منتهي{STAR}")
        me = await client.get_me()
        user_sessions[event.sender_id] = {"client": client, "phone": me.phone, "user_id": me.id}
        await save_user(event.sender_id, me.phone, session_str)
        await msg.edit(f"{STAR}{CHECK} تم الربط بنجاح{STAR}\n{STAR}الاسم: {me.first_name}{STAR}", buttons=clean_menu_buttons())
    except Exception as e:
        await msg.edit(f"{STAR}خطأ: {e}{STAR}")

@bot.on(events.CallbackQuery(data=b"clean_menu"))
async def clean_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit(f"{STAR}{PLANET} <b>اختر التنظيف</b> {PLANET}{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_private"))
async def clean_private(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}{CAT} جاري حذف الخاص...{STAR}", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"{STAR}{CAT} تم: {count}{STAR}", parse_mode='html')
                await asyncio.sleep(1.5)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى: {count} محادثة{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_groups"))
async def clean_groups(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}{USER} جاري فحص الجروبات...{STAR}", parse_mode='html')
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
                await msg.edit(f"{STAR}{USER} خرجت: {left} | تخطيت: {skipped}{STAR}", parse_mode='html')
                await asyncio.sleep(2)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى: خرجت {left} | سبت {skipped}{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_channels"))
async def clean_channels(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}{PLANET} جاري فحص القنوات...{STAR}", parse_mode='html')
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
                await msg.edit(f"{STAR}{PLANET} خرجت: {left} | تخطيت: {skipped}{STAR}", parse_mode='html')
                await asyncio.sleep(2)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى: خرجت {left} | سبت {skipped}{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_bots"))
async def clean_bots(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}{PC} جاري حذف البوتات...{STAR}", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"{STAR}{PC} تم: {count}{STAR}", parse_mode='html')
                await asyncio.sleep(1)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى: {count} بوت{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_all"))
async def clean_all(event):
    client = await check_account(event)
    if not client: return
    buttons = [[Button.inline("✅ متأكد", b"confirm_all")], [Button.inline("❌ إلغاء", b"clean_menu")]]
    await event.edit(f"{STAR}{BOLT} <b>تحذير: هيمسح الكل</b> {BOLT}{STAR}", buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"confirm_all"))
async def confirm_all(event):
    await event.edit(f"{STAR}{ROCKET} بدء التنظيف...{STAR}", parse_mode='html')
    await clean_channels(event); await asyncio.sleep(3)
    await clean_groups(event); await asyncio.sleep(3)
    await clean_private(event); await asyncio.sleep(3)
    await clean_bots(event)
    await event.respond(f"{STAR}{CHECK} تم التنظيف الكامل{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"fetch_menu"))
async def fetch_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit(f"{STAR}{DICE} اختر ما تريد جلبه{STAR}", buttons=fetch_menu_buttons(), parse_mode='html')

async def fetch_and_send(event, filter_func, name):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}جاري جلب {name}...{STAR}", parse_mode='html')
    links = []
    async for dialog in client.iter_dialogs():
        if filter_func(dialog) and dialog.entity.username:
            links.append(f"https://t.me/{dialog.entity.username}")
    if len(links) > 50:
        file = f"{name}_{event.sender_id}.txt"
        with open(file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(links))
        await bot.send_file(event.sender_id, file, caption=f"{STAR}عدد {name}: {len(links)}{STAR}")
        os.remove(file)
        await msg.delete()
    else:
        await msg.edit(f"{STAR}{name}:\n" + '\n'.join(links) + f"\n\n{STAR}العدد: {len(links)}{STAR}")

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
    await event.edit(f"{STAR}{ROCKET} ابعت الروابط/اليوزر/الايدي كل سطر{STAR}\n{STAR}حتى 1000 رابط{STAR}")

@bot.on(events.NewMessage(func=lambda e: waiting_state.get(e.sender_id)=="join_links"))
async def handle_join(event):
    client = user_sessions[event.sender_id]["client"]
    links = event.text.split('\n')
    msg = await event.reply(f"{STAR}جاري الانضمام...{STAR}")
    success, fail = 0, 0
    for link in links[:1000]:
        link = link.strip()
        if not link: continue
        try:
            if "t.me/joinchat/" in link or "t.me/+" in link:
                hash = link.split('/')[-1]
                await client(ImportChatInviteRequest(hash))
            else:
                username = link.replace("https://t.me/", "").replace("@", "")
                await client(JoinChannelRequest(username))
            success += 1
            await asyncio.sleep(3)
        except:
            fail += 1
            await asyncio.sleep(2)
    del waiting_state[event.sender_id]
    await msg.edit(f"{STAR}{CHECK} انتهى{STAR}\n{STAR}نجح: {success}\nفشل: {fail}{STAR}", buttons=join_menu_buttons())

@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id!= ADMIN_ID: return
    await event.edit(f"{STAR}{PC} <b>لوحة الأدمن</b> {PC}{STAR}", buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_stats"))
async def admin_stats(event):
    if event.sender_id!= ADMIN_ID: return
    cur.execute('SELECT COUNT(*) FROM users')
    total_users = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM banned')
    banned_count = cur.fetchone()[0]
    cur.execute('SELECT total_clean FROM stats WHERE id=1')
    total_clean = cur.fetchone()[0]
    text = f"{STAR}{BOLT} <b>الاحصائيات</b> {BOLT}{STAR}\n\n{STAR}المستخدمين: {total_users}{STAR}\n{STAR}المحظورين: {banned_count}{STAR}\n{STAR}العمليات: {total_clean}{STAR}"
    await event.edit(text, buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_users"))
async def admin_users(event):
    if event.sender_id!= ADMIN_ID: return
    cur.execute('SELECT user_id, phone FROM users')
    users = cur.fetchall()
    if not users:
        return await event.edit(f"{STAR}مفيش مستخدمين{STAR}", buttons=admin_panel_buttons())
    text = f"{STAR}{USER} <b>المستخدمين</b> {USER}{STAR}\n\n"
    for uid, phone in users[:30]:
        status = "🚫" if uid in banned_users else "✅"
        text += f"{STAR}{status} {uid} | {phone}{STAR}\n"
    await event.edit(text, buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_search"))
async def admin_search(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "search_user"
    await event.edit(f"{STAR}ابعت ايدي المستخدم{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_ban"))
async def admin_ban(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "ban_user"
    await event.edit(f"{STAR}ابعت ايدي المستخدم للحظر{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_unban"))
async def admin_unban(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "unban_user"
    await event.edit(f"{STAR}ابعت ايدي المستخدم لفك الحظر{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_broadcast(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "broadcast"
    await event.edit(f"{STAR}ابعت الرسالة للإذاعة{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_backup"))
async def admin_backup(event):
    if event.sender_id!= ADMIN_ID: return
    await event.edit(f"{STAR}{PC} جاري انشاء النسخة...{STAR}")
    await bot.send_file(event.sender_id, 'database.db', caption=f"{STAR}نسخة {datetime.now().strftime('%Y-%m-%d %H:%M')}{STAR}")

@bot.on(events.NewMessage(func=lambda e: e.sender_id == ADMIN_ID and e.sender_id in waiting_state))
async def admin_handler(event):
    state = waiting_state[event.sender_id]
    if state == "search_user":
        try:
            uid = int(event.text)
            info = get_user_info(uid)
            if info:
                status = "🚫 محظور" if uid in banned_users else "✅ شغال"
                text = f"{STAR}{USER} <b>معلومات</b> {USER}{STAR}\n{STAR}الايدي: {uid}{STAR}\n{STAR}الرقم: {info[0]}{STAR}\n{STAR}السيشن: `{info[1]}`{STAR}\n{STAR}التاريخ: {info[2]}{STAR}\n{STAR}الحالة: {status}{STAR}"
            else:
                text = f"{STAR}غير موجود{STAR}"
            del waiting_state[event.sender_id]
            await event.reply(text, parse_mode='html', buttons=admin_panel_buttons())
        except:
            await event.reply(f"{STAR}ايدي غلط{STAR}")
    elif state == "ban_user":
        try:
            uid = int(event.text)
            ban_user(uid)
            del waiting_state[event.sender_id]
            await event.reply(f"{STAR}{LOCK} تم حظر {uid}{STAR}", buttons=admin_panel_buttons())
            try: await bot.send_message(uid, f"{STAR}{LOCK} تم حظرك{STAR}")
            except: pass
        except:
            await event.reply(f"{STAR}ايدي غلط{STAR}")
    elif state == "unban_user":
        try:
            uid = int(event.text)
            unban_user(uid)
            del waiting_state[event.sender_id]
            await event.reply(f"{STAR}{CHECK} تم فك الحظر {uid}{STAR}", buttons=admin_panel_buttons())
        except:
            await event.reply(f"{STAR}ايدي غلط{STAR}")
    elif state == "broadcast":
        msg = event.text
        del waiting_state[event.sender_id]
        cur.execute('SELECT user_id FROM users')
        sent = 0
        for (uid,) in cur.fetchall():
            try:
                await bot.send_message(uid, f"{STAR}{BOLT} <b>اذاعة</b> {BOLT}{STAR}\n\n{msg}", parse_mode='html')
                sent += 1
                await asyncio.sleep(0.1)
            except: pass
        await event.reply(f"{STAR}{CHECK} تم الارسال لـ {sent}{STAR}", buttons=admin_panel_buttons())

@bot.on(events.CallbackQuery(data=b"del_account"))
async def del_account(event):
    if event.sender_id in user_sessions:
        await user_sessions[event.sender_id]["client"].disconnect()
        del user_sessions[event.sender_id]
        cur.execute('DELETE FROM users WHERE user_id=?', (event.sender_id,))
        conn.commit()
        await event.edit(f"{STAR}{CHECK} تم الحذف{STAR}", buttons=main_menu(event.sender_id))
    else:
        await event.answer(f"{STAR}مفيش حساب{STAR}", alert=True)

@bot.on(events.CallbackQuery(data=b"features"))
async def features(event):
    if not await check_subscription(event.sender_id): return
    text = f"{STAR}{BOLT} <b>مميزات</b> {BOLT}{STAR}\n\n{STAR}{LOCK} امان كامل{STAR}\n{STAR}{ROCKET} سرعة عالية{STAR}\n{STAR}{DICE} جلب روابط{STAR}\n{STAR}{ROCKET} انضمام تلقائي{STAR}\n{STAR}{PC} لوحة ادمن{STAR}"
    await event.edit(text, buttons=[[Button.inline("🔙 رجوع", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event):
    await event.edit(f"{STAR}{PLANET} <b>الرئيسية</b> {PLANET}{STAR}", buttons=main_menu(event.sender_id), parse_mode='html')

print("Bot is running...")
bot.run_until_disconnected()
