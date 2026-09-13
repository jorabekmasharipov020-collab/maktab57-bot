import os
import sqlite3
import logging
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from openai import AsyncOpenAI


# =========================================================
# SOZLAMALAR
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Render'da xohlasang OPENAI_MODEL ni o'zgartirishing mumkin.
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

DB_NAME = "school_bot.db"


# =========================================================
# LOG
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# OPENAI
# =========================================================

ai_client = None

if OPENAI_API_KEY:
    ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade TEXT NOT NULL,
            day TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            subject TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade TEXT NOT NULL,
            subject TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# KLAVIATURA
# =========================================================

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📚 Dars jadvali", "📝 Uyga vazifa"],
            ["📢 E'lonlar", "🎉 Tadbirlar"],
            ["🤖 AI yordamchi", "ℹ️ Yordam"],
        ],
        resize_keyboard=True,
    )


def admin_menu():
    return ReplyKeyboardMarkup(
        [
            ["📚 Dars jadvali", "📝 Uyga vazifa"],
            ["📢 E'lonlar", "🎉 Tadbirlar"],
            ["🤖 AI yordamchi", "⚙️ Admin"],
            ["ℹ️ Yordam"],
        ],
        resize_keyboard=True,
    )


def is_admin(user_id):
    return user_id == ADMIN_ID and ADMIN_ID != 0


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if is_admin(user.id):
        keyboard = admin_menu()
    else:
        keyboard = main_menu()

    text = (
        "🏫 Maktab 57 botiga xush kelibsiz!\n\n"
        f"👤 Salom, {user.first_name}!\n\n"
        "Kerakli bo‘limni tanlang:"
    )

    await update.message.reply_text(
        text,
        reply_markup=keyboard
    )


# =========================================================
# DARS JADVALI
# =========================================================

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):

    grades = [
        ["1-sinf", "2-sinf", "3-sinf"],
        ["4-sinf", "5-sinf", "6-sinf"],
        ["7-sinf", "8-sinf", "9-sinf"],
        ["10-sinf", "11-sinf"],
    ]

    keyboard = ReplyKeyboardMarkup(
        grades + [["⬅️ Orqaga"]],
        resize_keyboard=True
    )

    context.user_data["mode"] = "schedule_grade"

    await update.message.reply_text(
        "📚 Sinfni tanlang:",
        reply_markup=keyboard
    )


async def show_grade_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):

    grade = update.message.text

    if not grade.endswith("-sinf"):
        return

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT day, lesson, subject
        FROM schedules
        WHERE grade = ?
        ORDER BY
            CASE day
                WHEN 'Dushanba' THEN 1
                WHEN 'Seshanba' THEN 2
                WHEN 'Chorshanba' THEN 3
                WHEN 'Payshanba' THEN 4
                WHEN 'Juma' THEN 5
                WHEN 'Shanba' THEN 6
                ELSE 7
            END,
            lesson
        """,
        (grade,)
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(
            f"📚 {grade} uchun dars jadvali hali kiritilmagan."
        )
        return

    result = f"📚 <b>{grade} dars jadvali</b>\n\n"

    current_day = None

    for row in rows:

        if row["day"] != current_day:
            current_day = row["day"]
            result += f"\n📅 <b>{current_day}</b>\n"

        result += (
            f"{row['lesson']}. {row['subject']}\n"
        )

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_menu()
    )

    context.user_data.clear()


# =========================================================
# UYGA VAZIFA
# =========================================================

async def show_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):

    grades = [
        ["1-sinf", "2-sinf", "3-sinf"],
        ["4-sinf", "5-sinf", "6-sinf"],
        ["7-sinf", "8-sinf", "9-sinf"],
        ["10-sinf", "11-sinf"],
    ]

    keyboard = ReplyKeyboardMarkup(
        grades + [["⬅️ Orqaga"]],
        resize_keyboard=True
    )

    context.user_data["mode"] = "homework_grade"

    await update.message.reply_text(
        "📝 Sinfni tanlang:",
        reply_markup=keyboard
    )


async def show_grade_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):

    grade = update.message.text

    if not grade.endswith("-sinf"):
        return

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT subject, text, created_at
        FROM homework
        WHERE grade = ?
        ORDER BY id DESC
        """,
        (grade,)
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(
            f"📝 {grade} uchun uyga vazifa yo‘q."
        )
        return

    result = f"📝 <b>{grade} uyga vazifalari</b>\n\n"

    for row in rows:
        result += (
            f"📖 <b>{row['subject']}</b>\n"
            f"{row['text']}\n\n"
        )

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_menu()
    )

    context.user_data.clear()


