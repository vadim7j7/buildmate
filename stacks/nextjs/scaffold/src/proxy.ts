// Next.js 16 renamed `middleware.ts` to `proxy.ts` (same API, runs before routing).
// next-intl still exports its handler from `next-intl/middleware`.
import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Match all paths except API, Next internals, and files with an extension.
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
