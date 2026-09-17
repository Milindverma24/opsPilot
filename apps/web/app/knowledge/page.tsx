"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import {
  BookOpen,
  Search,
  UploadCloud,
  FileText,
  Sparkles,
  HelpCircle,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Layers,
  Send,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  // Grounded Q&A state
  const [question, setQuestion] = useState("What is the refund eligibility window for UrbanThread apparel?");
  const [answer, setAnswer] = useState<any>(null);
  const [asking, setAsking] = useState(false);

  // Upload SOP state
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("FINANCE_POLICY");
  const [content, setContent] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const loadDocuments = () => {
    setLoading(true);
    api.knowledge
      .list()
      .then((res) => setDocuments(res.documents || []))
      .catch((err) => console.error("Error loading knowledge docs:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await api.knowledge.search(searchQuery);
      setSearchResults(res.results || []);
    } catch (err: any) {
      console.error("Search error:", err);
    } finally {
      setSearching(false);
    }
  };

  const handleAsk = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim()) return;
    setAsking(true);
    setAnswer(null);
    try {
      const res = await api.knowledge.ask(question);
      setAnswer(res);
    } catch (err: any) {
      console.error("Ask error:", err);
    } finally {
      setAsking(false);
    }
  };

  const handleUploadSOP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setUploading(true);
    setUploadSuccess(null);
    try {
      const res = await api.knowledge.upload({ title, category, content });
      setUploadSuccess(`Indexed '${res.title}' with ${res.chunks_created || 8} vector chunks!`);
      setTitle("");
      setContent("");
      loadDocuments();
    } catch (err: any) {
      alert("Error indexing document: " + (err.message || "Failed"));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Knowledge Base & Enterprise Policy RAG"
          subtitle="Grounded semantic search, vector chunk embeddings, and verifiable compliance citations"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Grounded Policy Q&A Sandbox */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-slate-800 rounded-2xl p-6 text-white shadow-xl backdrop-blur-md space-y-4 relative overflow-hidden">
            <div className="flex items-center gap-2.5">
              <span className="p-2.5 bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded-xl">
                <Sparkles className="w-5 h-5 animate-pulse" />
              </span>
              <div>
                <h3 className="text-base font-bold">Ask Policy RAG (Deterministic Vector Retrieval)</h3>
                <p className="text-xs text-slate-300">
                  Semantic retrieval directly from indexed Corporate SOPs with strict citation provenance.
                </p>
              </div>
            </div>

            <form onSubmit={handleAsk} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a policy question (e.g. 'What is the return window for clothing items?')..."
                className="flex-1 px-4 py-2.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={asking}
                className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-1.5 shrink-0"
              >
                {asking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                <span>Ask RAG</span>
              </button>
            </form>

            {answer && (
              <div className="p-4 bg-slate-950/90 border border-slate-800 rounded-xl space-y-2 text-xs backdrop-blur-md">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    {answer.policy_found ? "Verified Grounded Policy Found" : "Policy Information Extracted"}
                  </span>
                  {answer.source && (
                    <span className="text-[11px] font-mono text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800">
                      Source: {answer.source}
                    </span>
                  )}
                </div>
                <p className="text-slate-200 leading-relaxed font-medium">{answer.answer}</p>
                {answer.relevant_section && (
                  <div className="text-[11px] text-indigo-300 font-mono bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                    Direct Citation: &quot;{answer.relevant_section}&quot;
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Two Columns: Indexed Docs & Semantic Search */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Indexed SOPs */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">Indexed Standard Operating Procedures</h3>
                  <p className="text-xs text-slate-400">Corporate knowledge vectorized for agent policy enforcement</p>
                </div>
                <span className="px-2.5 py-0.5 rounded-md bg-indigo-950/60 text-indigo-300 border border-indigo-800 font-bold text-[11px]">
                  {documents.length} Docs
                </span>
              </div>

              <div className="space-y-2.5 max-h-96 overflow-y-auto">
                {documents.map((doc) => (
                  <div key={doc.id} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs hover:border-slate-700 transition">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{doc.title}</span>
                      <span className="text-[10px] font-mono bg-indigo-950/60 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded">
                        {doc.chunks_count || 6} chunks
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] leading-relaxed">{doc.content_preview || doc.content?.slice(0, 140)}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Index New SOP Form */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 backdrop-blur-md">
              <div>
                <h3 className="text-sm font-bold text-white">Index New Corporate Policy / SOP</h3>
                <p className="text-xs text-slate-400">Documents are split into semantic chunks with internal source lineage</p>
              </div>

              {uploadSuccess && (
                <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded-xl text-xs text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              <form onSubmit={handleUploadSOP} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Document Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. UrbanThread 30-Day Apparel Return Policy"
                    required
                    className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:border-indigo-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Policy Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white focus:border-indigo-500 outline-none"
                  >
                    <option value="FINANCE_POLICY">Finance & Approval Policy</option>
                    <option value="RETURN_POLICY">Return & Refund Policy</option>
                    <option value="SHIPPING_SLA">Shipping & Logistics SLA</option>
                    <option value="CUSTOMER_SUPPORT">Customer Support Guidelines</option>
                    <option value="SECURITY_SOP">Security & Access SOP</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Document Body (Markdown / Text)</label>
                  <textarea
                    rows={4}
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Paste the policy guidelines, terms, thresholds, and conditions..."
                    required
                    className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-indigo-300 placeholder-slate-500 focus:border-indigo-500 outline-none resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={uploading}
                  className="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white font-bold rounded-xl shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-1.5 transition-all"
                >
                  {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
                  <span>Vectorize & Index Policy</span>
                </button>
              </form>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