# =========================================================
# E'LONLAR
# =========================================================

async def show_announcements(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT text, created_at
        FROM announcements
        ORDER BY id DESC
        LIMIT 10
        """
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(
            "📢 Hozircha e'lonlar yo‘q.",
            reply_markup=main_menu()
        )
        return

    result = "📢 <b>So‘nggi e'lonlar</b>\n\n"

    for row in rows:
        result += (
            f"🔹 {row['text']}\n"
            f"🕐 {row['created_at']}\n\n"
        )

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================================================
# TADBIRLAR
# =========================================================

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT title, date, description
        FROM events
        ORDER BY id DESC
        LIMIT 10
        """
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(
            "🎉 Hozircha tadbirlar yo‘q.",
            reply_markup=main_menu()
        )
        return

    result = "🎉 <b>Tadbirlar</b>\n\n"

    for row in rows:
        result += (
            f"🎯 <b>{row['title']}</b>\n"
            f"📅 {row['date']}\n"
            f"ℹ️ {row['description']}\n\n"
        )

    await update.message.reply_text(
        result,
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================================================
# AI
# =========================================================

AI_INSTRUCTIONS = """
Sen Maktab 57 Telegram botining AI yordamchisisan.

Vazifang:
- O'quvchilarga darslarni tushuntirish.
- Matematika, ona tili, tarix, fizika va boshqa fanlardan yordam berish.
- Uy vazifasini tushuntirish.
- Masalalarni bosqichma-bosqich yechish.
- O'zbek tilida sodda va tushunarli javob berish.
- Agar foydalanuvchi qisqa javob so'rasa, qisqa javob berish.
- Bilmagan ma'lumotni to'qib chiqarmaslik.
- O'quvchini mustaqil o'rganishga yordam berish.
- Hurmatli va do'stona ohangda gapirish.

Sen maktab botining yordamchisisan.
"""


async def ask_ai(question):

    if not ai_client:
        return (
            "⚠️ AI hozir ulanmagan.\n\n"
            "Admin Render'da OPENAI_API_KEY ni "
            "Environment Variables bo‘limiga qo‘yishi kerak."
        )

    try:

        response = await ai_client.responses.create(
            model=MODEL,
            instructions=AI_INSTRUCTIONS,
            input=question,
            max_output_tokens=1200,
        )

        answer = response.output_text

        if not answer:
            return "⚠️ AI javob qaytarmadi."

        return answer

    except Exception as e:

        logger.exception("AI xatosi")

        return (
            "⚠️ AI bilan bog‘lanishda xatolik yuz berdi.\n"
            "Bir ozdan keyin qayta urinib ko‘ring."
        )


async def ai_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "ai"

    await update.message.reply_text(
        "🤖 AI yordamchi yoqildi!\n\n"
        "Savolingizni yozing.\n"
        "Masalan:\n"
        "• Kvadrat tenglamani tushuntir\n"
        "• Amir Temur haqida ma'lumot ber\n"
        "• 25 × 16 ni hisobla\n\n"
        "⬅️ Orqaga — menyuga qaytish",
        reply_markup=ReplyKeyboardMarkup(
            [["⬅️ Orqaga"]],
            resize_keyboard=True
        )
    )


# =========================================================
# ADMIN MENU
# =========================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ Bu bo‘lim faqat administrator uchun."
        )
        return

    keyboard = ReplyKeyboardMarkup(
        [
            ["➕ Jadval qo‘shish"],
            ["➕ Uyga vazifa qo‘shish"],
            ["➕ E'lon qo‘shish"],
            ["➕ Tadbir qo‘shish"],
            ["🗑 Ma'lumotlarni tozalash"],
            ["⬅️ Orqaga"],
        ],
        resize_keyboard=True
    )

    context.user_data["mode"] = "admin"

    await update.message.reply_text(
        "⚙️ <b>Admin panel</b>\n\n"
        "Kerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================================================
# ADMIN - JADVAL
# =========================================================

async def add_schedule_start(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["mode"] = "add_schedule"

    await update.message.reply_text(
        "📚 Jadval qo‘shish.\n\n"
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

        parts = [x.strip() for x in update.message.text.split("|")]

        if len(parts) != 4:
            raise ValueError

        grade, day, lesson, subject = parts

        lesson = int(lesson)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO schedules
            (grade, day, lesson, subject)
            VALUES (?, ?, ?, ?)
            """,
            (grade, day, lesson, subject)
        )

        conn.commit()
        conn.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ Dars jadvali qo‘shildi!",
            reply_markup=admin_menu()
        )

    except Exception:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Masalan:\n"
            "11-sinf | Dushanba | 1 | Matematika"
        )


# =========================================================
# ADMIN - UYGA VAZIFA
# =========================================================

async def add_homework_start(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["mode"] = "add_homework"

    await update.message.reply_text(
        "📝 Uyga vazifa qo‘shish.\n\n"
        "Format:\n\n"
        "<code>11-sinf | Matematika | 12-misol, 13-misol</code>",
        parse_mode="HTML"
    )


async def save_homework(update, context):

    if not is_admin(update.effective_user.id):
        return

    try:

        parts = [x.strip() for x in update.message.text.split("|")]

        if len(parts) != 3:
            raise ValueError

        grade, subject, text = parts

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO homework
            (grade, subject, text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                grade,
                subject,
                text,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        )

        conn.commit()
        conn.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ Uyga vazifa qo‘shildi!",
            reply_markup=admin_menu()
        )

    except Exception:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Masalan:\n"
            "11-sinf | Matematika | 12-misol, 13-misol"
        )


# =========================================================
# ADMIN - E'LON
# =========================================================

async def add_announcement_start(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["mode"] = "add_announcement"

    await update.message.reply_text(
        "📢 E'lon matnini yuboring:"
    )


async def save_announcement(update, context):

    if not is_admin(update.effective_user.id):
        return

    text = update.message.text

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO announcements
        (text, created_at)
        VALUES (?, ?)
        """,
        (
            text,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )

    conn.commit()
    conn.close()

    context.user_data.clear()

    await update.message.reply_text(
        "✅ E'lon qo‘shildi!",
        reply_markup=admin_menu()
    )


# =========================================================
# ADMIN - TADBIR
# =========================================================

async def add_event_start(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["mode"] = "add_event"

    await update.message.reply_text(
        "🎉 Tadbir qo‘shish.\n\n"
        "Format:\n\n"
        "<code>Sport musobaqasi | 20-sentabr | Maktab hovlisida</code>",
        parse_mode="HTML"
    )


async def save_event(update, context):

    if not is_admin(update.effective_user.id):
        return

    try:

        parts = [x.strip() for x in update.message.text.split("|")]

        if len(parts) != 3:
            raise ValueError

        title, date, description = parts

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO events
            (title, date, description)
            VALUES (?, ?, ?)
            """,
            (title, date, description)
        )

        conn.commit()
        conn.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ Tadbir qo‘shildi!",
            reply_markup=admin_menu()
        )

    except Exception:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Masalan:\n"
            "Sport musobaqasi | 20-sentabr | Maktab hovlisida"
        )


# =========================================================
# TOZALASH
# =========================================================

async def clear_data(update, context):

    if not is_admin(update.effective_user.id):
        return

    keyboard = ReplyKeyboardMarkup(
        [
            ["🗑 Jadvalni tozalash"],
            ["🗑 Uyga vazifani tozalash"],
            ["🗑 E'lonlarni tozalash"],
            ["🗑 Tadbirlarni tozalash"],
            ["⬅️ Orqaga"],
        ],
        resize_keyboard=True
    )

    context.user_data["mode"] = "clear_menu"

    await update.message.reply_text(
        "🗑 Qaysi ma'lumotni tozalaymiz?",
        reply_markup=keyboard
    )


async def clear_selected(update, context):

    if not is_admin(update.effective_user.id):
        return

    text = update.message.text

    table = None

    if text == "🗑 Jadvalni tozalash":
        table = "schedules"

    elif text == "🗑 Uyga vazifani tozalash":
        table = "homework"

    elif text == "🗑 E'lonlarni tozalash":
        table = "announcements"

    elif text == "🗑 Tadbirlarni tozalash":
        table = "events"

    if not table:
        return

    conn = get_db()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {table}")

    conn.commit()
    conn.close()

    context.user_data.clear()

    await update.message.reply_text(
        "✅ Ma'lumotlar tozalandi.",
        reply_markup=admin_menu()
    )


# =========================================================
# YORDAM
# =========================================================

async def help_command(update, context):

    await update.message.reply_text(
        "ℹ️ <b>Maktab 57 bot</b>\n\n"
        "📚 Dars jadvali — sinflar jadvali\n"
        "📝 Uyga vazifa — berilgan vazifalar\n"
        "📢 E'lonlar — maktab yangiliklari\n"
        "🎉 Tadbirlar — tadbirlar ro‘yxati\n"
        "🤖 AI yordamchi — savollarga AI javob beradi\n\n"
        "Muammo bo‘lsa administratorga murojaat qiling.",
        parse_mode="HTML",
        reply_markup=(
            admin_menu()
            if is_admin(update.effective_user.id)
            else main_menu()
        )
    )


# =========================================================
# MATN HANDLER
# =========================================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text
    user_id = update.effective_user.id
    mode = context.user_data.get("mode")

    # -------------------------
    # ORQAGA
    # -------------------------

    if text == "⬅️ Orqaga":

        context.user_data.clear()

        await update.message.reply_text(
            "🏠 Bosh menyu:",
            reply_markup=(
                admin_menu()
                if is_admin(user_id)
                else main_menu()
            )
        )

        return

    # -------------------------
    # ASOSIY MENU
    # -------------------------

    if text == "📚 Dars jadvali":
        await show_schedule(update, context)
        return

    if text == "📝 Uyga vazifa":
        await show_homework(update, context)
        return

    if text == "📢 E'lonlar":
        await show_announcements(update, context)
        return

    if text == "🎉 Tadbirlar":
        await show_events(update, context)
        return

    if text == "🤖 AI yordamchi":
        await ai_mode(update, context)
        return

    if text == "ℹ️ Yordam":
        await help_command(update, context)
        return

    # -------------------------
    # ADMIN
    # -------------------------

    if text == "⚙️ Admin":

        if is_admin(user_id):
            await admin_panel(update, context)

        return

    if text == "➕ Jadval qo‘shish":

        if is_admin(user_id):
            await add_schedule_start(update, context)

        return

    if text == "➕ Uyga vazifa qo‘shish":

        if is_admin(user_id):
            await add_homework_start(update, context)

        return

    if text == "➕ E'lon qo‘shish":

        if is_admin(user_id):
            await add_announcement_start(update, context)

        return

    if text == "➕ Tadbir qo‘shish":

        if is_admin(user_id):
            await add_event_start(update, context)

        return

    if text == "🗑 Ma'lumotlarni tozalash":

        if is_admin(user_id):
            await clear_data(update, context)

        return

    # -------------------------
    # CLEAR
    # -------------------------

    if mode == "clear_menu":

        await clear_selected(update, context)
        return

    # -------------------------
    # SCHEDULE
    # -------------------------

    if mode == "schedule_grade":

        await show_grade_schedule(update, context)
        return

    # -------------------------
    # HOMEWORK
    # -------------------------

    if mode == "homework_grade":

        await show_grade_homework(update, context)
        return

    # -------------------------
    # ADMIN SCHEDULE
    # -------------------------

    if mode == "add_schedule":

        await save_schedule(update, context)
        return

    # -------------------------
    # ADMIN HOMEWORK
    # -------------------------

    if mode == "add_homework":

        await save_homework(update, context)
        return

    # -------------------------
    # ADMIN ANNOUNCEMENT
    # -------------------------

    if mode == "add_announcement":

        await save_announcement(update, context)
        return

    # -------------------------
    # ADMIN EVENT
    # -------------------------

    if mode == "add_event":

        await save_event(update, context)
        return

    # -------------------------
    # AI
    # -------------------------

    if mode == "ai":

        await update.message.chat.send_action("typing")

        answer = await ask_ai(text)

        # Telegram xabari juda uzun bo'lsa bo'lib yuboramiz.
        chunk_size = 4000

        for i in range(0, len(answer), chunk_size):

            await update.message.reply_text(
                answer[i:i + chunk_size]
            )

        return

    # -------------------------
    # DEFAULT
    # -------------------------

    await update.message.reply_text(
        "Tushunmadim 🙂\n\n"
        "Menyudagi tugmalardan birini tanlang.",
        reply_markup=(
            admin_menu()
            if is_admin(user_id)
            else main_menu()
        )
    )


# =========================================================
# ERROR
# =========================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):

    logger.exception(
        "Botda xatolik:",
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN topilmadi. Render Environment Variables "
            "bo‘limiga BOT_TOKEN qo‘shing."
        )

    init_db()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    application.add_error_handler(error_handler)

    logger.info("🏫 Maktab 57 bot ishga tushdi!")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
