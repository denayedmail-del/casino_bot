from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_balance, update_balance, create_coin, get_coin, get_coin_price, add_to_inventory, remove_from_inventory, add_transaction, update_coin_supply, update_coin_volume, update_royalties, get_user_tokens, get_top_users, get_top_creators, get_top_coins, get_address, get_user_by_username, get_global_var, set_global_var
from config import ADMIN_ID
from decimal import Decimal
from decimal import Decimal

router = Router()

TIERS = {
    "Bronze": {"cost": 10000, "fee": 0.005, "bot_fee": 0.01},
    "Silver": {"cost": 50000, "fee": 0.015, "bot_fee": 0.005},
    "Gold": {"cost": 200000, "fee": 0.05, "bot_fee": 0.002}
}

@router.message(F.text.startswith("/give"))
async def cmd_give(message: Message):
    print(f"Give command from {message.from_user.id}, admin: {ADMIN_ID}")
    if message.from_user.id != ADMIN_ID:
        print("Not admin")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: /give <@username or user_id> <amount>")
        return
    
    target = args[1]
    try:
        amount = float(args[2])
    except ValueError:
        await message.reply("Invalid amount")
        return
    
    if target.startswith('@'):
        username = target[1:]  # remove @
        user_id = await get_user_by_username(username)
        print(f"Username {username}, user_id {user_id}")
        if not user_id:
            await message.reply("User not found")
            return
    else:
        try:
            user_id = int(target)
        except ValueError:
            await message.reply("Invalid user identifier")
            return
    
    await update_balance(user_id, amount)
    print(f"Gave {amount} to {user_id}")
    try:
        await message.reply(f"Gave {amount} coins to user {target}")
        print("Reply sent")
    except Exception as e:
        print(f"Error sending reply: {e}")

@router.message(F.text == "/help")
async def cmd_help(message: Message):
    print("Help command received")
    help_text = "Допомога: /give, /top, /create_coin, /buy, /sell, /my_tokens, /dice, /dice_bot, /rob, /shop"
    try:
        await message.reply(help_text)
        print("Help reply sent")
    except Exception as e:
        print(f"Error sending help reply: {e}")

