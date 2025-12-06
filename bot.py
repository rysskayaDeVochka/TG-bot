import os
import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8287234268:AAGKxZay_fxm3_xQvGgQ0vE0gYB6UpjUPA8"
ADMIN_CHAT_ID = -4107322998

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
links = {}  # {admin_message_id: {"user_id": int, "user_name": str}}

@dp.message()
async def handle_all_messages(message: types.Message):
    # Сообщение от пользователя
    if message.chat.id != ADMIN_CHAT_ID:
        user_info = {
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name
        }
        
        logger.info(f"📩 От {user_info['user_name']}: {message.text or message.content_type}")
        
        try:
            # Пересылаем в группу
            if message.photo:
                forwarded = await bot.send_photo(
                    ADMIN_CHAT_ID,
                    message.photo[-1].file_id,
                    caption=f"{message.caption or '📷 Фото'}\n\n👤 {user_info['user_name']}"
                )
            elif message.text:
                forwarded = await message.forward(ADMIN_CHAT_ID)
            elif message.document:
                forwarded = await bot.send_document(
                    ADMIN_CHAT_ID,
                    message.document.file_id,
                    caption=f"{message.caption or '📎 Документ'}\n\n👤 {user_info['user_name']}"
                )
            else:
                return
            
            # Сохраняем связь
            links[forwarded.message_id] = user_info
            
            # Подсказка админам
            await bot.send_message(
                ADMIN_CHAT_ID,
                "💬 Ответьте на сообщение выше\nЧтобы отправить ответ, добавьте #отправить",
                reply_to_message_id=forwarded.message_id
            )
            
            await message.answer("✅ Сообщение передано администраторам")
            logger.info(f"✅ Переслано в группу")
            
        except Exception as e:
            logger.error(f"❌ Ошибка пересылки: {e}")
    
    # Ответ админа
    elif message.reply_to_message:
        user_info = links.get(message.reply_to_message.message_id)
        
        if user_info:
            text = message.text or message.caption or ""
            
            if "#отправить" in text.lower():
                clean_text = text.replace('#отправить', '').replace('#ОТПРАВИТЬ', '').strip()
                
                try:
                    if message.photo:
                        await bot.send_photo(
                            user_info["user_id"],
                            message.photo[-1].file_id,
                            caption=f"📨 Ответ от администратора:\n{clean_text}"
                        )
                    else:
                        await bot.send_message(
                            user_info["user_id"],
                            f"📨 Ответ от администратора:\n\n{clean_text}"
                        )
                    
                    await message.reply(f"✅ Ответ отправлен {user_info['user_name']}")
                    logger.info(f"✅ Ответ отправлен пользователю")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки ответа: {e}")

# Веб-приложение
app = web.Application()
handler = SimpleRequestHandler(dp, bot)
handler.register(app, path="/webhook")

async def home_handler(request):
    return web.Response(text="✅ Telegram Bot работает!")

app.router.add_get('/', home_handler)

# Запуск
async def main():
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info("=" * 50)
    logger.info("🤖 БОТ ЗАПУЩЕН И РАБОТАЕТ")
    
    logger.info(f"🌐 URL: https://tg-bot-production-5047.up.railway.app")
    logger.info(f"👥 Админ группа: {ADMIN_CHAT_ID}")
    logger.info("=" * 50)
    
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())


