import sqlite3
import json
import os
import time
import random
import telebot
from telebot import types
import requests
from datetime import datetime
import traceback

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

token = "8603287845:AAH_KgPlaPxzVXQlrxyTyZmlisXDU-kANIE"
bot = telebot.TeleBot(token)

ADMIN_ID = 8085768728

def init_db():
    conn = sqlite3.connect('freenum.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        active INTEGER DEFAULT 1,
        balance REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        code TEXT,
        price REAL DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        country_name TEXT,
        number TEXT,
        status TEXT DEFAULT 'active',
        otp_code TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS numbers (
        country_name TEXT,
        number TEXT,
        used INTEGER DEFAULT 0,
        PRIMARY KEY (country_name, number)
    )
    ''')
    
    default_settings = [
        ('bot_locked', 'false'),
        ('lock_message', '*⛔️ ⌯ البوت حاليا في حالة صيانة، يرجى الانتضار إلى أن ينتهي الفريق البرمجي من إجراء الصيانة والتحديثات🙂💙.*'),
        ('bot_channel', 'https://t.me/X5HDO'),
        ('user_join_channel', ''),
        ('otp_received_channel', ''),
        ('incomplete_orders_channel', ''),
        ('activations_channel', '-1003264480944'),
        ('publish_activations', 'true')
    ]
    
    for key, value in default_settings:
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()

init_db()

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def get_db_connection():
    return sqlite3.connect('freenum.db')

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'user_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'active': bool(user[3]),
            'balance': user[4],
            'created_at': user[5]
        }
    return None

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def create_user(user_id, username, first_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', 
                   (user_id, username, first_name))
    conn.commit()
    conn.close()

def update_user_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def is_banned(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def ban_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def unban_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# برمجة يوسف

# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def get_setting(key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

# برمجة يوسف

# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def get_countries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM countries ORDER BY name')
    countries = cursor.fetchall()
    conn.close()
    
    return [{
        'id': c[0],
        'name': c[1],
        'code': c[2],
        'price': c[3]
    } for c in countries]

def add_country(name, code, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO countries (name, code, price) VALUES (?, ?, ?)', (name, code, price))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# برمجة يوسف

# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def delete_country(country_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM countries WHERE id = ?', (country_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def get_available_numbers(country_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT number FROM numbers WHERE country_name = ? AND used = 0', (country_name,))
    numbers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return numbers

# برمجة يوسف

# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def add_number(country_name, number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR IGNORE INTO numbers (country_name, number) VALUES (?, ?)', (country_name, number))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# برمجة يوسف

# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def mark_number_used(country_name, number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE numbers SET used = 1 WHERE country_name = ? AND number = ?', (country_name, number))
    conn.commit()
    conn.close()

def get_random_number(country_name):
    numbers = get_available_numbers(country_name)
    if not numbers:
        return None
    number = random.choice(numbers)
    mark_number_used(country_name, number)
    return number

# برمجة يوسف

# يوزري @oosss44
# قناة الملفات @X5HDO

#حقوقي شرفك لا تلعب بشرفك

def create_order(user_id, country_name, number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, country_name, number, status) 
        VALUES (?, ?, ?, 'active')
    ''', (user_id, country_name, number))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def get_active_order(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM orders 
        WHERE user_id = ? AND status = 'active' 
        ORDER BY created_at DESC LIMIT 1
    ''', (user_id,))
    order = cursor.fetchone()
    conn.close()
    
    if order:
        return {
            'id': order[0],
            'user_id': order[1],
            'country_name': order[2],
            'number': order[3],
            'status': order[4],
            'otp_code': order[5],
            'created_at': order[6]
        }
    return None

def update_order_otp(order_id, otp_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET otp_code = ?, status = "completed" WHERE id = ?', (otp_code, order_id))
    conn.commit()
    conn.close()

def cancel_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT country_name, number FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone()
    
    if order:
        country_name, number = order
        
        cursor.execute('UPDATE numbers SET used = 0 WHERE country_name = ? AND number = ?', (country_name, number))
        
        cursor.execute('UPDATE orders SET status = "cancelled" WHERE id = ?', (order_id,))
    
    conn.commit()
    conn.close()

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def change_order_number(order_id, new_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT country_name, number FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone()
    
    if order:
        country_name, old_number = order
        
        cursor.execute('UPDATE numbers SET used = 0 WHERE country_name = ? AND number = ?', (country_name, old_number))
        
        mark_number_used(country_name, new_number)
        
        cursor.execute('''
            UPDATE orders 
            SET number = ?, otp_code = NULL, created_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_number, order_id))
    
    conn.commit()
    conn.close()

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

