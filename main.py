import asyncio
import json
from fastapi import FastAPI, HTTPException
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, ADMIN_ID
from database import init_db, get_user, create_user, get_top_coins, get_top_creators, get_global_var, get_user_balance, get_user_tokens, buy_token, sell_token, create_coin
from middlewares.reaction_middleware import ReactionMiddleware
from handlers.casino_games import router as casino_router
from handlers.shop_effects import router as shop_router
from handlers.economy_admin import router as admin_router
from handlers.market_logic import router as market_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Set logging
logging.basicConfig(level=logging.INFO)

# FastAPI app for web app API
app = FastAPI()

@app.get("/api/user/{user_id}")
async def get_user_data(user_id: int):
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    balance = await get_user_balance(user_id)
    tokens = await get_user_tokens(user_id)
    return {"balance": balance, "tokens": tokens}

@app.post("/api/command")
async def process_command(data: dict):
    user_id = data.get("user_id")
    command = data.get("command")
    # Simulate processing (integrate with handlers later)
    return {"response": f"Processed: {command}"}

async def morning_report(bot: Bot):
    # Send to a channel or admin, for now to admin
    top_coins = await get_top_coins(3)
    top_creators = await get_top_creators(3)
    bot_balance = await get_global_var('bot_balance')
    
    text = "🌅 Morning Market Report:\n\n"
    text += "Top Coins by Volume:\n"
    for ticker, volume in top_coins:
        text += f"${ticker}: {volume:.2f}\n"
    
    text += "\nTop Creators by Royalties:\n"
    for id, username, royalties in top_creators:
        text += f"@{username}: {royalties:.2f}\n"
    
    text += f"\nBot Treasury: {bot_balance} coins"
    
    await bot.send_message(chat_id=ADMIN_ID, text=text)

async def main():
    print("Initializing bot...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Init db
    await init_db()
    print("Database initialized.")
    
    # Add middleware
    dp.message.middleware(ReactionMiddleware())
    
    # Include routers
    dp.include_router(casino_router)
    dp.include_router(shop_router)
    dp.include_router(admin_router)
    dp.include_router(market_router)
    
    # Debug: log all messages
    # @dp.message()
    # async def log_message(message: Message):
    #     print(f"Received message: {message.text} from {message.from_user.username} in chat {message.chat.id}")
    
    @dp.message(F.text == "/test")
    async def cmd_test(message: Message):
        await message.reply("Bot is working!")
    
    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Відкрити Mini-App", web_app=WebAppInfo(url="https://your-domain.com/web_app/index.html"))]
        ])
        await message.reply("Привіт! Я Crypto-Tycoon & Casino бот. Натисніть кнопку нижче, щоб відкрити mini-app.", reply_markup=keyboard)
    
    @dp.message(F.web_app_data)
    async def handle_web_app_data(message: Message):
        data = message.web_app_data.data
        try:
            payload = json.loads(data)
            action = payload.get('action')
            user_id = payload.get('user_id')
            username = payload.get('username')
            
            # Process the action
            if action == 'command':
                command = payload.get('command')
                # Simulate processing the command
                response = f"Оброблено команду: {command} від {username}"
                await message.reply(response)
            else:
                await message.reply("Невідома дія")
        except json.JSONDecodeError:
            await message.reply("Помилка обробки даних")
    
    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(morning_report, CronTrigger(hour=9), args=[bot])
    scheduler.start()
    
    print("Bot started! Press Ctrl+C to stop.")
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    import uvicorn
    # Run bot in asyncio
    asyncio.run(main())
    # For API, run separately: uvicorn main:app --host 0.0.0.0 --port 8001