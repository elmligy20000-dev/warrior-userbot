
import asyncio
import io
from telethon import TelegramClient, events, Button
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات الأساسية (ضع بياناتك هنا) ---
API_ID = 20867472 
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
ADMIN_ID = 932862531 
SESSION_NAME = 'Iphone 17 Pro' # اسم ملف الجلسة (يجب أن يكون موجوداً في نفس المجلد)

# --- الرموز التعبيرية (للتجميل) ---
E = {
    'bolt': '⚡', 'dice': '🎲', 'spark': '✨', 
    'white': '⚪', 'dim': '🔹', 'error': '❌',
    'success': '✅', 'back': '🔙', 'menu': '🛠'
}

# --- تشغيل العملاء (Client Initialization) ---
# عميل Telethon (للتحكم بالحساب الشخصي)
user_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
# عميل Pyrogram (لإدارة البوت)
bot = Client("my_bot", bot_token=BOT_TOKEN)

# --- دالة الجلب (Extraction Engine) ---
async def extract_chats(mode):
    """دالة تجلب البيانات وتصنفها حسب الطلب"""
    extracted_data = []
    try:
        async for dialog in user_client.iter_dialogs():
            # 1. جلب الخاص (المستخدمين)
            if mode == "pvt" and dialog.is_user:
                extracted_data.append(f"👤 User: {dialog.name} | ID: {dialog.id}")

            # 2. جلب البوتات
            elif mode == "bot" and dialog.is_user:
                # ملاحظة: التحقق من كونه بوت يتطلب طلب معلومات الشات
                try:
                    entity = await user_client.get_entity(dialog.id)
                    if getattr(entity, 'bot', False):
                        extracted_data.append(f"🤖 Bot: {dialog.name} | ID: {dialog.id}")
                except: continue

            # 3. جلب الجروبات (استثناء الأدمن)
            elif mode == "grp" and dialog.is_group:
                perms = await user_client.get_permissions(dialog.id, 'me')
                if not perms.is_admin and not perms.is_creator:
                    extracted_data.append(f"👥 Group: {dialog.name} | ID: {dialog.id}")

            # 4. جلب القنوات (استثناء الأدمن)
            elif mode == "chn" and dialog.is_channel:
                perms = await user_client.get_permissions(dialog.id, 'me')
                if not perms.is_admin and not perms.is_creator:
                    extracted_data.append(f"📺 Channel: {dialog.name} | ID: {dialog.id}")

            # 5. جلب الكل
            elif mode == "all":
                if dialog.is_user:
                    extracted_data.append(f"👤 User/Bot: {dialog.name} | ID: {dialog.id}")
                elif dialog.is_group or dialog.is_channel:
                    perms = await user_client.get_permissions(dialog.id, 'me')
                    if not perms.is_admin and not perms.is_creator:
                        type_icon = "👥" if dialog.is_group else "📺"
                        extracted_data.append(f"{type_icon} Chat: {dialog.name} | ID: {dialog.id}")

        if not extracted_data:
            return None, "⚠️ لم يتم العثور على أي عناصر مطابقة."

        content = "\n".join(extracted_data)
        
        # إذا كان العدد كبير، نرسله كملف
        if len(extracted_data) > 50:
            file_buffer = io.BytesIO(content.encode('utf-8'))
            file_buffer.name = f"extracted_chats_{mode}.txt"
            return file_buffer, f"✅ تم جلب {len(extracted_data)} عنصر. (تم إنشاء ملف)"
        else:
            return content, f"✅ تم جلب {len(extracted_data)} عنصر."

    except Exception as e:
        return None, f"{E['error']} خطأ: {str(e)}"

# --- دالة الحذف (Cleaning Engine) ---
async def clean_chats(mode):
    """دالة الحذف المباشر"""
    count = 0
    try:
        async for dialog in user_client.iter_dialogs():
            should_delete = False
            
            if mode == "pvt" and dialog.is_user: should_delete = True
            elif mode == "grp" and dialog.is_group:
                perms = await user_client.get_permissions(dialog.id, 'me')
                if not perms.is_admin and not perms.is_creator: should_delete = True
            elif mode == "chn" and dialog.is_channel:
                perms = await user_client.get_permissions(dialog.id, 'me')
                if not perms.is_admin and not perms.is_creator: should_delete = True
            elif mode == "bot" and dialog.is_user:
                entity = await user_client.get_entity(dialog.id)
                if getattr(entity, 'bot', False): should_delete = True
            elif mode == "all":
                if dialog.is_user or dialog.is_group or dialog.is_channel:
                    perms = await user_client.get_permissions(dialog.id, 'me')
                    if not perms.is_admin and not perms.is_creator: should_delete = True

            if should_delete:
                await user_client.delete_dialog(dialog.id)
                count += 1
                await asyncio.sleep(0.5) # لتجنب الحظر

        return count
    except Exception as e:
        raise e

