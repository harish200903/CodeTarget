"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  fetchMyGamification,
  fetchBadges,
  fetchXPHistory,
  UserGamificationResponse,
  BadgeItem,
  XPTransactionItem,
} from "@/lib/api";
import {
  Trophy, Flame, Target, Award, ArrowLeft, History, Zap, CheckCircle2, Lock, Star
} from "lucide-react";

export default function GamificationHubPage() {
  const { accessToken } = useAuth();
  const [profile, setProfile] = useState<UserGamificationResponse | null>(null);
  const [badges, setBadges] = useState<BadgeItem[]>([]);
  const [history, setHistory] = useState<XPTransactionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      if (!accessToken) return;
      try {
        setLoading(true);
        const [profData, badgeData, histData] = await Promise.all([
          fetchMyGamification(accessToken),
          fetchBadges(accessToken),
          fetchXPHistory(accessToken, 1, 15),
        ]);
        setProfile(profData);
        setBadges(badgeData);
        setHistory(histData.items);
      } catch (err) {
        console.error("Failed to load gamification hub:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [accessToken]);

  if (loading || !profile) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Gamification Hub...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-200 p-6 md:p-12 max-w-6xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white rounded-xl border border-slate-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Gamification & Practice Rewards</h1>
            <p className="text-xs text-slate-400">Earn XP, build streaks, level up, and unlock practice badges.</p>
          </div>
        </div>

        <Link
          href="/leaderboard"
          className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600 text-purple-300 hover:text-white border border-purple-500/30 font-semibold text-xs rounded-xl flex items-center gap-2 transition-all"
        >
          <Award className="w-4 h-4 text-purple-400" />
          <span>Weekly Leaderboard</span>
        </Link>
      </div>

      {/* Profile Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Level Card */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/60 border border-indigo-500/30 rounded-2xl p-6 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Candidate Level</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Trophy className="w-5 h-5" />
            </div>
          </div>
          <div>
            <p className="text-3xl font-black text-white tracking-tight">Level {profile.current_level}</p>
            <p className="text-xs text-slate-400 font-mono mt-1">{profile.total_xp} Total XP</p>
          </div>

          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>{profile.total_xp} XP</span>
              <span>{profile.xp_for_next_level} XP</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden border border-slate-700">
              <div
                className="bg-gradient-to-r from-amber-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${profile.level_progress_pct}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-400 font-mono block text-right">
              {profile.level_progress_pct}% to Level {profile.current_level + 1}
            </span>
          </div>
        </div>

        {/* Streak Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Practice Streak</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Flame className="w-5 h-5 animate-pulse" />
            </div>
          </div>
          <div>
            <p className="text-3xl font-black text-white tracking-tight">{profile.current_streak} Days 🔥</p>
            <p className="text-xs text-slate-400 mt-1">Longest Streak: {profile.longest_streak} Days</p>
          </div>
          <p className="text-xs text-slate-400">
            {profile.current_streak > 0
              ? "Keep practicing every calendar day to maintain your streak!"
              : "Solve a coding problem or complete a mock test today to start your streak!"}
          </p>
        </div>

        {/* Today's Goal Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Today's Daily Goal</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Target className="w-5 h-5" />
            </div>
          </div>
          <div>
            <p className="text-3xl font-black text-white tracking-tight">
              {profile.today_activity?.minutes_practiced || 0} / {profile.today_activity?.goal_minutes || 30} min
            </p>

            {profile.today_activity?.goal_completed ? (
              <span className="text-xs text-emerald-400 font-bold flex items-center gap-1 mt-1">
                <CheckCircle2 className="w-4 h-4" /> Goal Completed (+25 XP)
              </span>
            ) : (
              <p className="text-xs text-slate-400 mt-1">Practice to complete today's goal!</p>
            )}
          </div>

          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, ((profile.today_activity?.minutes_practiced || 0) / (profile.today_activity?.goal_minutes || 30)) * 100)}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Badges Grid */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Achievement Badges</h2>
            <p className="text-xs text-slate-400">Deterministic rewards unlocked through learning milestones.</p>
          </div>
          <span className="px-3 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-300 font-extrabold text-xs rounded-full">
            {profile.unlocked_badges_count} / {profile.total_badges} Unlocked
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {badges.map((b) => (
            <div
              key={b.id}
              className={`p-4 rounded-2xl border transition-all ${
                b.is_unlocked
                  ? "bg-slate-800/60 border-amber-500/30 text-slate-200 shadow-lg shadow-amber-500/5"
                  : "bg-slate-950/60 border-slate-800 text-slate-500 opacity-60"
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2.5 rounded-xl ${b.is_unlocked ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : "bg-slate-900 text-slate-600"}`}>
                  {b.is_unlocked ? <Award className="w-5 h-5" /> : <Lock className="w-5 h-5" />}
                </div>
                <span className={`text-[11px] font-bold font-mono px-2 py-0.5 rounded-full ${b.is_unlocked ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-slate-900 text-slate-600"}`}>
                  +{b.xp_reward} XP
                </span>
              </div>

              <h3 className={`text-xs font-bold ${b.is_unlocked ? "text-white" : "text-slate-400"}`}>{b.name}</h3>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{b.description}</p>

              {b.is_unlocked && b.awarded_at && (
                <span className="text-[10px] text-amber-400/80 font-mono mt-3 block">
                  Unlocked {new Date(b.awarded_at).toLocaleDateString()}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* XP Transaction History */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-bold text-white">Auditable XP Transaction History</h2>
        </div>

        <div className="divide-y divide-slate-800/80">
          {history.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No XP transactions recorded yet.</p>
          ) : (
            history.map((tx) => (
              <div key={tx.id} className="py-3 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <span className="px-2.5 py-1 rounded-lg font-bold font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20">
                    +{tx.amount} XP
                  </span>
                  <div>
                    <span className="font-semibold text-slate-200 uppercase tracking-wider text-[11px] block">{tx.reason}</span>
                    <span className="text-[10px] font-mono text-slate-500">{tx.reference_type}: {tx.reference_id.slice(0, 12)}</span>
                  </div>
                </div>

                <span className="text-[10px] font-mono text-slate-500">
                  {new Date(tx.created_at).toLocaleString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
