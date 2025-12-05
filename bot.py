import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "-1002879409912"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
links = {}

@dp.message()
async def handle_all(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        # Пользователь → админам
        user_info = {
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name
        }
        
        if message.photo:
            # Фото
            caption = message.caption or "📷 Фото"
            forwarded = await bot.send_photo(
                ADMIN_CHAT_ID,
                message.photo[-1].file_id,
                caption=f"{caption}\n\n👤 {message.from_user.full_name}"
            )
            links[forwarded.message_id] = user_info
            
        elif message.text:
            # Текст
            forwarded = await message.forward(ADMIN_CHAT_ID)
            links[forwarded.message_id] = user_info
            
        elif message.document:
            # Документ
            caption = message.caption or "📎 Документ"
            forwarded = await bot.send_document(
                ADMIN_CHAT_ID,
                message.document.file_id,
                caption=f"{caption}\n\n👤 {message.from_user.full_name}"
            )
            links[forwarded.message_id] = user_info
        
        await message.answer("✅ Отправлено админам")
        
        # Подсказка админам
        await bot.send_message(
            ADMIN_CHAT_ID,
            "💬 Ответьте на сообщение выше\n#отправить",
            reply_to_message_id=forwarded.message_id
        )
    
    elif message.reply_to_message:
        # Админ отвечает
        user_info = links.get(message.reply_to_message.message_id)
        if user_info:
            text = message.text or message.caption or ""
            
            if "#отправить" in text.lower():
                clean = text.replace('#отправить', '').strip()
                await bot.send_message(
                    user_info["user_id"],
                    f"📨 Ответ от администратора:\n{clean}"
                )
                await message.reply("✅ Отправлено")

# ========== ТОЛЬКО ВЕБХУК, НЕ POLLING! ==========
app = web.Application()
handler = SimpleRequestHandler(dp, bot)
handler.register(app, path="/webhook")

# Для проверки
async def home(request):
    return web.Response(text="✅ Бот работает через вебхук")

app.router.add_get('/', home)

async def main():
    port = int(os.getenv("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"✅ Сервер запущен на порту {port}")
    print("✅ Готов принимать вебхук запросы")
    print("✅ Сообщения будут пересылаться в группу админов")
    
    # БЕСКОНЕЧНОЕ ОЖИДАНИЕ - НЕ POLLING!
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

