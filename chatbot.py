import os
import asyncio
import aiohttp
from telegram import Update
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# توکن‌ها رو اینجا بذار یا از محیط (توصیه می‌شه)
TELEGRAM_BOT_TOKEN = "8153352792:AAG-62yVYD3jdEQDmZ-EyoOXLUWBAWEvgmk"
OPENROUTER_API_KEY = "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"

# مدل دلخواه در OpenRouter (اینجا چندتا از بهترین‌های رایگان/ارزان رو گذاشتم)
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"   # رایگان و سریع
# یا مثلاً:
# "meta-llama/llama-3.1-70b-instruct"
# "openrouter/openchat-3.5"
# "google/gemma-2-27b-it"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من یه بات Zero-Shot هستم که با OpenRouter کار می‌کنم.\n"
        "هر سوالی داری بپرس، سریع جواب می‌دم 😊"
    )

async def chat_with_openrouter(message: str, chat_id: int, message_id: int, context: ContextTypes.DEFAULT_TYPE):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://yourdomain.com",  # اختیاری ولی بهتره بذاری
        "X-Title": "Telegram Bot",                 # اختیاری
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": message}],
        "stream": True  # برای استریم فعال باشه
    }

    full_response = ""
    last_sent_length = 0

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status != 200:
                error = await resp.text()
                await context.bot.send_message(chat_id, text=f"خطا: {resp.status}\n{error}")
                return

            async for line in resp.content:
                if line:
                    decoded = line.decode('utf-8').strip()
                    if decoded.startswith("data: "):
                        chunk = decoded[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            import json
                            json_chunk = json.loads(chunk)
                            delta = json_chunk["choices"][0]["delta"].get("content", "")
                            full_response += delta

                            # هر ۲-۳ کاراکتر یه بار آپدیت می‌کنیم (برای جلوگیری از فلود)
                            if len(full_response) - last_sent_length >= 3:
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    text=full_response + "▌",  # نشانگر تایپ
                                    parse_mode="HTML"
                                )
                                last_sent_length = len(full_response)
                        except Exception as e:
                            continue

    # پاسخ نهایی بدون نشانگر
    if full_response.strip():
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=full_response.strip(),
            parse_mode="Markdown"
        )
    else:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="متأسفانه جوابی دریافت نشد 😔"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    if not user_message:
        return

    # اول یه پیام "در حال تایپ..." می‌فرستیم
    sent_message = await update.message.reply_text("▌")

    # حالا درخواست به OpenRouter
    await chat_with_openrouter(
        message=user_message,
        chat_id=update.effective_chat.id,
        message_id=sent_message.message_id,
        context=context
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("بات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()