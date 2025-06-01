import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database import DatabaseManager
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """Middleware for user authentication and authorization"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Process authentication and authorization"""
        
        # Get user info from event
        user_info = event.from_user
        if not user_info:
            return await handler(event, data)
        
        try:
            # Check if user is admin
            is_admin = user_info.id in ADMIN_IDS
            
            # Get or create user in database
            user = await DatabaseManager.get_or_create_user(
                telegram_id=user_info.id,
                username=user_info.username,
                first_name=user_info.first_name,
                last_name=user_info.last_name,
                is_admin=is_admin
            )
            
            # Add user and admin status to handler data
            data['user'] = user
            data['is_admin'] = is_admin
            
            logger.info(f"User {user_info.id} authenticated (admin: {is_admin})")
            
        except Exception as e:
            logger.error(f"Error in auth middleware: {e}")
            # Continue without user data if there's an error
            data['user'] = None
            data['is_admin'] = False
        
        return await handler(event, data)

def admin_required(func):
    """Decorator to require admin privileges"""
    async def wrapper(message_or_query, **kwargs):
        is_admin = kwargs.get('is_admin', False)
        
        if not is_admin:
            # Handle both Message and CallbackQuery
            if hasattr(message_or_query, 'answer'):
                # It's a Message
                await message_or_query.answer(
                    "❌ You don't have permission to perform this action.\n"
                    "This feature is restricted to administrators only."
                )
            else:
                # It's a CallbackQuery
                from utils.helpers import MessageHelper
                await MessageHelper.safe_answer_callback(
                    message_or_query,
                    "❌ Access denied. Admin privileges required.",
                    show_alert=True
                )
            return
        
        return await func(message_or_query, **kwargs)
    
    return wrapper