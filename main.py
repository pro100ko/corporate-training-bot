import logging
import os
import sys
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

# Import configuration
from config import BOT_TOKEN, PORT, WEBHOOK_URL, WEBHOOK_PATH

# Import database
from database import init_database

# Import middleware
from middleware.auth import AuthMiddleware

# Import handlers
from handlers import (
    start_router,
    admin_router,
    knowledge_router,
    testing_router,
    search_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("[BOOT] Corporate Training Bot started")

# Create bot and dispatcher with memory storage for FSM
storage = MemoryStorage()

# Validate BOT_TOKEN before creating bot
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is required but not set")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Register middleware
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

# Register routers
dp.include_router(start_router)
dp.include_router(admin_router)
dp.include_router(knowledge_router)
dp.include_router(testing_router)
dp.include_router(search_router)

# Global error handler
@dp.error()
async def error_handler(event, exception):
    """Global error handler"""
    logger.error(f"Error occurred: {exception}")
    
    if hasattr(event, 'message') and event.message:
        try:
            await event.message.answer(
                "❌ Произошла неожиданная ошибка. Попробуйте снова или обратитесь в поддержку."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    return True

# Fallback handler for unhandled messages
@dp.message()
async def fallback_handler(message: types.Message, **kwargs):
    """Fallback handler for unhandled messages"""
    user_id = message.from_user.id if message.from_user else 0
    logger.info(f"Unhandled message from user {user_id}: {message.text}")
    
    text = (
        "🤔 Я не понимаю эту команду.\n\n"
        "Используйте /start чтобы увидеть доступные опции или выберите из меню ниже:"
    )
    
    from utils.keyboards import Keyboards
    await message.answer(
        text=text,
        reply_markup=Keyboards.main_menu(is_admin=kwargs.get('is_admin', False))
    )

# Fallback handler for unhandled callbacks
@dp.callback_query()
async def fallback_callback_handler(query: types.CallbackQuery, **kwargs):
    """Fallback handler for unhandled callbacks"""
    user_id = query.from_user.id if query.from_user else 0
    logger.info(f"Unhandled callback from user {user_id}: {query.data}")
    
    from utils.helpers import MessageHelper
    await MessageHelper.safe_answer_callback(
        query, 
        "❌ Это действие недоступно. Попробуйте снова.", 
        show_alert=True
    )

# Create aiohttp app
app = web.Application()

# Health check endpoint
async def health(request):
    """Health check endpoint"""
    logger.info("[HTTP] Health check requested")
    return web.Response(text="OK", content_type="text/plain")

app.router.add_get("/health", health)

# Root endpoint
async def root(request):
    """Root endpoint"""
    logger.info("[HTTP] Root endpoint requested")
    return web.Response(
        text="Corporate Training Bot is running",
        content_type="text/plain"
    )

app.router.add_get("/", root)

# Webhook handler
async def webhook_handler(request):
    """Handle incoming webhook requests"""
    logger.info("[HTTP] Webhook POST received")
    try:
        update_data = await request.json()
        update = types.Update.model_validate(update_data)
        logger.info(f"[UPDATE] Processing update: {update.update_id}")
        
        await dp.feed_update(bot, update)
        
    except Exception as e:
        logger.error(f"[ERROR] Webhook handler error: {e}")
        return web.Response(status=500, text="Internal Server Error")
    
    return web.Response(text="OK")

app.router.add_post(WEBHOOK_PATH, webhook_handler)

# Startup handler
async def on_startup(app):
    """Application startup handler"""
    logger.info("[STARTUP] Initializing application...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("[STARTUP] Database initialized")
        
        # Try to set webhook, but don't fail if it can't be set
        try:
            await bot.set_webhook(WEBHOOK_URL)
            logger.info(f"[STARTUP] Webhook set to: {WEBHOOK_URL}")
        except Exception as webhook_error:
            logger.warning(f"[STARTUP] Could not set webhook: {webhook_error}")
            logger.info("[STARTUP] Bot will work in webhook mode when accessible")
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"[STARTUP] Bot started: @{bot_info.username}")
        
    except Exception as e:
        logger.error(f"[STARTUP ERROR] {e}")
        # Don't exit on webhook errors, continue running
        if "webhook" not in str(e).lower():
            sys.exit(1)

app.on_startup.append(on_startup)

# Shutdown handler
async def on_shutdown(app):
    """Application shutdown handler"""
    logger.info("[SHUTDOWN] Shutting down application...")
    
    try:
        # Delete webhook
        await bot.delete_webhook()
        logger.info("[SHUTDOWN] Webhook deleted")
        
        # Close bot session
        await bot.session.close()
        logger.info("[SHUTDOWN] Bot session closed")
        
    except Exception as e:
        logger.error(f"[SHUTDOWN ERROR] {e}")

app.on_shutdown.append(on_shutdown)

# Main execution
if __name__ == "__main__":
    logger.info("[MAIN] Starting aiohttp web server...")
    
    try:
        web.run_app(
            app,
            host="0.0.0.0",
            port=PORT,
            access_log=logger
        )
    except Exception as e:
        logger.error(f"[MAIN ERROR] {e}")
        sys.exit(1)
