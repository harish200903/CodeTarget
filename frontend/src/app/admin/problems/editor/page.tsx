"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  fetchAdminCompanies,
  fetchAdminTopics,
  fetchAdminProblemDetail,
  createAdminProblem,
  updateAdminProblem,
  createAdminTestCase,
  deleteAdminTestCase,
  createAdminHint,
  deleteAdminHint,
} from "@/lib/api";
import {
  FileCode2, ArrowLeft, Save, Building2, Tag, FileSpreadsheet, Lightbulb, Plus, Trash2, CheckCircle2
} from "lucide-react";

export default function AdminProblemEditorPage() {
  const { accessToken } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const problemId = searchParams.get("id");

  const [activeTab, setActiveTab] = useState<"details" | "classification" | "test_cases" | "hints">("details");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [allCompanies, setAllCompanies] = useState<any[]>([]);
  const [allTopics, setAllTopics] = useState<any[]>([]);

  // Problem Details
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [difficulty, setDifficulty] = useState("EASY");
  const [category, setCategory] = useState("Arrays");
  const [isActive, setIsActive] = useState(true);
  const [descriptionMarkdown, setDescriptionMarkdown] = useState("");
  const [constraintsText, setConstraintsText] = useState("");
  const [starterPython, setStarterPython] = useState("def solution():\n    pass");
  const [starterJava, setStarterJava] = useState("class Solution {\n    public void solve() {}\n}");
  const [starterCpp, setStarterCpp] = useState("class Solution {\npublic:\n    void solve() {}\n};");

  // Classifications
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  // Test Cases & Hints (for existing problem)
  const [testCases, setTestCases] = useState<any[]>([]);
  const [hints, setHints] = useState<any[]>([]);

  // Test Case Modal Form
  const [tcInput, setTcInput] = useState("");
  const [tcExpected, setTcExpected] = useState("");
  const [tcIsSample, setTcIsSample] = useState(false);

  // Hint Form
  const [hintStep, setHintStep] = useState(1);
  const [hintTitle, setHintTitle] = useState("");
  const [hintContent, setHintContent] = useState("");

  useEffect(() => {
    async function loadEditorData() {
      if (!accessToken) return;
      try {
        setLoading(true);
        const [comps, tops] = await Promise.all([
          fetchAdminCompanies(accessToken),
          fetchAdminTopics(accessToken),
        ]);
        setAllCompanies(comps);
        setAllTopics(tops);

        if (problemId) {
          const detail = await fetchAdminProblemDetail(accessToken, problemId);
          setTitle(detail.title);
          setSlug(detail.slug);
          setDifficulty(detail.difficulty);
          setCategory(detail.category);
          setIsActive(detail.is_active);
          setDescriptionMarkdown(detail.description_markdown);
          setConstraintsText(detail.constraints_text || "");
          setStarterPython(detail.starter_code?.python || "");
          setStarterJava(detail.starter_code?.java || "");
          setStarterCpp(detail.starter_code?.cpp || "");
          setSelectedCompanies(detail.company_ids || []);
          setSelectedTopics(detail.topic_ids || []);
          setTestCases(detail.test_cases || []);
          setHints(detail.hints || []);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadEditorData();
  }, [accessToken, problemId]);

  async function handleSaveDetails(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    setSuccess(null);

    const body = {
      title,
      slug,
      difficulty,
      category,
      is_active: isActive,
      description_markdown: descriptionMarkdown,
      constraints_text: constraintsText,
      starter_code: {
        python: starterPython,
        java: starterJava,
        cpp: starterCpp,
      },
      company_ids: selectedCompanies,
      topic_ids: selectedTopics,
    };

    try {
      if (problemId) {
        await updateAdminProblem(accessToken, problemId, body);
        setSuccess("Problem updated successfully.");
      } else {
        const res = await createAdminProblem(accessToken, body);
        setSuccess("Problem created successfully!");
        router.push(`/admin/problems/editor?id=${res.id}`);
      }
    } catch (err: any) {
      setError(err.message || "Failed to save problem");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddTestCase(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !problemId) return;
    try {
      await createAdminTestCase(accessToken, problemId, {
        input_data: tcInput,
        expected_output: tcExpected,
        is_sample: tcIsSample,
      });
      setTcInput("");
      setTcExpected("");
      setTcIsSample(false);
      const detail = await fetchAdminProblemDetail(accessToken, problemId);
      setTestCases(detail.test_cases || []);
    } catch (err: any) {
      setError(err.message || "Failed to add test case");
    }
  }

  async function handleDeleteTestCase(tcId: string) {
    if (!accessToken || !problemId) return;
    try {
      await deleteAdminTestCase(accessToken, tcId);
      const detail = await fetchAdminProblemDetail(accessToken, problemId);
      setTestCases(detail.test_cases || []);
    } catch (err: any) {
      setError(err.message || "Failed to delete test case");
    }
  }

  async function handleAddHint(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !problemId) return;
    try {
      await createAdminHint(accessToken, problemId, {
        step_number: hintStep,
        title: hintTitle,
        content_markdown: hintContent,
      });
      setHintTitle("");
      setHintContent("");
      setHintStep((prev) => prev + 1);
      const detail = await fetchAdminProblemDetail(accessToken, problemId);
      setHints(detail.hints || []);
    } catch (err: any) {
      setError(err.message || "Failed to add hint");
    }
  }

  async function handleDeleteHint(hintId: string) {
    if (!accessToken || !problemId) return;
    try {
      await deleteAdminHint(accessToken, hintId);
      const detail = await fetchAdminProblemDetail(accessToken, problemId);
      setHints(detail.hints || []);
    } catch (err: any) {
      setError(err.message || "Failed to delete hint");
    }
  }

  if (loading) {
    return <div className="h-64 bg-slate-900 animate-pulse rounded-2xl" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/problems")}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              {problemId ? `Edit Problem: ${title}` : "Create New Coding Problem"}
            </h1>
            <p className="text-xs text-slate-400">Configure specifications, classification, test cases, and static hints.</p>
          </div>
        </div>

        <button
          onClick={handleSaveDetails}
          disabled={saving}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{saving ? "Saving..." : "Save Problem"}</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-semibold">
          {error}
        </div>
      )}

      {success && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{success}</span>
        </div>
      )}

      {/* Editor Tabs */}
      <div className="flex border-b border-slate-800 text-xs font-semibold">
        {[
          { id: "details", label: "1. Problem Details", icon: FileCode2 },
          { id: "classification", label: "2. Companies & Topics", icon: Building2 },
          { id: "test_cases", label: `3. Test Cases (${testCases.length})`, icon: FileSpreadsheet, disabled: !problemId },
          { id: "hints", label: `4. Curated Hints (${hints.length})`, icon: Lightbulb, disabled: !problemId },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              disabled={tab.disabled}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 border-b-2 flex items-center gap-2 transition-colors disabled:opacity-30 ${
                activeTab === tab.id
                  ? "border-indigo-500 text-indigo-400 font-bold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: Problem Details */}
      {activeTab === "details" && (
        <form onSubmit={handleSaveDetails} className="space-y-5 text-xs bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Problem Title *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  if (!problemId) setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, "-"));
                }}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                placeholder="e.g. Two Sum"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Slug *</label>
              <input
                type="text"
                required
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
                placeholder="e.g. two-sum"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Difficulty Level *</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="EASY">Easy</option>
                <option value="MEDIUM">Medium</option>
                <option value="HARD">Hard</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Category / Pattern *</label>
              <input
                type="text"
                required
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                placeholder="e.g. Arrays & Hashing"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-slate-400 font-medium">Problem Description (Markdown) *</label>
            <textarea
              rows={6}
              required
              value={descriptionMarkdown}
              onChange={(e) => setDescriptionMarkdown(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 font-mono text-xs"
              placeholder="Given an array of integers nums and an integer target..."
            />
          </div>

          <div className="space-y-1">
            <label className="text-slate-400 font-medium">Constraints Text</label>
            <input
              type="text"
              value={constraintsText}
              onChange={(e) => setConstraintsText(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
              placeholder="e.g. 2 <= nums.length <= 10^4"
            />
          </div>

          <div className="space-y-3 pt-2">
            <h3 className="text-slate-300 font-bold">Starter Code Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-mono text-[11px]">Python Starter Code</label>
                <textarea
                  rows={4}
                  value={starterPython}
                  onChange={(e) => setStarterPython(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-mono text-[11px]">Java Starter Code</label>
                <textarea
                  rows={4}
                  value={starterJava}
                  onChange={(e) => setStarterJava(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-mono text-[11px]">C++ Starter Code</label>
                <textarea
                  rows={4}
                  value={starterCpp}
                  onChange={(e) => setStarterCpp(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
                />
              </div>
            </div>
          </div>
        </form>
      )}

      {/* TAB 2: Classifications */}
      {activeTab === "classification" && (
        <div className="space-y-6 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 text-xs">
          <div className="space-y-3">
            <h3 className="text-slate-200 font-bold flex items-center gap-2">
              <Building2 className="w-4 h-4 text-amber-400" />
              <span>Target Companies</span>
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {allCompanies.map((c) => {
                const isSelected = selectedCompanies.includes(c.id);
                return (
                  <button
                    type="button"
                    key={c.id}
                    onClick={() => {
                      if (isSelected) {
                        setSelectedCompanies(selectedCompanies.filter((id) => id !== c.id));
                      } else {
                        setSelectedCompanies([...selectedCompanies, c.id]);
                      }
                    }}
                    className={`px-3 py-2 rounded-xl border text-left font-semibold transition-all ${
                      isSelected
                        ? "bg-amber-500/10 border-amber-500/40 text-amber-300"
                        : "bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {c.name}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-3 pt-4 border-t border-slate-800">
            <h3 className="text-slate-200 font-bold flex items-center gap-2">
              <Tag className="w-4 h-4 text-blue-400" />
              <span>DSA Topics</span>
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {allTopics.map((t) => {
                const isSelected = selectedTopics.includes(t.id);
                return (
                  <button
                    type="button"
                    key={t.id}
                    onClick={() => {
                      if (isSelected) {
                        setSelectedTopics(selectedTopics.filter((id) => id !== t.id));
                      } else {
                        setSelectedTopics([...selectedTopics, t.id]);
                      }
                    }}
                    className={`px-3 py-2 rounded-xl border text-left font-semibold transition-all ${
                      isSelected
                        ? "bg-blue-500/10 border-blue-500/40 text-blue-300"
                        : "bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {t.name}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Test Cases */}
      {activeTab === "test_cases" && problemId && (
        <div className="space-y-6">
          <form onSubmit={handleAddTestCase} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4 text-xs">
            <h3 className="text-slate-200 font-bold">Add Test Case</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Input Data</label>
                <textarea
                  rows={2}
                  required
                  value={tcInput}
                  onChange={(e) => setTcInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono text-[11px]"
                  placeholder="[2, 7, 11, 15]\n9"
                />
              </div>
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Expected Output</label>
                <textarea
                  rows={2}
                  required
                  value={tcExpected}
                  onChange={(e) => setTcExpected(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono text-[11px]"
                  placeholder="[0, 1]"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-slate-300 font-semibold cursor-pointer">
                <input
                  type="checkbox"
                  checked={tcIsSample}
                  onChange={(e) => setTcIsSample(e.target.checked)}
                  className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Public Sample Test Case (Visible to candidate)</span>
              </label>

              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl flex items-center gap-2"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Test Case</span>
              </button>
            </div>
          </form>

          {/* Test Case List */}
          <div className="space-y-3">
            {testCases.map((tc, idx) => (
              <div key={tc.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-start justify-between gap-4 text-xs">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-200">Test Case #{idx + 1}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${tc.is_sample ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "bg-slate-800 text-slate-400"}`}>
                      {tc.is_sample ? "Public Sample" : "Hidden Test Case"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 font-mono text-[11px]">
                    <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-slate-300">
                      <span className="text-slate-500 block text-[10px] mb-1">INPUT</span>
                      {tc.input_data}
                    </div>
                    <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-emerald-400">
                      <span className="text-slate-500 block text-[10px] mb-1">EXPECTED OUTPUT</span>
                      {tc.expected_output}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteTestCase(tc.id)}
                  className="p-2 hover:bg-rose-950 text-slate-500 hover:text-rose-400 rounded-xl transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: Curated Hints */}
      {activeTab === "hints" && problemId && (
        <div className="space-y-6">
          <form onSubmit={handleAddHint} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4 text-xs">
            <h3 className="text-slate-200 font-bold">Add Curated Static Hint</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Step Number</label>
                <input
                  type="number"
                  required
                  min={1}
                  value={hintStep}
                  onChange={(e) => setHintStep(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono"
                />
              </div>

              <div className="space-y-1 md:col-span-2">
                <label className="text-slate-400 font-medium">Hint Title</label>
                <input
                  type="text"
                  required
                  value={hintTitle}
                  onChange={(e) => setHintTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white"
                  placeholder="e.g. Consider using a Hash Map"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Hint Explanation (Markdown)</label>
              <textarea
                rows={3}
                required
                value={hintContent}
                onChange={(e) => setHintContent(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono text-[11px]"
                placeholder="Store values in a hash map as you iterate..."
              />
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl flex items-center gap-2"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Static Hint</span>
              </button>
            </div>
          </form>

          {/* Hint List */}
          <div className="space-y-3">
            {hints.map((h) => (
              <div key={h.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-start justify-between gap-4 text-xs">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      Hint #{h.step_number}
                    </span>
                    <span className="font-bold text-white">{h.title}</span>
                  </div>
                  <p className="text-slate-300 font-mono text-[11px] pt-1">{h.content_markdown}</p>
                </div>

                <button
                  onClick={() => handleDeleteHint(h.id)}
                  className="p-2 hover:bg-rose-950 text-slate-500 hover:text-rose-400 rounded-xl transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
