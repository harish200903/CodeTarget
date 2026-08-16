"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  fetchAdminDashboardSummary,
  fetchAdminAuditLogs,
  AdminDashboardSummary,
  AuditLogItem,
} from "@/lib/api";
import {
  Building2, Tag, FileCode2, Award, FileSpreadsheet, Lightbulb, History, Plus
} from "lucide-react";

export default function AdminDashboardPage() {
  const { accessToken } = useAuth();
  const [summary, setSummary] = useState<AdminDashboardSummary | null>(null);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      if (!accessToken) return;
      try {
        setLoading(true);
        const [sumData, logData] = await Promise.all([
          fetchAdminDashboardSummary(accessToken),
          fetchAdminAuditLogs(accessToken, 1, 5),
        ]);
        setSummary(sumData);
        setLogs(logData.items);
      } catch (err) {
        console.error("Failed to load admin summary:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [accessToken]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-slate-800 animate-pulse rounded-lg" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-slate-800 animate-pulse rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  const statCards = [
    { label: "Target Companies", count: summary?.companies_count || 0, icon: Building2, color: "text-amber-400 bg-amber-500/10" },
    { label: "DSA Topics", count: summary?.topics_count || 0, icon: Tag, color: "text-blue-400 bg-blue-500/10" },
    { label: "Total Problems", count: summary?.problems_count || 0, icon: FileCode2, color: "text-emerald-400 bg-emerald-500/10" },
    { label: "Active Problems", count: summary?.active_problems_count || 0, icon: FileCode2, color: "text-indigo-400 bg-indigo-500/10" },
    { label: "Mock Test Specs", count: summary?.mock_tests_count || 0, icon: Award, color: "text-purple-400 bg-purple-500/10" },
    { label: "Total Test Cases", count: summary?.total_test_cases || 0, icon: FileSpreadsheet, color: "text-cyan-400 bg-cyan-500/10" },
    { label: "Total Static Hints", count: summary?.total_hints || 0, icon: Lightbulb, color: "text-pink-400 bg-pink-500/10" },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Content Management Overview</h1>
          <p className="text-xs text-slate-400 mt-1">Platform metric summary and recent administrator audit events.</p>
        </div>

        <div className="flex gap-2">
          <Link
            href="/admin/problems/editor"
            className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Problem</span>
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{card.label}</span>
                <div className={`p-2 rounded-xl ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <p className="text-2xl font-black text-white tracking-tight">{card.count}</p>
            </div>
          );
        })}
      </div>

      {/* Recent Audit Logs */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-bold text-white">Recent Audit Events</h2>
          </div>
          <Link href="/admin/audit-logs" className="text-xs text-indigo-400 hover:underline font-semibold">
            View All Logs →
          </Link>
        </div>

        <div className="divide-y divide-slate-800/80">
          {logs.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No audit logs recorded yet.</p>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="py-3 flex items-center justify-between text-xs">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-indigo-300">
                      {log.action}
                    </span>
                    <span className="text-slate-300 font-semibold">{log.resource_type}</span>
                    {log.resource_id && <span className="text-slate-500 font-mono text-[10px]">({log.resource_id.slice(0, 8)})</span>}
                  </div>
                  <p className="text-slate-400 text-[11px] font-mono">
                    {JSON.stringify(log.details)}
                  </p>
                </div>
                <div className="text-right text-[10px] text-slate-500 font-mono">
                  {new Date(log.timestamp).toLocaleString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
