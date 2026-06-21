#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, ChatPermissions, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

FORBIDDEN_WORDS = [
    "تواصل معي خاص",
    "دخل يومي",
    "استثمر معي",
    "ربح من الجوال",
    "تسويق شبكي",
    "فرصة ذهبية",
    "واتساب خاص",
    "تواصل خاص",
    "منصة ربح",
    "استثمار مضمون",
    "عمل من البيت",
    "كسب سريع",
    "اربح",
    "للتواصل",
    "تواصل معي",
]

PROMO_PATTERNS = [
    "دخل يومي",
    "استثمر مع",
    "تسويق شبكي",
    "ربح من الجوال",
    "فرصة ذهبية",
    "عمل من البيت",
    "منصة ربح",
    "تواصل معي خاص",
    "واتساب خاص",
    "للتواصل واتس",
    "profit",
    "earn money",
    "invest with",
]

PHONE_PATTERNS = [
    r"05\d{8}",
    r"\+9665\d{8}",
    r"009665\d{8}",
]

BLOCKED_LINKS = [
    r"https?://",
    r"t\.me/joinchat",
    r"t\.me/\+",
    r"bit\.ly/",
]

WHITELIST = [
    "drive.google.com",
    "forms.gle",
    "classroom.google.com",
    "docs.google.com",
]

RATE_LIMIT = 5
MUTE_MINUTES = 30
MAX_WARNINGS = 3

user_warnings = defaultdict(int)
user_msg_times = defaultdict(list)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

def normalize(text):
    ar = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
    for i, c in enumerate(ar):
        text = text.replace(c, str(i))
    return text

def check_forbidden(text):
    t = text.lower()
    for w in FORBIDDEN_WORDS:
        if w.lower() in t:
            return "كلمة ممنوعة: " + w
    return None

def check_promo(text):
    t = text.lower()
    for p in PROMO_PATTERNS:
        if p.lower() in t:
            return "رسالة ترويجية: " + p
    return None

def check_phone(text):
    t = normalize(text)
    for p in PHONE_PATTERNS:
        if re.search(p, t):
            return "رقم جوال"
    return None

def check_links(text):
    for w in WHITELIST:
        if w in text:
            return None
    for p in BLOCKED_LINKS:
        if re.search(p, text, re.IGNORECASE):
            return "رابط محظور"
    return None

def check_rate(user_id):
    now = time.time()
    user_msg_times[user_id] = [t for t in user_msg_times[user_id] if now - t < 60]
    user_msg_times[user_id].append(now)
    return len(user_msg_times[user_id]) > RATE_LIMIT

async def delete_msg(update, context):
    try:
        await context.bot.delete_message(
            update.effective_chat.id,
            update.message.message_id
        )
        logger.info("✅ تم حذف رسالة")
    except Exception as e:
        logger.error("❌ خطأ حذف: " + str(e))

