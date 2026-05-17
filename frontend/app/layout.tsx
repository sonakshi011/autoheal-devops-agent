import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Sidebar from "@/components/sidebar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AutoHeal Control Panel",
  description: "AI-Powered Self-Healing DevOps Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#09090b] text-gray-200 antialiased`}>
        <div className="flex min-h-screen">
          {/* Persistent Sidebar */}
          <Sidebar />

          {/* Scrollable Main Content Frame */}
          <main className="flex-1 pl-64 min-h-screen flex flex-col">
            <div className="p-8 max-w-7xl w-full mx-auto flex-1 flex flex-col">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
