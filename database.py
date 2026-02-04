import aiosqlite
import asyncio
from datetime import datetime
from decimal import Decimal

DATABASE_PATH = 'casino_bot.db'

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 1000,
                vip_status INTEGER DEFAULT 0,
                title TEXT DEFAULT '',
                total_royalties REAL DEFAULT 0
            )
        ''')
        # Inventory table (for shop items)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_type TEXT,
                item_name TEXT,
                expires_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        # Coins table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                ticker TEXT PRIMARY KEY,
                creator_id INTEGER,
                initial_price REAL,
                current_supply REAL DEFAULT 0,
                total_volume REAL DEFAULT 0,
                tier TEXT,
                royalty_fee REAL,
                bot_fee REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users (id)
            )
        ''')
        # User inventory for tokens
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticker TEXT,
                amount REAL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (ticker) REFERENCES coins (ticker)
            )
        ''')
        # Transactions table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticker TEXT,
                type TEXT,  -- buy/sell
                amount REAL,
                price REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (ticker) REFERENCES coins (ticker)
            )
        ''')
        # Global vars table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS global_vars (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Initialize bot balance if not exists
        await db.execute('INSERT OR IGNORE INTO global_vars (key, value) VALUES (?, ?)', ('bot_balance', '10000'))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return await cursor.fetchone()

async def create_user(user_id, username):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT INTO users (id, username) VALUES (?, ?)', (user_id, username))
        await db.commit()

async def update_balance(user_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
        await db.commit()

async def set_balance(user_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE users SET balance = ? WHERE id = ?', (amount, user_id))
        await db.commit()

async def get_balance(user_id):
    user = await get_user(user_id)
    return user[2] if user else 0

async def set_vip(user_id, status):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE users SET vip_status = ? WHERE id = ?', (status, user_id))
        await db.commit()

async def set_title(user_id, title):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE users SET title = ? WHERE id = ?', (title, user_id))
        await db.commit()

async def get_global_var(key):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT value FROM global_vars WHERE key = ?', (key,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_global_var(key, value):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO global_vars (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

async def add_inventory(user_id, item_type, item_name, expires_at=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT INTO inventory (user_id, item_type, item_name, expires_at) VALUES (?, ?, ?, ?)',
                         (user_id, item_type, item_name, expires_at))
        await db.commit()

async def get_inventory(user_id, item_type=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if item_type:
            cursor = await db.execute('SELECT * FROM inventory WHERE user_id = ? AND item_type = ? AND (expires_at IS NULL OR expires_at > ?)',
                                      (user_id, item_type, datetime.now()))
        else:
            cursor = await db.execute('SELECT * FROM inventory WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)',
                                      (user_id, datetime.now()))
        return await cursor.fetchall()

async def get_title(user_id):
    user = await get_user(user_id)
    return user[4] if user else ''

async def get_address(user_id):
    user = await get_user(user_id)
    title = user[4] if user else ''
    username = user[1] if user else 'User'
    return f"{title} {username}" if title else username

async def get_user_by_username(username):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT id FROM users WHERE username = ?', (username,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def update_royalties(user_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE users SET total_royalties = total_royalties + ? WHERE id = ?', (amount, user_id))
        await db.commit()

async def get_total_equity(user_id):
    balance = await get_balance(user_id)
    # Calculate value of tokens
    holdings = await get_user_tokens(user_id)
    equity = Decimal(str(balance))
    for ticker, amount in holdings:
        price = await get_coin_price(ticker)
        equity += Decimal(str(amount)) * price
    return float(equity)

# Coin functions
async def create_coin(ticker, creator_id, initial_price, tier, royalty_fee, bot_fee):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT INTO coins (ticker, creator_id, initial_price, tier, royalty_fee, bot_fee) VALUES (?, ?, ?, ?, ?, ?)',
                         (ticker, creator_id, initial_price, tier, royalty_fee, bot_fee))
        await db.commit()

async def get_coin(ticker):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT * FROM coins WHERE ticker = ?', (ticker,))
        return await cursor.fetchone()

async def update_coin_supply(ticker, new_supply):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE coins SET current_supply = ? WHERE ticker = ?', (new_supply, ticker))
        await db.commit()

async def update_coin_volume(ticker, volume):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE coins SET total_volume = total_volume + ? WHERE ticker = ?', (volume, ticker))
        await db.commit()

async def get_coin_price(ticker):
    coin = await get_coin(ticker)
    if not coin:
        return Decimal('0')
    supply = Decimal(str(coin[3]))  # current_supply
    initial = Decimal(str(coin[2]))  # initial_price
    # Simple bonding curve: price increases with supply
    if supply == 0:
        return initial
    return initial * (supply / 1000 + 1)

# User inventory
async def add_to_inventory(user_id, ticker, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if exists
        cursor = await db.execute('SELECT amount FROM user_inventory WHERE user_id = ? AND ticker = ?', (user_id, ticker))
        row = await cursor.fetchone()
        if row:
            new_amount = Decimal(str(row[0])) + Decimal(str(amount))
            await db.execute('UPDATE user_inventory SET amount = ? WHERE user_id = ? AND ticker = ?', (float(new_amount), user_id, ticker))
        else:
            await db.execute('INSERT INTO user_inventory (user_id, ticker, amount) VALUES (?, ?, ?)', (user_id, ticker, amount))
        await db.commit()

async def remove_from_inventory(user_id, ticker, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT amount FROM user_inventory WHERE user_id = ? AND ticker = ?', (user_id, ticker))
        row = await cursor.fetchone()
        if row:
            new_amount = Decimal(str(row[0])) - Decimal(str(amount))
            if new_amount <= 0:
                await db.execute('DELETE FROM user_inventory WHERE user_id = ? AND ticker = ?', (user_id, ticker))
            else:
                await db.execute('UPDATE user_inventory SET amount = ? WHERE user_id = ? AND ticker = ?', (float(new_amount), user_id, ticker))
        await db.commit()

async def get_user_tokens(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT ticker, amount FROM user_inventory WHERE user_id = ?', (user_id,))
        return await cursor.fetchall()

# Transactions
async def add_transaction(user_id, ticker, type_, amount, price):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT INTO transactions (user_id, ticker, type, amount, price) VALUES (?, ?, ?, ?, ?)',
                         (user_id, ticker, type_, amount, price))
        await db.commit()

# Leaderboard
async def get_top_users(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT id, username, balance, total_royalties FROM users ORDER BY balance DESC LIMIT ?', (limit,))
        return await cursor.fetchall()

async def get_top_creators(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT id, username, total_royalties FROM users ORDER BY total_royalties DESC LIMIT ?', (limit,))
        return await cursor.fetchall()

async def get_top_coins(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT ticker, total_volume FROM coins ORDER BY total_volume DESC LIMIT ?', (limit,))
        return await cursor.fetchall()