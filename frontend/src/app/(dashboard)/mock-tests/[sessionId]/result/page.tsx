"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { fetchMockTestResult, MockTestResultResponse } from "@/lib/api";
import {
  Award, CheckCircle2, AlertCircle, ArrowRight, RotateCcw, Sparkles,
  BarChart3, FileCode2, Clock, Check, X, ChevronRight, Target
} from "lucide-react";

export default function MockTestResultPage() {
  const params = useParams();
  const router = useRouter();
  const { user, accessToken, loading } = useAuth();
  const sessionId = params.sessionId as string;

  const [result, setResult] = useState<MockTestResultResponse | null>(null);
  const [resultLoading, setResultLoading] = useState(true);
  const [resultError, setResultError] = useState<string | null>(null);

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
    async function loadResult() {
      if (!accessToken || !sessionId) return;
      setResultLoading(true);
      setResultError(null);
      try {
        const data = await fetchMockTestResult(accessToken, sessionId);
        setResult(data);
      } catch (err) {
        setResultError(err instanceof Error ? err.message : "Failed to load result");
      } finally {
        setResultLoading(false);
      }
    }

    loadResult();
  }, [accessToken, sessionId]);

  if (loading || resultLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F17]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading assessment results...</p>
        </div>
      </div>
    );
  }

  if (resultError || !result) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#0B0F17] p-6 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400" />
        <p className="text-sm font-semibold text-slate-200">{resultError || "Result not found"}</p>
        <Link href="/mock-tests" className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold">
          Return to Mock Tests Catalog
        </Link>
      </div>
    );
  }

  const minsTaken = Math.floor(result.time_taken_seconds / 60);

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col justify-between p-6 md:p-12 max-w-5xl mx-auto space-y-10">
      {/* Top Navbar */}
      <header className="w-full flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/20">
            <Award className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">{result.title} — Result</h1>
            <p className="text-xs text-slate-400">{result.company_name} Assessment Simulation Summary</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/mock-tests"
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-semibold text-xs transition-colors"
          >
            Take Another Mock
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
      <main className="space-y-8">
        {/* Score & Hero Summary Card */}
        <div className="glass-panel rounded-2xl p-8 border border-slate-800 space-y-6 text-center">
          <div className="max-w-md mx-auto space-y-3">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              {result.status.replace("_", " ")}
            </span>

            <div className="py-2">
              <span className="text-5xl font-black text-white">{result.score}</span>
              <span className="text-xl font-bold text-slate-400"> / {result.total_points}</span>
              <span className="text-2xl font-black text-indigo-400 block mt-1">({result.percentage}%)</span>
            </div>

            <div className="flex items-center justify-center gap-4 text-xs text-slate-400 font-semibold pt-1">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-indigo-400" /> Time Used: {minsTaken} mins
              </span>
            </div>
          </div>

          {result.ai_explanation && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 to-violet-950/40 border border-indigo-500/30 text-xs text-slate-200 leading-relaxed font-sans text-left space-y-1">
              <span className="text-indigo-400 font-bold flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Post-Assessment AI Synthesis
              </span>
              <p>{result.ai_explanation}</p>
            </div>
          )}
        </div>

        {/* Per-Problem Performance Breakdown */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileCode2 className="w-5 h-5 text-indigo-400" /> Problem Performance Breakdown
          </h3>

          <div className="space-y-3">
            {result.problems.map((p) => {
              const isPassed = p.status === "ACCEPTED" || p.score_obtained === p.weight_score;
              return (
                <div
                  key={p.problem_id}
                  className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-white">{p.order_index}. {p.title}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                        {p.difficulty}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      Passed {p.passed_test_cases} / {p.total_test_cases} test cases
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                      isPassed
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    }`}>
                      {p.score_obtained} / {p.weight_score} pts
                    </span>

                    <Link
                      href={`/solve/${p.slug}`}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                    >
                      <span>Review Problem</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Topic & Difficulty Performance */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <BarChart3 className="w-4 h-4 text-indigo-400" /> Topic Performance
            </h4>
            <div className="space-y-2">
              {result.topic_breakdown.map((tb) => (
                <div key={tb.topic_id} className="flex items-center justify-between text-xs p-2.5 bg-slate-900/60 rounded-lg">
                  <span className="font-semibold text-slate-200">{tb.topic_name}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    tb.status === "STRONG"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}>
                    {tb.status.replace("_", " ")} ({tb.solved_count}/{tb.problems_count})
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Target className="w-4 h-4 text-emerald-400" /> Difficulty Exposure
            </h4>
            <div className="space-y-2">
              {result.difficulty_breakdown.map((db) => (
                <div key={db.difficulty} className="flex items-center justify-between text-xs p-2.5 bg-slate-900/60 rounded-lg">
                  <span className="font-semibold text-slate-200">{db.difficulty}</span>
                  <span className="text-slate-300 font-bold">{db.solved_count} / {db.problems_count} Solved</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Post-Test Recommended Next Steps */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ArrowRight className="w-5 h-5 text-indigo-400" /> Recommended Next Preparation Steps
          </h3>
          <div className="space-y-2">
            {result.recommended_next_steps.map((step, i) => (
              <div key={i} className="p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl text-xs text-slate-200 font-semibold flex items-center justify-between">
                <span>{step}</span>
                <ChevronRight className="w-4 h-4 text-slate-500" />
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full text-center text-xs text-slate-500 border-t border-slate-800/80 pt-6">
        CodeTarget Platform &copy; {new Date().getFullYear()} — Assessment Performance Summary
      </footer>
    </div>
  );
}
