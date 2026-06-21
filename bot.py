#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════╗
║     بوت الحماية المتكامل - تصميم د/فواز         ║
║     Telegram Group Protection Bot               ║
╚══════════════════════════════════════════════════╝
المتطلبات:
    pip install python-telegram-bot==20.7
    pip install python-dotenv

التشغيل:
    python bot.py
"""

import re
import json
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    filters, ContextTypes
)
from telegram.constants import ParseMode

# ═══════════════════════════════════════════
# ⚙️ الإعدادات
# ═══════════════════════════════════════════
BOT_TOKEN  = "ضع_توكن_البوت_هنا"
GROUP_CHAT_ID = -1001234567890          # معرف المجموعة
LOG_CHAT_ID   = -1001234567891          # معرف مجموعة السجل (اختياري)
ADMIN_IDS     = [123456789]            # معرفات الأدمن

# ═══════════════════════════════════════════
# 🚫 الكلمات الممنوعة
# ═══════════════════════════════════════════
FORBIDDEN_WORDS = [
    # أضف كلماتك هنا - ستُحدَّث تلقائياً من المنصة
    "تواصل معي خاص",
    "دخل يومي",
    "استثمر معي",
    "ربح من الجوال",
    "تسويق شبكي",
    "فرصة ذهبية",
]

# قائمة عبارات الترويج والاستثمار
PROMO_PHRASES = [
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
]

# ═══════════════════════════════════════════
# 📱 أنماط أرقام الجوالات
# ═══════════════════════════════════════════
PHONE_PATTERNS = [
    r'(? str:
    """تحويل الأرقام العربية والفارسية إلى غربية"""
    arabic  = '٠١٢٣٤٥٦٧٨٩'
    persian = '۰۱۲۳۴۵۶۷۸۹'
    for i, (a, p) in enumerate(zip(arabic, persian)):
        text = text.replace(a, str(i)).replace(p, str(i))
    return text

def check_forbidden_words(text: str) -> str | None:
    """فحص الكلمات الممنوعة"""
    text_lower = text.lower()
    for word in FORBIDDEN_WORDS:
        if word.lower() in text_lower:
            return f"كلمة ممنوعة: {word}"
    return None

def check_promo(text: str) -> str | None:
    """كشف رسائل الترويج والاستثمار"""
    for pattern in PROMO_PHRASES:
        if re.search(pattern, text, re.IGNORECASE):
            return "رسالة ترويجية أو استثمارية"
    return None

def check_phone(text: str) -> str | None:
    """كشف أرقام الجوالات"""
    converted = arabic_to_western(text)
    for pattern in PHONE_PATTERNS:
        if re.search(pattern, converted):
            return "رقم جوال"
    return None

def check_links(text: str) -> str | None:
    """كشف الروابط غير المسموح بها"""
    for domain in WHITELIST_DOMAINS:
        if domain in text:
            return None
    for pattern in BLOCKED_LINK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "رابط أو إعلان"
    return None

def check_rate_limit(user_id: int) -> bool:
    """فحص معدل الرسائل"""
    now = time.time()
    user_msg_times[user_id] = [
        t for t in user_msg_times[user_id]
        if now - t < 60
    ]
    user_msg_times[user_id].append(now)
    return len(user_msg_times[user_id]) > RATE_LIMIT_MSGS

# ═══════════════════════════════════════════
# ⚡ دوال الإجراء
# ═══════════════════════════════════════════

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logger.error(f"خطأ في حذف الرسالة: {e}")

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    reason: str):
    user = update.effective_user
    user_warnings[user.id] += 1
    warns = user_warnings[user.id]

    if warns >= MAX_WARNINGS:
        await ban_user(update, context, "تجاوز الحد الأقصى للتحذيرات")
        return

    msg = (
        f"⚠️ تحذير يا {user.mention_html()}!\n"
        f"رسالتك تخالف قواعد المجموعة وتمت إزالتها.\n"
        f"السبب: {reason}\n"
        f"عدد التحذيرات: {warns}/{MAX_WARNINGS}\n"
        f"بعد {MAX_WARNINGS} تحذيرات سيتم حظرك تلقائياً."
    )
    sent = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg, parse_mode=ParseMode.HTML
    )
    # حذف التحذير بعد 30 ثانية
    context.job_queue.run_once(
        lambda ctx: ctx.bot.delete_message(
            update.effective_chat.id, sent.message_id
        ),
        when=30
    )

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    reason: str, minutes: int = MUTE_MINUTES):
    user = update.effective_user
    try:
        until = datetime.now() + timedelta(minutes=minutes)
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
            until_date=until
        )
        msg = (
            f"🔇 تم كتم {user.mention_html()} لمدة {minutes} دقيقة.\n"
            f"السبب: {reason}"
        )
        await context.bot.send_message(
            update.effective_chat.id,
            msg, parse_mode=ParseMode.HTML
        )
        await log_action(context, f"كتم | {user.full_name} | {reason}")
    except Exception as e:
        logger.error(f"خطأ في كتم المستخدم: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE,
                   reason: str):
    user = update.effective_user
    try:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id
        )
        msg = (
            f"🚫 تم حظر {user.mention_html()}\n"
            f"السبب: {reason}"
        )
        await context.bot.send_message(
            update.effective_chat.id,
            msg, parse_mode=ParseMode.HTML
        )
        user_warnings.pop(user.id, None)
        await log_action(context, f"حظر | {user.full_name} | {reason}")
    except Exception as e:
        logger.error(f"خطأ في حظر المستخدم: {e}")

async def log_action(context: ContextTypes.DEFAULT_TYPE, action: str):
    if LOG_CHAT_ID:
        try:
            await context.bot.send_message(
                LOG_CHAT_ID,
                f"🛡️ سجل الحماية\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"📋 {action}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

# ═══════════════════════════════════════════
# 🎯 المعالج الرئيسي للرسائل
# ═══════════════════════════════════════════

async def handle_message(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):
    msg  = update.message
    user = update.effective_user
    if not msg or not user: return

    # تجاهل المشرفين
    chat_member = await context.bot.get_chat_member(
        msg.chat_id, user.id
    )
    if chat_member.status in ('administrator', 'creator'):
        return

    text = msg.text or msg.caption or ""

    # ──────────────────────────────────────
    # 1. فحص الكلمات الممنوعة
    reason = check_forbidden_words(text)
    if reason:
        await delete_message(update, context)
        await warn_user(update, context, reason)
        return

    # 2. فحص رسائل الترويج والاستثمار
    reason = check_promo(text)
    if reason:
        await delete_message(update, context)
        await ban_user(update, context, reason)
        return

    # 3. فحص أرقام الجوالات
    reason = check_phone(text)
    if reason:
        await delete_message(update, context)
        await mute_user(update, context, reason)
        return

    # 4. فحص الروابط
    reason = check_links(text)
    if reason:
        await delete_message(update, context)
        await warn_user(update, context, reason)
        return

    # 5. فحص معدل الرسائل (سبام)
    if check_rate_limit(user.id):
        await delete_message(update, context)
        await mute_user(update, context, "رسائل متكررة - سبام", 10)
        return

    # 6. تقييد المستخدمين الجدد
    if msg.from_user.date:
        days = (datetime.now() - msg.from_user.date.replace(tzinfo=None)).days
        if days < NEW_USER_DAYS and msg.forward_origin:
            await delete_message(update, context)
            await warn_user(update, context, "مستخدم جديد - تحويل رسائل ممنوع")
            return

# ═══════════════════════════════════════════
# 🤖 الأوامر
# ═══════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ بوت الحماية المتكامل\n"
        "تصميم: د/فواز\n\n"
        "الأوامر:\n"
        "/status - حالة البوت\n"
        "/warns @user - عرض تحذيرات مستخدم\n"
        "/resetwarn @user - إعادة ضبط تحذيرات\n"
        "/addword كلمة - إضافة كلمة ممنوعة\n",
        parse_mode=ParseMode.HTML
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_warned = len(user_warnings)
    await update.message.reply_text(
        f"🛡️ حالة البوت\n"
        f"✅ يعمل بشكل طبيعي\n"
        f"👥 مستخدمون لديهم تحذيرات: {total_warned}\n"
        f"🚫 كلمات ممنوعة: {len(FORBIDDEN_WORDS)}",
        parse_mode=ParseMode.HTML
    )

async def cmd_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("الاستخدام: /warns @username")
        return
    # لتبسيط: تحتاج تحديد user_id من الاسم
    await update.message.reply_text("⚙️ الأمر قيد التطوير")

async def cmd_addword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة كلمة ممنوعة من المشرف"""
    if not context.args: return
    user = update.effective_user
    chat_member = await context.bot.get_chat_member(
        update.effective_chat.id, user.id
    )
    if chat_member.status not in ('administrator', 'creator'):
        return
    word = " ".join(context.args)
    FORBIDDEN_WORDS.append(word)
    await update.message.reply_text(f"✅ تمت إضافة الكلمة: {word}")

# ═══════════════════════════════════════════
# 🚀 تشغيل البوت
# ═══════════════════════════════════════════

def main():
    logger.info("🛡️ جاري تشغيل بوت الحماية...")
    app = Application.builder().token(BOT_TOKEN).build()

    # المعالجات
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("warns",     cmd_warns))
    app.add_handler(CommandHandler("addword",   cmd_addword))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))
    app.add_handler(MessageHandler(
        filters.CAPTION & ~filters.COMMAND,
        handle_message
    ))

    logger.info("✅ البوت يعمل الآن!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