API_KEY = "G8vC2xZ5bN7mM4qW1eR3"

def fetch_numbers_from_api(country_name):
    countries = get_countries()
    country_code = None
    
    for country in countries:
        if country['name'] == country_name:
            country_code = country['code']
            break
    
    if not country_code:
        return False
    
    try:
        response = requests.get(f"http://hamadh.store/n/router.php?ye={API_KEY}&country={country_code}")
        data = response.json()
        
        if data.get('success') and data.get('number'):
            add_number(country_name, data['number'])
            return True
    except:
        pass
    
    return False

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def get_otp_from_api(number):
    try:
        cleaned_number = str(number).replace('+', '').replace(' ', '')
        response = requests.get(f"http://hamadh.store/y/mo.php?number={cleaned_number}")
        data = response.json()
        
        if 'otp' in data:
            return data['otp']
    except:
        pass
    
    return None

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

def send_notification(channel_type, message, reply_markup=None):
    channel_id = get_setting(f'{channel_type}_channel')
    if channel_id and channel_id.strip():
        try:
            if reply_markup:
                bot.send_message(channel_id, message, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                bot.send_message(channel_id, message, parse_mode='Markdown')
            return True
        except:
            pass
    return False

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {str(e)}")
            print(traceback.format_exc())
    return wrapper

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

@bot.message_handler(commands=['start'])
@handle_errors
def start_command(message):
    user_id = message.from_user.id
    
    if get_setting('bot_locked') == 'true' and user_id != ADMIN_ID:
        bot.send_message(message.chat.id, get_setting('lock_message'), parse_mode='Markdown')
        return
    
    if is_banned(user_id) and user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "*❌ ⌯ تم حظرك من استخدام البوت.*", parse_mode='Markdown')
        return
    
    create_user(user_id, message.from_user.username, message.from_user.first_name)
    
    username_display = f"**@{message.from_user.username}**" if message.from_user.username else "*⌯ لا يوجد*"
    
    if user_id == ADMIN_ID:
        welcome_text = f"""*♻️ ⌯ اهلا بك عزيزي الادمن في لوحه التحكم اختر زر من الأزرار التاليه*

*🆔 ⌯ ايدي حسابك:* `{user_id}`

*⬇️ ⌯ تحكم عبر الأزرار التالية ⬇️*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("اضافه دوله", callback_data="addcountry"),
            types.InlineKeyboardButton("حذف دوله", callback_data="delcountry")
        )
        markup.row(types.InlineKeyboardButton("رموز الدول", callback_data="country_codes"))
        markup.row(
            types.InlineKeyboardButton("حظر مستخدم", callback_data="banuser"),
            types.InlineKeyboardButton("فك حظر مستخدم", callback_data="unbanuser")
        )
        markup.row(types.InlineKeyboardButton("ادارة قنوات الاشعارات", callback_data="notification_channels"))
        markup.row(types.InlineKeyboardButton("☎️ ⌯ شراء ارقام", callback_data="buy_number"))
        markup.row(
            types.InlineKeyboardButton("📮 ⌯ الدعم المباشر", url="https://t.me/oosss44"),
            types.InlineKeyboardButton("🚦 ⌯ قناة البوت", url="https://t.me/X5HDO")
        )
    else:
        welcome_text = f"""*🤖 ⌯ اهلا بك عزيزي المستخدم في بوت الارقام المجانية 👋*

*🆔 ⌯ ايدي حسابك:* `{user_id}`

