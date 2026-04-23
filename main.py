from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio, os, aiohttp
from datetime import datetime
from pymongo import MongoClient

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")

app = Client("currency_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo.currency_bot
alerts = db.alerts

cache = {"time": None, "data": None}

CURRENCY_NAMES = {
    "usd": "دولار أمريكي 🇺🇸", "eur": "يورو 🇪🇺", "sar": "ريال سعودي 🇸🇦",
    "aed": "درهم إماراتي 🇦🇪", "kwd": "دينار كويتي 🇰🇼", "qar": "ريال قطري 🇶🇦",
    "omr": "ريال عماني 🇴🇲", "bhd": "دينار بحريني 🇧🇭", "jod": "دينار أردني 🇯🇴",
    "iqd": "دينار عراقي 🇮🇶", "gbp": "جنيه استرليني 🇬🇧", "chf": "فرنك سويسري 🇨🇭",
    "jpy": "ين ياباني 🇯🇵", "cad": "دولار كندي 🇨🇦", "aud": "دولار استرالي 🇦🇺",
    "cny": "يوان صيني 🇨🇳", "try": "ليرة تركي 🇹🇷", "inr": "روبية هندي 🇮🇳",
    "pkr": "روبية باكستاني 🇵🇰", "myr": "رينغيت ماليزي 🇲🇾"
}

async def get_prices():
    if cache["time"] and (datetime.now() - cache["time"]).seconds < 60:
        return cache["data"]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.exchangerate-api.com/v4/latest/USD") as r:
                forex = await r.json()
                rates = forex["rates"]

            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,toncoin,the-open-network,litecoin&vs_currencies=usd") as r:
                crypto = await r.json()
                ton_price = crypto.get("toncoin", {}).get("usd") or crypto.get("the-open-network", {}).get("usd", 5.5)

            data = {
                "usd": round(rates["EGP"], 2), "eur": round(rates["EGP"] / rates["EUR"], 2),
                "sar": round(rates["EGP"] / rates["SAR"], 2), "aed": round(rates["EGP"] / rates["AED"], 2),
                "kwd": round(rates["EGP"] / rates["KWD"], 2), "qar": round(rates["EGP"] / rates["QAR"], 2),
                "omr": round(rates["EGP"] / rates["OMR"], 2), "bhd": round(rates["EGP"] / rates["BHD"], 2),
                "jod": round(rates["EGP"] / rates["JOD"], 2), "iqd": round(rates["EGP"] / rates["IQD"], 4),
                "gbp": round(rates["EGP"] / rates["GBP"], 2), "chf": round(rates["EGP"] / rates["CHF"], 2),
                "jpy": round(rates["EGP"] / rates["JPY"], 4), "cad": round(rates["EGP"] / rates["CAD"], 2),
                "aud": round(rates["EGP"] / rates["AUD"], 2), "cny": round(rates["EGP"] / rates["CNY"], 2),
                "try": round(rates["EGP"] / rates["TRY"], 2), "inr": round(rates["EGP"] / rates["INR"], 2),
                "pkr": round(rates["EGP"] / rates["PKR"], 2), "myr": round(rates["EGP"] / rates["MYR"], 2),
                "btc": crypto["bitcoin"]["usd"], "eth": crypto["ethereum"]["usd"],
                "usdt": crypto["tether"]["usd"], "ton": ton_price,
                "ltc": crypto["litecoin"]["usd"],
                "updated": datetime.now().strftime("%I:%M %p")
            }

            cache["time"] = datetime.now()
            cache["data"] = data
            return data
            
    except Exception as e:
        print(f"Error fetching prices: {e}")
        if cache["data"]:
            return cache["data"]
        return {
            "usd": 48.5, "eur": 52.0, "sar": 12.9, "aed": 13.2, "kwd": 158.0,
            "qar": 13.3, "omr": 126.0, "bhd": 128.5, "jod": 68.4, "iqd": 0.037,
            "gbp": 61.0, "chf": 54.0, "jpy": 0.32, "cad": 35.5, "aud": 31.8,
            "cny": 6.7, "try": 1.5, "inr": 0.58, "pkr": 0.17, "myr": 10.8,
            "btc": 65000, "eth": 3200, "usdt": 1, "ton": 5.5, "ltc": 70,
            "updated": "Offline"
        }

async def check_alerts():
    while True:
        await asyncio.sleep(60)
        try:
            data = await get_prices()
            for alert in alerts.find({}):
                user_id = alert["user_id"]
                currency = alert["currency"]
                target = alert["target"]
                condition = alert["condition"]

                current = data[currency]
                triggered = False

                if condition == "above" and current >= target:
                    triggered = True
                    text = f"🚨 **تنبيه سعر!**\n\n{CURRENCY_NAMES.get(currency, currency.upper())} وصل `{current}`\nكنت طالب تنبيه لما يوصل `{target}` أو أعلى ⬆️"
                elif condition == "below" and current <= target:
                    triggered = True
                    text = f"🚨 **تنبيه سعر!**\n\n{CURRENCY_NAMES.get(currency, currency.upper())} نزل `{current}`\nكنت طالب تنبيه لما ينزل `{target}` أو أقل ⬇️"

                if triggered:
                    try:
                        await app.send_message(user_id, text)
                        alerts.delete_one({"_id": alert["_id"]})
                    except: pass
        except Exception as e:
            print(f"Alert Error: {e}")

@app.on_message(filters.command(["start", "اسعار"]))
async def start(client, message: Message):
    text = """
💰 **بوت أسعار العملات اللحظية**

**الأوامر الأساسية:**
`اسعار` - كل الأسعار المهمة
`عملات` - كل العملات العربية والأجنبية
`دولار` `يورو` `ريال` `درهم` `دينار` `عراقي`
`رصيد` - أسعار رصيد آسياسيل وزين
`بيتكوين` `لايت` `تون` `ايث`

**🔔 التنبيهات:**
`تنبيه دولار 50` `تنبيه يورو 55`
`تنبيهاتي` - عرض تنبيهاتك
`حذف التنبيهات` - حذف الكل

اكتب `سعر الدولار` وهيرد عليك 👇
"""
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 أهم الأسعار", callback_data="all_prices")],
        [InlineKeyboardButton("🌍 كل العملات", callback_data="all_currencies")],
        [
            InlineKeyboardButton("💰 دولار", callback_data="usd"),
            InlineKeyboardButton("💶 يورو", callback_data="eur"),
            InlineKeyboardButton("🇸🇦 ريال", callback_data="sar")
        ],
        [
            InlineKeyboardButton("🇮🇶 عراقي", callback_data="iqd"),
            InlineKeyboardButton("🔶 لايت", callback_data="ltc"),
            InlineKeyboardButton("💎 TON", callback_data="ton")
        ]
    ])
    await message.reply(text, reply_markup=btn)

