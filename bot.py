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
BOT_TOKEN  = "8709874175:AAHUQdd69xyrwhQg_uWx_UDj7JOH9OClytc"
GROUP_CHAT_ID = -1001234567890          # معرف المجموعة
LOG_CHAT_ID   = -1001234567891          # معرف مجموعة السجل (اختياري)
ADMIN_IDS     = [123456789]            # معرفات الأدمن

# ═══════════════════════════════════════════
# 🚫 الكلمات الممنوعة
# ═══════════════════════════════════════════
FORBIDDEN_WORDS = [
    "خاص",
    "دخل يومي",
    "سيكليف, س ي ك ل ي ف, س ى ك ل ى ف, س   ي   ك   ل   ي   ف, سـيـكـلـيـف, س۪ي۪ك۪ل۪ي۪ف, سہيہكہلہيہف, س̲ي̲ك̲ل̲ي̲ف̲, س̀ي̀ك̀ل̀ي̀ف̀, س́ي́ك́ل́ي́ف́, س‌ي‌ك‌ل‌ي‌ف, س.ي.ك.ل.ي.ف, س،ي،ك،ل،ي،ف, س-ي-ك-ل-ي-ف, س_ي_ك_ل_ي_ف, س•ي•ك•ل•ي•ف, س○ي○ك○ل○ي○ف, س◆ي◆ك◆ل◆ي◆ف, ســيــكــلــيــف, سےكلےف, صيكليف, سيقليف, سيكلايف, سيڪليف, سیکلیف, sickleave, sick leave, sick-leave, sick_leave, sick.leave, s i c k l e a v e, s.i.c.k.l.e.a.v.e, s-i-c-k-l-e-a-v-e, s_i_c_k_l_e_a_v_e, s   i   c   k   l   e   a   v   e, s1ckleave, s1ckl3ave, s1ckl34v3, 51ckl34v3, 5ickleave, sick1eave, sickl3ave, sickle4ve, s!ckleave, s@ckleave, $ickleave, s#ckleave, s*ckleave, 𝒮𝒾𝒸𝓀𝓁𝑒𝒶𝓋𝑒, 𝓢𝓲𝓬𝓴𝓵𝓮𝓪𝓿𝓮, 𝔖𝔦𝔠𝔨𝔩𝔢𝔞𝔳𝔢, 𝕊𝕚𝕔𝕜𝕝𝕖𝕒𝕧𝕖, 𝖘𝖎𝖈𝖐𝖑𝖊𝖆𝖛𝖊, 𝗦𝗶𝗰𝗸𝗹𝗲𝗮𝘃𝗲, 𝘚𝘪𝘤𝘬𝘭𝘦𝘢𝘷𝘦, 𝙎𝙞𝙘𝙠𝙡𝙚𝙖𝙫𝙚, 𝚂𝚒𝚌𝚔𝚕𝚎𝚊𝚟𝚎, ꜱɪᴄᴋʟᴇᴀᴠᴇ, ⓢⓘⓒⓚⓛⓔⓐⓥⓔ, 🅂🅸🅲🅺🅻🅴🅰️🆅🅴, 🆂🅸🅲🅺🅻🅴🅰️🆅🅴, 𝐒𝐢𝐜𝐤𝐥𝐞𝐚𝐯𝐞, 𝐬𝐢𝐜𝐤𝐥𝐞𝐚𝐯𝐞, 𝑺𝒊𝒄𝒌𝒍𝒆𝒂𝒗𝒆, ѕι¢кℓєανє, sɪᴄᴋʟᴇᴀᴠᴇ, s|i|c|k|l|e|a|v|e, s¦i¦c¦k¦l¦e¦a¦v¦e, s⋅i⋅c⋅k⋅l⋅e⋅a⋅v⋅e, s•i•c•k•l•e•a•v•e, s○i○c○k○l○e○a○v○e, s◆i◆c◆k◆l◆e◆a◆v◆e, s▪️i▪️c▪️k▪️l▪️e▪️a▪️v▪️e, s■i■c■k■l■e■a■v■e, s★i★c★k★l★e★a★v★e, s☆i☆c☆k☆l☆e☆a☆v☆e, s♦️i♦️c♦️k♦️l♦️e♦️a♦️v♦️e, evael kcis, evaelkcis, sickleavesickleave, sickleave, sickleave, sickleave, sickleave, si‌ck‌le‌ave, si​ck​le​ave, si‍ck‍le‍ave, fuck, f u c k, f.u.c.k, f-u-c-k, f_u_c_k, fck, fuk, fuq, fvck, fu©k, fu€k, f*ck, f**k, f***, f@ck, f#ck, f$ck, shit, sh1t, sh!t, sh*t, sh@t, s h i t, s.h.i.t, $hit, $h!t, 5hit, sh¡t, bitch, b1tch, b!tch, b*tch, b@tch, bi+ch, b i t c h, b.i.t.c.h, biatch, biotch, ass, a$, a$s, @ss, @$, a s s, a.s.s, damn, d@mn, d*mn, dammit, damnit, كلب, ك ل ب, كـلـب, ڪلب, گلب, كــلــب, حمار, ح م ا ر, حـمـار, 7mar, 7maar, حــمــار, شرموط, شرموطة, ش ر م و ط, شـرمـوط, $رموط, غبي, غ ب ي, غـبـي, 8aby, ghabi, spam, sp@m, sp4m, s p a m, s.p.a.m, viagra, v1agra, v!agra, v-i-a-g-r-a, vi@gra, فياجرا, فياغرا, casino, cas1no, ca$ino, c@sino, كازينو, كازىنو, قمار, cryptoinvestment, crypto investment, bitcoin profit, btc profit, ethereum profit, استثمار كريبتو, ربح بيتكوين, earn money, make money fast, quick money, easy money, $$ guaranteed, اربح المال, فلوس سريعة, ربح سريع, porn, p0rn, pr0n, xxx, sex, s3x, سكس, سيكس, follow me, follow back, f4f, followforfollow, تابعني, فولو باك, onlyfans, only fans, 0nlyfans, onlyf@ns, racist, racism, r@cist, عنصري, عنصرية, terrorist, terror1st, إرهابي, ارهابي, drugs, drug$, weed, w33d, cocaine, coke, مخدرات, حشيش, kill you, k!ll you, murder, murd3r, سأقتلك, اقتلك, click here, click link, cl!ck here, اضغط هنا, اضغط على الرابط, free download, free money, free gift, تحميل مجاني, مجانا, congratulations you won, you have won, winner, w!nner, مبروك لقد ربحت, انت الفائز, badword, forbidden, blocked, banned, محظور, ممنوع, حظر",
    "تعال خاص",
    "# ============= SICKLEAVE VARIATIONS =============",
    "# Arabic variations",
    "\"سيكليف\",",
    "\"س ي ك ل ي ف\",",
    "\"س ى ك ل ى ف\",",
    "\"س   ي   ك   ل   ي   ف\",",
    "\"سـيـكـلـيـف\",",
    "\"س۪ي۪ك۪ل۪ي۪ف\",",
    "\"سہيہكہلہيہف\",",
    "\"س̲ي̲ك̲ل̲ي̲ف̲\",",
    "\"س̀ي̀ك̀ل̀ي̀ف̀\",",
    "\"س́ي́ك́ل́ي́ف́\",",
    "\"س‌ي‌ك‌ل‌ي‌ف\",",
    "\"س.ي.ك.ل.ي.ف\",",
    "\"س،ي،ك،ل،ي،ف\",",
    "\"س-ي-ك-ل-ي-ف\",",
    "\"س_ي_ك_ل_ي_ف\",",
    "\"س•ي•ك•ل•ي•ف\",",
    "\"س○ي○ك○ل○ي○ف\",",
    "\"س◆ي◆ك◆ل◆ي◆ف\",",
    "\"ســيــكــلــيــف\",",
    "\"سےكلےف\",",
    "\"صيكليف\",  # With wrong letters",
    "\"سيقليف\",",
    "\"سيكلايف\",",
    "\"سيڪليف\",",
    "\"سیکلیف\",  # Persian/Urdu letters",
    "# English variations - Basic",
    "\"sickleave\",",
    "\"sick leave\",",
    "\"sick-leave\",",
    "\"sick_leave\",",
    "\"sick.leave\",",
    "\"s i c k l e a v e\",",
    "\"s.i.c.k.l.e.a.v.e\",",
    "\"s-i-c-k-l-e-a-v-e\",",
    "\"s_i_c_k_l_e_a_v_e\",",
    "\"s   i   c   k   l   e   a   v   e\",",
    "# Leetspeak variations",
    "\"s1ckleave\",",
    "\"s1ckl3ave\",",
    "\"s1ckl34v3\",",
    "\"51ckl34v3\",",
    "\"5ickleave\",",
    "\"sick1eave\",",
    "\"sickl3ave\",",
    "\"sickle4ve\",",
    "\"s!ckleave\",",
    "\"s@ckleave\",",
    "\"$ickleave\",",
    "\"s#ckleave\",",
    "\"s*ckleave\",",
    "# Unicode fancy text variations",
    "\"𝒮𝒾𝒸𝓀𝓁𝑒𝒶𝓋𝑒\",",
    "\"𝓢𝓲𝓬𝓴𝓵𝓮𝓪𝓿𝓮\",",
    "\"𝔖𝔦𝔠𝔨𝔩𝔢𝔞𝔳𝔢\",",
    "\"𝕊𝕚𝕔𝕜𝕝𝕖𝕒𝕧𝕖\",",
    "\"𝖘𝖎𝖈𝖐𝖑𝖊𝖆𝖛𝖊\",",
    "\"𝗦𝗶𝗰𝗸𝗹𝗲𝗮𝘃𝗲\",",
    "\"𝘚𝘪𝘤𝘬𝘭𝘦𝘢𝘷𝘦\",",
    "\"𝙎𝙞𝙘𝙠𝙡𝙚𝙖𝙫𝙚\",",
    "\"𝚂𝚒𝚌𝚔𝚕𝚎𝚊𝚟𝚎\",",
    "\"ꜱɪᴄᴋʟᴇᴀᴠᴇ\",",
    "\"ⓈⒾⒸⓀⓁⒺⒶⓋⒺ\",",
    "\"🅂🅸🅲🅺🅻🅴🅰🆅🅴\",",
    "\"🆂🅸🅲🅺🅻🅴🅰🆅🅴\",",
    "\"𝐒𝐢𝐜𝐤𝐥𝐞𝐚𝐯𝐞\",",
    "\"𝐬𝐢𝐜𝐤𝐥𝐞𝐚𝐯𝐞\",",
    "\"𝑺𝒊𝒄𝒌𝒍𝒆𝒂𝒗𝒆\",",
    "\"ѕι¢кℓєανє\",",
    "\"Sɪᴄᴋʟᴇᴀᴠᴇ\",",
    "# With special characters",
    "\"s|i|c|k|l|e|a|v|e\",",
    "\"s¦i¦c¦k¦l¦e¦a¦v¦e\",",
    "\"s⋅i⋅c⋅k⋅l⋅e⋅a⋅v⋅e\",",
    "\"s•i•c•k•l•e•a•v•e\",",
    "\"s○i○c○k○l○e○a○v○e\",",
    "\"s◆i◆c◆k◆l◆e◆a◆v◆e\",",
    "\"s▪i▪c▪k▪l▪e▪a▪v▪e\",",
    "\"s■i■c■k■l■e■a■v■e\",",
    "\"s★i★c★k★l★e★a★v★e\",",
    "\"s☆i☆c☆k☆l☆e☆a☆v☆e\",",
    "\"s♦i♦c♦k♦l♦e♦a♦v♦e\",",
    "# Reversed and mixed",
    "\"evael kcis\",",
    "\"evaelkcis\",",
    "\"sickleavesickleave\",",
    "\"SICKLEAVE\",",
    "\"SickLeave\",",
    "\"SiCkLeAvE\",",
    "\"sIcKlEaVe\",",
    "# With invisible characters (zero-width)",
    "\"si‌ck‌le‌ave\",",
    "\"si​ck​le​ave\",",
    "\"si‍ck‍le‍ave\",",
    "# ============= ENGLISH PROFANITY =============",
    "# F-word variations",
    "\"fuck\",",
    "\"f u c k\",",
    "\"f.u.c.k\",",
    "\"f-u-c-k\",",
    "\"f_u_c_k\",",
    "\"fck\",",
    "\"fuk\",",
    "\"fuq\",",
    "\"fvck\",",
    "\"fu©k\",",
    "\"fu€k\",",
    "\"f*ck\",",
    "\"f**k\",",
    "\"f***\",",
    "\"f@ck\",",
    "\"f#ck\",",
    "\"f$ck\",",
    "# S-word variations",
    "\"shit\",",
    "\"sh1t\",",
    "\"sh!t\",",
    "\"sh*t\",",
    "\"sh@t\",",
    "\"s h i t\",",
    "\"s.h.i.t\",",
    "\"$hit\",",
    "\"$h!t\",",
    "\"5hit\",",
    "\"sh¡t\",",
    "# B-word variations",
    "\"bitch\",",
    "\"b1tch\",",
    "\"b!tch\",",
    "\"b*tch\",",
    "\"b@tch\",",
    "\"bi+ch\",",
    "\"b i t c h\",",
    "\"b.i.t.c.h\",",
    "\"biatch\",",
    "\"biotch\",",
    "# A-word variations",
    "\"ass\",",
    "\"a$\",",
    "\"a$s\",",
    "\"@ss\",",
    "\"@$\",",
    "\"a s s\",",
    "\"a.s.s\",",
    "# D-word variations",
    "\"damn\",",
    "\"d@mn\",",
    "\"d*mn\",",
    "\"dammit\",",
    "\"damnit\",",
    "# ============= ARABIC PROFANITY =============",
    "# K-word variations (Arabic)",
    "\"كلب\",",
    "\"ك ل ب\",",
    "\"كـلـب\",",
    "\"ڪلب\",",
    "\"گلب\",",
    "\"كــلــب\",",
    "# H-word variations (Arabic)",
    "\"حمار\",",
    "\"ح م ا ر\",",
    "\"حـمـار\",",
    "\"7mar\",",
    "\"7maar\",",
    "\"حــمــار\",",
    "# Sh-word variations (Arabic)",
    "\"شرموط\",",
    "\"شرموطة\",",
    "\"ش ر م و ط\",",
    "\"شـرمـوط\",",
    "\"$رموط\",",
    "# G-word variations (Arabic)",
    "\"غبي\",",
    "\"غ ب ي\",",
    "\"غـبـي\",",
    "\"8aby\",",
    "\"ghabi\",",
    "# ============= SPAM KEYWORDS =============",
    "\"spam\",",
    "\"sp@m\",",
    "\"sp4m\",",
    "\"s p a m\",",
    "\"s.p.a.m\",",
    "# Viagra/pills variations",
    "\"viagra\",",
    "\"v1agra\",",
    "\"v!agra\",",
    "\"v-i-a-g-r-a\",",
    "\"vi@gra\",",
    "\"فياجرا\",",
    "\"فياغرا\",",
    "# Casino/gambling",
    "\"casino\",",
    "\"cas1no\",",
    "\"ca$ino\",",
    "\"c@sino\",",
    "\"كازينو\",",
    "\"كازىنو\",",
    "\"قمار\",",
    "# Crypto spam",
    "\"cryptoinvestment\",",
    "\"crypto investment\",",
    "\"bitcoin profit\",",
    "\"btc profit\",",
    "\"ethereum profit\",",
    "\"استثمار كريبتو\",",
    "\"ربح بيتكوين\",",
    "# Money/financial scams",
    "\"earn money\",",
    "\"make money fast\",",
    "\"quick money\",",
    "\"easy money\",",
    "\"$$ guaranteed\",",
    "\"اربح المال\",",
    "\"فلوس سريعة\",",
    "\"ربح سريع\",",
    "# Adult content",
    "\"porn\",",
    "\"p0rn\",",
    "\"pr0n\",",
    "\"xxx\",",
    "\"sex\",",
    "\"s3x\",",
    "\"سكس\",",
    "\"سيكس\",",
    "# ============= SOCIAL MEDIA SPAM =============",
    "\"follow me\",",
    "\"follow back\",",
    "\"f4f\",",
    "\"followforfollow\",",
    "\"تابعني\",",
    "\"فولو باك\",",
    "# OnlyFans variations",
    "\"onlyfans\",",
    "\"only fans\",",
    "\"0nlyfans\",",
    "\"onlyf@ns\",",
    "# ============= HATE SPEECH =============",
    "\"racist\",",
    "\"racism\",",
    "\"r@cist\",",
    "\"عنصري\",",
    "\"عنصرية\",",
    "\"terrorist\",",
    "\"terror1st\",",
    "\"إرهابي\",",
    "\"ارهابي\",",
    "# ============= DRUGS =============",
    "\"drugs\",",
    "\"drug$\",",
    "\"weed\",",
    "\"w33d\",",
    "\"cocaine\",",
    "\"coke\",",
    "\"مخدرات\",",
    "\"حشيش\",",
    "# ============= THREATS =============",
    "\"kill you\",",
    "\"k!ll you\",",
    "\"murder\",",
    "\"murd3r\",",
    "\"سأقتلك\",",
    "\"اقتلك\",",
    "# ============= SCAM PATTERNS =============",
    "\"click here\",",
    "\"click link\",",
    "\"cl!ck here\",",
    "\"اضغط هنا\",",
    "\"اضغط على الرابط\",",
    "\"free download\",",
    "\"free money\",",
    "\"free gift\",",
    "\"تحميل مجاني\",",
    "\"مجانا\",",
    "\"congratulations you won\",",
    "\"you have won\",",
    "\"winner\",",
    "\"w!nner\",",
    "\"مبروك لقد ربحت\",",
    "\"انت الفائز\",",
    "# ============= CUSTOM ADDITIONS =============",
    "# Add any specific words for your community",
    "\"badword\",",
    "\"forbidden\",",
    "\"blocked\",",
    "\"banned\",",
    "\"محظور\",",
    "\"ممنوع\",",
    "\"حظر\",",
    "# Spam numbers",
    "\"12345\",",
    "\"123456\",",
    "\"1234567\",",
    "\"99999\",",
    "\"00000\",",
    "\"11111\",",
    "\"420\",",
    "\"69\",",
    "\"666\",",
    "\"6969\",",
    "\"420420\",",
    "# Common spam phone prefixes (add your own)",
    "\"900\",  # Premium numbers",
    "\"0900\",",
    "\"+234\",  # Nigerian scam prefix"
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
