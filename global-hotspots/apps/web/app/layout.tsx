import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata = {
  title: "Global Hotspots",
  description: "Global hotspot radar MVP",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="text-lg font-semibold tracking-wide">Global Hotspots</div>
          <nav className="flex gap-6 text-sm text-slate-300">
            <Link href="/">地球热点</Link>
            <Link href="/ranking">热度榜单</Link>
            <Link href="/settings">配置中心</Link>
          </nav>
        </header>
        <main className="mx-auto max-w-7xl px-4 pb-10">{children}</main>
      </body>
    </html>
  );
}
