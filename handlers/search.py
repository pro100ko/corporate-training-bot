import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import DatabaseManager
from utils.keyboards import Keyboards
from utils.helpers import MessageHelper

router = Router()
logger = logging.getLogger(__name__)

class SearchStates(StatesGroup):
    waiting_for_query = State()

@router.callback_query(lambda c: c.data == "search_products")
async def search_products_handler(query: types.CallbackQuery, state: FSMContext, **kwargs):
    """Handle search products menu"""
    text = (
        "🔍 **Поиск продуктов**\n\n"
        "💬 Введите название продукта:\n\n"
        "📝 Вы можете искать по:\n"
        "• Названию продукта\n"
        "• Ключевым словам в описании\n\n"
        "Введите ваш поисковый запрос:"
    )
    
    await MessageHelper.safe_edit_message(
        query,
        text=text,
        reply_markup=None,
        parse_mode="Markdown"
    )
    
    await state.set_state(SearchStates.waiting_for_query)

@router.message(SearchStates.waiting_for_query)
async def search_query_handler(message: types.Message, state: FSMContext, **kwargs):
    """Handle search query input"""
    try:
        query_text = message.text.strip() if message.text else ""
        
        if len(query_text) < 2:
            await message.answer(
                "⚠️ Слишком короткий запрос. Введите минимум 2 символа."
            )
            return
        
        # Search for products
        products = await DatabaseManager.search_products(query_text)
        
        await state.clear()
        
        if not products:
            text = (
                f"🔍 **Результаты поиска**\n\n"
                f"Не найдено продуктов по запросу: '{query_text}'\n\n"
                "Попробуйте использовать другие ключевые слова или просмотрите категории."
            )
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            builder.row(
                types.InlineKeyboardButton(
                    text="📚 Просмотр категорий",
                    callback_data="knowledge_base"
                )
            )
            
            builder.row(
                types.InlineKeyboardButton(
                    text="🔍 Искать снова",
                    callback_data="search_products"
                )
            )
            
            builder.row(
                types.InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu"
                )
            )
            
            await message.answer(
                text=text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            return
        
        text = (
            f"🔍 **Результаты поиска**\n\n"
            f"Найдено {len(products)} продуктов по запросу: '{query_text}'\n\n"
            "Выберите продукт для просмотра:"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        for product in products:
            builder.row(
                types.InlineKeyboardButton(
                    text=f"📦 {product.name}",
                    callback_data=f"search_result:{product.id}"
                )
            )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔍 Искать снова",
                callback_data="search_products"
            )
        )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        )
        
        await message.answer(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in search_query_handler: {e}")
        await message.answer("❌ Ошибка обработки поиска. Попробуйте снова.")
        await state.clear()

@router.callback_query(lambda c: c.data.startswith("search_result:"))
async def search_result_handler(query: types.CallbackQuery, **kwargs):
    """Handle search result selection"""
    try:
        product_id = int(query.data.split(":")[1])
        
        # Get product with category info
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                SELECT p.id, p.name, p.description, p.image_file_id, p.document_file_id, 
                       c.name as category_name, c.id as category_id
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                WHERE p.id = :product_id
                """),
                {"product_id": product_id}
            )
            product = result.fetchone()
        
        if not product:
            await MessageHelper.safe_answer_callback(
                query, 
                "Продукт не найден.", 
                show_alert=True
            )
            return
        
        # Check if product has test questions
        questions = await DatabaseManager.get_test_questions(product_id)
        has_test = len(questions) > 0
        
        text = MessageHelper.format_product_info(product, product.category_name)
        
        if has_test:
            text += f"\n📝 Доступен тест ({len(questions)} вопросов)"
        
        # Create keyboard with search-specific back button
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if has_test:
            builder.row(
                types.InlineKeyboardButton(
                    text="📝 Пройти тест",
                    callback_data=f"start_test:{product_id}"
                )
            )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔍 Искать снова",
                callback_data="search_products"
            )
        )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        )
        
        # Send image/document if available
        if product.image_file_id:
            try:
                await query.message.answer_photo(
                    photo=product.image_file_id,
                    caption=text,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
                await MessageHelper.safe_answer_callback(query)
                return
            except Exception as e:
                logger.warning(f"Failed to send image: {e}")
        
        if product.document_file_id:
            try:
                await query.message.answer_document(
                    document=product.document_file_id,
                    caption=text,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
                await MessageHelper.safe_answer_callback(query)
                return
            except Exception as e:
                logger.warning(f"Failed to send document: {e}")
        
        # Send as text message if no files or files failed
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid product ID in search_result_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Неверный продукт. Попробуйте снова.", 
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in search_result_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Ошибка загрузки продукта. Попробуйте снова.", 
            show_alert=True
        )