@router.message(F.text.startswith("/create_coin"))
async def cmd_create_coin(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: /create_coin <ticker> <initial_price>")
        return
    
    ticker = args[1].upper()
    try:
        initial_price = float(args[2])
    except ValueError:
        await message.reply("Invalid price")
        return
    
    user_id = message.from_user.id
    
    # Check if ticker exists
    if await get_coin(ticker):
        await message.reply("Ticker already exists")
        return
    
    # Ask for tier
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Bronze ({TIERS['Bronze']['cost']} coins)", callback_data=f"create_tier:{ticker}:{initial_price}:Bronze")],
        [InlineKeyboardButton(text=f"Silver ({TIERS['Silver']['cost']} coins)", callback_data=f"create_tier:{ticker}:{initial_price}:Silver")],
        [InlineKeyboardButton(text=f"Gold ({TIERS['Gold']['cost']} coins)", callback_data=f"create_tier:{ticker}:{initial_price}:Gold")]
    ])
    
    await message.reply("Choose tier:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("create_tier:"))
async def create_tier(callback: CallbackQuery):
    data = callback.data.split(":")
    ticker = data[1]
    initial_price = float(data[2])
    tier = data[3]
    
    user_id = callback.from_user.id
    tier_info = TIERS[tier]
    cost = tier_info["cost"]
    
    bal = await get_balance(user_id)
    if bal < cost:
        await callback.answer("Insufficient balance")
        return
    
    await update_balance(user_id, -cost)
    await create_coin(ticker, user_id, initial_price, tier, tier_info["fee"], tier_info["bot_fee"])
    
    await callback.message.edit_text(f"Created coin ${ticker} with tier {tier}!")

@router.message(F.text.startswith("/buy"))
async def cmd_buy(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: /buy <ticker> <amount>")
        return
    
    ticker = args[1].upper()
    try:
        amount = float(args[2])
    except ValueError:
        await message.reply("Invalid amount")
        return
    
    user_id = message.from_user.id
    coin = await get_coin(ticker)
    if not coin:
        await message.reply("Coin not found")
        return
    
    price = await get_coin_price(ticker)
    total_cost = price * Decimal(str(amount))
    
    bal = await get_balance(user_id)
    if bal < float(total_cost):
        await message.reply("Insufficient balance")
        return
    
    # Update supply
    new_supply = Decimal(str(coin[3])) + Decimal(str(amount))
    await update_coin_supply(ticker, float(new_supply))
    
    # Update volume
    await update_coin_volume(ticker, float(total_cost))
    
    # Deduct balance
    await update_balance(user_id, -float(total_cost))
    
    # Add to inventory
    await add_to_inventory(user_id, ticker, amount)
    
    # Add transaction
    await add_transaction(user_id, ticker, 'buy', amount, float(price))
    
    # Royalties
    royalty = total_cost * Decimal(str(coin[6]))  # royalty_fee
    bot_fee = total_cost * Decimal(str(coin[7]))  # bot_fee
    creator_id = coin[1]
    await update_royalties(creator_id, float(royalty))
    # Bot fee to bot_balance
    from database import set_global_var, get_global_var
    bot_bal = float(await get_global_var('bot_balance') or 0)
    await set_global_var('bot_balance', str(bot_bal + float(bot_fee)))
    
    new_price = await get_coin_price(ticker)
    creator_username = (await get_user_by_username(await get_user(creator_id)[1]))[1] if await get_user(creator_id) else "Unknown"
    
    await message.reply(f"{await get_address(user_id)} bought {amount} ${ticker}. Price rose to {new_price:.4f}. Creator @{creator_username} got {royalty:.4f} coins royalty!")

@router.message(F.text.lower().startswith("/help"))
async def cmd_sell(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: /sell <ticker> <amount>")
        return
    
    ticker = args[1].upper()
    try:
        amount = float(args[2])
    except ValueError:
        await message.reply("Invalid amount")
        return
    
    user_id = message.from_user.id
    holdings = await get_user_tokens(user_id)
    holding = next((h for h in holdings if h[0] == ticker), None)
    if not holding or holding[1] < amount:
        await message.reply("Insufficient holdings")
        return
    
    coin = await get_coin(ticker)
    price = await get_coin_price(ticker)
    total_value = price * Decimal(str(amount))
    
    # Update supply
    new_supply = Decimal(str(coin[3])) - Decimal(str(amount))
    await update_coin_supply(ticker, float(new_supply))
    
    # Update volume
    await update_coin_volume(ticker, float(total_value))
    
    # Add balance
    await update_balance(user_id, float(total_value))
    
    # Remove from inventory
    await remove_from_inventory(user_id, ticker, amount)
    
    # Add transaction
    await add_transaction(user_id, ticker, 'sell', amount, float(price))
    
    # Royalties on sell too?
    royalty = total_value * Decimal(str(coin[6]))
    bot_fee = total_value * Decimal(str(coin[7]))
    creator_id = coin[1]
    await update_royalties(creator_id, float(royalty))
    bot_bal = float(await get_global_var('bot_balance') or 0)
    await set_global_var('bot_balance', str(bot_bal + float(bot_fee)))
    
    new_price = await get_coin_price(ticker)
    creator_username = (await get_user(creator_id))[1] if await get_user(creator_id) else "Unknown"
    
    await message.reply(f"{await get_address(user_id)} sold {amount} ${ticker}. Price fell to {new_price:.4f}. Creator @{creator_username} got {royalty:.4f} coins royalty!")

@router.message(F.text.startswith("/my_tokens"))
async def cmd_my_tokens(message: Message):
    user_id = message.from_user.id
    holdings = await get_user_tokens(user_id)
    if not holdings:
        await message.reply("You have no tokens")
        return
    
    text = "Your tokens:\n"
    total_value = Decimal('0')
    for ticker, amount in holdings:
        price = await get_coin_price(ticker)
        value = price * Decimal(str(amount))
        total_value += value
        text += f"${ticker}: {amount} (value: {value:.4f})\n"
    
    text += f"Total token value: {total_value:.4f}"
    await message.reply(text)

@router.message(F.text.startswith("/top"))
async def cmd_top(message: Message):
    top_users = await get_top_users(5)
    text = "Top by balance:\n"
    for i, (id, username, balance, royalties) in enumerate(top_users, 1):
        equity = await get_total_equity(id)
        text += f"{i}. @{username}: {balance:.2f} coins, Equity: {equity:.2f}\n"
    
    await message.reply(text)