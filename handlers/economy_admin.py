from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import update_balance, set_global_var, get_global_var, set_balance
from config import ADMIN_ID

router = Router()

@router.message(F.text.startswith("/admin_set_balance"))
async def admin_set_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: /admin_set_balance <user_id> <amount>")
        return
    
    try:
        user_id = int(args[1])
        amount = float(args[2])
    except ValueError:
        await message.reply("Invalid args")
        return
    
    await set_balance(user_id, amount)
    await message.reply("Balance set")

# Add set_balance to database.py
# async def set_balance(user_id, amount):
#     async with aiosqlite.connect(DATABASE_PATH) as db:
#         await db.execute('UPDATE users SET balance = ? WHERE id = ?', (amount, user_id))
#         await db.commit()

# Then import and use

@router.message(F.text.startswith("/admin_set_bot_balance"))
async def admin_set_bot_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /admin_set_bot_balance <amount>")
        return
    
    try:
        amount = float(args[1])
    except ValueError:
        await message.reply("Invalid amount")
        return
    
    await set_global_var('bot_balance', str(amount))
    await message.reply("Bot balance set")