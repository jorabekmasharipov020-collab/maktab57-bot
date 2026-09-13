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
if name == "main":
    threading.Thread(target=run_server, daemon=True).start()
    main()
