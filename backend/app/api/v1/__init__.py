from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.benchmark import router as benchmark_router
from app.api.v1.explain import router as explain_router
from app.api.v1.fraud import router as fraud_router
from app.api.v1.health import router as health_router
from app.api.v1.location import router as location_router
from app.api.v1.prediction import router as prediction_router
from app.api.v1.simulation import router as simulation_router
from app.api.v1.uploads import router as uploads_router


router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(uploads_router, tags=["uploads"])
router.include_router(location_router, tags=["location"])
router.include_router(prediction_router, tags=["prediction"])
router.include_router(fraud_router, tags=["fraud"])
router.include_router(explain_router, tags=["explain"])
router.include_router(simulation_router, tags=["simulation"])
router.include_router(benchmark_router, tags=["benchmark"])

