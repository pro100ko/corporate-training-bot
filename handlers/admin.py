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
        "⚙️ **Панель администратора**\n\n"
        "Добро пожаловать в панель управления. Выберите опцию:"
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
            "📁 **Управление категориями**\n\n"
            f"Всего категорий: {len(categories)}\n\n"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if categories:
            text += "Выберите категорию для управления:"
            for category in categories:
                builder.row(
                    types.InlineKeyboardButton(
                        text=f"📁 {category.name}",
                        callback_data=f"admin_view_category:{category.id}"
                    )
                )
        else:
            text += "Категории недоступны."
        
        builder.row(
            types.InlineKeyboardButton(
                text="➕ Добавить категорию",
                callback_data="add_category"
            )
        )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔙 К панели администратора",
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
            "Ошибка загрузки категорий. Попробуйте снова.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "add_category")
@admin_required
async def add_category_handler(query: types.CallbackQuery, state: FSMContext, **kwargs):
    """Handle add category"""
    text = (
        "➕ **Добавить новую категорию**\n\n"
        "📝 Введите название категории:\n\n"
        "Требования:\n"
        "• 2-100 символов\n"
        "• Описательное и понятное"
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
        category_name = message.text.strip() if message.text else ""
        
        if not ValidationHelper.is_valid_category_name(category_name):
            await message.answer(
                "⚠️ Неверное название категории. Введите 2-100 символов."
            )
            return
        
        # Check if category already exists
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("SELECT id FROM categories WHERE name = :name"),
                {"name": category_name}
            )
            existing = result.fetchone()
        
        if existing:
            await message.answer(
                "⚠️ Категория с таким названием уже существует. Выберите другое название."
            )
            return
        
        await state.update_data(category_name=category_name)
        
        text = (
            f"📝 **Название категории:** {category_name}\n\n"
            "📄 Введите описание для этой категории (необязательно):\n\n"
            "Можете отправить 'пропустить' чтобы продолжить без описания."
        )
        
        await message.answer(text, parse_mode="Markdown")
        await state.set_state(AdminStates.waiting_for_category_description)
        
    except Exception as e:
        logger.error(f"Error in process_category_name: {e}")
        await message.answer("❌ Ошибка обработки названия категории. Попробуйте снова.")
        await state.clear()

@router.message(AdminStates.waiting_for_category_description)
@admin_required
async def process_category_description(message: types.Message, state: FSMContext, user=None, **kwargs):
    """Process category description input"""
    try:
        description = message.text.strip() if message.text else ""
        
        if description.lower() == 'пропустить':
            description = None
        elif not ValidationHelper.is_valid_description(description):
            await message.answer(
                "⚠️ Слишком длинное описание. Максимум 2000 символов."
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
            "✅ **Категория создана успешно!**\n\n"
            f"📁 Название: {category_name}\n"
        )
        
        if description:
            text += f"📄 Описание: {description}\n"
        
        text += "\nТеперь вы можете добавить продукты в эту категорию."
        
        await message.answer(
            text,
            reply_markup=Keyboards.admin_panel(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in process_category_description: {e}")
        await message.answer("❌ Ошибка создания категории. Попробуйте снова.")
        await state.clear()

@router.callback_query(lambda c: c.data == "admin_products")
@admin_required
async def admin_products_handler(query: types.CallbackQuery, **kwargs):
    """Handle admin products management"""
    try:
        # Get all products with category names
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                SELECT p.id, p.name, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                ORDER BY c.name, p.name
                """)
            )
            products = result.fetchall()
        
        text = (
            "📦 **Управление продуктами**\n\n"
            f"Всего продуктов: {len(products)}\n\n"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if products:
            text += "Выберите продукт для управления:"
            
            for product in products[:10]:  # Limit to 10 for keyboard space
                display_name = f"{product.name}"
                if product.category_name:
                    display_name += f" ({product.category_name})"
                
                builder.row(
                    types.InlineKeyboardButton(
                        text=f"📦 {display_name}",
                        callback_data=f"admin_view_product:{product.id}"
                    )
                )
            
            if len(products) > 10:
                text += f"\n\n(Показано первые 10 из {len(products)} продуктов)"
        else:
            text += "Продукты недоступны."
        
        builder.row(
            types.InlineKeyboardButton(
                text="➕ Добавить продукт",
                callback_data="select_category_for_product"
            )
        )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔙 К панели администратора",
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
        logger.error(f"Error in admin_products_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Ошибка загрузки продуктов. Попробуйте снова.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "select_category_for_product")
@admin_required
async def select_category_for_product(query: types.CallbackQuery, **kwargs):
    """Handle category selection for new product"""
    try:
        categories = await DatabaseManager.get_categories()
        
        if not categories:
            await MessageHelper.safe_answer_callback(
                query, 
                "Категории недоступны. Сначала создайте категорию.", 
                show_alert=True
            )
            return
        
        text = (
            "📁 **Выберите категорию**\n\n"
            "Выберите категорию для нового продукта:"
        )
        
        keyboard = Keyboards.categories_list(categories, "add_product")
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in select_category_for_product: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Ошибка загрузки категорий. Попробуйте снова.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "admin_questions")
@admin_required
async def admin_questions_handler(query: types.CallbackQuery, **kwargs):
    """Handle admin questions management"""
    try:
        # Get all products with question counts
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                SELECT p.id, p.name, c.name as category_name, COUNT(tq.id) as question_count
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                LEFT JOIN test_questions tq ON p.id = tq.product_id
                GROUP BY p.id, p.name, c.name
                ORDER BY c.name, p.name
                """)
            )
            products = result.fetchall()
        
        text = (
            "❓ **Управление тестами**\n\n"
            f"Всего продуктов: {len(products)}\n\n"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if products:
            text += "Выберите продукт для управления вопросами:"
            
            for product in products[:10]:  # Limit to 10 for keyboard space
                display_name = f"{product.name}"
                if product.category_name:
                    display_name += f" ({product.category_name})"
                display_name += f" [{product.question_count} В]"
                
                builder.row(
                    types.InlineKeyboardButton(
                        text=f"❓ {display_name}",
                        callback_data=f"manage_questions:{product.id}"
                    )
                )
            
            if len(products) > 10:
                text += f"\n\n(Показано первые 10 из {len(products)} продуктов)"
        else:
            text += "Продукты недоступны. Сначала создайте продукты."
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔙 К панели администратора",
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
        logger.error(f"Error in admin_questions_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Ошибка загрузки вопросов. Попробуйте снова.", 
            show_alert=True
        )

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
            "📊 **Статистика системы**\n\n"
            f"👥 Пользователи: {stats['users']}\n"
            f"📁 Категории: {stats['categories']}\n"
            f"📦 Продукты: {stats['products']}\n"
            f"❓ Вопросы: {stats['questions']}\n"
            f"📝 Результаты тестов: {stats['test_results']}\n"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔙 К панели администратора",
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
            "Ошибка загрузки статистики. Попробуйте снова.", 
            show_alert=True
        )
