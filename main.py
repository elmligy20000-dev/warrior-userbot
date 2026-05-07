import requests
import telebot
from telebot import types
import threading
import time
import json
import os
from datetime import datetime, timedelta
import sqlite3
from functools import wraps
import sys
import traceback

TOKEN = '8732196949:AAG_TeK8M0anLMYSlOTMQhEx0bnRhGvATM8' 
MODERATION_API_URL = 'http://apo-fares.abrdns.com/GPT-5.php'
ADMIN_IDS = [8085768728]

bot = telebot.TeleBot(TOKEN)
bot.set_webhook()

#مبرمج البوت @Devazf

class Database:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect('bot.db', check_same_thread=False)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS group_settings
                     (group_id INTEGER PRIMARY KEY,
                      group_title TEXT,
                      punishment_type TEXT DEFAULT 'ban',
                      mute_duration INTEGER DEFAULT 0,
                      warn_limit INTEGER DEFAULT 3,
                      auto_moderation BOOLEAN DEFAULT 1)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                     (user_id INTEGER,
                      group_id INTEGER,
                      reason TEXT,
                      banned_by INTEGER,
                      ban_date TIMESTAMP,
                      PRIMARY KEY (user_id, group_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS muted_users
                     (user_id INTEGER,
                      group_id INTEGER,
                      until_date TIMESTAMP,
                      PRIMARY KEY (user_id, group_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS warnings
                     (user_id INTEGER,
                      group_id INTEGER,
                      warning_count INTEGER DEFAULT 0,
                      PRIMARY KEY (user_id, group_id))''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query, params=(), fetch_one=False, fetch_all=False):
        try:
            conn = sqlite3.connect('bot.db', check_same_thread=False)
            c = conn.cursor()
            c.execute(query, params)
            
            if fetch_one:
                result = c.fetchone()
            elif fetch_all:
                result = c.fetchall()
            else:
                result = None
            
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            print(f"❌ خطأ في قاعدة البيانات: {e}")
            return None if fetch_one or fetch_all else False

db = Database()

#مبرمج البوت @Devazf

def safe_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"⚠️ خطأ في {func.__name__}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, f"⚠️ حدث خطأ:\n<code>{error_msg[:200]}</code>", parse_mode='HTML')
                except:
                    pass
            return None
    return wrapper

def check_content_moderation(text):
    try:
        if not text or len(text.strip()) == 0:
            return False
        
        clean_text = text.strip()[:500]
        
        response = requests.get(
            f"{MODERATION_API_URL}?q={clean_text}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "").lower()
            
            inappropriate_keywords = ['غير اخلاقي', 'سب', 'قذف', 'نصب', 'احتيال', 'cursing', 'bad', 'inappropriate']
            if any(keyword in answer for keyword in inappropriate_keywords):
                return True
            
            if "لا" in answer or "غير مسموح" in answer:
                return True
                
        return False
    except Exception as e:
        print(f"❌ خطأ في فحص المحتوى: {e}")
        return False

#مبرمج البوت @Devazf

@safe_execution
def punish_user(message, user_id, group_id, reason="محتوى غير أخلاقي"):
    
    settings = db.execute_query(
        "SELECT punishment_type, mute_duration FROM group_settings WHERE group_id = ?",
        (group_id,), fetch_one=True
    )
    
    if not settings:
        punishment_type = "ban"
        mute_duration = 0
    else:
        punishment_type, mute_duration = settings
    
    try:
        if punishment_type == "ban":
            bot.ban_chat_member(group_id, user_id)
            bot.send_message(group_id, f"🚫 تم حظر المستخدم بسبب: {reason}")
            
        elif punishment_type == "kick":
            bot.ban_chat_member(group_id, user_id)
            bot.unban_chat_member(group_id, user_id)
            bot.send_message(group_id, f"👢 تم طرد المستخدم بسبب: {reason}")
            
        elif punishment_type == "mute":
            until_date = None
            if mute_duration > 0:
                until_date = datetime.now() + timedelta(seconds=mute_duration)
                db.execute_query(
                    "INSERT OR REPLACE INTO muted_users (user_id, group_id, until_date) VALUES (?, ?, ?)",
                    (user_id, group_id, until_date)
                )
            
            bot.restrict_chat_member(
                group_id, user_id,
                until_date=until_date,
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
            
            duration_text = f" لمدة {mute_duration} ثانية" if mute_duration > 0 else " للأبد"
            bot.send_message(group_id, f"🔇 تم كتم المستخدم{duration_text} بسبب: {reason}")
            
        elif punishment_type == "warn":
            warning = db.execute_query(
                "SELECT warning_count FROM warnings WHERE user_id = ? AND group_id = ?",
                (user_id, group_id), fetch_one=True
            )
            
            if warning:
                new_count = warning[0] + 1
                db.execute_query(
                    "UPDATE warnings SET warning_count = ? WHERE user_id = ? AND group_id = ?",
                    (new_count, user_id, group_id)
                )
            else:
                new_count = 1
                db.execute_query(
                    "INSERT INTO warnings (user_id, group_id, warning_count) VALUES (?, ?, ?)",
                    (user_id, group_id, new_count)
                )
            
            warn_limit = settings[2] if len(settings) > 2 else 3
            
            if new_count >= warn_limit:
                punish_user(message, user_id, group_id, f"تجاوز الحد الأقصى للإنذارات ({warn_limit})")
                db.execute_query(
                    "DELETE FROM warnings WHERE user_id = ? AND group_id = ?",
                    (user_id, group_id)
                )
            else:
                bot.send_message(
                    group_id, 
                    f"⚠️ إنذار {new_count}/{warn_limit} للمستخدم بسبب: {reason}"
                )
    
    except Exception as e:
        print(f"❌ خطأ في تطبيق العقوبة: {e}")
        try:
            bot.send_message(
                group_id,
                f"⚠️ تعذر تطبيق العقوبة. قد لا أملك الصلاحيات الكافية."
            )
        except:
            pass

def admin_only(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        try:
            if message.chat.type in ['group', 'supergroup']:
                admin = bot.get_chat_member(message.chat.id, message.from_user.id)
                if admin.status in ['creator', 'administrator'] or message.from_user.id in ADMIN_IDS:
                    return func(message, *args, **kwargs)
                else:
                    bot.reply_to(message, "⛔ هذا الأمر للمشرفين فقط!")
            else:
                bot.reply_to(message, "⚠️ هذا الأمر يعمل فقط في المجموعات!")
        except Exception as e:
            print(f"❌ خطأ في التحقق من الصلاحيات: {e}")
            bot.reply_to(message, "⚠️ حدث خطأ في التحقق من الصلاحيات")
        return None
    return wrapper

#مبرمج البوت @Devazf

def get_target_user(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    elif len(message.text.split()) > 1:
        try:
            user_id = int(message.text.split()[1])
            class User:
                def __init__(self, id):
                    self.id = id
                    self.first_name = f"User {id}"
            return User(user_id)
        except:
            return None
    return None

@safe_execution
@admin_only
def handle_ban(message):
    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ يرجى الرد على رسالة المستخدم أو إضافة معرفه")
        return
    
    reason = "بدون سبب"
    if len(message.text.split()) > 2:
        reason = ' '.join(message.text.split()[2:])
    elif message.reply_to_message and len(message.text.split()) > 1:
        reason = ' '.join(message.text.split()[1:])
    
    try:
        bot.ban_chat_member(message.chat.id, target.id)
        bot.reply_to(message, f"✅ تم حظر {target.first_name}\nالسبب: {reason}")
        
        db.execute_query(
            "INSERT OR REPLACE INTO banned_users (user_id, group_id, reason, banned_by, ban_date) VALUES (?, ?, ?, ?, ?)",
            (target.id, message.chat.id, reason, message.from_user.id, datetime.now())
        )
    except Exception as e:
        bot.reply_to(message, f"❌ فشل الحظر: {e}")

#مبرمج البوت @Devazf

@safe_execution
@admin_only
def handle_unban(message):
    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ يرجى الرد على رسالة المستخدم أو إضافة معرفه")
        return
    
    try:
        bot.unban_chat_member(message.chat.id, target.id)
        bot.reply_to(message, f"✅ تم إلغاء حظر {target.first_name}")
        
        db.execute_query(
            "DELETE FROM banned_users WHERE user_id = ? AND group_id = ?",
            (target.id, message.chat.id)
        )
    except Exception as e:
        bot.reply_to(message, f"❌ فشل إلغاء الحظر: {e}")

@safe_execution
@admin_only
def handle_kick(message):
    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ يرجى الرد على رسالة المستخدم أو إضافة معرفه")
        return
    
    reason = "بدون سبب"
    if len(message.text.split()) > 2:
        reason = ' '.join(message.text.split()[2:])
    
    try:
        bot.ban_chat_member(message.chat.id, target.id)
        bot.unban_chat_member(message.chat.id, target.id)
        bot.reply_to(message, f"✅ تم طرد {target.first_name}\nالسبب: {reason}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل الطرد: {e}")

@safe_execution
@admin_only
def handle_mute(message):
    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ يرجى الرد على رسالة المستخدم أو إضافة معرفه")
        return
    
    duration = 0
    reason = "بدون سبب"
    
    parts = message.text.split()
    if len(parts) > 1:
        try:
            for i, part in enumerate(parts):
                if part.isdigit() and i+1 < len(parts):
                    if parts[i+1] in ['ثانية', 'ثواني', 's']:
                        duration = int(part)
                    elif parts[i+1] in ['دقيقة', 'دقائق', 'm']:
                        duration = int(part) * 60
                    elif parts[i+1] in ['ساعة', 'ساعات', 'h']:
                        duration = int(part) * 3600
                    elif parts[i+1] in ['يوم', 'أيام', 'd']:
                        duration = int(part) * 86400
                    break
        except:
            pass
        
        if message.reply_to_message:
            reason = ' '.join(parts[1:]) if len(parts) > 1 else "بدون سبب"
        else:
            reason = ' '.join(parts[2:]) if len(parts) > 2 else "بدون سبب"
    
    try:
        until_date = None
        if duration > 0:
            until_date = datetime.now() + timedelta(seconds=duration)
            db.execute_query(
                "INSERT OR REPLACE INTO muted_users (user_id, group_id, until_date) VALUES (?, ?, ?)",
                (target.id, message.chat.id, until_date)
            )
        
        bot.restrict_chat_member(
            message.chat.id, target.id,
            until_date=until_date,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        
        duration_text = f" لمدة {duration} ثانية" if duration > 0 else " للأبد"
        bot.reply_to(message, f"✅ تم كتم {target.first_name}{duration_text}\nالسبب: {reason}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ فشل الكتم: {e}")

@safe_execution
@admin_only
def handle_unmute(message):
    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ يرجى الرد على رسالة المستخدم أو إضافة معرفه")
        return
    
    try:
        bot.restrict_chat_member(
            message.chat.id, target.id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        
        db.execute_query(
            "DELETE FROM muted_users WHERE user_id = ? AND group_id = ?",
            (target.id, message.chat.id)
        )
        
        bot.reply_to(message, f"✅ تم إلغاء كتم {target.first_name}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل إلغاء الكتم: {e}")

#مبرمج البوت @Devazf

@safe_execution
@admin_only
def handle_settings(message):
    args = message.text.split()
    if len(args) == 1:
        settings = db.execute_query(
            "SELECT punishment_type, mute_duration, warn_limit, auto_moderation FROM group_settings WHERE group_id = ?",
            (message.chat.id,), fetch_one=True
        )
        
        if settings:
            punishment, mute_duration, warn_limit, auto_mod = settings
            auto_text = "مفعل" if auto_mod else "معطل"
            mute_text = f"{mute_duration} ثانية" if mute_duration > 0 else "غير محدد"
            
            text = f"⚙️ إعدادات المجموعة:\n"
            text += f"• العقوبة التلقائية: {punishment}\n"
            text += f"• مدة الكتم: {mute_text}\n"
            text += f"• حد الإنذارات: {warn_limit}\n"
            text += f"• المراقبة التلقائية: {auto_text}"
        else:
            text = "⚙️ لم يتم تعيين إعدادات خاصة. الإعدادات الافتراضية:\n"
            text += "• العقوبة: ban\n• المراقبة التلقائية: مفعل"
        
        bot.reply_to(message, text)
        
    elif len(args) >= 3:
        setting = args[1].lower()
        value = args[2].lower()
        
        if setting == "punishment":
            if value in ["ban", "kick", "mute", "warn"]:
                db.execute_query(
                    "INSERT OR REPLACE INTO group_settings (group_id, punishment_type) VALUES (?, ?)",
                    (message.chat.id, value)
                )
                bot.reply_to(message, f"✅ تم تعيين العقوبة التلقائية إلى: {value}")
            else:
                bot.reply_to(message, "❌ قيمة غير صحيحة. اختر: ban, kick, mute, warn")
        
        elif setting == "mutetime" and len(args) >= 4:
            try:
                duration = int(args[3])
                db.execute_query(
                    "UPDATE group_settings SET mute_duration = ? WHERE group_id = ?",
                    (duration, message.chat.id)
                )
                bot.reply_to(message, f"✅ تم تعيين مدة الكتم إلى: {duration} ثانية")
            except:
                bot.reply_to(message, "❌ يرجى إدخال رقم صحيح للمدة")
        
        elif setting == "warnlimit":
            try:
                limit = int(value)
                db.execute_query(
                    "UPDATE group_settings SET warn_limit = ? WHERE group_id = ?",
                    (limit, message.chat.id)
                )
                bot.reply_to(message, f"✅ تم تعيين حد الإنذارات إلى: {limit}")
            except:
                bot.reply_to(message, "❌ يرجى إدخال رقم صحيح")
        
        elif setting == "automod":
            if value in ["on", "off", "1", "0", "true", "false"]:
                auto_val = 1 if value in ["on", "1", "true"] else 0
                db.execute_query(
                    "UPDATE group_settings SET auto_moderation = ? WHERE group_id = ?",
                    (auto_val, message.chat.id)
                )
                bot.reply_to(message, f"✅ تم {'تفعيل' if auto_val else 'تعطيل'} المراقبة التلقائية")
            else:
                bot.reply_to(message, "❌ قيمة غير صحيحة. استخدم on/off")

@safe_execution
@admin_only
def handle_warns(message):
    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ يرجى الرد على رسالة المستخدم")
        return
    
    warning = db.execute_query(
        "SELECT warning_count FROM warnings WHERE user_id = ? AND group_id = ?",
        (target.id, message.chat.id), fetch_one=True
    )
    
    count = warning[0] if warning else 0
    bot.reply_to(message, f"⚠️ إنذارات {target.first_name}: {count}")

@safe_execution
@admin_only
def handle_reset_warns(message):
    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ يرجى الرد على رسالة المستخدم")
        return
    
    db.execute_query(
        "DELETE FROM warnings WHERE user_id = ? AND group_id = ?",
        (target.id, message.chat.id)
    )
    bot.reply_to(message, f"✅ تم إعادة تعيين إنذارات {target.first_name}")

#مبرمج البوت @Devazf

@safe_execution
@admin_only
def handle_help(message):
    help_text = """
🤖 **أوامر البوت المتاحة:**

**أوامر الإدارة (للمشرفين فقط):**
• `حظر` - حظر المستخدم (بالرد أو المعرف)
• `الغاء حظر` - إلغاء حظر المستخدم
• `طرد` - طرد المستخدم من المجموعة
• `كتم [مدة]` - كتم المستخدم (مثال: كتم 10 دقيقة)
• `الغاء كتم` - إلغاء كتم المستخدم
• `انذارات` - عرض إنذارات المستخدم
• `مسح انذارات` - مسح إنذارات المستخدم

**إعدادات المجموعة:**
• `اعدادات` - عرض الإعدادات الحالية
• `اعدادات punishment ban/kick/mute/warn` - تعيين العقوبة
• `اعدادات mutetime [ثواني]` - تعيين مدة الكتم
• `اعدادات warnlimit [رقم]` - تعيين حد الإنذارات
• `اعدادات automod on/off` - تفعيل/تعطيل المراقبة

**ملاحظات:**
• يمكن تنفيذ الأوامر بالرد على رسالة المستخدم
• يمكن إضافة سبب بعد الأمر (مثال: حظر 123456789 سبب مخالف)
• البوت يحتاج صلاحيات المشرف في المجموعة
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@safe_execution
def handle_group_message(message):
    if message.from_user.id == bot.get_me().id:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    muted = db.execute_query(
        "SELECT until_date FROM muted_users WHERE user_id = ? AND group_id = ?",
        (user_id, chat_id), fetch_one=True
    )
    
    if muted:
        until_date = muted[0]
        if until_date:
            try:
                until = datetime.fromisoformat(until_date.replace(' ', 'T'))
                if datetime.now() > until:
                    try:
                        bot.restrict_chat_member(
                            chat_id, user_id,
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_other_messages=True,
                            can_add_web_page_previews=True
                        )
                        db.execute_query(
                            "DELETE FROM muted_users WHERE user_id = ? AND group_id = ?",
                            (user_id, chat_id)
                        )
                    except:
                        pass
                else:
                    try:
                        bot.delete_message(chat_id, message.message_id)
                    except:
                        pass
                    return
            except:
                pass
    
    banned = db.execute_query(
        "SELECT * FROM banned_users WHERE user_id = ? AND group_id = ?",
        (user_id, chat_id), fetch_one=True
    )
    
    if banned:
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        return
    
    settings = db.execute_query(
        "SELECT auto_moderation FROM group_settings WHERE group_id = ?",
        (chat_id,), fetch_one=True
    )
    
    auto_mod = settings[0] if settings else 1
    
    if auto_mod and message.text:
        is_inappropriate = check_content_moderation(message.text)
        
        if is_inappropriate:
            try:
                bot.delete_message(chat_id, message.message_id)
                
                punish_user(message, user_id, chat_id, "محتوى غير أخلاقي")
                
            except Exception as e:
                print(f"❌ خطأ في معالجة الرسالة غير الأخلاقية: {e}")

@safe_execution
def handle_private_message(message):
    if message.text == '/start':
        bot.send_message(
            message.chat.id,
            "👋 مرحباً! أنا بوت حماية المجموعات.\n"
            "أقوم بمراقبة المحتوى غير الأخلاقي وتطبيق العقوبات.\n\n"
            "لإضافتي إلى مجموعتك، احتاج صلاحيات المشرف.\n"
            "للحصول على المساعدة، أرسل 'مساعدة'"
        )
    elif message.text == 'مساعدة' or message.text == 'help':
        bot.send_message(
            message.chat.id,
            "🤖 **أوامر البوت:**\n\n"
            "في المجموعات (للمشرفين):\n"
            "• حظر - حظر مستخدم\n"
            "• الغاء حظر - إلغاء حظر\n"
            "• طرد - طرد مستخدم\n"
            "• كتم - كتم مستخدم\n"
            "• الغاء كتم - إلغاء كتم\n"
            "• اعدادات - إعدادات المجموعة\n\n"
            "يمكن تنفيذ الأوامر بالرد على رسالة المستخدم.",
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            message.chat.id,
            "مرحباً! أنا بوت حماية المجموعات.\n"
            "أرسل 'مساعدة' لعرض الأوامر المتاحة."
        )

#مبرمج البوت @Devazf

def register_handlers():
    bot.register_message_handler(handle_ban, func=lambda m: m.text and m.text.startswith('حظر') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_unban, func=lambda m: m.text and m.text.startswith('الغاء حظر') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_kick, func=lambda m: m.text and m.text.startswith('طرد') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_mute, func=lambda m: m.text and m.text.startswith('كتم') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_unmute, func=lambda m: m.text and m.text.startswith('الغاء كتم') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_warns, func=lambda m: m.text and m.text.startswith('انذارات') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_reset_warns, func=lambda m: m.text and m.text.startswith('مسح انذارات') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_settings, func=lambda m: m.text and m.text.startswith('اعدادات') and m.chat.type in ['group', 'supergroup'])
    bot.register_message_handler(handle_help, func=lambda m: m.text and m.text == 'مساعدة' and m.chat.type in ['group', 'supergroup'])
    
    bot.register_message_handler(handle_group_message, func=lambda m: m.chat.type in ['group', 'supergroup'], content_types=['text'])
    
    bot.register_message_handler(handle_private_message, func=lambda m: m.chat.type == 'private')

#مبرمج البوت @Devazf

def start_bot():
    print("✅ البوت يعمل بنجاح!")
    
    register_handlers()
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout:
            print("⚠️ انتهت مهلة الاتصال، إعادة المحاولة...")
            time.sleep(5)
            continue
        except requests.exceptions.ConnectionError:
            print("⚠️ مشكلة في الاتصال بالإنترنت، إعادة المحاولة بعد 10 ثوان...")
            time.sleep(10)
            continue
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            print("🔄 إعادة تشغيل البوت بعد 5 ثوان...")
            time.sleep(5)
            continue

if __name__ == "__main__":
    start_bot()
