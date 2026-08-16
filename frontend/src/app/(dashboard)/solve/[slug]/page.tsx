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
  toggleBookmark,
  updateNotes,
  ProblemDetail,
  BatchExecutionResult,
  Submission,
  Hint,
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
  const [activeTab, setActiveTab] = useState<"description" | "hints" | "submissions" | "notes">("description");
  
  // Execution & Output State
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [sampleResult, setSampleResult] = useState<BatchExecutionResult | null>(null);
  const [submissionResult, setSubmissionResult] = useState<Submission | null>(null);
  const [activeConsoleTab, setActiveConsoleTab] = useState<"sample" | "submission">("sample");

  // Submissions & Notes & Hints State
  const [submissionsList, setSubmissionsList] = useState<Submission[]>([]);
  const [selectedSubmissionCode, setSelectedSubmissionCode] = useState<string | null>(null);
  const [unlockedHints, setUnlockedHints] = useState<Hint[]>([]);
  const [unlockingHint, setUnlockingHint] = useState(false);
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

  // Load problem details
  useEffect(() => {
    async function loadProblem() {
      if (!accessToken || !slug) return;
      setLoading(true);
      setError(null);
      try {
        const data = await fetchProblemBySlug(slug, accessToken);
        setProblem(data);
        setUnlockedHints(data.hints || []);
        setIsBookmarked(data.is_bookmarked || false);
        setNotesText(data.personal_notes || "");

        // Set initial code (check local storage draft or default starter code)
        const savedDraft = localStorage.getItem(`codetarget_draft_${slug}_${language}`);
        if (savedDraft) {
          setCode(savedDraft);
        } else if (data.starter_code?.[language]) {
          setCode(data.starter_code[language]);
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
    // If current code has been modified from starter, warn user
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
      // Reload problem detail to reflect updated progress (SOLVED/ATTEMPTED)
      const updated = await fetchProblemBySlug(slug, accessToken);
      setProblem(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUnlockHint = async () => {
    if (!accessToken || !problem) return;
    setUnlockingHint(true);
    try {
      const newHint = await unlockNextHint(accessToken, problem.id);
      setUnlockedHints((prev) => [...prev, newHint]);
      setProblem((prev) =>
        prev ? { ...prev, hints_unlocked: prev.hints_unlocked + 1 } : null
      );
    } catch (err) {
      console.error(err);
    } finally {
      setUnlockingHint(false);
    }
  };

  const handleToggleBookmark = async () => {
    if (!accessToken || !problem) return;
    const nextState = !isBookmarked;
    setIsBookmarked(nextState);
    try {
      await toggleBookmark(accessToken, problem.id, nextState);
    } catch (err) {
      setIsBookmarked(!nextState); // Rollback on error
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
        {/* Left Panel: Problem Specs, Description, Hints, Submissions, Notes */}
        <div className="lg:col-span-5 border-r border-slate-800 flex flex-col bg-slate-950/50 overflow-hidden">
          {/* Tab Selection Navigation */}
          <div className="flex items-center border-b border-slate-800 bg-slate-900/60 px-2 shrink-0">
            {[
              { id: "description", label: "Description", icon: FileText },
              { id: "hints", label: `Hints (${unlockedHints.length})`, icon: Lightbulb },
              { id: "submissions", label: "Submissions", icon: History },
              { id: "notes", label: "Notes", icon: Sparkles },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-4 py-3 text-xs font-medium border-b-2 transition-colors ${
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

          {/* Tab Content Panel */}
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            {activeTab === "description" && (
              <div className="space-y-6 text-sm text-slate-300">
                {/* Difficulty & Categories */}
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

                {/* Markdown Problem Description */}
                <div className="prose prose-invert max-w-none text-slate-200 whitespace-pre-line font-sans text-sm leading-relaxed">
                  {problem.description_markdown}
                </div>

                {/* Constraints */}
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

                {/* Associated Recruiter Target Companies */}
                {problem.companies.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Target Recruiters
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {problem.companies.map((pc) => (
                        <span
                          key={pc.id}
                          className="px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-950/40 text-indigo-300 border border-indigo-800/40"
                        >
                          {pc.company.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "hints" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">Progressive Hints</h3>
                  {unlockedHints.length < 3 && (
                    <button
                      disabled={unlockingHint}
                      onClick={handleUnlockHint}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors flex items-center space-x-1"
                    >
                      <Lightbulb className="w-3.5 h-3.5" />
                      <span>{unlockingHint ? "Unlocking..." : `Unlock Hint ${unlockedHints.length + 1}`}</span>
                    </button>
                  )}
                </div>

                {unlockedHints.length === 0 ? (
                  <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 text-slate-400">
                    <Lightbulb className="w-8 h-8 text-amber-400/60 mx-auto" />
                    <p className="text-xs">No hints unlocked yet. Click above to reveal progressive guidance.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {unlockedHints.map((hint) => (
                      <div
                        key={hint.id}
                        className="p-4 bg-slate-900 border border-amber-500/20 rounded-xl space-y-2"
                      >
                        <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs">
                          <Lightbulb className="w-4 h-4" />
                          <span>Hint {hint.step_number}: {hint.title}</span>
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

                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span>Passed: {sub.passed_test_cases}/{sub.total_test_cases}</span>
                          {sub.execution_time_ms !== undefined && (
                            <span>{sub.execution_time_ms} ms</span>
                          )}
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
          {/* Editor Header Toolbar */}
          <div className="h-12 bg-slate-900/80 border-b border-slate-800 px-4 flex items-center justify-between shrink-0">
            {/* Language Selector */}
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

            {/* Actions */}
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

          {/* Monaco Editor Container */}
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

          {/* Bottom Execution Console Panel */}
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
                        {sampleResult.execution_time_ms !== undefined && (
                          <span className="text-slate-500">• {sampleResult.execution_time_ms} ms</span>
                        )}
                      </div>

                      <div className="space-y-3">
                        {sampleResult.test_case_results.map((tc, idx) => (
                          <div key={idx} className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
                            <div className="flex items-center space-x-2 font-sans font-semibold">
                              {tc.passed ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                              ) : (
                                <XCircle className="w-4 h-4 text-rose-400" />
                              )}
                              <span>Test Case {idx + 1}</span>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-xs">
                              <div>
                                <span className="text-slate-500 block">Input:</span>
                                <pre className="bg-slate-950 p-2 rounded text-slate-300">{tc.input_data}</pre>
                              </div>
                              <div>
                                <span className="text-slate-500 block">Expected:</span>
                                <pre className="bg-slate-950 p-2 rounded text-slate-300">{tc.expected_output}</pre>
                              </div>
                            </div>
                            {!tc.passed && tc.actual_output && (
                              <div>
                                <span className="text-slate-500 block">Received:</span>
                                <pre className="bg-slate-950 p-2 rounded text-rose-300">{tc.actual_output}</pre>
                              </div>
                            )}
                            {tc.error_message && (
                              <pre className="bg-rose-950/40 border border-rose-800/40 p-2 rounded text-rose-300 whitespace-pre-wrap">
                                {tc.error_message}
                              </pre>
                            )}
                          </div>
                        ))}
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
                          <span className="text-xs text-slate-400">
                            Passed {submissionResult.passed_test_cases} / {submissionResult.total_test_cases} test cases
                          </span>
                        </div>

                        {submissionResult.execution_time_ms !== undefined && (
                          <div className="text-xs text-slate-400 flex items-center space-x-4 pt-2">
                            <span>Runtime: {submissionResult.execution_time_ms} ms</span>
                            {submissionResult.memory_kb && (
                              <span>Memory: {submissionResult.memory_kb} KB</span>
                            )}
                          </div>
                        )}

                        {submissionResult.error_output && (
                          <pre className="mt-3 p-3 bg-rose-950/40 border border-rose-800/40 rounded-lg text-xs font-mono text-rose-300 whitespace-pre-wrap">
                            {submissionResult.error_output}
                          </pre>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Language Override Warning Modal */}
      {showLanguageWarning && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-amber-400" />
              <span>Change Language?</span>
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              You have modified code in the editor. Changing language will load the starter code for {pendingLanguage}. Your current code draft is saved locally.
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
