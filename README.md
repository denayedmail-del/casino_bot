# Crypto-Tycoon & Casino Bot

A Telegram bot for economic strategy with internal currency (Coins) and custom token creation.

## Features

- **Internal Economy**: All transactions in Coins, minted via /give by admin.
- **Token Creation**: Create custom coins with tiers (Bronze/Silver/Gold) affecting royalties and fees.
- **Market Trading**: Buy/sell tokens with dynamic pricing (bonding curve).
- **Royalties**: Creators earn passive income on transactions.
- **Casino Games**: P2P duels and bot duels.
- **Shop System**: Buy effects, status, items.
- **Leaderboards**: Top users by equity, top creators, top coins.
- **Morning Reports**: Daily market summary at 9:00.

## Commands

- `/give <@username or user_id> <amount>`: Admin mints coins.
- `/create_coin <ticker> <initial_price>`: Create a token (choose tier).
- `/buy <ticker> <amount>`: Buy tokens.
- `/sell <ticker> <amount>`: Sell tokens.
- `/my_tokens`: View your token holdings and stats.
- `/top`: Leaderboard by total equity.
- `/dice <amount> <username>`: P2P duel.
- `/dice_bot <amount>`: Duel with bot.
- `/rob @username`: Social engineering.
- `/shop`: Open shop.

## Database Schema

- `users`: id, username, balance, vip_status, title, total_royalties
- `coins`: ticker, creator_id, initial_price, current_supply, total_volume, tier, royalty_fee, bot_fee
- `user_inventory`: user_id, ticker, amount
- `transactions`: user_id, ticker, type, amount, price, timestamp
- `inventory`: Shop items
- `global_vars`: bot_balance, etc.

## Setup

1. Install: `pip install -r requirements.txt`
2. Set BOT_TOKEN and ADMIN_ID in .env
3. Run: `python main.py`

- `users`: id, username, balance, vip_status, title
- `inventory`: id, user_id, item_type, item_name, expires_at
- `global_vars`: key, value (e.g., bot_balance)