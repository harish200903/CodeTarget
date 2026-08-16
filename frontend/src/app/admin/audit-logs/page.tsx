"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { fetchAdminAuditLogs, AuditLogItem } from "@/lib/api";
import { History, ShieldAlert } from "lucide-react";

export default function AdminAuditLogsPage() {
  const { accessToken } = useAuth();
  const [data, setData] = useState<{ items: AuditLogItem[]; total: number; page: number; total_pages: number }>({
    items: [],
    total: 0,
    page: 1,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  async function loadLogs() {
    if (!accessToken) return;
    try {
      setLoading(true);
      const res = await fetchAdminAuditLogs(accessToken, page, 20);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLogs();
  }, [accessToken, page]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Administrator Audit Log Inspector</h1>
        <p className="text-xs text-slate-400 mt-1">Immutable audit trail of administrator content-management operations.</p>
      </div>

      {loading ? (
        <div className="h-64 bg-slate-900 animate-pulse rounded-2xl" />
      ) : (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Timestamp</th>
                <th className="p-4">Action</th>
                <th className="p-4">Resource Type</th>
                <th className="p-4">Resource ID</th>
                <th className="p-4">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono text-[11px]">
              {data.items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500">
                    No audit events recorded.
                  </td>
                </tr>
              ) : (
                data.items.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-4 text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-indigo-300">
                        {log.action}
                      </span>
                    </td>
                    <td className="p-4 text-slate-300 font-semibold">{log.resource_type}</td>
                    <td className="p-4 text-slate-400">{log.resource_id || "—"}</td>
                    <td className="p-4 text-slate-400 max-w-xs truncate">
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination Footer */}
          {data.total_pages > 1 && (
            <div className="p-4 bg-slate-800/40 border-t border-slate-800 flex items-center justify-between text-xs font-sans">
              <span className="text-slate-400">
                Page {data.page} of {data.total_pages} ({data.total} total audit logs)
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
