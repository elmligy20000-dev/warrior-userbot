import os
import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import LeaveChannelRequest, GetParticipantRequest
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.types import Channel, Chat, User, ChannelParticipantCreator, ChannelParticipantAdmin
from telethon.errors import UserNotParticipantError
from dotenv import load_dotenv

load_dotenv()

API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
DEVELOPER = "Programmer_error"
FORCE_CHANNEL = "Programmer_error1"

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}

# ===== التحقق من الاشتراك =====
async def check_subscription(user_id):
    try:
        await bot(GetParticipantRequest(FORCE_CHANNEL, user_id))
        return True
    except UserNotParticipantError:
        return False
    except:
        return True

def force_sub_buttons():
    return [[Button.url("📢 اشترك في قناة السورس", f"https://t.me/{FORCE_CHANNEL}")],
            [Button.inline("✅ تحققت من الاشتراك", b"check_sub")]]

# ===== الأزرار =====
def main_menu():
    return [
        [Button.inline("إضافة حساب", b"add_account")],
        [Button.inline("قائمة التنظيف", b"clean_menu")],
        [Button.inline("المميزات", b"features")],
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
            "<b>⚠️ اشتراك إجباري</b>\n\n"
            f"لازم تشترك في @{FORCE_CHANNEL} الأول عشان تستخدم البوت",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )
        return None
    if uid not in user_sessions:
        await event.answer("ضيف حسابك الأول", alert=True)
        return None
    return user_sessions[uid]["client"]

