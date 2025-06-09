# Lapis Spider Frontend

A Next.js web application for managing and viewing crawled content from the Lapis Spider system.

## Features

- **Authentication**: Secure login and registration
- **Website Management**: Add and manage websites to crawl
- **LLMs.txt Viewer**: View generated documentation in llms.txt format
- **Page Navigation**: Browse through crawled pages with sidebar navigation
- **Settings**: Configure API endpoints and view environment variables
- **System Status**: Real-time health monitoring of backend services

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_APP_NAME=Lapis Spider
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

   The app will be available at http://localhost:3000

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout with navbar
│   ├── page.tsx           # Home page
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   ├── websites/          # Website management
│   │   ├── page.tsx       # List websites
│   │   ├── new/           # Add new website
│   │   └── [id]/llms/     # View llms.txt content
│   └── settings/          # Settings page
├── components/            # Reusable components
│   └── Navbar.tsx        # Navigation bar
├── lib/                   # Utilities
│   └── api.ts            # API client
└── types/                 # TypeScript types
    └── index.ts          # Type definitions
```

## Usage

### 1. Authentication

- Register a new account or login with existing credentials
- JWT tokens are stored in localStorage
- Authenticated routes are protected

### 2. Managing Websites

- Click "Add Website" to add a new site to crawl
- Configure crawl settings (max pages, depth, robots.txt)
- Start crawls from the websites list
- View crawl status and statistics

### 3. Viewing LLMs.txt

- Click "View LLMs.txt" on any crawled website
- Browse pages in the sidebar
- View complete site documentation or individual pages
- Copy content to clipboard

### 4. Settings

- Configure API URL (requires restart to take effect)
- View current environment variables
- Check API documentation links

## API Integration

The frontend connects to the Lapis Spider backend API. Ensure the backend is running before using the frontend.

Required backend services:
- FastAPI application (port 8000)
- PostgreSQL database
- MongoDB
- Redis
- Celery workers

## Building for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

For deployment, you can use:
- Vercel (recommended for Next.js)
- Docker container
- Any Node.js hosting platform

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_APP_NAME`: Application name (default: Lapis Spider)

## Troubleshooting

### API Connection Issues
- Verify the backend is running
- Check the API URL in settings
- Ensure CORS is configured on the backend

### Authentication Errors
- Clear localStorage and login again
- Check JWT token expiration
- Verify backend auth endpoints

### Content Not Loading
- Ensure websites have been crawled
- Check if AI processing is enabled
- Verify page processing status

## Development

```bash
# Run development server
npm run dev

# Run type checking
npm run type-check

# Run linting
npm run lint

# Format code
npm run format
```

## License

MIT