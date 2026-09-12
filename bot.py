from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8987242329:AAE__C8u4VqomL6YwHkF7Zvg4oolM0GVzrQ"


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ 1-sinf", callback_data="1"),
         InlineKeyboardButton("2️⃣ 2-sinf", callback_data="2")],

        [InlineKeyboardButton("3️⃣ 3-sinf", callback_data="3"),
         InlineKeyboardButton("4️⃣ 4-sinf", callback_data="4")],

        [InlineKeyboardButton("5️⃣ 5-sinf", callback_data="5"),
         InlineKeyboardButton("6️⃣ 6-sinf", callback_data="6")],

        [InlineKeyboardButton("7️⃣ 7-sinf", callback_data="7"),
         InlineKeyboardButton("8️⃣ 8-sinf", callback_data="8")],

        [InlineKeyboardButton("9️⃣ 9-sinf", callback_data="9"),
         InlineKeyboardButton("🔟 10-sinf", callback_data="10")],

        [InlineKeyboardButton("1️⃣1️⃣ 11-sinf", callback_data="11")]
    ]

    await update.message.reply_text(
        "🏫 Maktab 57 botiga xush kelibsiz!\n\n"
        "Sinfingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# SINF TANLASH
# =========================
async def class_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sinf = query.data

    keyboard = [
        [InlineKeyboardButton(
            "📚 Dars jadvali",
            callback_data=f"dars_{sinf}"
        )],

        [InlineKeyboardButton(
            "📝 Uy vazifasi",
            callback_data=f"vazifa_{sinf}"
        )],

        [InlineKeyboardButton(
            "📢 E'lonlar",
            callback_data="elonlar"
        )],

        [InlineKeyboardButton(
            "📅 Tadbirlar",
            callback_data="tadbirlar"
        )],

        [InlineKeyboardButton(
            "🔄 Sinfni almashtirish",
            callback_data="change"
        )]
    ]

    await query.edit_message_text(
        f"✅ Siz {sinf}-sinfni tanladingiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# DARS JADVALI
# =========================
async def dars_jadvali(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sinf = query.data.replace("dars_", "")

    # Hozircha faqat 11-sinf
    if sinf == "11":
        keyboard = [
            [InlineKeyboardButton("📅 Dushanba", callback_data="kun_dushanba")],
            [InlineKeyboardButton("📅 Seshanba", callback_data="kun_seshanba")],
            [InlineKeyboardButton("📅 Chorshanba", callback_data="kun_chorshanba")],
            [InlineKeyboardButton("📅 Payshanba", callback_data="kun_payshanba")],
            [InlineKeyboardButton("📅 Juma", callback_data="kun_juma")],
            [InlineKeyboardButton("📅 Shanba", callback_data="kun_shanba")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="orqaga_11")]
        ]

        await query.edit_message_text(
            "📚 11-SINF DARS JADVALI\n\n"
            "Haftaning kunini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        await query.edit_message_text(
            f"📚 {sinf}-sinf dars jadvali\n\n"
            "⏳ Bu sinf uchun jadval hali qo‘shilmagan."
        )


# =========================
# KUNLAR VA FANLAR
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
# KUN BOSILGANDA
# =========================
async def kun_tanlandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    matn = JADVAL.get(query.data)

    keyboard = [
        [InlineKeyboardButton(
            "⬅️ Kunlarga qaytish",
            callback_data="dars_11"
        )],

        [InlineKeyboardButton(
            "🏠 Bosh menyu",
            callback_data="home"
        )]
    ]

    await query.edit_message_text(
        matn,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ORQAGA
# =========================
async def back_to_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📚 Dars jadvali", callback_data="dars_11")],
        [InlineKeyboardButton("📝 Uy vazifasi", callback_data="vazifa_11")],
        [InlineKeyboardButton("📢 E'lonlar", callback_data="elonlar")],
        [InlineKeyboardButton("📅 Tadbirlar", callback_data="tadbirlar")],
        [InlineKeyboardButton("🔄 Sinfni almashtirish", callback_data="change")]
    ]

    await query.edit_message_text(
        "✅ Siz 11-sinfni tanladingiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ASOSIY DASTUR
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Sinf tanlash
    app.add_handler(
        CallbackQueryHandler(
            class_selected,
            pattern=r"^(1|2|3|4|5|6|7|8|9|10|11)$"
        )
    )

    # Dars jadvali tugmasi
    app.add_handler(
        CallbackQueryHandler(
            dars_jadvali,
            pattern=r"^dars_"
        )
    )

    # Haftaning kunlari
    app.add_handler(
        CallbackQueryHandler(
            kun_tanlandi,
            pattern=r"^kun_"
        )
    )

    # Orqaga
    app.add_handler(
        CallbackQueryHandler(
            back_to_class,
            pattern=r"^orqaga_11$"
        )
    )

    print("Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()