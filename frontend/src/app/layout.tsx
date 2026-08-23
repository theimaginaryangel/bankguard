import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "BankGuard",
  description: "Unified security findings layer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="flex flex-col md:flex-row h-screen overflow-hidden bg-[#0a0a0a] text-zinc-100 font-sans selection:bg-zinc-800 selection:text-white">
        
        {/* Navigation */}
        <nav className="w-full md:w-64 border-b md:border-b-0 md:border-r border-zinc-800 bg-[#0a0a0a] flex flex-col shrink-0">
          <div className="p-4 md:p-8 md:pb-4 flex justify-between items-center md:block">
            <h1 className="font-mono text-lg md:text-xl tracking-widest uppercase text-white">
              BankGuard<span className="text-emerald-500">.</span>
            </h1>
            <div className="w-12 h-[1px] bg-zinc-700 rounded-full mt-4 hidden md:block"></div>
          </div>
          
          {/* Scrollable on mobile, stacked on desktop */}
          <div className="flex flex-row md:flex-col overflow-x-auto px-4 pb-2 md:pb-0 md:py-4 space-x-1 md:space-x-0 md:space-y-1 md:flex-grow no-scrollbar">
            <Link href="/" className="px-3 md:px-4 py-2 md:py-3 text-xs md:text-sm font-medium tracking-wide whitespace-nowrap text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-md transition-colors">
              OVERVIEW
            </Link>
            <Link href="/compliance" className="px-3 md:px-4 py-2 md:py-3 text-xs md:text-sm font-medium tracking-wide whitespace-nowrap text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-md transition-colors">
              COMPLIANCE
            </Link>
            <Link href="/fraud" className="px-3 md:px-4 py-2 md:py-3 text-xs md:text-sm font-medium tracking-wide whitespace-nowrap text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-md transition-colors">
              FRAUD
            </Link>
            <Link href="/architecture" className="px-3 md:px-4 py-2 md:py-3 text-xs md:text-sm font-medium tracking-wide whitespace-nowrap text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-md transition-colors">
              ARCHITECTURE
            </Link>
          </div>
          
          <div className="hidden md:block p-8 text-[10px] font-mono tracking-widest text-zinc-600 uppercase">
            System V1.0
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-12">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
        
      </body>
    </html>
  );
}
