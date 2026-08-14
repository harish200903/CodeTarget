"use client";

import { useEffect, useState } from "react";
import { fetchHealthStatus, HealthCheckResponse } from "@/lib/api";
import { CheckCircle2, AlertTriangle, RefreshCw, Server, Database, Cpu } from "lucide-react";

export default function SystemHealth() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const checkHealth = async () => {
    setLoading(true);
    const data = await fetchHealthStatus();
    setHealth(data);
    setLoading(false);
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const getStatusBadge = (status?: string) => {
    if (status === "healthy" || status === "ok") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" /> Healthy
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <AlertTriangle className="w-3.5 h-3.5" /> {status || "Unknown"}
      </span>
    );
  };

  return (
    <div className="glass-panel rounded-xl p-6 max-w-2xl w-full shadow-2xl space-y-6 border border-slate-800">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" /> System Status Monitor
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Phase 1 Foundation Verification & Connectivity Diagnostics
          </p>
        </div>
        <button
          onClick={checkHealth}
          disabled={loading}
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors disabled:opacity-50"
          title="Refresh Status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Backend API */}
        <div className="glass-card rounded-lg p-4 flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-300 flex items-center gap-2">
              <Server className="w-4 h-4 text-indigo-400" /> FastAPI Engine
            </span>
            {getStatusBadge(health?.status)}
          </div>
          <p className="text-xs text-slate-400">
            {health?.app_name || "CodeTarget"} ({health?.environment || "dev"})
          </p>
        </div>

        {/* Database */}
        <div className="glass-card rounded-lg p-4 flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-300 flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400" /> PostgreSQL 16
            </span>
            {getStatusBadge(health?.services?.database?.status)}
          </div>
          <p className="text-xs text-slate-400 truncate" title={health?.services?.database?.message}>
            {health?.services?.database?.message || "Checking status..."}
          </p>
        </div>

        {/* Redis */}
        <div className="glass-card rounded-lg p-4 flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-300 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-red-400" /> Redis Cache
            </span>
            {getStatusBadge(health?.services?.redis?.status)}
          </div>
          <p className="text-xs text-slate-400 truncate" title={health?.services?.redis?.message}>
            {health?.services?.redis?.message || "Checking status..."}
          </p>
        </div>
      </div>

      {health?.timestamp && (
        <div className="text-right text-[10px] text-slate-500">
          Last Check: {new Date(health.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
