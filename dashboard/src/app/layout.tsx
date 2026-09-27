import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CDR Control Room — Chaos-Driven Refactoring",
  description:
    "Chaos + load pipeline that classifies failures, generates refactor pull requests and verifies resilience. Built with IBM Bob 2.0.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-zinc-950 text-zinc-100">
        <header className="sticky top-0 z-10 border-b border-white/10 bg-zinc-950/80 backdrop-blur">
          <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4">
            <Link href="/" className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-cyan-500 to-emerald-500 font-mono text-sm font-bold text-zinc-950">
                CD
              </span>
              <span>
                <span className="block text-sm font-semibold leading-4">CDR Control Room</span>
                <span className="block text-[11px] text-zinc-500">
                  Chaos-Driven Refactoring
                </span>
              </span>
            </Link>
            <div className="flex items-center gap-4 text-xs">
              <span className="hidden rounded-full border border-white/10 px-2.5 py-1 text-zinc-400 sm:inline">
                Built with IBM Bob 2.0
              </span>
              <a
                href="https://github.com/LuisRz1/chaos-driven-refactoring"
                className="text-zinc-400 transition hover:text-cyan-300"
              >
                GitHub
              </a>
            </div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-white/10 py-4">
          <p className="mx-auto w-full max-w-6xl px-4 text-[11px] text-zinc-600">
            CDR closes the APM-to-code gap: physical collapse → root cause → repository-aware
            refactor → verification under the same chaos scenario.
          </p>
        </footer>
      </body>
    </html>
  );
}
