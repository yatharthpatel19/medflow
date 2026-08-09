import React, { useState } from 'react'
import { Cpu, Activity, CheckCircle, AlertTriangle, Clock } from 'lucide-react'

export default function App() {
  const [metrics] = useState({
    total_workers: 8,
    active_workers: 2,
    queue_size: 14,
    total_completed: 1284,
    total_failed: 2,
    avg_execution_ms: 1.4,
    throughput_per_min: 420,
    engine_mode: 'C++ Hardware Native Pool (std::thread)'
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="max-w-7xl mx-auto flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-sky-400">MedFlow Platform</h1>
          <p className="text-slate-400 text-sm mt-1">Intelligent Diagnostic Center & C++ Parallel Processing Engine</p>
        </div>
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-mono text-emerald-400">ENGINE ONLINE</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-bold text-sky-400 flex items-center gap-2">
                <Cpu className="w-6 h-6 text-sky-400 animate-pulse" /> Custom C++ Thread Pool Monitor
              </h2>
              <p className="text-xs text-slate-400 mt-1">Engine Mode: <span className="text-emerald-400 font-mono">{metrics.engine_mode}</span></p>
            </div>
            <span className="px-3 py-1 bg-sky-950 text-sky-300 border border-sky-800 rounded-full text-xs font-semibold">
              {metrics.active_workers} / {metrics.total_workers} Workers Active
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs text-slate-400 flex items-center gap-1"><Clock className="w-3.5 h-3.5"/> Queue Size</span>
              <p className="text-2xl font-black text-amber-400 mt-1">{metrics.queue_size}</p>
            </div>
            <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs text-slate-400 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5"/> Completed</span>
              <p className="text-2xl font-black text-emerald-400 mt-1">{metrics.total_completed.toLocaleString()}</p>
            </div>
            <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs text-slate-400 flex items-center gap-1"><Activity className="w-3.5 h-3.5"/> Avg Exec Time</span>
              <p className="text-2xl font-black text-sky-400 mt-1">{metrics.avg_execution_ms} <span className="text-xs font-normal">ms</span></p>
            </div>
            <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/50">
              <span className="text-xs text-slate-400 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5"/> Failed Jobs</span>
              <p className="text-2xl font-black text-rose-400 mt-1">{metrics.total_failed}</p>
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Worker Thread Status</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2">
              {Array.from({ length: metrics.total_workers }).map((_, idx) => {
                const isBusy = idx < metrics.active_workers;
                return (
                  <div 
                    key={idx} 
                    className={`p-3 rounded-md border flex flex-col items-center justify-center transition-all ${
                      isBusy 
                        ? 'bg-emerald-950/40 border-emerald-500 text-emerald-300 animate-pulse' 
                        : 'bg-slate-800/40 border-slate-700 text-slate-500'
                    }`}
                  >
                    <span className="text-[10px] font-mono">Worker #{idx + 1}</span>
                    <span className="text-[11px] font-bold mt-1">{isBusy ? 'BUSY' : 'IDLE'}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
