"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  fetchAdminMockTests,
  fetchAdminCompanies,
  fetchAdminProblems,
  createAdminMockTest,
} from "@/lib/api";
import { Award, Plus, Building2, Clock, CheckCircle2 } from "lucide-react";

export default function AdminMockTestsPage() {
  const { accessToken } = useAuth();
  const [mocks, setMocks] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [problems, setProblems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [companyId, setCompanyId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [assignments, setAssignments] = useState<{ problem_id: string; order_index: number; weight_score: number }[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    if (!accessToken) return;
    try {
      setLoading(true);
      const [mList, cList, pList] = await Promise.all([
        fetchAdminMockTests(accessToken),
        fetchAdminCompanies(accessToken),
        fetchAdminProblems(accessToken, { page_size: 50 }),
      ]);
      setMocks(mList);
      setCompanies(cList);
      setProblems(pList.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [accessToken]);

  function handleOpenCreate() {
    setTitle("");
    setDescription("");
    setDurationMinutes(60);
    setCompanyId(companies[0]?.id || "");
    setAssignments([]);
    setError(null);
    setShowModal(true);
  }

  function handleAddProblemAssignment(probId: string) {
    if (assignments.some((a) => a.problem_id === probId)) return;
    setAssignments([
      ...assignments,
      {
        problem_id: probId,
        order_index: assignments.length + 1,
        weight_score: 30,
      },
    ]);
  }

  function handleRemoveAssignment(probId: string) {
    setAssignments(assignments.filter((a) => a.problem_id !== probId));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    if (assignments.length === 0) {
      setError("At least one problem must be assigned to the mock test.");
      return;
    }
    setError(null);

    try {
      await createAdminMockTest(accessToken, {
        company_id: companyId,
        title,
        description,
        duration_minutes: durationMinutes,
        problem_assignments: assignments,
      });
      setShowModal(false);
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create mock test spec");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Mock Test Specification Manager</h1>
          <p className="text-xs text-slate-400 mt-1">Configure timed assessment templates for target companies.</p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Mock Spec</span>
        </button>
      </div>

      {loading ? (
        <div className="h-48 bg-slate-900 animate-pulse rounded-2xl" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mocks.map((m) => (
            <div key={m.id} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  {m.company_name}
                </span>
                <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {m.duration_minutes} min
                </span>
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">{m.title}</h3>
                <p className="text-xs text-slate-400 line-clamp-2 mt-1">{m.description || "Company assessment template."}</p>
              </div>
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>{m.problem_count} assigned problems</span>
                <span className="font-bold text-emerald-400">{m.total_points} total points</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-xl space-y-5 max-h-[90vh] overflow-y-auto">
            <h2 className="text-sm font-bold text-white">Create New Mock Test Specification</h2>

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Target Company</label>
                  <select
                    value={companyId}
                    onChange={(e) => setCompanyId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white"
                  >
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Duration (Minutes)</label>
                  <input
                    type="number"
                    required
                    min={15}
                    max={180}
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(parseInt(e.target.value) || 60)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white"
                  placeholder="e.g. TCS Ninja Standard Coding Round"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white"
                  placeholder="Mock assessment description..."
                />
              </div>

              {/* Problem Picker */}
              <div className="space-y-3 pt-2">
                <label className="text-slate-300 font-bold block">Assigned Problems ({assignments.length})</label>

                {/* Assigned List */}
                <div className="space-y-2">
                  {assignments.map((a, idx) => {
                    const prob = problems.find((p) => p.id === a.problem_id);
                    return (
                      <div key={a.problem_id} className="p-3 bg-slate-800 rounded-xl flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-slate-500 font-bold">#{idx + 1}</span>
                          <span className="font-semibold text-white">{prob?.title || a.problem_id}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <label className="text-slate-400 text-[10px]">Points:</label>
                          <input
                            type="number"
                            value={a.weight_score}
                            onChange={(e) => {
                              const pts = parseInt(e.target.value) || 0;
                              setAssignments(assignments.map((item) => item.problem_id === a.problem_id ? { ...item, weight_score: pts } : item));
                            }}
                            className="w-16 px-2 py-1 rounded bg-slate-900 border border-slate-700 text-white text-center font-mono"
                          />
                          <button
                            type="button"
                            onClick={() => handleRemoveAssignment(a.problem_id)}
                            className="text-rose-400 hover:text-rose-300 font-bold px-2 py-1"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Problem Selection Box */}
                <div className="space-y-1">
                  <span className="text-slate-400 text-[11px]">Select problem to add:</span>
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        handleAddProblemAssignment(e.target.value);
                        e.target.value = "";
                      }
                    }}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white"
                  >
                    <option value="">-- Choose Problem --</option>
                    {problems.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.title} ({p.difficulty})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-md shadow-indigo-600/20"
                >
                  Save Specification
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
