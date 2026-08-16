"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  fetchRecommendations,
  fetchMyGamification,
  RecommendationItem,
  RecommendationListResponse,
  UserGamificationResponse,
} from "@/lib/api";
import {
  Target, Building2, Star, Code2, Gauge, Clock, LogOut, CheckCircle2,
  User as UserIcon, Sparkles, ArrowRight, Play, Bot, AlertCircle, BarChart3,
  FileCode2, Flame, Award, Trophy, Zap, ShieldAlert
} from "lucide-react";

export default function DashboardPage() {
  const { user, accessToken, loading, logout } = useAuth();
  const router = useRouter();

  const [recommendations, setRecommendations] = useState<RecommendationListResponse | null>(null);
  const [gamification, setGamification] = useState<UserGamificationResponse | null>(null);
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

  // Load Personalized Recommendations & Gamification
  useEffect(() => {
    async function loadData() {
      if (!accessToken || !user || !user.onboarding_completed) return;
      setRecLoading(true);
      setRecError(null);
      try {
        const [recData, gamiData] = await Promise.all([
          fetchRecommendations(accessToken, 5),
          fetchMyGamification(accessToken).catch(() => null),
        ]);
        setRecommendations(recData);
        setGamification(gamiData);
      } catch (err) {
        setRecError(err instanceof Error ? err.message : "Failed to load recommendations");
      } finally {
        setRecLoading(false);
      }
    }

    loadData();
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

        <div className="flex items-center gap-3 flex-wrap">
          {user.role === "ADMIN" && (
            <Link
              href="/admin"
              className="px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition-colors flex items-center gap-2 shadow"
            >
              <ShieldAlert className="w-4 h-4" /> Admin Console
            </Link>
          )}

          <Link
            href="/gamification"
            className="px-4 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <Trophy className="w-4 h-4 text-amber-400" /> Badges & XP
          </Link>

          <Link
            href="/leaderboard"
            className="px-4 py-2 rounded-xl bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <Award className="w-4 h-4 text-purple-400" /> Leaderboard
          </Link>

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
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </header>

      {/* Gamification Summary Widget */}
      {gamification && (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl">
          <div className="flex items-center gap-4">
            <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Trophy className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-extrabold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Level {gamification.current_level}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {gamification.total_xp} Total XP
                </span>
              </div>
              <div className="w-48 bg-slate-800 rounded-full h-2 mt-2 overflow-hidden border border-slate-700">
                <div
                  className="bg-gradient-to-r from-amber-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${gamification.level_progress_pct}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                {gamification.level_progress_pct}% to Level {gamification.current_level + 1}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-6 divide-x divide-slate-800 text-xs">
            <div className="flex items-center gap-2.5 pl-4">
              <Flame className="w-5 h-5 text-amber-400 animate-pulse" />
              <div>
                <span className="text-slate-400 font-medium block text-[11px]">Current Streak</span>
                <span className="text-white font-black text-sm">{gamification.current_streak} Days 🔥</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 pl-6">
              <Target className="w-5 h-5 text-indigo-400" />
              <div>
                <span className="text-slate-400 font-medium block text-[11px]">Today's Practice</span>
                <span className="text-white font-black text-sm">
                  {gamification.today_activity?.minutes_practiced || 0} / {gamification.today_activity?.goal_minutes || 30} min
                  {gamification.today_activity?.goal_completed && " ✓"}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 pl-6">
              <Award className="w-5 h-5 text-purple-400" />
              <div>
                <span className="text-slate-400 font-medium block text-[11px]">Unlocked Badges</span>
                <span className="text-white font-black text-sm">
                  {gamification.unlocked_badges_count} / {gamification.total_badges} 🏆
                </span>
              </div>
            </div>
          </div>

          <Link
            href="/gamification"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20"
          >
            <span>Gamification Hub</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <UserIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Target Profile</h2>
              <p className="text-xs text-slate-400">{user.email}</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex justify-between items-center py-1.5 border-b border-slate-800">
              <span className="text-slate-400 flex items-center gap-1.5"><Gauge className="w-3.5 h-3.5 text-slate-500" /> Skill Level</span>
              <span className="font-semibold text-slate-200 uppercase bg-slate-800 px-2 py-0.5 rounded text-[10px]">{user.skill_level}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-slate-800">
              <span className="text-slate-400 flex items-center gap-1.5"><Code2 className="w-3.5 h-3.5 text-slate-500" /> Language</span>
              <span className="font-semibold text-indigo-400 uppercase bg-indigo-950/40 border border-indigo-800/40 px-2 py-0.5 rounded text-[10px]">{user.preferred_language}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-slate-800">
              <span className="text-slate-400 flex items-center gap-1.5"><Clock className="w-3.5 h-3.5 text-slate-500" /> Daily Goal</span>
              <span className="font-semibold text-slate-200">{user.daily_goal_minutes} mins/day</span>
            </div>
          </div>
        </div>

        {/* Target Companies */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 md:col-span-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Target Companies</h2>
                <p className="text-xs text-slate-400">Targeting company interview standards</p>
              </div>
            </div>
            <Link href="/onboarding" className="text-xs text-indigo-400 hover:underline">Edit Selection</Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {user.target_companies.map((tc) => (
              <div key={tc.id} className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <Star className={`w-4 h-4 ${tc.priority === 1 ? "text-amber-400 fill-amber-400" : "text-slate-500"}`} />
                  <div>
                    <span className="font-bold text-white block">{tc.company.name}</span>
                    <span className="text-[10px] text-slate-400">{tc.company.tier} Tier</span>
                  </div>
                </div>
                <Link
                  href={`/company-preparation?company=${tc.company.id}`}
                  className="px-2.5 py-1 rounded bg-indigo-950/60 border border-indigo-800/40 text-indigo-300 text-[10px] font-semibold hover:bg-indigo-900/60"
                >
                  Prep Profile →
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mock Tests Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <FileCode2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Mock Company Coding Tests</h2>
              <p className="text-xs text-slate-400">Simulate company timed online assessment coding rounds</p>
            </div>
          </div>
          <Link href="/mock-tests" className="text-xs text-indigo-400 hover:underline font-semibold">
            View All Mock Tests →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {user.target_companies.slice(0, 3).map((tc) => (
            <div key={tc.id} className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-2 text-xs">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-300 border border-amber-500/20">
                {tc.company.name}
              </span>
              <h3 className="font-bold text-white text-xs">{tc.company.name}-Style Mock Test</h3>
              <p className="text-[11px] text-slate-400">Timed 60-min assessment based on your selected target profile.</p>
              <Link
                href="/mock-tests"
                className="inline-block pt-1 text-[11px] font-semibold text-indigo-400 hover:underline"
              >
                Start Assessment →
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Practice Problems Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                Personalized Practice Recommendations
                {recommendations?.source === "AI_POWERED" && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    Gemini AI
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400">Targeted DSA problems based on your target companies and activity</p>
            </div>
          </div>

          <Link href="/problems" className="text-xs font-semibold text-indigo-400 hover:underline flex items-center gap-1">
            Browse Catalog <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {recLoading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-slate-800/50 animate-pulse rounded-xl" />
            ))}
          </div>
        ) : recError ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{recError}</span>
          </div>
        ) : recommendations?.items.length === 0 ? (
          <p className="text-xs text-slate-400 py-4 text-center">No problem recommendations available.</p>
        ) : (
          <div className="space-y-3">
            {recommendations?.items.map((item: RecommendationItem) => (
              <div
                key={item.problem.id}
                className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-slate-600 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-white text-xs">{item.problem.title}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                        item.problem.difficulty === "EASY"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : item.problem.difficulty === "MEDIUM"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {item.problem.difficulty}
                    </span>
                    {item.problem.user_status === "SOLVED" && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Solved
                      </span>
                    )}
                  </div>

                  <p className="text-[11px] text-slate-400">{item.reason}</p>
                </div>

                <Link
                  href={`/solve/${item.problem.slug}`}
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 self-start sm:self-center shadow"
                >
                  <Play className="w-3 h-3 fill-white" /> Solve Now
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      <footer className="text-center text-xs text-slate-500 pt-4 border-t border-slate-800/60">
        CodeTarget Phase 7 — Gamification, Streaks & Engagement Production Ready
      </footer>
    </div>
  );
}
