"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { fetchAdminProblems, deactivateAdminProblem } from "@/lib/api";
import { FileCode2, Plus, Edit2, Trash2, Search, Filter } from "lucide-react";

export default function AdminProblemsPage() {
  const { accessToken } = useAuth();
  const [data, setData] = useState<{ items: any[]; total: number; page: number; total_pages: number }>({
    items: [],
    total: 0,
    page: 1,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [page, setPage] = useState(1);

  async function loadProblems() {
    if (!accessToken) return;
    try {
      setLoading(true);
      const res = await fetchAdminProblems(accessToken, { page, page_size: 15, search, difficulty });
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProblems();
  }, [accessToken, page, difficulty]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    loadProblems();
  }

  async function handleDeactivate(id: string, title: string) {
    if (!accessToken) return;
    if (!confirm(`Are you sure you want to soft-deactivate problem "${title}"?\nHistorical user submissions will remain intact.`)) {
      return;
    }
    try {
      await deactivateAdminProblem(accessToken, id);
      loadProblems();
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Problem Catalog Management</h1>
          <p className="text-xs text-slate-400 mt-1">Create, edit, classify, and manage platform coding problems.</p>
        </div>

        <Link
          href="/admin/problems/editor"
          className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Problem</span>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search problem title..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button type="submit" className="px-4 py-2 bg-slate-800 text-slate-200 rounded-xl text-xs font-semibold hover:bg-slate-700">
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={difficulty}
            onChange={(e) => {
              setDifficulty(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Difficulties</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
        </div>
      </div>

      {/* Problems Table */}
      {loading ? (
        <div className="h-64 bg-slate-900 animate-pulse rounded-2xl" />
      ) : (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Title</th>
                <th className="p-4">Difficulty</th>
                <th className="p-4">Companies</th>
                <th className="p-4">Topics</th>
                <th className="p-4">Test Cases / Hints</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {data.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No problems found matching criteria.
                  </td>
                </tr>
              ) : (
                data.items.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-4 font-semibold text-white">
                      <div>{p.title}</div>
                      <span className="text-[10px] font-mono text-slate-500">{p.slug}</span>
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
                          p.difficulty === "EASY"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : p.difficulty === "MEDIUM"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        {p.difficulty}
                      </span>
                    </td>
                    <td className="p-4 text-slate-400 text-[11px]">
                      {p.companies?.slice(0, 2).join(", ") || "—"}
                      {p.companies?.length > 2 && ` (+${p.companies.length - 2})`}
                    </td>
                    <td className="p-4 text-slate-400 text-[11px]">
                      {p.topics?.slice(0, 2).join(", ") || "—"}
                      {p.topics?.length > 2 && ` (+${p.topics.length - 2})`}
                    </td>
                    <td className="p-4 font-mono text-slate-300">
                      {p.test_cases_count} test cases / {p.hints_count} hints
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          p.is_active
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {p.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="p-4 text-right space-x-1">
                      <Link
                        href={`/admin/problems/editor?id=${p.id}`}
                        className="p-1.5 inline-block hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </Link>
                      {p.is_active && (
                        <button
                          onClick={() => handleDeactivate(p.id, p.title)}
                          className="p-1.5 hover:bg-rose-950 text-slate-400 hover:text-rose-400 rounded-lg transition-colors"
                          title="Soft Deactivate Problem"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination Footer */}
          {data.total_pages > 1 && (
            <div className="p-4 bg-slate-800/40 border-t border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-400">
                Page {data.page} of {data.total_pages} ({data.total} total problems)
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-slate-300 font-semibold"
                >
                  Previous
                </button>
                <button
                  disabled={page >= data.total_pages}
                  onClick={() => setPage(page + 1)}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-slate-300 font-semibold"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
