import os
import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import LeaveChannelRequest, GetParticipantRequest
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantAdmin
from telethon.errors import UserNotParticipantError
from dotenv import load_dotenv

load_dotenv()

API_ID = 20867472"
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
DEVELOPER = "Programmer_error"
FORCE_CHANNEL = "Programmer_error1"
FORCE_GROUP = "Programmer_error2"

# الايموجي البريميوم بتوعك
SPARK = '<tg-emoji emoji-id="5884015001206791984">✨</tg-emoji>'
BOLT = '<tg-emoji emoji-id="5886360482847137476">⚡️</tg-emoji>'
SIGNAL = '<tg-emoji emoji-id="5886386768046988787">📶</tg-emoji>'
USER = '<tg-emoji emoji-id="5886695331382435915">👤</tg-emoji>'
PC = '<tg-emoji emoji-id="5886664420502805908">💻</tg-emoji>'
PLANET = '<tg-emoji emoji-id="5886449487454416104">🪐</tg-emoji>'
CAT = '<tg-emoji emoji-id="5886470240736387171">🐈</tg-emoji>'
ROCKET = '<tg-emoji emoji-id="5886426509378198">🚀</tg-emoji>'
LOCK = '<tg-emoji emoji-id="5886249404544443212">🔒</tg-emoji>'
CHECK = '<tg-emoji emoji-id="5886345304115969449">✅</tg-emoji>'

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}

async def check_subscription(user_id):
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
        [Button.url("📢 اشترك في قناة السورس", f"https://t.me/{FORCE_CHANNEL}")],
        [Button.url("👥 اشترك في جروب الدعم", f"https://t.me/{FORCE_GROUP}")],
        [Button.inline("✅ تحققت من الاشتراك", b"check_sub")]
    ]

def main_menu():
    return [
        [Button.inline("➕ إضافة حساب", b"add_account")],
        [Button.inline("🧹 قائمة التنظيف", b"clean_menu")],
        [Button.inline("⭐ المميزات", b"features")],
        [Button.url("👨‍💻 المبرمج", f"https://t.me/{DEVELOPER}")]
    ]

def clean_menu_buttons():
    return [
        [Button.inline("📢 تنظيف القنوات", b"clean_channels")],
        [Button.inline("👥 تنظيف الجروبات", b"clean_groups")],
        [Button.inline("💬 تنظيف الخاص", b"clean_private")],
        [Button.inline("🤖 تنظيف البوتات", b"clean_bots")],
        [Button.inline("💣 تنظيف الكل", b"clean_all")],
        [Button.inline("🗑️ حذف الحساب", b"del_account")],
        [Button.inline("🔙 رجوع", b"back")]
    ]

