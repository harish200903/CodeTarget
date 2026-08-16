"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  Target, Building2, Star, Code2, Gauge, Clock, LogOut, CheckCircle2,
  User as UserIcon, ShieldCheck, Sparkles
} from "lucide-react";

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  // Route Protection Guard
  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/login");
      } else if (!user.onboarding_completed) {
        router.push("/onboarding");
      }
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F17]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Authenticating session...</p>
        </div>
      </div>
    );
  }

  // Find primary target company
  const primaryTarget = user.target_companies?.find((tc) => tc.priority === 1);
  const secondaryTargets = user.target_companies?.filter((tc) => tc.priority > 1) || [];

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col justify-between p-6 md:p-12 max-w-6xl mx-auto space-y-10">
      {/* Top Navbar */}
      <header className="w-full flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/20">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">CodeTarget Dashboard</h1>
            <p className="text-xs text-slate-400">Phase 2 Authenticated Shell</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
            <UserIcon className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-semibold">{user.full_name || user.email}</span>
          </div>

          <button
            onClick={logout}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <LogOut className="w-3.5 h-3.5 text-red-400" /> Log Out
          </button>
        </div>
      </header>

      {/* Main Welcome Hero */}
      <main className="space-y-8">
        <div className="glass-panel rounded-2xl p-8 border border-slate-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" /> Onboarding Completed
              </div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-white">
                Welcome back, {user.full_name || "Candidate"} 👋
              </h2>
              <p className="text-xs text-slate-400">
                Your target company preparation environment is personalized and ready.
              </p>
            </div>

            {primaryTarget && (
              <div className="glass-card rounded-xl p-4 border border-indigo-500/30 bg-indigo-950/20 flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-indigo-500/20 text-indigo-400">
                  <Star className="w-5 h-5 fill-current" />
                </div>
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-indigo-400 font-bold">Primary Target</span>
                  <h3 className="text-lg font-bold text-white">{primaryTarget.company.name}</h3>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Persisted Onboarding Information Overview Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Target Companies */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-indigo-400" /> Target Companies
              </span>
              <span className="text-slate-200 font-bold">{user.target_companies?.length || 0}</span>
            </div>

            <div className="space-y-1.5 pt-1">
              {user.target_companies?.map((tc) => (
                <div
                  key={tc.id}
                  className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80"
                >
                  <span className="font-semibold text-slate-200">{tc.company.name}</span>
                  {tc.priority === 1 ? (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-bold flex items-center gap-1">
                      <Star className="w-2.5 h-2.5 fill-current" /> Primary
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500">Secondary</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Preferred Language */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <Code2 className="w-4 h-4 text-emerald-400" /> Preferred Language
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-black text-white capitalize">{user.preferred_language}</h3>
              <p className="text-[11px] text-slate-400 mt-1">Configured for starter code & runner environment</p>
            </div>
          </div>

          {/* Skill Level */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <Gauge className="w-4 h-4 text-amber-400" /> Skill Level
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-black text-white capitalize">{user.skill_level.toLowerCase()}</h3>
              <p className="text-[11px] text-slate-400 mt-1">Influences recommendation engine difficulty calibration</p>
            </div>
          </div>

          {/* Daily Goal */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-purple-400" /> Daily Target Goal
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-black text-white">{user.daily_goal_minutes} mins</h3>
              <p className="text-[11px] text-slate-400 mt-1">Daily practice commitment</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full text-center text-xs text-slate-500 border-t border-slate-800/80 pt-6">
        CodeTarget Platform &copy; {new Date().getFullYear()} — Phase 2 Authentication & Onboarding Verification Shell
      </footer>
    </div>
  );
}
