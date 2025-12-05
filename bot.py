import os
import sys
import asyncio
import logging

# ВСЕГДА ПЕЧАТАТЬ ПЕРЕМЕННЫЕ
print("=" * 50)
print("🚀 Бот запускается...")
print(f"Python: {sys.version}")
print(f"Токен установлен: {'ДА' if os.getenv('BOT_TOKEN') else 'НЕТ'}")
print("=" * 50)

# Принудительно устанавливаем токен если нет переменной
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8287234268:AAGKxZay_fxm3_xQvGgQ0vE0gYB6UpjUPA8"
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID") or "-1002879409912")

print(f"Используем токен: {BOT_TOKEN[:10]}...")
print(f"Админ чат: {ADMIN_CHAT_ID}")

# Теперь импортируем aiogram
try:
    from aiogram import Bot, Dispatcher, types
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler
    from aiohttp import web
    print("✅ Модули загружены")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# ... остальной код без изменений ...

# Настройка логирования в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
links = {}

# Обработчик сообщений
@dp.message()
async def handle_message(message: types.Message):
    # Логируем ВСЁ
    logger.info(f"📩 От {message.from_user.id} ({message.from_user.full_name}): {message.text or message.content_type}")
    
    # Если сообщение от пользователя (не из группы админов)
    if message.chat.id != ADMIN_CHAT_ID:
        # Сохраняем информацию о пользователе
        user_info = {
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name
        }
        
        try:
            # Пересылаем в группу админов
            if message.text:
                forwarded = await message.forward(ADMIN_CHAT_ID)
                links[forwarded.message_id] = user_info
                
                # Добавляем подсказку для админов
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    f"💬 Ответьте на сообщение выше\n#отправить",
                    reply_to_message_id=forwarded.message_id
                )
                
            elif message.photo:
                # Фото с подписью
                caption = message.caption or "📷 Фото"
                forwarded = await bot.send_photo(
                    ADMIN_CHAT_ID,
                    message.photo[-1].file_id,
                    caption=f"{caption}\n\n👤 {message.from_user.full_name}"
                )
                links[forwarded.message_id] = user_info
                
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    f"💬 Ответьте на фото выше\n#отправить",
                    reply_to_message_id=forwarded.message_id
                )
            
            # Отвечаем пользователю
            await message.answer("✅ Сообщение передано администраторам")
            logger.info(f"✅ Переслано в группу")
            
        except Exception as e:
            logger.error(f"❌ Ошибка пересылки: {e}")
            await message.answer("⚠️ Ошибка, попробуйте позже")
    
    # Если сообщение из группы админов И это ответ на сообщение пользователя
    elif message.reply_to_message:
        user_info = links.get(message.reply_to_message.message_id)
        
        if user_info:
            text = message.text or message.caption or ""
            
            # Если есть #отправить - отправляем пользователю
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
                    logger.info(f"✅ Ответ отправлен пользователю {user_info['user_id']}")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки ответа: {e}")
                    await message.reply(f"❌ Ошибка: {str(e)[:100]}")
            else:
                # Без #отправить - черновик
                await message.reply("💭 Черновик сохранён (добавьте #отправить для отправки)")

# Создаём веб-приложение
app = web.Application()

# Регистрируем обработчик вебхука
webhook_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
    handle_in_background=False  # для отладки
)
webhook_handler.register(app, path="/webhook")

# Простой эндпоинт для проверки работы
async def home_handler(request):
    return web.Response(text="✅ Telegram Bot работает!\nВебхук: /webhook")

async def health_handler(request):
    return web.Response(text="OK")

app.router.add_get('/', home_handler)
app.router.add_get('/health', health_handler)

# Главная функция
async def main():
    # Запускаем сервер
    port = int(os.getenv("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info("=" * 50)
    logger.info("🤖 БОТ ЗАПУЩЕН")
    logger.info(f"🌐 Порт: {port}")
    logger.info(f"👥 Админ группа: {ADMIN_CHAT_ID}")
    logger.info(f"🔗 Доступен по: https://ваш-проект.up.railway.app")
    logger.info("=" * 50)
    
    # Бесконечное ожидание
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())






