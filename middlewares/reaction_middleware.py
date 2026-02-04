from aiogram import BaseMiddleware
from aiogram.types import Message
from database import get_user, create_user

class ReactionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        # Ensure user exists
        if event.from_user:
            user_id = event.from_user.id
            username = event.from_user.username
            if not await get_user(user_id):
                await create_user(user_id, username)
        
        # Call the handler first
        result = await handler(event, data)
        
        # After handling, check if user is VIP
        if event.from_user:
            user = await get_user(event.from_user.id)
            if user and user[3] == 1:  # vip_status
                # Set reaction
                try:
                    await event.bot.set_message_reaction(
                        chat_id=event.chat.id,
                        message_id=event.message_id,
                        reaction="🔥"
                    )
                except Exception as e:
                    print(f"Failed to set reaction: {e}")
        
        return result