# ===== أوامر البوت =====
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if not await check_subscription(event.sender_id):
        return await event.respond(
            "<b>⚠️ اشتراك إجباري</b>\n\n"
            f"لازم تشترك في @{FORCE_CHANNEL} الأول عشان تستخدم البوت",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    user = await event.get_sender()
    name_user = user.first_name

    # الصيغة الصح اللي بتشتغل مع Telethon
    welcome_text = (
        f'<b><tg-emoji emoji-id="5798482080421649554">🔒</tg-emoji> اهلا بك ‹ {name_user} › في بوت تنظيف الحسابات <tg-emoji emoji-id="5796526727840669257">🎲</tg-emoji></b>\n\n'
        f'<b><tg-emoji emoji-id="5796499583647359561">📌</tg-emoji> ضيف حسابك وابدأ التنظيف بضغطة زر <tg-emoji emoji-id="5798941981224737816">🚀</tg-emoji></b>\n\n'
        f'<b><tg-emoji emoji-id="5798482080421649554">🔒</tg-emoji> كل العمليات فيها تأخير تلقائي عشان أمان حسابك <tg-emoji emoji-id="5798941981224737816">🚀</tg-emoji></b>'
    )

    await event.respond(welcome_text, buttons=main_menu(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"check_sub"))
async def check_sub(event):
    if await check_subscription(event.sender_id):
        await event.edit("<b>✅ تم التحقق من الاشتراك</b>\n\nتقدر تستخدم البوت دلوقتي", buttons=main_menu(), parse_mode='html')
    else:
        await event.answer("❌ لسه مشتركتش في القناة", alert=True)

@bot.on(events.CallbackQuery(data=b"features"))
async def features(event):
    if not await check_subscription(event.sender_id):
        return await event.edit(
            "<b>⚠️ اشتراك إجباري</b>\n\n"
            f"لازم تشترك في @{FORCE_CHANNEL} الأول",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )
    
    features_text = (
        "<b>مميزات البوت:</b>\n\n"
        "<b>أمان كامل:</b> تأخير تلقائي بين العمليات\n"
        "<b>سرعة عالية:</b> تنظيف مئات المحادثات بدقايق\n"
        "<b>ذكي:</b> بيتخطى الجروبات اللي انت أدمن فيها\n"
        "<b>شامل:</b> قنوات + جروبات + خاص + بوتات\n"
        "<b>حذف من الطرفين:</b> للرسايل الجديدة في الخاص\n"
        "<b>واجهة سهلة:</b> كل حاجة بضغطة زر\n\n"
    )
    await event.edit(features_text, buttons=[[Button.inline("🔙 رجوع", b"back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"add_account"))
async def add_account(event):
    if not await check_subscription(event.sender_id):
        return await event.edit(
            "<b>⚠️ اشتراك إجباري</b>\n\n"
            f"لازم تشترك في @{FORCE_CHANNEL} الأول",
            buttons=force_sub_buttons(),
            parse_mode='html'
        )

    async with bot.conversation(event.sender_id, timeout=300) as conv:
        await conv.send_message("ابعت رقم الحساب مع كود الدولة: `+2010xxxxxxx`\n\nلإلغاء العملية ابعت /cancel")
        phone_msg = await conv.get_response()
        if phone_msg.text == '/cancel':
            return await conv.send_message("تم الإلغاء", buttons=main_menu())

        phone = phone_msg.text
        await conv.send_message("تمام. دلوقتي ابعت كود التفعيل اللي وصلك كذا 5 6 6 6 بمسافات:")

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        # اسم الجلسة لازم يتحط هنا قبل connect
        client._init_request.app_version = "iPhone 17 Pro"
        client._init_request.device_model = "iPhone 17 Pro"
        client._init_request.system_version = "iOS 18.0"
        
        await client.connect()
        try:
            await client.send_code_request(phone)
        except Exception as e:
            return await conv.send_message(f"خطأ: {e}\nاتأكد من الرقم", buttons=main_menu())

        code = (await conv.get_response()).text
        try:
            await client.sign_in(phone, code)
        except:
            await conv.send_message("فيه تحقق بخطوتين؟ ابعت الباسورد:")
            password = (await conv.get_response()).text
            await client.sign_in(password=password)

        me = await client.get_me()

        user_sessions[event.sender_id] = {
            "client": client,
            "phone": phone,
            "user_id": me.id
        }
        await conv.send_message(
            f"✅ تم إضافة الحساب بنجاح\nالرقم: `{phone}`",
            buttons=clean_menu_buttons()
        )

@bot.on(events.CallbackQuery(data=b"clean_menu"))
async def clean_menu(event):
    client = await check_account(event)
    if not client: return
    await event.edit("<b>اختر عملية التنظيف:</b>", buttons=clean_menu_buttons(), parse_mode='html')

# ===== دوال التنظيف - نفس الكود اللي فات =====
@bot.on(events.CallbackQuery(data=b"clean_channels"))
async def clean_channels(event):
    client = await check_account(event)
    if not client: return

    msg = await event.edit("<b>جاري فحص القنوات...</b>", parse_mode='html')
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
                await msg.edit(f"<b>تنظيف القنوات</b>\nخرجت من: {count_left}\nتخطيت: {count_skipped}", parse_mode='html')
                await asyncio.sleep(2)
            except: pass

    await msg.edit(f"<b>✅ خلصنا تنظيف القنوات</b>\nخرجت من: {count_left}\nسبت: {count_skipped} كأدمن/مالك", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_groups"))
async def clean_groups(event):
    client = await check_account(event)
    if not client: return

    msg = await event.edit("<b>جاري فحص الجروبات...</b>", parse_mode='html')
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
                await msg.edit(f"<b>تنظيف الجروبات</b>\nخرجت من: {count_left}\nتخطيت: {count_skipped}", parse_mode='html')
                await asyncio.sleep(2)
            except: pass

    await msg.edit(f"<b>✅ خلصنا تنظيف الجروبات</b>\nخرجت من: {count_left}\nسبت: {count_skipped} كأدمن/مالك", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_private"))
async def clean_private(event):
    client = await check_account(event)
    if not client: return

    msg = await event.edit("<b>جاري حذف المحادثات الخاصة...</b>\nتحذير: الحذف من الطرفين شغال للرسايل الجديدة بس", parse_mode='html')
    count = 0

    async for dialog in client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"<b>تنظيف الخاص</b>\nتم حذف: {count} محادثة", parse_mode='html')
                await asyncio.sleep(1)
            except: pass

    await msg.edit(f"<b>✅ خلصنا تنظيف الخاص</b>\nتم حذف: {count} محادثة", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_bots"))
async def clean_bots(event):
    client = await check_account(event)
    if not client: return

    msg = await event.edit("<b>جاري حذف البوتات...</b>", parse_mode='html')
    count = 0

    async for dialog in client.iter_dialogs():
        if dialog.is_user and dialog.entity.bot:
            try:
                await client(DeleteHistoryRequest(peer=dialog.id, max_id=0, just_clear=False, revoke=True))
                count += 1
                await msg.edit(f"<b>تنظيف البوتات</b>\nتم حذف: {count} بوت", parse_mode='html')
                await asyncio.sleep(1)
            except: pass

    await msg.edit(f"<b>✅ خلصنا تنظيف البوتات</b>\nتم حذف: {count} بوت", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"clean_all"))
async def clean_all(event):
    client = await check_account(event)
    if not client: return

    buttons = [
        [Button.inline("✅ متأكد، نفذ", b"confirm_all")],
        [Button.inline("❌ إلغاء", b"clean_menu")]
    ]
    await event.edit("<b>تحذير: تنظيف الكل هيحذف كل حاجة</b>\nالقنوات + الجروبات + الخاص + البوتات\n\nمتأكد؟", buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"confirm_all"))
async def confirm_all(event):
    await event.edit("<b>بدء التنظيف الكامل...</b>", parse_mode='html')
    await clean_channels(event)
    await asyncio.sleep(1)
    await clean_groups(event)
    await asyncio.sleep(1)
    await clean_private(event)
    await asyncio.sleep(1)
    await clean_bots(event)
    await event.respond("<b>💣 تم الانتهاء من تنظيف الكل</b>", buttons=clean_menu_buttons(), parse_mode='html')

@bot.on(events.CallbackQuery(data=b"del_account"))
async def del_account(event):
    if event.sender_id in user_sessions:
        await user_sessions[event.sender_id]["client"].disconnect()
        del user_sessions[event.sender_id]
        await event.edit("✅ تم حذف الحساب من البوت", buttons=main_menu())
    else:
        await event.answer("مفيش حساب مضاف", alert=True)

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event):
    await event.edit("<b>القائمة الرئيسية:</b>", buttons=main_menu(), parse_mode='html')

print("Bot is running...")
bot.run_until_disconnected()