*⬇️ ⌯ تحكم عبر الأزرار التالية ⬇️*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("☎️ ⌯ شراء ارقام", callback_data="buy_number"))
        markup.row(
            types.InlineKeyboardButton("📮 ⌯ الدعم المباشر", url="https://t.me/oosss44"),
            types.InlineKeyboardButton("🚦 ⌯ قناة البوت", url="https://t.me/X5HDO")
        )
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        disable_web_page_preview=True,
        reply_markup=markup
    )
    
    user_info = get_user(user_id)
    if user_info and user_id != ADMIN_ID:
        notification_text = f"""*👤 ⌯ دخول مستخدم جديد*

*👤 ⌯ الاسم:* {message.from_user.first_name}
*📛 ⌯ اليوزر:* {username_display}
*🆔 ⌯ الايدي:* `{user_id}`
*⏰ ⌯ الوقت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        send_notification('user_join', notification_text)

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

@bot.callback_query_handler(func=lambda call: True)
@handle_errors
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if is_banned(user_id) and user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ تم حظرك من استخدام البوت", show_alert=True)
        return
    
    if call.data == "back_to_menu":
        if user_id == ADMIN_ID:
            text = f"""*♻️ ⌯ اهلا بك عزيزي الادمن في لوحه التحكم اختر زر من الأزرار التاليه*

*🆔 ⌯ ايدي حسابك:* `{user_id}`

*⬇️ ⌯ تحكم عبر الأزرار التالية ⬇️*"""
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("اضافه دوله", callback_data="addcountry"),
                types.InlineKeyboardButton("حذف دوله", callback_data="delcountry")
            )
            markup.row(types.InlineKeyboardButton("رموز الدول", callback_data="country_codes"))
            markup.row(
                types.InlineKeyboardButton("حظر مستخدم", callback_data="banuser"),
                types.InlineKeyboardButton("فك حظر مستخدم", callback_data="unbanuser")
            )
            markup.row(types.InlineKeyboardButton("ادارة قنوات الاشعارات", callback_data="notification_channels"))
            markup.row(types.InlineKeyboardButton("☎️ ⌯ شراء ارقام", callback_data="buy_number"))
            markup.row(
                types.InlineKeyboardButton("📮 ⌯ الدعم المباشر", url="https://t.me/oosss44"),
                types.InlineKeyboardButton("🚦 ⌯ قناة البوت", url="https://t.me/X5HDO")
            )
        else:
            text = f"""*🤖 ⌯ اهلا بك عزيزي المستخدم في بوت الارقام المجانية 👋*

*🆔 ⌯ ايدي حسابك:* `{user_id}`

*⬇️ ⌯ تحكم عبر الأزرار التالية ⬇️*"""
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("☎️ ⌯ شراء ارقام", callback_data="buy_number"))
            markup.row(
                types.InlineKeyboardButton("📮 ⌯ الدعم المباشر", url="https://t.me/oosss44"),
                types.InlineKeyboardButton("🚦 ⌯ قناة البوت", url="https://t.me/X5HDO")
            )
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=markup
        )
    
    elif call.data == "country_codes" and user_id == ADMIN_ID:
        countries = get_countries()
        
        if not countries:
            bot.edit_message_text(
                "*❌ ⌯ لا توجد دول مضافة حالياً.*",
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="adminback")
                )
            )
            return
        
        text = "*⌯ كل دولة لها رمز مثال*\n\n"
        for country in countries:
            text += f"*⌯ {country['name']} [ {country['code']} ]*\n"
        
        text += "\n*⌯ يمكنك استخدام هذه الرموز في إضافة الأرقام من الـ API*"
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="adminback")
            )
        )
    
    elif call.data == "buy_number":
        countries = get_countries()
        
        if not countries:
            bot.edit_message_text(
                "*❌ ⌯ لا توجد دول متاحة حالياً.*\n*⌯ يرجى المحاولة لاحقاً.*",
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="back_to_menu")
                )
            )
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("السعر 💰", callback_data="price_header"),
            types.InlineKeyboardButton("الدولة ☑️", callback_data="country_header")
        )
        
        for country in countries:
            available_numbers = len(get_available_numbers(country['name']))
            price_text = f"{country['price']} نقطة💸" if country['price'] > 0 else "0 نقطة💸"
            
            markup.row(
                types.InlineKeyboardButton(price_text, callback_data=f"buy_{country['name']}"),
                types.InlineKeyboardButton(country['name'], callback_data=f"buy_{country['name']}")
            )
        
        markup.row(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu"))
        
        bot.edit_message_text(
            "*🌍 ⌯ اختر الدولة:*\n\n*⌯ يرجى الضغط على الدولة المراد سحب رقم لها♻️*",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data.startswith("buy_") and call.data != "buy_number":
        country_name = call.data.replace("buy_", "")
        
        countries = get_countries()
        country_price = 0
        for country in countries:
            if country['name'] == country_name:
                country_price = country['price']
                break
        
        number = get_random_number(country_name)
        
        if not number:
            if fetch_numbers_from_api(country_name):
                number = get_random_number(country_name)
            
            if not number:
                bot.edit_message_text(
                    "*❌ ⌯ لا توجد أرقام متاحة لهذه الدولة حالياً.*",
                    chat_id,
                    message_id,
                    parse_mode='Markdown',
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="buy_number")
                    )
                )
                return
        
        order_id = create_order(user_id, country_name, number)
        
        current_time = datetime.now()
        time_text = f"{current_time.day}|{['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'][current_time.weekday()]}|{current_time.strftime('%I:%M')} {'صباحاً' if current_time.hour < 12 else 'مساءً'}"
        
        text = f"""*☑️ ⌯ تم شراء الرقم بنجاح ✅*

