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

# ============================================================
# SOZLAMALAR
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "0")

try:
    ADMIN_ID = int(ADMIN_ID)
except:
    ADMIN_ID = 0

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
    return ADMIN_ID != 0 and user_id == ADMIN_ID


# ============================================================
# KLAVIATURALAR
# ============================================================

def main_keyboard():

    return ReplyKeyboardMarkup(
        [
            ["📚 Dars jadvali", "📝 Uyga vazifa"],
            ["📢 E'lonlar", "🎉 Tadbirlar"],
            ["🤖 Yordamchi", "ℹ️ Yordam"],
        ],
        resize_keyboard=True
    )


def admin_keyboard():

    return ReplyKeyboardMarkup(
        [
            ["📚 Dars jadvali", "📝 Uyga vazifa"],
            ["📢 E'lonlar", "🎉 Tadbirlar"],
            ["🤖 Yordamchi", "⚙️ Admin"],
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

    keyboard = (
        admin_keyboard()
        if is_admin(user.id)
        else main_keyboard()
    )

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

    context.user_data["state"] = "schedule_grade"

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
            result += f"{lesson}. {subject}\n"

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

    context.user_data["state"] = "homework_grade"

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
# ODDIY YORDAMCHI
# ============================================================

async def assistant(update, context):

    context.user_data["state"] = "assistant"

    await update.message.reply_text(
        "🤖 <b>Yordamchi</b>\n\n"
        "Men oddiy savollarga javob beraman.\n\n"
        "Masalan:\n"
        "• salom\n"
        "• maktab haqida\n"
        "• dars jadvali\n"
        "• uyga vazifa\n\n"
        "⬅️ Orqaga — asosiy menyuga qaytish.",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )


async def assistant_answer(update, context):

    text = update.message.text.lower().strip()

    if text in ["salom", "assalomu alaykum", "assalom"]:

        answer = (
            "👋 Va alaykum assalom!\n"
            "🏫 Maktab 57 botiga xush kelibsiz!"
        )

    elif "maktab" in text:

        answer = (
            "🏫 <b>Maktab 57</b>\n\n"
            "Bu bot orqali dars jadvali, "
            "uyga vazifalar, e'lonlar va "
            "tadbirlarni ko‘rishingiz mumkin."
        )

    elif "rahmat" in text:

        answer = "😊 Arzimaydi!"

    elif "kim" in text and "sen" in text:

        answer = (
            "🤖 Men Maktab 57 botining "
            "oddiy yordamchisiman."
        )

    else:

        answer = (
            "🙂 Bu savolga hozircha tayyor "
            "javobim yo‘q.\n\n"
            "📚 Dars jadvali yoki boshqa "
            "menyu tugmalaridan foydalaning."
        )

    await update.message.reply_text(
        answer,
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
# ADMIN - JADVAL
# ============================================================

async def add_schedule(update, context):

    if not is_admin(update.effective_user.id):
        return

    context.user_data["state"] = "add_schedule"

    await update.message.reply_text(
        "➕ <b>Dars qo‘shish</b>\n\n"
        "Format:\n\n"
        "<code>11-sinf | Dushanba | 1 | Matematika</code>\n\n"
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

    except:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Masalan:\n"
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
        "<code>11-sinf | Matematika | 12-misol</code>",
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

    except:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Masalan:\n"
            "11-sinf | Matematika | 12-misol"
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

    except:

        await update.message.reply_text(
            "❌ Format xato.\n\n"
            "Masalan:\n"
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

    tables = {
        "🗑 Jadval": "schedules",
        "🗑 Uyga vazifalar": "homework",
        "🗑 E'lonlar": "announcements",
        "🗑 Tadbirlar": "events"
    }

    text = update.message.text

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
        "ℹ️ <b>Maktab 57 bot</b>\n\n"
        "📚 Dars jadvali — sinflar bo‘yicha jadval\n"
        "📝 Uyga vazifa — vazifalarni ko‘rish\n"
        "📢 E'lonlar — maktab e'lonlari\n"
        "🎉 Tadbirlar — tadbirlar ro‘yxati\n"
        "🤖 Yordamchi — oddiy savollarga javob\n"
        "⚙️ Admin — faqat admin uchun",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# ASOSIY HANDLER
# ============================================================

async def text_handler(update, context):

    if not update.message:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

    state = context.user_data.get("state")

    # ORQAGA

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

    # ASOSIY MENYU

    if text == "📚 Dars jadvali":
        await schedule_menu(update, context)
        return

    if text == "📝 Uyga vazifa":
        await homework_menu(update, context)
        return

    if text == "📢 E'lonlar":
        await announcements(update, context)
        return

    if text == "🎉 Tadbirlar":
        await events(update, context)
        return

    if text == "🤖 Yordamchi":
        await assistant(update, context)
        return

    if text == "ℹ️ Yordam":
        await help_command(update, context)
        return

    # ADMIN

    if text == "⚙️ Admin":
        await admin_menu(update, context)
        return

    if text == "➕ Jadval qo‘shish":
        await add_schedule(update, context)
        return

    if text == "➕ Uyga vazifa qo‘shish":
        await add_homework(update, context)
        return

    if text == "➕ E'lon qo‘shish":
        await add_announcement(update, context)
        return

    if text == "➕ Tadbir qo‘shish":
        await add_event(update, context)
        return

    if text == "🗑 Ma'lumotlarni tozalash":
        await clear_menu(update, context)
        return

    # STATE

    if state == "schedule_grade":
        await show_schedule(update, context)
        return

    if state == "homework_grade":
        await show_homework(update, context)
        return

    if state == "add_schedule":
        await save_schedule(update, context)
        return

    if state == "add_homework":
        await save_homework(update, context)
        return

    if state == "add_announcement":
        await save_announcement(update, context)
        return

    if state == "add_event":
        await save_event(update, context)
        return

    if state == "clear":
        await clear_data(update, context)
        return

    if state == "assistant":
        await assistant_answer(update, context)
        return

    # TUSHUNILMAGAN

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
# ERROR
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


if __name__ == "__main__":
    main()
