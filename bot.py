import os
import logging
import sqlite3
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from openai import AsyncOpenAI


# ============================================================
# SOZLAMALAR
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = os.getenv("ADMIN_ID", "0")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    ADMIN_ID = 0

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

DATABASE = "school.db"


# ============================================================
# LOG
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# OPENAI
# ============================================================

ai_client = None

if OPENAI_API_KEY:
    ai_client = AsyncOpenAI(
        api_key=OPENAI_API_KEY
    )


# ============================================================
# DATABASE
# ============================================================

def database():

    return sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )


def create_database():

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade TEXT NOT NULL,
            day TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            subject TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade TEXT NOT NULL,
            subject TEXT NOT NULL,
            task TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# ADMIN
# ============================================================

def is_admin(user_id):

    return (
        ADMIN_ID != 0
        and user_id == ADMIN_ID
    )


# ============================================================
# ASOSIY MENYU
# ============================================================

def main_keyboard():

    return ReplyKeyboardMarkup(
        [
            ["📚 Dars jadvali", "📝 Uyga vazifa"],
            ["📢 E'lonlar", "🎉 Tadbirlar"],
            ["🤖 AI yordamchi", "ℹ️ Yordam"],
        ],
        resize_keyboard=True
    )


def admin_keyboard():

    return ReplyKeyboardMarkup(
        [
            ["📚 Dars jadvali", "📝 Uyga vazifa"],
            ["📢 E'lonlar", "🎉 Tadbirlar"],
            ["🤖 AI yordamchi", "⚙️ Admin"],
            ["ℹ️ Yordam"],
        ],
        resize_keyboard=True
    )