*🌐 ⌯ الدولة:* {country_name}
*☎️ ⌯ الرقم:* `{number}`
*💰 ⌯ السعر:* {country_price} نقطة
*💭 ⌯ الكود:* لم يصل بعد...
*📅 ⌯ الوقت:* {time_text}

*🌀 ⌯ التعليمات:*
*🔰 ⌯ قم بإدخال الرقم في تطبيق واتساب ، ثم قم بطلب الكود عبر زر طلب الكود اسفل.*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("☑️ ⌯ طلب الكود", callback_data="request_otp"))
        markup.row(
            types.InlineKeyboardButton("🔄 ⌯ تغيير الرقم", callback_data="change_number"),
            types.InlineKeyboardButton("❎ ⌯ إلغاء الرقم", callback_data="cancel_order")
        )
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        user_info = get_user(user_id)
        username_display = f"**@{user_info['username']}**" if user_info and user_info['username'] else "*⌯ لا يوجد*"
        
        notification_text = f"""*🛒 ⌯ طلب جديد غير مكتمل*

*👤 ⌯ المستخدم:* {call.from_user.first_name}
*📛 ⌯ اليوزر:* {username_display}
*🆔 ⌯ الايدي:* `{user_id}`
*🌍 ⌯ الدولة:* {country_name}
*📞 ⌯ الرقم:* {number}
*💰 ⌯ السعر:* {country_price} نقطة
*⏰ ⌯ الوقت:* {current_time.strftime('%Y-%m-%d %H:%M:%S')}"""
        
        send_notification('incomplete_orders', notification_text)
    
    elif call.data == "request_otp":
        order = get_active_order(user_id)
        
        if not order:
            bot.answer_callback_query(call.id, "*❌ ⌯ لا يوجد طلب نشط.*", show_alert=True)
            return
        
        if order['otp_code']:
            countries = get_countries()
            country_price = 0
            for country in countries:
                if country['name'] == order['country_name']:
                    country_price = country['price']
                    break
            
            current_time = datetime.now()
            time_text = f"{current_time.day}|{['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'][current_time.weekday()]}|{current_time.strftime('%I:%M')} {'صباحاً' if current_time.hour < 12 else 'مساءً'}"
            
            text = f"""*☑️ ⌯ تم شراء الرقم بنجاح ✅*

*🌐 ⌯ الدولة:* {order['country_name']}
*☎️ ⌯ الرقم:* `{order['number']}`
*💰 ⌯ السعر:* {country_price} نقطة
*💭 ⌯ الكود:* `{order['otp_code']}`
*📅 ⌯ الوقت:* {time_text}

*🌀 ⌯ التعليمات:*
*🔰 ⌯ قم بإدخال الرقم في تطبيق واتساب ، ثم قم بطلب الكود عبر زر طلب الكود اسفل.*"""
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🛒 ⌯ شراء رقم جديد", callback_data="buy_number"))
            
            bot.edit_message_text(
                text,
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
            return
        
        bot.edit_message_text(
            "*⏳ ⌯ جاري جلب الكود... الرجاء الانتظار*",
            chat_id,
            message_id,
            parse_mode='Markdown'
        )
        
        otp = get_otp_from_api(order['number'])
        
        countries = get_countries()
        country_price = 0
        for country in countries:
            if country['name'] == order['country_name']:
                country_price = country['price']
                break
        
        current_time = datetime.now()
        time_text = f"{current_time.day}|{['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'][current_time.weekday()]}|{current_time.strftime('%I:%M')} {'صباحاً' if current_time.hour < 12 else 'مساءً'}"
        
        if otp:
            update_order_otp(order['id'], otp)
            
            text = f"""*☑️ ⌯ تم شراء الرقم بنجاح ✅*

*🌐 ⌯ الدولة:* {order['country_name']}
*☎️ ⌯ الرقم:* `{order['number']}`
*💰 ⌯ السعر:* {country_price} نقطة
*💭 ⌯ الكود:* `{otp}`
*📅 ⌯ الوقت:* {time_text}

*🌀 ⌯ التعليمات:*
*🔰 ⌯ قم بإدخال الرقم في تطبيق واتساب ، ثم قم بطلب الكود عبر زر طلب الكود اسفل.*"""
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🛒 ⌯ شراء رقم جديد", callback_data="buy_number"))
            
            bot.edit_message_text(
                text,
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
            
            user_info = get_user(user_id)
            username_display = f"**@{user_info['username']}**" if user_info and user_info['username'] else "*⌯ لا يوجد*"
            
            notification_text = f"""*💬 ⌯ تم وصول كود جديد*

*👤 ⌯ المستخدم:* {call.from_user.first_name}
*📛 ⌯ اليوزر:* {username_display}
*🆔 ⌯ الايدي:* `{user_id}`
*📞 ⌯ الرقم:* {order['number']}
*🔑 ⌯ الكود:* {otp}
*🌍 ⌯ الدولة:* {order['country_name']} 
*💙 ⌯ السعر:* {country_price} نقطة
*⏰ ⌯ الوقت:* {current_time.strftime('%Y-%m-%d %H:%M:%S')}"""
            
            send_notification('otp_received', notification_text)
            
            if get_setting('publish_activations') == 'true':
                masked_number = order['number'][:-4] + "••••" if len(order['number']) >= 4 else order['number']
                masked_user_id = str(user_id)[:-3] + "•••" if len(str(user_id)) >= 3 else str(user_id)
                
                activation_text = f"""*🛰︙تم تنفيذ طلب خدمة رقمية عبر [ خدمات مجانية| Free bots 📲 ] بنجاح.*

*🎰︙النظام:* WA
*🌐︙المنطقة:* {order['country_name']} 

*📎︙المعرّف:* {masked_number}
*🆔︙المستخدم:* {masked_user_id}
*💵︙القيمة:* $ 0
*🔐︙رمز المعالجة:* [ {otp} ]

*📆︙تاريخ العملية:* {current_time.strftime('%Y-%m-%d %H:%M:%S')}"""
                
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton(f"رمز المعالجة: {otp}", callback_data="empty_callback"))
                markup.row(types.InlineKeyboardButton("▰{ ✅️ بوت الطلبات }▰", url="https://t.me/N4S5bot"))
                
                send_notification('activations', activation_text, markup)
        else:
            text = f"""*☑️ ⌯ تم شراء الرقم بنجاح ✅*

*🌐 ⌯ الدولة:* {order['country_name']}
*☎️ ⌯ الرقم:* `{order['number']}`
*💰 ⌯ السعر:* {country_price} نقطة
*💭 ⌯ الكود:* لم يصل بعد...
*📅 ⌯ الوقت:* {time_text}

*🌀 ⌯ التعليمات:*
*🔰 ⌯ قم بإدخال الرقم في تطبيق واتساب ، ثم قم بطلب الكود عبر زر طلب الكود اسفل.*"""
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("☑️ ⌯ طلب الكود", callback_data="request_otp"))
            markup.row(
                types.InlineKeyboardButton("🔄 ⌯ تغيير الرقم", callback_data="change_number"),
                types.InlineKeyboardButton("❎ ⌯ إلغاء الرقم", callback_data="cancel_order")
            )
            
            bot.edit_message_text(
                text,
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    elif call.data == "change_number":
        order = get_active_order(user_id)
        
        if not order:
            bot.answer_callback_query(call.id, "*ليس لديك طلب نشط*", show_alert=True)
            return
        
        order_time = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        time_diff = (current_time - order_time).total_seconds()
        
        if time_diff < 3:
            bot.answer_callback_query(call.id, "*يمكنك تغيير رقم بعد 3 ثواني ⚠️*", show_alert=True)
            return
        
        new_number = get_random_number(order['country_name'])
        
        if not new_number:
            if fetch_numbers_from_api(order['country_name']):
                new_number = get_random_number(order['country_name'])
            
            if not new_number:
                bot.edit_message_text(
                    "*❌ ⌯ لا توجد أرقام متاحة لهذه الدولة حالياً.*",
                    chat_id,
                    message_id,
                    parse_mode='Markdown',
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="buy_number")
                    )
                )
                return
        
        change_order_number(order['id'], new_number)
        
        countries = get_countries()
        country_price = 0
        for country in countries:
            if country['name'] == order['country_name']:
                country_price = country['price']
                break
        
        current_time = datetime.now()
        time_text = f"{current_time.day}|{['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'][current_time.weekday()]}|{current_time.strftime('%I:%M')} {'صباحاً' if current_time.hour < 12 else 'مساءً'}"
        
        text = f"""*☑️ ⌯ تم شراء الرقم بنجاح ✅*

*🌐 ⌯ الدولة:* {order['country_name']}
*☎️ ⌯ الرقم:* `{new_number}`
*💰 ⌯ السعر:* {country_price} نقطة
*💭 ⌯ الكود:* لم يصل بعد...
*📅 ⌯ الوقت:* {time_text}

*🌀 ⌯ التعليمات:*
*🔰 ⌯ قم بإدخال الرقم في تطبيق واتساب ، ثم قم بطلب الكود عبر زر طلب الكود اسفل.*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("☑️ ⌯ طلب الكود", callback_data="request_otp"))
        markup.row(
            types.InlineKeyboardButton("🔄 ⌯ تغيير الرقم", callback_data="change_number"),
            types.InlineKeyboardButton("❎ ⌯ إلغاء الرقم", callback_data="cancel_order")
        )
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data == "cancel_order":
        order = get_active_order(user_id)
        
        if not order:
            bot.answer_callback_query(call.id, "*لا يوجد طلب نشط لإلغائه.*", show_alert=True)
            return
        
        cancel_order(order['id'])
        
        text = "*✅ ⌯ تم إلغاء الرقم بنجاح*\n\n*⬇️ ⌯ هل تريد الشراء مجددا؟*"
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("☑️ ⌯ شراء مرة اخرى؟", callback_data="buy_number"))
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data == "notification_channels" and user_id == ADMIN_ID:
        user_join_channel = get_setting('user_join_channel') or '*❌ غير معين*'
        otp_received_channel = get_setting('otp_received_channel') or '*❌ غير معين*'
        incomplete_orders_channel = get_setting('incomplete_orders_channel') or '*❌ غير معين*'
        activations_channel = get_setting('activations_channel') or '*❌ غير معين*'
        publish_activations = "✅ ⌯ مفعل" if get_setting('publish_activations') == 'true' else "❌ ⌯ معطل"
        
        text = f"""*📢 ⌯ إدارة قنوات الإشعارات*

