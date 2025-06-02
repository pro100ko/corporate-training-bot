from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class Keyboards:
    """Utility class for creating inline keyboards"""
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📚 База знаний",
                callback_data="knowledge_base"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔍 Поиск продуктов",
                callback_data="search_products"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📝 Пройти тест",
                callback_data="take_test"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📊 Мои результаты",
                callback_data="my_results"
            )
        )
        
        if is_admin:
            builder.row(
                InlineKeyboardButton(
                    text="⚙️ Панель администратора",
                    callback_data="admin_panel"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        """Admin panel keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📁 Управление категориями",
                callback_data="admin_categories"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📦 Управление продуктами",
                callback_data="admin_products"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="❓ Управление тестами",
                callback_data="admin_questions"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="admin_stats"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 В главное меню",
                callback_data="main_menu"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def categories_list(categories: List, action_prefix: str = "view_category") -> InlineKeyboardMarkup:
        """Categories list keyboard"""
        builder = InlineKeyboardBuilder()
        
        for category in categories:
            builder.row(
                InlineKeyboardButton(
                    text=f"📁 {category.name}",
                    callback_data=f"{action_prefix}:{category.id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 В главное меню",
                callback_data="main_menu"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def products_list(products: List, action_prefix: str = "view_product") -> InlineKeyboardMarkup:
        """Products list keyboard"""
        builder = InlineKeyboardBuilder()
        
        for product in products:
            builder.row(
                InlineKeyboardButton(
                    text=f"📦 {product.name}",
                    callback_data=f"{action_prefix}:{product.id}"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def product_actions(product_id: int, has_test: bool = False, category_id: int = None) -> InlineKeyboardMarkup:
        """Product actions keyboard"""
        builder = InlineKeyboardBuilder()
        
        if has_test:
            builder.row(
                InlineKeyboardButton(
                    text="📝 Пройти тест",
                    callback_data=f"start_test:{product_id}"
                )
            )
        
        if category_id:
            builder.row(
                InlineKeyboardButton(
                    text="🔙 К продуктам",
                    callback_data=f"view_category:{category_id}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="🔙 К категориям",
                    callback_data="knowledge_base"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def test_question(question_id: int, current_question: int, total_questions: int) -> InlineKeyboardMarkup:
        """Test question keyboard"""
        builder = InlineKeyboardBuilder()
        
        # Answer options
        for option in ['A', 'B', 'C', 'D']:
            builder.row(
                InlineKeyboardButton(
                    text=f"🔘 {option}",
                    callback_data=f"answer:{question_id}:{option}"
                )
            )
        
        # Progress info (non-clickable)
        builder.row(
            InlineKeyboardButton(
                text=f"📊 Вопрос {current_question}/{total_questions}",
                callback_data="noop"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def admin_category_actions(category_id: int) -> InlineKeyboardMarkup:
        """Admin category actions keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"edit_category:{category_id}"
            ),
            InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"delete_category:{category_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 К категориям",
                callback_data="admin_categories"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def admin_product_actions(product_id: int) -> InlineKeyboardMarkup:
        """Admin product actions keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"edit_product:{product_id}"
            ),
            InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"delete_product:{product_id}"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 К продуктам",
                callback_data="admin_products"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def confirm_action(action_data: str) -> InlineKeyboardMarkup:
        """Confirmation keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"confirm:{action_data}"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel"
            )
        )
        
        return builder.as_markup()
