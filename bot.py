import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters, ConversationHandler
)
import sqlite3
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Tuple

# Load environment variables
load_dotenv()

# Bot Configuration - Set your variables here or in .env file
BOT_TOKEN = "8914045842:AAEz6MNsGTShwob_M3H0ECy8eOkl2nT5gno"
DEVELOPER_ID = 932862531
DEVELOPER_USERNAME = "Programmer_error"
# Premium Emoji constants
COMPUTER = "💻"
DICE = "🎲"
HERB = "🌿"
USER = "👤"
PLANET = "🪐"
SUN = "🔅"
ZAP = "⚡️"
GUITAR = "🎸"
DOVE = "🕊️"
WHITE_CIRCLE = "⚪️"
BUTTERFLY = "🦋"
SPARKLES = "✨"
PREMIUM = "⚡️"
CROWN = "👑"
FIRE = "🔥"
LOCK = "🔒"
UNLOCK = "🔓"
WARNING = "⚠️"
CHECK = "✅"
CROSS = "❌"
MONEY = "💰"
CREDIT = "💳"
PHONE = "📱"
CLOCK = "⏳"
CHANNEL = "📢"
KEY = "🔑"
GEAR = "⚙️"
GRAPH = "📊"
SHIELD = "🛡️"
GIFT = "🎁"

# Conversation states
ADD_NUMBER, ADD_BALANCE, ADD_CHANNEL, SET_CRYPTO_TOKEN, SET_MIN_DEPOSIT, SET_ADMIN_PASSWORD, SET_OTP_API_KEY, SET_OTP_SERVICE_URL = range(8)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_logged_in INTEGER DEFAULT 0,
            is_subscribed INTEGER DEFAULT 0,
            last_login DATETIME,
            join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            language_code TEXT DEFAULT 'ar'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS numbers (
            number_id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT UNIQUE,
            price INTEGER,
            is_sold INTEGER DEFAULT 0,
            category TEXT DEFAULT 'new',
            otp_service TEXT DEFAULT 'unknown',
            otp_id TEXT,
            otp_api_key TEXT,
            otp_status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            crypto_amount REAL,
            currency TEXT,
            invoice_id TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            invoice_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            username TEXT,
            required INTEGER DEFAULT 1,
            title TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            number_id INTEGER,
            user_id INTEGER,
            otp_code TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(number_id) REFERENCES numbers(number_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    # Insert default settings
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('min_deposit', '1'))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('crypto_bot_token', ''))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('admin_password', ''))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('otp_api_key', ''))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                  ('otp_service_url', 'https://api.sms-activate.org/stubs/handler_api.php'))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('bot_language', 'ar'))
    # Set developer as admin
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, is_admin) VALUES (?, ?, 1)', (DEVELOPER_ID, DEVELOPER_USERNAME))
    conn.commit()
    conn.close()

init_db()

# Admin check
def is_admin(user_id: int) -> bool:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

