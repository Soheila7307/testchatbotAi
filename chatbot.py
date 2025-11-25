import os
import asyncio
import aiohttp
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# لاگ کامل رو فعال می‌کنیم
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن‌ها از محیط
TELEGRAM_BOT_TOKEN = os.getenv("8153352792:AAG-62yVYD3jdEQDmZ-EyoOXLUWBAWEvgmk")
OPENROUTER_API_KEY = os.getenv("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")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"

if not TELEGRAM_BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("توکن تلگرام یا OpenRouter پیدا نشد! چک کن Variables درست باشه")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! بات الان آنلاینه و با OpenRouter کار می‌کنه 🚀\nهر چی بپرسی جواب می‌دم.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    sent = await update.message.reply_text("در حال فکر کردن... ▌")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://github.com",
                    "X-Title": "Telegram Bot",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": user_message}],
                    "stream": True
                },
                timeout=60
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    await sent.edit_text(f"خطای OpenRouter: {resp.status}\n{error}")
                    return

                full = ""
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]": break
                        try:
                            import json
                            delta = json.loads(chunk)["choices"][0]["delta"].get("content", "")
                            full += delta
                            if len(full) % 5 == 0:  # هر چند کاراکتر آپدیت کن
                                await sent.edit_text(full + "▌")
                        except: continue
                await sent.edit_text(full or "جوابی دریافت نشد 😔")

    except Exception as e:
        logger.error(f"خطا: {e}", exc_info=True)
        await sent.edit_text(f"خطای داخلی: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    print("بات در حال اجراست...")
    app.run_polling(drop_pending_updates=True)  # این خط مهمه! آپدیت‌های قدیمی رو دور می‌ریزه

if __name__ == "__main__":
    main()
