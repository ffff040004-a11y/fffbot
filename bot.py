import os, re, logging, unicodedata
from telegram import Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

FORBIDDEN = [
    # ============= SICKLEAVE =============
    "سيكليف", "س ي ك ل ي ف", "س ى ك ل ى ف", "سـيـكـلـيـف",
    "س.ي.ك.ل.ي.ف", "س-ي-ك-ل-ي-ف", "س_ي_ك_ل_ي_ف", "س•ي•ك•ل•ي•ف",
    "ســيــكــلــيــف", "صيكليف", "سيقليف", "سيكلايف", "سیکلیف",
    "sickleave", "sick leave", "sick-leave", "sick_leave", "sick.leave",
    "s i c k l e a v e", "s1ckleave", "s1ckl3ave", "5ickleave",
    "s!ckleave", "$ickleave", "SICKLEAVE", "SickLeave", "SiCkLeAvE",

    # ============= ENGLISH PROFANITY =============
    "fuck", "f u c k", "fck", "fuk", "f*ck", "f**k", "f@ck",
    "shit", "sh1t", "sh!t", "sh*t", "$hit",
    "bitch", "b1tch", "b!tch", "b*tch", "biatch",
    "ass", "a$$", "@ss",
    "damn", "dammit",

    # ============= ARABIC PROFANITY =============
    "كلب", "ك ل ب", "كـلـب",
    "حمار", "ح م ا ر", "حـمـار",
    "شرموط", "شرموطة", "ش ر م و ط",
    "غبي", "غ ب ي", "غـبـي",

    # ============= SPAM =============
    "viagra", "v1agra", "فياجرا", "فياغرا",
    "casino", "كازينو", "قمار",
    "cryptoinvestment", "crypto investment", "bitcoin profit",
    "استثمار كريبتو", "ربح بيتكوين",
    "earn money", "make money fast", "quick money", "easy money",
    "اربح المال", "فلوس سريعة", "ربح سريع",
    "porn", "p0rn", "xxx", "sex", "s3x", "سكس",
    "follow me", "follow back", "f4f", "تابعني", "فولو باك",
    "onlyfans", "only fans", "0nlyfans",

    # ============= HATE SPEECH =============
    "racist", "racism", "عنصري", "عنصرية",
    "terrorist", "إرهابي", "ارهابي",

    # ============= DRUGS =============
    "drugs", "weed", "w33d", "cocaine", "مخدرات", "حشيش",

    # ============= THREATS =============
    "kill you", "murder", "سأقتلك", "اقتلك",

    # ============= SCAM PATTERNS =============
    "click here", "click link", "اضغط هنا", "اضغط على الرابط",
    "free money", "free gift",
    "congratulations you won", "you have won",
    "مبروك لقد ربحت", "انت الفائز",

    # ============= INVESTMENT SCAMS =============
    "دخل يومي", "استثمر معي", "واتساب خاص", "تواصل خاص",
    "منصة ربح", "تسويق شبكي", "فرصة ذهبية", "ربح من الجوال",
    "عمل من البيت", "اربح", "للتواصل", "تواصل معي",
]

warns = {}
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

def normalize_text(text):
    # تحويل Unicode الخيالي لنص عادي
    try:
        normalized = unicodedata.normalize('NFKD', text)
        result = ''
        for c in normalized:
            cat = unicodedata.category(c)
            if cat not in ('Mn', 'Cf'):
                result += c
        return result.lower()
    except:
        return text.lower()

def check(text):
    # فحص النص الأصلي والمُعالج
    t1 = text.lower()
    t2 = normalize_text(text)
    # إزالة المسافات والرموز للكشف عن التمويه
    t3 = re.sub(r'[\s\.\-_•○◆▪■★☆♦|¦⋅]', '', t1)

    for w in FORBIDDEN:
        w_clean = re.sub(r'[\s\.\-_•○◆▪■★☆♦|¦⋅]', '', w.lower())
        if w.lower() in t1: return "كلمة ممنوعة: " + w
        if w.lower() in t2: return "كلمة ممنوعة: " + w
        if w_clean and w_clean in t3: return "كلمة ممنوعة: " + w

    if re.search(r"05\d{8}|\+9665\d{8}|009665\d{8}", text): return "رقم جوال"
    if re.search(r"https?://|t\.me/\+|t\.me/joinchat", text, re.I): return "رابط محظور"
    return None

def handle(update: Update, context: CallbackContext):
    msg = update.message
    user = update.effective_user
    if not msg or not user: return
    try:
        member = context.bot.get_chat_member(msg.chat_id, user.id)
        if member.status in ("administrator", "creator"): return
    except: return
    text = msg.text or msg.caption or ""
    if not text: return
    logger.info("فحص: " + text[:40])
    r = check(text)
    if r:
        try: context.bot.delete_message(msg.chat_id, msg.message_id)
        except: pass
        warns[user.id] = warns.get(user.id, 0) + 1
        w = warns[user.id]
        context.bot.send_message(
            msg.chat_id,
            "تحذير يا " + user.mention_html() + "\nالسبب: " + r + "\nالتحذيرات: " + str(w) + "/3",
            parse_mode=ParseMode.HTML
        )
        logger.info("حذف: " + r)
    else:
        logger.info("نظيفة")

updater = Updater(BOT_TOKEN)
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
updater.dispatcher.add_handler(MessageHandler(Filters.caption & ~Filters.command, handle))
logger.info("البوت يعمل")
updater.start_polling(drop_pending_updates=False, poll_interval=0.5)
updater.idle()
