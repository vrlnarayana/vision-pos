import base64
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScanSession
from app.schemas.scan_item import (
    ImageDetectionRequest,
    ImageDetectionResponse,
    DetectionResult,
)
from app.services.ollama_service import ollama_service
from app.services.inventory_service import InventoryService
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions/{session_id}/scan", tags=["detect"])


@router.post("/detect-from-image", response_model=ImageDetectionResponse)
def detect_from_image(
    session_id: UUID,
    request: ImageDetectionRequest,
    db: Session = Depends(get_db),
):
    """
    Detect products from image using Ollama Llava-Phi3.

    Returns list of potential product matches from inventory.
    """
    # Verify session exists
    session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    try:
        # Get all inventory items for matching
        inventory_items = InventoryService.get_all_inventory(db)
        inventory_names = [item.name for item in inventory_items]

        if not inventory_names:
            raise HTTPException(
                status_code=400,
                detail="No inventory items available for matching"
            )

        # Detect products using Ollama
        ollama_results, processing_time = ollama_service.detect_products(
            request.image_base64,
            inventory_names
        )

        # Match detected products to inventory
        detection_results: List[DetectionResult] = []

        for ollama_result in ollama_results:
            # Find best match in inventory
            best_match = InventoryService.match_product(
                db,
                ollama_result.product_name
            )

            if best_match:
                detection_results.append(
                    DetectionResult(
                        inventory_id=best_match.id,
                        name=best_match.name,
                        sku=best_match.sku,
                        confidence=ollama_result.confidence,
                        quantity=ollama_result.quantity,
                        matched_from=ollama_result.product_name,
                    )
                )

        return ImageDetectionResponse(
            results=detection_results,
            processing_time_ms=processing_time,
            model_used="llava-phi3",
        )

    except ValueError as e:
        logger.warning(f"Invalid detection request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        logger.error(f"Ollama connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Detection service unavailable. Is Ollama running?"
        )
    except Exception as e:
        logger.error(f"Unexpected error during detection: {e}")
        raise HTTPException(status_code=500, detail="Detection failed")
