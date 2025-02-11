import { getToken } from 'next-auth/jwt'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const token = await getToken({ req: request })
  const isAuthPage = request.nextUrl.pathname.startsWith('/auth')

  if (isAuthPage) {
    if (token) {
      // Redirect to home if user is already logged in
      return NextResponse.redirect(new URL('/', request.url))
    }
    // Allow access to auth pages if not logged in
    return NextResponse.next()
  }

  // Protect all other routes
  if (!token) {
    const signInUrl = new URL('/auth/signin', request.url)
    return NextResponse.redirect(signInUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api routes
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}
