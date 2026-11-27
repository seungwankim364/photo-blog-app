import { proxyTo } from "@/lib/proxy";

// /api/photos/... -> API /photos/...
export const dynamic = "force-dynamic";

const forward = proxyTo("photos");
export { forward as GET, forward as POST, forward as DELETE };
