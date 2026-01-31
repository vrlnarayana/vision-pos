# Webcam Ollama Detection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate Ollama LLava-Phi3 model for real-time webcam-based product detection with inventory-aware matching.

**Architecture:** Frontend captures images on-demand via webcam, sends to new backend endpoint that uses Ollama Llava-Phi3 model with inventory context for detection, backend matches results to inventory using fuzzy matching, returns ranked list of potential matches for user selection.

**Tech Stack:**
- Backend: FastAPI, Ollama API (http://localhost:11434), requests library
- Frontend: React, TypeScript, react-webcam library
- Model: LLava-Phi3 (served via Ollama)

---

## Task 1: Backend Setup - Add Ollama Service

**Files:**
- Create: `backend/app/services/ollama_service.py`
- Modify: `backend/requirements.txt` (add requests)
- Modify: `backend/config.py` (add Ollama endpoint config)

**Step 1: Update requirements.txt**

Edit `backend/requirements.txt` and add:
```
requests==2.31.0
```

**Step 2: Update config.py**

Edit `backend/config.py` and add these constants after existing configs:
```python
# Ollama Configuration
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava-phi3")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))
```

**Step 3: Create ollama_service.py**

Create `backend/app/services/ollama_service.py`:

```python
import base64
import json
import logging
from typing import List, Optional
import requests
from config import config

logger = logging.getLogger(__name__)


class OllamaDetectionResult:
    """Result from Ollama detection."""
    def __init__(self, product_name: str, confidence: float, quantity: int = 1):
        self.product_name = product_name.strip()
        self.confidence = min(max(confidence, 0.0), 1.0)  # Clamp 0-1
        self.quantity = max(quantity, 1)


class OllamaService:
    """Service for interacting with Ollama LLava-Phi3 model."""

    def __init__(self, endpoint: str = None, model: str = None):
        self.endpoint = endpoint or config.OLLAMA_ENDPOINT
        self.model = model or config.OLLAMA_MODEL
        self.api_url = f"{self.endpoint}/api/generate"

    def build_inventory_prompt(self, inventory_names: List[str]) -> str:
        """Build prompt with inventory context."""
        inventory_str = ", ".join(inventory_names)
        prompt = f"""Analyze this image and identify products from our inventory.

Available products: {inventory_str}

Please respond with a JSON object containing detected products. Format:
{{
  "products": [
    {{"name": "product_name_from_list", "confidence": 0.95, "quantity": 1}},
    ...
  ]
}}

Only include products that you see in the image from the available list.
Set confidence as a decimal 0-1.
Be strict - only report products you're confident about.
If no products detected, return {{"products": []}}"""
        return prompt

    def detect_products(
        self,
        image_base64: str,
        inventory_names: List[str]
    ) -> tuple[List[OllamaDetectionResult], int]:
        """
        Detect products in image using Ollama Llava-Phi3.

        Returns: (results, processing_time_ms)
        Raises: ValueError for invalid input, requests.RequestException for API errors
        """
        if not image_base64:
            raise ValueError("Image base64 cannot be empty")

        if not inventory_names:
            raise ValueError("Inventory list cannot be empty")

        prompt = self.build_inventory_prompt(inventory_names)

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False,
                },
                timeout=config.OLLAMA_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            # Parse response to extract products
            response_text = data.get("response", "")
            results = self._parse_response(response_text)

            # Get processing time in milliseconds
            eval_duration = data.get("eval_duration", 0)
            processing_time_ms = eval_duration // 1_000_000  # Convert nanoseconds to ms

            return results, processing_time_ms

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama at {self.endpoint}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise

    def _parse_response(self, response_text: str) -> List[OllamaDetectionResult]:
        """Parse Ollama response and extract products."""
        try:
            # Try to extract JSON from response
            # Look for { and } markers
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start == -1 or end == 0:
                logger.warning(f"No JSON found in response: {response_text[:200]}")
                return []

            json_str = response_text[start:end]
            data = json.loads(json_str)

            results = []
            for product in data.get("products", []):
                try:
                    result = OllamaDetectionResult(
                        product_name=product.get("name", ""),
                        confidence=float(product.get("confidence", 0.0)),
                        quantity=int(product.get("quantity", 1))
                    )
                    if result.product_name:  # Only add non-empty names
                        results.append(result)
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Failed to parse product entry: {product}, error: {e}")
                    continue

            return results

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Ollama response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing Ollama response: {e}")
            return []


# Singleton instance
ollama_service = OllamaService()
```

**Step 4: Commit**

```bash
git add backend/requirements.txt backend/config.py backend/app/services/ollama_service.py
git commit -m "feat: add ollama service for product detection"
```

---

## Task 2: Backend - Add Detection Schemas

**Files:**
- Modify: `backend/app/schemas/scan_item.py` (add new schemas)

**Step 1: Add imports and new schemas**

Edit `backend/app/schemas/scan_item.py` and add at the end before `SessionItemsResponse`:

```python
class ImageDetectionRequest(BaseModel):
    """Request for image-based product detection."""

    image_base64: str = Field(..., description="Base64 encoded JPEG/PNG image")

    @validator('image_base64')
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
```

**Step 2: Commit**

```bash
git add backend/app/schemas/scan_item.py
git commit -m "feat: add image detection request/response schemas"
```

---

## Task 3: Backend - Add Detection Router

**Files:**
- Create: `backend/app/routers/detect.py`
- Modify: `backend/main.py` (include detect router)

**Step 1: Create detect.py router**

Create `backend/app/routers/detect.py`:

```python
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
                ollama_result.product_name,
                threshold=0.6  # Fuzzy match threshold
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
```

**Step 2: Update main.py**

Edit `backend/main.py` and add to imports:
```python
from app.routers import sessions, inventory, checkout, detect
```

Then add to the router includes section (after checkout):
```python
app.include_router(detect.router)
```

**Step 3: Commit**

```bash
git add backend/app/routers/detect.py backend/main.py
git commit -m "feat: add image detection endpoint"
```

---

## Task 4: Backend - Add inventory_service utility method

**Files:**
- Modify: `backend/app/services/inventory_service.py`

**Step 1: Add get_all_inventory method**

Edit `backend/app/services/inventory_service.py` and add this method to the `InventoryService` class:

```python
@staticmethod
def get_all_inventory(db: Session) -> List:
    """Get all inventory items."""
    from app.models import InventoryMaster
    return db.query(InventoryMaster).all()
```

**Step 2: Commit**

```bash
git add backend/app/services/inventory_service.py
git commit -m "feat: add get_all_inventory helper method"
```

---

## Task 5: Frontend Setup - Install Dependency

**Files:**
- Modify: `frontend/package.json`

**Step 1: Add react-webcam**

Edit `frontend/package.json` and add to dependencies:
```json
"react-webcam": "^7.2.0"
```

**Step 2: Install dependencies**

```bash
cd frontend && npm install
```

**Step 3: Update package-lock.json**

```bash
npm install --package-lock-only
```

**Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add react-webcam dependency"
```

---

## Task 6: Frontend - Create WebcamScanner Component

**Files:**
- Create: `frontend/src/components/WebcamScanner.tsx`

**Step 1: Create component**

Create `frontend/src/components/WebcamScanner.tsx`:

```typescript
import { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import { sessionsApi } from '@/api/sessions';

interface WebcamScannerProps {
  sessionId: string;
  onProductsDetected: (products: any[]) => Promise<void>;
  disabled?: boolean;
}

interface DetectionResult {
  inventory_id: string;
  name: string;
  sku: string;
  confidence: number;
  quantity: number;
  matched_from: string;
}

export function WebcamScanner({
  sessionId,
  onProductsDetected,
  disabled = false,
}: WebcamScannerProps) {
  const webcamRef = useRef<Webcam>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [showResults, setShowResults] = useState(false);

  const captureAndDetect = async () => {
    if (!webcamRef.current) return;

    try {
      setLoading(true);
      setError(null);

      // Capture image
      const imageSrc = webcamRef.current.getScreenshot();
      if (!imageSrc) {
        throw new Error('Failed to capture image');
      }

      // Remove data URL prefix to get base64
      const base64Image = imageSrc.replace(/^data:image\/\w+;base64,/, '');

      // Send to backend for detection
      const response = await sessionsApi.detectFromImage(sessionId, base64Image);

      if (response.results && response.results.length > 0) {
        setResults(response.results);
        setShowResults(true);
      } else {
        setError('No products detected in image. Try again.');
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Detection failed. Is Ollama running?';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProduct = async (product: DetectionResult) => {
    try {
      setLoading(true);
      await onProductsDetected([product]);
      setShowResults(false);
      setResults([]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add product';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Webcam Preview */}
      <div className="bg-black rounded-lg overflow-hidden">
        <Webcam
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          screenshotQuality={0.8}
          width={640}
          height={480}
          videoConstraints={{ facingMode: 'environment' }}
        />
      </div>

      {/* Detect Button */}
      <button
        onClick={captureAndDetect}
        disabled={loading || disabled}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400"
      >
        {loading ? 'Detecting...' : 'Detect Products'}
      </button>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Detection Results Modal */}
      {showResults && results.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full max-h-96 overflow-auto">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold">
                Detected Products ({results.length})
              </h3>
            </div>

            <div className="p-4 space-y-2">
              {results.map((product, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectProduct(product)}
                  disabled={loading}
                  className="w-full text-left p-3 border rounded hover:bg-blue-50 disabled:opacity-50"
                >
                  <div className="font-medium">{product.name}</div>
                  <div className="text-sm text-gray-600">SKU: {product.sku}</div>
                  <div className="text-sm text-gray-600">
                    Confidence: {(product.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Detected as: "{product.matched_from}"
                  </div>
                </button>
              ))}
            </div>

            <div className="p-4 border-t">
              <button
                onClick={() => setShowResults(false)}
                className="w-full bg-gray-300 text-gray-800 py-2 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/WebcamScanner.tsx
git commit -m "feat: add webcam scanner component"
```

---

## Task 7: Frontend API - Add detection endpoint

**Files:**
- Modify: `frontend/src/api/sessions.ts`

**Step 1: Add detectFromImage method**

Edit `frontend/src/api/sessions.ts` and add this method to the `sessionsApi` object:

```typescript
detectFromImage: (sessionId: string, imageBase64: string) =>
  apiClient.post<ImageDetectionResponse>(
    `/sessions/${sessionId}/scan/detect-from-image`,
    { image_base64: imageBase64 }
  ),
```

**Step 2: Add types**

Edit `frontend/src/api/sessions.ts` and add these interfaces at the top:

```typescript
interface DetectionResult {
  inventory_id: string;
  name: string;
  sku: string;
  confidence: number;
  quantity: number;
  matched_from: string;
}

interface ImageDetectionResponse {
  results: DetectionResult[];
  processing_time_ms: number;
  model_used: string;
}
```

**Step 3: Commit**

```bash
git add frontend/src/api/sessions.ts
git commit -m "feat: add image detection API client"
```

---

## Task 8: Frontend - Integrate WebcamScanner into ScanSessionPage

**Files:**
- Modify: `frontend/src/pages/ScanSessionPage.tsx`

**Step 1: Import WebcamScanner**

Edit `frontend/src/pages/ScanSessionPage.tsx` and add to imports:
```typescript
import { WebcamScanner } from '@/components/WebcamScanner';
```

**Step 2: Add state for tab selection**

In the `ScanSessionPage` function, add after existing state declarations:
```typescript
const [scanMethod, setScanMethod] = useState<'manual' | 'webcam'>('manual');
```

**Step 3: Create handler for webcam products**

Add this function in `ScanSessionPage`:
```typescript
const handleWebcamDetection = async (detectedProducts: any[]) => {
  for (const product of detectedProducts) {
    // Use the detected product to add to session
    // We'll add via the scan endpoint with the product name
    await scanProductApi.execute(
      sessionId,
      product.name,
      product.confidence
    );
  }
  await loadSessionItems(sessionId);
};
```

**Step 4: Update UI to show both methods**

In the return JSX, update the scan form section to include tabs:

Before the `<ScanProductForm>` component, add:
```typescript
<div className="mb-4 flex gap-2 border-b">
  <button
    onClick={() => setScanMethod('manual')}
    className={`px-4 py-2 font-medium border-b-2 ${
      scanMethod === 'manual'
        ? 'border-blue-600 text-blue-600'
        : 'border-transparent text-gray-600 hover:text-gray-900'
    }`}
  >
    Manual Entry
  </button>
  <button
    onClick={() => setScanMethod('webcam')}
    className={`px-4 py-2 font-medium border-b-2 ${
      scanMethod === 'webcam'
        ? 'border-blue-600 text-blue-600'
        : 'border-transparent text-gray-600 hover:text-gray-900'
    }`}
  >
    Webcam Scanner
  </button>
</div>
```

Then wrap the existing form and add webcam option:
```typescript
{scanMethod === 'manual' ? (
  <div>
    <h2 className="text-lg font-semibold mb-4">Scan Product</h2>
    <ScanProductForm
      onSubmit={handleScanProduct}
      loading={scanProductApi.loading}
    />
  </div>
) : (
  <div>
    <h2 className="text-lg font-semibold mb-4">Webcam Scanner</h2>
    {sessionId && (
      <WebcamScanner
        sessionId={sessionId}
        onProductsDetected={handleWebcamDetection}
        disabled={scanProductApi.loading}
      />
    )}
  </div>
)}
```

**Step 5: Commit**

```bash
git add frontend/src/pages/ScanSessionPage.tsx
git commit -m "feat: integrate webcam scanner into scan session page"
```

---

## Task 9: Documentation - Update README

**Files:**
- Modify: `backend/README.md`
- Modify: `frontend/README.md`

**Step 1: Update backend README**

Add section to `backend/README.md`:

```markdown
## Webcam Product Detection

The system can detect products from webcam images using Ollama with LLava-Phi3 model.

### Prerequisites

1. **Ollama Installation**
   ```bash
   # Download and install from https://ollama.ai
   ollama pull llava-phi3
   ollama serve  # Runs on http://localhost:11434
   ```

2. **Environment Variables**
   ```bash
   OLLAMA_ENDPOINT=http://localhost:11434
   OLLAMA_MODEL=llava-phi3
   OLLAMA_TIMEOUT=30  # seconds
   ```

### API Endpoint

**POST** `/sessions/{session_id}/scan/detect-from-image`

Request:
```json
{
  "image_base64": "iVBORw0KGgo..."
}
```

Response:
```json
{
  "results": [
    {
      "inventory_id": "...",
      "name": "Red Apple",
      "sku": "APPLE001",
      "confidence": 0.95,
      "quantity": 2,
      "matched_from": "apple"
    }
  ],
  "processing_time_ms": 2500,
  "model_used": "llava-phi3"
}
```

### How It Works

1. User opens webcam scanner in scan session
2. Clicks "Detect Products" to capture frame
3. Image sent to backend with session context
4. Backend sends image + full inventory list to Ollama
5. Ollama detects products and returns list
6. Backend fuzzy-matches detected products to inventory
7. Frontend displays matches in ranked order by confidence
8. User selects product to add to cart
```

**Step 2: Update frontend README**

Add section to `frontend/README.md`:

```markdown
## Webcam Scanner

The frontend includes a webcam-based product scanner powered by Ollama LLava-Phi3.

### Usage

1. Navigate to Scan Session page
2. Click "Webcam Scanner" tab
3. Allow camera permission
4. Position product in frame
5. Click "Detect Products"
6. Select correct product from results
7. Product added to cart

### Technical Details

- Uses `react-webcam` for browser camera access
- Captures frames as JPEG (quality 0.8 for balance)
- Sends to backend for AI-powered detection
- Works offline after Ollama model is cached
```

**Step 3: Commit**

```bash
git add backend/README.md frontend/README.md
git commit -m "docs: add webcam detection documentation"
```

---

## Task 10: Docker - Update Environment & Build

**Files:**
- Modify: `.env.docker`
- Modify: `docker-compose.yml` (add Ollama service reference if needed)

**Step 1: Update .env.docker**

Edit `.env.docker` and add:
```bash
# Ollama Configuration
OLLAMA_ENDPOINT=http://host.docker.internal:11434
OLLAMA_MODEL=llava-phi3
OLLAMA_TIMEOUT=30
```

**Step 2: Rebuild frontend**

```bash
cd frontend && npm run build
```

**Step 3: Rebuild backend**

```bash
cd backend && docker build -t visionscan-pos-backend:latest .
```

**Step 4: Commit**

```bash
git add .env.docker docker-compose.yml
git commit -m "build: update environment and docker config for ollama"
```

---

## Summary

**What was built:**
- Backend Ollama service for product detection via LLava-Phi3
- Image detection endpoint with inventory-aware matching
- Frontend webcam scanner component with on-demand capture
- Integration into existing ScanSessionPage
- Complete documentation and Docker setup

**Key files changed:**
- Backend: `ollama_service.py`, `detect.py`, updated configs
- Frontend: `WebcamScanner.tsx`, updated `ScanSessionPage.tsx`
- Both: Documentation updated, dependencies added

**Next steps:**
- Start Ollama locally: `ollama serve`
- Pull model: `ollama pull llava-phi3`
- Run Docker: `docker-compose up -d`
- Test at `http://localhost` → Scan Session → Webcam Scanner tab

**Testing checklist:**
- [ ] Ollama endpoint accessible from backend container
- [ ] Image capture and Base64 encoding works
- [ ] Ollama model responds with valid JSON
- [ ] Fuzzy matching correctly identifies products
- [ ] Webcam permissions work in browser
- [ ] Results display correctly in modal
- [ ] Selected product adds to cart properly
- [ ] Error handling for Ollama unavailability
```

