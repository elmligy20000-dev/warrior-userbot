from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ChatMemberStatus
import asyncio, os
from datetime import datetime, timedelta
import motor.motor_asyncio

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")
DEV_ID = 154919127 # غيره لايدي حسابك

app = Client("cleaner_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = mongo.cleaner_bot
vips = db.vips
settings = db.settings
users = db.users

# ========== دوال مساعدة ==========
async def is_vip(chat_id):
    vip = await vips.find_one({"chat_id": chat_id})
    if not vip: return False
    return vip["expire"] > datetime.now()

async def is_registered(user_id):
    user = await users.find_one({"user_id": user_id})
    return user is not None

# ========== أوامر اليوزر ==========
@app.on_message(filters.command("start", prefixes=".") & filters.private)
async def start(client, message: Message):
    user_id = message.from_user.id
    if await is_registered(user_id):
        return await message.reply(
            "👋 **أهلاً بيك تاني**\n\nضيفني في جروبك واديني صلاحية `Ban users`\nبعدين اكتب.اشتراك عشان تفعل البوت",
            reply_markup=ReplyKeyboardRemove()
        )

    btn = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 تسجيل برقم الهاتف", request_contact=True)]],
        resize_keyboard=True
    )
    await message.reply(
        "👋 **أهلاً بيك في بوت تصفية عـازف**\n\nعشان تستخدم البوت لازم تسجل رقمك الأول\nدوس الزرار اللي تحت 👇",
        reply_markup=btn
    )