*👤 ⌯ قناة دخول المستخدمين:* `{user_join_channel}`
*🔑 ⌯ قناة وصول الكود:* `{otp_received_channel}`
*🛒 ⌯ قناة الأرقام غير المكتملة:* `{incomplete_orders_channel}`
*🎥 ⌯ قناة التفعيلات:* `{activations_channel}`
*📢 ⌯ نشر التفعيلات:* {publish_activations}"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("👤 ⌯ تعيين قناة دخول المستخدمين", callback_data="set_user_join_channel"))
        markup.row(types.InlineKeyboardButton("🔑 ⌯ تعيين قناة وصول الكود", callback_data="set_otp_received_channel"))
        markup.row(types.InlineKeyboardButton("🛒 ⌯ تعيين قناة الأرقام غير المكتملة", callback_data="set_incomplete_orders_channel"))
        markup.row(types.InlineKeyboardButton("🎥 ⌯ تعيين قناة التفعيلات", callback_data="set_activations_channel"))
        markup.row(types.InlineKeyboardButton(f"{publish_activations} نشر التفعيلات", callback_data="toggle_publish_activations"))
        markup.row(types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="adminback"))
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data in ["set_user_join_channel", "set_otp_received_channel", "set_incomplete_orders_channel", "set_activations_channel"] and user_id == ADMIN_ID:
        channel_type_map = {
            "set_user_join_channel": "دخول المستخدمين",
            "set_otp_received_channel": "وصول الكود",
            "set_incomplete_orders_channel": "الأرقام غير المكتملة",
            "set_activations_channel": "التفعيلات"
        }
        
        channel_type_name = channel_type_map[call.data]
        
        with open(f'do_{chat_id}.txt', 'w') as f:
            f.write(call.data)
        
        text = f"""*⌯ تعيين قناة {channel_type_name}*

*⌯ يرجى إرسال آيدي القناة:*

*⌯ مثال:* `-1001234567890`

*⌯ أرسل /cancel للإلغاء*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("الغاء", callback_data="notification_channels"))
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data == "toggle_publish_activations" and user_id == ADMIN_ID:
        current = get_setting('publish_activations')
        new_value = 'false' if current == 'true' else 'true'
        set_setting('publish_activations', new_value)
        
        status = "✅ ⌯ تم تفعيل نشر التفعيلات" if new_value == 'true' else "❌ ⌯ تم تعطيل نشر التفعيلات"
        
        bot.edit_message_text(
            status,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="notification_channels")
            )
        )
    
    elif call.data in ["banuser", "unbanuser"] and user_id == ADMIN_ID:
        action = "حظر" if call.data == "banuser" else "فك حظر"
        
        with open(f'do_{chat_id}.txt', 'w') as f:
            f.write(call.data)
        
        text = f"""*🚫 ⌯ {action} مستخدم*

