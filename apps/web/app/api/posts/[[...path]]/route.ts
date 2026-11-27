import { proxyTo } from "@/lib/proxy";

// /api/posts/... -> API /posts/...
export const dynamic = "force-dynamic";

const forward = proxyTo("posts");
export { forward as GET, forward as POST, forward as PATCH, forward as DELETE };
