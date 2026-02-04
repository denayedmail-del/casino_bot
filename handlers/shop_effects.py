from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_balance, update_balance, add_inventory, set_vip, set_title, get_inventory, get_address
from datetime import datetime, timedelta
import aiosqlite

router = Router()

shop_items = {
    'Effects': {
        'Trigger Word': {'price': 500, 'duration': 86400}  # seconds
    },
    'Status': {
        'VIP': {'price': 1000, 'duration': None},
        'Title: Ваша Величність': {'price': 200, 'duration': None},
        'Title: Крипто-король': {'price': 300, 'duration': None}
    },
    'Items': {
        # Add more if needed
    }
}

@router.message(F.text.startswith("/shop"))
async def cmd_shop(message: Message):
    print("Shop command received")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Effects", callback_data="shop_category:Effects")],
        [InlineKeyboardButton(text="Status", callback_data="shop_category:Status")],
        [InlineKeyboardButton(text="Items", callback_data="shop_category:Items")]
    ])
    try:
        await message.reply("Оберіть категорію:", reply_markup=keyboard)
        print("Shop reply sent")
    except Exception as e:
        print(f"Error sending shop reply: {e}")

@router.callback_query(F.data.startswith("shop_category:"))
async def shop_category(callback: CallbackQuery):
    category = callback.data.split(":")[1]
    items = shop_items.get(category, {})
    if not items:
        await callback.message.edit_text("Немає товарів у цій категорії")
        return
    
    keyboard = []
    for item_name, info in items.items():
        keyboard.append([InlineKeyboardButton(text=f"{item_name} - {info['price']} монет", callback_data=f"buy_item:{category}:{item_name}")])
    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="shop_back")])
    
    await callback.message.edit_text(f"Товари у {category}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data == "shop_back")
async def shop_back(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Effects", callback_data="shop_category:Effects")],
        [InlineKeyboardButton(text="Status", callback_data="shop_category:Status")],
        [InlineKeyboardButton(text="Items", callback_data="shop_category:Items")]
    ])
    await callback.message.edit_text("Оберіть категорію:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("buy_item:"))
async def buy_item(callback: CallbackQuery):
    data = callback.data.split(":")
    category = data[1]
    item_name = data[2]
    user_id = callback.from_user.id
    
    item_info = shop_items.get(category, {}).get(item_name)
    if not item_info:
        await callback.answer("Товар не знайдено")
        return
    
    price = item_info['price']
    bal = await get_balance(user_id)
    if bal < price:
        await callback.answer("Недостатньо коштів")
        return
    
    # Deduct balance
    await update_balance(user_id, -price)
    
    # Add to inventory or apply
    if category == 'Status':
        if item_name == 'VIP':
            await set_vip(user_id, 1)
        elif item_name.startswith('Title:'):
            title = item_name.split(': ')[1]
            await set_title(user_id, title)
    else:
        # For Effects, Items
        expires_at = None
        if item_info['duration']:
            expires_at = datetime.now() + timedelta(seconds=item_info['duration'])
        await add_inventory(user_id, category, item_name, expires_at)
    
    await callback.answer(f"Куплено {item_name}!")
    await callback.message.edit_text(f"{await get_address(user_id)}, покупка успішна!")

# Handler for trigger words
@router.message()
async def check_triggers(message: Message):
    if not message.text:
        return
    if message.text.startswith('/'):
        return
    
    text = message.text.lower()
    # Get all active trigger words
    # This is inefficient, but for demo
    # In real, perhaps cache or separate table
    async with aiosqlite.connect('casino_bot.db') as db:
        cursor = await db.execute('SELECT user_id, item_name FROM inventory WHERE item_type = ? AND (expires_at IS NULL OR expires_at > ?)',
                                  ('Effects', datetime.now()))
        triggers = await cursor.fetchall()
    
    for user_id, trigger in triggers:
        if trigger.lower() in text:
            # Trigger activated, send something
            await message.reply("🔥 Trigger activated!")  # Or sticker, but need id
            break  # Or handle multiple