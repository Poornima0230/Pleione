import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";

export const metadata: Metadata = {
  title: "Pleione — Reliability Intelligence",
  description: "AI-driven anomaly detection and burn-in screening platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased transition-colors duration-200 dark:bg-slate-950 dark:text-slate-100">
        <Sidebar />
        <TopBar />

        <main className="ml-[248px] min-h-screen pt-[80px]">
          <div className="px-6 pb-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
