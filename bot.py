#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN     = os.environ.get("BOT_TOKEN", "")
GROUP_CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
LOG_CHAT_ID   = int(os.environ.get("LOG_CHAT_ID", "0")) if os.environ.get("LOG_CHAT_ID") else None

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
    "ادفع واربح",
    "profit",
    "earn money",
]

PHONE_PATTERNS = [
    r"05\d{8}",
    r"\+9665\d{8}",
    r"009665\d{8}",
]

BLOCKED_LINKS = [
    r"https?://",
    r"t\.me/",
    r"bit\.ly/",
    r"youtu\.be/",
]

WHITELIST = [
    "drive.google.com",
    "forms.gle",
    "classroom.google.com",
    "docs.google.com",
]

RATE_LIMIT   = 5
MUTE_MINUTES = 30
MAX_WARNINGS = 3

user_warnings  = defaultdict(int)
user_msg_times = defaultdict(list)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
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
            return "رسالة ترويجية"
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
        await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
    except Exception as e:
        logger.error("حذف: " + str(e))

async def send_temp(context, chat_id, text, seconds=30):
    try:
        msg = await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(seconds)
        await context.bot.delete_message(chat_id, msg.message_id)
    except:
        pass

async def warn_user(update, context, reason):
    user = update.effective_user
    user_warnings[user.id] += 1
    w = user_warnings[user.id]
    if w >= MAX_WARNINGS:
        await ban_user(update, context, "تجاوز الحد الأقصى للتحذيرات")
        return
    text = (
        "<b>تحذير</b> يا " + user.mention_html() + "\n"
        "رسالتك تخالف قواعد المجموعة\n"
        "السبب: <b>" + reason + "</b>\n"
        "التحذيرات: <b>" + str(w) + "/" + str(MAX_WARNINGS) + "</b>"
    )
    asyncio.create_task(send_temp(context, update.effective_chat.id, text))
    logger.info("تحذير | " + user.full_name + " | " + reason)

async def mute_user(update, context, reason, minutes=MUTE_MINUTES):
    user = update.effective_user
    try:
        until = datetime.now() + timedelta(minutes=minutes)
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        text = "تم كتم " + user.mention_html() + " لمدة " + str(minutes) + " دقيقة\nالسبب: " + reason
        asyncio.create_task(send_temp(context, update.effective_chat.id, text))
        logger.info("كتم | " + user.full_name + " | " + reason)
    except Exception as e:
        logger.error("كتم: " + str(e))

async def ban_user(update, context, reason):
    user = update.effective_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        text = "تم حظر " + user.mention_html() + "\nالسبب: " + reason
        asyncio.create_task(send_temp(context, update.effective_chat.id, text))
        user_warnings.pop(user.id, None)
        logger.info("حظر | " + user.full_name + " | " + reason)
    except Exception as e:
        logger.error("حظر: " + str(e))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg  = update.message
    user = update.effective_user
    if not msg or not user:
        return
    try:
        member = await context.bot.get_chat_member(msg.chat_id, user.id)
        if member.status in ("administrator", "creator"):
            return
    except:
        return
    text = msg.text or msg.caption or ""
    if not text:
        return

    r = check_forbidden(text)
    if r:
        await delete_msg(update, context)
        await warn_user(update, context, r)
        return

    r = check_promo(text)
    if r:
        await delete_msg(update, context)
        await ban_user(update, context, r)
        return

    r = check_phone(text)
    if r:
        await delete_msg(update, context)
        await mute_user(update, context, r)
        return

    r = check_links(text)
    if r:
        await delete_msg(update, context)
        await warn_user(update, context, r)
        return

    if check_rate(user.id):
        await delete_msg(update, context)
        await mute_user(update, context, "رسائل متكررة", 10)
        return

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "البوت يعمل\n/status - الحالة\n/addword كلمة - اضافة كلمة",
        parse_mode=ParseMode.HTML
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "البوت يعمل\nمحذورون: " + str(len(user_warnings)) + "\nكلمات: " + str(len(FORBIDDEN_WORDS))
    )

async def cmd_addword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        if member.status not in ("administrator", "creator"):
            return
    except:
        return
    if not context.args:
        return
    word = " ".join(context.args)
    FORBIDDEN_WORDS.append(word)
    await update.message.reply_text("تمت الاضافة: " + word)

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN غير موجود")
        return
    logger.info("تشغيل البوت...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("addword", cmd_addword))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_message))
    logger.info("البوت يعمل الآن")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True, poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    main()