# Check subscription
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id, username, title FROM channels WHERE required = 1')
    channels = cursor.fetchall()
    conn.close()

    if not channels:
        return True

    for channel in channels:
        try:
            member = await context.bot.get_chat_member(channel[0], user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return False
    return True

# Force subscription
async def force_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id, username, title FROM channels WHERE required = 1')
    channels = cursor.fetchall()
    conn.close()

    if not channels:
        return

    keyboard = []
    for channel in channels:
        keyboard.append([InlineKeyboardButton(
            f"الانضمام إلى {channel[2] or channel[1]}",
            url=f"https://t.me/{channel[1]}"
        )])

    keyboard.append([InlineKeyboardButton("✅ تم الاشتراك", callback_data='check_subscription')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{CHANNEL} يجب عليك الاشتراك في القنوات التالية لاستخدام البوت {CHANNEL}\n\n"
        f"{WHITE_CIRCLE} بعد الاشتراك اضغط على الزر أدناه {WHITE_CIRCLE}",
        reply_markup=reply_markup
    )

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user.id, user.username))
    cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?', (user.id,))
    conn.commit()
    conn.close()

    if not await check_subscription(user.id, context):
        await force_subscription(update, context)
        return

    keyboard = [
        [InlineKeyboardButton(f"{COMPUTER} قائمة الأرقام", callback_data='numbers_list')],
        [InlineKeyboardButton(f"{USER} حسابي", callback_data='my_account')],
        [InlineKeyboardButton(f"{CREDIT} شحن الرصيد", callback_data='deposit')],
        [InlineKeyboardButton(f"{ZAP} الدعم", callback_data='support')],
        [InlineKeyboardButton(f"{LOCK} تسجيل الدخول", callback_data='login')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{SPARKLES} أهلا بك في بوت بيع أرقام التليجرام المتطور {SPARKLES}\n\n"
        f"{HERB} اختر من القائمة أدناه {HERB}",
        reply_markup=reply_markup
    )

# Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(f"{ZAP} ليس لديك صلاحية للوصول إلى هذه الأوامر {ZAP}")
        return

    keyboard = [
        [InlineKeyboardButton(f"{PLANET} إضافة رقم", callback_data='add_number')],
        [InlineKeyboardButton(f"{SUN} إدارة الأرقام", callback_data='manage_numbers')],
        [InlineKeyboardButton(f"{GUITAR} إضافة رصيد يدوي", callback_data='add_balance')],
        [InlineKeyboardButton(f"{DOVE} قائمة المستخدمين", callback_data='users_list')],
        [InlineKeyboardButton(f"{GRAPH} الإحصائيات", callback_data='stats')],
        [InlineKeyboardButton(f"{GEAR} إعدادات البوت", callback_data='bot_settings')],
        [InlineKeyboardButton(f"{CHANNEL} إدارة القنوات", callback_data='manage_channels')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{CROWN} لوحة التحكم المتطورة {CROWN}\n\n"
        f"{WHITE_CIRCLE} اختر من القائمة أدناه {WHITE_CIRCLE}",
        reply_markup=reply_markup
    )

# Bot settings
async def bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return

    keyboard = [
        [InlineKeyboardButton(f"{KEY} تعيين كلمة مرور الأدمن", callback_data='set_admin_password')],
        [InlineKeyboardButton(f"{CREDIT} إعدادات الدفع", callback_data='payment_settings')],
        [InlineKeyboardButton(f"{PHONE} إعدادات OTP", callback_data='otp_settings')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='admin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"{FIRE} إعدادات البوت {FIRE}\n\n"
            f"{WHITE_CIRCLE} اختر الإعداد الذي تريد تعديله {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"{FIRE} إعدادات البوت {FIRE}\n\n"
            f"{WHITE_CIRCLE} اختر الإعداد الذي تريد تعديله {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )

# OTP settings
async def otp_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('otp_api_key',))
    otp_api_key = cursor.fetchone()[0] or ''
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('otp_service_url',))
    otp_service_url = cursor.fetchone()[0] or ''
    conn.close()

    keyboard = [
        [InlineKeyboardButton(f"{KEY} تعيين مفتاح API لـ OTP", callback_data='set_otp_api_key')],
        [InlineKeyboardButton(f"{GEAR} تعيين رابط خدمة OTP", callback_data='set_otp_service_url')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='bot_settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"{PHONE} إعدادات OTP {PHONE}\n\n"
            f"{WHITE_CIRCLE} مفتاح API: `{otp_api_key if otp_api_key else 'غير مضبوط'}`\n"
            f"{WHITE_CIRCLE} رابط الخدمة: `{otp_service_url if otp_service_url else 'غير مضبوط'}` {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"{PHONE} إعدادات OTP {PHONE}\n\n"
            f"{WHITE_CIRCLE} مفتاح API: `{otp_api_key if otp_api_key else 'غير مضبوط'}`\n"
            f"{WHITE_CIRCLE} رابط الخدمة: `{otp_service_url if otp_service_url else 'غير مضبوط'}` {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )

# Payment settings
async def payment_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('crypto_bot_token',))
    crypto_token = cursor.fetchone()[0] or ''
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('min_deposit',))
    min_deposit = cursor.fetchone()[0] or '1'
    conn.close()

    keyboard = [
        [InlineKeyboardButton(f"{KEY} تعيين توكن CryptoBot", callback_data='set_crypto_token')],
        [InlineKeyboardButton(f"{MONEY} تعيين الحد الأدنى للشحن", callback_data='set_min_deposit')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='bot_settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"{CREDIT} إعدادات الدفع {CREDIT}\n\n"
            f"{WHITE_CIRCLE} توكن CryptoBot: `{crypto_token if crypto_token else 'غير مضبوط'}`\n"
            f"{WHITE_CIRCLE} الحد الأدنى للشحن: `{min_deposit}$` {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"{CREDIT} إعدادات الدفع {CREDIT}\n\n"
            f"{WHITE_CIRCLE} توكن CryptoBot: `{crypto_token if crypto_token else 'غير مضبوط'}`\n"
            f"{WHITE_CIRCLE} الحد الأدنى للشحن: `{min_deposit}$` {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )

# Login system
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_logged_in = 1, last_login = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"{UNLOCK} تم تسجيل الدخول بنجاح! {UNLOCK}\n\n"
            f"{WHITE_CIRCLE} يمكنك الآن تصفح الأرقام وشراؤها {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"{UNLOCK} تم تسجيل الدخول بنجاح! {UNLOCK}\n\n"
            f"{WHITE_CIRCLE} يمكنك الآن تصفح الأرقام وشراؤها {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )

# Logout system
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_logged_in = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"{LOCK} تم تسجيل الخروج بنجاح! {LOCK}\n\n"
            f"{WHITE_CIRCLE} شكرًا لاستخدامك بوتنا {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"{LOCK} تم تسجيل الخروج بنجاح! {LOCK}\n\n"
            f"{WHITE_CIRCLE} شكرًا لاستخدامك بوتنا {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )

# Check subscription callback
async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if await check_subscription(user_id, context):
        await query.answer("تم التحقق من الاشتراك بنجاح!")
        await start(update, context)
    else:
        await query.answer("لم يتم الاشتراك بعد في جميع القنوات المطلوبة!", show_alert=True)

# Deposit system
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('crypto_bot_token',))
    crypto_token = cursor.fetchone()[0]
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('min_deposit',))
    min_deposit = int(cursor.fetchone()[0] or 1)
    conn.close()

    if not crypto_token:
        keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            f"{WARNING} نظام الدفع غير مضبوط بعد {WARNING}\n\n"
            f"{WHITE_CIRCLE} يرجى التواصل مع الأدمن {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )
        return

    # Create invoice
    url = f"https://pay.crypt.bot/api/createInvoice"
    headers = {
        "Crypto-Pay-API-Token": crypto_token,
        "Content-Type": "application/json"
    }
    payload = {
        "asset": "USDT",
        "amount": str(min_deposit),
        "description": "Deposit to Telegram Numbers Bot"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if data.get('ok'):
            invoice = data['result']
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (user_id, amount, crypto_amount, currency, payment_id, status, invoice_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, min_deposit, invoice['amount'], invoice['asset'], invoice['invoice_id'], 'pending', invoice['pay_url']))
            conn.commit()
            conn.close()

            keyboard = [
                [InlineKeyboardButton(f"{CREDIT} دفع {min_deposit}$", url=invoice['pay_url'])],
                [InlineKeyboardButton(f"{CHECK} تحقق من الدفع", callback_data=f'check_payment_{invoice["invoice_id"]}')],
                [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                f"{MONEY} شحن الرصيد {MONEY}\n\n"
                f"{WHITE_CIRCLE} المبلغ: `{min_deposit}$`\n"
                f"{WHITE_CIRCLE} العملة: USDT\n"
                f"{WHITE_CIRCLE} الحالة: في انتظار الدفع {CLOCK} {WHITE_CIRCLE}\n\n"
                f"{ZAP} اضغط على الزر أدناه للدفع {ZAP}",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                f"{WARNING} حدث خطأ أثناء إنشاء الفاتورة {WARNING}\n\n"
                f"{WHITE_CIRCLE} يرجى المحاولة لاحقًا {WHITE_CIRCLE}"
            )
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            f"{WARNING} حدث خطأ أثناء إنشاء الفاتورة {WARNING}\n\n"
            f"{WHITE_CIRCLE} يرجى المحاولة لاحقًا {WHITE_CIRCLE}"
        )

# Check payment
async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    payment_id = query.data.split('_')[2]

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('crypto_bot_token',))
    crypto_token = cursor.fetchone()[0]
    cursor.execute('SELECT user_id, amount FROM payments WHERE payment_id = ?', (payment_id,))
    payment = cursor.fetchone()
    conn.close()

    if not payment:
        await query.answer("الفاتورة غير موجودة!", show_alert=True)
        return

    user_id, amount = payment

    if not crypto_token:
        await query.answer("نظام الدفع غير مضبوط!", show_alert=True)
        return

    # Check invoice status
    url = f"https://pay.crypt.bot/api/getInvoices"
    headers = {
        "Crypto-Pay-API-Token": crypto_token
    }
    params = {
        "invoice_ids": payment_id
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if data.get('ok') and data['result']['items']:
            invoice = data['result']['items'][0]
            if invoice['status'] == 'paid':
                conn = sqlite3.connect('bot_database.db')
                cursor = conn.cursor()

                # Update payment status
                cursor.execute('UPDATE payments SET status = ? WHERE payment_id = ?', ('completed', payment_id))

                # Update user balance
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))

                # Add transaction
                cursor.execute('''
                    INSERT INTO transactions (user_id, amount, type, description)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, amount, 'deposit', f'Deposit via CryptoBot invoice {payment_id}'))

                conn.commit()
                conn.close()

                await query.answer("تم تأكيد الدفع بنجاح!")
                keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"{CHECK} تم شحن الرصيد بنجاح! {CHECK}\n\n"
                    f"{WHITE_CIRCLE} المبلغ: `{amount}$`\n"
                    f"{WHITE_CIRCLE} الرصيد الجديد: `{get_user_balance(user_id)}$` {WHITE_CIRCLE}",
                    reply_markup=reply_markup
                )
            else:
                await query.answer("لم يتم الدفع بعد!")
        else:
            await query.answer("حدث خطأ أثناء التحقق من الدفع!", show_alert=True)
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        await query.answer("حدث خطأ أثناء التحقق من الدفع!", show_alert=True)

# Get user balance
def get_user_balance(user_id: int) -> int:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    conn.close()
    return balance

# Request OTP from service
async def request_otp(otp_api_key: str, otp_service: str, otp_id: str, service_url: str) -> Optional[str]:
    try:
        params = {
            'api_key': otp_api_key,
            'action': 'getStatus',
            'id': otp_id
        }
        response = requests.get(service_url, params=params)
        response_text = response.text

        if 'STATUS_OK' in response_text:
            otp_code = response_text.split(':')[1]
            return otp_code
        elif 'STATUS_WAIT_CODE' in response_text:
            return None  # OTP not ready yet
        else:
            logger.error(f"OTP service error: {response_text}")
            return None
    except Exception as e:
        logger.error(f"Error requesting OTP: {e}")
        return None

# Show numbers categories
async def show_numbers_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(f"{CHECK} أرقام جديدة", callback_data='category_new')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} أرقام قديمة", callback_data='category_old')],
        [InlineKeyboardButton(f"{WARNING} أرقام مزيفة", callback_data='category_fake')],
        [InlineKeyboardButton(f"{CROSS} أرقام احتيالية", callback_data='category_scam')],
        [InlineKeyboardButton(f"{DICE} أرقام عشوائية", callback_data='category_random')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"{COMPUTER} اختر فئة الأرقام {COMPUTER}",
        reply_markup=reply_markup
    )

# Show manage numbers categories
async def show_manage_numbers_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(f"{CHECK} إدارة أرقام جديدة", callback_data='manage_category_new')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} إدارة أرقام قديمة", callback_data='manage_category_old')],
        [InlineKeyboardButton(f"{WARNING} إدارة أرقام مزيفة", callback_data='manage_category_fake')],
        [InlineKeyboardButton(f"{CROSS} إدارة أرقام احتيالية", callback_data='manage_category_scam')],
        [InlineKeyboardButton(f"{DICE} إدارة أرقام عشوائية", callback_data='manage_category_random')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='admin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"{SUN} اختر فئة الأرقام للإدارة {SUN}",
        reply_markup=reply_markup
    )

# Show numbers list by category
async def show_numbers_list(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    category_names = {
        'new': 'جديدة',
        'old': 'قديمة',
        'fake': 'مزيفة',
        'scam': 'احتيالية',
        'random': 'عشوائية'
    }

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT number_id, number, price, otp_service
        FROM numbers
        WHERE is_sold = 0 AND category = ?
        ORDER BY created_at DESC
    ''', (category,))
    numbers = cursor.fetchall()
    conn.close()

    if not numbers:
        keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='numbers_list')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            text=f"{DICE} لا توجد أرقام متاحة في هذه الفئة حاليًا {DICE}",
            reply_markup=reply_markup
        )
        return

    keyboard = []
    for number in numbers:
        keyboard.append([InlineKeyboardButton(
            f"{PHONE} {number[1]} - {number[2]}$ ({number[3]})",
            callback_data=f'buy_number_{number[0]}'
        )])

    keyboard.append([InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='numbers_list')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"{COMPUTER} قائمة الأرقام {category_names[category]} {COMPUTER}",
        reply_markup=reply_markup
    )

