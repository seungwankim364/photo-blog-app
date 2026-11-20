import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Seungwan's Photo Blog",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link href="/" className="site-title">
            Seungwan&apos;s Photo Blog
          </Link>
          <nav className="site-nav">
            <Link href="/">Photos</Link>
            <Link href="/upload">Upload</Link>
            <Link href="/status">Status</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
