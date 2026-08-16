"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  fetchLeaderboard,
  fetchMyGamification,
  updateGamificationPreferences,
  LeaderboardResponse,
  UserGamificationResponse,
} from "@/lib/api";
import {
  Award, Trophy, ArrowLeft, Shield, CheckCircle2, AlertCircle, Eye, EyeOff, Crown
} from "lucide-react";

export default function LeaderboardPage() {
  const { accessToken } = useAuth();
  const [board, setBoard] = useState<LeaderboardResponse | null>(null);
  const [profile, setProfile] = useState<UserGamificationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [displayName, setDisplayName] = useState("");

  async function loadData() {
    if (!accessToken) return;
    try {
      setLoading(true);
      const [boardData, profData] = await Promise.all([
        fetchLeaderboard(accessToken, 50),
        fetchMyGamification(accessToken),
      ]);
      setBoard(boardData);
      setProfile(profData);
      setDisplayName(profData.display_name || "");
    } catch (err) {
      console.error("Failed to load leaderboard:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [accessToken]);

  async function handleToggleOptIn() {
    if (!accessToken || !profile) return;
    setToggling(true);
    try {
      const newOptIn = !profile.leaderboard_opt_in;
      await updateGamificationPreferences(accessToken, {
        leaderboard_opt_in: newOptIn,
        display_name: displayName,
      });
      await loadData();
    } catch (err) {
      console.error("Failed to update leaderboard preference:", err);
    } finally {
      setToggling(false);
    }
  }

  if (loading || !profile) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Leaderboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-200 p-6 md:p-12 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white rounded-xl border border-slate-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Weekly Candidate Leaderboard
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-purple-500/10 text-purple-300 border border-purple-500/20">
                {board?.period || "This Week"}
              </span>
            </h1>
            <p className="text-xs text-slate-400">Competitive ranking based on Weekly XP earned from coding practice.</p>
          </div>
        </div>

        <Link
          href="/gamification"
          className="px-4 py-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold text-xs rounded-xl flex items-center gap-2 transition-all"
        >
          <Trophy className="w-4 h-4 text-amber-400" />
          <span>My Badges & XP</span>
        </Link>
      </div>

      {/* Opt-In Preference Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-2xl ${profile.leaderboard_opt_in ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-slate-800 text-slate-400"}`}>
            {profile.leaderboard_opt_in ? <Eye className="w-6 h-6" /> : <EyeOff className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              {profile.leaderboard_opt_in ? "You are currently participating in the public leaderboard" : "Leaderboard Participation is Opt-In Only"}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {profile.leaderboard_opt_in
                ? `Displayed as "${profile.display_name}". You can hide your ranking anytime.`
                : "Opt in to compete with other candidate coders and compare weekly practice XP."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          {profile.leaderboard_opt_in && (
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Display Name"
              className="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
            />
          )}

          <button
            onClick={handleToggleOptIn}
            disabled={toggling}
            className={`px-4 py-2 rounded-xl text-xs font-semibold shrink-0 transition-all ${
              profile.leaderboard_opt_in
                ? "bg-slate-800 hover:bg-slate-700 text-slate-300"
                : "bg-purple-600 hover:bg-purple-500 text-white shadow-md shadow-purple-600/20"
            }`}
          >
            {toggling ? "Updating..." : profile.leaderboard_opt_in ? "Opt Out & Hide" : "Opt In to Leaderboard"}
          </button>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
            <tr>
              <th className="p-4 w-16 text-center">Rank</th>
              <th className="p-4">Candidate</th>
              <th className="p-4">Level</th>
              <th className="p-4 text-right">Weekly XP</th>
              <th className="p-4 text-right">Total XP</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {!board?.items || board.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-500">
                  No opted-in candidates on the leaderboard this week yet.
                </td>
              </tr>
            ) : (
              board.items.map((item) => (
                <tr
                  key={item.user_id}
                  className={`transition-colors ${
                    item.is_current_user
                      ? "bg-purple-950/40 border-l-4 border-l-purple-500 text-white font-semibold"
                      : "hover:bg-slate-800/30"
                  }`}
                >
                  <td className="p-4 text-center font-black">
                    {item.rank === 1 ? (
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        <Crown className="w-4 h-4 fill-amber-400 text-amber-400" />
                      </span>
                    ) : item.rank === 2 ? (
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-300/20 text-slate-200 border border-slate-300/30">
                        #2
                      </span>
                    ) : item.rank === 3 ? (
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-700/20 text-amber-400 border border-amber-700/30">
                        #3
                      </span>
                    ) : (
                      <span className="text-slate-400 font-mono">#{item.rank}</span>
                    )}
                  </td>

                  <td className="p-4 font-bold text-white flex items-center gap-2">
                    <span>{item.display_name}</span>
                    {item.is_current_user && (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        YOU
                      </span>
                    )}
                  </td>

                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-slate-800 text-slate-300">
                      Level {item.level}
                    </span>
                  </td>

                  <td className="p-4 text-right font-mono font-bold text-emerald-400 text-sm">
                    +{item.weekly_xp} XP
                  </td>

                  <td className="p-4 text-right font-mono text-slate-400">
                    {item.total_xp} XP
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