async def check_account(event):
    uid = event.sender_id
    if not await check_subscription(uid):
        await event.edit(
            f"{SPARK}{LOCK} <b>اشتراك إجباري مطلوب</b> {LOCK}{SPARK}\n\n"
            f"{SPARK}لازم تدخل @{FORCE_CHANNEL} + @{FORCE_GROUP} الأول{SPARK}\n\n"
            f"{SPARK}بعد ما تشترك دوس الزرار تحت{SPARK}",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )
        return None
    if uid not in user_sessions:
        await event.answer(f"{SPARK}{USER} ضيف حسابك الأول {USER}{SPARK}", alert=True)
        return None
    return user_sessions[uid]["client"]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if not await check_subscription(event.sender_id):
        return await event.respond(
            f"{LOCK} <b>مرحباً بك في بوت التنظيف</b> {SPARK}\n\n"
            f"{SPARK}ممنوع الاستخدام قبل الاشتراك{SPARK}\n\n"
            f"{SPARK}اشترك في القناة والجروب تحت{SPARK}",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    user = await event.get_sender()
    name_user = user.first_name

    welcome_text = (
        f"{SPARK}<b>أهلاً {name_user}</b> {ROCKET}\n\n"
        f"{PLANET} بوت تنظيف الحسابات الاحترافي{SPARK}\n\n"
        f"{BOLT} سريع وآمن 100%{SPARK}\n\n"
        f"{SIGNAL} ابدأ باضافة حسابك{SPARK}"
    )

    await event.respond(welcome_text, buttons=main_menu(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"check_sub"))
async def check_sub(event):
    if await check_subscription(event.sender_id):
        await event.edit(f"{SPARK}{CHECK} <b>تم التحقق بنجاح</b> {CHECK}{SPARK}\n\n{SPARK}دلوقتي تقدر تستخدم كل المميزات{SPARK}", buttons=main_menu(), parse_mode='html')
    else:
        await event.answer(f"{SPARK}{LOCK} لسه مشتركتش في الاتنين{SPARK}", alert=True)

@bot.on(events.CallbackQuery(data=b"features"))
async def features(event):
    if not await check_subscription(event.sender_id):
        return await event.edit(
            f"{SPARK}{LOCK} <b>اشترك الأول</b> {LOCK}{SPARK}\n\n"
            f"{SPARK}القناة + الجروب إجباري{SPARK}",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    features_text = (
        f"{BOLT} <b>مميزات متطورة</b> {SPARK}\n\n"
        f"{LOCK} حماية من التقييد بتأخير ذكي{SPARK}\n"
        f"{ROCKET} سرعة خارقة في التنظيف{SPARK}\n"
        f"{SIGNAL} كشف تلقائي للجروبات المهمة{SPARK}\n"
        f"{PLANET} يدعم كل انواع المحادثات{SPARK}\n"
        f"{CAT} حذف من الطرفين للخاص{SPARK}\n"
        f"{PC} واجهة سهلة وبضغطة واحدة{SPARK}\n\n"
    )
    await event.edit(features_text, buttons=[[Button.inline("🔙 رجوع", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"add_account"))
async def add_account(event):
    if not await check_subscription(event.sender_id):
        return await event.edit(
            f"{SPARK}{LOCK} <b>اشتراك إجباري</b> {LOCK}{SPARK}\n\n"
            f"{SPARK}ادخل القناة والجروب اولا{SPARK}",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    async with bot.conversation(event.sender_id, timeout=300) as conv:
        await conv.send_message(f"{SPARK}{USER} ارسل رقمك مع الكود: +2010xxxxxxx{SPARK}")
        phone_msg = await conv.get_response()
        if phone_msg.text == '/cancel':
            return await conv.send_message(f"{SPARK}{LOCK} تم الإلغاء{SPARK}", buttons=main_menu())

        phone = phone_msg.text
        await conv.send_message(f"{SPARK}{SIGNAL} ارسل كود التفعيل اللي وصلك كذا 7 6 5 6 بمسافات{SPARK}")

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        client._init_request.app_version = "iPhone 17 Pro"
        client._init_request.device_model = "iPhone 17 Pro"
        client._init_request.system_version = "iOS 18.0"

        await client.connect()
        try:
            await client.send_code_request(phone)
        except Exception as e:
            return await conv.send_message(f"{SPARK}{LOCK} خطأ: {e}{SPARK}", buttons=main_menu())

        code = (await conv.get_response()).text
        try:
            await client.sign_in(phone, code)
        except:
            await conv.send_message(f"{SPARK}{LOCK} ابعت كلمة سر التحقق بخطوتين{SPARK}")
            password = (await conv.get_response()).text
            await client.sign_in(password=password)

        me = await client.get_me()
        user_sessions[event.sender_id] = {"client": client, "phone": phone, "user_id": me.id}

        await conv.send_message(
            f"{SPARK}{CHECK} <b>تم الربط بنجاح</b> {CHECK}{SPARK}\n"
            f"{SPARK}الرقم: {phone}{SPARK}\n"
            f"{SPARK}اختار عملية التنظيف{SPARK}",
            buttons=clean_menu_buttons()
        )

@bot.on(events.CallbackQuery(data=b"clean_menu"))
async def clean_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit(f"{SPARK}{PLANET} <b>اختر نوع التنظيف</b> {PLANET}{SPARK}\n\n{SPARK}كل عملية ليها تأخير للأمان{SPARK}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_channels"))
async def clean_channels(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{SPARK}{PLANET} جاري فحص القنوات...{SPARK}", parse_mode='html')
    count_left, count_skipped = 0, 0
    async for dialog in client.iter_dialogs():
        if dialog.is_channel and not dialog.is_group:
            if dialog.entity.username and dialog.entity.username.lower() == FORCE_CHANNEL.lower():
                continue
            try:
                participant = await client(GetParticipantRequest(dialog.id, 'me'))
                if isinstance(participant.participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
                    count_skipped += 1
                    continue
                await client(LeaveChannelRequest(dialog.id))
                count_left += 1
                await msg.edit(f"{SPARK}{PLANET} تم الخروج من: {count_left}\nتخطي: {count_skipped}{SPARK}", parse_mode='html')
                await asyncio.sleep(2)
            except: pass
    await msg.edit(f"{SPARK}{CHECK} <b>انتهى تنظيف القنوات</b> {CHECK}{SPARK}\n{SPARK}خرجت من: {count_left} قناة{SPARK}\n{SPARK}تخطيت: {count_skipped} كأدمن{SPARK}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_groups"))
async def clean_groups(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{SPARK}{USER} جاري فحص الجروبات...{SPARK}", parse_mode='html')
    count_left, count_skipped = 0, 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            try:
                participant = await client(GetParticipantRequest(dialog.id, 'me'))
                if isinstance(participant.participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
                    count_skipped += 1
                    continue
                await client(LeaveChannelRequest(dialog.id))
                count_left += 1
                await msg.edit(f"{SPARK}{USER} تم الخروج من: {count_left}\nتخطي: {count_skipped}{SPARK}", parse_mode='html')
                await asyncio.sleep(2)
            except: pass
    await msg.edit(f"{CHECK} <b>انتهى تنظيف الجروبات</b> {SPARK}\n{SPARK}خرجت من: {count_left} جروب{SPARK}\n{SPARK}تخطيت: {count_skipped} كأدمن{SPARK}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_private"))
async def clean_private(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{SPARK}{CAT} جاري حذف الخاص...{SPARK}\n{SPARK}الحذف من الطرفين للجديد فقط{SPARK}", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"{SPARK}{CAT} تم حذف: {count} محادثة{SPARK}", parse_mode='html')
                await asyncio.sleep(1.5)
            except: pass
    await msg.edit(f"{SPARK}{CHECK} <b>انتهى تنظيف الخاص</b> {CHECK}{SPARK}\n{SPARK}تم حذف: {count} محادثة{SPARK}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_bots"))
async def clean_bots(event):
    client = await check_account(event)
    if not client: return
    msg = await event.edit(f"{SPARK}{PC} جاري حذف البوتات...{SPARK}", parse_mode='html')
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"{SPARK}{PC} تم حذف: {count} بوت{SPARK}", parse_mode='html')
                await asyncio.sleep(1)
            except: pass
    await msg.edit(f"{SPARK}{CHECK} <b>انتهى تنظيف البوتات</b> {CHECK}{SPARK}\n{SPARK}تم حذف: {count} بوت{SPARK}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_all"))
async def clean_all(event):
    client = await check_account(event)
    if not client: return
    buttons = [[Button.inline("✅ متأكد، نفذ", b"confirm_all")], [Button.inline("❌ إلغاء", b"clean_menu")]]
    await event.edit(f"{SPARK}{BOLT} <b>تحذير نهائي</b> {BOLT}{SPARK}\n\n{SPARK}هيتم مسح كل شيء{SPARK}\n{SPARK}قنوات + جروبات + خاص + بوتات{SPARK}\n\n{SPARK}متأكد؟{SPARK}", buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"confirm_all"))
async def confirm_all(event):
    await event.edit(f"{SPARK}{ROCKET} بدء التنظيف الكامل...{SPARK}", parse_mode='html')
    await clean_channels(event)
    await asyncio.sleep(3)
    await clean_groups(event)
    await asyncio.sleep(3)
    await clean_private(event)
    await asyncio.sleep(3)
    await clean_bots(event)
    await event.respond(f"{SPARK}{CHECK} <b>تم التنظيف الكامل</b> {CHECK}{SPARK}\n\n{SPARK}حسابك نضيف دلوقتي{SPARK}", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"del_account"))
async def del_account(event):
    if event.sender_id in user_sessions:
        await user_sessions[event.sender_id]["client"].disconnect()
        del user_sessions[event.sender_id]
        await event.edit(f"{SPARK}{CHECK} تم حذف الحساب{SPARK}", buttons=main_menu())
    else:
        await event.answer(f"{SPARK}{USER} مفيش حساب مضاف{SPARK}", alert=True)

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event):
    await event.edit(f"{SPARK}{PLANET} <b>القائمة الرئيسية</b> {PLANET}{SPARK}", buttons=main_menu(), parse_mode='html')

print("Bot is running...")
bot.run_until_disconnected()
