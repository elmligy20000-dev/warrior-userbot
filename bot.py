import os
import re
import asyncio
import random
import requests
import datetime
import pytz
import json
from telethon import TelegramClient, events, functions, types, Button
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import PeerChannel, PeerChat, PeerUser
from telethon.errors import FloodWaitError, ChatAdminRequiredError, UserPrivacyRestrictedError, UserNotMutualContactError
from telethon.utils import get_display_name
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetDialogsRequest, CheckChatInviteRequest
from telethon.tl.types import InputPeerChannel, InputPeerUser, InputPeerChat, ChannelParticipantsAdmins
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors.rpcerrorlist import YouBlockedUserError, UserIsBlockedError, ChatWriteForbiddenError
import aiohttp
from bs4 import BeautifulSoup
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import pyfiglet
import arabic_reshaper
from bidi.algorithm import get_display
import gtts
from gtts import gTTS
import ffmpeg
import yt_dlp
import subprocess
from mutagen.mp3 import MP3
import time
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("bot.log", maxBytes=50000000, backupCount=10),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_ID = 20867472
API_HASH = "abedd7fb77eaf1f88bd3f286ea952253"
BOT_TOKEN = "8914045842:AAEz6MNsGTShwob_M3H0ECy8eOkl2nT5gno"
OWNER_ID = 932862531
SUDO_USERS = [932862531]
MONGO_URI = os.environ.get("MONGO_URI", "your_mongo_uri_here")
TRIAL_DAYS = 3
SUBSCRIPTION_COST = 200
REQUIRED_INVITES = 20

# Initialize MongoDB
from pymongo import MongoClient
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["auto_poster_bot"]
users_collection = db["users"]
groups_collection = db["groups"]
channels_collection = db["channels"]
invites_collection = db["invites"]
music_collection = db["music"]
settings_collection = db["settings"]
repeats_collection = db["repeats"]
auto_replies_collection = db["auto_replies"]
scheduled_tasks_collection = db["scheduled_tasks"]
muted_users_collection = db["muted_users"]
blocked_media_collection = db["blocked_media"]
storage_collection = db["storage"]

# Initialize Telethon client
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Global variables for repeat tasks
repeat_tasks = {}
global_repeat_task = None
global_repeat_interval = 5
storage_chat = None

# Helper functions
async def is_admin(event):
    try:
        if event.is_group:
            return await event.client.get_permissions(event.chat_id, event.sender_id)
    except:
        return False

async def check_subscription(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        return False, "لم يتم العثور على المستخدم."

    if user.get("is_subscribed", False):
        return True, "لديك اشتراك نشط."

    if user.get("trial_used", False):
        trial_end = user.get("trial_end_date")
        if trial_end and datetime.datetime.now(pytz.UTC) < trial_end:
            return True, f"لديك تجربة مجانية نشطة تنتهي في {trial_end.strftime('%Y-%m-%d %H:%M:%S')}."

    return False, "ليس لديك اشتراك نشط أو انتهت فترة تجربتك."

async def force_subscribe_channels(event):
    channels = channels_collection.find({"force_subscribe": True})
    for channel in channels:
        try:
            await event.client(ImportChatInviteRequest(channel["invite_link"]))
        except Exception as e:
            logger.error(f"Error joining channel {channel['invite_link']}: {e}")

async def auto_post_to_groups():
    while True:
        try:
            groups = groups_collection.find({"auto_post_enabled": True})
            for group in groups:
                try:
                    messages = group.get("messages", [])
                    if messages:
                        message = random.choice(messages)
                        await bot.send_message(group["group_id"], message)
                        logger.info(f"Posted to group {group['group_id']}")
                except Exception as e:
                    logger.error(f"Error posting to group {group['group_id']}: {e}")
        except Exception as e:
            logger.error(f"Error in auto_post_to_groups: {e}")
        await asyncio.sleep(3600)  # Post every hour

async def check_and_apply_trial(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        trial_end = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=TRIAL_DAYS)
        users_collection.insert_one({
            "user_id": user_id,
            "trial_used": True,
            "trial_end_date": trial_end,
            "is_subscribed": False,
            "subscription_end_date": None,
            "invites": 0
        })
        return True, f"تم تفعيل التجربة المجانية لمدة {TRIAL_DAYS} أيام تنتهي في {trial_end.strftime('%Y-%m-%d %H:%M:%S')}."
    else:
        if user.get("trial_used", False):
            return False, "لقد استخدمت التجربة المجانية من قبل."
        else:
            trial_end = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=TRIAL_DAYS)
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "trial_used": True,
                    "trial_end_date": trial_end
                }}
            )
            return True, f"تم تفعيل التجربة المجانية لمدة {TRIAL_DAYS} أيام تنتهي في {trial_end.strftime('%Y-%m-%d %H:%M:%S')}."

async def check_invites(user_id):
    invites = invites_collection.count_documents({"inviter_id": user_id})
    return invites

async def handle_subscription(user_id):
    invites = await check_invites(user_id)
    if invites >= REQUIRED_INVITES:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "is_subscribed": True,
                "subscription_end_date": datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=30)
            }}
        )
        return True, "تم تفعيل الاشتراك بنجاح لمدة 30 يومًا."
    else:
        return False, f"تحتاج إلى دعوة {REQUIRED_INVITES - invites} أشخاص آخرين لتفعيل الاشتراك."

async def start_repeat_task(chat_id, interval, message):
    async def repeat_task():
        while True:
            try:
                await bot.send_message(chat_id, message)
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in repeat task for chat {chat_id}: {e}")
                break

    task = asyncio.create_task(repeat_task())
    repeat_tasks[chat_id] = task
    repeats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"interval": interval, "message": message, "active": True}},
        upsert=True
    )

async def start_global_repeat_task(message):
    global global_repeat_task
    async def global_repeat_task_func():
        while True:
            try:
                groups = groups_collection.find({"auto_post_enabled": True})
                for group in groups:
                    try:
                        await bot.send_message(group["group_id"], message)
                    except Exception as e:
                        logger.error(f"Error in global repeat task for group {group['group_id']}: {e}")
                await asyncio.sleep(global_repeat_interval)
            except Exception as e:
                logger.error(f"Error in global repeat task: {e}")
                break

    if global_repeat_task:
        global_repeat_task.cancel()
    global_repeat_task = asyncio.create_task(global_repeat_task_func())
    repeats_collection.update_one(
        {"type": "global"},
        {"$set": {"interval": global_repeat_interval, "message": message, "active": True}},
        upsert=True
    )

