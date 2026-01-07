# Frontend Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` if your backend is running on a different port.

3. **Start Development Server**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

## First Time Setup

### Prerequisites
- Node.js 18 or higher
- npm, yarn, or pnpm

### Installation Steps

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install all dependencies:
   ```bash
   npm install
   ```

3. Make sure your backend is running on `http://localhost:8000`

4. Start the frontend:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to `http://localhost:3000`

6. Login with any username and password (authentication is simplified for now)

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Troubleshooting

### Port Already in Use
If port 3000 is already in use, Vite will automatically try the next available port.

### API Connection Issues
- Make sure the backend is running on `http://localhost:8000`
- Check the `VITE_API_URL` in your `.env` file
- Check browser console for CORS errors

### Build Errors
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## Features

- ✅ Responsive design (mobile-friendly)
- ✅ Dark mode support (via TailwindCSS)
- ✅ Real-time data updates
- ✅ Beautiful UI with shadcn/ui components
- ✅ Interactive charts and visualizations

