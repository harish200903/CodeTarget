"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { fetchCompanies, completeOnboarding, Company } from "@/lib/api";
import {
  Target, Building2, Search, Check, Star, Code2, Gauge, Clock,
  ArrowRight, ArrowLeft, Loader2, AlertCircle, Sparkles
} from "lucide-react";

export default function OnboardingPage() {
  const { user, accessToken, loading, updateUser } = useAuth();
  const router = useRouter();

  // Onboarding Form State
  const [currentStep, setCurrentStep] = useState(1);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<string[]>([]);
  const [primaryCompanyId, setPrimaryCompanyId] = useState<string | null>(null);
  const [preferredLanguage, setPreferredLanguage] = useState<"python" | "java" | "cpp">("python");
  const [skillLevel, setSkillLevel] = useState<"BEGINNER" | "INTERMEDIATE" | "ADVANCED">("INTERMEDIATE");
  const [dailyGoalMinutes, setDailyGoalMinutes] = useState<number>(45);

  const [loadingCompanies, setLoadingCompanies] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Route Protection Guard
  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/login");
      } else if (user.onboarding_completed) {
        router.push("/dashboard");
      }
    }
  }, [user, loading, router]);

  // Load Companies
  useEffect(() => {
    async function load() {
      try {
        const list = await fetchCompanies();
        setCompanies(list);
      } catch (err: any) {
        setError("Failed to load company list.");
      } finally {
        setLoadingCompanies(false);
      }
    }
    load();
  }, []);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0F17]">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  // Filter Companies
  const filteredCompanies = companies.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.tier.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleCompanySelection = (id: string) => {
    if (selectedCompanyIds.includes(id)) {
      const next = selectedCompanyIds.filter((item) => item !== id);
      setSelectedCompanyIds(next);
      if (primaryCompanyId === id) {
        setPrimaryCompanyId(next.length > 0 ? next[0] : null);
      }
    } else {
      const next = [...selectedCompanyIds, id];
      setSelectedCompanyIds(next);
      if (!primaryCompanyId) {
        setPrimaryCompanyId(id);
      }
    }
  };

  const handleNextStep = () => {
    setError(null);
    if (currentStep === 1) {
      if (selectedCompanyIds.length === 0) {
        setError("Please select at least one target company.");
        return;
      }
      if (!primaryCompanyId) {
        setError("Please choose a primary target company.");
        return;
      }
    }
    setCurrentStep((prev) => Math.min(prev + 1, 4));
  };

  const handlePrevStep = () => {
    setError(null);
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmitOnboarding = async () => {
    setError(null);
    if (!accessToken || selectedCompanyIds.length === 0 || !primaryCompanyId) return;

    setSubmitting(true);
    try {
      const updatedUser = await completeOnboarding(accessToken, {
        target_company_ids: selectedCompanyIds,
        primary_company_id: primaryCompanyId,
        preferred_language: preferredLanguage,
        skill_level: skillLevel,
        daily_goal_minutes: dailyGoalMinutes,
      });
      updateUser(updatedUser);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to submit onboarding. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-between p-6 md:p-12 bg-[#0B0F17] max-w-4xl mx-auto space-y-8">
      {/* Top Header & Progress */}
      <header className="w-full space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-md">
              <Target className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-sm font-bold text-white">CodeTarget Setup</span>
              <p className="text-[11px] text-slate-400">Personalizing your target preparation environment</p>
            </div>
          </div>
          <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
            Step {currentStep} of 4
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-indigo-500 to-violet-500 h-full transition-all duration-300"
            style={{ width: `${(currentStep / 4) * 100}%` }}
          />
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="w-full flex items-center gap-2 text-xs p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: Target Companies */}
      {currentStep === 1 && (
        <div className="w-full space-y-6">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-white">Which companies are you preparing for?</h2>
            <p className="text-xs text-slate-400">
              Choose the companies you're actually applying to or preparing for. Select one as your primary target.
            </p>
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search companies (TCS, Cognizant, Amazon...)"
              className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Company Cards Grid */}
          {loadingCompanies ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Loading recruiter database...
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-h-[380px] overflow-y-auto pr-1">
              {filteredCompanies.map((company) => {
                const isSelected = selectedCompanyIds.includes(company.id);
                const isPrimary = primaryCompanyId === company.id;

                return (
                  <div
                    key={company.id}
                    onClick={() => toggleCompanySelection(company.id)}
                    className={`rounded-xl p-4 cursor-pointer transition-all border flex flex-col justify-between space-y-3 ${
                      isSelected
                        ? isPrimary
                          ? "bg-indigo-950/40 border-indigo-500 ring-1 ring-indigo-500 shadow-lg shadow-indigo-500/10"
                          : "bg-slate-900/90 border-slate-700"
                        : "glass-card hover:border-slate-700 opacity-70 hover:opacity-100"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Building2 className={`w-4 h-4 ${isSelected ? "text-indigo-400" : "text-slate-500"}`} />
                        <span className="text-sm font-bold text-slate-100">{company.name}</span>
                      </div>
                      {isSelected && (
                        <div className="p-1 rounded-full bg-emerald-500/20 text-emerald-400">
                          <Check className="w-3.5 h-3.5" />
                        </div>
                      )}
                    </div>

                    <p className="text-[11px] text-slate-400 line-clamp-2">{company.description}</p>

                    {/* Primary Target Toggle Button */}
                    {isSelected && (
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                        <span className="text-[10px] text-slate-400">{company.tier}</span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setPrimaryCompanyId(company.id);
                          }}
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 transition-colors ${
                            isPrimary
                              ? "bg-indigo-500 text-white"
                              : "bg-slate-800 text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          <Star className="w-3 h-3 fill-current" />
                          {isPrimary ? "Primary Target" : "Make Primary"}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Selected Summary Badge */}
          {selectedCompanyIds.length > 0 && (
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 flex items-center justify-between">
              <span>
                Selected: <strong className="text-white">{selectedCompanyIds.length} companies</strong>
              </span>
              {primaryCompanyId && (
                <span className="text-indigo-400 flex items-center gap-1 font-semibold">
                  <Star className="w-3.5 h-3.5 fill-indigo-400" />
                  Primary: {companies.find((c) => c.id === primaryCompanyId)?.name}
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* STEP 2: Preferred Language */}
      {currentStep === 2 && (
        <div className="w-full space-y-6">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-white">Which programming language do you prefer?</h2>
            <p className="text-xs text-slate-400">
              Select your primary language for code editor starter code and test execution.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { id: "python", name: "Python 3", desc: "Clean syntax, fast problem-solving, ideal for DSA speed.", icon: "🐍" },
              { id: "java", name: "Java", desc: "Strong typing, standard OOP recruiter interviews.", icon: "☕" },
              { id: "cpp", name: "C++", desc: "High execution speed, Standard Template Library (STL).", icon: "⚡" },
            ].map((lang) => {
              const isSelected = preferredLanguage === lang.id;
              return (
                <div
                  key={lang.id}
                  onClick={() => setPreferredLanguage(lang.id as any)}
                  className={`rounded-2xl p-6 cursor-pointer transition-all border flex flex-col justify-between space-y-4 ${
                    isSelected
                      ? "bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/10"
                      : "glass-card hover:border-slate-700 opacity-70 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-3xl">{lang.icon}</span>
                    {isSelected && (
                      <div className="p-1 rounded-full bg-indigo-500 text-white">
                        <Check className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">{lang.name}</h3>
                    <p className="text-xs text-slate-400 mt-1">{lang.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* STEP 3: Skill Level */}
      {currentStep === 3 && (
        <div className="w-full space-y-6">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-white">How would you describe your coding level?</h2>
            <p className="text-xs text-slate-400">
              This helps tailor initial recommendations and problem difficulty.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                id: "BEGINNER",
                title: "Beginner",
                desc: "I'm still learning programming and basic problem solving.",
                badge: "Foundational DSA",
              },
              {
                id: "INTERMEDIATE",
                title: "Intermediate",
                desc: "I'm comfortable with basic DSA and coding problems.",
                badge: "Standard Placement Level",
              },
              {
                id: "ADVANCED",
                title: "Advanced",
                desc: "I'm comfortable solving medium/hard DSA problems.",
                badge: "Top Tech Product Level",
              },
            ].map((level) => {
              const isSelected = skillLevel === level.id;
              return (
                <div
                  key={level.id}
                  onClick={() => setSkillLevel(level.id as any)}
                  className={`rounded-2xl p-6 cursor-pointer transition-all border flex flex-col justify-between space-y-4 ${
                    isSelected
                      ? "bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/10"
                      : "glass-card hover:border-slate-700 opacity-70 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300">
                      {level.badge}
                    </span>
                    {isSelected && (
                      <div className="p-1 rounded-full bg-indigo-500 text-white">
                        <Check className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">{level.title}</h3>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{level.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* STEP 4: Daily Practice Goal */}
      {currentStep === 4 && (
        <div className="w-full space-y-6">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-white">How much time do you want to practice each day?</h2>
            <p className="text-xs text-slate-400">
              Set a consistent practice streak goal tailored to your schedule.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[15, 30, 45, 60, 90].map((mins) => {
              const isSelected = dailyGoalMinutes === mins;
              return (
                <div
                  key={mins}
                  onClick={() => setDailyGoalMinutes(mins)}
                  className={`rounded-2xl p-5 cursor-pointer transition-all border text-center space-y-2 flex flex-col items-center justify-center ${
                    isSelected
                      ? "bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/10"
                      : "glass-card hover:border-slate-700 opacity-70 hover:opacity-100"
                  }`}
                >
                  <Clock className={`w-5 h-5 ${isSelected ? "text-indigo-400" : "text-slate-500"}`} />
                  <span className="text-lg font-extrabold text-white">{mins} mins</span>
                  <span className="text-[10px] text-slate-400">Daily Target</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Navigation Footer */}
      <footer className="w-full flex items-center justify-between border-t border-slate-800/80 pt-6">
        {currentStep > 1 ? (
          <button
            type="button"
            onClick={handlePrevStep}
            disabled={submitting}
            className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold text-xs transition-colors flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        ) : (
          <div />
        )}

        {currentStep < 4 ? (
          <button
            type="button"
            onClick={handleNextStep}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/20 transition-colors flex items-center gap-2"
          >
            Continue <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmitOnboarding}
            disabled={submitting}
            className="px-8 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs shadow-xl shadow-indigo-600/20 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Saving Selections...
              </>
            ) : (
              <>
                Complete Onboarding <Sparkles className="w-4 h-4 text-amber-300" />
              </>
            )}
          </button>
        )}
      </footer>
    </div>
  );
}
