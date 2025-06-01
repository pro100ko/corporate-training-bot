import re
from typing import Optional
from aiogram.types import CallbackQuery, Message

class MessageHelper:
    """Helper class for message handling"""
    
    @staticmethod
    async def safe_edit_message(
        message_or_query,
        text: str,
        reply_markup=None,
        parse_mode: Optional[str] = None
    ):
        """Safely edit message, handling both Message and CallbackQuery"""
        try:
            if isinstance(message_or_query, CallbackQuery):
                if message_or_query.message:
                    await message_or_query.message.edit_text(
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
            else:
                await message_or_query.edit_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        except Exception as e:
            # If editing fails, try to send a new message
            try:
                if isinstance(message_or_query, CallbackQuery):
                    if message_or_query.message:
                        await message_or_query.message.answer(
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode
                        )
                else:
                    await message_or_query.answer(
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
            except Exception:
                pass  # Fail silently if both attempts fail

    @staticmethod
    async def safe_answer_callback(query: CallbackQuery, text: str = None, show_alert: bool = False):
        """Safely answer callback query"""
        try:
            await query.answer(text=text, show_alert=show_alert)
        except Exception:
            pass  # Fail silently if answer fails

    @staticmethod
    def format_product_info(product, category_name: str = None) -> str:
        """Format product information for display"""
        text = f"📦 **{product.name}**\n\n"
        
        if category_name:
            text += f"📁 Category: {category_name}\n"
        
        if product.description:
            text += f"📄 Description: {product.description}\n"
        
        return text

    @staticmethod
    def format_test_result(score: float, correct: int, total: int) -> str:
        """Format test result for display"""
        if score >= 80:
            emoji = "🎉"
            status = "Excellent!"
        elif score >= 60:
            emoji = "👍"
            status = "Good job!"
        elif score >= 40:
            emoji = "📚"
            status = "Keep studying!"
        else:
            emoji = "💪"
            status = "Practice more!"
        
        return (
            f"{emoji} **Test Complete!**\n\n"
            f"📊 Score: {score:.1f}%\n"
            f"✅ Correct: {correct}/{total}\n"
            f"📈 Status: {status}"
        )

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown special characters"""
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

class ValidationHelper:
    """Helper class for input validation"""
    
    @staticmethod
    def is_valid_category_name(name: str) -> bool:
        """Validate category name"""
        return 2 <= len(name.strip()) <= 100
    
    @staticmethod
    def is_valid_product_name(name: str) -> bool:
        """Validate product name"""
        return 2 <= len(name.strip()) <= 255
    
    @staticmethod
    def is_valid_description(description: str) -> bool:
        """Validate description"""
        return len(description.strip()) <= 2000
    
    @staticmethod
    def is_valid_question(question: str) -> bool:
        """Validate test question"""
        return 10 <= len(question.strip()) <= 1000
    
    @staticmethod
    def is_valid_option(option: str) -> bool:
        """Validate test option"""
        return 1 <= len(option.strip()) <= 500
    
    @staticmethod
    def is_valid_answer(answer: str) -> bool:
        """Validate correct answer"""
        return answer.upper() in ['A', 'B', 'C', 'D']