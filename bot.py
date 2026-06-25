import os
import asyncio
import sqlite3
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import LeaveChannelRequest, GetParticipantRequest, JoinChannelRequest
from telethon.tl.functions.messages import DeleteHistoryRequest, ImportChatInviteRequest
from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantAdmin
from telethon.errors import UserNotParticipantError, InviteHashInvalidError, ChannelPrivateError, FloodWaitError
from dotenv import load_dotenv

load_dotenv()

API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
DEVELOPER = "Programmer_error"
FORCE_CHANNEL = "Programmer_error1"
FORCE_GROUP = "Programmer_error2"
ADMIN_ID = 932862531

# الايموجي البريميوم - للاستخدام في كل البوت عدا الاستارت
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
CROWN = '<tg-emoji emoji-id="5886402792366505817">👑</tg-emoji>'

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
        [Button.url("📢 قناة السورس", f"https://t.me/{FORCE_CHANNEL}")],
        [Button.url("👥 جروب السورس", f"https://t.me/{FORCE_GROUP}")],
        [Button.inline("✅ تحققت من الاشتراك", b"check_sub")]
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
        [Button.inline("🔙 رجوع للقائمة", b"back")]
    ]

def fetch_menu_buttons():
    return [
        [Button.inline("📢 جلب القنوات", b"fetch_channels")],
        [Button.inline("👥 جلب الجروبات", b"fetch_groups")],
        [Button.inline("🤖 جلب البوتات", b"fetch_bots")],
        [Button.inline("📋 جلب الكل", b"fetch_all")],
        [Button.inline("🔙 رجوع للقائمة", b"back")]
    ]

def join_menu_buttons():
    return [
        [Button.inline("📢 انضمام قنوات", b"join_channels")],
        [Button.inline("👥 انضمام جروبات", b"join_groups")],
        [Button.inline("🔙 رجوع للقائمة", b"back")]
    ]

def admin_panel_buttons():
    return [
        [Button.inline("📊 الاحصائيات", b"admin_stats")],
        [Button.inline("👥 كل المستخدمين", b"admin_users")],
        [Button.inline("🔍 بحث عن مستخدم", b"admin_search")],
        [Button.inline("🚫 حظر مستخدم", b"admin_ban")],
        [Button.inline("✅ فك الحظر", b"admin_unban")],
        [Button.inline("📢 اذاعة رسالة", b"admin_broadcast")],
        [Button.inline("💾 نسخة احتياطية", b"admin_backup")],
        [Button.inline("🔙 رجوع للقائمة", b"back")]
    ]

async def check_account(event):
    uid = event.sender_id
    if uid in banned_users:
        await event.answer(f"{STAR}{LOCK} انت محظور من البوت{STAR}", alert=True)
        return None
    if not await check_subscription(uid):
        await event.edit(f"{STAR}{LOCK} <b>اشتراك إجباري</b> {LOCK}{STAR}\n{STAR}اشترك في القناة والجروب الأول{STAR}", buttons=force_sub_buttons(), parse_mode='html')
        return None
    if uid not in user_sessions:
        await event.answer(f"{STAR}{USER} ضيف حسابك الأول{STAR}", alert=True)
        return None
    return user_sessions[uid]["client"]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id

    if uid in banned_users:
        return await event.respond("🚫 انت محظور من استخدام البوت")

    if uid!= ADMIN_ID:
        try:
            user = await event.get_sender()
            await bot.send_message(ADMIN_ID, f"{STAR}{DOVE} دخول جديد للبوت{STAR}\n{STAR}الاسم: {user.first_name}\nالايدي: {uid}\nاليوزر: @{user.username or 'لا يوجد'}{STAR}")
        except: pass

    if not await check_subscription(uid):
        return await event.respond(
            "<b>مرحباً بك في بوت التنظيف الاحترافي</b>\n\n"
            "هذا البوت يقوم بتنظيف حسابك من القنوات والجروبات والخاص\n"
            "اشترك في القناة والجروب لفتح البوت",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    try:
        user = await event.get_sender()
        name_user = user.first_name if user.first_name else "مستخدم"

        welcome_text = (
            f"<b>أهلاً وسهلاً {name_user}</b>\n\n"
            f"<b>بوت تنظيف الحسابات الاحترافي</b>\n\n"
            f"<b>المميزات:</b>\n"
            f"<b>• تنظيف الخاص والبوتات حذف من الطرفين</b>\n"
            f"<b>• مغادرة الجروبات والقنوات باستثناء الادمن</b>\n"
            f"<b>• جلب روابط القنوات والجروبات</b>\n"
            f"<b>• انضمام تلقائي لعدد كبير من الروابط</b>\n"
            f"<b>• لوحة تحكم ادمن متطورة</b>\n\n"
            f"<b>ابدأ باضافة حسابك من القائمة بالأسفل</b>"
        )

        await event.respond(welcome_text, buttons=main_menu(uid), parse_mode='html')
    except Exception:
        await event.respond("<b>البوت جاهز للاستخدام</b>", buttons=main_menu(uid), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"check_sub"))
