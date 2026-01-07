# Unified Investment Tracker - Frontend

Modern React frontend for the Unified Investment Tracker application.

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Fast build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful component library
- **React Query (TanStack Query)** - Data fetching and caching
- **Recharts** - Chart library for visualizations
- **React Router** - Client-side routing
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── layout/       # Layout components
│   │   └── dashboard/    # Dashboard-specific components
│   ├── contexts/         # React contexts (auth, etc.)
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and API client
│   ├── pages/            # Page components
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## Features

- ✅ Dashboard with portfolio overview
- ✅ Holdings management
- ✅ Transaction tracking
- ✅ Mutual funds CAS import
- ✅ Asset management
- ✅ Responsive design
- ✅ Authentication
- ✅ Real-time data updates

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## Development

The frontend is configured to proxy API requests to the backend running on `http://localhost:8000`.

## License

Private project for personal use.