# Show manage numbers by category
async def show_manage_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    category_names = {
        'new': 'جديدة',
        'old': 'قديمة',
        'fake': 'مزيفة',
        'scam': 'احتيالية',
        'random': 'عشوائية'
    }

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT number_id, number, price, otp_service, is_sold
        FROM numbers
        WHERE category = ?
        ORDER BY created_at DESC
    ''', (category,))
    numbers = cursor.fetchall()
    conn.close()

    if not numbers:
        keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='manage_numbers')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            text=f"{DICE} لا توجد أرقام مسجلة في هذه الفئة {DICE}",
            reply_markup=reply_markup
        )
        return

    keyboard = []
    for number in numbers:
        status = "مباع" if number[4] else "متاح"
        keyboard.append([InlineKeyboardButton(
            f"{PHONE} {number[1]} - {number[2]}$ ({number[3]}) - {status}",
            callback_data=f'delete_number_{number[0]}'
        )])

    keyboard.append([InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='manage_numbers')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"{SUN} إدارة الأرقام {category_names[category]} {SUN}",
        reply_markup=reply_markup
    )

# Buy number
async def buy_number(update: Update, context: ContextTypes.DEFAULT_TYPE, number_id: str) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    # Check if user is logged in
    cursor.execute('SELECT is_logged_in FROM users WHERE user_id = ?', (user_id,))
    is_logged_in = cursor.fetchone()[0]
    if not is_logged_in:
        keyboard = [[InlineKeyboardButton(f"{LOCK} تسجيل الدخول", callback_data='login')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            text=f"{LOCK} يجب تسجيل الدخول أولاً لشراء الأرقام {LOCK}",
            reply_markup=reply_markup
        )
        return

    cursor.execute('''
        SELECT number, price, category, otp_service, otp_id, otp_api_key
        FROM numbers
        WHERE number_id = ? AND is_sold = 0
    ''', (number_id,))
    number = cursor.fetchone()

    if not number:
        await update.callback_query.edit_message_text(text=f"{ZAP} هذا الرقم غير متاح أو تم بيعه بالفعل {ZAP}")
        return

    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    user_balance = cursor.fetchone()[0]

    if user_balance < number[1]:
        await update.callback_query.edit_message_text(text=f"{ZAP} رصيدك غير كافٍ لشراء هذا الرقم {ZAP}")
        return

    # Get OTP API settings
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('otp_api_key',))
    global_otp_api_key = cursor.fetchone()[0]
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('otp_service_url',))
    otp_service_url = cursor.fetchone()[0]

    # Use number-specific API key if available, otherwise use global
    otp_api_key = number[5] if number[5] else global_otp_api_key

    if not otp_api_key or not otp_service_url:
        await update.callback_query.edit_message_text(
            text=f"{WARNING} خدمة OTP غير مضبوطة بعد {WARNING}\n\n"
            f"{WHITE_CIRCLE} يرجى التواصل مع الأدمن لإعداد خدمة OTP {WHITE_CIRCLE}"
        )
        return

    # Request OTP
    otp_code = await request_otp(otp_api_key, number[3], number[4], otp_service_url)

    if not otp_code:
        await update.callback_query.edit_message_text(
            text=f"{CLOCK} جاري استلام رمز OTP من الخدمة، يرجى المحاولة بعد قليل {CLOCK}\n\n"
            f"{WHITE_CIRCLE} إذا استمرت المشكلة، يرجى التواصل مع الدعم {WHITE_CIRCLE}"
        )
        return

    # Update user balance and mark number as sold
    cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (number[1], user_id))
    cursor.execute('''
        UPDATE numbers
        SET is_sold = 1, otp_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE number_id = ?
    ''', ('delivered', number_id))

    # Add transaction
    cursor.execute('''
        INSERT INTO transactions (user_id, amount, type, description)
        VALUES (?, ?, ?, ?)
    ''', (user_id, -number[1], 'purchase', f'Purchase of number {number[0]}'))

    # Record OTP request
    cursor.execute('''
        INSERT INTO otp_requests (number_id, user_id, otp_code, status)
        VALUES (?, ?, ?, ?)
    ''', (number_id, user_id, otp_code, 'delivered'))

    conn.commit()
    conn.close()

    category_names = {
        'new': 'جديدة',
        'old': 'قديمة',
        'fake': 'مزيفة',
        'scam': 'احتيالية',
        'random': 'عشوائية'
    }

    # Force logout after purchase
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_logged_in = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton(f"{LOCK} تسجيل الخروج (مفعل تلقائيًا)", callback_data='logout')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='numbers_list')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"{SPARKLES} تم شراء الرقم بنجاح! {SPARKLES}\n\n"
        f"{WHITE_CIRCLE} الرقم: `{number[0]}`\n"
        f"{WHITE_CIRCLE} السعر: `{number[1]}` دولار\n"
        f"{WHITE_CIRCLE} الفئة: {category_names[number[2]]}\n"
        f"{WHITE_CIRCLE} الخدمة: {number[3]}\n"
        f"{WHITE_CIRCLE} رمز OTP: `{otp_code}` {WHITE_CIRCLE}\n\n"
        f"{BUTTERFLY} تم تسجيل خروجك تلقائيًا لأسباب أمنية {BUTTERFLY}\n"
        f"{ZAP} يمكنك تسجيل الدخول مرة أخرى عند الحاجة {ZAP}",
        reply_markup=reply_markup
    )

# Delete number
async def delete_number(update: Update, context: ContextTypes.DEFAULT_TYPE, number_id: str) -> None:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM numbers WHERE number_id = ?', (number_id,))
    conn.commit()
    conn.close()

    await update.callback_query.edit_message_text(text=f"{ZAP} تم حذف الرقم بنجاح {ZAP}")

# Show my account
async def show_my_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT balance, is_logged_in, join_date, username
        FROM users
        WHERE user_id = ?
    ''', (user_id,))
    user_data = cursor.fetchone()
    balance = user_data[0]
    is_logged_in = user_data[1]
    join_date = user_data[2]
    username = user_data[3]
    conn.close()

    keyboard = [
        [InlineKeyboardButton(f"{CREDIT} شحن الرصيد", callback_data='deposit')],
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    login_status = f"{UNLOCK} مسجل دخول" if is_logged_in else f"{LOCK} غير مسجل دخول"

    await update.callback_query.edit_message_text(
        text=f"{USER} حسابي {USER}\n\n"
        f"{WHITE_CIRCLE} الاسم: @{username or 'غير متوفر'}\n"
        f"{WHITE_CIRCLE} الرصيد: `{balance}` دولار\n"
        f"{WHITE_CIRCLE} الحالة: {login_status}\n"
        f"{WHITE_CIRCLE} تاريخ الانضمام: `{join_date.split(' ')[0]}` {WHITE_CIRCLE}\n\n"
        f"{ZAP} لإضافة رصيد، اضغط على الزر أدناه {ZAP}",
        reply_markup=reply_markup
    )

# Show users list
async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, balance, is_admin, join_date
        FROM users
        ORDER BY join_date DESC
    ''')
    users = cursor.fetchall()
    conn.close()

    if not users:
        await update.callback_query.edit_message_text(text=f"{DICE} لا يوجد مستخدمون مسجلون {DICE}")
        return

    message = f"{DOVE} قائمة المستخدمين {DOVE} ({len(users)})\n\n"
    for user in users:
        admin_status = f"{CROWN} أدمن" if user[3] else f"{WHITE_CIRCLE} مستخدم عادي"
        message += (
            f"{WHITE_CIRCLE} المعرف: `{user[0]}`\n"
            f"{WHITE_CIRCLE} الاسم: @{user[1] or 'غير متوفر'}\n"
            f"{WHITE_CIRCLE} الرصيد: `{user[2]}` دولار\n"
            f"{WHITE_CIRCLE} الصلاحية: {admin_status}\n"
            f"{WHITE_CIRCLE} انضم في: `{user[4].split(' ')[0]}` {WHITE_CIRCLE}\n\n"
        )

    keyboard = [
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='admin')],
        [InlineKeyboardButton(f"{GRAPH} إحصائيات المستخدمين", callback_data='user_stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )

# User stats
async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
    admin_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE is_logged_in = 1')
    active_users = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(balance) FROM users')
    avg_balance = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(balance) FROM users')
    total_balance = cursor.fetchone()[0] or 0

    cursor.execute('SELECT COUNT(*) FROM users WHERE join_date >= datetime("now", "-7 days")')
    new_users_week = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE join_date >= datetime("now", "-30 days")')
    new_users_month = cursor.fetchone()[0]

    conn.close()

    message = (
        f"{GRAPH} إحصائيات المستخدمين {GRAPH}\n\n"
        f"{WHITE_CIRCLE} إجمالي المستخدمين: `{total_users}`\n"
        f"{WHITE_CIRCLE} عدد الأدمن: `{admin_users}`\n"
        f"{WHITE_CIRCLE} المستخدمين النشطين: `{active_users}`\n"
        f"{WHITE_CIRCLE} متوسط الرصيد: `{avg_balance:.2f}$`\n"
        f"{WHITE_CIRCLE} إجمالي الرصيد: `{total_balance}$`\n"
        f"{WHITE_CIRCLE} مستخدمين جدد (7 أيام): `{new_users_week}`\n"
        f"{WHITE_CIRCLE} مستخدمين جدد (30 يومًا): `{new_users_month}` {WHITE_CIRCLE}\n\n"
        f"{ZAP} إحصائيات مفصلة للمستخدمين {ZAP}"
    )

    keyboard = [[InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='users_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )

# Show stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM numbers WHERE is_sold = 0')
    available_numbers = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM numbers WHERE is_sold = 1')
    sold_numbers = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(amount) FROM transactions WHERE amount > 0')
    total_deposits = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(amount) FROM transactions WHERE amount < 0')
    total_purchases = cursor.fetchone()[0] or 0

    cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "completed"')
    completed_payments = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(amount) FROM payments WHERE status = "completed"')
    total_payments = cursor.fetchone()[0] or 0

    # Category stats
    categories = ['new', 'old', 'fake', 'scam', 'random']
    category_stats = {}
    for category in categories:
        cursor.execute('SELECT COUNT(*) FROM numbers WHERE category = ? AND is_sold = 0', (category,))
        available = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM numbers WHERE category = ? AND is_sold = 1', (category,))
        sold = cursor.fetchone()[0]
        category_stats[category] = {'available': available, 'sold': sold}

    # OTP service stats
    cursor.execute('SELECT otp_service, COUNT(*) FROM numbers WHERE is_sold = 0 GROUP BY otp_service')
    available_services = cursor.fetchall()
    cursor.execute('SELECT otp_service, COUNT(*) FROM numbers WHERE is_sold = 1 GROUP BY otp_service')
    sold_services = cursor.fetchall()

    conn.close()

    category_names = {
        'new': 'جديدة',
        'old': 'قديمة',
        'fake': 'مزيفة',
        'scam': 'احتيالية',
        'random': 'عشوائية'
    }

    message = (
        f"{BUTTERFLY} الإحصائيات المتطورة {BUTTERFLY}\n\n"
        f"{WHITE_CIRCLE} عدد المستخدمين: `{users_count}`\n"
        f"{WHITE_CIRCLE} الأرقام المتاحة: `{available_numbers}`\n"
        f"{WHITE_CIRCLE} الأرقام المباعة: `{sold_numbers}`\n"
        f"{WHITE_CIRCLE} إجمالي الإيداعات: `{total_deposits}$`\n"
        f"{WHITE_CIRCLE} إجمالي المشتريات: `{abs(total_purchases)}$`\n"
        f"{WHITE_CIRCLE} عدد الدفعات المكتملة: `{completed_payments}`\n"
        f"{WHITE_CIRCLE} إجمالي المدفوعات: `{total_payments}$`\n\n"
        f"{PREMIUM} إحصائيات الفئات {PREMIUM}\n"
    )

    for category, stats in category_stats.items():
        message += f"{WHITE_CIRCLE} {category_names[category]}: متاحة `{stats['available']}`, مباعة `{stats['sold']}`\n"

    message += f"\n{PREMIUM} إحصائيات خدمات OTP {PREMIUM}\n"
    for service in available_services:
        sold_count = next((s[1] for s in sold_services if s[0] == service[0]), 0)
        message += f"{WHITE_CIRCLE} {service[0]}: متاحة `{service[1]}`, مباعة `{sold_count}`\n"

    keyboard = [
        [InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='admin')],
        [InlineKeyboardButton(f"{GRAPH} إحصائيات المستخدمين", callback_data='user_stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )

# Manage channels
async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id, username, required, title FROM channels')
    channels = cursor.fetchall()
    conn.close()

    keyboard = []
    for channel in channels:
        status = "مطلوب" if channel[2] else "اختياري"
        keyboard.append([InlineKeyboardButton(
            f"{CHANNEL} {channel[3] or channel[1]} ({status})",
            callback_data=f'remove_channel_{channel[0]}'
        )])

    keyboard.append([InlineKeyboardButton(f"{CHECK} إضافة قناة جديدة", callback_data='add_channel')])
    keyboard.append([InlineKeyboardButton(f"{WHITE_CIRCLE} رجوع", callback_data='admin')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=f"{CHANNEL} إدارة القنوات الإلزامية {CHANNEL}\n\n"
            f"{WHITE_CIRCLE} اضغط على القناة لإزالتها أو أضف قناة جديدة {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=f"{CHANNEL} إدارة القنوات الإلزامية {CHANNEL}\n\n"
            f"{WHITE_CIRCLE} اضغط على القناة لإزالتها أو أضف قناة جديدة {WHITE_CIRCLE}",
            reply_markup=reply_markup
        )

# Remove channel
async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: str) -> None:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
    conn.commit()
    conn.close()

    query = update.callback_query
    await query.answer("تم إزالة القناة بنجاح!")
    await manage_channels(update, context)

# Callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == 'numbers_list':
        await show_numbers_categories(update, context)
    elif data == 'my_account':
        await show_my_account(update, context)
    elif data == 'support':
        await query.edit_message_text(text=f"{ZAP} للدعم الفني، يرجى التواصل مع @{DEVELOPER_USERNAME} {ZAP}")
    elif data == 'deposit':
        await deposit(update, context)
    elif data == 'add_number':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                text=f"{PLANET} أرسل الرقم والسعر والفئة وخدمة OTP ومعرف OTP ومفتاح API (اختياري) بالشكل التالي:\n\n"
                f"`رقم:سعر:فئة:خدمة_otp:id_otp[:api_key]`\n"
                f"الفئات المتاحة: new, old, fake, scam, random\n"
                f"خدمات OTP: telegram, whatsapp, viber, etc.\n"
                f"مثال: `123456789:100:new:telegram:12345` أو `123456789:100:new:telegram:12345:abcdef123456` {PLANET}"
            )
            return ADD_NUMBER
    elif data == 'manage_numbers':
        if is_admin(query.from_user.id):
            await show_manage_numbers_categories(update, context)
    elif data.startswith('buy_number_'):
        number_id = data.split('_')[2]
        await buy_number(update, context, number_id)
    elif data.startswith('delete_number_'):
        if is_admin(query.from_user.id):
            number_id = data.split('_')[2]
            await delete_number(update, context, number_id)
    elif data == 'add_balance':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                text=f"{GUITAR} أرسل معرف المستخدم والمبلغ بالشكل التالي:\n\n"
                f"`معرف_المستخدم:مبلغ`\n"
                f"مثال: `123456789:100` {GUITAR}"
            )
            return ADD_BALANCE
    elif data == 'users_list':
        if is_admin(query.from_user.id):
            await show_users_list(update, context)
    elif data == 'stats':
        if is_admin(query.from_user.id):
            await show_stats(update, context)
    elif data == 'bot_settings':
        if is_admin(query.from_user.id):
            await bot_settings(update, context)
    elif data == 'payment_settings':
        if is_admin(query.from_user.id):
            await payment_settings(update, context)
    elif data == 'otp_settings':
        if is_admin(query.from_user.id):
            await otp_settings(update, context)
    elif data == 'set_crypto_token':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                f"{KEY} أرسل التوكن الجديد لـ CryptoBot {KEY}\n\n"
                f"{WHITE_CIRCLE} مثال: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` {WHITE_CIRCLE}"
            )
            return SET_CRYPTO_TOKEN
    elif data == 'set_min_deposit':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                f"{MONEY} أرسل الحد الأدنى للشحن بالدولار {MONEY}\n\n"
                f"{WHITE_CIRCLE} مثال: `1` {WHITE_CIRCLE}"
            )
            return SET_MIN_DEPOSIT
    elif data == 'set_admin_password':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                f"{KEY} أرسل كلمة المرور الجديدة للأدمن {KEY}\n\n"
                f"{WHITE_CIRCLE} سيتم استخدامها لأوامر مثل /admin {WHITE_CIRCLE}"
            )
            return SET_ADMIN_PASSWORD
    elif data == 'set_otp_api_key':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                f"{KEY} أرسل مفتاح API الجديد لخدمة OTP {KEY}\n\n"
                f"{WHITE_CIRCLE} مثال: `1234567890abcdef1234567890abcdef` {WHITE_CIRCLE}"
            )
            return SET_OTP_API_KEY
    elif data == 'set_otp_service_url':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                f"{GEAR} أرسل رابط خدمة OTP الجديد {GEAR}\n\n"
                f"{WHITE_CIRCLE} مثال: `https://api.sms-activate.org/stubs/handler_api.php` {WHITE_CIRCLE}"
            )
            return SET_OTP_SERVICE_URL
    elif data == 'login':
        await login(update, context)
    elif data.startswith('check_payment_'):
        await check_payment(update, context)
    elif data.startswith('category_'):
        category = data.split('_')[1]
        await show_numbers_list(update, context, category)
    elif data.startswith('manage_category_'):
        category = data.split('_')[2]
        await show_manage_numbers(update, context, category)
    elif data == 'start':
        await start(update, context)
    elif data == 'admin':
        await admin_panel(update, context)
    elif data == 'check_subscription':
        await check_subscription_callback(update, context)
    elif data == 'manage_channels':
        if is_admin(query.from_user.id):
            await manage_channels(update, context)
    elif data == 'add_channel':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                text=f"{CHANNEL} أرسل معرف القناة أو اسم المستخدم بالشكل التالي:\n\n"
                f"`@channel_username` أو `-1001234567890`\n\n"
                f"{WHITE_CIRCLE} مثال: `@my_channel` أو `-1001234567890` {WHITE_CIRCLE}"
            )
            return ADD_CHANNEL

# Add number handler
async def add_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text
    try:
        parts = text.split(':')
        if len(parts) < 5:
            await update.message.reply_text(
                f"{ZAP} خطأ في الإدخال، يرجى المحاولة مرة أخرى بالشكل الصحيح: رقم:سعر:فئة:خدمة_otp:id_otp[:api_key] {ZAP}"
            )
            return ADD_NUMBER

        number = parts[0].strip()
        price = int(parts[1].strip())
        category = parts[2].strip().lower()
        otp_service = parts[3].strip()
        otp_id = parts[4].strip()
        otp_api_key = parts[5].strip() if len(parts) > 5 else ''

        valid_categories = ['new', 'old', 'fake', 'scam', 'random']
        if category not in valid_categories:
            await update.message.reply_text(
                f"{ZAP} فئة غير صالحة. الفئات المتاحة: new, old, fake, scam, random {ZAP}"
            )
            return ADD_NUMBER

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO numbers (number, price, category, otp_service, otp_id, otp_api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (number, price, category, otp_service, otp_id, otp_api_key))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"{PLANET} تم إضافة الرقم بنجاح {PLANET}\n\n"
            f"{WHITE_CIRCLE} الرقم: `{number}`\n"
            f"{WHITE_CIRCLE} السعر: `{price}`\n"
            f"{WHITE_CIRCLE} الفئة: `{category}`\n"
            f"{WHITE_CIRCLE} الخدمة: `{otp_service}`\n"
            f"{WHITE_CIRCLE} OTP ID: `{otp_id}`\n"
            f"{WHITE_CIRCLE} مفتاح API: `{otp_api_key if otp_api_key else 'العام'}` {WHITE_CIRCLE}"
        )
    except ValueError:
        await update.message.reply_text(
            f"{ZAP} خطأ في الإدخال، يرجى المحاولة مرة أخرى بالشكل الصحيح: رقم:سعر:فئة:خدمة_otp:id_otp[:api_key] {ZAP}"
        )
        return ADD_NUMBER
    except Exception as e:
        await update.message.reply_text(f"{ZAP} حدث خطأ: {str(e)} {ZAP}")
        return ADD_NUMBER

    return ConversationHandler.END

# Add balance handler
async def add_balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text
    try:
        user_id, amount = text.split(':')
        user_id = int(user_id.strip())
        amount = int(amount.strip())

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, 'admin_add', f'Manual balance addition by admin'))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"{GUITAR} تم إضافة الرصيد بنجاح {GUITAR}\n\n"
            f"{WHITE_CIRCLE} المستخدم: `{user_id}`\n"
            f"{WHITE_CIRCLE} المبلغ: `{amount}$` {WHITE_CIRCLE}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"{ZAP} خطأ في الإدخال، يرجى المحاولة مرة أخرى {ZAP}\n\n"
            f"{WHITE_CIRCLE} مثال: `123456789:100` {WHITE_CIRCLE}"
        )
        return ADD_BALANCE

    return ConversationHandler.END

# Add channel handler
async def add_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        if text.startswith('@'):
            username = text[1:]
            chat = await context.bot.get_chat(text)
            channel_id = chat.id
            title = chat.title
        elif text.startswith('-100'):
            channel_id = int(text)
            chat = await context.bot.get_chat(channel_id)
            username = chat.username
            title = chat.title
        else:
            await update.message.reply_text(f"{WARNING} معرف القناة غير صالح {WARNING}")
            return ADD_CHANNEL

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO channels (channel_id, username, required, title)
            VALUES (?, ?, ?, ?)
        ''', (channel_id, username, 1, title))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"{CHECK} تم إضافة القناة بنجاح {CHECK}\n\n"
            f"{WHITE_CIRCLE} القناة: {title or username}\n"
            f"{WHITE_CIRCLE} المعرف: `{channel_id}` {WHITE_CIRCLE}"
        )
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await update.message.reply_text(f"{WARNING} حدث خطأ أثناء إضافة القناة {WARNING}")
        return ADD_CHANNEL

    return ConversationHandler.END

