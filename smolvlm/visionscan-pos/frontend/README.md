# VisionScan POS - Frontend Service

Modern React-based user interface for retail point-of-sale system with real-time session management and inventory tracking.

## Overview

The frontend service provides:
- **Scan Session**: Start sessions, scan products, view items, process checkout
- **Inventory Management**: View all products, add new items, manage stock
- **Real-time Updates**: Live item lists and price calculations
- **Error Handling**: User-friendly error messages and loading states

## Technology Stack

- **Framework**: React 18.2
- **Language**: TypeScript 5.2
- **Build Tool**: Vite 5.0
- **Styling**: Tailwind CSS 3.3
- **HTTP Client**: Fetch API
- **Package Manager**: npm

## Quick Start

### Local Development

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env: VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

App runs on **http://localhost:5173** with auto-reload.

### With Docker

```bash
# From project root
docker-compose up -d frontend

# View logs
docker-compose logs -f frontend

# Access at http://localhost:3000
```

## Project Structure

```
frontend/
├── package.json           # Dependencies and scripts
├── tsconfig.json          # TypeScript configuration
├── vite.config.ts         # Vite build configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── index.html             # HTML entry point
├── Dockerfile             # Docker image definition
├── .env.example          # Environment template
└── src/
    ├── main.tsx          # React entry point
    ├── App.tsx           # Root component with navigation
    ├── api/              # API communication layer
    │   ├── client.ts     # Fetch API wrapper
    │   ├── sessions.ts   # Session API endpoints
    │   └── inventory.ts  # Inventory API endpoints
    ├── pages/            # Page components
    │   ├── ScanSessionPage.tsx
    │   └── InventoryPage.tsx
    ├── components/       # Reusable components
    │   ├── ScanProductForm.tsx
    │   ├── ScannedItemsList.tsx
    │   ├── InventoryTable.tsx
    │   └── InventoryForm.tsx
    ├── hooks/            # Custom React hooks
    │   └── useApi.ts
    ├── types/            # TypeScript interfaces
    │   ├── session.ts
    │   ├── inventory.ts
    │   └── index.ts
    └── styles/           # Global styles
        └── index.css
```

## Configuration

### Environment Variables (.env)

```bash
# API endpoint
VITE_API_URL=http://localhost:8000
```

## Features

### Scan Session Page

**Start a new scanning session:**
- Click "Start New Session" button
- Session ID displayed for reference

**Scan products:**
- Enter product name or barcode
- Adjust confidence level (0-100%)
- System automatically matches to inventory
- Duplicate products increment quantity

**View scanned items:**
- Real-time list of scanned items
- Shows matched product name and SKU
- Displays quantity and subtotal
- Calculates running total

**Checkout:**
- Validates all items are matched
- Checks sufficient stock
- Displays bill with itemized charges
- Shows final total
- Option to start new session

### Inventory Management Page

**View inventory:**
- Table of all products
- Shows SKU, name, category, price, stock
- Color-coded stock levels (green=available, red=out)
- Refresh button for real-time updates

**Add new items:**
- Form to create inventory items
- Required fields: SKU, Name, Price
- Optional fields: Category, Stock, Aliases
- Form validation with error messages
- Auto-updates table on success

## Component Architecture

### API Client (`api/client.ts`)

Base HTTP client with:
- GET, POST, PUT, DELETE methods
- Automatic JSON serialization
- Error handling with timeout support
- Configurable base URL

```typescript
// Usage
const data = await apiClient.get<T>(endpoint);
const result = await apiClient.post<T>(endpoint, body);
```

### Custom Hook (`hooks/useApi.ts`)

React hook for async API calls:

```typescript
const { data, loading, error, execute } = useApi(apiFunction);

// Execute the API call
await execute(args);
```

Manages:
- Loading state
- Error state
- Data state
- Automatic cleanup

### Type Definitions (`types/`)

TypeScript interfaces for:
- Session and ScanItem
- Inventory and InventoryList
- Checkout and BillItem
- Full type safety across app

## Page Components

### ScanSessionPage

Manages:
- Session lifecycle (start, scan, end, checkout)
- Item scanning and deduplication
- Real-time item list updates
- Checkout processing
- Completion screen with bill

State:
- `session` - Current session object
- `items` - Scanned items in session
- `loading` - API call loading state
- `error` - Error messages
- `checkoutData` - Final bill after checkout

### InventoryPage

Manages:
- Inventory list loading
- New item creation
- Form visibility toggle
- Real-time table updates

State:
- `items` - All inventory items
- `loading` - API call loading state
- `error` - Error messages
- `showForm` - Form visibility

## Styling

**Tailwind CSS** provides:
- Responsive design
- Consistent spacing and colors
- Dark mode compatible (optional)
- Utility-first approach

