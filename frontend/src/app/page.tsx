import SystemHealth from "@/components/SystemHealth";
import { Target, Code2, ShieldCheck, Sparkles, Building2 } from "lucide-react";

const TARGET_COMPANIES = [
  { name: "TCS", category: "Service & Product" },
  { name: "Cognizant", category: "Service & Product" },
  { name: "Infosys", category: "Service & Product" },
  { name: "Accenture", category: "Service & Product" },
  { name: "Wipro", category: "Service & Product" },
  { name: "Deloitte", category: "Consulting & Product" },
  { name: "Capgemini", category: "Service & Product" },
  { name: "Zoho", category: "Product Recruiters" },
  { name: "Amazon", category: "Top Tech" },
  { name: "Microsoft", category: "Top Tech" },
];

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-between p-6 md:p-12 max-w-6xl mx-auto space-y-12">
      {/* Header */}
      <header className="w-full flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/20">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-white">
              CodeTarget <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 ml-2">v0.1 Foundation</span>
            </h1>
            <p className="text-xs text-slate-400">Company-Specific Coding-Round Preparation Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <ShieldCheck className="w-4 h-4 text-emerald-400" /> Phase 1 Architecture Ready
        </div>
      </header>

      {/* Hero Intro */}
      <section className="text-center space-y-4 max-w-2xl">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-indigo-500/10 to-purple-500/10 text-indigo-300 border border-indigo-500/20">
          <Sparkles className="w-3.5 h-3.5" /> Placement & Recruitment Preparation
        </div>
        <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
          Target the Exact Coding Rounds of Top Recruiters
        </h2>
        <p className="text-sm text-slate-400 leading-relaxed">
          Stop practicing generic LeetCode problems blindly. CodeTarget tailors your practice, progressive hints, timed mock assessments, and readiness metrics specifically to your target companies.
        </p>
      </section>

      {/* Target Companies Grid */}
      <section className="w-full space-y-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-300">
          <Building2 className="w-4 h-4 text-indigo-400" /> Initial Recruiter Focus Dataset
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {TARGET_COMPANIES.map((company) => (
            <div
              key={company.name}
              className="glass-card rounded-xl p-3 flex flex-col items-center justify-center text-center space-y-1 hover:border-indigo-500/40 transition-all cursor-default group"
            >
              <span className="text-sm font-bold text-slate-200 group-hover:text-indigo-400 transition-colors">
                {company.name}
              </span>
              <span className="text-[10px] text-slate-500">{company.category}</span>
            </div>
          ))}
        </div>
      </section>

      {/* System Health Diagnostics Component */}
      <section className="w-full flex justify-center pt-4">
        <SystemHealth />
      </section>

      {/* Footer */}
      <footer className="w-full text-center text-xs text-slate-500 border-t border-slate-800/60 pt-6">
        CodeTarget Platform Architecture &copy; {new Date().getFullYear()} — Production Foundation
      </footer>
    </main>
  );
}
