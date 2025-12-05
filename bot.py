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
ADMIN_CHAT_ID = -1002879409912

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
links = {}

@dp.message()
async def handle_message(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        logger.info(f"От {message.from_user.full_name}: {message.text}")
        
        # Пересылаем в группу
        if message.text:
            forwarded = await message.forward(ADMIN_CHAT_ID)
            links[forwarded.message_id] = message.from_user.id
            
            # Подсказка
            await bot.send_message(
                ADMIN_CHAT_ID,
                "💬 Ответьте на сообщение выше\n#отправить",
                reply_to_message_id=forwarded.message_id
            )
            
            await message.answer("✅ Отправлено админам")

# Кастомный обработчик с отладкой
class DebugRequestHandler(SimpleRequestHandler):
    async def _handle_request(self, bot, request):
        try:
            # Логируем входящий запрос
            body = await request.text()
            logger.info(f"📨 Входящий запрос ({len(body)} байт)")
            
            if not body or body.strip() == '':
                logger.warning("⚠️ Пустое тело запроса")
                return web.Response(text='Empty body', status=400)
            
            # Пробуем распарсить JSON
            try:
                data = json.loads(body)
                logger.info(f"📊 JSON валиден, update_id: {data.get('update_id', 'none')}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Невалидный JSON: {e}")
                logger.error(f"   Тело: {body[:200]}")
                return web.Response(text='Invalid JSON', status=400)
            
            # Обрабатываем через родительский класс
            return await super()._handle_request(bot, request)
            
        except Exception as e:
            logger.error(f"🔥 Необработанная ошибка: {e}")
            return web.Response(text='Server Error', status=500)

# Веб-приложение
app = web.Application()

# Используем кастомный обработчик
handler = DebugRequestHandler(
    dispatcher=dp,
    bot=bot,
    handle_in_background=False
)
handler.register(app, path="/webhook")

# Корневой URL
async def home_handler(request):
    return web.Response(text="✅ Бот работает")

app.router.add_get('/', home_handler)

# Запуск
async def main():
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info(f"✅ Сервер запущен на порту {port}")
    logger.info("✅ Ожидаю вебхук запросы")
    
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