def back_keyboard():

    return ReplyKeyboardMarkup(
        [
            ["⬅️ Orqaga"]
        ],
        resize_keyboard=True
    )


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    user = update.effective_user

    if is_admin(user.id):
        keyboard = admin_keyboard()
    else:
        keyboard = main_keyboard()

    await update.message.reply_text(
        f"🏫 <b>Maktab 57 botiga xush kelibsiz!</b>\n\n"
        f"👤 Salom, {user.first_name}!\n\n"
        f"Kerakli bo‘limni tanlang 👇",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# DARS JADVALI
# ============================================================

async def schedule_menu(update, context):

    context.user_data["state"] = "choose_schedule_grade"

    keyboard = ReplyKeyboardMarkup(
        [
            ["1-sinf", "2-sinf", "3-sinf"],
            ["4-sinf", "5-sinf", "6-sinf"],
            ["7-sinf", "8-sinf", "9-sinf"],
            ["10-sinf", "11-sinf"],
            ["⬅️ Orqaga"]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📚 <b>Dars jadvali</b>\n\n"
        "Sinfni tanlang:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def show_schedule(update, context):

    grade = update.message.text

    if not grade.endswith("-sinf"):
        return

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT day, lesson, subject
        FROM schedules
        WHERE grade = ?
        ORDER BY id
    """, (grade,))

    rows = cursor.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text(
            f"📚 <b>{grade}</b>\n\n"
            f"❌ Hozircha dars jadvali kiritilmagan.",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

        context.user_data.clear()
        return

    days = {}

    for day, lesson, subject in rows:

        if day not in days:
            days[day] = []

        days[day].append(
            (lesson, subject)
        )

    result = f"📚 <b>{grade} dars jadvali</b>\n\n"

    for day, lessons in days.items():

        result += f"📅 <b>{day}</b>\n"

        for lesson, subject in lessons:

            result += (
                f"{lesson}. {subject}\n"
            )

        result += "\n"

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

    context.user_data.clear()


# ============================================================
# UYGA VAZIFA
# ============================================================

async def homework_menu(update, context):

    context.user_data["state"] = "choose_homework_grade"

    keyboard = ReplyKeyboardMarkup(
        [
            ["1-sinf", "2-sinf", "3-sinf"],
            ["4-sinf", "5-sinf", "6-sinf"],
            ["7-sinf", "8-sinf", "9-sinf"],
            ["10-sinf", "11-sinf"],
            ["⬅️ Orqaga"]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "📝 <b>Uyga vazifa</b>\n\n"
        "Sinfni tanlang:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def show_homework(update, context):

    grade = update.message.text

    if not grade.endswith("-sinf"):
        return

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject, task, created_at
        FROM homework
        WHERE grade = ?
        ORDER BY id DESC
    """, (grade,))

    rows = cursor.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text(
            f"📝 <b>{grade}</b>\n\n"
            f"❌ Hozircha uyga vazifa yo‘q.",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

        context.user_data.clear()
        return

    result = f"📝 <b>{grade} uyga vazifalari</b>\n\n"

    for subject, task, created_at in rows:

        result += (
            f"📖 <b>{subject}</b>\n"
            f"{task}\n"
            f"🕐 {created_at}\n\n"
        )

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

    context.user_data.clear()


# ============================================================
# E'LONLAR
# ============================================================

async def announcements(update, context):

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT text, created_at
        FROM announcements
        ORDER BY id DESC
        LIMIT 15
    """)

    rows = cursor.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text(
            "📢 Hozircha e'lonlar yo‘q.",
            reply_markup=main_keyboard()
        )

        return

    result = "📢 <b>E'lonlar</b>\n\n"

    for text, created_at in rows:

        result += (
            f"🔹 {text}\n"
            f"🕐 {created_at}\n\n"
        )

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


# ============================================================
# TADBIRLAR
# ============================================================

async def events(update, context):

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, event_date, description
        FROM events
        ORDER BY id DESC
        LIMIT 15
    """)

    rows = cursor.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text(
            "🎉 Hozircha tadbirlar yo‘q.",
            reply_markup=main_keyboard()
        )

        return

    result = "🎉 <b>Tadbirlar</b>\n\n"

    for title, event_date, description in rows:

        result += (
            f"🎯 <b>{title}</b>\n"
            f"📅 {event_date}\n"
            f"ℹ️ {description}\n\n"
        )

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


# ============================================================
# AI
# ============================================================

AI_INSTRUCTIONS = """
Sen Maktab 57 Telegram botining AI yordamchisisan.

Foydalanuvchi o'zbek tilida yozsa, o'zbek tilida javob ber.

Sen:
- matematika
- ona tili
- adabiyot
- tarix
- geografiya
- fizika
- kimyo
- informatika
- ingliz tili

va boshqa maktab fanlarida yordam berasan.

Masalalarni kerak bo'lsa bosqichma-bosqich tushuntir.

Javoblarni sodda, aniq va o'quvchiga tushunarli qil.

Agar foydalanuvchi "faqat javob" desa,
ortiqcha tushuntirish bermasdan javob ber.

Agar ma'lumotni aniq bilmasang,
to'qib chiqarmagin.

Hurmatli va do'stona bo'l.
"""


async def ask_ai(question):

    if not ai_client:

        return (
            "⚠️ AI hali ulanmagan.\n\n"
            "Render → Environment Variables bo‘limida "
            "OPENAI_API_KEY qo‘yilishi kerak."
        )

    try:

        response = await ai_client.responses.create(
            model=OPENAI_MODEL,
            instructions=AI_INSTRUCTIONS,
            input=question,
            max_output_tokens=1500
        )

        answer = response.output_text

        if not answer:

            return "⚠️ AI javob qaytarmadi."

        return answer

    except Exception as error:

        logger.exception(
            "OpenAI xatosi: %s",
            error
        )

        return (
            "⚠️ AI bilan bog‘lanishda xatolik yuz berdi.\n\n"
            "Bir ozdan keyin yana urinib ko‘ring."
        )


async def ai_menu(update, context):

    context.user_data["state"] = "ai"

    await update.message.reply_text(
        "🤖 <b>AI yordamchi</b>\n\n"
        "Savolingizni yozing.\n\n"
        "Masalan:\n"
        "🔹 25 × 16 nechiga teng?\n"
        "🔹 Kvadrat tenglamani tushuntir.\n"
        "🔹 Amir Temur haqida ma'lumot ber.\n"
        "🔹 Ingliz tilidan yordam ber.\n\n"
        "⬅️ Orqaga — asosiy menyuga qaytish.",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )


# ============================================================
# ADMIN PANEL
# ============================================================

async def admin_menu(update, context):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "⛔ Siz administrator emassiz."
        )

        return

    context.user_data["state"] = "admin"

    keyboard = ReplyKeyboardMarkup(
        [
            ["➕ Jadval qo‘shish"],
            ["➕ Uyga vazifa qo‘shish"],
            ["➕ E'lon qo‘shish"],
            ["➕ Tadbir qo‘shish"],
            ["🗑 Ma'lumotlarni tozalash"],
            ["⬅️ Orqaga"]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "⚙️ <b>Administrator paneli</b>\n\n"
        "Kerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# ADMIN - JADVAL QO'SHISH
# ============================================================

async def add_schedule(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["state"] = "add_schedule"

    await update.message.reply_text(
        "➕ <b>Dars qo‘shish</b>\n\n"
        "Quyidagi formatda yozing:\n\n"
        "<code>11-sinf | Dushanba | 1 | Matematika</code>\n\n"
        "Tartibi:\n"
        "Sinf | Kun | Dars raqami | Fan",
        parse_mode="HTML"
    )


async def save_schedule(update, context):

    if not is_admin(update.effective_user.id):
        return

    try:

        parts = [
            x.strip()
            for x in update.message.text.split("|")
        ]

        if len(parts) != 4:
            raise ValueError

        grade = parts[0]
        day = parts[1]
        lesson = int(parts[2])
        subject = parts[3]

        conn = database()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO schedules
            (grade, day, lesson, subject)
            VALUES (?, ?, ?, ?)
        """, (
            grade,
            day,
            lesson,
            subject
        ))

        conn.commit()
        conn.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ <b>Dars jadvali qo‘shildi!</b>",
            parse_mode="HTML",
            reply_markup=admin_keyboard()
        )

    except Exception:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "To‘g‘ri misol:\n\n"
            "11-sinf | Dushanba | 1 | Matematika"
        )


# ============================================================
# ADMIN - UYGA VAZIFA
# ============================================================

async def add_homework(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["state"] = "add_homework"

    await update.message.reply_text(
        "➕ <b>Uyga vazifa qo‘shish</b>\n\n"
        "Format:\n\n"
        "<code>11-sinf | Matematika | 12-misol, 13-misol</code>",
        parse_mode="HTML"
    )


async def save_homework(update, context):

    if not is_admin(update.effective_user.id):
        return

    try:

        parts = [
            x.strip()
            for x in update.message.text.split("|")
        ]

        if len(parts) != 3:
            raise ValueError

        grade = parts[0]
        subject = parts[1]
        task = parts[2]

        conn = database()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO homework
            (grade, subject, task, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            grade,
            subject,
            task,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        ))

        conn.commit()
        conn.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ <b>Uyga vazifa qo‘shildi!</b>",
            parse_mode="HTML",
            reply_markup=admin_keyboard()
        )

    except Exception:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Misol:\n\n"
            "11-sinf | Matematika | 12-misol, 13-misol"
        )


# ============================================================
# ADMIN - E'LON
# ============================================================

async def add_announcement(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["state"] = "add_announcement"

    await update.message.reply_text(
        "📢 E'lon matnini yuboring:"
    )


async def save_announcement(update, context):

    if not is_admin(update.effective_user.id):
        return

    text = update.message.text.strip()

    if not text:

        await update.message.reply_text(
            "❌ E'lon bo‘sh bo‘lishi mumkin emas."
        )

        return

    conn = database()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO announcements
        (text, created_at)
        VALUES (?, ?)
    """, (
        text,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    ))

    conn.commit()
    conn.close()

    context.user_data.clear()

    await update.message.reply_text(
        "✅ <b>E'lon qo‘shildi!</b>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# ============================================================
# ADMIN - TADBIR
# ============================================================

async def add_event(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["state"] = "add_event"

    await update.message.reply_text(
        "🎉 <b>Tadbir qo‘shish</b>\n\n"
        "Format:\n\n"
        "<code>Sport musobaqasi | 20-sentabr | "
        "Maktab hovlisida</code>",
        parse_mode="HTML"
    )


async def save_event(update, context):

    if not is_admin(update.effective_user.id):
        return

    try:

        parts = [
            x.strip()
            for x in update.message.text.split("|")
        ]

        if len(parts) != 3:
            raise ValueError

        title = parts[0]
        event_date = parts[1]
        description = parts[2]

        conn = database()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO events
            (title, event_date, description)
            VALUES (?, ?, ?)
        """, (
            title,
            event_date,
            description
        ))

        conn.commit()
        conn.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ <b>Tadbir qo‘shildi!</b>",
            parse_mode="HTML",
            reply_markup=admin_keyboard()
        )

    except Exception:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Misol:\n\n"
            "Sport musobaqasi | 20-sentabr | "
            "Maktab hovlisida"
        )


# ============================================================
# ADMIN - TOZALASH
# ============================================================

async def clear_menu(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["state"] = "clear"

    keyboard = ReplyKeyboardMarkup(
        [
            ["🗑 Jadval"],
            ["🗑 Uyga vazifalar"],
            ["🗑 E'lonlar"],
            ["🗑 Tadbirlar"],
            ["⬅️ Orqaga"]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🗑 <b>Ma'lumotlarni tozalash</b>\n\n"
        "Qaysi bo‘limni tozalash kerak?",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def clear_data(update, context):

    if not is_admin(update.effective_user.id):
        return

    text = update.message.text

    tables = {
        "🗑 Jadval": "schedules",
        "🗑 Uyga vazifalar": "homework",
        "🗑 E'lonlar": "announcements",
        "🗑 Tadbirlar": "events"
    }

    if text not in tables:
        return

    table = tables[text]

    conn = database()
    cursor = conn.cursor()

    cursor.execute(
        f"DELETE FROM {table}"
    )

    conn.commit()
    conn.close()

    context.user_data.clear()

    await update.message.reply_text(
        "✅ Ma'lumotlar tozalandi.",
        reply_markup=admin_keyboard()
    )


# ============================================================
# YORDAM
# ============================================================

async def help_command(update, context):

    keyboard = (
        admin_keyboard()
        if is_admin(update.effective_user.id)
        else main_keyboard()
    )

    await update.message.reply_text(
        "ℹ️ <b>Maktab 57 bot yordamchisi</b>\n\n"
        "📚 Dars jadvali\n"
        "Sinf bo‘yicha darslarni ko‘rish.\n\n"
        "📝 Uyga vazifa\n"
        "Sinf bo‘yicha vazifalarni ko‘rish.\n\n"
        "📢 E'lonlar\n"
        "Maktab e'lonlarini ko‘rish.\n\n"
        "🎉 Tadbirlar\n"
        "Maktab tadbirlarini ko‘rish.\n\n"
        "🤖 AI yordamchi\n"
        "Fanlar bo‘yicha AI dan yordam olish.\n\n"
        "⚙️ Admin\n"
        "Faqat administrator uchun.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# ASOSIY TEXT HANDLER
# ============================================================

async def text_handler(update, context):

    if not update.message:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

    state = context.user_data.get(
        "state"
    )

    # --------------------------------------------------------
    # ORQAGA
    # --------------------------------------------------------

    if text == "⬅️ Orqaga":

        context.user_data.clear()

        keyboard = (
            admin_keyboard()
            if is_admin(user_id)
            else main_keyboard()
        )

        await update.message.reply_text(
            "🏠 <b>Asosiy menyu</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        return

    # --------------------------------------------------------
    # ASOSIY TUGMALAR
    # --------------------------------------------------------

    if text == "📚 Dars jadvali":

        await schedule_menu(
            update,
            context
        )

        return

    if text == "📝 Uyga vazifa":

        await homework_menu(
            update,
            context
        )

        return

    if text == "📢 E'lonlar":

        await announcements(
            update,
            context
        )

        return

    if text == "🎉 Tadbirlar":

        await events(
            update,
            context
        )

        return

    if text == "🤖 AI yordamchi":

        await ai_menu(
            update,
            context
        )

        return

    if text == "ℹ️ Yordam":

        await help_command(
            update,
            context
        )

        return

    # --------------------------------------------------------
    # ADMIN MENU
    # --------------------------------------------------------

    if text == "⚙️ Admin":

        await admin_menu(
            update,
            context
        )

        return

    if text == "➕ Jadval qo‘shish":

        await add_schedule(
            update,
            context
        )

        return

    if text == "➕ Uyga vazifa qo‘shish":

        await add_homework(
            update,
            context
        )

        return

    if text == "➕ E'lon qo‘shish":

        await add_announcement(
            update,
            context
        )

        return

    if text == "➕ Tadbir qo‘shish":

        await add_event(
            update,
            context
        )

        return

    if text == "🗑 Ma'lumotlarni tozalash":

        await clear_menu(
            update,
            context
        )

        return

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    if state == "choose_schedule_grade":

        await show_schedule(
            update,
            context
        )

        return

    if state == "choose_homework_grade":

        await show_homework(
            update,
            context
        )

        return

    if state == "add_schedule":

        await save_schedule(
            update,
            context
        )

        return

    if state == "add_homework":

        await save_homework(
            update,
            context
        )

        return

    if state == "add_announcement":

        await save_announcement(
            update,
            context
        )

        return

    if state == "add_event":

        await save_event(
            update,
            context
        )

        return

    if state == "clear":

        await clear_data(
            update,
            context
        )

        return

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    if state == "ai":

        await update.message.reply_text(
            "🤖 O‘ylayapman...",
        )

        answer = await ask_ai(text)

        # Telegram 4096 belgidan katta xabarni qabul qilmaydi.
        chunk_size = 3800

        for start in range(
            0,
            len(answer),
            chunk_size
        ):

            await update.message.reply_text(
                answer[
                    start:start + chunk_size
                ]
            )

        return

    # --------------------------------------------------------
    # TUSHUNILMAGAN BUYRUQ
    # --------------------------------------------------------

    keyboard = (
        admin_keyboard()
        if is_admin(user_id)
        else main_keyboard()
    )

    await update.message.reply_text(
        "🙂 Buyruqni tushunmadim.\n\n"
        "Menyudagi tugmalardan foydalaning.",
        reply_markup=keyboard
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update, context):

    logger.error(
        "Bot xatosi: %s",
        context.error,
        exc_info=True
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN topilmadi!"
        )

    create_database()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "🏫 Maktab 57 bot ishga tushdi!"
    )

    application.run_polling(
        drop_pending_updates=True
    )


# ============================================================
# ISHGA TUSHIRISH
# ============================================================

if __name__ == "__main__":
    main()