async def send_temp(context, chat_id, text, seconds=25):
    try:
        msg = await context.bot.send_message(
            chat_id, text, parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(seconds)
        await context.bot.delete_message(chat_id, msg.message_id)
    except Exception as e:
        logger.error("خطأ send_temp: " + str(e))

async def warn_user(update, context, reason):
    user = update.effective_user
    user_warnings[user.id] += 1
    w = user_warnings[user.id]
    if w >= MAX_WARNINGS:
        await ban_user(update, context, "تجاوز الحد الأقصى للتحذيرات")
        return
    text = (
        "⚠️ تحذير يا " + user.mention_html() + "\n"
        "السبب: <b>" + reason + "</b>\n"
        "التحذيرات: <b>" + str(w) + "/" + str(MAX_WARNINGS) + "</b>"
    )
    asyncio.create_task(send_temp(context, update.effective_chat.id, text))
    logger.info("⚠️ تحذير | " + user.full_name + " | " + reason)

async def mute_user(update, context, reason, minutes=MUTE_MINUTES):
    user = update.effective_user
    try:
        until = datetime.now() + timedelta(minutes=minutes)
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        text = "🔇 تم كتم " + user.mention_html() + " لمدة " + str(minutes) + " دقيقة\nالسبب: " + reason
        asyncio.create_task(send_temp(context, update.effective_chat.id, text))
        logger.info("🔇 كتم | " + user.full_name + " | " + reason)
    except Exception as e:
        logger.error("❌ خطأ كتم: " + str(e))

async def ban_user(update, context, reason):
    user = update.effective_user
    try:
        await context.bot.ban_chat_member(
            update.effective_chat.id, user.id
        )
        text = "🚫 تم حظر " + user.mention_html() + "\nالسبب: " + reason
        asyncio.create_task(send_temp(context, update.effective_chat.id, text))
        user_warnings.pop(user.id, None)
        logger.info("🚫 حظر | " + user.full_name + " | " + reason)
    except Exception as e:
        logger.error("❌ خطأ حظر: " + str(e))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = update.effective_user

    if not msg or not user:
        return

    # تسجيل كل رسالة واردة
    logger.info("📨 رسالة من: " + str(user.id) + " | " + str(user.full_name))

    # تجاهل المشرفين فقط
    try:
        member = await context.bot.get_chat_member(msg.chat_id, user.id)
        if member.status in ("administrator", "creator"):
            logger.info("👑 تجاهل مشرف/مالك: " + user.full_name)
            return
    except Exception as e:
        logger.error("❌ خطأ التحقق من الصلاحيات: " + str(e))
        return

    text = msg.text or msg.caption or ""
    if not text:
        logger.info("📷 رسالة بدون نص - تجاهل")
        return

    logger.info("🔍 فحص: " + text[:50])

    # 1. كلمات ممنوعة
    r = check_forbidden(text)
    if r:
        logger.info("🚨 " + r)
        await delete_msg(update, context)
        await warn_user(update, context, r)
        return

    # 2. ترويج واستثمار
    r = check_promo(text)
    if r:
        logger.info("🚨 " + r)
        await delete_msg(update, context)
        await ban_user(update, context, r)
        return

    # 3. أرقام جوالات
    r = check_phone(text)
    if r:
        logger.info("🚨 " + r)
        await delete_msg(update, context)
        await mute_user(update, context, r)
        return

    # 4. روابط
    r = check_links(text)
    if r:
        logger.info("🚨 " + r)
        await delete_msg(update, context)
        await warn_user(update, context, r)
        return

    # 5. سبام
    if check_rate(user.id):
        logger.info("🚨 سبام: " + user.full_name)
        await delete_msg(update, context)
        await mute_user(update, context, "رسائل متكررة", 10)
        return

    logger.info("✅ رسالة نظيفة")

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج لجميع أنواع التحديثات للتشخيص"""
    logger.info("📬 تحديث: " + str(update.update_id))

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ البوت يعمل\n/status للحالة")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ البوت يعمل\n"
        "محذورون: " + str(len(user_warnings)) + "\n"
        "كلمات: " + str(len(FORBIDDEN_WORDS))
    )

async def cmd_addword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id, update.effective_user.id
        )
        if member.status not in ("administrator", "creator"):
            return
    except:
        return
    if not context.args:
        return
    word = " ".join(context.args)
    FORBIDDEN_WORDS.append(word)
    await update.message.reply_text("✅ تمت الاضافة: " + word)

async def post_init(application):
    """بعد تشغيل البوت - إرسال رسالة تأكيد"""
    bot = application.bot
    info = await bot.get_me()
    logger.info("🤖 البوت: @" + info.username)
    # طباعة الـ updates المعلقة
    updates = await bot.get_updates(limit=10)
    logger.info("📬 Updates معلقة: " + str(len(updates)))

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير موجود")
        return

    logger.info("🚀 تشغيل البوت...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("addword", cmd_addword))

    # معالج لجميع الرسائل النصية
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    # معالج للرسائل مع كابشن (صور/فيديو)
    app.add_handler(MessageHandler(
        filters.CAPTION & ~filters.COMMAND,
        handle_message
    ))

    logger.info("✅ البوت يعمل الآن")

    # تشغيل بدون حذف الرسائل المعلقة
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
        poll_interval=0.5,
        timeout=10,
        read_timeout=10,
        write_timeout=10,
        connect_timeout=10,
    )

if __name__ == "__main__":
    main()
