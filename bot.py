import asyncio, json, os, secrets
from telethon import TelegramClient, events, Button, types
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityCustomEmoji

# ========= الاعدادات الثابته =========
API_ID = 20867472
API_HASH = 'abedd7fb77eaf1f88bd3f286ea952253'
BOT_TOKEN = '8603695783:AAG97upYHXXICtlowOe5zJWt_5aSpeFTKTA'
OWNER_ID = 932862531
PC = '<b><tg-emoji emoji-id="5886664420502805908">💻</tg-emoji></b>'
ACCOUNTS_DB = 'accounts.json'
SETTINGS_DB = 'settings.json'
# =====================================

bot = TelegramClient('panel', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
userbots = {}
subscribed_cache = {}

def pc(text): return text, [MessageEntityCustomEmoji(offset=0, length=2, document_id=PC_ID)]
def load(db): return json.load(open(db)) if os.path.exists(db) else {}
def save(db, d): json.dump(d, open(db,'w'), indent=2)
def make_key(): return "ERR-" + secrets.token_hex(4).upper()

def get_settings():
    s = load(SETTINGS_DB)
    if 'force_ch' not in s: s = {'force_ch': "@Programmer_error1", 'force_gp': "@Programmer_error2"}
    return s

def panel_kb():
    accs = load(ACCOUNTS_DB); s = get_settings()
    btns = []
    for i, sess in enumerate(accs.keys(), 1):
        st = "🟢" if accs[sess]['active'] else "🔴"
        lock = "🔓" if accs[sess]['activated'] else "🔒"
        btns.append([Button.inline(f"{st}{lock} حساب {i}", data=f"toggle_{sess}")])
    btns += [[Button.inline("⚙️ الاجباري", data="force_menu"), Button.inline("➕ كود", data="gen_code")],
             [Button.inline("▶️ تشغيل الكل", data="start_all"), Button.inline("⏹️ ايقاف الكل", data="stop_all")],
             [Button.url("👨‍💻 المبرمج", "https://t.me/Programmer_error")]]
    return btns

# ======== بوت التحكم =========
@bot.on(events.NewMessage(from_users=OWNER_ID, pattern='/panel'))
async def panel(e):
    accs = load(ACCOUNTS_DB); s = get_settings()
    text = f"""PC • 𝗩𝗜𝗣 𝗣𝗔𝗡𝗘𝗟
{PC} • ═══════════════
{PC} • 📢 قناة: {s['force_ch']}
{PC} • 👥 جروب: {s['force_gp']}
{PC} • 📦 الحسابات: {len(accs)}
{PC} • 🟢 شغال: {sum(1 for v in accs.values() if v['active'])}
{PC} • ═══════════════"""
    await e.reply(text, buttons=panel_kb(), formatting_entities=pc(text)[1])

@bot.on(events.NewMessage(from_users=OWNER_ID, pattern='/add (.+)'))
async def add(e):
    s = e.pattern_match.group(1)
    accs = load(ACCOUNTS_DB)
    if s in accs: return await e.reply("{PC} ❌ موجود")
    accs[s] = {"active": False, "activated": False, "code": None}
    save(ACCOUNTS_DB, accs)
    await e.reply("{PC} ✅ تمت اضافة الحساب\n{PC} استخدم /gen للكود")

@bot.on(events.NewMessage(from_users=OWNER_ID, pattern='/gen'))
async def gen(e):
    accs = load(ACCOUNTS_DB)
    if not accs: return await e.reply("{PC} ❌ مفيش حسابات")
    last_s = list(accs.keys())[-1]
    code = make_key()
    accs[last_s]['code'] = code
    save(ACCOUNTS_DB, accs)
    await e.reply(f"{PC} • كود تفعيل:\nPC ` {code} `\n\n{PC} ابعته للحساب", parse_mode='md')

@bot.on(events.CallbackQuery)
async def cb(e):
    d = e.data.decode(); accs = load(ACCOUNTS_DB); s = get_settings()
    if d == "force_menu":
        txt = f"PC • اعدادات الاجباري\n{PC} • قناة: {s['force_ch']}\n{PC} • جروب: {s['force_gp']}\n\n{PC} ارسل:\nPC /setch @القناة\n{PC} /setgp @الجروب"
        await e.edit(txt, buttons=[[Button.inline("🔙", data="back")]])
    elif d == "start_all":
        for sess in accs:
            if accs[sess]['activated'] and not accs[sess]['active']:
                asyncio.create_task(run_userbot(sess))
        await e.edit("{PC} ✅ جاري تشغيل المتفعلين", buttons=panel_kb())
    elif d == "stop_all":
        for sess in list(userbots.keys()):
            await userbots[sess].disconnect()
            accs[sess]['active'] = False
        userbots.clear(); save(ACCOUNTS_DB, accs)
        await e.edit("{PC} ⏹️ تم ايقاف الكل", buttons=panel_kb())
    elif d.startswith("toggle_"):
        sess = d.split("_",1)[1]
        if not accs[sess]['activated']: return await e.answer("PC 🔒 غير مفعل", alert=True)
        if accs[sess]['active']:
            await userbots[sess].disconnect(); del userbots[sess]; accs[sess]['active'] = False
        else: asyncio.create_task(run_userbot(sess))
        save(ACCOUNTS_DB, accs); await e.edit("PC تم", buttons=panel_kb())
    elif d == "back": await e.edit("PC • لوحة التحكم", buttons=panel_kb())

# اوامر تغيير الاجباري من البوت
@bot.on(events.NewMessage(from_users=OWNER_ID, pattern='/setch (.+)'))
async def setch(e):
    ch = e.pattern_match.group(1)
    s = get_settings(); s['force_ch'] = ch
    save(SETTINGS_DB, s)
    await e.reply(f"{PC} ✅ تم تغيير القناة الى: {ch}")

@bot.on(events.NewMessage(from_users=OWNER_ID, pattern='/setgp (.+)'))
async def setgp(e):
    gp = e.pattern_match.group(1)
    s = get_settings(); s['force_gp'] = gp
    save(SETTINGS_DB, s)
    await e.reply(f"{PC} ✅ تم تغيير الجروب الى: {gp}")

# ======== مشغل اليوزربوت =========
async def run_userbot(session_str):
    accs = load(ACCOUNTS_DB)
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    subscribed_cache[session_str] = set()
    userbots[session_str] = client

    @client.on(events.NewMessage(incoming=True, private=True))
    async def handler(event):
        me = await client.get_me()
        if event.sender_id == me.id: return
        uid = event.sender_id
        txt = event.raw_text.strip()
        s_data = accs.get(session_str, {})
        s = get_settings()
        FORCE_CH = s['force_ch']; FORCE_GP = s['force_gp']

        # 1. التفعيل
        if not s_data.get('activated'):
            if txt.startswith("ERR-") and txt == s_data.get('code'):
                accs[session_str]['activated'] = True; save(ACCOUNTS_DB, accs)
                msg, ent = pc("{PC} • ✅ تم تفعيل الحساب\n{PC} • ارجع للمطور")
                await event.reply(msg, formatting_entities=ent)
            else:
                msg, ent = pc("{PC} • 🔒 الحساب غير مفعل\n{PC} • راسل @Programmer_error")
                await event.reply(msg, formatting_entities=ent)
            return

        # 2. فحص الاشتراك
        try:
            await client.get_participant(FORCE_CH, uid)
            await client.get_participant(FORCE_GP, uid)
            if uid not in subscribed_cache[session_str]:
                subscribed_cache[session_str].add(uid)
                text = f"""{PC} • 𝗪𝗘𝗟𝗖𝗢𝗠𝗘
{PC} • ══════════
{PC} • اهلا بك {event.sender.first_name} 👋
{PC} • تم التحقق ✅
{PC} • ══════════"""
                btns = [[Button.url("👨‍💻 المبرمج", "https://t.me/Programmer_error")],
                        [Button.url("📢 السورس", f"https://t.me/{FORCE_CH.replace('@','')}")]]
                msg, ent = pc(text)
                await client.send_message(uid, msg, buttons=btns, formatting_entities=ent)
            return
        except: pass

        # 3. مش مشترك
        await event.delete()
        if txt == "تم":
            try:
                await client.get_participant(FORCE_CH, uid); await client.get_participant(FORCE_GP, uid)
                subscribed_cache[session_str].add(uid); return
            except: pass

        text = f"""{PC} • مرحبا 👋
{PC} • للتواصل يجب الاشتراك أولاً
{PC} • اضغط بالأسفل
{PC} • قناة السورس : ‹@{FORCE_CH.replace('@','')}›.
{PC} • جروب الدعم : ‹@{FORCE_GP.replace('@','')}›."""
        btns = [[Button.url("قناة السورس", f"https://t.me/{FORCE_CH.replace('@','')}")],
                [Button.url("جروب الدعم", f"https://t.me/{FORCE_GP.replace('@','')}")]]
        msg, ent = pc(text)
        w = await client.send_message(uid, msg, buttons=btns, formatting_entities=ent)
        await asyncio.sleep(8); await w.delete()

    await client.start()
    accs[session_str]['active'] = True; save(ACCOUNTS_DB, accs)
    await client.run_until_disconnected()
    accs[session_str]['active'] = False; save(ACCOUNTS_DB, accs)
    if session_str in userbots: del userbots[session_str]

# ======== التشغيل =========
print("PC • 𝗩𝗜𝗣 𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗧𝗔𝗥𝗧𝗘𝗗")
for s, v in load(ACCOUNTS_DB).items():
    if v['activated'] and v['active']:
        asyncio.create_task(run_userbot(s))

bot.run_until_disconnected()
