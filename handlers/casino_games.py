import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_user, create_user, get_balance, update_balance, get_global_var, set_global_var, get_user_by_username, get_address
from config import ADMIN_ID

router = Router()

# Store pending duels: {message_id: {'challenger': id, 'target': id, 'amount': amount}}
pending_duels = {}

@router.message(F.text.startswith("/dice"))
async def cmd_dice(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: /dice <amount> <username>")
        return
    
    try:
        amount = float(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply("Invalid amount")
        return
    
    username = args[2].lstrip('@')
    
    # Find target user
    # In aiogram, to get user by username, it's tricky, assume username is provided
    # For simplicity, assume the target is mentioned or something, but since it's text, perhaps store username
    # Actually, in Telegram, usernames are unique, but to get user_id, need to have them in chat or something.
    # For this, perhaps assume the bot knows users by username if they have chatted.
    # But to simplify, let's say the command is /dice amount @username, and we store the username.
    # When accepting, the accepter must be the one with that username.
    
    challenger_id = message.from_user.id
    challenger_username = message.from_user.username
    
    # Check balance
    bal = await get_balance(challenger_id)
    if bal < amount:
        await message.reply("Insufficient balance")
        return
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Прийняти парі", callback_data=f"accept_duel:{challenger_id}:{amount}:{username}")]
    ])
    
    await message.reply(f"@{challenger_username} пропонує парі на {amount} монет з @{username}!", reply_markup=keyboard)
    
    # Store pending
    pending_duels[message.message_id] = {'challenger': challenger_id, 'target_username': username, 'amount': amount, 'challenger_username': challenger_username}

@router.callback_query(F.data.startswith("accept_duel:"))
async def accept_duel(callback: CallbackQuery):
    data = callback.data.split(":")
    challenger_id = int(data[1])
    amount = float(data[2])
    target_username = data[3]
    
    accepter_id = callback.from_user.id
    accepter_username = callback.from_user.username
    
    if accepter_username != target_username:
        await callback.answer("Це не для вас!")
        return
    
    # Check if pending
    if callback.message.message_id not in pending_duels:
        await callback.answer("Парі вже не актуальна")
        return
    
    duel = pending_duels.pop(callback.message.message_id)
    
    # Check balances
    chal_bal = await get_balance(challenger_id)
    acc_bal = await get_balance(accepter_id)
    
    if chal_bal < amount or acc_bal < amount:
        await callback.message.edit_text("Один з гравців не має достатньо коштів")
        return
    
    # Roll dice
    chal_dice = random.randint(1, 6)
    acc_dice = random.randint(1, 6)
    
    if chal_dice > acc_dice:
        winner = challenger_id
        loser = accepter_id
        winner_name = duel['challenger_username']  # Need to store username
        loser_name = accepter_username
    elif acc_dice > chal_dice:
        winner = accepter_id
        loser = challenger_id
        winner_name = accepter_username
        loser_name = duel['challenger_username']
    else:
        # Draw, refund
        await callback.message.edit_text(f"Нічия! {chal_dice} vs {acc_dice}. Гроші повернуто.")
        return
    
    # Update balances
    await update_balance(winner, amount)
    await update_balance(loser, -amount)
    
    new_winner_bal = await get_balance(winner)
    new_loser_bal = await get_balance(loser)
    
    await callback.message.edit_text(f"🎲 Результат: {winner_name} виграв! ({chal_dice} vs {acc_dice})\n"
                                     f"Забрано {amount} монет.\n"
                                     f"{winner_name} тепер має {new_winner_bal} монет.\n"
                                     f"{loser_name} тепер має {new_loser_bal} монет.")

@router.message(F.text.startswith("/dice_bot"))
async def cmd_dice_bot(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /dice_bot <amount>")
        return
    
    try:
        amount = float(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply("Invalid amount")
        return
    
    user_id = message.from_user.id
    bal = await get_balance(user_id)
    if bal < amount:
        await message.reply("Insufficient balance")
        return
    
    bot_bal = float(await get_global_var('bot_balance') or 0)
    if bot_bal < amount:
        await message.reply("Я банкрут, зачекайте поки хтось програє")
        return
    
    # Roll
    user_dice = random.randint(1, 6)
    bot_dice = random.randint(1, 6)
    
    if user_dice > bot_dice:
        # User wins
        await update_balance(user_id, amount)
        await set_global_var('bot_balance', str(bot_bal - amount))
        result = f"Ти виграв! {user_dice} vs {bot_dice}"
    elif bot_dice > user_dice:
        # Bot wins
        await update_balance(user_id, -amount)
        await set_global_var('bot_balance', str(bot_bal + amount))
        result = f"Ти програв! {user_dice} vs {bot_dice}"
    else:
        result = f"Нічия! {user_dice} vs {bot_dice}"
    
    new_bal = await get_balance(user_id)
    await message.reply(f"🎲 {result}\n{await get_address(user_id)}, твій баланс: {new_bal}")

@router.message(F.text.startswith("/rob"))
async def cmd_rob(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /rob @username")
        return
    
    target_username = args[1].lstrip('@')
    robber_id = message.from_user.id
    
    # Find target id, assume we have a way, but for simplicity, if target has chatted, but hard.
    # Perhaps store users by username in db.
    # For now, assume target_id is known, but since it's text, perhaps reply that target not found.
    # To make it work, perhaps the command is /rob and reply to message.
    # But the task says /rob @username
    
    # For simplicity, let's say we need to have the user in db.
    # Assume target_id is the id of the user with that username.
    # But to get id by username, need to query db.
    
    # Add a function to get user by username
    async def get_user_by_username(username):
        async with aiosqlite.connect('casino_bot.db') as db:
            cursor = await db.execute('SELECT id FROM users WHERE username = ?', (username,))
            row = await cursor.fetchone()
            return row[0] if row else None
    
    target_id = await get_user_by_username(target_username)
    if not target_id:
        await message.reply("Користувач не знайдений")
        return
    
    if target_id == robber_id:
        await message.reply("Не можна грабувати себе")
        return
    
    # Chance 30%
    if random.random() < 0.3:
        # Success, steal random amount
        target_bal = await get_balance(target_id)
        steal_amount = random.uniform(1, target_bal * 0.1)  # up to 10%
        await update_balance(robber_id, steal_amount)
        await update_balance(target_id, -steal_amount)
        await message.reply(f"Успіх! {await get_address(robber_id)}, ви вкрали {steal_amount:.2f} монет")
    else:
        # Failure, penalty x2, but x2 of what? Perhaps x2 of intended steal, but since random, perhaps fixed penalty.
        # The task says "штраф x2", but x2 of what? Perhaps x2 of the amount they would steal, but since failed, maybe x2 random.
        # Let's assume penalty is x2 of a random amount they tried to steal.
        penalty = random.uniform(10, 100) * 2
        bal = await get_balance(robber_id)
        if bal >= penalty:
            await update_balance(robber_id, -penalty)
            await message.reply(f"Невдача! {await get_address(robber_id)}, штраф {penalty:.2f} монет")
        else:
            await message.reply(f"Невдача! {await get_address(robber_id)}, але у вас недостатньо коштів для штрафу")