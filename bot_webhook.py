import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "8287234268:AAGKxZay_fxm3_xQvGgQ0vE0gYB6UpjUPA8")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "-1002879409912"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")  # Будет задано на сервере
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь для связи сообщений
links = {}  # {admin_message_id: {"user_id": int, "user_name": str}}

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 Напишите сообщение, и я передам его админам")

@dp.message(Command("status"))
async def status(message: types.Message):
    """Проверка статуса бота"""
    if message.chat.id == ADMIN_CHAT_ID:
        mode = "Вебхук" if WEBHOOK_URL else "Polling"
        await message.answer(f"✅ Бот работает\nРежим: {mode}\nСообщений в памяти: {len(links)}")

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
@dp.message()
async def handle_all_messages(message: types.Message):
    """Обработка всех сообщений"""
    
    # 1. Сообщение от пользователя (не из группы админов)
    if message.chat.id != ADMIN_CHAT_ID:
        await handle_user_message(message)
    
    # 2. Сообщение из группы админов
    else:
        await handle_admin_message(message)

async def handle_user_message(message: types.Message):
    """Обработка сообщений от пользователей"""
    try:
        # Отвечаем пользователю
        await message.answer("✅ Сообщение передано администраторам")
        
        user_info = {
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name
        }
        
        # Пересылаем в группу админов
        if message.photo:
            # Фото с подписью или без
            caption = message.caption or "📷 Фото"
            forwarded_msg = await bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=f"{caption}\n\n👤 От: {message.from_user.full_name}"
            )
            
        elif message.text:
            # Текстовое сообщение
            forwarded_msg = await bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            
        elif message.document:
            # Документ
            caption = message.caption or "📎 Документ"
            forwarded_msg = await bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=message.document.file_id,
                caption=f"{caption}\n\n👤 От: {message.from_user.full_name}"
            )
            
        else:
            # Другие типы
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"👤 {message.from_user.full_name} отправил {message.content_type}"
            )
            return
        
        # Сохраняем связь
        links[forwarded_msg.message_id] = user_info
        
        # Добавляем подсказку для админов
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"💬 Ответьте на сообщение выше\n"
                 f"Чтобы отправить ответ, добавьте #отправить",
            reply_to_message_id=forwarded_msg.message_id
        )
        
        logger.info(f"Сообщение от {user_info['user_name']} переслано в группу")
        
    except Exception as e:
        logger.error(f"Ошибка пересылки: {e}")
        await message.answer("⚠️ Ошибка при отправке")
async def handle_admin_message(message: types.Message):
    """Обработка сообщений от админов в группе"""
    # Проверяем, что это reply на сообщение пользователя
    if message.reply_to_message:
        original_msg_id = message.reply_to_message.message_id
        
        # Ищем информацию о пользователе
        user_info = links.get(original_msg_id)
        
        if user_info:
            user_id = user_info["user_id"]
            user_name = user_info["user_name"]
            
            # Получаем текст ответа (из текста или подписи)
            reply_text = ""
            
            if message.text:
                reply_text = message.text
            elif message.caption:
                reply_text = message.caption
            
            # Проверяем наличие #отправить
            if reply_text and "#отправить" in reply_text.lower():
                # ОТПРАВЛЯЕМ ПОЛЬЗОВАТЕЛЮ
                clean_text = reply_text.replace('#отправить', '').replace('#ОТПРАВИТЬ', '').strip()
                
                try:
                    if message.photo:
                        # Фото с подписью
                        await bot.send_photo(
                            chat_id=user_id,
                            photo=message.photo[-1].file_id,
                            caption=f"📨 Ответ от администратора:\n{clean_text}"
                        )
                        await message.reply(f"✅ Фото отправлено {user_name}")
                    
                    elif message.text:
                        # Текст
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"📨 Ответ от администратора:\n\n{clean_text}",
                            parse_mode=ParseMode.HTML
                        )
                        await message.reply(f"✅ Текст отправлен {user_name}")
                    
                    elif message.document:
                        # Документ
                        await bot.send_document(
                            chat_id=user_id,
                            document=message.document.file_id,
                            caption=f"📨 Ответ от администратора:\n{clean_text}"
                        )
                        await message.reply(f"✅ Документ отправлен {user_name}")
                    
                    logger.info(f"Ответ отправлен пользователю {user_name}")
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки: {e}")
                    await message.reply(f"❌ Ошибка: {str(e)[:100]}")
            
            else:
                # Без #отправить - просто комментируем в группе
                if reply_text:
                    await message.reply("💭 Черновик (добавьте #отправить для отправки)")

# ========== ВЕБХУК НАСТРОЙКИ ==========
async def on_startup(bot: Bot):
    """Устанавливаем вебхук при запуске"""
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")
    else:
        logger.warning("WEBHOOK_URL не задан, используется polling")

async def on_shutdown(bot: Bot):
    """Удаляем вебхук при выключении"""
    if WEBHOOK_URL:
        await bot.delete_webhook()
    await bot.session.close()
    logger.info("Бот остановлен")

# ========== ЗАПУСК ==========
async def main_webhook():
    """Запуск в режиме вебхука (для сервера)"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Создаем aiohttp приложение
    app = web.Application()
    
    # Создаем обработчик вебхука
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    
    # Регистрируем путь /webhook
    webhook_handler.register(app, path=WEBHOOK_PATH)
    
    # Запускаем на порту из переменных окружения
    port = int(os.getenv("PORT", 3000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logger.info(f"🌐 Сервер запущен на порту {port}")
    await site.start()
    
    # Бесконечное ожидание
    await asyncio.Future()

async def main_polling():
    """Запуск в режиме polling (для локального теста)"""
    logger.info("🤖 Запуск в режиме polling...")
    await dp.start_polling(bot)

# ========== ВЫБОР РЕЖИМА ==========
if __name__ == "__main__":
    # Определяем режим запуска
    mode = os.getenv("MODE", "webhook")  # по умолчанию вебхук
    
    if mode == "webhook" and WEBHOOK_URL:
        asyncio.run(main_webhook())
    else:
        asyncio.run(main_polling())