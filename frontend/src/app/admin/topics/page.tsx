"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { fetchAdminTopics, createAdminTopic, updateAdminTopic } from "@/lib/api";
import { Tag, Plus, Edit2 } from "lucide-react";

export default function AdminTopicsPage() {
  const { accessToken } = useAuth();
  const [topics, setTopics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    if (!accessToken) return;
    try {
      setLoading(true);
      const data = await fetchAdminTopics(accessToken);
      setTopics(data);
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
    setEditId(null);
    setName("");
    setSlug("");
    setDescription("");
    setError(null);
    setShowModal(true);
  }

  function handleOpenEdit(t: any) {
    setEditId(t.id);
    setName(t.name);
    setSlug(t.slug);
    setDescription(t.description || "");
    setError(null);
    setShowModal(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    setError(null);

    try {
      if (editId) {
        await updateAdminTopic(accessToken, editId, { name, slug, description });
      } else {
        await createAdminTopic(accessToken, { name, slug, description });
      }
      setShowModal(false);
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to save topic");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">DSA Topic Management</h1>
          <p className="text-xs text-slate-400 mt-1">Manage data structures and algorithm categories.</p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Topic</span>
        </button>
      </div>

      {loading ? (
        <div className="h-48 bg-slate-900 animate-pulse rounded-2xl" />
      ) : (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Topic Name</th>
                <th className="p-4">Slug</th>
                <th className="p-4">Associated Problems</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {topics.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 font-semibold text-white flex items-center gap-2">
                    <Tag className="w-4 h-4 text-blue-400" />
                    <span>{t.name}</span>
                  </td>
                  <td className="p-4 font-mono text-slate-400 text-[11px]">{t.slug}</td>
                  <td className="p-4 font-mono font-bold text-slate-200">{t.problem_count}</td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => handleOpenEdit(t)}
                      className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md space-y-5 shadow-2xl">
            <h2 className="text-sm font-bold text-white">
              {editId ? "Edit DSA Topic" : "Add DSA Topic"}
            </h2>

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Topic Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (!editId) setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, "-"));
                  }}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. Graph Algorithms"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Slug</label>
                <input
                  type="text"
                  required
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
                  placeholder="e.g. graph-algorithms"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  placeholder="Topic summary..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
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
                  Save Topic
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
