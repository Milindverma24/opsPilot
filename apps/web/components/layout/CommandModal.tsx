"use client";

import { useState } from "react";
import { Search, Sparkles, X, ArrowRight, Loader2, FileText, AlertTriangle, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

interface CommandModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PRESET_QUERIES = [
  "Show me all invoices above ₹1 lakh",
  "Which complaints are critical?",
  "Show failed workflows",
  "Generate operations report"
];

export function CommandModal({ isOpen, onClose }: CommandModalProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleExecute = async (commandStr?: string) => {
    const q = commandStr || query;
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.command.execute(q);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to execute command");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-slate-950/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[80vh]">
        {/* Input Bar */}
        <div className="p-4 border-b border-slate-100 flex items-center gap-3 bg-slate-50/50">
          <Sparkles className="w-5 h-5 text-blue-600 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleExecute()}
            placeholder="Ask AI Command Center... (e.g. 'Show invoices above ₹1 lakh')"
            className="flex-1 bg-transparent border-none text-slate-800 text-sm font-medium focus:outline-none placeholder:text-slate-400"
            autoFocus
          />
          <button
            onClick={() => handleExecute()}
            disabled={loading || !query.trim()}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Run"}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Presets */}
        <div className="px-4 py-2 bg-slate-100/60 border-b border-slate-100 flex items-center gap-2 overflow-x-auto text-[11px]">
          <span className="text-slate-500 font-medium shrink-0">Try asking:</span>
          {PRESET_QUERIES.map((preset) => (
            <button
              key={preset}
              onClick={() => {
                setQuery(preset);
                handleExecute(preset);
              }}
              className="px-2 py-1 bg-white hover:bg-blue-50 hover:text-blue-600 border border-slate-200 rounded-md text-slate-700 whitespace-nowrap transition-colors"
            >
              {preset}
            </button>
          ))}
        </div>

        {/* Results Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="space-y-3">
              <div className="p-3 bg-blue-50/70 border border-blue-100 rounded-lg flex items-center justify-between text-xs">
                <span className="font-semibold text-blue-900">{result.summary}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-200 text-blue-800 font-bold uppercase tracking-wider">
                  Intent: {result.intent}
                </span>
              </div>

              {/* Data Table */}
              {result.data && result.data.length > 0 && (
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                      <tr>
                        {Object.keys(result.data[0]).map((key) => (
                          <th key={key} className="px-3 py-2 capitalize">
                            {key.replace(/_/g, " ")}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {result.data.map((row: any, i: number) => (
                        <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                          {Object.values(row).map((val: any, j: number) => (
                            <td key={j} className="px-3 py-2 font-mono text-[11px]">
                              {typeof val === "object" ? JSON.stringify(val) : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {!result && !loading && !error && (
            <div className="py-12 text-center text-slate-400 text-xs">
              <Sparkles className="w-8 h-8 mx-auto mb-2 text-slate-300 stroke-1" />
              <p>Type a question in natural language or click a preset chip above.</p>
              <p className="text-[11px] text-slate-400 mt-1">Queries are safely converted to structured operations without raw SQL.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
