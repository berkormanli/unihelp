import fastapi

from src.api.routes.account import router as account_router
from src.api.routes.authentication import router as auth_router
from src.api.routes.post import router as post_router
from src.api.routes.photo import router as photo_router
from src.api.routes.poll import router as poll_router
from src.api.routes.interaction import router as interaction_router
from src.api.routes.search import router as search_router
from src.api.routes.tag import router as tag_router
from src.api.routes.comment import router as comment_router

router = fastapi.APIRouter()

router.include_router(router=account_router)
router.include_router(router=post_router)
router.include_router(router=interaction_router)
router.include_router(router=photo_router)
router.include_router(router=poll_router)
router.include_router(router=auth_router)
router.include_router(router=search_router)
router.include_router(router=tag_router)
router.include_router(router=comment_router)