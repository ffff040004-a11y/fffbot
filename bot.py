#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════╗
║     بوت الحماية المتكامل - تصميم د/فواز         ║
║     نظام Webhook عبر GitHub Actions             ║
╚══════════════════════════════════════════════════╝
"""

import os
import re
import time
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    filters, ContextTypes
)
from telegram.constants import ParseMode

# ═══════════════════════════════════════════
# ⚙️ الإعدادات من GitHub Secrets
# ═══════════════════════════════════════════
BOT_TOKEN     = os.environ.get("BOT_TOKEN", "")
GROUP_CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
LOG_CHAT_ID   = int(os.environ.get("LOG_CHAT_ID", "0")) if os.environ.get("LOG_CHAT_ID") else None
ADMIN_IDS     = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

# ═══════════════════════════════════════════
# 🚫 الكلمات الممنوعة
# ═══════════════════════════════════════════
FORBIDDEN_WORDS = [
    "تواصل معي خاص",
    "دخل يومي",
    "استثمر معي",
    "ربح من الجوال",
    "تسويق شبكي",
    "فرصة ذهبية",
    "واتساب خاص",
    "تواصل خاص",
    "اربح",
    "منصة ربح",
    "استثمار مضمون",
    "عمل من البيت",
    "كسب سريع",
]

# ═══════════════════════════════════════════
# 💰 عبارات الترويج والاستثمار
# ═══════════════════════════════════════════
PROMO_PATTERNS = [
    r"دخل\s*يومي",
    r"استثمر?\s*مع",
    r"تسويق\s*شبكي",
    r"ربح\s*من\s*الجوال",
    r"فرصة?\s*(ذهبية|استثمارية|عمل)",
    r"عمل\s*من\s*البيت",
    r"اربح?\s*\d+\s*(ريال|دولار|درهم)",
    r"منصة?\s*(ربح|استثمار)",
    r"بروفت|profit|earn\s*money",
    r"تواصل\s*(معي|معنا|خاص)",
    r"واتساب\s*خاص",
    r"للتواصل\s*واتس",
    r"ادفع\s*و\s*اربح",
]

# ═══════════════════════════════════════════
# 📱 أنماط أرقام الجوالات
# ═══════════════════════════════════════════
PHONE_PATTERNS = [
    r'(?<!\d)05\d[\s\-.]?\d{3}[\s\-.]?\d{4}(?!\d)',
    r'(?<!\d)\+?966\s*5\d[\s\-.]?\d{3}[\s\-.]?\d{4}(?!\d)',
    r'(?<!\d)009665\d{8}(?!\d)',
    r'(?<!\d)٠٥[\d٠-٩\s\-.]{8,12}(?!\d)',
    r'(?<!\d)(\d[\s\-._,]{1,3}){8,10}\d(?!\d)',
]

# ═══════════════════════════════════════════
# 🔗 أنماط الروابط المحظورة
# ═══════════════════════════════════════════
BLOCKED_LINK_PATTERNS = [
    r'https?://[^\s]+',
    r't\.me/[^\s]+',
    r'bit\.ly/[^\s]+',
    r'youtu\.be/[^\s]+',
]

WHITELIST_DOMAINS = [
    'drive.google.com',
    'forms.gle',
    'classroom.google.com',
    'docs.google.com',
]

# ═══════════════════════════════════════════
# ⚙️ إعدادات السبام
# ═══════════════════════════════════════════
RATE_LIMIT   = 5    # رسائل في الدقيقة
MUTE_MINUTES = 30
MAX_WARNINGS = 3
NEW_USER_DAYS = 3

# ═══════════════════════════════════════════
# 📦 الذاكرة
# ═══════════════════════════════════════════
user_warnings  = defaultdict(int)
user_msg_times = defaultdict(list)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# 🛡️ دوال الكشف
# ═══════════════════════════════════════════

def normalize(text: str) -> str:
    ar = '٠١٢٣٤٥٦٧٨٩'
    fa = '۰۱۲۳۴۵۶۷۸۹'
    for i, (a, f) in enumerate(zip(ar, fa)):
        text = text.replace(a, str(i)).replace(f, str(i))
    return text

def check_forbidden(text: str):
    t = text.lower()
    for w in FORBIDDEN_WORDS:
        if w.lower() in t:
            return f"كلمة ممنوعة: {w}"
    return None

def check_promo(text: str):
    for p in PROMO_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return "رسالة ترويجية أو استثمارية"
    return None

def check_phone(text: str):
    t = normalize(text)
    for p in PHONE_PATTERNS:
        if re.search(p, t):
            return "رقم جوال"
    return None

def check_links(text: str):
    for d in WHITELIST_DOMAINS:
        if d in text:
            return None
    for p in BLOCKED_LINK_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return "رابط أو إعلان"
    return None

def check_rate(user_id: int) -> bool:
    now = time.time()
    user_msg_times[user_id] = [t for t in user_msg_times[user_id] if now - t < 60]
    user_msg_times[user_id].append(now)
    return len(user_msg_times[user_id]) > RATE_LIMIT

# ═══════════════════════════════════════════
# ⚡ دوال الإجراء
# ═══════════════════════════════════════════

async def delete_msg(update, context):
    try:
        await context.bot.delete_message(
            update.effective_chat.id,
            update.message.message_id
        )
    except Exception as e:
        logger.error(f"حذف: {e}")

async def send_temp(context, chat_id, text, seconds=30):
    """إرسال رسالة مؤقتة تُحذف تلقائياً"""
    try:
        msg = await context.bot.send_message(
            chat_id, text, parse_mode=ParseMode.HTML
        )
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
        f"⚠️ <b>تحذير</b> يا {user.mention_html()}!\n"
        f"رسالتك تخالف قواعد المجموعة.\n"
        f"السبب: <b>{reason}</b>\n"
        f"التحذيرات: <b>{w}/{MAX_WARNINGS}</b>"
    )
    asyncio.create_task(send_temp(context, update.effective_chat.id, text))
    await log_action(context, f"⚠️ تحذير | {user.full_name} | {reason}")

async def mute_user(update, context, reason, minutes=MUTE_MINUTES):
    user = update.effective_user
    try:
        until = datetime.now() + timedelta(minutes=minutes)
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        text = (
            f"🔇 <b>كتم</b> {user.mention_html()} لمدة {minutes} دقيقة\n"
            f"السبب: <b>{reason}</b>"
        )
        asyncio.create_task(send_temp(context, update.effective_chat.id, text))
        await log_action(context, f"🔇 كتم | {user.full_name} | {reason}")
    except Exception as e:
        logger.error(f"كتم: {e}")

async def ban_user(update, context, reason):
    user = update.effective_user
    try:
        await context.bot.ban_chat_member(
            update.effective_chat.id, user.id
        )
        text = (
            f"🚫 <b>حظر</b> {user.mention_html()}\n"
            f"السبب: <b>{reason}</b>"
        )
        asyncio.create_task(send_temp(context, update.effective_chat.id, text))
        user_warnings.pop(user.id, None)
        await log_action(context, f"🚫 حظر | {user.full_name} | {reason}")
    except Exception as e:
        logger.error(f"حظر: {e}")

async def log_action(context, action):
    if LOG_CHAT_ID:
        try:
            await context.bot.send_message(
                LOG_CHAT_ID,
                f"🛡️ <b>سجل الحماية</b>\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"📋 {action}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

# ═══════════════════════════════════════════
# 🎯 المعالج الرئيسي
# ═══════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg  = update.message
    user = update.effective_user
    if not msg or not user: return

    # تجاهل المشرفين
    try:
        member = await context.bot.get_chat_member(msg.chat_id, user.id)
        if member.status in ('administrator', 'creator'): return
    except:
        return

    text = msg.text or msg.caption or ""
    if not text: return

    # 1. كلمات ممنوعة
    r = check_forbidden(text)
    if r:
        await delete_msg(update, context)
        await warn_user(update, context, r)
        return

    # 2. ترويج واستثمار → حظر فوري
    r = check_promo(text)
    if r:
        await delete_msg(update, context)
        await ban_user(update, context, r)
        return

    # 3. أرقام جوالات → كتم
    r = check_phone(text)
    if r:
        await delete_msg(update, context)
        await mute_user(update, context, r)
        return

    # 4. روابط → تحذير
    r = check_links(text)
    if r:
        await delete_msg(update, context)
        await warn_user(update, context, r)
        return

    # 5. سبام (رسائل متكررة) → كتم 10 دقائق
    if check_rate(user.id):
        await delete_msg(update, context)
        await mute_user(update, context, "رسائل متكررة", 10)
        return

    # 6. مستخدم جديد يرسل forward
    if msg.forward_origin:
        try:
            joined = member.user.date
            if joined and (datetime.now(joined.tzinfo) - joined).days < NEW_USER_DAYS:
                await delete_msg(update, context)
                await warn_user(update, context, "مستخدم جديد - تحويل رسائل ممنوع")
        except:
            pass

# ═══════════════════════════════════════════
# 🤖 الأوامر
# ═══════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ <b>بوت الحماية المتكامل</b>\n"
        "تصميم: د/فواز\n\n"
        "/status - حالة البوت\n"
        "/addword كلمة - إضافة كلمة ممنوعة\n"
        "/warns - عدد المحذورين\n"
        "/help - المساعدة",
        parse_mode=ParseMode.HTML
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🛡️ <b>حالة البوت</b>\n"
        f"✅ يعمل بشكل طبيعي\n"
        f"👥 محذورون: {len(user_warnings)}\n"
        f"🚫 كلمات: {len(FORBIDDEN_WORDS)}\n"
        f"⏰ {datetime.now().strftime('%H:%M')}",
        parse_mode=ParseMode.HTML
    )

async def cmd_addword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id, update.effective_user.id
        )
        if member.status not in ('administrator', 'creator'):
            return
    except:
        return
    if not context.args: return
    word = " ".join(context.args)
    FORBIDDEN_WORDS.append(word)
    await update.message.reply_text(f"✅ تمت إضافة: {word}")

async def cmd_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 إجمالي المستخدمين لديهم تحذيرات: {len(user_warnings)}"
    )

# ═══════════════════════════════════════════
# 🚀 التشغيل
# ═══════════════════════════════════════════

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير موجود!")
        return

    logger.info("🛡️ جاري تشغيل بوت الحماية...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("addword", cmd_addword))
    app.add_handler(CommandHandler("warns",   cmd_warns))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message
    ))
    app.add_handler(MessageHandler(
        filters.CAPTION & ~filters.COMMAND, handle_message
    ))

    logger.info("✅ البوت يعمل الآن - Polling mode")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=30
    )

if __name__ == "__main__":
    main()