@app.on_message(filters.command(["اسعار"]))
async def all_prices_cmd(client, message: Message):
    msg = await message.reply("⏳ جاري جلب الأسعار...")
    data = await get_prices()
    text = f"""
💰 **أهم الأسعار اللحظية**

**💵 العملات:**
دولار: `{data['usd']} جنيه`
يورو: `{data['eur']} جنيه`
ريال سعودي: `{data['sar']} جنيه`
درهم إماراتي: `{data['aed']} جنيه`
دينار كويتي: `{data['kwd']} جنيه`
دينار عراقي: `{data['iqd']} جنيه`

**₿ الكريبتو:**
بيتكوين: `${data['btc']:,}`
ايثريوم: `${data['eth']:,}`
لايتكوين: `${data['ltc']}`
تون: `${data['ton']}`

⏰ **آخر تحديث:** {data['updated']}
"""
    await msg.edit(text)

@app.on_message(filters.command(["عملات"]))
async def all_currencies_cmd(client, message: Message):
    msg = await message.reply("⏳ جاري جلب كل العملات...")
    data = await get_prices()

    text = "🌍 **أسعار كل العملات مقابل الجنيه**\n\n**💵 العملات العربية:**\n"
    for code in ["usd", "eur", "sar", "aed", "kwd", "qar", "omr", "bhd", "jod", "iqd"]:
        text += f"{CURRENCY_NAMES[code]}: `{data[code]} جنيه`\n"

    text += "\n**🌏 عملات آسيا:**\n"
    for code in ["cny", "jpy", "inr", "pkr", "myr", "try"]:
        text += f"{CURRENCY_NAMES[code]}: `{data[code]} جنيه`\n"

    text += "\n**🌐 عملات أخرى:**\n"
    for code in ["gbp", "chf", "cad", "aud"]:
        text += f"{CURRENCY_NAMES[code]}: `{data[code]} جنيه`\n"

    text += f"\n⏰ **آخر تحديث:** {data['updated']}"
    await msg.edit(text)