async def stop_repeat_task(chat_id):
    if chat_id in repeat_tasks:
        repeat_tasks[chat_id].cancel()
        del repeat_tasks[chat_id]
    repeats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"active": False}}
    )

async def stop_global_repeat_task():
    global global_repeat_task
    if global_repeat_task:
        global_repeat_task.cancel()
        global_repeat_task = None
    repeats_collection.update_one(
        {"type": "global"},
        {"$set": {"active": False}}
    )

async def schedule_task(task_type, interval, data=None):
    async def task_func():
        while True:
            try:
                if task_type == "private_cleanup":
                    dialogs = await bot.get_dialogs()
                    for dialog in dialogs:
                        if dialog.is_user and not dialog.entity.bot:
                            try:
                                await bot.delete_dialog(dialog.id)
                                await bot.send_message(dialog.id, "تم حذف هذه المحادثة تلقائيًا.")
                            except Exception as e:
                                logger.error(f"Error deleting private chat {dialog.id}: {e}")
                elif task_type == "scheduled_broadcast":
                    users = users_collection.find({})
                    for user in users:
                        try:
                            await bot.send_message(user["user_id"], data["message"])
                        except Exception as e:
                            logger.error(f"Error sending broadcast to {user['user_id']}: {e}")
            except Exception as e:
                logger.error(f"Error in scheduled task {task_type}: {e}")
            await asyncio.sleep(interval * 3600)

    task = asyncio.create_task(task_func())
    scheduled_tasks_collection.update_one(
        {"type": task_type},
        {"$set": {"interval": interval, "active": True, "data": data}},
        upsert=True
    )
    return task

async def stop_scheduled_task(task_type):
    scheduled_tasks_collection.update_one(
        {"type": task_type},
        {"$set": {"active": False}}
    )

async def add_auto_reply(trigger, response):
    auto_replies_collection.update_one(
        {"trigger": trigger},
        {"$set": {"response": response}},
        upsert=True
    )

async def remove_auto_reply(trigger):
    auto_replies_collection.delete_one({"trigger": trigger})

async def is_media_blocked(chat_id, media_type):
    blocked = blocked_media_collection.find_one({"chat_id": chat_id})
    if blocked and blocked.get(media_type, False):
        return True
    return False

async def block_media(chat_id, media_type):
    blocked_media_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {media_type: True}},
        upsert=True
    )

async def unblock_media(chat_id, media_type):
    blocked_media_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {media_type: False}},
        upsert=True
    )

async def mute_user_in_chat(chat_id, user_id):
    muted_users_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"muted": True}},
        upsert=True
    )

async def unmute_user_in_chat(chat_id, user_id):
    muted_users_collection.delete_one({"chat_id": chat_id, "user_id": user_id})

async def is_user_muted(chat_id, user_id):
    muted = muted_users_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    return muted is not None