*⌯ يرجى إرسال آيدي المستخدم الذي تريد {action}:*

*⌯ أرسل /cancel للإلغاء*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("الغاء", callback_data="adminback"))
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data == "delcountry" and user_id == ADMIN_ID:
        countries = get_countries()
        
        if not countries:
            bot.edit_message_text(
                "*❌ ⌯ لا توجد دول مضافة حالياً.*",
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="adminback")
                )
            )
            return
        
        markup = types.InlineKeyboardMarkup()
        for country in countries:
            markup.row(types.InlineKeyboardButton(
                f"{country['name']} - {country['price']} نقطة",
                callback_data=f"delete_country_{country['id']}"
            ))
        markup.row(types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="adminback"))
        
        bot.edit_message_text(
            "*🗑️ ⌯ اختر الدولة التي تريد حذفها:*",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data.startswith("delete_country_") and user_id == ADMIN_ID:
        country_id = int(call.data.replace("delete_country_", ""))
        
        countries = get_countries()
        country_name = None
        for country in countries:
            if country['id'] == country_id:
                country_name = country['name']
                break
        
        if country_name and delete_country(country_id):
            text = f"*✅ ⌯ تم حذف الدولة ({country_name}) بنجاح*"
        else:
            text = "*❌ ⌯ لم يتم العثور على الدولة*"
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 ⌯ رجوع", callback_data="adminback")
            )
        )
    
    elif call.data == "addcountry" and user_id == ADMIN_ID:
        with open(f'do_{chat_id}.txt', 'w') as f:
            f.write("addcountry")
        
        text = """*⌯ ارسل اسم الدولة ورمزها وسعرها (كل سطر)*
*⌯ مثال:*
*مصر*
*eg*
*0*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("الغاء", callback_data="adminback"))
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data == "adminback" and user_id == ADMIN_ID:
        text = f"""*♻️ ⌯ اهلا بك عزيزي الادمن في لوحه التحكم اختر زر من الأزرار التاليه*

