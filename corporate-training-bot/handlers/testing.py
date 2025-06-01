import logging
import json
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import DatabaseManager
from utils.keyboards import Keyboards
from utils.helpers import MessageHelper

router = Router()
logger = logging.getLogger(__name__)

class TestStates(StatesGroup):
    taking_test = State()

# Store test sessions in memory (in production, use Redis or database)
test_sessions = {}

@router.callback_query(lambda c: c.data == "take_test")
async def take_test_menu(query: types.CallbackQuery, **kwargs):
    """Handle take test menu"""
    try:
        categories = await DatabaseManager.get_categories()
        
        if not categories:
            text = (
                "📝 **Take Test**\n\n"
                "No test categories available yet.\n"
                "Please contact an administrator to add tests."
            )
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(
                    text="🔙 Back to Main",
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
            "📝 **Take Test**\n\n"
            "Choose a category to start testing:"
        )
        
        keyboard = Keyboards.categories_list(categories, "test_category")
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in take_test_menu: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Error loading test menu. Please try again.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data.startswith("test_category:"))
async def test_category_handler(query: types.CallbackQuery, **kwargs):
    """Handle test category selection"""
    try:
        category_id = int(query.data.split(":")[1])
        
        # Get products in this category that have test questions
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                SELECT DISTINCT p.id, p.name, COUNT(tq.id) as question_count
                FROM products p 
                INNER JOIN test_questions tq ON p.id = tq.product_id
                WHERE p.category_id = :category_id
                GROUP BY p.id, p.name
                HAVING COUNT(tq.id) > 0
                ORDER BY p.name
                """),
                {"category_id": category_id}
            )
            products = result.fetchall()
        
        if not products:
            text = (
                "📝 **No Tests Available**\n\n"
                "No test questions are available for products in this category yet.\n"
                "Please try another category or contact an administrator."
            )
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(
                    text="🔙 Back to Categories",
                    callback_data="take_test"
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
            "📝 **Select Product Test**\n\n"
            "Choose a product to take the test:"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        for product in products:
            builder.row(
                types.InlineKeyboardButton(
                    text=f"📝 {product.name} ({product.question_count} questions)",
                    callback_data=f"start_test:{product.id}"
                )
            )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔙 Back to Categories",
                callback_data="take_test"
            )
        )
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid category ID in test_category_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Invalid category. Please try again.", 
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in test_category_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Error loading tests. Please try again.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data.startswith("start_test:"))
async def start_test_handler(query: types.CallbackQuery, state: FSMContext, user=None, **kwargs):
    """Handle test start"""
    try:
        product_id = int(query.data.split(":")[1])
        
        # Get test questions
        questions = await DatabaseManager.get_test_questions(product_id)
        
        if not questions:
            await MessageHelper.safe_answer_callback(
                query, 
                "No questions available for this test.", 
                show_alert=True
            )
            return
        
        # Create test session
        session_key = f"{user.telegram_id}_{product_id}"
        test_sessions[session_key] = {
            'product_id': product_id,
            'questions': [q for q in questions],
            'current_question': 0,
            'answers': {},
            'correct_answers': 0
        }
        
        await state.set_state(TestStates.taking_test)
        await state.update_data(session_key=session_key)
        
        # Show first question
        await show_question(query, session_key)
        
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid product ID in start_test_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Invalid product. Please try again.", 
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in start_test_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Error starting test. Please try again.", 
            show_alert=True
        )

async def show_question(query: types.CallbackQuery, session_key: str):
    """Show current test question"""
    try:
        session = test_sessions.get(session_key)
        if not session:
            await MessageHelper.safe_answer_callback(
                query, 
                "Test session expired. Please start a new test.", 
                show_alert=True
            )
            return
        
        current_idx = session['current_question']
        questions = session['questions']
        
        if current_idx >= len(questions):
            # Test completed
            await complete_test(query, session_key)
            return
        
        question = questions[current_idx]
        
        text = (
            f"📝 **Question {current_idx + 1}/{len(questions)}**\n\n"
            f"❓ {question.question}\n\n"
            f"🔘 A) {question.option_a}\n"
            f"🔘 B) {question.option_b}\n"
            f"🔘 C) {question.option_c}\n"
            f"🔘 D) {question.option_d}\n\n"
            "Choose your answer:"
        )
        
        keyboard = Keyboards.test_question(
            question.id, 
            current_idx + 1, 
            len(questions)
        )
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_question: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Error displaying question. Please try again.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data.startswith("answer:"))
async def answer_handler(query: types.CallbackQuery, state: FSMContext, **kwargs):
    """Handle test answer"""
    try:
        _, question_id, answer = query.data.split(":")
        question_id = int(question_id)
        
        state_data = await state.get_data()
        session_key = state_data.get('session_key')
        
        if not session_key or session_key not in test_sessions:
            await MessageHelper.safe_answer_callback(
                query, 
                "Test session expired. Please start a new test.", 
                show_alert=True
            )
            return
        
        session = test_sessions[session_key]
        current_idx = session['current_question']
        questions = session['questions']
        
        if current_idx >= len(questions):
            await complete_test(query, session_key)
            return
        
        current_question = questions[current_idx]
        
        # Check if answer is correct
        is_correct = answer.upper() == current_question.correct_answer.upper()
        if is_correct:
            session['correct_answers'] += 1
        
        # Store answer
        session['answers'][question_id] = {
            'answer': answer,
            'correct': is_correct
        }
        
        # Move to next question
        session['current_question'] += 1
        
        # Show feedback and continue
        feedback = "✅ Correct!" if is_correct else f"❌ Incorrect. The correct answer was {current_question.correct_answer}."
        await MessageHelper.safe_answer_callback(query, feedback, show_alert=False)
        
        # Show next question or complete test
        await show_question(query, session_key)
        
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid answer format in answer_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Invalid answer format. Please try again.", 
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in answer_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Error processing answer. Please try again.", 
            show_alert=True
        )

async def complete_test(query: types.CallbackQuery, session_key: str):
    """Complete the test and show results"""
    try:
        session = test_sessions.get(session_key)
        if not session:
            return
        
        # Calculate score
        total_questions = len(session['questions'])
        correct_answers = session['correct_answers']
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Save result to database
        user_id = int(session_key.split('_')[0])
        product_id = session['product_id']
        
        await DatabaseManager.save_test_result(
            user_id=user_id,
            product_id=product_id,
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers
        )
        
        # Clean up session
        del test_sessions[session_key]
        
        # Show results
        text = MessageHelper.format_test_result(score, correct_answers, total_questions)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.row(
            types.InlineKeyboardButton(
                text="🔄 Take Another Test",
                callback_data="take_test"
            )
        )
        
        builder.row(
            types.InlineKeyboardButton(
                text="📊 View My Results",
                callback_data="my_results"
            )
        )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🏠 Main Menu",
                callback_data="main_menu"
            )
        )
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in complete_test: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Error completing test. Please try again.", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "my_results")
async def my_results_handler(query: types.CallbackQuery, user=None, **kwargs):
    """Handle user results view"""
    try:
        # Get user's test results
        async with DatabaseManager.AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                SELECT tr.score, tr.total_questions, tr.correct_answers, tr.completed_at, p.name as product_name
                FROM test_results tr
                INNER JOIN products p ON tr.product_id = p.id
                WHERE tr.user_id = :user_id
                ORDER BY tr.completed_at DESC
                LIMIT 10
                """),
                {"user_id": user.telegram_id}
            )
            results = result.fetchall()
        
        if not results:
            text = (
                "📊 **My Results**\n\n"
                "You haven't taken any tests yet.\n"
                "Take your first test to see results here!"
            )
        else:
            text = (
                f"📊 **My Results**\n\n"
                f"Recent test results (showing last {len(results)}):\n\n"
            )
            
            for i, result in enumerate(results, 1):
                date_str = result.completed_at.strftime("%Y-%m-%d %H:%M")
                text += (
                    f"{i}. **{result.product_name}**\n"
                    f"   Score: {result.score:.1f}% ({result.correct_answers}/{result.total_questions})\n"
                    f"   Date: {date_str}\n\n"
                )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if results:
            builder.row(
                types.InlineKeyboardButton(
                    text="🔄 Take Another Test",
                    callback_data="take_test"
                )
            )
        
        builder.row(
            types.InlineKeyboardButton(
                text="🏠 Main Menu",
                callback_data="main_menu"
            )
        )
        
        await MessageHelper.safe_edit_message(
            query,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in my_results_handler: {e}")
        await MessageHelper.safe_answer_callback(
            query, 
            "Error loading results. Please try again.", 
            show_alert=True
        )