from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanProductRequest(BaseModel):
    """Request schema for scanning a product."""

    detected_name: str = Field(..., min_length=1, max_length=255)
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class ScanItemResponse(BaseModel):
    """Response schema for scanned item."""

    id: UUID
    session_id: UUID
    inventory_id: Optional[UUID]
    detected_name: str
    confidence: float
    quantity: int
    unit_price: Optional[Decimal]
    first_seen: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanItemDetailResponse(BaseModel):
    """Detailed response including inventory info."""

    id: UUID
    session_id: UUID
    inventory_id: Optional[UUID]
    detected_name: str
    confidence: float
    quantity: int
    unit_price: Optional[Decimal]
    first_seen: datetime
    created_at: datetime
    inventory_name: Optional[str]
    inventory_sku: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ImageDetectionRequest(BaseModel):
    """Request for image-based product detection."""

    image_base64: str = Field(..., description="Base64 encoded JPEG/PNG image")

    @field_validator('image_base64')
    @classmethod
    def validate_image(cls, v):
        if not v:
            raise ValueError("Image cannot be empty")
        if len(v) > 5_000_000:  # 5MB limit
            raise ValueError("Image too large (max 5MB)")
        # Basic validation that it looks like base64
        if not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in v):
            raise ValueError("Invalid base64 encoding")
        return v


class DetectionResult(BaseModel):
    """Single product detection result."""

    inventory_id: UUID
    name: str
    sku: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    quantity: int = Field(..., ge=1)
    matched_from: str  # Original detected name that was matched


class ImageDetectionResponse(BaseModel):
    """Response from image-based detection endpoint."""

    results: List[DetectionResult]
    processing_time_ms: int
    model_used: str = "llava-phi3"


class SessionItemsResponse(BaseModel):
    """Response schema for session items."""

    items: List[ScanItemDetailResponse]
    total_count: int
    subtotal: Decimal
