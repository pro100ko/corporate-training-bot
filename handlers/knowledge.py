import logging
from aiogram import Router, types
from database import DatabaseManager
from utils.keyboards import Keyboards
from utils.helpers import MessageHelper

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == "knowledge_base")
async def knowledge_base_handler(query: types.CallbackQuery, **kwargs):
    """Handle knowledge base menu"""
    try:
        categories = await DatabaseManager.get_categories()
        
        if not categories:
            text = (
                "📚 **База знаний**\n\n"
                "Категории пока недоступны.\n"
                "Обратитесь к администратору для добавления контента."
            )
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(
                    text="🔙 В главное меню",
                    callback_data="main_menu"
                )
            )
            
            await MessageHelper.safe_edit_message(
                query,
                text=text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            return
        
        text = (
            "📚 **База знаний**\n\n"
            f"Просматривайте {len(categories)} категорий продуктов и информации:"
        )
        
        keyboard = Keyboards.categories_list(categories, "view_category")
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in knowledge_base_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Ошибка загрузки базы знаний. Попробуйте снова.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data.startswith("view_category:"))
async def view_category_handler(query: types.CallbackQuery, **kwargs):
    """Handle category view"""
    try:
        category_id = int(query.data.split(":")[1])
        
        # Get category info
        categories = await DatabaseManager.get_categories()
        category = next((c for c in categories if c.id == category_id), None)
        
        if not category:
            await MessageHelper.safe_answer_callback(
                query, 
                "Категория не найдена.", 
                show_alert=True
            )
            return
        
        # Get products in this category
        products = await DatabaseManager.get_products_by_category(category_id)
        
        text = (
            f"📁 **{category.name}**\n\n"
        )
        
        if category.description:
            text += f"📄 {category.description}\n\n"
        
        if products:
            text += f"Продукты ({len(products)}):"
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            for product in products:
                builder.row(
                    types.InlineKeyboardButton(
                        text=f"📦 {product.name}",
                        callback_data=f"view_product:{product.id}"
                    )
                )
            
            builder.row(
                types.InlineKeyboardButton(
                    text="🔙 К категориям",
                    callback_data="knowledge_base"
                )
            )
            
            await MessageHelper.safe_edit_message(
                query,
                text=text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
        else:
            text += "В этой категории пока нет продуктов."
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(
                    text="🔙 К категориям",
                    callback_data="knowledge_base"
                )
            )
            
            await MessageHelper.safe_edit_message(
                query,
                text=text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
        
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid category ID in view_category_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Неверная категория. Попробуйте снова.", 
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in view_category_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Ошибка загрузки категории. Попробуйте снова.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data.startswith("view_product:"))
async def view_product_handler(query: types.CallbackQuery, **kwargs):
    """Handle product view"""
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
        
        # Send image/document if available
        if product.image_file_id:
            try:
                await query.message.answer_photo(
                    photo=product.image_file_id,
                    caption=text,
                    reply_markup=Keyboards.product_actions(product_id, has_test, product.category_id),
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
                    reply_markup=Keyboards.product_actions(product_id, has_test, product.category_id),
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
            reply_markup=Keyboards.product_actions(product_id, has_test, product.category_id),
            parse_mode="Markdown"
        )
        
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid product ID in view_product_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Неверный продукт. Попробуйте снова.", 
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in view_product_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Ошибка загрузки продукта. Попробуйте снова.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "back_to_products")
async def back_to_products_handler(query: types.CallbackQuery, **kwargs):
    """Handle back to products navigation"""
    # Go back to knowledge base
    await knowledge_base_handler(query, **kwargs)
