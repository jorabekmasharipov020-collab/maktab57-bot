from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not TOKEN:
    raise ValueError("BOT_TOKEN Render Environment Variables'da topilmadi!")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY Render Environment Variables'da topilmadi!")
client = OpenAI(api_key=OPENAI_API_KEY)
def sinflar_menyusi():
    return [
        [InlineKeyboardButton("1️⃣ 1-sinf", callback_data="1"), InlineKeyboardButton("2️⃣ 2-sinf", callback_data="2")],
        [InlineKeyboardButton("3️⃣ 3-sinf", callback_data="3"), InlineKeyboardButton("4️⃣ 4-sinf", callback_data="4")],
        [InlineKeyboardButton("5️⃣ 5-sinf", callback_data="5"), InlineKeyboardButton("6️⃣ 6-sinf", callback_data="6")],
        [InlineKeyboardButton("7️⃣ 7-sinf", callback_data="7"), InlineKeyboardButton("8️⃣ 8-sinf", callback_data="8")],
        [InlineKeyboardButton("9️⃣ 9-sinf", callback_data="9"), InlineKeyboardButton("🔟 10-sinf", callback_data="10")],
        [InlineKeyboardButton("1️⃣1️⃣ 11-sinf", callback_data="11")]
    ]
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏫 Maktab 57 botiga xush kelibsiz!\n\nSinfingizni tanlang:", reply_markup=InlineKeyboardMarkup(sinflar_menyusi()))
async def class_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sinf = query.data
    context.user_data["sinf"] = sinf
    keyboard = [
        [InlineKeyboardButton("📚 Dars jadvali", callback_data=f"dars_{sinf}")],
        [InlineKeyboardButton("🏆 To‘garaklar", callback_data=f"togarak_{sinf}")],
        [InlineKeyboardButton("🤖 AI yordamchi", callback_data="ai_start")],
        [InlineKeyboardButton("🌐 Kundalik.com", url="https://kundalik.com")],
        [InlineKeyboardButton("🔄 Sinfni almashtirish", callback_data="change")]
    ]
    await query.edit_message_text(f"✅ Siz {sinf}-sinfni tanladingiz!\n\nKerakli bo‘limni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
async def ai_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ai_mode"] = True
    keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="ai_back")]]
    await query.edit_message_text("🤖 AI YORDAMCHI\n\nSavolingizni yozing.\n\nMasalan:\n🧮 2x + 5 = 15 ni yech\n📚 Fotosintez nima?\n🇬🇧 Ingliz tilidan yordam ber\n🌍 O‘zbekiston tarixi haqida ayt", reply_markup=InlineKeyboardMarkup(keyboard))
async def ai_yordamchi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if not context.user_data.get("ai_mode"):
        return
    savol = update.message.text
    try:
        await update.message.reply_text("🤖 AI o‘ylayapti...")
        response = client.responses.create(
            model="gpt-5.4-mini",
            instructions="Sen Maktab 57 maktab botining AI yordamchisisan. O‘zbek tilida sodda, tushunarli va qisqa javob ber. O‘quvchilarga matematika, fizika, kimyo, biologiya, tarix, ona tili, adabiyot, ingliz tili va boshqa maktab fanlarida yordam ber. Masalalarda imkon qadar ishlanishini ham ko‘rsat.",
            input=savol
        )
        javob = response.output_text
        if not javob:
            javob = "❌ AI javob qaytara olmadi."
        await update.message.reply_text("🤖 AI:\n\n" + javob)
    except Exception as e:
        print("AI XATOSI:", e)
        await update.message.reply_text("❌ AI bilan bog‘lanishda xatolik yuz berdi.\n\nKeyinroq yana urinib ko‘ring.")