*🆔 ⌯ ايدي حسابك:* `{user_id}`


*⬇️ ⌯ تحكم عبر الأزرار التالية ⬇️*"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("اضافه دوله", callback_data="addcountry"),
            types.InlineKeyboardButton("حذف دوله", callback_data="delcountry")
        )
        markup.row(types.InlineKeyboardButton("رموز الدول", callback_data="country_codes"))
        markup.row(
            types.InlineKeyboardButton("حظر مستخدم", callback_data="banuser"),
            types.InlineKeyboardButton("فك حظر مستخدم", callback_data="unbanuser")
        )
        markup.row(types.InlineKeyboardButton("ادارة قنوات الاشعارات", callback_data="notification_channels"))
        markup.row(types.InlineKeyboardButton("☎️ ⌯ شراء ارقام", callback_data="buy_number"))
        markup.row(
            types.InlineKeyboardButton("📮 ⌯ الدعم المباشر", url="https://t.me/oosss44"),
            types.InlineKeyboardButton("🚦 ⌯ قناة البوت", url="https://t.me/X5HDO")
        )
        
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=markup
        )
    
    elif call.data == "empty_callback":
        bot.answer_callback_query(call.id)
    
    bot.answer_callback_query(call.id, "✅ تمت العملية", show_alert=False)

