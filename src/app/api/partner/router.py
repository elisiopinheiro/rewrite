"""Assemble the partner API router."""

from fastapi import APIRouter

from app.api.partner.clusters import router as clusters_router

router = APIRouter(prefix="/v3")
router.include_router(clusters_router)