# Set crypto token handler
async def set_crypto_token_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (text, 'crypto_bot_token'))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"{CHECK} تم تحديث توكن CryptoBot بنجاح {CHECK}")
    return ConversationHandler.END

# Set OTP API key handler
async def set_otp_api_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (text, 'otp_api_key'))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"{CHECK} تم تحديث مفتاح API لـ OTP بنجاح {CHECK}")
    return ConversationHandler.END

# Set OTP service URL handler
async def set_otp_service_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (text, 'otp_service_url'))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"{CHECK} تم تحديث رابط خدمة OTP بنجاح {CHECK}")
    return ConversationHandler.END

# Set min deposit handler
async def set_min_deposit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        min_deposit = int(text)
        if min_deposit < 1:
            await update.message.reply_text(f"{WARNING} الحد الأدنى للشحن يجب أن يكون على الأقل 1$ {WARNING}")
            return SET_MIN_DEPOSIT

        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (str(min_deposit), 'min_deposit'))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"{CHECK} تم تحديث الحد الأدنى للشحن إلى {min_deposit}$ بنجاح {CHECK}")
    except ValueError:
        await update.message.reply_text(f"{WARNING} يرجى إرسال رقم صحيح {WARNING}")
        return SET_MIN_DEPOSIT

    return ConversationHandler.END

