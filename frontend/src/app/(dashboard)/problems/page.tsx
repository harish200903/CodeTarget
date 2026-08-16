"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  fetchProblems,
  fetchCompanies,
  fetchTopics,
  Company,
  Topic,
  ProblemListItem,
} from "@/lib/api";
import {
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Circle,
  Building2,
  Tag,
  ChevronLeft,
  ChevronRight,
  Code2,
  Sparkles,
  Bookmark,
} from "lucide-react";

export default function ProblemCatalogPage() {
  const { user, accessToken, loading: authLoading } = useAuth();
  const router = useRouter();

  const [problems, setProblems] = useState<ProblemListItem[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [search, setSearch] = useState("");
  const [selectedCompany, setSelectedCompany] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalProblems, setTotalProblems] = useState(0);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
      return;
    }

    async function initCatalogData() {
      try {
        const [compList, topList] = await Promise.all([
          fetchCompanies(),
          fetchTopics(),
        ]);
        setCompanies(compList);
        setTopics(topList);
      } catch (err) {
        console.error("Failed to load initial metadata", err);
      }
    }

    initCatalogData();
  }, [user, authLoading, router]);

  useEffect(() => {
    async function loadProblems() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchProblems(
          {
            search: search || undefined,
            company: selectedCompany || undefined,
            difficulty: selectedDifficulty || undefined,
            topic: selectedTopic || undefined,
            status: selectedStatus || undefined,
            page,
            page_size: 15,
          },
          accessToken
        );
        setProblems(data.items);
        setTotalPages(data.total_pages);
        setTotalProblems(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load problems");
      } finally {
        setLoading(false);
      }
    }

    if (accessToken || !authLoading) {
      loadProblems();
    }
  }, [
    accessToken,
    authLoading,
    search,
    selectedCompany,
    selectedDifficulty,
    selectedTopic,
    selectedStatus,
    page,
  ]);

  const getDifficultyBadge = (difficulty: string) => {
    switch (difficulty) {
      case "EASY":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Easy
          </span>
        );
      case "MEDIUM":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Medium
          </span>
        );
      case "HARD":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            Hard
          </span>
        );
      default:
        return null;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "SOLVED":
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case "ATTEMPTED":
        return <Clock className="w-5 h-5 text-amber-400" />;
      default:
        return <Circle className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <Code2 className="w-8 h-8 text-indigo-400" />
              <h1 className="text-3xl font-bold tracking-tight text-white">
                Problem Catalog
              </h1>
            </div>
            <p className="text-slate-400 text-sm">
              Practice company-specific coding questions targeted for top recruiter patterns.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800/80 hover:bg-slate-700 rounded-lg transition-colors border border-slate-700"
            >
              Dashboard
            </Link>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Search Input */}
            <div className="md:col-span-2 relative">
              <Search className="w-4 h-4 absolute left-3 top-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search problem title..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-9 pr-4 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            {/* Recruiter Company Filter */}
            <div>
              <select
                value={selectedCompany}
                onChange={(e) => {
                  setSelectedCompany(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Target Companies</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.slug}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Difficulty Filter */}
            <div>
              <select
                value={selectedDifficulty}
                onChange={(e) => {
                  setSelectedDifficulty(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Difficulties</option>
                <option value="EASY">Easy</option>
                <option value="MEDIUM">Medium</option>
                <option value="HARD">Hard</option>
              </select>
            </div>

            {/* Topic Filter */}
            <div>
              <select
                value={selectedTopic}
                onChange={(e) => {
                  setSelectedTopic(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All DSA Topics</option>
                {topics.map((t) => (
                  <option key={t.id} value={t.slug}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800/60 text-xs text-slate-400">
            <div className="flex items-center space-x-4">
              <span className="font-medium text-slate-300">
                Showing {problems.length} of {totalProblems} problems
              </span>
              {(selectedCompany || selectedDifficulty || selectedTopic || search || selectedStatus) && (
                <button
                  onClick={() => {
                    setSearch("");
                    setSelectedCompany("");
                    setSelectedDifficulty("");
                    setSelectedTopic("");
                    setSelectedStatus("");
                    setPage(1);
                  }}
                  className="text-indigo-400 hover:underline font-medium"
                >
                  Clear all filters
                </button>
              )}
            </div>

            {/* Status Tabs */}
            <div className="flex items-center space-x-1 bg-slate-800/60 p-1 rounded-lg">
              {[
                { label: "All", value: "" },
                { label: "Solved", value: "SOLVED" },
                { label: "Attempted", value: "ATTEMPTED" },
                { label: "Unattempted", value: "UNATTEMPTED" },
              ].map((s) => (
                <button
                  key={s.value}
                  onClick={() => {
                    setSelectedStatus(s.value);
                    setPage(1);
                  }}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    selectedStatus === s.value
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Problems Table */}
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Loading problems...</p>
            </div>
          ) : error ? (
            <div className="p-12 text-center text-rose-400 space-y-2">
              <p className="font-semibold">Error loading catalog</p>
              <p className="text-sm text-slate-400">{error}</p>
            </div>
          ) : problems.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <Sparkles className="w-10 h-10 text-slate-600 mx-auto" />
              <p className="text-base font-semibold text-slate-300">No problems found</p>
              <p className="text-xs">Try adjusting your filters or search query.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                    <th className="py-3.5 px-4 w-12 text-center">Status</th>
                    <th className="py-3.5 px-6">Problem Title</th>
                    <th className="py-3.5 px-4">Difficulty</th>
                    <th className="py-3.5 px-6">Topics</th>
                    <th className="py-3.5 px-6">Target Companies</th>
                    <th className="py-3.5 px-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {problems.map((p) => (
                    <tr
                      key={p.id}
                      className="hover:bg-slate-800/40 transition-colors group"
                    >
                      <td className="py-4 px-4 text-center">
                        <div className="flex justify-center">
                          {getStatusIcon(p.user_status)}
                        </div>
                      </td>
                      <td className="py-4 px-6 font-medium text-slate-100">
                        <Link
                          href={`/solve/${p.slug}`}
                          className="hover:text-indigo-400 transition-colors flex items-center space-x-2"
                        >
                          <span>{p.title}</span>
                          {p.is_bookmarked && (
                            <Bookmark className="w-3.5 h-3.5 fill-indigo-400 text-indigo-400" />
                          )}
                        </Link>
                      </td>
                      <td className="py-4 px-4">
                        {getDifficultyBadge(p.difficulty)}
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex flex-wrap gap-1.5">
                          {p.topics.slice(0, 3).map((t) => (
                            <span
                              key={t.id}
                              className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700"
                            >
                              {t.name}
                            </span>
                          ))}
                          {p.topics.length > 3 && (
                            <span className="text-xs text-slate-500">
                              +{p.topics.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex flex-wrap gap-1.5">
                          {p.companies.slice(0, 3).map((pc) => (
                            <span
                              key={pc.id}
                              className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-950/40 text-indigo-300 border border-indigo-800/40"
                            >
                              {pc.company.name}
                            </span>
                          ))}
                          {p.companies.length > 3 && (
                            <span className="text-xs text-slate-500">
                              +{p.companies.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <Link
                          href={`/solve/${p.slug}`}
                          className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors shadow"
                        >
                          Solve
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/40 text-xs text-slate-400">
              <span>
                Page {page} of {totalPages}
              </span>
              <div className="flex items-center space-x-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none transition-colors flex items-center space-x-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none transition-colors flex items-center space-x-1"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
