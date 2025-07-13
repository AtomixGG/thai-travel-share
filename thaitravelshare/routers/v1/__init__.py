from fastapi import APIRouter
from . import ( 
    user_router,
    travel_router,
    province_router,
    system_router,
)

router = APIRouter(prefix="/v1")
router.include_router(user_router.router)
router.include_router(travel_router.router)
router.include_router(province_router.router)
router.include_router(system_router.router)