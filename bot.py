import json
import os
import asyncio
import random
from telethon import TelegramClient, events, Button
from datetime import datetime
import google.generativeai as genai
from openai import AsyncOpenAI

# مفاتيح Gemini الافتراضية بتاعتك
GEMINI_KEYS = [
    "AQ.Ab8RN6ILnpoY378d8n5hUb6VJvz0rSlV5DC_xFdQ7ib1-RXRdQ",
    "AQ.Ab8RN6LHVg90hS6tSkX9KlscPfjqWbyUxIP2IowOOmo852C_Ow",
    "AQ.Ab8RN6ILWRjgUVTEF_2Y8hYrm6EXANjj93JXTSMF0r74BpNLoA"
]

API_ID = 20867472 
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
ADMIN_ID = 932862531 

DB_FILE = 'ai_bot_db.json'
waiting_for = {}

bot = TelegramClient('ai_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def b(text):
    """تحويل كل النص لعريض"""
    return f"**{text}**"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'users': {},
        'settings': {
            'openai_key': os.getenv("OPENAI_KEY", ""),
            'gemini_keys': GEMINI_KEYS,
            'provider': os.getenv("PROVIDER", "gemini"),
            'openai_model': 'gpt-3.5-turbo',
            'gemini_model': 'gemini-1.5-flash',
            'max_tokens': 1000
        },
        'stats': {'total_messages': 0, 'total_users': 0}
    }

def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()

OPENAI_MODELS = ['gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini']
GEMINI_MODELS = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']

def get_main_buttons():
    return [
        [Button.inline(b("اسأل الذكاء الاصطناعي"), b"ask_ai")],
        [Button.inline(b("مسح المحادثة"), b"clear_chat")],
        [Button.url(b("💻 المبرمج"), "https://t.me/Programmer_error")]
    ]

def get_admin_buttons():
    provider = db['settings']['provider']
    model = db['settings']['openai_model'] if provider == 'openai' else db['settings']['gemini_model']
    keys_count = len(db['settings']['gemini_keys'])
    openai_status = "✅" if db['settings']['openai_key'] else "❌"
    gemini_status = "✅" if keys_count > 0 else "❌"

    return [
        [Button.inline(b(f"🔑 OpenAI Key {openai_status}"), b"set_openai")],
        [Button.inline(b(f"🔑 Gemini Keys [{keys_count}] {gemini_status}"), b"manage_keys")],
        [Button.inline(b(f"📶 المزود: {provider.upper()}"), b"switch_provider")],
        [Button.inline(b(f"💻 النموذج: {model}"), b"select_model")],
        [Button.inline(b("👤 الاحصائيات"), b"stats")],
        [Button.inline(b("🪐 المستخدمين"), b"users")],
        [Button.inline(b("🗑️ مسح قاعدة البيانات"), b"reset_db")],
        [Button.inline(b("✅ رجوع"), b"back_main")]
    ]

def get_model_buttons():
    provider = db['settings']['provider']
    models = OPENAI_MODELS if provider == 'openai' else GEMINI_MODELS
    current = db['settings']['openai_model'] if provider == 'openai' else db['settings']['gemini_model']
    buttons = []
    for m in models:
        icon = "✅" if m == current else "⚡"
        buttons.append([Button.inline(b(f"{icon} {m}"), f"model_{m}".encode())])
    buttons.append([Button.inline(b("✅ رجوع"), b"admin_panel")])
    return buttons

async def ask_openai(question):
    client = AsyncOpenAI(api_key=db['settings']['openai_key'])
    response = await client.chat.completions.create(
        model=db['settings']['openai_model'],
        messages=[{"role": "user", "content": question}],
        max_tokens=db['settings']['max_tokens']
    )
    return response.choices[0].message.content

async def ask_gemini(question):
    key = random.choice(db['settings']['gemini_keys'])
    genai.configure(api_key=key)
    model = genai.GenerativeModel(db['settings']['gemini_model'])
    response = await model.generate_content_async(question)
    return response.text

@bot.on(events.NewMessage(pattern='/start', incoming=True))
async def start(event):
    uid = str(event.sender_id)

    if uid not in db['users']:
        db['users'][uid] = {
            'name': event.sender.first_name or 'User',
            'messages': 0,
            'join_date': datetime.now().isoformat(),
            'history': []
        }
        db['stats']['total_users'] += 1
        save_db()

    provider = db['settings']['provider'].upper()
    model = db['settings']['openai_model'] if provider == 'OPENAI' else db['settings']['gemini_model']

    # شلت اي كلام عن Gemini من الترحيب
    text = b(
        f"✨ اهلا بيك في بوت الذكاء الاصطناعي ✨\n\n"
        f"⚡ اسأل عن اي حاجة تختارها\n"
        f"اختر من القائمة:"
    )

    await event.reply(text, buttons=get_main_buttons(), link_preview=False, parse_mode='md')

