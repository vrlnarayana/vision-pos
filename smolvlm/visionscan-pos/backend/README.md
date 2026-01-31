# VisionScan POS - Backend Service

FastAPI-based REST API for retail point-of-sale system with real-time inventory management and session-based checkout.

## Overview

The backend service handles:
- **Session Management**: Create and manage checkout sessions
- **Product Detection**: Scan and match products with intelligent fuzzy matching
- **Inventory Management**: Track stock levels and movements
- **Checkout Processing**: Calculate totals and update inventory

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15 (via SQLAlchemy 2.0)
- **Validation**: Pydantic 2.5
- **Server**: Uvicorn 0.24
- **Python**: 3.11+

## Quick Start

### Local Development

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL

# Run migrations (if using Supabase/PostgreSQL)
psql -d visitionscan_pos -f migrations/001_initial_schema.sql

# Start server
python main.py
```

Server runs on **http://localhost:8000**

### With Docker

```bash
# From project root
docker-compose up -d backend

# View logs
docker-compose logs -f backend

# Connect to container
docker-compose exec backend bash
```

## API Endpoints

### Sessions
```
POST   /sessions/start              - Start new scan session
GET    /sessions/{session_id}       - Get session details
POST   /sessions/{session_id}/end   - End session
POST   /sessions/{session_id}/scan  - Scan product
GET    /sessions/{session_id}/items - Get session items
```

### Inventory
```
GET    /inventory                   - List all items
POST   /inventory                   - Create new item
GET    /inventory/{id}              - Get item details
PUT    /inventory/{id}              - Update item
```

### Checkout
```
POST   /checkout/{session_id}       - Process checkout
POST   /checkout/restock/{id}       - Restock inventory
```

### Health & Docs
```
GET    /health                      - Health check
GET    /docs                        - Swagger UI
GET    /openapi.json                - OpenAPI spec
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image definition
├── .env.example          # Environment template
├── migrations/           # Database migrations
│   └── 001_initial_schema.sql
└── app/
    ├── database.py       # SQLAlchemy setup
    ├── models/          # ORM models
    │   ├── inventory.py
    │   ├── session.py
    │   ├── scan_item.py
    │   └── movement.py
    ├── schemas/         # Pydantic models
    │   ├── inventory.py
    │   ├── session.py
    │   ├── scan_item.py
    │   └── movement.py
    ├── services/        # Business logic
    │   ├── inventory_service.py
    │   ├── session_service.py
    │   └── checkout_service.py
    └── routers/         # API endpoints
        ├── sessions.py
        ├── inventory.py
        └── checkout.py
```

## Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/visitionscan_pos

# API
DEBUG=false
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Fuzzy Matching
FUZZY_MATCH_THRESHOLD=0.6
```

## Database Schema

### inventory_master
Product catalog with pricing and stock tracking.

```
id (UUID)          - Primary key
sku (VARCHAR)      - Unique product SKU
name (VARCHAR)     - Product name
category (VARCHAR) - Product category
price (NUMERIC)    - Unit price
stock (INTEGER)    - Available quantity
aliases (TEXT[])   - Product aliases for matching
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### scan_sessions
Shopping sessions with checkout tracking.

```
id (UUID)              - Primary key
status (VARCHAR)       - 'active' or 'completed'
check_in_time (TIMESTAMP)
check_out_time (TIMESTAMP)
total_amount (NUMERIC)
created_at (TIMESTAMP)
```

### scan_items
Products detected/scanned in a session.

```
id (UUID)            - Primary key
session_id (UUID)    - Foreign key to scan_sessions
inventory_id (UUID)  - Foreign key to inventory_master
detected_name (VARCHAR)
confidence (FLOAT)   - Detection confidence (0-1)
quantity (INTEGER)   - Quantity of this item
unit_price (NUMERIC)
first_seen (TIMESTAMP)
created_at (TIMESTAMP)
```

### inventory_movements
Stock change tracking for auditing.

```
id (UUID)           - Primary key
inventory_id (UUID) - Foreign key to inventory_master
change_qty (INTEGER)
reason (VARCHAR)    - 'sale' or 'restock'
session_id (UUID)   - Related session (if applicable)
created_at (TIMESTAMP)
```

## Business Logic

### Product Matching Algorithm

When a product is scanned, the system matches it to inventory using this priority:

1. **Exact SKU Match** - Direct SKU lookup
2. **Exact Name Match** - Case-insensitive name comparison
3. **Alias Match** - Check product aliases array
4. **Fuzzy Match** - SequenceMatcher with 0.6 threshold
5. **No Match** - Returns unmatched item for manual reconciliation

### Session Deduplication

When the same product is scanned multiple times:
- If already in session: increment quantity
- If new: create new scan_item

### Checkout Process

1. **Validate** - Ensure all items are matched and stock is sufficient
2. **Bill** - Calculate totals for each item
3. **Update** - Reduce inventory stock levels
4. **Track** - Create inventory_movement records
5. **Complete** - Mark session as completed with timestamp

## Error Handling

| Status | Reason |
|--------|--------|
| 400 | Invalid input (validation error) |
| 404 | Resource not found |
| 409 | Conflict (e.g., insufficient stock) |
| 500 | Server error |

Example error response:
```json
{
  "detail": "Insufficient stock for Red Apple. Available: 1, Required: 3"
}
```

## Development

### Running Tests

```bash
# Type checking
python -m mypy app/