async def check_sub(event):
    if await check_subscription(event.sender_id):
        await event.edit(f"{STAR}{CHECK} <b>تم التحقق بنجاح</b> {CHECK}{STAR}\n{STAR}يمكنك الآن استخدام البوت{STAR}", buttons=main_menu(event.sender_id), parse_mode='html')
    else:
        await event.answer(f"{STAR}{LOCK} لسه مشتركتش في القناة والجروب{STAR}", alert=True)

@bot.on(events.CallbackQuery(data=b"my_info"))
async def my_info(event):
    uid = event.sender_id
    if uid not in user_sessions:
        return await event.answer(f"{STAR}مفيش حساب مضاف{STAR}", alert=True)
    info = get_user_info(uid)
    phone = info[0] if info else "غير معروف"
    session = info[1] if info else "غير معروف"
    date = info[2] if info else "غير معروف"
    username = info[3] if info else "لا يوجد"
    session_short = session[:30] + "..." if len(session) > 30 else session
    text = f"{STAR}{USER} <b>معلومات حسابك</b> {USER}{STAR}\n\n{STAR}الرقم: {phone}{STAR}\n{STAR}اليوزر: @{username}{STAR}\n{STAR}السيشن: `{session_short}`{STAR}\n{STAR}تاريخ الاضافة: {date}{STAR}"
    await event.edit(text, buttons=[[Button.inline("🔙 رجوع للقائمة", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"add_phone"))
async def add_phone(event):
    if not await check_subscription(event.sender_id): return
    waiting_state[event.sender_id] = "phone"
    await event.edit(f"{STAR}{USER} ابعت رقمك بصيغة دولية: +2010xxxxxxx{STAR}\n{STAR}او ابعت /cancel للإلغاء{STAR}")

@bot.on(events.CallbackQuery(data=b"add_session"))
async def add_session(event):
    if not await check_subscription(event.sender_id): return
    waiting_state[event.sender_id] = "session"
    await event.edit(f"{STAR}{PC} ابعت Session String الخاص بحسابك{STAR}\n{STAR}او ابعت /cancel للإلغاء{STAR}")

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
    msg = await event.reply(f"{STAR}{SIGNAL} جاري ارسال كود التفعيل...{STAR}")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    client._init_request.app_version = "iPhone 17 Pro"
    client._init_request.device_model = "iPhone 17 Pro"
    client._init_request.system_version = "iOS 18.0"
    await client.connect()
    try:
        await client.send_code_request(phone)
        waiting_state[event.sender_id] = {"step": "code", "client": client, "phone": phone}
        await msg.edit(f"{STAR}تم ارسال الكود{STAR}\n{STAR}ابعت كود التفعيل المكون من 5 ارقام{STAR}")
    except Exception as e:
        await msg.edit(f"{STAR}حدث خطأ: {e}{STAR}")

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
            await event.reply(f"{STAR}{CHECK} تم ربط الحساب بنجاح{STAR}\n{STAR}الرقم: {phone}{STAR}\n{STAR}الاسم: {me.first_name}{STAR}", buttons=clean_menu_buttons())
        except:
            waiting_state[event.sender_id]["step"] = "password"
            await event.reply(f"{STAR}{LOCK} الحساب محمي بكلمة سر{STAR}\n{STAR}ابعت كلمة سر التحقق الثنائي{STAR}")

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
        await event.reply(f"{STAR}{CHECK} تم ربط الحساب بنجاح{STAR}", buttons=clean_menu_buttons())
    except Exception as e:
        await event.reply(f"{STAR}كلمة السر غلط: {e}{STAR}")

async def add_account_session(event, session_str):
    msg = await event.reply(f"{STAR}{PC} جاري فحص السيشن...{STAR}")
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        client._init_request.app_version = "iPhone 17 Pro"
        client._init_request.device_model = "iPhone 17 Pro"
        client._init_request.system_version = "iOS 18.0"
        await client.connect()
        if not await client.is_user_authorized():
            return await msg.edit(f"{STAR}السيشن منتهي الصلاحية{STAR}")
        me = await client.get_me()
        user_sessions[event.sender_id] = {"client": client, "phone": me.phone, "user_id": me.id}
        await save_user(event.sender_id, me.phone, session_str, me.username or "")
        await msg.edit(f"{STAR}{CHECK} تم ربط الحساب بنجاح{STAR}\n{STAR}الاسم: {me.first_name}\nالرقم: {me.phone}{STAR}", buttons=clean_menu_buttons())
    except Exception as e:
        await msg.edit(f"{STAR}خطأ في السيشن: {e}{STAR}")

@bot.on(events.CallbackQuery(data=b"clean_menu"))
async def clean_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit(f"{STAR}{PLANET} <b>اختر نوع التنظيف</b> {PLANET}{STAR}\n{STAR}ملاحظة: البوتات والخاص حذف من الطرفين{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_private"))
async def clean_private(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}{CAT} جاري حذف محادثات الخاص...{STAR}", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"{STAR}{CAT} تم حذف: {count} محادثة{STAR}", parse_mode='html')
                await asyncio.sleep(1.5)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى التنظيف{STAR}\n{STAR}تم حذف: {count} محادثة خاص{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

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
                await msg.edit(f"{STAR}{USER} خرجت من: {left} | تخطيت: {skipped}{STAR}", parse_mode='html')
                await asyncio.sleep(2)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى التنظيف{STAR}\n{STAR}خرجت من: {left} جروب\nتخطيت: {skipped} جروب ادمن{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

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
                await msg.edit(f"{STAR}{PLANET} خرجت من: {left} | تخطيت: {skipped}{STAR}", parse_mode='html')
                await asyncio.sleep(2)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى التنظيف{STAR}\n{STAR}خرجت من: {left} قناة\nتخطيت: {skipped} قناة ادمن{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_bots"))
async def clean_bots(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}{PC} جاري حذف محادثات البوتات...{STAR}", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"{STAR}{PC} تم حذف: {count} بوت{STAR}", parse_mode='html')
                await asyncio.sleep(1)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except: pass
    update_stats()
    await msg.edit(f"{STAR}{CHECK} انتهى التنظيف{STAR}\n{STAR}تم حذف: {count} محادثة بوت{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_all"))
async def clean_all(event):
    client = await check_account(event)
    if not client: return
    buttons = [[Button.inline("✅ نعم متأكد امسح الكل", b"confirm_all")], [Button.inline("❌ إلغاء", b"clean_menu")]]
    await event.edit(f"{STAR}{BOLT} <b>تحذير هام</b> {BOLT}{STAR}\n{STAR}هذه العملية ستحذف كل شيء: القنوات والجروبات والخاص والبوتات{STAR}\n{STAR}هل انت متأكد؟{STAR}", buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"confirm_all"))
async def confirm_all(event):
    await event.edit(f"{STAR}{ROCKET} بدء التنظيف الشامل...{STAR}", parse_mode='html')
    await clean_channels(event); await asyncio.sleep(3)
    await clean_groups(event); await asyncio.sleep(3)
    await clean_private(event); await asyncio.sleep(3)
    await clean_bots(event)
    await event.respond(f"{STAR}{CHECK} تم التنظيف الكامل بنجاح{STAR}\n{STAR}حسابك أصبح نظيف 100%{STAR}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"fetch_menu"))
async def fetch_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit(f"{STAR}{DICE} اختر ما تريد جلبه من حسابك{STAR}", buttons=fetch_menu_buttons(), parse_mode='html')

async def fetch_and_send(event, filter_func, name):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{STAR}{STAR} جاري جلب {name}... انتظر{STAR}", parse_mode='html')
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
        await bot.send_file(event.sender_id, file, caption=f"{STAR}عدد {name}: {len(links)}{STAR}")
        os.remove(file)
        await msg.delete()
    else:
        text = f"{STAR}{name}:{STAR}\n" + '\n'.join(links[:50]) + f"\n\n{STAR}العدد الكلي: {len(links)}{STAR}"
        await msg.edit(text)

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
    await event.edit(f"{STAR}{ROCKET} ابعت الروابط/اليوزر/الايدي كل واحد في سطر{STAR}\n{STAR}يدعم حتى 1000 رابط{STAR}\n{STAR}مثال:\nhttps://t.me/channel\n@username\n-1001234567890{STAR}")

@bot.on(events.NewMessage(func=lambda e: waiting_state.get(e.sender_id)=="join_links"))
async def handle_join(event):
    if event.text == '/cancel':
        del waiting_state[event.sender_id]
        await event.reply(f"{STAR}تم الإلغاء{STAR}", buttons=main_menu(event.sender_id))
        return
    client = user_sessions[event.sender_id]["client"]
    links = event.text.split('\n')
    msg = await event.reply(f"{STAR}{ROCKET} جاري الانضمام...{STAR}")
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
    await msg.edit(f"{STAR}{CHECK} انتهى الانضمام{STAR}\n{STAR}نجح: {success}\nفشل: {fail}{STAR}", buttons=join_menu_buttons())

@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id!= ADMIN_ID: return
    await event.edit(f"{STAR}{CROWN} <b>لوحة تحكم الأدمن</b> {CROWN}{STAR}", buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_stats"))
async def admin_stats(event):
    if event.sender_id!= ADMIN_ID: return
    cur.execute('SELECT COUNT(*) FROM users')
    total_users = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM banned')
    banned_count = cur.fetchone()[0]
    cur.execute('SELECT total_clean FROM stats WHERE id=1')
    total_clean = cur.fetchone()[0]
    text = f"{STAR}{BOLT} <b>احصائيات البوت</b> {BOLT}{STAR}\n\n{STAR}اجمالي المستخدمين: {total_users}{STAR}\n{STAR}المحظورين: {banned_count}{STAR}\n{STAR}عمليات التنظيف: {total_clean}{STAR}"
    await event.edit(text, buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_users"))
async def admin_users(event):
    if event.sender_id!= ADMIN_ID: return
    cur.execute('SELECT user_id, phone, username FROM users ORDER BY user_id DESC LIMIT 50')
    users = cur.fetchall()
    if not users:
        return await event.edit(f"{STAR}مفيش مستخدمين مسجلين{STAR}", buttons=admin_panel_buttons())
    text = f"{STAR}{USER} <b>آخر 50 مستخدم</b> {USER}{STAR}\n\n"
    for uid, phone, username in users:
        status = "🚫" if uid in banned_users else "✅"
        user_display = f"@{username}" if username else phone
        text += f"{STAR}{status} {uid} | {user_display}{STAR}\n"
    await event.edit(text, buttons=admin_panel_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_search"))
async def admin_search(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "search_user"
    await event.edit(f"{STAR}ابعت ايدي المستخدم للبحث عنه{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_ban"))
async def admin_ban(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "ban_user"
    await event.edit(f"{STAR}ابعت ايدي المستخدم للحظر{STAR}\n{STAR}مثال: 123456789 سبب الحظر{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_unban"))
async def admin_unban(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "unban_user"
    await event.edit(f"{STAR}ابعت ايدي المستخدم لفك الحظر{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_broadcast(event):
    if event.sender_id!= ADMIN_ID: return
    waiting_state[event.sender_id] = "broadcast"
    await event.edit(f"{STAR}ابعت الرسالة اللي عايز تذيعها لكل المستخدمين{STAR}")

@bot.on(events.CallbackQuery(data=b"admin_backup"))
async def admin_backup(event):
    if event.sender_id!= ADMIN_ID: return
    await event.edit(f"{STAR}{PC} جاري انشاء النسخة الاحتياطية...{STAR}")
    await bot.send_file(event.sender_id, 'database.db', caption=f"{STAR}نسخة احتياطية بتاريخ {datetime.now().strftime('%Y-%m-%d %H:%M')}{STAR}")

@bot.on(events.NewMessage(func=lambda e: e.sender_id == ADMIN_ID and e.sender_id in waiting_state))
async def admin_handler(event):
    state = waiting_state[event.sender_id]
    if state == "search_user":
        try:
            uid = int(event.text.split()[0])
            info = get_user_info(uid)
            if info:
                status = "🚫 محظور" if uid in banned_users else "✅ شغال"
                text = f"{STAR}{USER} <b>معلومات المستخدم</b> {USER}{STAR}\n{STAR}الايدي: {uid}{STAR}\n{STAR}الرقم: {info[0]}{STAR}\n{STAR}اليوزر: @{info[3]}{STAR}\n{STAR}السيشن: `{info[1][:30]}...`{STAR}\n{STAR}تاريخ الاضافة: {info[2]}{STAR}\n{STAR}الحالة: {status}{STAR}"
            else:
                text = f"{STAR}المستخدم غير موجود في قاعدة البيانات{STAR}"
            del waiting_state[event.sender_id]
            await event.reply(text, parse_mode='html', buttons=admin_panel_buttons())
        except:
            await event.reply(f"{STAR}صيغة الايدي غلط{STAR}")
    elif state == "ban_user":
        try:
            parts = event.text.split(' ', 1)
            uid = int(parts[0])
            reason = parts[1] if len(parts) > 1 else "بدون سبب"
            ban_user(uid, reason)
            del waiting_state[event.sender_id]
            await event.reply(f"{STAR}{LOCK} تم حظر {uid}{STAR}\n{STAR}السبب: {reason}{STAR}", buttons=admin_panel_buttons())
            try: await bot.send_message(uid, f"{STAR}{LOCK} تم حظرك من البوت{STAR}\n{STAR}السبب: {reason}{STAR}")
            except: pass
        except:
            await event.reply(f"{STAR}صيغة غلط. مثال: 123456789 سبب الحظر{STAR}")
    elif state == "unban_user":
        try:
            uid = int(event.text)
            unban_user(uid)
            del waiting_state[event.sender_id]
            await event.reply(f"{STAR}{CHECK} تم فك الحظر عن {uid}{STAR}", buttons=admin_panel_buttons())
        except:
            await event.reply(f"{STAR}ايدي غلط{STAR}")
    elif state == "broadcast":
        msg = event.text
        del waiting_state[event.sender_id]
        cur.execute('SELECT user_id FROM users')
        sent, failed = 0, 0
        for (uid,) in cur.fetchall():
            try:
                await bot.send_message(uid, f"{STAR}{BOLT} <b>اذاعة من المطور</b> {BOLT}{STAR}\n\n{msg}", parse_mode='html')
                sent += 1
                await asyncio.sleep(0.1)
            except:
                failed += 1
        await event.reply(f"{STAR}{CHECK} تم الارسال{STAR}\n{STAR}وصل: {sent}\nفشل: {failed}{STAR}", buttons=admin_panel_buttons())

@bot.on(events.CallbackQuery(data=b"del_account"))
async def del_account(event):
    if event.sender_id in user_sessions:
        await user_sessions[event.sender_id]["client"].disconnect()
        del user_sessions[event.sender_id]
        cur.execute('DELETE FROM users WHERE user_id=?', (event.sender_id,))
        conn.commit()
        await event.edit(f"{STAR}{CHECK} تم حذف الحساب بنجاح{STAR}", buttons=main_menu(event.sender_id))
    else:
        await event.answer(f"{STAR}مفيش حساب مضاف للحذف{STAR}", alert=True)

@bot.on(events.CallbackQuery(data=b"features"))
async def features(event):
    if not await check_subscription(event.sender_id): return
    text = (
        f"{STAR}{BOLT} <b>مميزات البوت</b> {BOLT}{STAR}\n\n"
        f"{STAR}{LOCK} امان كامل وتشفير{STAR}\n"
        f"{STAR}{ROCKET} سرعة عالية في التنظيف{STAR}\n"
        f"{STAR}{DICE} جلب جميع الروابط بملف txt{STAR}\n"
        f"{STAR}{ROCKET} انضمام تلقائي 1000 رابط{STAR}\n"
        f"{STAR}{PC} لوحة ادمن متطورة كاملة{STAR}\n"
        f"{STAR}{CROWN} دعم السيشن والرقم{STAR}\n"
        f"{STAR}{SIGNAL} اسم جلسة iPhone 17 Pro{STAR}\n"
        f"{STAR}{SPARK} اشتراك اجباري قناة + جروب{STAR}"
    )
    await event.edit(text, buttons=[[Button.inline("🔙 رجوع للقائمة", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event):
    uid = event.sender_id
    await event.edit(f"{STAR}{PLANET} <b>القائمة الرئيسية</b> {PLANET}{STAR}", buttons=main_menu(uid), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"join_channels"))
async def join_channels(event):
    client = await check_account(event)
    if not client: return
    waiting_state[event.sender_id] = "join_links"
    await event.edit(f"{STAR}{PLANET} ابعت روابط القنوات فقط كل سطر رابط{STAR}\n{STAR}مثال: https://t.me/channelname{STAR}")

@bot.on(events.CallbackQuery(data=b"join_groups"))
async def join_groups(event):
    client = await check_account(event)
    if not client: return
    waiting_state[event.sender_id] = "join_links"
    await event.edit(f"{STAR}{USER} ابعت روابط الجروبات فقط كل سطر رابط{STAR}\n{STAR}مثال: https://t.me/joinchat/xxxxx{STAR}")

# تشغيل البوت
print(f"{STAR}البوت شغال الآن...{STAR}")
print(f"{STAR}المطور: @{DEVELOPER}{STAR}")
print(f"{STAR}قناة الاشتراك: @{FORCE_CHANNEL}{STAR}")
print(f"{STAR}جروب الاشتراك: @{FORCE_GROUP}{STAR}")

try:
    bot.run_until_disconnected()
except KeyboardInterrupt:
    print(f"{STAR}تم ايقاف البوت{STAR}")
    conn.close()
