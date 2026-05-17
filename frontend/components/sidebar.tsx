"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Shield, Cpu, Activity, GitBranch, Terminal } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Security Gate", href: "/security", icon: Shield },
    { name: "AI Analysis", href: "/ai-analysis", icon: Cpu },
    { name: "Monitoring", href: "/monitoring", icon: Activity },
  ];

  return (
    <aside className="w-64 bg-[#09090b] border-r border-[#27272a] flex flex-col h-screen fixed left-0 top-0 text-gray-200">
      {/* Sidebar Header / Branding */}
      <div className="p-6 border-b border-[#27272a] flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg tracking-wider text-white">
          <Terminal className="w-5 h-5 text-emerald-400" />
          <span>AUTOHEAL</span>
        </Link>
        {/* State Ping Light representing healthy agent state */}
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
      </div>

      {/* Navigation menu */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-zinc-800 text-white border border-[#3f3f46]"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-900 border border-transparent"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Sidebar Footer / Integrations status */}
      <div className="p-4 border-t border-[#27272a] space-y-3">
        <div className="flex items-center justify-between text-xs text-zinc-500 bg-zinc-950 p-3 rounded-lg border border-[#27272a]">
          <span className="flex items-center gap-1.5">
            <GitBranch className="w-3.5 h-3.5" />
            <span>CI Integration</span>
          </span>
          <span className="text-emerald-400 font-medium">Connected</span>
        </div>
        <div className="text-[10px] text-center text-zinc-600">
          AutoHeal Control Panel v0.1.0
        </div>
      </div>
    </aside>
  );
}
