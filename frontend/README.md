# Flagship 107 Frontend

React + Vite frontend for video intelligence and behavioral anomaly detection.

## Development

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

### Build for Production

```bash
npm run build
```

### Lint Code

```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   ├── services/        # API and WebSocket services
│   ├── utils/           # Utility functions
│   ├── App.jsx          # Main application component
│   ├── App.css          # Application styles
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
└── package.json         # Dependencies
```

## Environment Variables

Create `.env.local` for local configuration:

```
VITE_API_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## Technology Stack

- **React 18** - UI library
- **Vite 5** - Build tool and dev server
- **Axios** - HTTP client
- **Native WebSocket** - Real-time communication

## Backend Connection

The frontend expects the backend API to be running on `http://localhost:8000` by default. This can be configured via the `VITE_API_URL` environment variable.

API calls are proxied through Vite's dev server to avoid CORS issues during development.