Key classes used:
- `bg-*` - Background colors
- `px-*`, `py-*` - Padding
- `text-*` - Text colors and sizes
- `rounded` - Border radius
- `border` - Borders
- `hover:*` - Hover states
- `disabled:*` - Disabled states

## Scripts

```bash
# Development
npm run dev          # Start Vite dev server

# Production
npm run build        # Build for production
npm run preview      # Preview production build
npm run type-check   # Run TypeScript type checker

# Code Quality
npm run lint         # Lint with ESLint (if configured)
```

## API Integration

### Sessions API

```typescript
// Start session
sessionsApi.startSession()

// Get session details
sessionsApi.getSession(sessionId)

// Scan product
sessionsApi.scanProduct(sessionId, name, confidence)

// Get session items
sessionsApi.getSessionItems(sessionId)

// Checkout
sessionsApi.checkout(sessionId)

// End session
sessionsApi.endSession(sessionId)
```

### Inventory API

```typescript
// List inventory
inventoryApi.listInventory(limit, offset)

// Get item
inventoryApi.getInventory(id)

// Create item
inventoryApi.createInventory(data)

// Update item
inventoryApi.updateInventory(id, data)
```

## Error Handling

**API Errors:**
- Display user-friendly error messages
- Red error boxes in UI
- Automatic error clearing on retry

**Form Validation:**
- Input validation on change
- Required field checks
- Number range validation
- Disabled submit button on invalid input

**Loading States:**
- Disabled buttons while loading
- "Loading..." text in buttons
- Loading indicators in tables

## Performance Optimization

### Code Splitting
- Lazy page components with React
- Dynamic imports for large modules

### Rendering Optimization
- Memoized components prevent unnecessary renders
- Key props on lists for efficient updates

### Styling
- Tailwind CSS tree-shaking removes unused styles
- Minimal CSS bundle size

### Build Optimization
- Vite provides fast builds
- Code splitting by route
- Asset minification

## Development Workflow

### Adding a New Component

1. Create component in `src/components/`
2. Define TypeScript props interface
3. Export from file
4. Import and use in pages
5. Style with Tailwind CSS

```typescript
interface Props {
  title: string;
  onSubmit: () => void;
}

export function MyComponent({ title, onSubmit }: Props) {
  return <button onClick={onSubmit}>{title}</button>;
}
```

### Adding a New API Endpoint

1. Create method in `src/api/services.ts`
2. Add type in `src/types/`
3. Use with `useApi` hook in component

```typescript
// api/services.ts
export const api = {
  getExample: () => apiClient.get<T>('/endpoint'),
};

// Component.tsx
const { data, loading, execute } = useApi(api.getExample);
```

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Output goes to dist/ directory

# Test production build locally
npm run preview
```

Build output:
- Minified JS and CSS
- Asset hashing for cache busting
- Source maps for debugging

## Deployment

### Static Hosting (Vercel, Netlify)

```bash
# Build
npm run build

# Deploy dist/ folder
# Set environment variables in hosting platform
```

### Docker Deployment

```bash
# Build image
docker build -t visionscan-frontend ./frontend

# Run container
docker run -p 3000:80 \
  -e VITE_API_URL="https://api.yourdomain.com" \
  visionscan-frontend
```

### Environment Setup

For production:
```bash
VITE_API_URL=https://api.yourdomain.com
```

## Browser Compatibility

Supports:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### API Connection Error
```
Failed to fetch from http://localhost:8000
```

Solution:
- Verify backend is running
- Check VITE_API_URL in .env
- Ensure CORS is configured
- Check browser console for details

### TypeScript Errors
```
Type 'X' is not assignable to type 'Y'
```

Solution:
- Run `npm run type-check`
- Check type definitions in `src/types/`
- Verify API responses match types

### Build Fails
```
vite build failed
```

Solution:
- Check for TypeScript errors: `npm run type-check`
- Clear node_modules: `rm -rf node_modules && npm install`
- Check disk space
- Review error message in console

### Styling Issues
```
Tailwind classes not applied
```

Solution:
- Verify class names are exact (no typos)
- Check `tailwind.config.js` includes src files
- Rebuild: `npm run build`
- Clear browser cache (Ctrl+Shift+Delete)

## Development Tips

### Hot Module Replacement (HMR)
- Vite automatically reloads on file changes
- Component state is preserved during development
- Very fast refresh cycle

### React DevTools
- Install React DevTools browser extension
- Debug component state and props
- Profile component performance

### Network Debugging
- Open browser DevTools (F12)
- Go to Network tab
- Watch API calls in real-time
- Inspect request/response data

## Testing

When tests are added:

```bash
npm run test           # Run tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

## Code Quality

TypeScript provides:
- Type safety at build time
- Better IDE autocomplete
- Self-documenting code
- Fewer runtime errors

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

## Support

- App: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Code: `/Users/vrln/smolvlm/visionscan-pos/frontend/`

## License

MIT
