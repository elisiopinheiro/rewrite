"""Assemble the M4W API router."""

from fastapi import APIRouter

from app.api.m4w.clusters import router as clusters_router
from app.api.m4w.features import router as features_router
from app.api.m4w.locks import router as locks_router
from app.api.m4w.operations import router as operations_router
from app.api.m4w.releases import router as releases_router

router = APIRouter(prefix="/v3")
router.include_router(clusters_router)
router.include_router(features_router)
router.include_router(locks_router)
router.include_router(operations_router)
router.include_router(releases_router)
