from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

import os
import threading
import random
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer


# =========================
# BOT TOKEN
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN Render Environment Variables'da topilmadi!")


# =========================
# MA'LUMOTLAR BAZASI
# =========================

DB_NAME = "maktab57.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            sinf TEXT NOT NULL,
            score INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, name, sinf, score FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()

    return user


def register_user(user_id, name, sinf):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO users (user_id, name, sinf, score)
        VALUES (
            ?,
            ?,
            ?,
            COALESCE((SELECT score FROM users WHERE user_id = ?), 0)
        )
        """,
        (user_id, name, sinf, user_id)
    )

    conn.commit()
    conn.close()


def add_score(user_id, points):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET score = score + ? WHERE user_id = ?",
        (points, user_id)
    )

    conn.commit()
    conn.close()


def get_rating():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, sinf, score FROM users ORDER BY score DESC, name ASC LIMIT 10"
    )

    rating = cursor.fetchall()
    conn.close()

    return rating


def menu_keyboard(sinf):
    return [
        [
            InlineKeyboardButton(
                "📚 Dars jadvali",
                callback_data=f"dars_{sinf}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏆 To‘garaklar",
                callback_data=f"togarak_{sinf}"
            )
        ],
        [
            InlineKeyboardButton(
                "🌐 Kundalik.com",
                url="https://kundalik.com"
            )
        ],
        [
            InlineKeyboardButton(
                "🎯 Sonni top",
                callback_data="game_start"
            )
        ],
        [
            InlineKeyboardButton(
                "🏆 Reyting",
                callback_data="rating"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Sinfni almashtirish",
                callback_data="change"
            )
        ]
    ]


async def show_main_menu(query, sinf):
    await query.edit_message_text(
        f"✅ Siz {sinf}-sinfni tanladingiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=InlineKeyboardMarkup(menu_keyboard(sinf))
    )


# =========================
# RO‘YXATDAN O‘TISH
# =========================

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["registration"] = True

    await update.message.reply_text(
        "📝 Ro‘yxatdan o‘tish\n\n"
        "👤 Ismingizni yozing:"
    )


async def registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("registration"):
        return

    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❗ Ismingizni yozing."
        )
        return

    context.user_data["registration_name"] = name
    context.user_data["registration"] = False
    context.user_data["registration_class"] = True

    await update.message.reply_text(
        f"✅ Ism saqlandi: {name}\n\n"
        "🏫 Endi sinfingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(sinflar_menyusi())
    )


# =========================
# SINFLAR MENYUSI
# =========================

def sinflar_menyusi():

    return [
        [
            InlineKeyboardButton("1️⃣ 1-sinf", callback_data="1"),
            InlineKeyboardButton("2️⃣ 2-sinf", callback_data="2")
        ],
        [
            InlineKeyboardButton("3️⃣ 3-sinf", callback_data="3"),
            InlineKeyboardButton("4️⃣ 4-sinf", callback_data="4")
        ],
        [
            InlineKeyboardButton("5️⃣ 5-sinf", callback_data="5"),
            InlineKeyboardButton("6️⃣ 6-sinf", callback_data="6")
        ],
        [
            InlineKeyboardButton("7️⃣ 7-sinf", callback_data="7"),
            InlineKeyboardButton("8️⃣ 8-sinf", callback_data="8")
        ],
        [
            InlineKeyboardButton("9️⃣ 9-sinf", callback_data="9"),
            InlineKeyboardButton("🔟 10-sinf", callback_data="10")
        ],
        [
            InlineKeyboardButton("1️⃣1️⃣ 11-sinf", callback_data="11")
        ]
    ]


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    user = get_user(user_id)

    if user:

        context.user_data["registration_name"] = user[1]
        context.user_data["registration_class"] = user[2]

        await update.message.reply_text(
            f"🏫 Maktab 57 botiga xush kelibsiz, {user[1]}!\n\n"
            f"🏫 Sinfingiz: {user[2]}-sinf\n\n"
            "Kerakli bo‘limni tanlang:",
            reply_markup=InlineKeyboardMarkup(
                menu_keyboard(user[2])
            )
        )

        return

    await ask_name(update, context)


# =========================
# SINF TANLASH
# =========================

async def class_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    sinf = query.data

    if context.user_data.get("registration_class"):

        name = context.user_data.get(
            "registration_name",
            update.effective_user.first_name
        )

        register_user(
            update.effective_user.id,
            name,
            sinf
        )

        context.user_data["registration_class"] = False
        context.user_data["registration_name"] = name

        await query.edit_message_text(
            f"🎉 Ro‘yxatdan muvaffaqiyatli o‘tdingiz!\n\n"
            f"👤 Ism: {name}\n"
            f"🏫 Sinf: {sinf}-sinf\n\n"
            "Endi botdan foydalanishingiz mumkin.",
            reply_markup=InlineKeyboardMarkup(
                menu_keyboard(sinf)
            )
        )

        return

    await show_main_menu(query, sinf)


# =========================
# DARS JADVALI
# =========================

async def dars_jadvali(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    sinf = query.data.replace("dars_", "")

    if sinf == "11":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📅 Dushanba",
                    callback_data="kun_dushanba"
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Seshanba",
                    callback_data="kun_seshanba"
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Chorshanba",
                    callback_data="kun_chorshanba"
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Payshanba",
                    callback_data="kun_payshanba"
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Juma",
                    callback_data="kun_juma"
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Shanba",
                    callback_data="kun_shanba"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="orqaga_11"
                )
            ]
        ]

        await query.edit_message_text(
            "📚 11-SINF DARS JADVALI\n\n"
            "Haftaning kunini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data=f"orqaga_{sinf}"
                )
            ]
        ]

        await query.edit_message_text(
            f"📚 {sinf}-sinf dars jadvali\n\n"
            "⏳ Bu sinf uchun jadval hali qo‘shilmagan.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# 11-SINF JADVALI
# =========================

JADVAL = {

    "kun_dushanba": (
        "📅 DUSHANBA\n\n"
        "1. Sinf soati\n"
        "2. Fizika\n"
        "3. Informatika / Qoraqalpoq tili\n"
        "4. Algebra\n"
        "5. Rus tili\n"
        "6. CHQBT"
    ),

    "kun_seshanba": (
        "📅 SESHANBA\n\n"
        "1. Algebra\n"
        "2. Kimyo\n"
        "3. DHA\n"
        "4. Biologiya\n"
        "5. Jismoniy tarbiya"
    ),

    "kun_chorshanba": (
        "📅 CHORSHANBA\n\n"
        "1. Ingliz tili\n"
        "2. CHQBT\n"
        "3. Adabiyot\n"
        "4. O‘zbekiston tarixi / Qoraqalpog‘iston tarixi\n"
        "5. Algebra"
    ),

    "kun_payshanba": (
        "📅 PAYSHANBA\n\n"
        "1. Ingliz tili\n"
        "2. Ona tili\n"
        "3. Biologiya\n"
        "4. Fizika\n"
        "5. Qoraqalpog‘iston tili\n"
        "6. Jismoniy tarbiya"
    ),

    "kun_juma": (
        "📅 JUMA\n\n"
        "1. Geometriya\n"
        "2. Rus tili\n"
        "3. Tadbirkorlik asoslari\n"
        "4. Astronomiya\n"
        "5. Tarbiya"
    ),

    "kun_shanba": (
        "📅 SHANBA\n\n"
        "1. Geometriya\n"
        "2. Kimyo\n"
        "3. Adabiyot\n"
        "4. Informatika\n"
        "5. Jahon tarixi"
    )
}


# =========================
# HAFTA KUNI TANLANGANDA
# =========================

async def kun_tanlandi(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    matn = JADVAL.get(
        query.data,
        "❌ Bu kun uchun jadval topilmadi."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Kunlarga qaytish",
                callback_data="dars_11"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(
        matn,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# TO‘GARAKLAR
# =========================

async def togaraklar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    sinf = query.data.replace("togarak_", "")

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Orqaga",
                callback_data=f"orqaga_{sinf}"
            )
        ]
    ]

    await query.edit_message_text(
        f"🏆 {sinf}-SINF TO‘GARAKLARI\n\n"
        "⏳ To‘garaklar ma’lumotlari tez orada qo‘shiladi.\n\n"
        "Bu bo‘limga to‘garak nomi,\n"
        "hafta kuni va vaqti kiritiladi.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# SINF MENYUSIGA QAYTISH
# =========================

async def back_to_class(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    sinf = query.data.replace("orqaga_", "")

    await show_main_menu(query, sinf)


# =========================
# SINFNI ALMASHTIRISH
# =========================

async def change_class(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🏫 Sinfingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(
            sinflar_menyusi()
        )
    )


# =========================
# BOSH MENYU
# =========================

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🏫 Maktab 57 botiga xush kelibsiz!\n\n"
        "Sinfingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(
            sinflar_menyusi()
        )
    )


# =========================
# 🎯 SONNI TOP O‘YINI
# =========================

async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    son = random.randint(1, 100)

    context.user_data["game_number"] = son
    context.user_data["game_attempts"] = 0

    keyboard = [
        [
            InlineKeyboardButton(
                "❌ O‘yinni to‘xtatish",
                callback_data="game_stop"
            )
        ]
    ]

    await query.edit_message_text(
        "🎯 SONNI TOP O‘YINI\n\n"
        "Men 1 dan 100 gacha bo‘lgan bitta son o‘yladim. 🤫\n\n"
        "Sonni yozib yuboring! 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def game_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "game_number" not in context.user_data:
        return

    text = update.message.text.strip()

    if not text.isdigit():

        await update.message.reply_text(
            "❗ Iltimos, 1 dan 100 gacha bo‘lgan son yozing."
        )

        return

    taxmin = int(text)

    if taxmin < 1 or taxmin > 100:

        await update.message.reply_text(
            "❗ Son 1 dan 100 gacha bo‘lishi kerak."
        )

        return

    context.user_data["game_attempts"] += 1

    son = context.user_data["game_number"]
    urinish = context.user_data["game_attempts"]

    if taxmin < son:

        await update.message.reply_text(
            f"🔼 Men o‘ylagan son bundan KATTA!\n\n"
            f"🎯 Urinish: {urinish}"
        )

    elif taxmin > son:

        await update.message.reply_text(
            f"🔽 Men o‘ylagan son bundan KICHIK!\n\n"
            f"🎯 Urinish: {urinish}"
        )

    else:

        if urinish <= 3:
            points = 30
        elif urinish <= 6:
            points = 20
        elif urinish <= 10:
            points = 10
        else:
            points = 5

        add_score(
            update.effective_user.id,
            points
        )

        await update.message.reply_text(
            f"🎉 TABRIKLAYMAN!\n\n"
            f"To‘g‘ri topdingiz! 🥳\n"
            f"🔢 Son: {son}\n"
            f"🎯 Urinishlar: {urinish}\n"
            f"⭐ Sizga +{points} ball berildi!\n\n"
            "🏆 Reytingni ko‘rish uchun /start bosing."
        )

        del context.user_data["game_number"]
        del context.user_data["game_attempts"]


async def game_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data.pop(
        "game_number",
        None
    )

    context.user_data.pop(
        "game_attempts",
        None
    )

    await query.edit_message_text(
        "❌ O‘yin to‘xtatildi.\n\n"
        "🎯 Yana o‘ynash uchun /start bosing."
    )


# =========================
# 🏆 REYTING
# =========================

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    rows = get_rating()

    if not rows:

        matn = (
            "🏆 REYTING\n\n"
            "Hozircha reytingda hech kim yo‘q."
        )

    else:

        lines = [
            "🏆 REYTING — TOP 10\n"
        ]

        medals = [
            "🥇",
            "🥈",
            "🥉"
        ]

        for i, row in enumerate(rows, start=1):

            name, sinf, score = row

            belgi = (
                medals[i - 1]
                if i <= 3
                else f"{i}️⃣"
            )

            lines.append(
                f"{belgi} {name} — {score} ball ({sinf}-sinf)"
            )

        matn = "\n".join(lines)

    user = get_user(
        update.effective_user.id
    )

    keyboard = []

    if user:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data=f"orqaga_{user[2]}"
                )
            ]
        )

    await query.edit_message_text(
        matn,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# RENDER PORT SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)
        self.end_headers()

        self.wfile.write(
            b"Bot is running"
        )

    def log_message(self, format, *args):
        pass


def run_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"Server {port}-portda ishga tushdi!"
    )

    server.serve_forever()


# =========================
# ASOSIY DASTUR
# =========================

def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            class_selected,
            pattern=r"^(1|2|3|4|5|6|7|8|9|10|11)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            dars_jadvali,
            pattern=r"^dars_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            kun_tanlandi,
            pattern=r"^kun_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            togaraklar,
            pattern=r"^togarak_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            back_to_class,
            pattern=r"^orqaga_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            change_class,
            pattern=r"^change$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            home,
            pattern=r"^home$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            rating,
            pattern=r"^rating$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            registration_name
        )
    )

    # 🎯 O‘YIN HANDLERLARI

    app.add_handler(
        CallbackQueryHandler(
            game_start,
            pattern=r"^game_start$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            game_stop,
            pattern=r"^game_stop$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            game_message
        )
    )

    print("Bot ishga tushdi!")

    app.run_polling()


# =========================
# ISHGA TUSHIRISH
# =========================

if __name__ == "__main__":

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    main()