# --- أوامر البوت (Bot Handlers) ---

@bot.on_message(filters.command("start") & filters.user(ADMIN_ID))
async def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['menu']} لوحة التحكم", callback_data="main_menu")]
    ])
    await message.reply(f"👋 أهلاً بك يا مطور.\nاستخدم الزر أدناه للتحكم بالحساب.", reply_markup=keyboard)

@bot.on_callback_query(filters.regex("main_menu"))
async def main_menu(client, query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔍 جلب (بدون حذف)", callback_data="fetch_menu")],
        [InlineKeyboardButton(f"🧹 حذف (مباشر)", callback_data="clean_menu_direct")],
        [InlineKeyboardButton(f"{E['back']} رجوع", callback_data="back_to_start")]
    ])
    await query.edit_message_text(f"{E['bolt']} اختر العملية المطلوبة:", reply_markup=keyboard)

# --- قائمة خيارات الجلب ---
@bot.on_callback_query(filters.regex("fetch_menu"))
async def fetch_menu(client, query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 الخاص", callback_data="fetch_pvt"), InlineKeyboardButton("🤖 البوتات", callback_data="fetch_bot")],
        [InlineKeyboardButton("👥 الجروبات", callback_data="fetch_grp"), InlineKeyboardButton("📺 القنوات", callback_data="fetch_chn")],
        [InlineKeyboardButton("🧹 الكل", callback_data="fetch_all")],
        [InlineKeyboardButton(f"{E['back']} رجوع", callback_data="main_menu")]
    ])
    await query.edit_message_text(f"{E['dice']} ماذا تريد أن تجلب؟", reply_markup=keyboard)

# --- قائمة خيارات الحذف ---
@bot.on_callback_query(filters.regex("clean_menu_direct"))
async def clean_menu_direct(client, query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 الخاص", callback_data=&quot;del_pvt"), InlineKeyboardButton("🤖 البوتات", callback_data="del_bot")],
        [InlineKeyboardButton("👥 الجروبات", callback_data="del_grp"), InlineKeyboardButton("📺 القنوات", callback_data="del_chn")],
        [InlineKeyboardButton("🧹 الكل", callback_data="del_all")],
        [InlineKeyboardButton(f"{E['back']} رجوع", callback_data="main_menu")]
    ])
    await query.edit_message_text(f"{E['error']} ⚠️ تحذير: الحذف سيتم فوراً وبدون تراجع!", reply_markup=keyboard)

# --- معالجة عمليات الجلب (Execution) ---
@bot.on_callback_query(filters.regex("^fetch_"))
async def handle_fetch(client, query):
    mode_map = {"fetch_pvt":"pvt", "fetch_grp":"grp", "fetch_chn":"chn", "fetch_bot":"bot", "fetch_all":"all"}
    mode = mode_map.get(query.data)
    
    await query.answer("جاري المسح...", text_animation=True)
    await query.edit_message_text(f"{E['bolt']} جاري الفحص... قد يستغرق ذلك دقائق إذا كان العدد كبيراً.")

    result, msg = await extract_chats(mode)

    if result is None:
        await query.message.reply(msg)
    elif isinstance(result, bytes):
        await query.message.reply_document(document=result, caption=msg)
    else:
        await query.message.reply(f"{msg}\n\n`{result}`", parse_mode="Markdown")
    
    await query.message.reply(f"{E['back']} عد للقائمة الرئيسية:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرئيسية", callback_data="main_menu")]]))

# --- معالجة عمليات الحذف (Execution) ---
@bot.on_callback_query(filters.regex("^del_"))
async def handle_delete(client, query):
    mode_map = {"del_pvt":"pvt", "del_grp":"grp", "del_chn":"chn", "del_bot":"bot", "del_all":"all"}
    mode = mode_map.get(query.data)
    
    await query.edit_message_text(f"{E['error']} جاري الحذف... يرجى عدم إغلاق البوت.")
    
    try:
        count = await clean_chats(mode)
        await query.message.reply(f"{E['success']} تم حذف {count} عنصر بنجاح.")
    except Exception as e:
        await query.message.reply(f"{E['error']} حدث خطأ: {str(e)}")
    
    await query.message.reply(f"{E['back']} القائمة:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرئيسية", callback_data="main_menu")]]))

@bot.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query):
    await query.edit_message_text("👋 أهلاً بك يا مطور.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E['menu']} لوحة التحكم", callback_data="main_menu")]]))

# --- التشغيل الرئيسي ---
async def main():
    print("🚀 جاري تشغيل البوت والعميل...")
    await user_client.start()
    await bot.start()
    print("✅ البوت يعمل الآن!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
