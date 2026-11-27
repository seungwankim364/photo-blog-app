import type { NextRequest } from "next/server";

import { API_INTERNAL_URL } from "@/lib/api";

// Forwards a browser request under /api/<resource>/... to the API's /<resource>/...
// The browser only ever talks to this app, so the API can stay private in the cluster.
// Request and response bodies are streamed, so big uploads aren't held in memory.

const PASS_THROUGH = ["content-type", "content-length", "cache-control", "etag", "last-modified"];
const WITH_BODY = new Set(["POST", "PATCH", "PUT"]);

export type ProxyContext = { params: Promise<{ path?: string[] }> };

export function proxyTo(resource: string) {
  return async function forward(req: NextRequest, { params }: ProxyContext): Promise<Response> {
    const { path = [] } = await params;
    const url = new URL(
      `${API_INTERNAL_URL}/${resource}${path.map((p) => `/${encodeURIComponent(p)}`).join("")}`,
    );
    url.search = req.nextUrl.search;

    const init: RequestInit & { duplex?: "half" } = { method: req.method, cache: "no-store" };
    if (WITH_BODY.has(req.method)) {
      init.body = req.body;
      init.headers = { "content-type": req.headers.get("content-type") ?? "" };
      init.duplex = "half"; // required by Node's fetch to stream a request body
    }

    let res: Response;
    try {
      res = await fetch(url, init);
    } catch {
      return Response.json({ detail: "API unreachable" }, { status: 502 });
    }

    const headers = new Headers();
    for (const name of PASS_THROUGH) {
      const value = res.headers.get(name);
      if (value) headers.set(name, value);
    }
    return new Response(res.body, { status: res.status, headers });
  };
}
