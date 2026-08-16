"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Editor from "@monaco-editor/react";
import { useAuth } from "@/lib/auth-context";
import {
  fetchProblemBySlug,
  runSampleCode,
  submitSolution,
  fetchSubmissionsForProblem,
  unlockNextHint,
  fetchAIHintsHistory,
  generateAIHint,
  fetchLatestAICodeReview,
  generateAICodeReview,
  toggleBookmark,
  updateNotes,
  ProblemDetail,
  BatchExecutionResult,
  Submission,
  Hint,
  UserAIHintItem,
  AICodeReviewResponse,
} from "@/lib/api";
import {
  Play,
  Send,
  RotateCcw,
  Bookmark,
  Lightbulb,
  FileText,
  History,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  ChevronLeft,
  Code2,
  Sparkles,
  Save,
  Bot,
  Loader2,
  Check,
  AlertTriangle,
  Zap,
} from "lucide-react";

export default function ProblemWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { user, accessToken, loading: authLoading } = useAuth();

  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Workspace State
  const [language, setLanguage] = useState<"python" | "java" | "cpp">("python");
  const [code, setCode] = useState<string>("");
  const [activeTab, setActiveTab] = useState<
    "description" | "hints" | "ai_hints" | "code_review" | "submissions" | "notes"
  >("description");

  // Execution & Output State
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [sampleResult, setSampleResult] = useState<BatchExecutionResult | null>(null);
  const [submissionResult, setSubmissionResult] = useState<Submission | null>(null);
  const [activeConsoleTab, setActiveConsoleTab] = useState<"sample" | "submission">("sample");

  // Submissions & Notes State
  const [submissionsList, setSubmissionsList] = useState<Submission[]>([]);
  const [selectedSubmissionCode, setSelectedSubmissionCode] = useState<string | null>(null);
  
  // Static Hints State
  const [unlockedStaticHints, setUnlockedStaticHints] = useState<Hint[]>([]);
  const [unlockingStaticHint, setUnlockingStaticHint] = useState(false);

  // AI Hints State
  const [aiHints, setAiHints] = useState<UserAIHintItem[]>([]);
  const [requestingAIHint, setRequestingAIHint] = useState(false);
  const [aiHintError, setAiHintError] = useState<string | null>(null);

  // AI Code Review State
  const [codeReview, setCodeReview] = useState<AICodeReviewResponse | null>(null);
  const [requestingCodeReview, setRequestingCodeReview] = useState(false);
  const [codeReviewError, setCodeReviewError] = useState<string | null>(null);

  // Bookmarks & Notes
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [notesText, setNotesText] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [notesSavedSuccess, setNotesSavedSuccess] = useState(false);

  // Language Change Warning Modal
  const [showLanguageWarning, setShowLanguageWarning] = useState(false);
  const [pendingLanguage, setPendingLanguage] = useState<"python" | "java" | "cpp">("python");

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
      return;
    }

    if (user?.preferred_language) {
      setLanguage(user.preferred_language);
    }
  }, [user, authLoading, router]);

  // Load problem details & AI history
  useEffect(() => {
    async function loadProblem() {
      if (!accessToken || !slug) return;
      setLoading(true);
      setError(null);
      try {
        const data = await fetchProblemBySlug(slug, accessToken);
        setProblem(data);
        setUnlockedStaticHints(data.hints || []);
        setIsBookmarked(data.is_bookmarked || false);
        setNotesText(data.personal_notes || "");

        // Set initial code (check local storage draft or default starter code)
        const savedDraft = localStorage.getItem(`codetarget_draft_${slug}_${language}`);
        if (savedDraft) {
          setCode(savedDraft);
        } else if (data.starter_code?.[language]) {
          setCode(data.starter_code[language]);
        }

        // Fetch AI Hints & Code Review history
        try {
          const [aiHistory, latestReview] = await Promise.all([
            fetchAIHintsHistory(accessToken, data.id),
            fetchLatestAICodeReview(accessToken, data.id),
          ]);
          setAiHints(aiHistory.items || []);
          if (latestReview) {
            setCodeReview(latestReview);
          }
        } catch (e) {
          console.error("AI history load error", e);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load problem");
      } finally {
        setLoading(false);
      }
    }

    loadProblem();
  }, [slug, accessToken]);

  // Save code draft locally
  useEffect(() => {
    if (code && slug && language) {
      localStorage.setItem(`codetarget_draft_${slug}_${language}`, code);
    }
  }, [code, slug, language]);

  // Load submissions history when tab opens
  useEffect(() => {
    if (activeTab === "submissions" && accessToken && problem) {
      fetchSubmissionsForProblem(accessToken, problem.id)
        .then((res) => setSubmissionsList(res.items))
        .catch((err) => console.error(err));
    }
  }, [activeTab, accessToken, problem]);

  const handleLanguageChangeRequest = (newLang: "python" | "java" | "cpp") => {
    if (newLang === language) return;
    const starter = problem?.starter_code?.[language] || "";
    if (code.trim() !== starter.trim()) {
      setPendingLanguage(newLang);
      setShowLanguageWarning(true);
    } else {
      switchLanguage(newLang);
    }
  };

  const switchLanguage = (newLang: "python" | "java" | "cpp") => {
    setLanguage(newLang);
    setShowLanguageWarning(false);
    const savedDraft = localStorage.getItem(`codetarget_draft_${slug}_${newLang}`);
    if (savedDraft) {
      setCode(savedDraft);
    } else if (problem?.starter_code?.[newLang]) {
      setCode(problem.starter_code[newLang]);
    }
  };

  const handleResetCode = () => {
    if (problem?.starter_code?.[language]) {
      setCode(problem.starter_code[language]);
      localStorage.removeItem(`codetarget_draft_${slug}_${language}`);
    }
  };

  const handleRunSample = async () => {
    if (!accessToken || !problem) return;
    setRunning(true);
    setSampleResult(null);
    setActiveConsoleTab("sample");
    try {
      const res = await runSampleCode(accessToken, {
        problem_id: problem.id,
        language,
        code,
      });
      setSampleResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  const handleSubmitSolution = async () => {
    if (!accessToken || !problem) return;
    setSubmitting(true);
    setSubmissionResult(null);
    setActiveConsoleTab("submission");
    try {
      const res = await submitSolution(accessToken, {
        problem_id: problem.id,
        language,
        code,
      });
      setSubmissionResult(res);
      const updated = await fetchProblemBySlug(slug, accessToken);
      setProblem(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUnlockStaticHint = async () => {
    if (!accessToken || !problem) return;
    setUnlockingStaticHint(true);
    try {
      const newHint = await unlockNextHint(accessToken, problem.id);
      setUnlockedStaticHints((prev) => [...prev, newHint]);
      setProblem((prev) =>
        prev ? { ...prev, hints_unlocked: prev.hints_unlocked + 1 } : null
      );
    } catch (err) {
      console.error(err);
    } finally {
      setUnlockingStaticHint(false);
    }
  };

  const handleRequestAIHint = async () => {
    if (!accessToken || !problem) return;
    setRequestingAIHint(true);
    setAiHintError(null);
    try {
      const hintRes = await generateAIHint(accessToken, {
        problem_id: problem.id,
        language,
        source_code: code,
      });
      setAiHints((prev) => [
        ...prev,
        {
          id: String(Date.now()),
          hint_level: hintRes.hint_level,
          language,
          hint_text: hintRes.hint_text,
          focus_concept: hintRes.focus_concept,
          created_at: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setAiHintError(err instanceof Error ? err.message : "Failed to generate AI hint");
    } finally {
      setRequestingAIHint(false);
    }
  };

  const handleRequestAICodeReview = async () => {
    if (!accessToken || !problem) return;
    if (!code || !code.trim()) {
      setCodeReviewError("Please write or paste some source code before requesting a review.");
      return;
    }
    setRequestingCodeReview(true);
    setCodeReviewError(null);
    try {
      const reviewRes = await generateAICodeReview(accessToken, {
        problem_id: problem.id,
        language,
        source_code: code,
      });
      setCodeReview(reviewRes);
    } catch (err) {
      setCodeReviewError(err instanceof Error ? err.message : "Failed to generate AI code review");
    } finally {
      setRequestingCodeReview(false);
    }
  };

  const handleToggleBookmark = async () => {
    if (!accessToken || !problem) return;
    const nextState = !isBookmarked;
    setIsBookmarked(nextState);
    try {
      await toggleBookmark(accessToken, problem.id, nextState);
    } catch (err) {
      setIsBookmarked(!nextState);
    }
  };

  const handleSaveNotes = async () => {
    if (!accessToken || !problem) return;
    setSavingNotes(true);
    setNotesSavedSuccess(false);
    try {
      await updateNotes(accessToken, problem.id, notesText);
      setNotesSavedSuccess(true);
      setTimeout(() => setNotesSavedSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSavingNotes(false);
    }
  };

  const getAIHintLevelLabel = (level: number) => {
    switch (level) {
      case 1:
        return "Level 1: Conceptual Direction";
      case 2:
        return "Level 2: Algorithmic Strategy";
      case 3:
        return "Level 3: Tactical Guidance";
      default:
        return `Level ${level}`;
    }
  };

  if (loading || authLoading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center text-slate-400">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p>Loading coding workspace...</p>
        </div>
      </div>
    );
  }

  if (error || !problem) {
    return (
      <div className="min-h-screen bg-[#0B0F17] p-8 flex items-center justify-center text-slate-300">
        <div className="max-w-md text-center bg-slate-900 border border-slate-800 p-8 rounded-2xl space-y-4">
          <AlertCircle className="w-12 h-12 text-rose-400 mx-auto" />
          <h2 className="text-xl font-bold text-white">Problem Not Found</h2>
          <p className="text-sm text-slate-400">{error || "Could not retrieve problem details."}</p>
          <Link
            href="/problems"
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition-colors"
          >
            Back to Catalog
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#0B0F17] text-slate-100 flex flex-col overflow-hidden">
      {/* Navigation Top Bar */}
      <header className="h-14 bg-slate-900/90 border-b border-slate-800 px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-4">
          <Link
            href="/problems"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center text-xs font-medium space-x-1"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Catalog</span>
          </Link>
          <div className="h-4 w-px bg-slate-800" />
          <h1 className="text-sm font-bold text-white tracking-tight flex items-center space-x-2">
            <span>{problem.title}</span>
            {problem.user_status === "SOLVED" && (
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
                Solved
              </span>
            )}
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleToggleBookmark}
            className={`p-2 rounded-lg border transition-colors flex items-center space-x-1.5 text-xs font-medium ${
              isBookmarked
                ? "bg-indigo-950/60 text-indigo-300 border-indigo-700"
                : "bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            <Bookmark className={`w-4 h-4 ${isBookmarked ? "fill-indigo-400" : ""}`} />
            <span className="hidden sm:inline">{isBookmarked ? "Bookmarked" : "Bookmark"}</span>
          </button>
        </div>
      </header>

      {/* Main Two-Panel Split Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Panel */}
        <div className="lg:col-span-5 border-r border-slate-800 flex flex-col bg-slate-950/50 overflow-hidden">
          {/* Tab Navigation */}
          <div className="flex items-center border-b border-slate-800 bg-slate-900/60 px-2 shrink-0 overflow-x-auto">
            {[
              { id: "description", label: "Description", icon: FileText },
              { id: "hints", label: `Curated (${unlockedStaticHints.length}/3)`, icon: Lightbulb },
              { id: "ai_hints", label: `AI Mentor (${aiHints.length}/3)`, icon: Bot },
              { id: "code_review", label: "AI Code Review", icon: Sparkles },
              { id: "submissions", label: "Submissions", icon: History },
              { id: "notes", label: "Notes", icon: Save },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-1.5 px-3.5 py-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? "border-indigo-500 text-indigo-400 bg-slate-800/40"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Content */}
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            {activeTab === "description" && (
              <div className="space-y-6 text-sm text-slate-300">
                <div className="flex flex-wrap items-center gap-2 pb-4 border-b border-slate-800">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {problem.difficulty}
                  </span>
                  {problem.topics.map((t) => (
                    <span
                      key={t.id}
                      className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300 border border-slate-700"
                    >
                      {t.name}
                    </span>
                  ))}
                </div>

                <div className="prose prose-invert max-w-none text-slate-200 whitespace-pre-line font-sans text-sm leading-relaxed">
                  {problem.description_markdown}
                </div>

                {problem.constraints_text && (
                  <div className="space-y-2 pt-2">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Constraints
                    </h3>
                    <pre className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 whitespace-pre-wrap">
                      {problem.constraints_text}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {activeTab === "hints" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white">Curated Hints</h3>
                    <p className="text-[11px] text-slate-400">Static hints provided by problem authors</p>
                  </div>
                  {unlockedStaticHints.length < 3 && (
                    <button
                      disabled={unlockingStaticHint}
                      onClick={handleUnlockStaticHint}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1"
                    >
                      <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                      <span>{unlockingStaticHint ? "Unlocking..." : `Unlock Hint ${unlockedStaticHints.length + 1}`}</span>
                    </button>
                  )}
                </div>

                {unlockedStaticHints.length === 0 ? (
                  <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 text-slate-400">
                    <Lightbulb className="w-8 h-8 text-slate-600 mx-auto" />
                    <p className="text-xs">No curated static hints unlocked yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {unlockedStaticHints.map((hint) => (
                      <div
                        key={hint.id}
                        className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2"
                      >
                        <div className="flex items-center space-x-2 text-slate-300 font-semibold text-xs">
                          <Lightbulb className="w-4 h-4 text-amber-400" />
                          <span>Curated Hint {hint.step_number}: {hint.title}</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {hint.content_markdown}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* AI Mentor Progressive Hints Tab */}
            {activeTab === "ai_hints" && (
              <div className="space-y-5">
                <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 to-violet-950/40 border border-indigo-500/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
                        <Bot className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">AI Code Mentor</h3>
                        <p className="text-[11px] text-slate-400">Contextual guidance based on your current code draft</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-indigo-300 bg-indigo-500/20 border border-indigo-500/30 px-2.5 py-1 rounded-full">
                      {aiHints.length} / 3 Used
                    </span>
                  </div>

                  {problem.user_status === "SOLVED" ? (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-400">
                      You have already solved this problem! Review your approach or optimize your code instead of requesting hints.
                    </div>
                  ) : aiHints.length < 3 ? (
                    <button
                      disabled={requestingAIHint}
                      onClick={handleRequestAIHint}
                      className="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition-all shadow-md shadow-indigo-500/20 flex items-center justify-center space-x-2"
                    >
                      {requestingAIHint ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin text-white" />
                          <span>Your AI mentor is thinking...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-indigo-200" />
                          <span>{aiHints.length === 0 ? "Get AI Hint 1 (Conceptual)" : aiHints.length === 1 ? "Get AI Hint 2 (Strategic)" : "Get AI Hint 3 (Tactical)"}</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400 text-center font-medium">
                      You have used all 3 AI hints for this problem.
                    </div>
                  )}
                </div>

                {aiHintError && (
                  <div className="p-3 bg-rose-950/40 border border-rose-800/40 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{aiHintError}</span>
                  </div>
                )}

                <div className="space-y-4">
                  {aiHints.length === 0 ? (
                    <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 text-slate-400">
                      <Bot className="w-8 h-8 text-indigo-400/40 mx-auto" />
                      <p className="text-xs font-semibold text-slate-300">Need personalized guidance?</p>
                      <p className="text-[11px] text-slate-500">
                        Click "Get AI Hint" above to receive guidance without revealing the answer.
                      </p>
                    </div>
                  ) : (
                    aiHints.map((hint, idx) => (
                      <div
                        key={hint.id || idx}
                        className="p-5 bg-slate-900/90 border border-indigo-500/30 rounded-xl space-y-3 shadow-lg"
                      >
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <span className="text-xs font-bold text-indigo-400 flex items-center space-x-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                            <span>{getAIHintLevelLabel(hint.hint_level)}</span>
                          </span>
                          {hint.focus_concept && (
                            <span className="text-[10px] font-semibold text-violet-300 bg-violet-950/60 px-2 py-0.5 rounded border border-violet-800/40">
                              {hint.focus_concept}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                          {hint.hint_text}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* AI Code Review Tab (Phase 4C) */}
            {activeTab === "code_review" && (
              <div className="space-y-5">
                <div className="p-5 rounded-xl bg-gradient-to-r from-violet-950/40 to-indigo-950/40 border border-violet-500/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2.5">
                      <div className="p-2 rounded-lg bg-violet-500/20 text-violet-400">
                        <Sparkles className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">AI Code Reviewer</h3>
                        <p className="text-[11px] text-slate-400">Get constructive correctness & Big-O feedback on your code draft</p>
                      </div>
                    </div>
                  </div>

                  <button
                    disabled={requestingCodeReview}
                    onClick={handleRequestAICodeReview}
                    className="w-full py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition-all shadow-md shadow-violet-500/20 flex items-center justify-center space-x-2"
                  >
                    {requestingCodeReview ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span>Analyzing your code solution...</span>
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 text-amber-300 fill-amber-300" />
                        <span>Review My Code</span>
                      </>
                    )}
                  </button>
                </div>

                {codeReviewError && (
                  <div className="p-3 bg-rose-950/40 border border-rose-800/40 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{codeReviewError}</span>
                  </div>
                )}

                {!codeReview ? (
                  <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 text-slate-400">
                    <Sparkles className="w-8 h-8 text-violet-400/40 mx-auto" />
                    <p className="text-xs font-semibold text-slate-300">Ready for code review?</p>
                    <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                      Write your solution in the editor and click "Review My Code" to receive correctness analysis and Big-O performance metrics.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Safe Judge0 Context Banner */}
                    {codeReview.judge0_status && (
                      <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                        <span className="text-slate-400 font-medium">Judge0 Execution Context:</span>
                        <span className={`font-bold ${codeReview.judge0_status === "ACCEPTED" ? "text-emerald-400" : "text-rose-400"}`}>
                          {codeReview.judge0_status}
                        </span>
                      </div>
                    )}

                    {/* Summary */}
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Overall Assessment</h4>
                      <p className="text-xs text-slate-200 leading-relaxed">{codeReview.summary}</p>
                    </div>

                    {/* Correctness & Asymptotic Complexity Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                        <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Correctness</h4>
                        <div className="text-xs font-bold text-indigo-300 bg-indigo-950/60 p-2 rounded border border-indigo-800/40">
                          {codeReview.correctness_assessment}
                        </div>
                      </div>

                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                        <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Asymptotic Complexity</h4>
                        <div className="flex items-center space-x-2 text-xs">
                          <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded font-mono font-bold">
                            Time: {codeReview.time_complexity}
                          </span>
                          <span className="px-2.5 py-1 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded font-mono font-bold">
                            Space: {codeReview.space_complexity}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Strengths */}
                    {codeReview.strengths?.length > 0 && (
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                        <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>What You Did Well</span>
                        </h4>
                        <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                          {codeReview.strengths.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Potential Bugs */}
                    {codeReview.bugs?.length > 0 && (
                      <div className="p-4 bg-slate-900 border border-rose-900/30 rounded-xl space-y-2">
                        <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center space-x-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                          <span>Potential Issues & Bugs</span>
                        </h4>
                        <ul className="space-y-1 text-xs text-rose-200 list-disc list-inside">
                          {codeReview.bugs.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Actionable Improvements */}
                    {codeReview.improvements?.length > 0 && (
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                        <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                          <span>Refactoring & Optimization Areas</span>
                        </h4>
                        <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                          {codeReview.improvements.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === "submissions" && (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white">Submission History</h3>
                {submissionsList.length === 0 ? (
                  <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl text-slate-400 text-xs">
                    No submissions recorded yet for this problem.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {submissionsList.map((sub) => (
                      <div
                        key={sub.id}
                        onClick={() => setSelectedSubmissionCode(selectedSubmissionCode === sub.code ? null : sub.code)}
                        className="p-3 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl cursor-pointer transition-colors space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2 font-semibold">
                            {sub.status === "ACCEPTED" ? (
                              <span className="text-emerald-400 flex items-center space-x-1">
                                <CheckCircle2 className="w-4 h-4" />
                                <span>Accepted</span>
                              </span>
                            ) : (
                              <span className="text-rose-400 flex items-center space-x-1">
                                <XCircle className="w-4 h-4" />
                                <span>{sub.status}</span>
                              </span>
                            )}
                            <span className="text-slate-500">• {sub.language}</span>
                          </div>
                          <span className="text-slate-500">
                            {new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>

                        {selectedSubmissionCode === sub.code && (
                          <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto">
                            {sub.code}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "notes" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">Personal Notes</h3>
                  <button
                    disabled={savingNotes}
                    onClick={handleSaveNotes}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors flex items-center space-x-1"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{savingNotes ? "Saving..." : "Save Notes"}</span>
                  </button>
                </div>

                {notesSavedSuccess && (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-lg">
                    Notes saved successfully.
                  </div>
                )}

                <textarea
                  rows={10}
                  value={notesText}
                  onChange={(e) => setNotesText(e.target.value)}
                  placeholder="Write personal notes, complexity thoughts, or key algorithmic steps..."
                  className="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono leading-relaxed"
                />
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Monaco Code Editor & Execution Console */}
        <div className="lg:col-span-7 flex flex-col bg-[#0B0F17] overflow-hidden">
          <div className="h-12 bg-slate-900/80 border-b border-slate-800 px-4 flex items-center justify-between shrink-0">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-400 font-medium">Language:</span>
              <select
                value={language}
                onChange={(e) => handleLanguageChangeRequest(e.target.value as any)}
                className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-indigo-500 font-semibold"
              >
                <option value="python">Python 3</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleResetCode}
                title="Reset starter code"
                className="p-1.5 text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-700 rounded-lg transition-colors border border-slate-700"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                disabled={running || submitting}
                onClick={handleRunSample}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5"
              >
                <Play className="w-3.5 h-3.5 text-emerald-400 fill-emerald-400" />
                <span>{running ? "Running..." : "Run Sample"}</span>
              </button>
              <button
                disabled={running || submitting}
                onClick={handleSubmitSolution}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5 shadow"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submitting ? "Submitting..." : "Submit"}</span>
              </button>
            </div>
          </div>

          <div className="flex-1 bg-[#1e1e1e] relative min-h-[300px]">
            <Editor
              height="100%"
              language={language === "cpp" ? "cpp" : language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || "")}
              options={{
                fontSize: 14,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
              }}
            />
          </div>

          <div className="h-64 border-t border-slate-800 bg-slate-950 flex flex-col shrink-0">
            <div className="h-9 bg-slate-900 border-b border-slate-800 px-4 flex items-center space-x-4 text-xs font-medium">
              <button
                onClick={() => setActiveConsoleTab("sample")}
                className={`h-full border-b-2 px-1 flex items-center space-x-1.5 ${
                  activeConsoleTab === "sample"
                    ? "border-indigo-500 text-indigo-400 font-semibold"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>Sample Test Results</span>
              </button>
              <button
                onClick={() => setActiveConsoleTab("submission")}
                className={`h-full border-b-2 px-1 flex items-center space-x-1.5 ${
                  activeConsoleTab === "submission"
                    ? "border-indigo-500 text-indigo-400 font-semibold"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>Submission Output</span>
              </button>
            </div>

            <div className="flex-1 p-4 overflow-y-auto font-mono text-xs text-slate-300">
              {activeConsoleTab === "sample" && (
                <div>
                  {running ? (
                    <div className="flex items-center space-x-2 text-slate-400 p-4">
                      <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      <span>Executing code against sample test cases...</span>
                    </div>
                  ) : !sampleResult ? (
                    <div className="text-slate-500 p-4">
                      Run your code to see sample test outputs here.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3 font-sans">
                        <span className={`font-bold ${sampleResult.overall_status === "ACCEPTED" ? "text-emerald-400" : "text-rose-400"}`}>
                          {sampleResult.overall_status}
                        </span>
                        <span className="text-slate-400">
                          Passed: {sampleResult.passed_test_cases} / {sampleResult.total_test_cases}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeConsoleTab === "submission" && (
                <div>
                  {submitting ? (
                    <div className="flex items-center space-x-2 text-slate-400 p-4">
                      <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      <span>Evaluating solution against hidden evaluation cases...</span>
                    </div>
                  ) : !submissionResult ? (
                    <div className="text-slate-500 p-4">
                      Submit your solution to view evaluation status.
                    </div>
                  ) : (
                    <div className="space-y-3 font-sans">
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2 font-bold text-base">
                            {submissionResult.status === "ACCEPTED" ? (
                              <span className="text-emerald-400 flex items-center space-x-1.5">
                                <CheckCircle2 className="w-5 h-5" />
                                <span>Accepted</span>
                              </span>
                            ) : (
                              <span className="text-rose-400 flex items-center space-x-1.5">
                                <XCircle className="w-5 h-5" />
                                <span>{submissionResult.status}</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showLanguageWarning && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-amber-400" />
              <span>Change Language?</span>
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Changing language will load starter code for {pendingLanguage}. Your current code draft is saved locally.
            </p>
            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowLanguageWarning(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={() => switchLanguage(pendingLanguage)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