@bot.on(events.CallbackQuery)
async def callback(event):
    uid = str(event.sender_id)
    data = event.data.decode()

    try:
        if event.is_group and int(uid)!= ADMIN_ID:
            await event.answer(b("لوحة الادمن للخاص فقط 🔒"), alert=True)
            return

        if data == 'back_main':
            await start(event)
            return

        if data == 'ask_ai':
            waiting_for[uid] = 'waiting_question'
            text = b("🐈 ابعت سؤالك دلوقتي")
            await event.edit(text, buttons=[[Button.inline(b("الغاء"), b"back_main")]])

        elif data == 'clear_chat':
            db['users'][uid]['history'] = []
            save_db()
            await event.answer(b("✅ تم المسح"), alert=True)
            await start(event)

        elif data == 'admin_panel':
            if int(uid)!= ADMIN_ID:
                await event.answer(b("ممنوع"), alert=True)
                return
            await event.edit(b("💻 لوحة التحكم الكاملة\nاختر العملية:"), buttons=get_admin_buttons(), parse_mode='md')

        elif data == 'set_openai':
            if int(uid)!= ADMIN_ID: return
            waiting_for[uid] = 'waiting_openai'
            text = b("🔒 ابعت مفتاح OpenAI الجديد\nهيتم استبدال القديم")
            await event.edit(text, buttons=[[Button.inline(b("الغاء"), b"admin_panel")]])

        elif data == 'manage_keys':
            if int(uid)!= ADMIN_ID: return
            keys_count = len(db['settings']['gemini_keys'])
            text = b(f"🔑 ادارة مفاتيح Gemini\nالعدد الحالي: {keys_count}\n\nاختر:")
            buttons = [
                [Button.inline(b("➕ اضافة مفتاح جديد"), b"set_gemini")],
                [Button.inline(b("👁️ عرض المفاتيح"), b"show_keys")],
                [Button.inline(b("🗑️ مسح كل المفاتيح"), b"clear_keys")],
                [Button.inline(b("✅ رجوع"), b"admin_panel")]
            ]
            await event.edit(text, buttons=buttons, parse_mode='md')

        elif data == 'set_gemini':
            if int(uid)!= ADMIN_ID: return
            waiting_for[uid] = 'waiting_gemini'
            await event.edit(b("🔒 ابعت مفتاح Gemini الجديد\nهيتضاف مع المفاتيح القديمة"), buttons=[[Button.inline(b("الغاء"), b"manage_keys")]])

        elif data == 'show_keys':
            if int(uid)!= ADMIN_ID: return
            keys = db['settings']['gemini_keys']
            if not keys:
                text = b("❌ لا توجد مفاتيح")
            else:
                text = b(f"🔑 المفاتيح المخزنة [{len(keys)}]:\n\n")
                for i, k in enumerate(keys, 1):
                    text += b(f"{i}. {k[:20]}...{k[-10:]}\n")
            await event.edit(text, buttons=[[Button.inline(b("رجوع"), b"manage_keys")]], parse_mode='md')

        elif data == 'clear_keys':
            if int(uid)!= ADMIN_ID: return
            db['settings']['gemini_keys'] = []
            save_db()
            await event.answer(b("🗑️ تم مسح كل المفاتيح"), alert=True)
            await event.edit(b("💻 لوحة التحكم"), buttons=get_admin_buttons(), parse_mode='md')

        elif data == 'switch_provider':
            if int(uid)!= ADMIN_ID: return
            current = db['settings']['provider']
            if current == 'openai' and len(db['settings']['gemini_keys']) > 0:
                db['settings']['provider'] = 'gemini'
                msg = b("✅ تم التبديل للمزود الثاني")
            elif current == 'gemini' and db['settings']['openai_key']:
                db['settings']['provider'] = 'openai'
                msg = b("✅ تم التبديل للمزود الاول")
            else:
                msg = b("🔒 اضف المفتاح الاول")
            save_db()
            await event.answer(msg, alert=True)
            await event.edit(b("💻 لوحة التحكم"), buttons=get_admin_buttons(), parse_mode='md')

        elif data == 'select_model':
            if int(uid)!= ADMIN_ID: return
            provider = db['settings']['provider'].upper()
            await event.edit(b(f"💻 اختر النموذج للمزود {provider}"), buttons=get_model_buttons(), parse_mode='md')

        elif data.startswith('model_'):
            if int(uid)!= ADMIN_ID: return
            model = data.replace('model_', '')
            provider = db['settings']['provider']
            if provider == 'openai':
                db['settings']['openai_model'] = model
            else:
                db['settings']['gemini_model'] = model
            save_db()
            await event.answer(b(f"✅ تم التغيير لـ {model}"), alert=True)
            await event.edit(b("💻 لوحة التحكم"), buttons=get_admin_buttons(), parse_mode='md')

        elif data == 'stats':
            if int(uid)!= ADMIN_ID: return
            provider = db['settings']['provider'].upper()
            model = db['settings']['openai_model'] if provider == 'OPENAI' else db['settings']['gemini_model']
            keys_count = len(db['settings']['gemini_keys'])
            text = b(
                f"📶 الاحصائيات الكاملة\n"
                f"👤 المستخدمين: {db['stats']['total_users']}\n"
                f"🚀 الرسائل: {db['stats']['total_messages']}\n"
                f"✨ المزود: {provider}\n"
                f"💻 النموذج: {model}\n"
                f"🔑 مفاتيح Gemini: {keys_count}"
            )
            await event.edit(text, buttons=[[Button.inline(b("رجوع"), b"admin_panel")]], parse_mode='md')

        elif data == 'users':
            if int(uid)!= ADMIN_ID: return
            text = b("👤 اخر 15 مستخدم:\n\n")
            for i, (u_id, info) in enumerate(list(db['users'].items())[-15:], 1):
                text += b(f"{i}. {info['name']} - {info['messages']} رسالة\n")
            await event.edit(text, buttons=[[Button.inline(b("رجوع"), b"admin_panel")]], parse_mode='md')

        elif data == 'reset_db':
            if int(uid)!= ADMIN_ID: return
            text = b("⚠️ متأكد عايز تمسح قاعدة البيانات كلها؟\nالمستخدمين والاحصائيات هتتمسح")
            buttons = [
                [Button.inline(b("نعم امسح"), b"confirm_reset")],
                [Button.inline(b("الغاء"), b"admin_panel")]
            ]
            await event.edit(text, buttons=buttons, parse_mode='md')

        elif data == 'confirm_reset':
            if int(uid)!= ADMIN_ID: return
            db['users'] = {}
            db['stats'] = {'total_messages': 0, 'total_users': 0}
            save_db()
            await event.answer(b("🗑️ تم مسح قاعدة البيانات"), alert=True)
            await event.edit(b("💻 لوحة التحكم"), buttons=get_admin_buttons(), parse_mode='md')

    except Exception as e:
        await event.answer(b(f"خطأ: {str(e)[:40]}"), alert=True)

