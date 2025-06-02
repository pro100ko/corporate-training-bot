import logging
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from models import Base, User, Category, Product, TestQuestion, TestResult
from config import DATABASE_URL
from datetime import datetime

logger = logging.getLogger(__name__)

# Create async engine with proper configuration
if DATABASE_URL.startswith("postgresql"):
    # For PostgreSQL with asyncpg, handle SSL properly
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        connect_args={"ssl": "require"}
    )
else:
    # For SQLite
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_database():
    """Initialize database and create all tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def get_session():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

class DatabaseManager:
    """Database manager for common operations"""
    
    # Make AsyncSessionLocal accessible as class attribute
    AsyncSessionLocal = AsyncSessionLocal
    
    @staticmethod
    async def get_or_create_user(telegram_id: int, username: Optional[str] = None, 
                               first_name: Optional[str] = None, last_name: Optional[str] = None, 
                               is_admin: bool = False):
        """Get existing user or create new one"""
        async with AsyncSessionLocal() as session:
            # Try to get existing user
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Update last activity and other fields
                user.last_activity = datetime.utcnow()
                if username:
                    user.username = username
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                await session.commit()
                return user
            else:
                # Create new user
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=is_admin
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
    
    @staticmethod
    async def get_categories():
        """Get all categories"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Category).order_by(Category.name))
            return result.scalars().all()
    
    @staticmethod
    async def get_products_by_category(category_id: int):
        """Get products by category"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product).where(Product.category_id == category_id).order_by(Product.name)
            )
            return result.scalars().all()
    
    @staticmethod
    async def search_products(query: str):
        """Search products by name"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product).where(Product.name.ilike(f"%{query}%")).order_by(Product.name)
            )
            return result.scalars().all()
    
    @staticmethod
    async def get_test_questions(product_id: int):
        """Get test questions for a product"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TestQuestion).where(TestQuestion.product_id == product_id)
            )
            return result.scalars().all()
    
    @staticmethod
    async def save_test_result(user_id: int, product_id: int, score: float, 
                             total_questions: int, correct_answers: int):
        """Save test result"""
        async with AsyncSessionLocal() as session:
            test_result = TestResult(
                user_id=user_id,
                product_id=product_id,
                score=score,
                total_questions=total_questions,
                correct_answers=correct_answers
            )
            session.add(test_result)
            await session.commit()
            return test_result
