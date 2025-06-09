import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Pages that don't require authentication
const publicPaths = ['/', '/login', '/register'];

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Check if the path is public
  const isPublicPath = publicPaths.includes(pathname);
  
  // Get the token from cookies (if you store it there) or check another way
  // For now, we'll skip the check since tokens are in localStorage
  
  // You could implement server-side auth check here if needed
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};