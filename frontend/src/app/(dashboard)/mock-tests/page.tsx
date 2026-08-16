"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  fetchMockTestCatalog,
  startMockTestSession,
  fetchMockTestHistory,
  MockTestCatalogItem,
  MockTestHistoryItem,
} from "@/lib/api";
import {
  Clock, Award, Play, CheckCircle2, AlertCircle, ArrowRight, Building2,
  FileCode2, ShieldAlert, RotateCcw, History, Sparkles, BarChart2
} from "lucide-react";

export default function MockTestCatalogPage() {
  const { user, accessToken, loading } = useAuth();
  const router = useRouter();

  const [catalog, setCatalog] = useState<MockTestCatalogItem[]>([]);
  const [history, setHistory] = useState<MockTestHistoryItem[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [startingId, setStartingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/login");
      } else if (!user.onboarding_completed) {
        router.push("/onboarding");
      }
    }
  }, [user, loading, router]);

  useEffect(() => {
    async function loadData() {
      if (!accessToken || !user || !user.onboarding_completed) return;
      setCatalogLoading(true);
      setError(null);
      try {
        const [catData, histData] = await Promise.all([
          fetchMockTestCatalog(accessToken),
          fetchMockTestHistory(accessToken),
        ]);
        setCatalog(catData);
        setHistory(histData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load mock tests");
      } finally {
        setCatalogLoading(false);
      }
    }

    loadData();
  }, [accessToken, user]);

  const handleStartMock = async (mockTestId: string) => {
    if (!accessToken) return;
    setStartingId(mockTestId);
    try {
      const session = await startMockTestSession(accessToken, mockTestId);
      router.push(`/mock-tests/${session.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start mock test session");
      setStartingId(null);
    }
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F17]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading mock tests catalog...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col justify-between p-6 md:p-12 max-w-6xl mx-auto space-y-10">
      {/* Top Navbar */}
      <header className="w-full flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/20">
            <FileCode2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Mock Company Coding Tests</h1>
            <p className="text-xs text-slate-400">Timed Assessment Simulations & Practice Rounds</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/company-preparation"
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <BarChart2 className="w-4 h-4 text-indigo-400" /> Prep Intelligence
          </Link>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors"
          >
            Dashboard
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="space-y-10">
        {/* Banner Notice */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              <ShieldAlert className="w-3.5 h-3.5" /> Company-Oriented Practice Simulation
            </div>
            <h2 className="text-lg font-bold text-white">Simulate Target Company Coding Assessment Rounds</h2>
            <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
              CodeTarget Mock Assessments simulate timed coding test environments matching your selected target companies. AI assistance is disabled during active tests to assess your independent problem-solving readiness.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-rose-950/30 border border-rose-800/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Mock Catalog Grid */}
        <section className="space-y-5">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Building2 className="w-5 h-5 text-indigo-400" /> Available Company Mocks
          </h3>

          {catalogLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl animate-pulse space-y-4">
                  <div className="h-4 bg-slate-800 rounded w-2/3" />
                  <div className="h-3 bg-slate-800 rounded w-full" />
                  <div className="h-8 bg-slate-800 rounded" />
                </div>
              ))}
            </div>
          ) : catalog.length === 0 ? (
            <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-2xl text-slate-400 text-xs space-y-2">
              <FileCode2 className="w-8 h-8 text-indigo-400 mx-auto opacity-50" />
              <p className="font-semibold text-slate-300">No mock tests found for your target companies.</p>
              <p className="text-[11px] text-slate-500">Update your target company selection in your profile or onboarding.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {catalog.map((m) => {
                const isStarting = startingId === m.id;
                const isInProgress = m.user_last_status === "IN_PROGRESS";
                const isCompleted = m.user_last_status === "SUBMITTED" || m.user_last_status === "AUTO_SUBMITTED";

                return (
                  <div
                    key={m.id}
                    className="glass-card rounded-2xl p-6 border border-slate-800 hover:border-indigo-500/50 transition-all flex flex-col justify-between space-y-5 group"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 uppercase tracking-wider">
                          {m.company_name}
                        </span>

                        {isInProgress ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            In Progress
                          </span>
                        ) : isCompleted ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Score: {m.user_last_score}/{m.total_points}
                          </span>
                        ) : null}
                      </div>

                      <h4 className="text-base font-extrabold text-white group-hover:text-indigo-400 transition-colors">
                        {m.title}
                      </h4>

                      <p className="text-xs text-slate-400 leading-relaxed">
                        {m.description || `Assessment round matching ${m.company_name} problem patterns.`}
                      </p>

                      <div className="flex items-center gap-4 text-xs text-slate-300 font-semibold pt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-indigo-400" /> {m.duration_minutes} mins
                        </span>
                        <span className="flex items-center gap-1">
                          <FileCode2 className="w-3.5 h-3.5 text-emerald-400" /> {m.problem_count} Problems
                        </span>
                        <span className="flex items-center gap-1">
                          <Award className="w-3.5 h-3.5 text-amber-400" /> {m.total_points} pts
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleStartMock(m.id)}
                      disabled={isStarting}
                      className={`w-full py-3 rounded-xl font-bold text-xs transition-all flex items-center justify-center space-x-2 ${
                        isInProgress
                          ? "bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-600/20"
                          : isCompleted
                          ? "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                          : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20"
                      }`}
                    >
                      {isStarting ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5 fill-current" />
                          <span>
                            {isInProgress ? "Continue Assessment" : isCompleted ? "Retake Assessment" : "Start Assessment"}
                          </span>
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* History Section */}
        {history.length > 0 && (
          <section className="space-y-4 pt-4 border-t border-slate-800/80">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <History className="w-5 h-5 text-indigo-400" /> Completed Assessment History
            </h3>

            <div className="space-y-2">
              {history.map((h) => (
                <div
                  key={h.session_id}
                  className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-white">{h.title}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                        {h.company_name}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      Completed: {h.completed_at ? new Date(h.completed_at).toLocaleDateString() : "Submitted"}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-sm font-black text-white">{h.score} / {h.total_points}</span>
                      <span className="text-[11px] text-indigo-400 font-bold block">{h.percentage}%</span>
                    </div>
                    <Link
                      href={`/mock-tests/${h.session_id}/result`}
                      className="px-3.5 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold transition-all"
                    >
                      View Result
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full text-center text-xs text-slate-500 border-t border-slate-800/80 pt-6">
        CodeTarget Platform &copy; {new Date().getFullYear()} — Timed Mock Coding Assessments
      </footer>
    </div>
  );
}