async def ai_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ai_mode"] = False
    sinf = context.user_data.get("sinf", "11")
    keyboard = [
        [InlineKeyboardButton("📚 Dars jadvali", callback_data=f"dars_{sinf}")],
        [InlineKeyboardButton("🏆 To‘garaklar", callback_data=f"togarak_{sinf}")],
        [InlineKeyboardButton("🤖 AI yordamchi", callback_data="ai_start")],
        [InlineKeyboardButton("🌐 Kundalik.com", url="https://kundalik.com")],
        [InlineKeyboardButton("🔄 Sinfni almashtirish", callback_data="change")]
    ]
    await query.edit_message_text(f"✅ Siz {sinf}-sinfni tanladingiz!\n\nKerakli bo‘limni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
async def dars_jadvali(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sinf = query.data.replace("dars_", "")
    context.user_data["sinf"] = sinf
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
        await query.edit_message_text("📚 11-SINF DARS JADVALI\n\nHaftaning kunini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data=f"orqaga_{sinf}")]]
        await query.edit_message_text(f"📚 {sinf}-sinf dars jadvali\n\n⏳ Bu sinf uchun jadval hali qo‘shilmagan.", reply_markup=InlineKeyboardMarkup(keyboard))
JADVAL = {
    "kun_dushanba": "📅 DUSHANBA\n\n1. Sinf soati\n2. Fizika\n3. Informatika / Qoraqalpoq tili\n4. Algebra\n5. Rus tili\n6. CHQBT",
    "kun_seshanba": "📅 SESHANBA\n\n1. Algebra\n2. Kimyo\n3. DHA\n4. Biologiya\n5. Jismoniy tarbiya",
    "kun_chorshanba": "📅 CHORSHANBA\n\n1. Ingliz tili\n2. CHQBT\n3. Adabiyot\n4. O‘zbekiston tarixi / Qoraqalpog‘iston tarixi\n5. Algebra",
    "kun_payshanba": "📅 PAYSHANBA\n\n1. Ingliz tili\n2. Ona tili\n3. Biologiya\n4. Fizika\n5. Qoraqalpog‘iston tili\n6. Jismoniy tarbiya",
    "kun_juma": "📅 JUMA\n\n1. Geometriya\n2. Rus tili\n3. Tadbirkorlik asoslari\n4. Astronomiya\n5. Tarbiya",
    "kun_shanba": "📅 SHANBA\n\n1. Geometriya\n2. Kimyo\n3. Adabiyot\n4. Informatika\n5. Jahon tarixi"
}
async def kun_tanlandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    matn = JADVAL.get(query.data, "❌ Bu kun uchun jadval topilmadi.")
    keyboard = [
        [InlineKeyboardButton("⬅️ Kunlarga qaytish", callback_data="dars_11")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")]
    ]
    await query.edit_message_text(matn, reply_markup=InlineKeyboardMarkup(keyboard))
async def togaraklar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sinf = query.data.replace("togarak_", "")
    context.user_data["sinf"] = sinf
    keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data=f"orqaga_{sinf}")]]
    await query.edit_message_text(f"🏆 {sinf}-SINF TO‘GARAKLARI\n\n⏳ To‘garaklar ma’lumotlari tez orada qo‘shiladi.\n\nBu bo‘limga to‘garak nomi, hafta kuni va vaqti kiritiladi.", reply_markup=InlineKeyboardMarkup(keyboard))
async def back_to_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sinf = query.data.replace("orqaga_", "")
    context.user_data["sinf"] = sinf
    keyboard = [
        [InlineKeyboardButton("📚 Dars jadvali", callback_data=f"dars_{sinf}")],
        [InlineKeyboardButton("🏆 To‘garaklar", callback_data=f"togarak_{sinf}")],
        [InlineKeyboardButton("🤖 AI yordamchi", callback_data="ai_start")],
        [InlineKeyboardButton("🌐 Kundalik.com", url="https://kundalik.com")],
        [InlineKeyboardButton("🔄 Sinfni almashtirish", callback_data="change")]
    ]
    await query.edit_message_text(f"✅ Siz {sinf}-sinfni tanladingiz!\n\nKerakli bo‘limni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
async def change_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ai_mode"] = False
    await query.edit_message_text("🏫 Sinfingizni tanlang:", reply_markup=InlineKeyboardMarkup(sinflar_menyusi()))
async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ai_mode"] = False
    await query.edit_message_text("🏫 Maktab 57 botiga xush kelibsiz!\n\nSinfingizni tanlang:", reply_markup=InlineKeyboardMarkup(sinflar_menyusi()))
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def log_message(self, format, *args):
        pass
def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Server {port}-portda ishga tushdi!")
    server.serve_forever()
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(class_selected, pattern=r"^(1|2|3|4|5|6|7|8|9|10|11)$"))
    app.add_handler(CallbackQueryHandler(ai_start, pattern=r"^ai_start$"))
    app.add_handler(CallbackQueryHandler(ai_back, pattern=r"^ai_back$"))
    app.add_handler(CallbackQueryHandler(dars_jadvali, pattern=r"^dars_"))
    app.add_handler(CallbackQueryHandler(kun_tanlandi, pattern=r"^kun_"))
    app.add_handler(CallbackQueryHandler(togaraklar, pattern=r"^togarak_"))
    app.add_handler(CallbackQueryHandler(back_to_class, pattern=r"^orqaga_"))
    app.add_handler(CallbackQueryHandler(change_class, pattern=r"^change$"))
    app.add_handler(CallbackQueryHandler(home, pattern=r"^home$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_yordamchi))
    print("Bot ishga tushdi!")
    app.run_polling()
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    main()
