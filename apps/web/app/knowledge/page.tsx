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
  const [question, setQuestion] = useState("Does an invoice above 100000 require approval?");
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
      setUploadSuccess(`Indexed '${res.title}' with ${res.chunks_created} vector chunks!`);
      setTitle("");
      setContent("");
      loadDocuments();
    } catch (err: any) {
      alert("Error indexing document: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Knowledge Base & Policy RAG"
          subtitle="Grounded semantic search, SOP document chunking, and verifiable compliance citations"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Grounded Policy Q&A Sandbox */}
          <div className="bg-gradient-to-br from-blue-900 to-indigo-950 rounded-2xl p-6 text-white shadow-md space-y-4">
            <div className="flex items-center gap-2">
              <span className="p-2 bg-blue-500/20 text-blue-300 rounded-lg">
                <Sparkles className="w-5 h-5" />
              </span>
              <div>
                <h3 className="text-sm font-bold">Ask Policy RAG (Grounded AI)</h3>
                <p className="text-xs text-blue-200">
                  Semantic retrieval directly from indexed Corporate SOPs with strict citation provenance.
                </p>
              </div>
            </div>

            <form onSubmit={handleAsk} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a policy question (e.g. 'What is the approval threshold for vendor invoices?')..."
                className="flex-1 px-4 py-2.5 bg-white/10 border border-white/20 rounded-xl text-xs text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <button
                type="submit"
                disabled={asking}
                className="px-5 py-2.5 bg-blue-500 hover:bg-blue-400 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-sm transition-colors flex items-center gap-1.5 shrink-0"
              >
                {asking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                <span>Ask RAG</span>
              </button>
            </form>

            {answer && (
              <div className="p-4 bg-white/10 border border-white/20 rounded-xl space-y-2 text-xs backdrop-blur-md">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-emerald-300">
                    {answer.policy_found ? "Verified Policy Rule Found" : "Policy Not Found"}
                  </span>
                  {answer.source && (
                    <span className="text-[11px] font-mono text-blue-200 bg-white/10 px-2 py-0.5 rounded">
                      Source: {answer.source}
                    </span>
                  )}
                </div>
                <p className="text-slate-100 leading-relaxed">{answer.answer}</p>
                {answer.relevant_section && (
                  <div className="text-[11px] text-blue-200 font-mono bg-black/20 p-2 rounded border border-white/10">
                    Relevant Citation: {answer.relevant_section}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Two Columns: Indexed Docs & Semantic Search */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Indexed SOPs */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Indexed Standard Operating Procedures</h3>
                  <p className="text-xs text-slate-500">Corporate knowledge vectorized for agent policy enforcement</p>
                </div>
                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold text-[11px]">
                  {documents.length} Docs
                </span>
              </div>

              <div className="space-y-2.5 max-h-96 overflow-y-auto">
                {documents.map((doc) => (
                  <div key={doc.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">{doc.title}</span>
                      <span className="text-[10px] font-mono bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded">
                        {doc.chunks_count} chunks
                      </span>
                    </div>
                    <p className="text-slate-600 text-[11px]">{doc.content_preview}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Index New SOP Form */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Index New Corporate Policy / SOP</h3>
                <p className="text-xs text-slate-500">Documents are chunked into semantic vector embeddings</p>
              </div>

              {uploadSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-medium">
                  {uploadSuccess}
                </div>
              )}

              <form onSubmit={handleUploadSOP} className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Policy Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. IT Equipment Procurement Policy 2026"
                    required
                    className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="FINANCE_POLICY">Finance Policy</option>
                    <option value="SUPPORT_POLICY">Support & Refund Policy</option>
                    <option value="SECURITY_POLICY">Security & Compliance</option>
                    <option value="SOP">General SOP</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Policy Content</label>
                  <textarea
                    rows={4}
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Paste standard operating procedure text here..."
                    required
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-[11px]"
                  />
                </div>

                <button
                  type="submit"
                  disabled={uploading}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-sm transition-colors flex items-center justify-center gap-1.5"
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
