import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
    const token = request.cookies.get('auth-token')?.value
    const { pathname } = request.nextUrl

    // المسارات العامة التي لا تتطلب تسجيل الدخول
    const publicPaths = ['/login', '/register', '/forget-password']

    // استثناء الملفات الثابتة والصور ومسارات API الداخلية لـ Next.js
    if (
        pathname.startsWith('/_next') ||
        pathname.includes('.') ||
        pathname.startsWith('/api/') || // استثناء مسارات API (إذا كان لدينا API routes في Next.js)
        pathname === '/favicon.ico'
    ) {
        return NextResponse.next()
    }

    // إذا كان المستخدم غير مسجل دخول ويحاول الوصول لصفحة محمية
    if (!token && !publicPaths.includes(pathname)) {
        const url = request.nextUrl.clone()
        url.pathname = '/login'
        return NextResponse.redirect(url)
    }

    // إذا كان المستخدم مسجل دخول ويحاول الوصول لصفحة الدخول
    if (token && publicPaths.includes(pathname)) {
        const url = request.nextUrl.clone()
        url.pathname = '/'
        return NextResponse.redirect(url)
    }

    return NextResponse.next()
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
}