# برمجة يوسف
# يوزري @oosss44
# قناة الملفات @X5HDO
#حقوقي شرفك لا تلعب بشرفك

@bot.message_handler(func=lambda message: True)
@handle_errors
def handle_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id == ADMIN_ID and os.path.exists(f'do_{chat_id}.txt'):
        with open(f'do_{chat_id}.txt', 'r') as f:
            action = f.read().strip()
        
        os.remove(f'do_{chat_id}.txt')
        
        if action == "addcountry":
            lines = message.text.strip().split('\n')
            if len(lines) >= 3:
                name = lines[0].strip()
                code = lines[1].strip()
                try:
                    price = float(lines[2].strip())
                except:
                    price = 0
                
                if add_country(name, code, price):
                    response = f"*✅ ⌯ تم اضافة الدولة ({name}) بنجاح*"
                else:
                    response = f"*❌ ⌯ فشل في اضافة الدولة ({name})*"
                
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("رجوع", callback_data="adminback"))
                
                bot.send_message(
                    chat_id,
                    response,
                    parse_mode='Markdown',
                    reply_markup=markup
                )
                return
        
        elif action in ["set_user_join_channel", "set_otp_received_channel", 
                       "set_incomplete_orders_channel", "set_activations_channel"]:
            setting_key = action.replace("set_", "") + "_channel"
            set_setting(setting_key, message.text.strip())
            
            channel_type_map = {
                "set_user_join_channel": "دخول المستخدمين",
                "set_otp_received_channel": "وصول الكود",
                "set_incomplete_orders_channel": "الأرقام غير المكتملة",
                "set_activations_channel": "التفعيلات"
            }
            
            response = f"*✅ ⌯ تم تعيين قناة {channel_type_map[action]}:* `{message.text.strip()}`"
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("رجوع", callback_data="notification_channels"))
            
            bot.send_message(
                chat_id,
                response,
                parse_mode='Markdown',
                reply_markup=markup
            )
            return
        
        elif action in ["banuser", "unbanuser"]:
            try:
                target_id = int(message.text.strip())
                if target_id > 0:
                    if action == "banuser":
                        if ban_user(target_id):
                            response = f"*✅ ⌯ تم حظر المستخدم {target_id} بنجاح*"
                        else:
                            response = f"*❌ ⌯ المستخدم {target_id} محظور مسبقاً*"
                    else:  # unbanuser
                        if unban_user(target_id):
                            response = f"*✅ ⌯ تم فك حظر المستخدم {target_id} بنجاح*"
                        else:
                            response = f"*❌ ⌯ المستخدم {target_id} غير محظور*"
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.row(types.InlineKeyboardButton("رجوع", callback_data="adminback"))
                    
                    bot.send_message(
                        chat_id,
                        response,
                        parse_mode='Markdown',
                        reply_markup=markup
                    )
                    return
            except:
                pass
    
    if message.text and message.text.startswith('/cancel'):
        if os.path.exists(f'do_{chat_id}.txt'):
            os.remove(f'do_{chat_id}.txt')
        
        bot.send_message(
            chat_id,
            "*تم الإلغاء*",
            parse_mode='Markdown'
        )
        return
    
    bot.send_message(
        chat_id,
        "*🚫 ⌯ أمر غير معروف، استخدم /start للبدء*",
        parse_mode='Markdown'
    )

os.makedirs("do", exist_ok=True)
os.makedirs("user", exist_ok=True)
os.makedirs("banned", exist_ok=True)
os.makedirs("numbers", exist_ok=True)

print("✅ Bot is running...")
print("⚡ Dev : @oosss44 - @X5HDO")
if __name__ == '__main__':
    os.makedirs("do", exist_ok=True)
    os.makedirs("user", exist_ok=True)
    os.makedirs("banned", exist_ok=True)
    os.makedirs("numbers", exist_ok=True)
    
    print("✅ Bot is running...")
    print("⚡ Dev : @oosss44 - @X5HDO")
    
    bot.remove_webhook()  # ده أهم سطر
    time.sleep(1)
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error in polling: {str(e)}")
            time.sleep(5)
            continue
