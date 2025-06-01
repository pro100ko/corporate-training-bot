from .start import router as start_router
from .admin import router as admin_router
from .knowledge import router as knowledge_router
from .testing import router as testing_router
from .search import router as search_router

# Export all routers
__all__ = [
    'start_router',
    'admin_router', 
    'knowledge_router',
    'testing_router',
    'search_router'
]