@app.on_message(filters.command(["دولار", "usd"]))
async def usd_price(client, message: Message):
    data = await get_prices()
    await message.reply(f"💵 **دولار أمريكي:** `{data['usd']} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["يورو", "eur"]))
async def eur_price(client, message: Message):
    data = await get_prices()
    await message.reply(f"💶 **يورو:** `{data['eur']} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["ريال", "sar"]))
async def sar_price(client, message: Message):
    data = await get_prices()
    await message.reply(f"🇸🇦 **ريال سعودي:** `{data['sar']} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["درهم", "aed"]))
async def aed_price(client, message: Message):
    data = await get_prices()
    await message.reply(f"🇦🇪 **درهم إماراتي:** `{data['aed']} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["دينار", "kwd"]))
async def kwd_price(client, message: Message):
    data = await get_prices()
    await message.reply(f"🇰🇼 **دينار كويتي:** `{data['kwd']} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["عراقي", "iqd", "دينار عراقي"]))
async def iqd_price(client, message: Message):
    data = await get_prices()
    iqd_1000_egp = round(data['iqd'] * 1000, 2)
    text = f"""
🇮🇶 **الدينار العراقي**

**1 دينار:** `{data['iqd']} جنيه`
**1000 دينار:** `{iqd_1000_egp} جنيه`
**100 دولار:** `{round(100 / (1/data['iqd']) * data['usd'], 0):,} دينار`

⏰ **آخر تحديث:** {data['updated']}
"""
    await message.reply(text)

@app.on_message(filters.command(["رصيد", "اسياسيل", "زين"]))
async def iraq_balance(client, message: Message):
    data = await get_prices()
    usd_iqd = round(1 / (data['iqd'] / data['usd']), 0)
    asiacell = round(usd_iqd * 1.08, 0)
    zain = round(usd_iqd * 1.09, 0)

    text = f"""
🇮🇶 **أسعار الرصيد العراقي - تقديري**

**💵 سعر الصرف:** 1$ = `{usd_iqd} دينار`

**📱 آسياسيل:** `{asiacell} دينار` لكل 1$
**📱 زين العراق:** `{zain} دينار` لكل 1$
**💳 ماستر كارد:** `{round(usd_iqd * 1.05, 0)} دينار` لكل 1$

*الأسعار تقريبية وتختلف حسب السوق*
⏰ **آخر تحديث:** {data['updated']}
"""
    await message.reply(text)

@app.on_message(filters.command(["بيتكوين", "btc"]))
async def btc_price(client, message: Message):
    data = await get_prices()
    btc_egp = round(data['btc'] * data['usd'], 0)
    await message.reply(f"₿ **بيتكوين:** `${data['btc']:,}` = `{btc_egp:,} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["لايت", "ltc", "لايتكوين"]))
async def ltc_price(client, message: Message):
    data = await get_prices()
    ltc_egp = round(data['ltc'] * data['usd'], 2)
    await message.reply(f"🔶 **Litecoin:** `${data['ltc']}` = `{ltc_egp} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["تون", "ton"]))
async def ton_price(client, message: Message):
    data = await get_prices()
    ton_egp = round(data['ton'] * data['usd'], 2)
    await message.reply(f"💎 **TON:** `${data['ton']}` = `{ton_egp} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["ايث", "eth", "ايثريوم"]))
async def eth_price(client, message: Message):
    data = await get_prices()
    eth_egp = round(data['eth'] * data['usd'], 0)
    await message.reply(f"💎 **ايثريوم:** `${data['eth']:,}` = `{eth_egp:,} جنيه`\n⏰ {data['updated']}")

@app.on_message(filters.command(["تنبيه"]))
async def set_alert(client, message: Message):
    if len(message.command) < 3:
        return await message.reply("❌ **استخدم:** `تنبيه دولار 50`\n`تنبيه يورو 55`\n`تنبيه دينار 160`")

    currency_input = message.command[1].lower()
    currency_map = {
        "دولار": "usd", "usd": "usd", "يورو": "eur", "eur": "eur",
        "ريال": "sar", "sar": "sar", "درهم": "aed", "aed": "aed",
        "دينار": "kwd", "kwd": "kwd", "عراقي": "iqd", "iqd": "iqd",
        "استرليني": "gbp", "gbp": "gbp", "تون": "ton", "ton": "ton",
        "لايت": "ltc", "ltc": "ltc", "لايتكوين": "ltc",
        "بيتكوين": "btc", "btc": "btc", "ايث": "eth", "eth": "eth"
    }

    if currency_input not in currency_map:
        return await message.reply("❌ **العملات المتاحة:** دولار، يورو، ريال، درهم، دينار، عراقي، استرليني، تون، لايت، بيتكوين، ايث")

    try:
        target = float(message.command[2])
    except:
        return await message.reply("❌ **اكتب رقم صحيح:** `تنبيه دولار 50`")

    data = await get_prices()
    currency_key = currency_map[currency_input]
    current = data[currency_key]
    condition = "above" if target > current else "below"

    alerts.insert_one({
        "user_id": message.from_user.id,
        "currency": currency_key,
        "target": target,
        "condition": condition,
        "created": datetime.now()
    })

    direction = "يوصل" if condition == "above" else "ينزل"
    await message.reply(f"✅ **تم ضبط التنبيه**\n\n🔔 هبعتلك لما {CURRENCY_NAMES.get(currency_key, currency_key.upper())} {direction} `{target}`\n📊 **السعر الحالي:** `{current}`")

@app.on_message(filters.command(["تنبيهاتي"]))
async def my_alerts(client, message: Message):
    user_alerts = []
    for alert in alerts.find({"user_id": message.from_user.id}):
        direction = "⬆️ أعلى من" if alert["condition"] == "above" else "⬇️ أقل من"
        name = CURRENCY_NAMES.get(alert['currency'], alert['currency'].upper())
        user_alerts.append(f"• {name} {direction} `{alert['target']}`")

    if not user_alerts:
        return await message.reply("❌ **معندكش تنبيهات**\nاستخدم `تنبيه دولار 50`")

    text = "🔔 **تنبيهاتك النشطة:**\n\n" + "\n".join(user_alerts)
    await message.reply(text)

@app.on_message(filters.command(["حذف"]))
async def delete_alerts(client, message: Message):
    if len(message.command) > 1 and message.command[1] == "التنبيهات":
        result = alerts.delete_many({"user_id": message.from_user.id})
        await message.reply(f"✅ **تم حذف {result.deleted_count} تنبيه**")

@app.on_message(filters.text & ~filters.command([]))
async def text_prices(client, message: Message):
    text = message.text.lower().strip()

    commands = ['start', 'اسعار', 'عملات', 'دولار', 'يورو', 'ريال', 'درهم', 'دينار', 'عراقي', 'رصيد', 'استرليني', 'بيتكوين', 'لايت', 'تون', 'ايث', 'تنبيه', 'تنبيهاتي', 'حذف']
    if any(text == cmd or text.startswith(cmd + ' ') for cmd in commands):
        return

    if any(word in text for word in ['سعر الدولار', 'بكام الدولار', 'الدولار']):
        data = await get_prices()
        await message.reply(f"💵 **دولار أمريكي:** `{data['usd']} جنيه`\n⏰ {data['updated']}")

    elif any(word in text for word in ['سعر اليورو', 'بكام اليورو', 'اليورو']):
        data = await get_prices()
        await message.reply(f"💶 **يورو:** `{data['eur']} جنيه`\n⏰ {data['updated']}")

    elif any(word in text for word in ['سعر الريال', 'بكام الريال', 'الريال']):
        data = await get_prices()
        await message.reply(f"🇸🇦 **ريال سعودي:** `{data['sar']} جنيه`\n⏰ {data['updated']}")

    elif any(word in text for word in ['سعر العراقي', 'الدينار العراقي', 'عراقي']):
        data = await get_prices()
        iqd_1000 = round(data['iqd'] * 1000, 2)
        await message.reply(f"🇮🇶 **دينار عراقي:** `{data['iqd']} جنيه`\n**1000 دينار:** `{iqd_1000} جنيه`\n⏰ {data['updated']}")

    elif any(word in text for word in ['رصيد', 'اسياسيل', 'زين العراق']):
        data = await get_prices()
        usd_iqd = round(1 / (data['iqd'] / data['usd']), 0)
        await message.reply(f"🇮🇶 **رصيد العراق:**\nآسياسيل: `{round(usd_iqd * 1.08, 0)} دينار/دولار`\nزين: `{round(usd_iqd * 1.09, 0)} دينار/دولار`\n⏰ {data['updated']}")

@app.on_callback_query()
async def buttons(client, callback_query):
    data = await get_prices()
    if callback_query.data == "all_prices":
        text = f"""
💰 **أهم الأسعار**

**💵 العملات:**
دولار: `{data['usd']}` | يورو: `{data['eur']}`
ريال: `{data['sar']}` | درهم: `{data['aed']}`
دينار: `{data['kwd']}` | عراقي: `{data['iqd']}`

**₿ الكريبتو:**
بيتكوين: `${data['btc']:,}`
لايتكوين: `${data['ltc']}`
تون: `${data['ton']}`

⏰ {data['updated']}
"""
    elif callback_query.data == "all_currencies":
        text = "🌍 **كل العملات:**\n\n"
        for code in ["usd", "eur", "sar", "aed", "kwd", "qar", "omr", "bhd", "jod", "iqd", "gbp", "chf", "jpy", "cad", "aud", "cny", "try"]:
            text += f"{CURRENCY_NAMES[code]}: `{data[code]}`\n"
        text += f"\n⏰ {data['updated']}"

    elif callback_query.data in data:
        name = CURRENCY_NAMES.get(callback_query.data, callback_query.data.upper())
        text = f"{name}: `{data[callback_query.data]}` جنيه\n⏰ {data['updated']}"

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 تحديث", callback_data="all_prices")],
        [InlineKeyboardButton("🌍 كل العملات", callback_data="all_currencies")]
    ])
    await callback_query.message.edit_text(text, reply_markup=btn)

async def main():
    await app.start()
    print("✅ بوت الأسعار اشتغل")
    asyncio.create_task(check_alerts())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
