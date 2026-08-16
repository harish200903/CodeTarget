"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { fetchRecommendations, RecommendationItem, RecommendationListResponse } from "@/lib/api";
import {
  Target, Building2, Star, Code2, Gauge, Clock, LogOut, CheckCircle2,
  User as UserIcon, Sparkles, ArrowRight, Play, Bot, AlertCircle, BarChart3, FileCode2
} from "lucide-react";

export default function DashboardPage() {
  const { user, accessToken, loading, logout } = useAuth();
  const router = useRouter();

  const [recommendations, setRecommendations] = useState<RecommendationListResponse | null>(null);
  const [recLoading, setRecLoading] = useState(true);
  const [recError, setRecError] = useState<string | null>(null);

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

  // Load Personalized Recommendations
  useEffect(() => {
    async function loadRecs() {
      if (!accessToken || !user || !user.onboarding_completed) return;
      setRecLoading(true);
      setRecError(null);
      try {
        const data = await fetchRecommendations(accessToken, 5);
        setRecommendations(data);
      } catch (err) {
        setRecError(err instanceof Error ? err.message : "Failed to load recommendations");
      } finally {
        setRecLoading(false);
      }
    }

    loadRecs();
  }, [accessToken, user]);

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

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col justify-between p-6 md:p-12 max-w-6xl mx-auto space-y-10">
      {/* Top Navbar */}
      <header className="w-full flex flex-wrap items-center justify-between border-b border-slate-800 pb-6 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/20">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">CodeTarget Dashboard</h1>
            <p className="text-xs text-slate-400">Company-Specific Interview Preparation Engine</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/mock-tests"
            className="px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <FileCode2 className="w-4 h-4 text-indigo-400" /> Mock Tests
          </Link>

          <Link
            href="/company-preparation"
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <BarChart3 className="w-4 h-4 text-indigo-400" /> Prep Analytics
          </Link>

          <Link
            href="/problems"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors flex items-center gap-2 shadow"
          >
            <Code2 className="w-4 h-4" /> Practice Catalog
          </Link>

          <button
            onClick={logout}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <LogOut className="w-3.5 h-3.5 text-red-400" /> Log Out
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="space-y-8">
        {/* Welcome Hero Card */}
        <div className="glass-panel rounded-2xl p-8 border border-slate-800 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" /> Target Onboarding Complete
              </div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-white">
                Welcome back, {user.full_name || "Candidate"} 👋
              </h2>
              <p className="text-xs text-slate-400 max-w-xl leading-relaxed">
                Your personalized company preparation workspace. Practice problem patterns curated specifically for your target recruiters.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/mock-tests"
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-sm rounded-xl transition-all shadow-lg shadow-indigo-500/20 flex items-center gap-2"
              >
                <span>Take Mock Assessment</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>

        {/* Mock Tests Quick Action Card */}
        <section className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <FileCode2 className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-extrabold text-white">Mock Company Coding Tests</h3>
              </div>
              <p className="text-xs text-slate-400">
                Practice under timed assessment conditions simulating company coding rounds.
              </p>
            </div>

            <Link
              href="/mock-tests"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5"
            >
              <span>Explore Mock Catalog</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </section>

        {/* Recommended For You Section */}
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 text-white shadow-md shadow-indigo-500/20">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-lg font-extrabold text-white tracking-tight flex items-center gap-2">
                  <span>Recommended For You</span>
                </h3>
                <p className="text-xs text-slate-400">
                  {recommendations?.source === "ai"
                    ? "Prioritized using AI activity analysis & target company patterns"
                    : "Curated based on your target onboarding profile"}
                </p>
              </div>
            </div>

            {recommendations?.focus_topics && recommendations.focus_topics.length > 0 && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 font-semibold">Current Focus:</span>
                <div className="flex flex-wrap gap-1.5">
                  {recommendations.focus_topics.map((topic, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-0.5 rounded-full bg-indigo-950/60 text-indigo-300 border border-indigo-800/40 text-[11px] font-bold"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Recommendation Cards */}
          {recLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl animate-pulse space-y-4">
                  <div className="h-4 bg-slate-800 rounded w-2/3" />
                  <div className="h-3 bg-slate-800 rounded w-full" />
                  <div className="h-8 bg-slate-800 rounded" />
                </div>
              ))}
            </div>
          ) : recError ? (
            <div className="p-6 bg-rose-950/30 border border-rose-800/30 rounded-2xl text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{recError}</span>
            </div>
          ) : !recommendations || recommendations.items.length === 0 ? (
            <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-2xl text-slate-400 text-xs space-y-2">
              <Sparkles className="w-8 h-8 text-indigo-400 mx-auto opacity-50" />
              <p className="font-semibold text-slate-300">You've completed all recommended problems in your target pool!</p>
              <p className="text-[11px] text-slate-500">Explore more problems directly from the catalog.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendations.items.map((item: RecommendationItem) => (
                <div
                  key={item.problem.id}
                  className="glass-card rounded-2xl p-6 border border-slate-800 hover:border-indigo-500/50 transition-all flex flex-col justify-between space-y-4 group"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {item.problem.difficulty}
                      </span>
                      {item.problem.user_status === "ATTEMPTED" && (
                        <span className="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full font-semibold">
                          Attempted
                        </span>
                      )}
                    </div>

                    <h4 className="text-base font-bold text-white group-hover:text-indigo-400 transition-colors">
                      {item.problem.title}
                    </h4>

                    <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                      <span className="text-indigo-400 font-semibold block mb-0.5 text-[10px] uppercase tracking-wider">
                        {item.reason_type.replace("_", " ")}
                      </span>
                      {item.reason}
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {item.problem.topics.map((t) => (
                        <span key={t.id} className="text-[10px] bg-slate-800/80 text-slate-300 px-2 py-0.5 rounded">
                          {t.name}
                        </span>
                      ))}
                    </div>
                  </div>

                  <Link
                    href={`/solve/${item.problem.slug}`}
                    className="w-full py-2.5 bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 rounded-xl text-xs font-bold transition-all text-center flex items-center justify-center space-x-1.5"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Solve Problem</span>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Persisted Onboarding Overview Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-indigo-400" /> Target Companies
              </span>
              <span className="text-slate-200 font-bold">{user.target_companies?.length || 0}</span>
            </div>

            <div className="space-y-1.5 pt-1">
              {user.target_companies?.map((tc) => (
                <Link
                  key={tc.id}
                  href={`/company-preparation`}
                  className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 transition-colors"
                >
                  <span className="font-semibold text-slate-200">{tc.company.name}</span>
                  {tc.priority === 1 ? (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-bold flex items-center gap-1">
                      <Star className="w-2.5 h-2.5 fill-current" /> Primary
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500">Secondary</span>
                  )}
                </Link>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <Code2 className="w-4 h-4 text-emerald-400" /> Preferred Language
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-black text-white capitalize">{user.preferred_language}</h3>
              <p className="text-[11px] text-slate-400 mt-1">Configured for Monaco code editor & Judge0 runner</p>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <Gauge className="w-4 h-4 text-amber-400" /> Skill Level
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-black text-white capitalize">{user.skill_level.toLowerCase()}</h3>
              <p className="text-[11px] text-slate-400 mt-1">Calibrated problem difficulty spectrum</p>
            </div>
          </div>

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
        CodeTarget Platform &copy; {new Date().getFullYear()} — Company-Specific Preparation Platform
      </footer>
    </div>
  );
}
