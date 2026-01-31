from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from difflib import SequenceMatcher
from sqlalchemy.orm import Session

from app.models import InventoryMaster
from app.schemas.inventory import InventoryCreateRequest, InventoryUpdateRequest
from config import config


class InventoryService:
    """Service layer for inventory operations."""

    @staticmethod
    def create_inventory(
        db: Session, request: InventoryCreateRequest
    ) -> InventoryMaster:
        """Create a new inventory item."""
        # Check if SKU already exists
        existing = db.query(InventoryMaster).filter_by(sku=request.sku).first()
        if existing:
            raise ValueError(f"SKU {request.sku} already exists")

        item = InventoryMaster(
            sku=request.sku,
            name=request.name,
            category=request.category,
            price=request.price,
            stock=request.stock,
            aliases=request.aliases,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_inventory(db: Session, inventory_id: UUID) -> Optional[InventoryMaster]:
        """Get inventory item by ID."""
        return db.query(InventoryMaster).filter_by(id=inventory_id).first()

    @staticmethod
    def list_inventory(db: Session, limit: int = 100, offset: int = 0) -> tuple:
        """List all inventory items."""
        query = db.query(InventoryMaster)
        total = query.count()
        items = query.limit(limit).offset(offset).all()
        return items, total

    @staticmethod
    def get_all_inventory(db: Session) -> List[InventoryMaster]:
        """Get all inventory items without pagination."""
        return db.query(InventoryMaster).all()

    @staticmethod
    def update_inventory(
        db: Session, inventory_id: UUID, request: InventoryUpdateRequest
    ) -> Optional[InventoryMaster]:
        """Update inventory item."""
        item = db.query(InventoryMaster).filter_by(id=inventory_id).first()
        if not item:
            return None

        if request.name is not None:
            item.name = request.name
        if request.category is not None:
            item.category = request.category
        if request.price is not None:
            item.price = request.price
        if request.stock is not None:
            item.stock = request.stock
        if request.aliases is not None:
            item.aliases = request.aliases

        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def match_product(db: Session, detected_name: str) -> Optional[InventoryMaster]:
        """
        Match a detected product name to inventory.

        Strategy:
        1. Try exact SKU match
        2. Try exact name match
        3. Try alias match
        4. Try fuzzy match
        5. Return None if no match
        """
        detected_lower = detected_name.lower().strip()

        # 1. Exact SKU match
        item = db.query(InventoryMaster).filter_by(sku=detected_lower).first()
        if item:
            return item

        # 2. Exact name match (case-insensitive)
        item = (
            db.query(InventoryMaster)
            .filter(InventoryMaster.name.ilike(detected_lower))
            .first()
        )
        if item:
            return item

        # 3. Alias match
        all_items = db.query(InventoryMaster).all()
        for item in all_items:
            if item.aliases:
                for alias in item.aliases:
                    if alias.lower() == detected_lower:
                        return item

        # 4. Fuzzy match
        best_match = None
        best_score = 0.0

        for item in all_items:
            # Try matching against name
            score = SequenceMatcher(
                None, detected_lower, item.name.lower()
            ).ratio()
            if score > best_score:
                best_score = score
                best_match = item

            # Try matching against aliases
            if item.aliases:
                for alias in item.aliases:
                    score = SequenceMatcher(
                        None, detected_lower, alias.lower()
                    ).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = item

        if best_score >= config.FUZZY_MATCH_THRESHOLD:
            return best_match

        return None

    @staticmethod
    def update_stock(
        db: Session, inventory_id: UUID, change_qty: int
    ) -> Optional[InventoryMaster]:
        """Update stock for inventory item."""
        item = db.query(InventoryMaster).filter_by(id=inventory_id).first()
        if not item:
            return None

        item.stock += change_qty
        if item.stock < 0:
            raise ValueError(f"Insufficient stock for {item.sku}")

        db.commit()
        db.refresh(item)
        return item
