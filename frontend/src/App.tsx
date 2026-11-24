import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Activity, ArrowUpRight, HeartPulse, Mic, ShieldCheck, Sparkles } from "lucide-react";
import { getHealth } from "./services/api";
import type { HealthResponse } from "./types/health";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getHealth().then((result) => {
      if (active) setHealth(result);
    }).catch((reason: unknown) => {
      if (active) setError(reason instanceof Error ? reason.message : "Backend unavailable");
    });
    return () => { active = false; };
  }, []);

  const online = health?.status === "healthy";

  return (
    <main className="min-h-screen overflow-hidden bg-[#f7f9f7] text-slate-900">
      <div className="pointer-events-none absolute -right-24 -top-40 h-[34rem] w-[34rem] rounded-full bg-emerald-100/70 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-48 -left-32 h-[32rem] w-[32rem] rounded-full bg-sky-100/70 blur-3xl" />
      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-6 sm:px-10 lg:px-14">
        <header className="flex items-center justify-between">
          <a className="flex items-center gap-3" href="#home" aria-label="CareLine AI home">
            <span className="grid size-11 place-items-center rounded-2xl bg-emerald-700 text-white shadow-lg shadow-emerald-900/15">
              <HeartPulse size={22} strokeWidth={2.3} />
            </span>
            <span>
              <span className="block text-lg font-semibold tracking-tight">CareLine</span>
              <span className="block text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-500">AI health assistant</span>
            </span>
          </a>
          <div className="flex items-center gap-2 rounded-full border border-white/80 bg-white/75 px-3.5 py-2 text-xs font-medium shadow-sm backdrop-blur">
            <span className={`size-2 rounded-full ${online ? "bg-emerald-500" : error ? "bg-rose-500" : "animate-pulse bg-amber-400"}`} />
            <span>{online ? "Systems online" : error ? "Backend offline" : "Connecting"}</span>
          </div>
        </header>

        <section id="home" className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.08fr_0.92fr] lg:gap-20 lg:py-20">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-emerald-900/10 bg-white/70 px-4 py-2 text-xs font-semibold text-emerald-800 shadow-sm">
              <Sparkles size={14} /> A calmer way to get care
            </div>
            <h1 className="max-w-2xl text-5xl font-semibold leading-[1.05] tracking-[-0.055em] sm:text-6xl lg:text-7xl">
              Your next step to <span className="text-emerald-700">better care</span> starts here.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
              A thoughtful voice assistant to help you find the right doctor and book an appointment, whenever you need it.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-4">
              <button type="button" disabled className="inline-flex cursor-not-allowed items-center gap-3 rounded-full bg-emerald-800 px-6 py-4 text-sm font-semibold text-white opacity-90 shadow-xl shadow-emerald-950/15" aria-label="Voice appointment booking coming soon">
                <Mic size={17} /> Voice booking <ArrowUpRight size={16} />
              </button>
              <span className="text-sm text-slate-500">Voice booking is coming soon</span>
            </div>
            <div className="mt-12 flex items-center gap-3 text-sm text-slate-500">
              <ShieldCheck size={18} className="text-emerald-700" /> Provider credentials stay on the backend
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.65, delay: 0.12 }} className="relative mx-auto w-full max-w-lg">
            <div className="absolute inset-8 rounded-[2.5rem] bg-emerald-200/60 blur-2xl" />
            <div className="relative rounded-[2rem] border border-white/80 bg-white/80 p-5 shadow-[0_30px_100px_-40px_rgba(15,75,54,0.32)] backdrop-blur-xl sm:p-7">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">CareLine assistant</p>
                  <p className="mt-2 text-xl font-semibold tracking-tight">Here when you need us</p>
                </div>
                <div className="grid size-11 place-items-center rounded-2xl bg-emerald-50 text-emerald-700"><Activity size={20} /></div>
              </div>
              <div className="mt-9 rounded-3xl bg-[#f2f7f4] p-5">
                <div className="flex items-center gap-3">
                  <div className="grid size-10 place-items-center rounded-full bg-white text-emerald-700 shadow-sm"><HeartPulse size={18} /></div>
                  <div>
                    <p className="text-sm font-semibold">A little help, a lot of care.</p>
                    <p className="mt-1 text-xs text-slate-500">Doctor appointments made simpler.</p>
                  </div>
                </div>
                <div className="mt-5 flex h-16 items-center justify-center gap-1.5" aria-hidden="true">
                  {[14, 22, 35, 19, 42, 27, 50, 31, 18, 39, 24, 45, 16, 30, 20, 38, 25, 14].map((height, index) => (
                    <span key={index} className="w-1.5 rounded-full bg-emerald-600/80" style={{ height }} />
                  ))}
                </div>
                <div className="mt-4 flex justify-between text-[11px] font-medium text-slate-400"><span>LISTENING EXPERIENCE</span><span>VOICE • CARE • EASE</span></div>
              </div>
              <div className="mt-5 flex items-center justify-between rounded-2xl border border-slate-100 px-4 py-3">
                <div className="flex items-center gap-3">
                  <span className={`size-2.5 rounded-full ${online ? "bg-emerald-500" : error ? "bg-rose-500" : "animate-pulse bg-amber-400"}`} />
                  <div><p className="text-sm font-medium">Backend connection</p><p className="text-xs text-slate-500">{health ? `${health.service} · v${health.version}` : error ?? "Checking health endpoint"}</p></div>
                </div>
                <span className="text-xs font-semibold text-slate-500">{online ? "READY" : error ? "OFFLINE" : "…"}</span>
              </div>
            </div>
            <div className="absolute -bottom-5 -left-5 rounded-2xl border border-white/80 bg-white/90 px-4 py-3 shadow-lg shadow-slate-900/5 backdrop-blur">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-700"><span className="grid size-7 place-items-center rounded-lg bg-sky-50 text-sky-700"><ShieldCheck size={15} /></span> Privacy at every step</div>
            </div>
          </motion.div>
        </section>

        <footer className="flex flex-col gap-2 border-t border-slate-200/70 py-5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <span>CareLine AI <span className="px-1 text-slate-300">·</span> A more human way to get help</span>
          <span>For appointment support only. Not for medical emergencies.</span>
        </footer>
      </div>
    </main>
  );
}
