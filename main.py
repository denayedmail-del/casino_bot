import asyncio
import json
from fastapi import FastAPI, HTTPException
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, ADMIN_ID
from database import get_balance, update_balance, create_coin, get_coin, get_coin_price, add_to_inventory, remove_from_inventory, add_transaction, update_coin_supply, update_coin_volume, update_royalties, get_user_tokens, get_top_users, get_top_creators, get_top_coins, get_address, get_user_by_username, get_global_var, set_global_var, get_user_balance, get_user_tokens, buy_token, sell_token, create_coin
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

# Helper functions for actions
async def perform_buy(user_id, ticker, amount):
    coin = await get_coin(ticker)
    if not coin:
        return "Токен не знайдено"
    
    price = await get_coin_price(ticker)
    total_cost = price * Decimal(str(amount))
    
    bal = await get_balance(user_id)
    if bal < float(total_cost):
        return "Недостатньо коштів"
    
    # Update supply
    new_supply = Decimal(str(coin[3])) + Decimal(str(amount))
    await update_coin_supply(ticker, float(new_supply))
    await update_coin_volume(ticker, float(total_cost))
    await update_balance(user_id, -float(total_cost))
    await add_to_inventory(user_id, ticker, amount)
    await add_transaction(user_id, ticker, amount, float(price), "buy")
    return f"Куплено {amount} {ticker}"

async def perform_sell(user_id, ticker, amount):
    coin = await get_coin(ticker)
    if not coin:
        return "Токен не знайдено"
    
    user_tokens = await get_user_tokens(user_id)
    token_amount = next((t['amount'] for t in user_tokens if t['name'] == ticker), 0)
    if token_amount < amount:
        return "Недостатньо токенів"
    
    price = await get_coin_price(ticker)
    total_earn = price * Decimal(str(amount))
    
    # Update supply
    new_supply = Decimal(str(coin[3])) - Decimal(str(amount))
    await update_coin_supply(ticker, float(new_supply))
    await update_coin_volume(ticker, float(total_earn))
    await update_balance(user_id, float(total_earn))
    await remove_from_inventory(user_id, ticker, amount)
    await add_transaction(user_id, ticker, -amount, float(price), "sell")
    return f"Продано {amount} {ticker}"

async def perform_create_coin(user_id, name):
    # Simple create, assume tier Bronze
    tier = "Bronze"
    initial_price = 1.0
    tier_info = TIERS[tier]
    cost = tier_info["cost"]
    
    bal = await get_balance(user_id)
    if bal < cost:
        return "Недостатньо коштів для створення токена"
    
    await update_balance(user_id, -cost)
    await create_coin(name, user_id, initial_price, tier, tier_info["fee"], tier_info["bot_fee"])
    return f"Токен {name} створено!"

TIERS = {
    "Bronze": {"cost": 10000, "fee": 0.005, "bot_fee": 0.01},
    "Silver": {"cost": 50000, "fee": 0.015, "bot_fee": 0.005},
    "Gold": {"cost": 200000, "fee": 0.05, "bot_fee": 0.002}
}

@app.get("/api/user/{user_id}")
async def get_user_data(user_id: int):
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    balance = await get_user_balance(user_id)
    tokens = await get_user_tokens(user_id)
    return {"balance": balance, "tokens": tokens}

@app.post("/api/action")
async def process_action(data: dict):
    user_id = data.get("user_id")
    action = data.get("action")
    params = data.get("params", {})
    
    try:
        if action == "create_coin":
            name = params.get("name")
            response = await perform_create_coin(user_id, name)
        elif action == "buy":
            name = params.get("name")
            amount = params.get("amount")
            response = await perform_buy(user_id, name, amount)
        elif action == "sell":
            name = params.get("name")
            amount = params.get("amount")
            response = await perform_sell(user_id, name, amount)
        elif action == "dice":
            amount = params.get("amount")
            target = params.get("target")
            response = f"Запрошено {target} на дуель в кості на {amount}"
        elif action == "dice_bot":
            amount = params.get("amount")
            response = f"Гра проти бота на {amount}"
        elif action == "rob":
            target = params.get("target")
            response = f"Спроба пограбувати {target}"
        elif action == "buy_item":
            item = params.get("item")
            # Simulate buy item
            response = f"Куплено {item}"
        elif action == "give":
            amount = params.get("amount")
            target = params.get("target")
            # For give, only admin
            if user_id != ADMIN_ID:
                response = "Немає дозволу"
            else:
                target_id = await get_user_by_username(target)
                if target_id:
                    await update_balance(target_id, amount)
                    response = f"Дано {amount} користувачу {target}"
                else:
                    response = "Користувач не знайдений"
        else:
            response = "Невідома дія"
    except Exception as e:
        response = f"Помилка: {str(e)}"
    
    return {"response": response}

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