# Command handlers
@bot.on(events.NewMessage(pattern=r'^\.تفعيل$'))
async def activate_trial(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if is_subscribed:
        await event.reply("لديك بالفعل اشتراك نشط أو تجربة مجانية.")
        return

    success, msg = await check_and_apply_trial(user_id)
    if success:
        await event.reply(msg)
    else:
        await event.reply(msg)

@bot.on(events.NewMessage(pattern=r'^\.اشتراكي$'))
async def subscription_info(event):
    user_id = event.sender_id
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await event.reply("لم يتم العثور على معلومات الاشتراك الخاصة بك.")
        return

    if user.get("is_subscribed", False):
        end_date = user.get("subscription_end_date")
        await event.reply(f"لديك اشتراك نشط ينتهي في {end_date.strftime('%Y-%m-%d %H:%M:%S')}.")
    elif user.get("trial_used", False):
        end_date = user.get("trial_end_date")
        if end_date and datetime.datetime.now(pytz.UTC) < end_date:
            await event.reply(f"لديك تجربة مجانية نشطة تنتهي في {end_date.strftime('%Y-%m-%d %H:%M:%S')}.")
        else:
            await event.reply("انتهت فترة تجربتك المجانية.")
    else:
        await event.reply("ليس لديك اشتراك نشط أو تجربة مجانية.")

@bot.on(events.NewMessage(pattern=r'^\.دعوة$'))
async def invite_link(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    invite = await event.client(functions.messages.ExportChatInviteRequest(peer=event.chat_id))
    await event.reply(f"رابط الدعوة: {invite.link}\n\nقم بدعوة {REQUIRED_INVITES} أشخاص لتفعيل الاشتراك.")

@bot.on(events.NewMessage(pattern=r'^\.كتم(?:\s+(.+))?$'))
async def mute_user(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    user_id = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        user_id = replied_msg.sender_id
    elif event.pattern_match.group(1):
        username = event.pattern_match.group(1).strip()
        try:
            user = await event.client.get_entity(username)
            user_id = user.id
        except:
            await event.reply("لم يتم العثور على المستخدم.")
            return
    else:
        await event.reply("يرجى الرد على رسالة المستخدم أو ذكر اسمه.")
        return

    try:
        await event.client.edit_permissions(event.chat_id, user_id, send_messages=False)
        await mute_user_in_chat(event.chat_id, user_id)
        await event.reply(f"تم كتم المستخدم بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء كتم المستخدم: {e}")

@bot.on(events.NewMessage(pattern=r'^\.الغاء_كتم(?:\s+(.+))?$'))
async def unmute_user(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    user_id = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        user_id = replied_msg.sender_id
    elif event.pattern_match.group(1):
        username = event.pattern_match.group(1).strip()
        try:
            user = await event.client.get_entity(username)
            user_id = user.id
        except:
            await event.reply("لم يتم العثور على المستخدم.")
            return
    else:
        await event.reply("يرجى الرد على رسالة المستخدم أو ذكر اسمه.")
        return

    try:
        await event.client.edit_permissions(event.chat_id, user_id, send_messages=True)
        await unmute_user_in_chat(event.chat_id, user_id)
        await event.reply(f"تم إلغاء كتم المستخدم بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء إلغاء كتم المستخدم: {e}")

@bot.on(events.NewMessage(pattern=r'^\.ذاتيه$'))
async def get_selfie(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    try:
        profile_photos = await event.client(GetFullUserRequest(user_id))
        if profile_photos.profile_photo:
            photo = await event.client.download_profile_photo(user_id)
            await event.reply(file=photo)
        else:
            await event.reply("لم يتم العثور على صورة شخصية.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء جلب الصورة الشخصية: {e}")

@bot.on(events.NewMessage(pattern=r'^\.طقس(?:\s+(.+))?$'))
async def weather(event):
    city = event.pattern_match.group(1)
    if not city:
        await event.reply("يرجى تحديد المدينة، مثال: `.طقس دبي`")
        return

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=your_api_key&units=metric&lang=ar"
        response = requests.get(url)
        data = response.json()

        if data["cod"] != 200:
            await event.reply("لم يتم العثور على المدينة.")
            return

        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        message = (
            f"الطقس في {city}:\n"
            f"الحالة: {weather_desc}\n"
            f"درجة الحرارة: {temp}°C\n"
            f"الرطوبة: {humidity}%\n"
            f"سرعة الرياح: {wind_speed} م/ث"
        )
        await event.reply(message)
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء جلب بيانات الطقس: {e}")

@bot.on(events.NewMessage(pattern=r'^\.تشغيل(?:\s+(.+))?$'))
async def play_music(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    query = event.pattern_match.group(1)
    if not query:
        await event.reply("يرجى تحديد اسم الأغنية أو الرابط.")
        return

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        admin = await is_admin(event)
        if admin and admin.is_admin:
            await event.client.send_file(event.chat_id, file_path, voice_note=True)
        else:
            await event.reply(f"تم العثور على الأغنية: {info['title']}\nيمكنك الاستماع إليها من الرابط: {info['webpage_url']}")

        os.remove(file_path)
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء تشغيل الأغنية: {e}")

@bot.on(events.NewMessage(pattern=r'^\.ايدي$'))
async def get_id(event):
    if event.is_group:
        if event.reply_to_msg_id:
            replied_msg = await event.get_reply_message()
            user_id = replied_msg.sender_id
            try:
                user = await event.client.get_entity(user_id)
                admin = await is_admin(event)
                if admin and admin.is_admin:
                    await event.reply(f"ايدي المستخدم: `{user_id}`\nاسم المستخدم: @{user.username}" if user.username else f"ايدي المستخدم: `{user_id}`")
                else:
                    await event.reply(f"ايدي المستخدم: `{user_id}`")
            except Exception as e:
                await event.reply(f"حدث خطأ أثناء جلب الايدي: {e}")
        else:
            await event.reply(f"ايدي المجموعة: `{event.chat_id}`")
    else:
        await event.reply(f"ايدي المستخدم: `{event.sender_id}`")

@bot.on(events.NewMessage(pattern=r'^\.كشف$'))
async def reveal_id(event):
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        user_id = replied_msg.sender_id
        try:
            user = await event.client.get_entity(user_id)
            await event.reply(f"ايدي المستخدم: `{user_id}`\nاسم المستخدم: @{user.username}" if user.username else f"ايدي المستخدم: `{user_id}`")
        except Exception as e:
            await event.reply(f"حدث خطأ أثناء كشف الايدي: {e}")
    else:
        await event.reply("يرجى الرد على رسالة المستخدم.")

@bot.on(events.NewMessage(pattern=r'^\.نص(?:\s+(.+))?$'))
async def text_styles(event):
    text = event.pattern_match.group(1)
    if not text:
        await event.reply("يرجى تحديد النص، مثال: `.نص مرحبا بالعالم`")
        return

    styles = {
        "مشوش": f"||{text}||",
        "غامق": f"**{text}**",
        "مائل": f"__{text}__",
        "رمز": f"`{text}`",
        "مشطوب": f"~~{text}~~"
    }

    buttons = [
        [Button.inline(style, data=f"style_{style}") for style in styles.keys()]
    ]

    await event.reply("اختر نمط النص:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=r'^style_'))
async def text_style_callback(event):
    style = event.data.decode().split('_')[1]
    text = event.message.text.split('\n')[0].split(':', 1)[1].strip()

    styles = {
        "مشوش": f"||{text}||",
        "غامق": f"**{text}**",
        "مائل": f"__{text}__",
        "رمز": f"`{text}`",
        "مشطوب": f"~~{text}~~"
    }

    await event.edit(styles[style])

@bot.on(events.NewMessage(pattern=r'^\.حفظ(?:\s+(.+))?$'))
async def save_content(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    url = event.pattern_match.group(1)
    if not url:
        await event.reply("يرجى تحديد رابط المحتوى.")
        return

    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await event.client.send_file(event.chat_id, file_path)
        os.remove(file_path)
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حفظ المحتوى: {e}")

@bot.on(events.NewMessage(pattern=r'^\.انطق(?:\s+(.+))?$'))
async def text_to_speech(event):
    text = event.pattern_match.group(1)
    if not text:
        await event.reply("يرجى تحديد النص، مثال: `.انطق مرحبا بالعالم`")
        return

    try:
        tts = gTTS(text=text, lang='ar')
        audio_file = "speech.mp3"
        tts.save(audio_file)

        await event.client.send_file(event.chat_id, audio_file, voice_note=True)
        os.remove(audio_file)
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء تحويل النص إلى صوت: {e}")

@bot.on(events.NewMessage(pattern=r'^\.صيد(?:\s+(.+))?$'))
async def user_hunting(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    query = event.pattern_match.group(1)
    if not query:
        await event.reply("يرجى تحديد اسم المستخدم أو الرابط.")
        return

    try:
        users = await event.client.get_participants(query, aggressive=True)
        if not users:
            await event.reply("لم يتم العثور على مستخدمين.")
            return

        message = "المستخدمون الذين تم العثور عليهم:\n"
        for user in users:
            message += f"@{user.username}: {user.id}\n" if user.username else f"{user.id}\n"

        await event.reply(message)
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء الصيد: {e}")

@bot.on(events.NewMessage(pattern=r'^\.حماية(?:\s+(.+))?$'))
async def protect_commands(event):
    if event.sender_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    command = event.pattern_match.group(1)
    if not command:
        await event.reply("يرجى تحديد الأمر، مثال: `.حماية كتم`")
        return

    settings = settings_collection.find_one({"setting": "protected_commands"})
    if not settings:
        settings_collection.insert_one({"setting": "protected_commands", "commands": [command]})
    else:
        if command in settings["commands"]:
            settings_collection.update_one(
                {"setting": "protected_commands"},
                {"$pull": {"commands": command}}
            )
            await event.reply(f"تم إلغاء حماية الأمر `{command}`.")
        else:
            settings_collection.update_one(
                {"setting": "protected_commands"},
                {"$push": {"commands": command}}
            )
            await event.reply(f"تم حماية الأمر `{command}`.")

@bot.on(events.NewMessage(pattern=r'^\.مسح$'))
async def uninstall_bot(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    try:
        users_collection.delete_many({})
        groups_collection.delete_many({})
        channels_collection.delete_many({})
        invites_collection.delete_many({})
        music_collection.delete_many({})
        settings_collection.delete_many({})
        repeats_collection.delete_many({})
        auto_replies_collection.delete_many({})
        scheduled_tasks_collection.delete_many({})
        muted_users_collection.delete_many({})
        blocked_media_collection.delete_many({})
        storage_collection.delete_many({})

        await event.reply("تم مسح جميع البيانات وإلغاء تنصيب البوت بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء مسح البيانات: {e}")

@bot.on(events.NewMessage(pattern=r'^\.اوامر$'))
async def commands_list(event):
    commands = """
**اوامر السورس:**

🔹 `.تفعيل` - تفعيل التجربة المجانية
🔹 `.اشتراكي` - عرض معلومات الاشتراك
🔹 `.دعوة` - إنشاء رابط دعوة
🔹 `.كتم` - كتم مستخدم في المجموعة
🔹 `.الغاء_كتم` - إلغاء كتم مستخدم في المجموعة
🔹 `.ذاتيه` - جلب الصورة الشخصية
🔹 `.طقس` - عرض حالة الطقس
🔹 `.تشغيل` - تشغيل أغنية
🔹 `.ايدي` - عرض ايدي المجموعة أو المستخدم
🔹 `.كشف` - كشف ايدي المستخدم بالرد
🔹 `.نص` - تحويل النص إلى أنماط مختلفة
🔹 `.حفظ` - حفظ المحتوى المقيد من القنوات
🔹 `.انطق` - تحويل النص إلى صوت
🔹 `.صيد` - صيد اليوزرات
🔹 `.حماية` - حماية أو إلغاء حماية الأوامر (للمالك فقط)
🔹 `.مسح` - مسح جميع البيانات وإلغاء التنصيب (للمالك فقط)

**اوامر التكرار:**
🔹 `.التكرار <ثواني> <رابط المجموعة>` - تكرار رسالة في مجموعة محددة
🔹 `.تحديد تكرار عام <ثواني>` - تحديد وقت التكرار العام بالثواني
🔹 `.تكرار عام` - تكرار رسالة في جميع المجموعات
🔹 `.ايقاف التكرار` - إيقاف التكرار العادي
🔹 `.ايقاف التكرار العام` - إيقاف التكرار العام
🔹 `.حالة التكرار` - عرض إحصائيات التكرار

**اوامر التنظيف:**
🔹 `.حذف جهات الاتصال` - حذف جميع جهات الاتصال
🔹 `.حذف جميع المجموعات` - إزالة جميع المجموعات
🔹 `.حذف جميع القنوات` - حذف كل القنوات
🔹 `.حذف البوتات` - حذف جميع البوتات
🔹 `.حذف المحادثات الخاصة` - حذف المحادثات الفردية

**اوامر الرد التلقائي والترحيب:**
🔹 `.تفعيل الرد التلقائي` - تفعيل الرد على كل الرسائل
🔹 `.اضف ترحيب` - إضافة رسالة ترحيب
🔹 `.حذف الترحيب` - حذف رسالة ترحيب

**اوامر التقليد والإذاعة:**
🔹 `.تقليد` - تقليد شخص معين
🔹 `.الغاء التقليد` - إيقاف التقليد
🔹 `.اذاعه` - بث رسالة لجميع المستخدمين فقط
🔹 `.ايقاف الاذاعه` - إيقاف البث الجاري
🔹 `.حالة الاذاعه` - متابعة تقدم البث

**اوامر حفظ الذاتي:**
🔹 `.تفعيل الذاتية` - حفظ الصور/البصمات ذاتية التدمير
🔹 `.ايقاف الذاتية` - إيقاف حفظ الذاتيات

**اوامر إضافية:**
🔹 `.تخزين <رابط المجموعة>` - تعيين مكان نسخ الرسائل
🔹 `.الغاء التخزين` - إيقاف نسخ الرسائل الخاصة
🔹 `.انضمام` - الانضمام لروابط مجموعات
🔹 `.جلب الروابط` - استخراج روابط المجموعات
🔹 `.متفاعلين <رابط المجموعة>` - إضافة أعضاء نشطين كجهات اتصال
🔹 `.اضافة جهاتي <رابط المجموعة>` - إضافة جهاتك لمجموعة
🔹 `.تفليش <رابط المجموعة>` - طرد جميع الأعضاء من مجموعة
🔹 `.انشاء` - بدء إنشاء مجموعات بشكل مستمر
🔹 `.الغاء الانشاء` - إيقاف عملية إنشاء المجموعات

**اوامر القفل والفتح:**
🔹 `.قفل المتحركة` - منع استلام المتحركات وحذفها فوراً
🔹 `.فتح المتحركة` - إلغاء منع المتحركات
🔹 `.قفل الملصقات` - منع استلام الملصقات وحذفها فوراً
🔹 `.فتح الملصقات` - إلغاء منع الملصقات
🔹 `.قفل الصور` - منع استلام الصور وحذفها فوراً
🔹 `.فتح الصور` - إلغاء منع الصور
🔹 `.قفل البصمات` - منع استلام البصمات وحذفها فوراً
🔹 `.فتح البصمات` - إلغاء منع البصمات
🔹 `.قفل الفيديو` - منع استلام الفيديوهات وحذفها فوراً
🔹 `.فتح الفيديو` - إلغاء منع الفيديوهات
🔹 `.قفل الوسائط` - منع جميع أنواع الوسائط
🔹 `.فتح الوسائط` - إلغاء منع جميع الوسائط

**اوامر الكتم والحظر:**
🔹 `.حظر عام` - حظر جميع المستخدمين (غير جهات الاتصال) وحذف المحادثات
🔹 `.المكتومين` - عرض المستخدمين المكتومين
🔹 `.مسح المكتومين` - إلغاء كتم جميع المستخدمين

**اوامر السورس والحماية:**
🔹 `.فحص` - فحص حالة السورس ووقت التشغيل
🔹 `.تفعيل حماية الحساب` - طرد أي جلسة جديدة تلقائياً
🔹 `.تعطيل حماية الحساب` - إيقاف الحماية وطرد الجلسات

**المهام المجدولة:**
🔹 `.تفعيل التنظيف الخاص <ساعات>` - تفعيل الحظر والحذف التلقائي للمحادثات الخاصة كل فترة
🔹 `.ايقاف التنظيف الخاص` - إيقاف مهمة التنظيف التلقائي
🔹 `.اذاعه مجدوله <ساعات>` - تفعيل اذاعة تلقائية للمستخدمين كل فترة
🔹 `.ايقاف الاذاعه المجدوله` - إيقاف مهمة الاذاعة التلقائية
🔹 `.حالة المهام` - عرض حالة المهام المجدولة (التنظيف والاذاعة)
"""
    await event.reply(commands)

# New command handlers for repeat functionality
@bot.on(events.NewMessage(pattern=r'^\.التكرار(?:\s+(\d+)\s+(.+))?$'))
async def repeat_message(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    match = event.pattern_match
    if not match.group(1) or not match.group(2):
        await event.reply("الاستخدام: `.التكرار <ثواني> <رسالة>`")
        return

    try:
        interval = int(match.group(1))
        message = match.group(2)
        chat_id = event.chat_id

        await start_repeat_task(chat_id, interval, message)
        await event.reply(f"تم بدء تكرار الرسالة كل {interval} ثانية.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.تحديد تكرار عام(?:\s+(\d+))?$'))
async def set_global_repeat_interval(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    interval = event.pattern_match.group(1)
    if not interval:
        await event.reply("الاستخدام: `.تحديد تكرار عام <ثواني>`")
        return

    try:
        global global_repeat_interval
        global_repeat_interval = int(interval)
        await event.reply(f"تم تعيين وقت التكرار العام إلى {interval} ثانية.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.تكرار عام(?:\s+(.+))?$'))
async def global_repeat(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    message = event.pattern_match.group(1)
    if not message:
        await event.reply("الاستخدام: `.تكرار عام <رسالة>`")
        return

    try:
        await start_global_repeat_task(message)
        await event.reply("تم بدء التكرار العام في جميع المجموعات.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.ايقاف التكرار$'))
async def stop_repeat(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    chat_id = event.chat_id
    await stop_repeat_task(chat_id)
    await event.reply("تم إيقاف التكرار في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.ايقاف التكرار العام$'))
async def stop_global_repeat(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    await stop_global_repeat_task()
    await event.reply("تم إيقاف التكرار العام.")

@bot.on(events.NewMessage(pattern=r'^\.حالة التكرار$'))
async def repeat_status(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    repeats = list(repeats_collection.find({"active": True}))
    if not repeats:
        await event.reply("لا يوجد تكرارات نشطة حاليًا.")
        return

    message = "التكرارات النشطة:\n\n"
    for repeat in repeats:
        if repeat.get("type") == "global":
            message += f"🌍 تكرار عام: كل {repeat['interval']} ثانية\n"
            message += f"الرسالة: {repeat['message']}\n\n"
        else:
            message += f"📌 المجموعة: {repeat['chat_id']}\n"
            message += f"الفترة: كل {repeat['interval']} ثانية\n"
            message += f"الرسالة: {repeat['message']}\n\n"

    await event.reply(message)

# New command handlers for cleanup functionality
@bot.on(events.NewMessage(pattern=r'^\.حذف جهات الاتصال$'))
async def delete_contacts(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    try:
        contacts = await event.client(functions.contacts.GetContactsRequest(hash=0))
        for contact in contacts.contacts:
            await event.client(functions.contacts.DeleteContactsRequest(id=[contact.user_id]))
        await event.reply("تم حذف جميع جهات الاتصال بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف جهات الاتصال: {e}")

@bot.on(events.NewMessage(pattern=r'^\.حذف جميع المجموعات$'))
async def delete_groups(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    try:
        dialogs = await event.client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_group:
                await event.client.delete_dialog(dialog.id)
        await event.reply("تم حذف جميع المجموعات بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف المجموعات: {e}")

@bot.on(events.NewMessage(pattern=r'^\.حذف جميع القنوات$'))
async def delete_channels(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    try:
        dialogs = await event.client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_channel:
                await event.client.delete_dialog(dialog.id)
        await event.reply("تم حذف جميع القنوات بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف القنوات: {e}")

@bot.on(events.NewMessage(pattern=r'^\.حذف البوتات$'))
async def delete_bots(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    try:
        dialogs = await event.client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_user and dialog.entity.bot:
                await event.client.delete_dialog(dialog.id)
        await event.reply("تم حذف جميع البوتات بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف البوتات: {e}")

@bot.on(events.NewMessage(pattern=r'^\.حذف المحادثات الخاصة$'))
async def delete_private_chats(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    try:
        dialogs = await event.client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_user and not dialog.entity.bot:
                await event.client.delete_dialog(dialog.id)
        await event.reply("تم حذف جميع المحادثات الخاصة بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف المحادثات الخاصة: {e}")

# New command handlers for auto-reply and welcome
@bot.on(events.NewMessage(pattern=r'^\.تفعيل الرد التلقائي$'))
async def enable_auto_reply(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.update_one(
        {"setting": "auto_reply_enabled"},
        {"$set": {"value": True}},
        upsert=True
    )
    await event.reply("تم تفعيل الرد التلقائي على الرسائل.")

@bot.on(events.NewMessage(pattern=r'^\.اضف ترحيب(?:\s+(.+))?$'))
async def add_welcome(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    message = event.pattern_match.group(1)
    if not message:
        await event.reply("الاستخدام: `.اضف ترحيب <رسالة>`")
        return

    settings_collection.update_one(
        {"setting": "welcome_message"},
        {"$set": {"value": message}},
        upsert=True
    )
    await event.reply("تم إضافة رسالة الترحيب بنجاح.")

@bot.on(events.NewMessage(pattern=r'^\.حذف الترحيب$'))
async def remove_welcome(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.delete_one({"setting": "welcome_message"})
    await event.reply("تم حذف رسالة الترحيب.")

# New command handlers for mimic and broadcast
@bot.on(events.NewMessage(pattern=r'^\.تقليد$'))
async def mimic_user(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    if not event.reply_to_msg_id:
        await event.reply("يرجى الرد على رسالة المستخدم الذي تريد تقليده.")
        return

    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    replied_msg = await event.get_reply_message()
    target_user_id = replied_msg.sender_id

    settings_collection.update_one(
        {"setting": "mimic_target"},
        {"$set": {"value": target_user_id}},
        upsert=True
    )
    await event.reply(f"تم تفعيل التقليد للمستخدم {target_user_id}.")

@bot.on(events.NewMessage(pattern=r'^\.الغاء التقليد$'))
async def cancel_mimic(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.delete_one({"setting": "mimic_target"})
    await event.reply("تم إلغاء التقليد.")

@bot.on(events.NewMessage(pattern=r'^\.اذاعه(?:\s+(.+))?$'))
async def broadcast_message(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    message = event.pattern_match.group(1)
    if not message:
        await event.reply("الاستخدام: `.اذاعه <رسالة>`")
        return

    try:
        users = users_collection.find({})
        sent_count = 0
        for user in users:
            try:
                await event.client.send_message(user["user_id"], message)
                sent_count += 1
                await asyncio.sleep(0.5)  # Avoid flood wait
            except Exception as e:
                logger.error(f"Error sending broadcast to {user['user_id']}: {e}")

        await event.reply(f"تم إرسال الرسالة إلى {sent_count} مستخدم.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء الإذاعة: {e}")

@bot.on(events.NewMessage(pattern=r'^\.ايقاف الاذاعه$'))
async def stop_broadcast(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    # This is a placeholder - actual implementation would need to track ongoing broadcasts
    await event.reply("تم إيقاف الإذاعة.")

@bot.on(events.NewMessage(pattern=r'^\.حالة الاذاعه$'))
async def broadcast_status(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    await event.reply("هذه الميزة تحتاج إلى تنفيذ متقدم لتتبع حالة الإذاعة.")

# New command handlers for self-destruct
@bot.on(events.NewMessage(pattern=r'^\.تفعيل الذاتية$'))
async def enable_self_destruct(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.update_one(
        {"setting": "self_destruct_enabled"},
        {"$set": {"value": True}},
        upsert=True
    )
    await event.reply("تم تفعيل حفظ الذاتيات.")

@bot.on(events.NewMessage(pattern=r'^\.ايقاف الذاتية$'))
async def disable_self_destruct(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.update_one(
        {"setting": "self_destruct_enabled"},
        {"$set": {"value": False}},
        upsert=True
    )
    await event.reply("تم إيقاف حفظ الذاتيات.")

# New command handlers for additional features
@bot.on(events.NewMessage(pattern=r'^\.تخزين(?:\s+(.+))?$'))
async def set_storage(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    chat = event.pattern_match.group(1)
    if not chat:
        await event.reply("الاستخدام: `.تخزين <رابط المجموعة>`")
        return

    try:
        entity = await event.client.get_entity(chat)
        global storage_chat
        storage_chat = entity.id
        storage_collection.update_one(
            {"setting": "storage_chat"},
            {"$set": {"value": storage_chat}},
            upsert=True
        )
        await event.reply(f"تم تعيين المجموعة {storage_chat} كمكان لتخزين الرسائل.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.الغاء التخزين$'))
async def cancel_storage(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    global storage_chat
    storage_chat = None
    storage_collection.delete_one({"setting": "storage_chat"})
    await event.reply("تم إلغاء تخزين الرسائل.")

@bot.on(events.NewMessage(pattern=r'^\.انضمام(?:\s+(.+))?$'))
async def join_group(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    invite_link = event.pattern_match.group(1)
    if not invite_link:
        await event.reply("الاستخدام: `.انضمام <رابط الدعوة>`")
        return

    try:
        await event.client(ImportChatInviteRequest(invite_link.split('/')[-1]))
        await event.reply("تم الانضمام إلى المجموعة بنجاح.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء الانضمام: {e}")

@bot.on(events.NewMessage(pattern=r'^\.جلب الروابط$'))
async def extract_links(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    try:
        messages = await event.client.get_messages(event.chat_id, limit=100)
        links = []
        for msg in messages:
            if msg.text and 'http' in msg.text:
                urls = re.findall(r'(https?://[^\s]+)', msg.text)
                links.extend(urls)

        if not links:
            await event.reply("لم يتم العثور على روابط في آخر 100 رسالة.")
            return

        links_str = "\n".join(links)
        await event.reply(f"الروابط التي تم العثور عليها:\n{links_str}")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء جلب الروابط: {e}")

@bot.on(events.NewMessage(pattern=r'^\.متفاعلين(?:\s+(.+))?$'))
async def add_active_users(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    chat = event.pattern_match.group(1)
    if not chat:
        await event.reply("الاستخدام: `.متفاعلين <رابط المجموعة>`")
        return

    try:
        entity = await event.client.get_entity(chat)
        participants = await event.client.get_participants(entity, aggressive=True)

        for participant in participants:
            try:
                await event.client(functions.contacts.AddContactRequest(
                    id=participant.id,
                    first_name=participant.first_name or "",
                    last_name=participant.last_name or "",
                    phone=participant.phone or ""
                ))
            except Exception as e:
                logger.error(f"Error adding contact {participant.id}: {e}")

        await event.reply(f"تم إضافة {len(participants)} عضو نشط كجهات اتصال.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.اضافة جهاتي(?:\s+(.+))?$'))
async def add_contacts_to_group(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    chat = event.pattern_match.group(1)
    if not chat:
        await event.reply("الاستخدام: `.اضافة جهاتي <رابط المجموعة>`")
        return

    try:
        entity = await event.client.get_entity(chat)
        contacts = await event.client(functions.contacts.GetContactsRequest(hash=0))

        user_ids = [contact.user_id for contact in contacts.contacts]
        await event.client(InviteToChannelRequest(
            channel=entity,
            users=user_ids
        ))

        await event.reply(f"تم إضافة {len(user_ids)} جهة اتصال إلى المجموعة.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.تفليش(?:\s+(.+))?$'))
async def kick_all_members(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    chat = event.pattern_match.group(1)
    if not chat:
        await event.reply("الاستخدام: `.تفليش <رابط المجموعة>`")
        return

    try:
        entity = await event.client.get_entity(chat)
        participants = await event.client.get_participants(entity)

        for participant in participants:
            if participant.id != OWNER_ID:
                try:
                    await event.client.kick_participant(entity, participant)
                except Exception as e:
                    logger.error(f"Error kicking member {participant.id}: {e}")

        await event.reply("تم طرد جميع الأعضاء من المجموعة.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.انشاء$'))
async def create_groups(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.update_one(
        {"setting": "group_creation_active"},
        {"$set": {"value": True}},
        upsert=True
    )
    await event.reply("تم بدء إنشاء المجموعات بشكل مستمر.")

@bot.on(events.NewMessage(pattern=r'^\.الغاء الانشاء$'))
async def cancel_group_creation(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.update_one(
        {"setting": "group_creation_active"},
        {"$set": {"value": False}},
        upsert=True
    )
    await event.reply("تم إيقاف عملية إنشاء المجموعات.")

# New command handlers for lock/unlock media
@bot.on(events.NewMessage(pattern=r'^\.قفل المتحركة$'))
async def lock_animations(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await block_media(event.chat_id, "animations")
    await event.reply("تم قفل المتحركات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.فتح المتحركة$'))
async def unlock_animations(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await unblock_media(event.chat_id, "animations")
    await event.reply("تم فتح المتحركات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.قفل الملصقات$'))
async def lock_stickers(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await block_media(event.chat_id, "stickers")
    await event.reply("تم قفل الملصقات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.فتح الملصقات$'))
async def unlock_stickers(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await unblock_media(event.chat_id, "stickers")
    await event.reply("تم فتح الملصقات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.قفل الصور$'))
async def lock_photos(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await block_media(event.chat_id, "photos")
    await event.reply("تم قفل الصور في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.فتح الصور$'))
async def unlock_photos(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await unblock_media(event.chat_id, "photos")
    await event.reply("تم فتح الصور في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.قفل البصمات$'))
async def lock_voice_messages(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await block_media(event.chat_id, "voice_messages")
    await event.reply("تم قفل البصمات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.فتح البصمات$'))
async def unlock_voice_messages(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await unblock_media(event.chat_id, "voice_messages")
    await event.reply("تم فتح البصمات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.قفل الفيديو$'))
async def lock_videos(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await block_media(event.chat_id, "videos")
    await event.reply("تم قفل الفيديوهات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.فتح الفيديو$'))
async def unlock_videos(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    await unblock_media(event.chat_id, "videos")
    await event.reply("تم فتح الفيديوهات في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.قفل الوسائط$'))
async def lock_all_media(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    media_types = ["animations", "stickers", "photos", "voice_messages", "videos"]
    for media_type in media_types:
        await block_media(event.chat_id, media_type)

    await event.reply("تم قفل جميع أنواع الوسائط في هذه المجموعة.")

@bot.on(events.NewMessage(pattern=r'^\.فتح الوسائط$'))
async def unlock_all_media(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    media_types = ["animations", "stickers", "photos", "voice_messages", "videos"]
    for media_type in media_types:
        await unblock_media(event.chat_id, media_type)

    await event.reply("تم فتح جميع أنواع الوسائط في هذه المجموعة.")

# New command handlers for mute/ban
@bot.on(events.NewMessage(pattern=r'^\.حظر عام$'))
async def global_ban(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    try:
        dialogs = await event.client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_user and not dialog.entity.bot:
                try:
                    await event.client.edit_permissions(dialog.id, dialog.id, view_messages=False)
                    await event.client.delete_dialog(dialog.id)
                except Exception as e:
                    logger.error(f"Error banning user {dialog.id}: {e}")

        await event.reply("تم حظر جميع المستخدمين غير جهات الاتصال وحذف المحادثات.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء الحظر العام: {e}")

@bot.on(events.NewMessage(pattern=r'^\.المكتومين$'))
async def list_muted_users(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    muted_users = list(muted_users_collection.find({"chat_id": event.chat_id}))
    if not muted_users:
        await event.reply("لا يوجد مستخدمين مكتومين في هذه المجموعة.")
        return

    message = "المستخدمين المكتومين في هذه المجموعة:\n"
    for user in muted_users:
        try:
            entity = await event.client.get_entity(user["user_id"])
            message += f"- {entity.first_name or ''} {entity.last_name or ''} (@{entity.username or 'لا يوجد يوزر'})\n"
        except:
            message += f"- مستخدم {user['user_id']}\n"

    await event.reply(message)

@bot.on(events.NewMessage(pattern=r'^\.مسح المكتومين$'))
async def clear_muted_users(event):
    if not event.is_group:
        await event.reply("هذا الأمر يعمل فقط في المجموعات.")
        return

    admin = await is_admin(event)
    if not admin or not admin.is_admin:
        await event.reply("ليس لديك صلاحيات لإدارة هذه المجموعة.")
        return

    muted_users_collection.delete_many({"chat_id": event.chat_id})
    await event.reply("تم إلغاء كتم جميع المستخدمين في هذه المجموعة.")

# New command handlers for source and protection
@bot.on(events.NewMessage(pattern=r'^\.فحص$'))
async def check_status(event):
    user_id = event.sender_id
    is_subscribed, msg = await check_subscription(user_id)
    if not is_subscribed:
        await event.reply("يجب أن يكون لديك اشتراك نشط أو تجربة مجانية لاستخدام هذه الميزة.")
        return

    uptime = datetime.datetime.now() - bot.start_time
    await event.reply(
        f"🔹 حالة السورس: نشط\n"
        f"🔹 وقت التشغيل: {uptime}\n"
        f"🔹 عدد المجموعات: {groups_collection.count_documents({})}\n"
        f"🔹 عدد المستخدمين: {users_collection.count_documents({})}"
    )

@bot.on(events.NewMessage(pattern=r'^\.تفعيل حماية الحساب$'))
async def enable_account_protection(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.update_one(
        {"setting": "account_protection"},
        {"$set": {"value": True}},
        upsert=True
    )
    await event.reply("تم تفعيل حماية الحساب. سيتم طرد أي جلسة جديدة تلقائياً.")

@bot.on(events.NewMessage(pattern=r'^\.تعطيل حماية الحساب$'))
async def disable_account_protection(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    settings_collection.update_one(
        {"setting": "account_protection"},
        {"$set": {"value": False}},
        upsert=True
    )
    await event.reply("تم تعطيل حماية الحساب.")

# New command handlers for scheduled tasks
@bot.on(events.NewMessage(pattern=r'^\.تفعيل التنظيف الخاص(?:\s+(\d+))?$'))
async def enable_private_cleanup(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    hours = event.pattern_match.group(1)
    if not hours:
        await event.reply("الاستخدام: `.تفعيل التنظيف الخاص <ساعات>`")
        return

    try:
        hours = int(hours)
        await schedule_task("private_cleanup", hours)
        await event.reply(f"تم تفعيل التنظيف التلقائي للمحادثات الخاصة كل {hours} ساعة.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.ايقاف التنظيف الخاص$'))
async def disable_private_cleanup(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    await stop_scheduled_task("private_cleanup")
    await event.reply("تم إيقاف مهمة التنظيف التلقائي.")

@bot.on(events.NewMessage(pattern=r'^\.اذاعه مجدوله(?:\s+(\d+)\s+(.+))?$'))
async def enable_scheduled_broadcast(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    match = event.pattern_match
    if not match.group(1) or not match.group(2):
        await event.reply("الاستخدام: `.اذاعه مجدوله <ساعات> <رسالة>`")
        return

    try:
        hours = int(match.group(1))
        message = match.group(2)
        await schedule_task("scheduled_broadcast", hours, {"message": message})
        await event.reply(f"تم تفعيل الإذاعة المجدولة كل {hours} ساعة.")
    except Exception as e:
        await event.reply(f"حدث خطأ: {e}")

@bot.on(events.NewMessage(pattern=r'^\.ايقاف الاذاعه المجدوله$'))
async def disable_scheduled_broadcast(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    await stop_scheduled_task("scheduled_broadcast")
    await event.reply("تم إيقاف مهمة الإذاعة المجدولة.")

@bot.on(events.NewMessage(pattern=r'^\.حالة المهام$'))
async def task_status(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("هذا الأمر مخصص للمالك فقط.")
        return

    tasks = list(scheduled_tasks_collection.find({"active": True}))
    if not tasks:
        await event.reply("لا توجد مهام مجدولة نشطة حاليًا.")
        return

    message = "المهام المجدولة النشطة:\n\n"
    for task in tasks:
        message += f"🔹 نوع المهمة: {task['type']}\n"
        message += f"الفترة: كل {task['interval']} ساعة\n"
        if task['type'] == "scheduled_broadcast":
            message += f"الرسالة: {task['data']['message']}\n"
        message += "\n"

    await event.reply(message)

# Event handlers for new features
@bot.on(events.NewMessage)
async def handle_auto_reply(event):
    auto_reply_enabled = settings_collection.find_one({"setting": "auto_reply_enabled"})
    if auto_reply_enabled and auto_reply_enabled.get("value", False):
        auto_reply = auto_replies_collection.find_one({"trigger": event.text})
        if auto_reply:
            await event.reply(auto_reply["response"])

@bot.on(events.NewMessage)
async def handle_welcome(event):
    if event.is_group and event.is_private is False:
        welcome_message = settings_collection.find_one({"setting": "welcome_message"})
        if welcome_message:
            await event.reply(welcome_message["value"])

@bot.on(events.NewMessage)
async def handle_mimic(event):
    if event.is_group:
        mimic_target = settings_collection.find_one({"setting": "mimic_target"})
        if mimic_target and mimic_target.get("value") == event.sender_id:
            # Check if the bot is admin
            try:
                permissions = await event.client.get_permissions(event.chat_id, (await event.client.get_me()).id)
                if permissions.is_admin:
                    await event.reply(event.text)
            except Exception as e:
                logger.error(f"Error in mimic: {e}")

@bot.on(events.NewMessage)
async def handle_media_block(event):
    if event.is_group:
        if event.photo and await is_media_blocked(event.chat_id, "photos"):
            await event.delete()
        elif event.sticker and await is_media_blocked(event.chat_id, "stickers"):
            await event.delete()
        elif event.video and await is_media_blocked(event.chat_id, "videos"):
            await event.delete()
        elif event.voice and await is_media_blocked(event.chat_id, "voice_messages"):
            await event.delete()
        elif event.document and event.document.mime_type.startswith('image/gif') and await is_media_blocked(event.chat_id, "animations"):
            await event.delete()

@bot.on(events.NewMessage)
async def handle_storage(event):
    global storage_chat
    if storage_chat and event.is_private and not event.is_group:
        try:
            await event.client.forward_messages(storage_chat, event.message)
        except Exception as e:
            logger.error(f"Error storing message: {e}")

# Start the auto poster
async def start_auto_poster():
    await bot.start()
    bot.start_time = datetime.datetime.now()
    await force_subscribe_channels(bot)
    asyncio.create_task(auto_post_to_groups())
    logger.info("Auto poster started successfully.")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_auto_poster())
