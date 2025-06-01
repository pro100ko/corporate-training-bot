import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import DatabaseManager
from utils.keyboards import Keyboards
from utils.helpers import MessageHelper, ValidationHelper
from middleware.auth import admin_required

router = Router()
logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_category_description = State()
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_image = State()
    waiting_for_question_text = State()
    waiting_for_option_a = State()
    waiting_for_option_b = State()
    waiting_for_option_c = State()
    waiting_for_option_d = State()
    waiting_for_correct_answer = State()

@router.callback_query(lambda c: c.data == "admin_panel")
@admin_required
async def admin_panel_handler(query: types.CallbackQuery, **kwargs):
    """Handle admin panel menu"""
    text = (
        "⚙️ **Admin Panel**\n\n"
        "Welcome to the administration panel. Choose an option:"
    )
    
    await MessageHelper.safe_edit_message(
        query,
        text=text,
        reply_markup=Keyboards.admin_panel(),
        parse_mode="Markdown"
    )

@router.callback_query(lambda c: c.data == "admin_categories")
@admin_required
async def admin_categories_handler(query: types.CallbackQuery, **kwargs):
    """Handle admin categories management"""
    try:
        categories = await DatabaseManager.get_categories()
        
        text = (
            "📁 **Manage Categories**\n\n"
            f"Total categories: {len(categories)}\n\n"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if categories:
            text += "Select a category to manage:"
            for category in categories:
                builder.row(
                    types.InlineKeyboardButton(
                        text=f"📁 {category.name}",
                        callback_data=f"admin_view_category:{category.id}"
                    )
                )
        else:
            text += "No categories available."
        
        builder.row(
            types.InlineKeyboardButton(
                text="➕ Add Category",
                callback_data="add_category"
            )
        )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔙 Back to Admin",
                callback_data="admin_panel"
            )
        )
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in admin_categories_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "❌ Error loading categories. Please try again.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "add_category")
@admin_required
async def add_category_handler(query: types.CallbackQuery, state: FSMContext, **kwargs):
    """Handle add category"""
    text = (
        "➕ **Add New Category**\n\n"
        "📝 Please enter the category name:\n\n"
        "Requirements:\n"
        "• 2-100 characters\n"
        "• Descriptive and clear"
    )
    
    await MessageHelper.safe_edit_message(
        query,
        text=text,
        reply_markup=None,
        parse_mode="Markdown"
    )
    
    await state.set_state(AdminStates.waiting_for_category_name)

@router.message(AdminStates.waiting_for_category_name)
@admin_required
async def process_category_name(message: types.Message, state: FSMContext, user=None, **kwargs):
    """Process category name input"""
    try:
        category_name = message.text.strip()
        
        if not ValidationHelper.is_valid_category_name(category_name):
            await message.answer(
                "⚠️ Invalid category name. Please enter 2-100 characters."
            )
            return
        
        # Check if category already exists
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import select, text
            result = await session.execute(
                text("SELECT id FROM categories WHERE name = :name"),
                {"name": category_name}
            )
            existing = result.fetchone()
        
        if existing:
            await message.answer(
                "⚠️ Category with this name already exists. Please choose a different name."
            )
            return
        
        await state.update_data(category_name=category_name)
        
        text = (
            f"📝 **Category Name:** {category_name}\n\n"
            "📄 Please enter a description for this category (optional):\n\n"
            "You can send 'skip' to continue without description."
        )
        
        await message.answer(text, parse_mode="Markdown")
        await state.set_state(AdminStates.waiting_for_category_description)
        
    except Exception as e:
        logger.error(f"Error in process_category_name: {e}")
        await message.answer("❌ Error processing category name. Please try again.")
        await state.clear()

@router.message(AdminStates.waiting_for_category_description)
@admin_required
async def process_category_description(message: types.Message, state: FSMContext, user=None, **kwargs):
    """Process category description input"""
    try:
        description = message.text.strip()
        
        if description.lower() == 'skip':
            description = None
        elif not ValidationHelper.is_valid_description(description):
            await message.answer(
                "⚠️ Description too long. Maximum 2000 characters allowed."
            )
            return
        
        state_data = await state.get_data()
        category_name = state_data.get('category_name')
        
        # Create category
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            await session.execute(
                text("INSERT INTO categories (name, description, created_by) VALUES (:name, :description, :created_by)"),
                {"name": category_name, "description": description, "created_by": user.telegram_id}
            )
            await session.commit()
        
        await state.clear()
        
        text = (
            "✅ **Category Created Successfully!**\n\n"
            f"📁 Name: {category_name}\n"
        )
        
        if description:
            text += f"📄 Description: {description}\n"
        
        text += "\nYou can now add products to this category."
        
        await message.answer(
            text,
            reply_markup=Keyboards.admin_panel(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in process_category_description: {e}")
        await message.answer("❌ Error creating category. Please try again.")
        await state.clear()

@router.callback_query(lambda c: c.data == "admin_stats")
@admin_required
async def admin_stats_handler(query: types.CallbackQuery, **kwargs):
    """Handle admin statistics view"""
    try:
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            
            # Get various statistics
            stats = {}
            
            # Total users
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            stats['users'] = result.scalar()
            
            # Total categories
            result = await session.execute(text("SELECT COUNT(*) FROM categories"))
            stats['categories'] = result.scalar()
            
            # Total products
            result = await session.execute(text("SELECT COUNT(*) FROM products"))
            stats['products'] = result.scalar()
            
            # Total questions
            result = await session.execute(text("SELECT COUNT(*) FROM test_questions"))
            stats['questions'] = result.scalar()
            
            # Total test results
            result = await session.execute(text("SELECT COUNT(*) FROM test_results"))
            stats['test_results'] = result.scalar()
        
        text = (
            "📊 **System Statistics**\n\n"
            f"👥 Users: {stats['users']}\n"
            f"📁 Categories: {stats['categories']}\n"
            f"📦 Products: {stats['products']}\n"
            f"❓ Questions: {stats['questions']}\n"
            f"📝 Test Results: {stats['test_results']}\n"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔙 Back to Admin",
                callback_data="admin_panel"
            )
        )
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in admin_stats_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "❌ Error loading statistics. Please try again.", 
            show_alert=True
        )