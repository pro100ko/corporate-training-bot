import logging
from aiogram import Router, types
from aiogram.filters import Command
from utils.keyboards import Keyboards
from utils.helpers import MessageHelper

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def start_handler(message: types.Message, user=None, is_admin: bool = False, **kwargs):
    """Handle /start command"""
    user_id = message.from_user.id if message.from_user else 0
    first_name = message.from_user.first_name if message.from_user else "User"
    
    logger.info(f"Start command from user {user_id}")
    
    welcome_text = (
        f"👋 Welcome to the Corporate Training Bot, {first_name}!\n\n"
        "🎯 This bot helps you:\n"
        "• 📚 Browse our knowledge base\n"
        "• 🔍 Search for products\n"
        "• 📝 Take training tests\n"
        "• 📊 Track your progress\n\n"
    )
    
    if is_admin:
        welcome_text += "⚙️ As an administrator, you also have access to management tools.\n\n"
    
    welcome_text += "Choose an option below to get started:"
    
    await message.answer(
        text=welcome_text,
        reply_markup=Keyboards.main_menu(is_admin=is_admin)
    )

@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(query: types.CallbackQuery, user=None, is_admin: bool = False, **kwargs):
    """Handle main menu callback"""
    text = (
        "🏠 **Main Menu**\n\n"
        "Choose an option:"
    )
    
    await MessageHelper.safe_edit_message(
        query,
        text=text,
        reply_markup=Keyboards.main_menu(is_admin=is_admin),
        parse_mode="Markdown"
    )

@router.callback_query(lambda c: c.data == "cancel")
async def cancel_callback(query: types.CallbackQuery, **kwargs):
    """Handle cancel callback"""
    await MessageHelper.safe_answer_callback(query, "❌ Action cancelled")
    
    # Return to main menu
    await main_menu_callback(query, **kwargs)

@router.callback_query(lambda c: c.data == "noop")
async def noop_callback(query: types.CallbackQuery, **kwargs):
    """Handle no-operation callback"""
    await MessageHelper.safe_answer_callback(query)