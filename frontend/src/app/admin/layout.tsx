"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  ShieldAlert, LayoutDashboard, Building2, Tag, FileCode2, Award,
  History, ArrowLeft, LogOut, Code2, Sparkles
} from "lucide-react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/login");
      } else if (user.role !== "ADMIN") {
        router.push("/dashboard");
      }
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F17]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Verifying administrator privileges...</p>
        </div>
      </div>
    );
  }

  if (user.role !== "ADMIN") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#0B0F17] p-6 text-center space-y-4">
        <ShieldAlert className="w-12 h-12 text-rose-500" />
        <h1 className="text-xl font-bold text-white">403 Forbidden — Administrator Access Required</h1>
        <p className="text-xs text-slate-400">Your account does not have content-management privileges.</p>
        <Link href="/dashboard" className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold">
          Return to Candidate Dashboard
        </Link>
      </div>
    );
  }

  const navItems = [
    { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
    { label: "Companies", href: "/admin/companies", icon: Building2 },
    { label: "DSA Topics", href: "/admin/topics", icon: Tag },
    { label: "Problems Catalog", href: "/admin/problems", icon: FileCode2 },
    { label: "Mock Tests", href: "/admin/mock-tests", icon: Award },
    { label: "Audit Logs", href: "/admin/audit-logs", icon: History },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col md:flex-row text-slate-200">
      {/* Admin Sidebar */}
      <aside className="w-full md:w-64 bg-slate-900/90 border-b md:border-b-0 md:border-r border-slate-800 p-6 flex flex-col justify-between shrink-0">
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-rose-600 text-white shadow-lg shadow-rose-600/20">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-white tracking-tight">CodeTarget Admin</h2>
              <span className="text-[10px] text-rose-400 font-bold block uppercase tracking-wider">CMS Console</span>
            </div>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/admin" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="pt-6 border-t border-slate-800 space-y-2">
          <Link
            href="/dashboard"
            className="w-full py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Candidate Portal</span>
          </Link>

          <button
            onClick={logout}
            className="w-full py-2.5 px-3 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/40 text-rose-300 text-xs font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Log Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 p-6 md:p-10 max-w-6xl overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