@app.on_message(filters.contact & filters.private)
async def save_contact(client, message: Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    await users.update_one(
        {"user_id": user_id},
        {"$set": {"phone": phone, "name": message.from_user.first_name, "date": datetime.now()}},
        upsert=True
    )

    await message.reply(
        f"✅ **تم التسجيل بنجاح**\n\n📱 **رقمك:** `{phone}`\n\nدلوقتي ضيفني في جروبك واكتب.اشتراك",
        reply_markup=ReplyKeyboardRemove()
    )

    await app.send_message(
        DEV_ID,
        f"🆕 **يوزر جديد سجل**\n\n👤 **الاسم:** {message.from_user.mention}\n🆔 **الايدي:** `{user_id}`\n📱 **الرقم:** `{phone}`"
    )

@app.on_message(filters.command("احصائية", prefixes=".") & filters.group)
async def stats(client, message: Message):
    chat_id = message.chat.id
    if not await is_registered(message.from_user.id):
        return await message.reply("❌ **سجل رقمك الأول**\nابعتلي.start خاص")

    if not await is_vip(chat_id):
        return await message.reply("❌ **الجروب مش VIP**\nاشترك بـ 2$ شهرياً من.اشتراك")

    total = 0
    deleted = 0
    async for member in app.get_chat_members(chat_id):
        total += 1
        if member.user.is_deleted: deleted += 1

    await message.reply(f"📊 **احصائية الجروب**\n\n👥 **العدد الكلي:** {total}\n🗑️ **حسابات محذوفة:** {deleted}\n✅ **أعضاء حقيقيين:** {total - deleted}")

@app.on_message(filters.command(["تصفية", "عازف"], prefixes=".") & filters.group)
async def clean_deleted(client, message: Message):
    chat_id = message.chat.id
    if not await is_registered(message.from_user.id):
        return await message.reply("❌ **سجل رقمك الأول**\nابعتلي.start خاص")

    user_status = await app.get_chat_member(chat_id, message.from_user.id)
    if user_status.status not in ["administrator", "owner"]:
        return await message.reply("❌ **لازم تكون أدمن**")

    if not await is_vip(chat_id):
        return await message.reply("❌ **الجروب مش VIP**\nاطلب اشتراك من.اشتراك")

    bot_status = await app.get_chat_member(chat_id, "me")
    if not bot_status.privileges.can_restrict_members:
        return await message.reply("❌ **اديني صلاحية حظر الأعضاء الأول**")

    msg = await message.reply("🎵 ** 🤓 عازف بدأ يعزف...**\n🔍 **جاري حذف الحسابات المحذوفة...**")
    deleted = 0

    async for member in app.get_chat_members(chat_id):
        if member.user.is_deleted:
            try:
                await app.ban_chat_member(chat_id, member.user.id)
                deleted += 1
                await asyncio.sleep(1.2)
            except: pass

    await msg.edit(f"✅ **العازف خلص**\n🗑️ **حذف {deleted} حساب محذوف**\n🎵 تمت التصفية بنجاح")

@app.on_message(filters.command("اشتراك", prefixes=".") & filters.group)
async def subscribe(client, message: Message):
    if not await is_registered(message.from_user.id):
        return await message.reply("❌ **سجل رقمك الأول**\nابعتلي.start خاص")

    data = await settings.find_one({"_id": "payment"}) or {}
    usdt = data.get('usdt', 'لم يتم التحديد')
    ltc = data.get('ltc', 'لم يتم التحديد')
    ton = data.get('ton', 'لم يتم التحديد')
    vodafone = data.get('vodafone', 'لم يتم التحديد')

    text = f"""
💎 **اشتراك بوت التصفية - 2$ شهرياً**

**المميزات:**
1. حذف كل الحسابات المحذوفة بأمر واحد
2. احصائيات تفصيلية للجروب
3. دعم فني مباشر

**طرق الدفع:**
**USDT TRC20:** `{usdt}`
**LTC:** `{ltc}`
**TON:** `{ton}`
**فودافون كاش:** `{vodafone}`

دوس على زرار الدفع اللي يناسبك 👇
بعد التحويل ابعت سكرين هنا وهيتفعل تلقائي
"""

    payment_buttons = []
    if usdt!= 'لم يتم التحديد':
        payment_buttons.append([InlineKeyboardButton("💵 دفع USDT TRC20", url=f"https://tronscan.org/#/address/{usdt}")])
    if ltc!= 'لم يتم التحديد':
        payment_buttons.append([InlineKeyboardButton("🔶 دفع LTC", url=f"https://blockchair.com/litecoin/address/{ltc}")])
    if ton!= 'لم يتم التحديد':
        payment_buttons.append([InlineKeyboardButton("💎 دفع TON", url=f"https://tonviewer.com/{ton}")])
    if vodafone!= 'لم يتم التحديد':
        payment_buttons.append([InlineKeyboardButton("📱 فودافون كاش", url=f"https://t.me/share/url?url={vodafone}")])

    payment_buttons.append([
        InlineKeyboardButton("📊 احصائية الجروب", callback_data="check_stats"),
        InlineKeyboardButton("📖 شرح الاستخدام", callback_data="how_to_use")
    ])
    payment_buttons.append([InlineKeyboardButton("📞 تواصل مع المطور", url=f"tg://user?id={DEV_ID}")])

    buttons = InlineKeyboardMarkup(payment_buttons)
    await message.reply(text, reply_markup=buttons)

@app.on_message(filters.photo & filters.group)
async def payment_proof(client, message: Message):
    if not await is_registered(message.from_user.id):
        return

    chat_id = message.chat.id
    user_data = await users.find_one({"user_id": message.from_user.id})
    phone = user_data.get("phone", "مش مسجل")

    await app.send_photo(
        DEV_ID,
        message.photo.file_id,
        caption=f"💰 **اشعار دفع جديد**\n\n**الجروب:** {message.chat.title}\n**الايدي:** `{chat_id}`\n**من:** {message.from_user.mention}\n📱 **رقمه:** `{phone}`\n\n.cancel_{chat_id} لإلغاء\n.vip_{chat_id} للتفعيل شهر"
    )
    await message.reply("✅ **تم استلام اثبات الدفع**\nجاري المراجعة والتفعيل خلال دقايق")

# ========== كول باك الزراير ==========
@app.on_callback_query(filters.regex("check_stats"))
async def stats_button(client, callback_query):
    chat_id = callback_query.message.chat.id
    if not await is_vip(chat_id):
        return await callback_query.answer("❌ الجروب مش VIP", show_alert=True)

    await callback_query.answer("جاري جلب الاحصائية...")
    total = 0
    deleted = 0
    async for member in app.get_chat_members(chat_id):
        total += 1
        if member.user.is_deleted: deleted += 1

    text = f"📊 **احصائية الجروب**\n\n👥 **العدد الكلي:** {total}\n🗑️ **حسابات محذوفة:** {deleted}\n✅ **أعضاء حقيقيين:** {total - deleted}"
    await callback_query.message.reply(text)

@app.on_callback_query(filters.regex("how_to_use"))
async def how_to_use_button(client, callback_query):
    text = """
📖 **شرح استخدام بوت التصفية**

**1. التسجيل:** ابعت.start للبوت خاص وسجل رقمك

**2. تفعيل البوت:**
- ضيف البوت للجروب
- اديله صلاحية `Ban users`
- اكتب `.اشتراك` وفعل الـ VIP بـ 2$ شهرياً

**3. الأوامر:**
`.تصفية` أو `.عازف` - يحذف كل الحسابات المحذوفة
`.احصائية` - يعرض احصائية الجروب

**ملاحظة:** البوت يحذف `Deleted Account` فقط
"""
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_sub")]])
    await callback_query.message.edit_text(text, reply_markup=back_btn)

@app.on_callback_query(filters.regex("back_to_sub"))
async def back_to_sub(client, callback_query):
    await callback_query.message.delete()
    await subscribe(client, callback_query.message)

# ========== أوامر المطور ==========
@app.on_message(filters.command("ارقام", prefixes=".") & filters.user(DEV_ID))
async def show_numbers(client, message: Message):
    data = await settings.find_one({"_id": "payment"}) or {}
    text = f"""
💳 **بيانات الدفع الحالية:**

**USDT TRC20:** `{data.get('usdt', 'مش متضاف')}`
**LTC:** `{data.get('ltc', 'مش متضاف')}`
**TON:** `{data.get('ton', 'مش متضاف')}`
**فودافون كاش:** `{data.get('vodafone', 'مش متضاف')}`

**للتعديل استخدم:**
`.set_usdt العنوان`
`.set_ltc العنوان`
`.set_ton العنوان`
`.set_vodafone الرقم`
"""
    await message.reply(text)

@app.on_message(filters.command("set_usdt", prefixes=".") & filters.user(DEV_ID))
async def set_usdt(client, message: Message):
    if len(message.command) < 2: return await message.reply("استخدم:.set_usdt العنوان")
    await settings.update_one({"_id": "payment"}, {"$set": {"usdt": message.command[1]}}, upsert=True)
    await message.reply("✅ **تم تحديث عنوان USDT**")

@app.on_message(filters.command("set_ltc", prefixes=".") & filters.user(DEV_ID))
async def set_ltc(client, message: Message):
    if len(message.command) < 2: return await message.reply("استخدم:.set_ltc العنوان")
    await settings.update_one({"_id": "payment"}, {"$set": {"ltc": message.command[1]}}, upsert=True)
    await message.reply("✅ **تم تحديث عنوان LTC**")

@app.on_message(filters.command("set_ton", prefixes=".") & filters.user(DEV_ID))
async def set_ton(client, message: Message):
    if len(message.command) < 2: return await message.reply("استخدم:.set_ton العنوان")
    await settings.update_one({"_id": "payment"}, {"$set": {"ton": message.command[1]}}, upsert=True)
    await message.reply("✅ **تم تحديث عنوان TON**")

@app.on_message(filters.command("set_vodafone", prefixes=".") & filters.user(DEV_ID))
async def set_vodafone(client, message: Message):
    if len(message.command) < 2: return await message.reply("استخدم:.set_vodafone الرقم")
    await settings.update_one({"_id": "payment"}, {"$set": {"vodafone": message.command[1]}}, upsert=True)
    await message.reply("✅ **تم تحديث رقم فودافون كاش**")

@app.on_message(filters.command("vip_", prefixes=".") & filters.user(DEV_ID))
async def add_vip(client, message: Message):
    chat_id = int(message.text.split("_")[1])
    expire_date = datetime.now() + timedelta(days=30)
    await vips.update_one({"chat_id": chat_id}, {"$set": {"expire": expire_date}}, upsert=True)
    await message.reply(f"✅ **تم تفعيل VIP للجروب** `{chat_id}` **لمدة 30 يوم**")
    try:
        await app.send_message(chat_id, "🎉 **تم تفعيل اشتراك VIP بنجاح**\nدلوقتي تقدر تستخدم.تصفية و.احصائية")
    except: pass

@app.on_message(filters.command("cancel_", prefixes=".") & filters.user(DEV_ID))
async def remove_vip(client, message: Message):
    chat_id = int(message.text.split("_")[1])
    await vips.delete_one({"chat_id": chat_id})
    await message.reply(f"❌ **تم إلغاء VIP للجروب** `{chat_id}`")

@app.on_message(filters.command("لوحة", prefixes=".") & filters.user(DEV_ID))
async def admin_panel(client, message: Message):
    vips_count = await vips.count_documents({"expire": {"$gt": datetime.now()}})
    users_count = await users.count_documents({})

    text = f"""
⚙️ **لوحة تحكم المطور**

👑 **الجروبات الـ VIP:** {vips_count}
👥 **اليوزرز المسجلين:** {users_count}

اختر العملية 👇
"""

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 الجروبات VIP", callback_data="show_all_vips")],
        [InlineKeyboardButton("👥 اليوزرز المسجلين", callback_data="show_users")],
        [
            InlineKeyboardButton("➕ تفعيل شهر", callback_data="add_vip_month"),
            InlineKeyboardButton("➖ إلغاء VIP", callback_data="remove_vip")
        ]
    ])
    await message.reply(text, reply_markup=buttons)

print("✅ البوت اشتغل")
app.run()