@bot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private or e.is_group))
async def handler(event):
    uid = str(event.sender_id)

    if event.sender.bot:
        return

    # امر /keys للادمن
    if event.raw_text == '/keys' and int(uid) == ADMIN_ID and event.is_private:
        keys = db['settings']['gemini_keys']
        if not keys:
            await event.reply(b("❌ لا توجد مفاتيح مخزنة"))
        else:
            text = b(f"🔑 مفاتيح Gemini [{len(keys)}]:\n\n")
            for i, k in enumerate(keys, 1):
                text += b(f"{i}. {k[:25]}...{k[-10:]}\n")
        await event.reply(text, parse_mode='md')
        return

    if uid in waiting_for:
        if waiting_for[uid] == 'waiting_openai' and int(uid) == ADMIN_ID and event.is_private:
            db['settings']['openai_key'] = event.raw_text.strip()
            save_db()
            del waiting_for[uid]
            await event.reply(b("✅ تم حفظ مفتاح OpenAI"), parse_mode='md')
            return

        if waiting_for[uid] == 'waiting_gemini' and int(uid) == ADMIN_ID and event.is_private:
            new_key = event.raw_text.strip()
            if new_key not in db['settings']['gemini_keys']:
                db['settings']['gemini_keys'].append(new_key)
                save_db()
                msg = b(f"✅ تم اضافة المفتاح\nالاجمالي: {len(db['settings']['gemini_keys'])} مفتاح")
            else:
                msg = b("⚡ المفتاح موجود بالفعل")
            del waiting_for[uid]
            await event.reply(msg, parse_mode='md')
            return

        if waiting_for[uid] == 'waiting_question':
            question = event.raw_text.strip()
            del waiting_for[uid]
            provider = db['settings']['provider']

            if provider == 'openai' and not db['settings']['openai_key']:
                await event.reply(b("🔒 المفتاح غير موجود"), parse_mode='md')
                return

            if provider == 'gemini' and len(db['settings']['gemini_keys']) == 0:
                await event.reply(b("🔒 لا توجد مفاتيح"), parse_mode='md')
                return

            msg_wait = await event.reply(b("⚡ جاري المعالجة..."), parse_mode='md')
            try:
                if provider == 'openai':
                    answer = await ask_openai(question)
                else:
                    answer = await ask_gemini(question)

                db['stats']['total_messages'] += 1
                db['users'][uid]['messages'] += 1
                save_db()

                answer_text = b(f"✨ الاجابة:\n\n{answer}")
                await msg_wait.edit(answer_text, buttons=get_main_buttons(), parse_mode='md')
            except Exception as e:
                await msg_wait.edit(b(f"🔒 خطأ: {str(e)[:100]}"), parse_mode='md')

print(b("🚀 البوت شغال"))
bot.run_until_disconnected()