# Set admin password handler
async def set_admin_password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (text, 'admin_password'))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"{CHECK} تم تحديث كلمة مرور الأدمن بنجاح {CHECK}")
    return ConversationHandler.END

# Admin command with password
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('admin_password',))
    admin_password = cursor.fetchone()[0]
    conn.close()

    if not admin_password:
        await admin_panel(update, context)
        return

    if not context.args or context.args[0] != admin_password:
        await update.message.reply_text(f"{LOCK} كلمة مرور الأدمن غير صحيحة {LOCK}")
        return

    await admin_panel(update, context)

# Check subscription for all messages
async def check_subscription_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text and update.message.text.startswith('/'):
        return

    if update.message and not await check_subscription(update.effective_user.id, context):
        await force_subscription(update, context)

# Main function
def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))

    # Conversation handlers
    add_number_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^add_number$')],
        states={
            ADD_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_number_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    add_balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^add_balance$')],
        states={
            ADD_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_balance_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^add_channel$')],
        states={
            ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    set_crypto_token_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^set_crypto_token$')],
        states={
            SET_CRYPTO_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_crypto_token_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    set_min_deposit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^set_min_deposit$')],
        states={
            SET_MIN_DEPOSIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_min_deposit_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    set_admin_password_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^set_admin_password$')],
        states={
            SET_ADMIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_admin_password_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    set_otp_api_key_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^set_otp_api_key$')],
        states={
            SET_OTP_API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_otp_api_key_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    set_otp_service_url_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^set_otp_service_url$')],
        states={
            SET_OTP_SERVICE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_otp_service_url_handler)],
        },
        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    # Callback query handler
    application.add_handler(CallbackQueryHandler(button))

    # Add conversation handlers
    application.add_handler(add_number_conv)
    application.add_handler(add_balance_conv)
    application.add_handler(add_channel_conv)
    application.add_handler(set_crypto_token_conv)
    application.add_handler(set_min_deposit_conv)
    application.add_handler(set_admin_password_conv)
    application.add_handler(set_otp_api_key_conv)
    application.add_handler(set_otp_service_url_conv)

    # Check subscription for all messages
    application.add_handler(MessageHandler(filters.ALL, check_subscription_wrapper))

    application.run_polling()

if __name__ == '__main__':
    main()
