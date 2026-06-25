import json
import os
import asyncio
from telethon import TelegramClient, events, Button
from datetime import datetime
import google.generativeai as genai
from openai import AsyncOpenAI

# ====== ايموجي بريميوم ======
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
# ============================

API_ID = 20867472 
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8837648752:AAHICVc71aEknIjgrE_FoOH2nln7oEOSNUA"
ADMIN_ID = 932862531 


bot = TelegramClient('ai_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'users': {},
        'settings': {
            'openai_key': os.getenv("OPENAI_KEY", ""),
            'gemini_key': os.getenv("GEMINI_KEY", ""),
            'provider': os.getenv("PROVIDER", "openai"),
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
        [Button.inline(f"{ROCKET} اسأل الذكاء الاصطناعي", b"ask_ai")],
        [Button.inline(f"{PC} مسح المحادثة", b"clear_chat")],
        [Button.url(f"{BOLT} مبرمجي", "https://t.me/Programmer_error")]
    ]

def get_admin_buttons():
    provider = db['settings']['provider']
    model = db['settings']['openai_model'] if provider == 'openai' else db['settings']['gemini_model']
    return [
        [Button.inline(f"{SPARK} اضافة OpenAI Key", b"set_openai")],
        [Button.inline(f"{SPARK} اضافة Gemini Key", b"set_gemini")],
        [Button.inline(f"{SIGNAL} المزود: {provider.upper()}", b"switch_provider")],
        [Button.inline(f"{PC} النموذج: {model}", b"select_model")],
        [Button.inline(f"{USER} الاحصائيات", b"stats")],
        [Button.inline(f"{PLANET} المستخدمين", b"users")],
        [Button.inline(f"{CHECK} رجوع", b"back_main")]
    ]

def get_model_buttons():
    provider = db['settings']['provider']
    models = OPENAI_MODELS if provider == 'openai' else GEMINI_MODELS
    current = db['settings']['openai_model'] if provider == 'openai' else db['settings']['gemini_model']
    buttons = []
    for m in models:
        icon = CHECK if m == current else BOLT
        buttons.append([Button.inline(f"{icon} {m}", f"model_{m}".encode())])
    buttons.append([Button.inline(f"{CHECK} رجوع", b"admin_panel")])
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
    genai.configure(api_key=db['settings']['gemini_key'])
    model = genai.GenerativeModel(db['settings']['gemini_model'])
    response = await model.generate_content_async(question)
    return response.text

@bot.on(events.NewMessage(pattern='/start'))
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
    text = (
        f"{SPARK} اهلا بيك في بوت الذكاء الاصطناعي {SPARK}\n\n"
        f"{PLANET} المزود: {provider}\n"
        f"{ROCKET} النموذج: {model}\n"
        f"{BOLT} اسأل عن اي حاجة\n"
        f"اختار من القائمة:"
    )
    await event.reply(text, buttons=get_main_buttons(), parse_mode='html', link_preview=False)

@bot.on(events.CallbackQuery)
async def callback(event):
    uid = str(event.sender_id)
    data = event.data.decode()
    try:
        if data == 'back_main':
            await start(event)
            return
        if data == 'ask_ai':
            waiting_for[uid] = 'waiting_question'
            provider = db['settings']['provider'].upper()
            model = db['settings']['openai_model'] if provider == 'OPENAI' else db['settings']['gemini_model']
            await event.edit(
                f"{CAT} ابعت سؤالك\n{SIGNAL} المزود: {provider}\n{ROCKET} النموذج: {model}",
                buttons=[[Button.inline("الغاء", b"back_main")]],
                parse_mode='html'
            )
        elif data == 'clear_chat':
            db['users'][uid]['history'] = []
            save_db()
            await event.answer(f"{CHECK} تم المسح", alert=True)
            await start(event)
        elif data == 'admin_panel':
            if int(uid)!= ADMIN_ID:
                await event.answer("ممنوع", alert=True)
                return
            text = f"{PC} لوحة الادمن المتطورة\n{SPARK} اختار العملية:"
            await event.edit(text, buttons=get_admin_buttons(), parse_mode='html')
        elif data == 'set_openai':
            if int(uid)!= ADMIN_ID: return
            waiting_for[uid] = 'waiting_openai'
            await event.edit(f"{LOCK} ابعت OpenAI API Key", buttons=[[Button.inline("الغاء", b"admin_panel")]], parse_mode='html')
        elif data == 'set_gemini':
            if int(uid)!= ADMIN_ID: return
            waiting_for[uid] = 'waiting_gemini'
            await event.edit(f"{LOCK} ابعت Gemini API Key", buttons=[[Button.inline("الغاء", b"admin_panel")]], parse_mode='html')
        elif data == 'switch_provider':
            if int(uid)!= ADMIN_ID: return
            current = db['settings']['provider']
            if current == 'openai' and db['settings']['gemini_key']:
                db['settings']['provider'] = 'gemini'
                msg = f"{CHECK} تم التبديل لـ Gemini"
            elif current == 'gemini' and db['settings']['openai_key']:
                db['settings']['provider'] = 'openai'
                msg = f"{CHECK} تم التبديل لـ OpenAI"
            else:
                msg = f"{LOCK} اضف المفتاح الاول"
            save_db()
            await event.answer(msg, alert=True)
            await event.edit(f"{PC} لوحة الادمن", buttons=get_admin_buttons(), parse_mode='html')
        elif data == 'select_model':
            if int(uid)!= ADMIN_ID: return
            provider = db['settings']['provider'].upper()
            await event.edit(f"{PC} اختار النموذج لـ {provider}", buttons=get_model_buttons(), parse_mode='html')
        elif data.startswith('model_'):
            if int(uid)!= ADMIN_ID: return
            model = data.replace('model_', '')
            provider = db['settings']['provider']
            if provider == 'openai':
                db['settings']['openai_model'] = model
            else:
                db['settings']['gemini_model'] = model
            save_db()
            await event.answer(f"{CHECK} تم التغيير لـ {model}", alert=True)
            await event.edit(f"{PC} لوحة الادمن", buttons=get_admin_buttons(), parse_mode='html')
        elif data == 'stats':
            if int(uid)!= ADMIN_ID: return
            provider = db['settings']['provider'].upper()
            model = db['settings']['openai_model'] if provider == 'OPENAI' else db['settings']['gemini_model']
            text = f"{SIGNAL} الاحصائيات\n{USER} المستخدمين: {db['stats']['total_users']}\n{ROCKET} الرسائل: {db['stats']['total_messages']}\n{SPARK} المزود: {provider}\n{PC} النموذج: {model}"
            await event.edit(text, buttons=[[Button.inline("رجوع", b"admin_panel")]], parse_mode='html')
        elif data == 'users':
            if int(uid)!= ADMIN_ID: return
            text = f"{USER} اخر 10 مستخدمين:\n\n"
            for i, (u_id, info) in enumerate(list(db['users'].items())[-10:], 1):
                text += f"{i}. {info['name']} - {info['messages']} رسالة\n"
            await event.edit(text, buttons=[[Button.inline("رجوع", b"admin_panel")]], parse_mode='html')
    except Exception as e:
        await event.answer(f"خطأ: {str(e)[:40]}", alert=True)

@bot.on(events.NewMessage)
async def handler(event):
    uid = str(event.sender_id)
    if uid in waiting_for:
        if waiting_for[uid] == 'waiting_openai' and int(uid) == ADMIN_ID:
            db['settings']['openai_key'] = event.raw_text.strip()
            save_db()
            del waiting_for[uid]
            await event.reply(f"{CHECK} تم حفظ OpenAI Key")
            return
        if waiting_for[uid] == 'waiting_gemini' and int(uid) == ADMIN_ID:
            db['settings']['gemini_key'] = event.raw_text.strip()
            save_db()
            del waiting_for[uid]
            await event.reply(f"{CHECK} تم حفظ Gemini Key")
            return
        if waiting_for[uid] == 'waiting_question':
            question = event.raw_text.strip()
            del waiting_for[uid]
            provider = db['settings']['provider']
            if provider == 'openai' and not db['settings']['openai_key']:
                await event.reply(f"{LOCK} الادمن مفعلش OpenAI Key")
                return
            if provider == 'gemini' and not db['settings']['gemini_key']:
                await event.reply(f"{LOCK} الادمن مفعلش Gemini Key")
                return
            msg = await event.reply(f"{BOLT} جاري التفكير...")
            try:
                if provider == 'openai':
                    answer = await ask_openai(question)
                else:
                    answer = await ask_gemini(question)
                db['stats']['total_messages'] += 1
                db['users'][uid]['messages'] += 1
                save_db()
                await msg.edit(f"{SPARK} الاجابة من {provider.upper()}:\n\n{answer}", buttons=get_main_buttons(), parse_mode='html')
            except Exception as e:
                await msg.edit(f"{LOCK} خطأ: {str(e)[:100]}")

print(f"{ROCKET} AI Bot is running...")
bot.run_until_disconnected()
