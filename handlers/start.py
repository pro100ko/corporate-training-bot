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
    first_name = message.from_user.first_name if message.from_user else "Пользователь"
    
    logger.info(f"Start command from user {user_id}")
    
    welcome_text = (
        f"👋 Добро пожаловать в корпоративный бот обучения, {first_name}!\n\n"
        "🎯 Этот бот поможет вам:\n"
        "• 📚 Изучать базу знаний\n"
        "• 🔍 Искать продукты\n"
        "• 📝 Проходить тесты\n"
        "• 📊 Отслеживать прогресс\n\n"
    )
    
    if is_admin:
        welcome_text += "⚙️ Как администратор, у вас также есть доступ к инструментам управления.\n\n"
    
    welcome_text += "Выберите опцию ниже, чтобы начать:"
    
    await message.answer(
        text=welcome_text,
        reply_markup=Keyboards.main_menu(is_admin=is_admin)
    )

@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(query: types.CallbackQuery, user=None, is_admin: bool = False, **kwargs):
    """Handle main menu callback"""
    text = (
        "🏠 **Главное меню**\n\n"
        "Выберите опцию:"
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
    await MessageHelper.safe_answer_callback(query, "❌ Действие отменено")
    
    # Return to main menu
    await main_menu_callback(query, **kwargs)

@router.callback_query(lambda c: c.data == "noop")
async def noop_callback(query: types.CallbackQuery, **kwargs):
    """Handle no-operation callback"""
    await MessageHelper.safe_answer_callback(query)
