"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { useAuth } from "@/lib/auth-context";
import {
  fetchActiveMockTestSession,
  runMockProblemSample,
  submitMockProblemSolution,
  submitCompleteMockTest,
  UserMockTestSessionResponse,
  MockTestProblemItem,
  BatchExecutionResult,
  SubmitMockProblemResponse,
} from "@/lib/api";
import {
  Clock, Play, Send, AlertCircle, CheckCircle2, ShieldAlert, FileCode2,
  ChevronRight, RefreshCw, XCircle, ArrowLeft, Lock
} from "lucide-react";

// Dynamically import Monaco Editor to avoid SSR hydration issues
const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

export default function TimedMockWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const { user, accessToken, loading } = useAuth();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<UserMockTestSessionResponse | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [sessionError, setSessionError] = useState<string | null>(null);

  const [activeProblemIndex, setActiveProblemIndex] = useState<number>(0);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("python");
  const [codeDrafts, setCodeDrafts] = useState<Record<string, string>>({});

  // Execution states
  const [runningSample, setRunningSample] = useState(false);
  const [sampleResult, setSampleResult] = useState<BatchExecutionResult | null>(null);
  const [submittingProblem, setSubmittingProblem] = useState(false);
  const [problemSubmitResult, setProblemSubmitResult] = useState<SubmitMockProblemResponse | null>(null);

  // Submit test confirmation modal
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [submittingTest, setSubmittingTest] = useState(false);

  // Remaining time in seconds
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);

  // Route protection
  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/login");
      } else if (!user.onboarding_completed) {
        router.push("/onboarding");
      }
    }
  }, [user, loading, router]);

  // Set default language from user preference
  useEffect(() => {
    if (user?.preferred_language) {
      setSelectedLanguage(user.preferred_language);
    }
  }, [user]);

  // Fetch Session Data
  useEffect(() => {
    async function loadSession() {
      if (!accessToken || !sessionId) return;
      setSessionLoading(true);
      setSessionError(null);
      try {
        const data = await fetchActiveMockTestSession(accessToken, sessionId);

        if (data.status === "SUBMITTED" || data.status === "AUTO_SUBMITTED" || data.status === "COMPLETED") {
          router.push(`/mock-tests/${sessionId}/result`);
          return;
        }

        setSession(data);
        setRemainingSeconds(data.remaining_seconds);

        // Populate initial code drafts
        const initialDrafts: Record<string, string> = {};
        data.problems.forEach((p) => {
          if (p.code_draft) {
            initialDrafts[p.problem_id] = p.code_draft;
          }
        });
        setCodeDrafts(initialDrafts);
      } catch (err) {
        setSessionError(err instanceof Error ? err.message : "Failed to load session");
      } finally {
        setSessionLoading(false);
      }
    }

    loadSession();
  }, [accessToken, sessionId, router]);

  // Server-authoritative Timer Countdown
  useEffect(() => {
    if (remainingSeconds <= 0 || !session || session.status !== "IN_PROGRESS") return;

    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          // Auto-submit test on timer expiry
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [remainingSeconds, session]);

  const handleAutoSubmit = async () => {
    if (!accessToken || !sessionId) return;
    try {
      await submitCompleteMockTest(accessToken, sessionId);
      router.push(`/mock-tests/${sessionId}/result`);
    } catch {
      router.push(`/mock-tests/${sessionId}/result`);
    }
  };

  const handleCodeChange = (val?: string) => {
    if (!session) return;
    const currentProb = session.problems[activeProblemIndex];
    if (currentProb && val !== undefined) {
      setCodeDrafts((prev) => ({
        ...prev,
        [currentProb.problem_id]: val,
      }));
    }
  };

  const handleRunSample = async () => {
    if (!accessToken || !session) return;
    const currentProb = session.problems[activeProblemIndex];
    const code = codeDrafts[currentProb.problem_id] || "";

    setRunningSample(true);
    setSampleResult(null);
    setProblemSubmitResult(null);

    try {
      const res = await runMockProblemSample(
        accessToken,
        sessionId,
        currentProb.problem_id,
        selectedLanguage,
        code
      );
      setSampleResult(res);
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to run sample code");
    } finally {
      setRunningSample(false);
    }
  };

  const handleSubmitProblem = async () => {
    if (!accessToken || !session) return;
    const currentProb = session.problems[activeProblemIndex];
    const code = codeDrafts[currentProb.problem_id] || "";

    setSubmittingProblem(true);
    setSampleResult(null);
    setProblemSubmitResult(null);

    try {
      const res = await submitMockProblemSolution(
        accessToken,
        sessionId,
        currentProb.problem_id,
        selectedLanguage,
        code
      );
      setProblemSubmitResult(res);

      // Update problem status in local session state
      setSession((prev) => {
        if (!prev) return prev;
        const updatedProbs = [...prev.problems];
        updatedProbs[activeProblemIndex] = {
          ...updatedProbs[activeProblemIndex],
          user_status: res.status === "ACCEPTED" ? "SOLVED" : "ATTEMPTED",
          score_obtained: res.score_obtained,
        };
        return { ...prev, problems: updatedProbs };
      });
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to submit problem solution");
    } finally {
      setSubmittingProblem(false);
    }
  };

  const handleFinalSubmitTest = async () => {
    if (!accessToken || !sessionId) return;
    setSubmittingTest(true);
    try {
      await submitCompleteMockTest(accessToken, sessionId);
      router.push(`/mock-tests/${sessionId}/result`);
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to submit assessment");
      setSubmittingTest(false);
    }
  };

  if (loading || sessionLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F17]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading assessment workspace...</p>
        </div>
      </div>
    );
  }

  if (sessionError || !session) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#0B0F17] p-6 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400" />
        <p className="text-sm font-semibold text-slate-200">{sessionError || "Session not found"}</p>
        <Link href="/mock-tests" className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold">
          Return to Mock Tests Catalog
        </Link>
      </div>
    );
  }

  const currentProblem = session.problems[activeProblemIndex];
  const minutesLeft = Math.floor(remainingSeconds / 60);
  const secondsLeft = remainingSeconds % 60;
  const formattedTime = `${String(minutesLeft).padStart(2, "0")}:${String(secondsLeft).padStart(2, "0")}`;

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col justify-between text-slate-200">
      {/* Top Header Bar */}
      <header className="w-full bg-slate-900 border-b border-slate-800 px-6 py-3.5 flex items-center justify-between gap-4 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-600 text-white">
            <FileCode2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-none">{session.title}</h1>
            <span className="text-[11px] text-slate-400 font-semibold">{session.company_name} Assessment Simulation</span>
          </div>
        </div>

        {/* Server Countdown Timer */}
        <div className="flex items-center gap-4">
          <div className={`px-4 py-1.5 rounded-xl border text-xs font-black flex items-center gap-2 shadow-inner ${
            remainingSeconds < 300
              ? "bg-rose-950/80 border-rose-500/50 text-rose-400 animate-pulse"
              : remainingSeconds < 600
              ? "bg-amber-950/80 border-amber-500/50 text-amber-400"
              : "bg-slate-950 border-slate-800 text-indigo-400"
          }`}>
            <Clock className="w-4 h-4" />
            <span className="text-sm font-mono">{formattedTime}</span>
          </div>

          <button
            onClick={() => setShowSubmitModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl transition-all shadow-md shadow-emerald-600/20"
          >
            Submit Test
          </button>
        </div>
      </header>

      {/* Strict Restrictions Notice Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border-b border-slate-800/80 px-6 py-2 flex items-center justify-between text-xs text-indigo-300">
        <span className="flex items-center gap-2 font-semibold">
          <Lock className="w-3.5 h-3.5 text-indigo-400" />
          AI Mentor Hints & Code Review are disabled during this assessment simulation.
        </span>
        <span className="text-[11px] text-slate-400 hidden sm:inline">Problem Progress Saved Automatically</span>
      </div>

      {/* Main Workspace Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-0">
        {/* Left Column: Problem List & Problem Description */}
        <div className="lg:col-span-5 border-r border-slate-800 flex flex-col bg-slate-950/50">
          {/* Problem Tabs Header */}
          <div className="flex items-center border-b border-slate-800 bg-slate-900/80 overflow-x-auto">
            {session.problems.map((p, idx) => (
              <button
                key={p.problem_id}
                onClick={() => {
                  setActiveProblemIndex(idx);
                  setSampleResult(null);
                  setProblemSubmitResult(null);
                }}
                className={`px-4 py-3 text-xs font-bold transition-all border-b-2 flex items-center gap-2 shrink-0 ${
                  activeProblemIndex === idx
                    ? "border-indigo-500 text-white bg-slate-900"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                }`}
              >
                <span>{idx + 1}. {p.title}</span>
                {p.user_status === "SOLVED" ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : p.user_status === "ATTEMPTED" ? (
                  <div className="w-2 h-2 rounded-full bg-amber-400" />
                ) : null}
              </button>
            ))}
          </div>

          {/* Problem Details Body */}
          <div className="p-6 overflow-y-auto max-h-[calc(100vh-180px)] space-y-4">
            <div className="flex items-center justify-between">
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                currentProblem.difficulty === "EASY"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : currentProblem.difficulty === "MEDIUM"
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                  : "bg-rose-500/10 text-rose-400 border-rose-500/20"
              }`}>
                {currentProblem.difficulty}
              </span>
              <span className="text-xs text-slate-400 font-semibold">Allocated Points: {currentProblem.weight_score} pts</span>
            </div>

            <h2 className="text-xl font-extrabold text-white">{currentProblem.title}</h2>
            <p className="text-xs text-slate-400 capitalize font-medium">Category: {currentProblem.category}</p>

            <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed font-sans space-y-2">
              <p className="font-semibold text-slate-200">Problem Guidance:</p>
              <p>Solve this problem within the assessment duration. Ensure your solution passes all sample test cases before submitting.</p>
            </div>
          </div>
        </div>

        {/* Right Column: Monaco Code Editor & Execution Panel */}
        <div className="lg:col-span-7 flex flex-col bg-[#0B0F17]">
          {/* Language Selector Toolbar */}
          <div className="p-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-400 font-semibold">Language:</label>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-xs font-bold text-white rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
              >
                <option value="python">Python 3</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
              </select>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleRunSample}
                disabled={runningSample || submittingProblem}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                {runningSample ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current text-indigo-400" />
                )}
                <span>Run Sample</span>
              </button>

              <button
                onClick={handleSubmitProblem}
                disabled={runningSample || submittingProblem}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5 shadow"
              >
                {submittingProblem ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
                <span>Submit Problem</span>
              </button>
            </div>
          </div>

          {/* Monaco Editor */}
          <div className="flex-1 min-h-[350px] border-b border-slate-800">
            <Editor
              height="100%"
              theme="vs-dark"
              language={selectedLanguage === "cpp" ? "cpp" : selectedLanguage === "java" ? "java" : "python"}
              value={codeDrafts[currentProblem.problem_id] || `# Write your solution for ${currentProblem.title} in ${selectedLanguage}\n`}
              onChange={handleCodeChange}
              options={{
                fontSize: 13,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />
          </div>

          {/* Execution Results Panel */}
          <div className="p-4 bg-slate-950/80 max-h-[220px] overflow-y-auto space-y-3">
            {sampleResult && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-slate-300">Sample Test Execution Results:</span>
                  <span className={sampleResult.overall_status === "ACCEPTED" ? "text-emerald-400" : "text-rose-400"}>
                    {sampleResult.overall_status} ({sampleResult.passed_test_cases}/{sampleResult.total_test_cases} Passed)
                  </span>
                </div>
                {sampleResult.error_output && (
                  <pre className="p-3 bg-rose-950/40 border border-rose-800/40 text-rose-300 text-[11px] rounded-lg font-mono whitespace-pre-wrap">
                    {sampleResult.error_output}
                  </pre>
                )}
              </div>
            )}

            {problemSubmitResult && (
              <div className="p-4 rounded-xl border bg-slate-900 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-slate-200">Problem Submission Result:</span>
                  <span className={problemSubmitResult.status === "ACCEPTED" ? "text-emerald-400" : "text-amber-400"}>
                    {problemSubmitResult.status} (+{problemSubmitResult.score_obtained} pts)
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Passed {problemSubmitResult.passed_test_cases} of {problemSubmitResult.total_test_cases} evaluation test cases.
                </p>
              </div>
            )}

            {!sampleResult && !problemSubmitResult && (
              <p className="text-[11px] text-slate-500 font-mono">Run samples or submit solution to see evaluation outputs.</p>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Finish Assessment?</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to finish and submit your {session.title}? Once submitted, your scores will be finalized and your session will close.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowSubmitModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleFinalSubmitTest}
                disabled={submittingTest}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl flex items-center gap-2"
              >
                {submittingTest ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <span>Confirm & Submit</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
