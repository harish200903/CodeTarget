"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  fetchCompanyPreparation,
  CompanyPreparationResponse,
  UserTargetCompany,
} from "@/lib/api";
import {
  Building2, Target, CheckCircle2, AlertCircle, ArrowRight, Star, Sparkles,
  BarChart3, Award, TrendingUp, ShieldCheck, ChevronRight, HelpCircle, RefreshCw
} from "lucide-react";

export default function CompanyPreparationPage() {
  const { user, accessToken, loading, logout } = useAuth();
  const router = useRouter();

  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [prepData, setPrepData] = useState<CompanyPreparationResponse | null>(null);
  const [prepLoading, setPrepLoading] = useState(true);
  const [prepError, setPrepError] = useState<string | null>(null);
  const [showExplanationModal, setShowExplanationModal] = useState(false);

  // Route Protection Guard
  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/login");
      } else if (!user.onboarding_completed) {
        router.push("/onboarding");
      } else if (user.target_companies && user.target_companies.length > 0) {
        // Set primary company as default
        const primary = user.target_companies.find((tc) => tc.priority === 1);
        if (primary && !selectedCompanyId) {
          setSelectedCompanyId(primary.company_id);
        } else if (!selectedCompanyId) {
          setSelectedCompanyId(user.target_companies[0].company_id);
        }
      }
    }
  }, [user, loading, router, selectedCompanyId]);

  // Load Company Preparation Analytics
  useEffect(() => {
    async function loadPrep() {
      if (!accessToken || !selectedCompanyId) return;
      setPrepLoading(true);
      setPrepError(null);
      try {
        const data = await fetchCompanyPreparation(accessToken, selectedCompanyId);
        setPrepData(data);
      } catch (err) {
        setPrepError(err instanceof Error ? err.message : "Failed to load company preparation");
      } finally {
        setPrepLoading(false);
      }
    }

    loadPrep();
  }, [accessToken, selectedCompanyId]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F17]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading preparation metrics...</p>
        </div>
      </div>
    );
  }

  const targetCompanies: UserTargetCompany[] = user.target_companies || [];

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col justify-between p-6 md:p-12 max-w-6xl mx-auto space-y-10">
      {/* Top Navbar */}
      <header className="w-full flex flex-wrap items-center justify-between border-b border-slate-800 pb-6 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/20">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Company Preparation Intelligence</h1>
            <p className="text-xs text-slate-400">Target-Specific Interview Preparation & Analytics</p>
          </div>
        </div>

        {/* Company Switcher Dropdown */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-semibold">Target Company:</label>
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-100 font-bold text-xs rounded-xl px-4 py-2 focus:outline-none focus:border-indigo-500"
          >
            {targetCompanies.map((tc) => (
              <option key={tc.id} value={tc.company_id}>
                {tc.company.name} {tc.priority === 1 ? "★ (Primary)" : ""}
              </option>
            ))}
          </select>

          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold text-xs transition-colors"
          >
            Dashboard
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="space-y-8">
        {prepLoading ? (
          <div className="p-12 bg-slate-900/60 border border-slate-800 rounded-2xl text-center space-y-4 animate-pulse">
            <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-slate-400">Computing preparation coverage & topic metrics...</p>
          </div>
        ) : prepError ? (
          <div className="p-6 bg-rose-950/30 border border-rose-800/30 rounded-2xl text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{prepError}</span>
          </div>
        ) : !prepData ? null : (
          <>
            {/* Score & Hero Summary Card */}
            <div className="glass-panel rounded-2xl p-8 border border-slate-800 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
                {/* Score Gauge Circle */}
                <div className="md:col-span-4 flex flex-col items-center justify-center p-6 bg-slate-900/90 border border-slate-800 rounded-2xl text-center space-y-3 shadow-inner">
                  <div className="relative w-32 h-32 flex items-center justify-center rounded-full bg-gradient-to-tr from-indigo-950 to-slate-900 border-4 border-indigo-500/40 shadow-lg">
                    <div className="text-center">
                      <span className="text-3xl font-black text-white">
                        {prepData.preparation_score !== null ? prepData.preparation_score : "--"}
                      </span>
                      <span className="text-[10px] text-slate-400 font-bold block">/ 100</span>
                    </div>
                  </div>

                  <div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      prepData.status === "WELL_PREPARED"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : prepData.status === "DEVELOPING"
                        ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                        : prepData.status === "STARTING"
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}>
                      {prepData.status.replace("_", " ")}
                    </span>
                  </div>

                  <button
                    onClick={() => setShowExplanationModal(true)}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition-colors"
                  >
                    <HelpCircle className="w-3.5 h-3.5" /> How is this score calculated?
                  </button>
                </div>

                {/* Status Overview & AI Explanation */}
                <div className="md:col-span-8 space-y-4">
                  <div className="space-y-1.5">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                      <Star className="w-3.5 h-3.5 fill-current text-indigo-400" />
                      <span>{prepData.company.name} Target Preparation</span>
                    </div>
                    <h2 className="text-2xl font-extrabold text-white">{prepData.confidence_message}</h2>
                  </div>

                  {prepData.ai_explanation && (
                    <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 to-violet-950/40 border border-indigo-500/30 text-xs text-slate-200 leading-relaxed font-sans space-y-1">
                      <span className="text-indigo-400 font-bold flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> AI Personal Preparation Synthesis
                      </span>
                      <p>{prepData.ai_explanation}</p>
                    </div>
                  )}

                  <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-[11px] text-slate-400 leading-relaxed">
                    Disclaimer: CodeTarget Preparation Coverage Score is a deterministic preparation metric based on platform activity. It is NOT an official company score or a prediction of interview selection.
                  </div>
                </div>
              </div>
            </div>

            {/* Coverage Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-2">
                <span className="text-xs text-slate-400 font-semibold block">Problem Coverage</span>
                <div className="text-2xl font-black text-white">
                  {prepData.problems.solved} / {prepData.problems.available}
                </div>
                <p className="text-[11px] text-slate-500">Solved company problems</p>
              </div>

              <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-2">
                <span className="text-xs text-slate-400 font-semibold block">Topic Coverage</span>
                <div className="text-2xl font-black text-indigo-400">{prepData.coverage.topics}%</div>
                <p className="text-[11px] text-slate-500">Target topics explored</p>
              </div>

              <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-2">
                <span className="text-xs text-slate-400 font-semibold block">Difficulty Fit</span>
                <div className="text-2xl font-black text-emerald-400">{prepData.coverage.difficulty}%</div>
                <p className="text-[11px] text-slate-500">Skill-calibrated exposure</p>
              </div>

              <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-2">
                <span className="text-xs text-slate-400 font-semibold block">Attempt Success Rate</span>
                <div className="text-2xl font-black text-amber-400">
                  {prepData.problems.attempted > 0
                    ? `${Math.round((prepData.problems.solved / prepData.problems.attempted) * 100)}%`
                    : "0%"}
                </div>
                <p className="text-[11px] text-slate-500">Solved / Attempted ratio</p>
              </div>
            </div>

            {/* Topic & Difficulty Breakdown Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Topic Breakdown */}
              <div className="lg:col-span-7 glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-indigo-400" /> Topic Breakdown for {prepData.company.name}
                </h3>

                {prepData.topic_breakdown.length === 0 ? (
                  <p className="text-xs text-slate-400 p-4">No topic data available yet.</p>
                ) : (
                  <div className="space-y-4">
                    {prepData.topic_breakdown.map((t) => (
                      <div key={t.topic_id} className="space-y-1.5">
                        <div className="flex items-center justify-between text-xs font-semibold">
                          <span className="text-slate-200">{t.topic_name}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-slate-400">{t.solved}/{t.available} solved</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              t.status === "STRONG"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : t.status === "DEVELOPING"
                                ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                                : t.status === "NEEDS_PRACTICE"
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                : "bg-slate-800 text-slate-500 border border-slate-700"
                            }`}>
                              {t.status.replace("_", " ")}
                            </span>
                          </div>
                        </div>

                        <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              t.status === "STRONG"
                                ? "bg-emerald-500"
                                : t.status === "DEVELOPING"
                                ? "bg-indigo-500"
                                : t.status === "NEEDS_PRACTICE"
                                ? "bg-rose-500"
                                : "bg-slate-800"
                            }`}
                            style={{ width: `${t.coverage_pct}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Difficulty Breakdown */}
              <div className="lg:col-span-5 glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" /> Difficulty Breakdown
                </h3>

                <div className="space-y-4">
                  {prepData.difficulty_breakdown.map((d) => (
                    <div key={d.difficulty} className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-2">
                      <div className="flex items-center justify-between text-xs font-bold">
                        <span className={
                          d.difficulty === "EASY" ? "text-emerald-400" : d.difficulty === "MEDIUM" ? "text-amber-400" : "text-rose-400"
                        }>
                          {d.difficulty}
                        </span>
                        <span className="text-slate-300">{d.solved} / {d.available} Solved</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            d.difficulty === "EASY" ? "bg-emerald-500" : d.difficulty === "MEDIUM" ? "bg-amber-500" : "bg-rose-500"
                          }`}
                          style={{ width: `${(d.solved / maxVal(d.available, 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Strengths & Focus Areas */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Strengths
                </h4>
                <ul className="space-y-2 text-xs text-slate-300 list-disc list-inside">
                  {prepData.strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>

              <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-amber-400" /> Focus Areas
                </h4>
                <ul className="space-y-2 text-xs text-slate-300 list-disc list-inside">
                  {prepData.focus_areas.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommended Next Steps */}
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ArrowRight className="w-5 h-5 text-indigo-400" /> Recommended Next Steps
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {prepData.recommended_next_steps.map((step, i) => (
                  <div key={i} className="p-4 bg-slate-900/90 border border-slate-800 rounded-xl text-xs text-slate-200 font-semibold flex items-center justify-between">
                    <span>{step}</span>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </main>

      {/* Explanation Modal */}
      {showExplanationModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-indigo-400" /> How is this score calculated?
            </h3>
            <div className="text-xs text-slate-300 leading-relaxed space-y-3">
              <p>The CodeTarget Preparation Coverage Score (0-100) is a transparent, deterministic preparation metric combining 5 components:</p>
              <ul className="list-disc list-inside space-y-1 text-slate-400">
                <li><strong className="text-slate-200">Problem Coverage (30%):</strong> Solved company problem ratio.</li>
                <li><strong className="text-slate-200">Topic Coverage (25%):</strong> Target topics with solved problems.</li>
                <li><strong className="text-slate-200">Difficulty Exposure (20%):</strong> Skill-calibrated difficulty ratio.</li>
                <li><strong className="text-slate-200">Success Rate (15%):</strong> Solve accuracy across attempted questions.</li>
                <li><strong className="text-slate-200">Recent Performance (10%):</strong> Acceptance rate on recent submissions.</li>
              </ul>
              <p className="text-[11px] text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800">
                Notice: This metric evaluates your preparation progress against the platform problem catalog. It is not an official company score or a guarantee of selection.
              </p>
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowExplanationModal(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="w-full text-center text-xs text-slate-500 border-t border-slate-800/80 pt-6">
        CodeTarget Platform &copy; {new Date().getFullYear()} — Company-Specific Preparation Platform
      </footer>
    </div>
  );
}

function maxVal(a: number, b: number): number {
  return a > b ? a : b;
}