# Run tests (when available)
pytest tests/
```

### Adding New Endpoints

1. Create service method in `app/services/`
2. Create schema in `app/schemas/`
3. Create router in `app/routers/`
4. Include router in `main.py`

### Database Migrations

```bash
# Create migration
# Edit migrations/XXX_description.sql

# Apply migration
psql -d visitionscan_pos -f migrations/XXX_description.sql
```

## Performance Tuning

### Database Indexes
Automatically created on:
- `inventory_master.sku` - SKU lookups
- `scan_sessions.status` - Session filtering
- `scan_items.session_id` - Session item queries
- `inventory_movements.inventory_id` - Movement tracking

### Connection Pooling
- Pool size: 5 connections
- Max overflow: 10 connections
- Recycle: 3600 seconds

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### Database Connection
```bash
curl http://localhost:8000/docs
# Interactive API documentation
```

### Logs
```bash
# Local development
tail -f server.log

# Docker
docker-compose logs -f backend
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Update `CORS_ORIGINS` to your domain
- [ ] Use external PostgreSQL (Supabase, AWS RDS)
- [ ] Set strong database password
- [ ] Configure SSL/TLS
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Enable database backups
- [ ] Configure rate limiting

### Docker Deployment

```bash
# Build image
docker build -t visionscan-backend ./backend

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e DEBUG="false" \
  visionscan-backend
```

## Troubleshooting

### Database Connection Error
```
Error: psycopg2.OperationalError: could not connect to server
```

Solution:
- Verify DATABASE_URL format
- Check PostgreSQL is running
- Verify credentials
- Check network connectivity

### Import Error
```
ModuleNotFoundError: No module named 'app'
```

Solution:
- Ensure you're in the `backend/` directory
- Verify virtual environment is activated
- Run `pip install -r requirements.txt`

### CORS Error
```
Access to XMLHttpRequest blocked by CORS policy
```

Solution:
- Update `CORS_ORIGINS` in `.env`
- Include your frontend URL
- Restart backend service

## Security

- **Input Validation**: Pydantic validates all requests
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **CORS Configured**: Restricted to specified origins
- **No Secrets in Code**: Use environment variables

## API Example Usage

### Start Session
```bash
curl -X POST http://localhost:8000/sessions/start
# Returns: {"id": "uuid...", "status": "active", ...}
```

### Scan Product
```bash
curl -X POST http://localhost:8000/sessions/{id}/scan \
  -H "Content-Type: application/json" \
  -d '{"detected_name": "apple", "confidence": 0.95}'
```

### Checkout
```bash
curl -X POST http://localhost:8000/checkout/{session_id}
# Returns: {"session_id": "...", "items": [...], "total": 15.50, ...}
```

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

## Support

- API Docs: http://localhost:8000/docs
- Code: `/Users/vrln/smolvlm/visionscan-pos/backend/`
- Guide: `../claude.md`

## License

MIT
