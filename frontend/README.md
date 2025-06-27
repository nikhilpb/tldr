# TLDR Frontend

A clean and minimalist news aggregator web app built with React and TypeScript.

## Features

- **Articles Page**: View recent articles sorted by time (latest first)
  - Click on any article to view full content in a modal
  - Refresh button to reload articles
  - Clean, card-based layout

- **Sources Page**: Manage RSS feeds and website sources
  - Click on any source to edit its details
  - Add new sources with the "Add Source" button
  - Delete sources (with confirmation)
  - View source statistics (last fetched, error count, status)

## Development

### Prerequisites

- Node.js 18+ 
- Backend API running on port 8000

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:5173

### API Integration

The frontend is configured to proxy API requests to the backend:
- All `/api/*` requests are forwarded to `http://localhost:8000`
- Make sure the backend is running before using the frontend

### Building for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Architecture

- **React 18** with TypeScript
- **React Router** for navigation
- **Vite** for build tooling
- Clean, minimal CSS (no frameworks)
- Responsive design with mobile support

## API Endpoints Used

- `GET /api/v1/articles` - Fetch articles
- `GET /api/v1/articles/{id}` - Get article details
- `GET /api/v1/sources` - Fetch sources
- `POST /api/v1/sources` - Create source
- `PUT /api/v1/sources/{id}` - Update source
- `DELETE /api/v1/sources/{id}` - Delete source 