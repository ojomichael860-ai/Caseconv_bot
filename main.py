import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- Web Server for Render Health Checks ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Case Converter Engine is Active!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

# --- Bot Command and Message Routing ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔤 **Welcome to the AI Case Converter Bot!**\n\n"
        "Send me any text, sentence, or block of copy, and I will instantly help you "
        "convert it into Uppercase, Lowercase, Title Case, or Sentence Case!\n\n"
        "👉 *Type or paste your text below to begin:*",
        parse_mode="Markdown"
    )

async def handle_incoming_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if not user_text.strip():
        return

    # Temporary storage mapping using the chat context instance 
    context.user_data["active_text"] = user_text

    # Build an interactive selection menu panel
    keyboard = [
        [
            InlineKeyboardButton("✨ UPPERCASE", callback_data="case_upper"),
            InlineKeyboardButton("✨ lowercase", callback_data="case_lower")
        ],
        [
            InlineKeyboardButton("✨ Title Case", callback_data="case_title"),
            InlineKeyboardButton("✨ Sentence case", callback_data="case_sentence")
        ],
        [
            InlineKeyboardButton("🔄 Swap Case (aBc -> AbC)", callback_data="case_swap")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚡ **Select your desired conversion format layout below:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_case_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    original_text = context.user_data.get("active_text")
    if not original_text:
        await query.message.edit_text("⚠️ *Session expired.* Please paste your text string again.", parse_mode="Markdown")
        return

    action = query.data
    converted_text = ""

    # Execute text transformation profiles using native string methods
    if action == "case_upper":
        converted_text = original_text.upper()
        label = "UPPERCASE"
    elif action == "case_lower":
        converted_text = original_text.lower()
        label = "lowercase"
    elif action == "case_title":
        converted_text = original_text.title()
        label = "Title Case"
    elif action == "case_sentence":
        # Capitalizes only the first letter of the entire string block
        converted_text = original_text.capitalize()
        label = "Sentence Case"
    elif action == "case_swap":
        converted_text = original_text.swapcase()
        label = "Swapped Case"

    # Present results inside clear mono-spaced layout blocks for single-tap copying
    response_message = (
        f"✅ **Converted to {label}:**\n\n"
        f"`{converted_text}`\n\n"
        f"💡 *Tip: Tap the text block above to copy it instantly.*"
    )

    await query.message.edit_text(text=response_message, parse_mode="Markdown")

async def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("Missing TELEGRAM_TOKEN environment target variable.")

    # Start the background port service routing for Render
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_text))
    app.add_handler(CallbackQueryHandler(handle_case_conversion))
    
    print("Case conversion bot polling cycle active...")
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
