"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Globe, 
  Plus, 
  RefreshCw, 
  ExternalLink, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  FileCode,
  ShieldCheck,
  Search,
  ArrowRight
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function WebsitesPage() {
  const [websites, setWebsites] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [crawlingId, setCrawlingId] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [url, setUrl] = useState("https://urbanthread.local");
  const [description, setDescription] = useState("");
  const [maxPages, setMaxPages] = useState(50);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchWebsites = async () => {
    try {
      setLoading(true);
      const res = await api.websites.list();
      setWebsites(res.data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWebsites();
  }, []);

  const handleTriggerCrawl = async (id: string) => {
    try {
      setCrawlingId(id);
      await api.websites.crawl(id);
      await fetchWebsites();
    } catch (err: any) {
      alert("Crawl failed: " + err.message);
    } finally {
      setCrawlingId(null);
    }
  };

  const handleCreateWebsite = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setErrorMsg(null);
      await api.websites.create({
        name,
        url,
        description,
        max_pages: maxPages,
        respect_robots_txt: true,
      });
      setShowAddModal(false);
      setName("");
      setDescription("");
      fetchWebsites();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register website");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
              <Globe className="w-6 h-6 text-blue-600" />
              Website Ingestion & Crawlers
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Configure external storefronts and portals for SSRF-protected link discovery, HTML normalization, and change detection.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchWebsites}
              className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Target Website</span>
            </button>
          </div>
        </div>

        {/* Security Banner */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800 leading-relaxed">
            <span className="font-bold">SSRF & Ingestion Security Notice:</span> All crawled pages are treated strictly as <code className="font-mono bg-amber-100 px-1 rounded">UNTRUSTED_EXTERNAL_DATA</code>. Loops, private IP ranges (RFC 1918), and cloud metadata endpoints are deterministically blocked. Instructions found on crawled web pages will never be executed.
          </div>
        </div>

        {/* Websites Grid */}
        {loading ? (
          <div className="text-center py-16 text-slate-400 text-xs">Loading website monitors...</div>
        ) : websites.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 p-8">
            <Globe className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <div className="text-sm font-semibold text-slate-700">No websites monitored</div>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Add your enterprise e-commerce storefront to index catalog pages, customer return policies, and FAQs.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {websites.map((site) => (
              <div key={site.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow transition-shadow flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">{site.name}</h3>
                      <a 
                        href={site.url} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="text-xs text-blue-600 hover:underline flex items-center gap-1 mt-0.5"
                      >
                        <span>{site.url}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      site.crawl_status === "COMPLETED" 
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : site.crawl_status === "CRAWLING"
                        ? "bg-blue-50 text-blue-700 border-blue-200 animate-pulse"
                        : site.crawl_status === "PARTIAL"
                        ? "bg-amber-50 text-amber-700 border-amber-200"
                        : "bg-slate-50 text-slate-600 border-slate-200"
                    }`}>
                      {site.crawl_status}
                    </span>
                  </div>

                  {site.description && (
                    <p className="text-xs text-slate-500 mb-4 line-clamp-2">{site.description}</p>
                  )}

                  <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-100 text-xs mb-4">
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider block">Indexed Pages</span>
                      <span className="font-bold text-slate-800 text-sm">{site.pages_count || 0}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider block">Last Crawl</span>
                      <span className="text-slate-600 text-[11px] flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {site.last_crawled_at ? new Date(site.last_crawled_at).toLocaleDateString() : "Never"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-2 pt-2">
                  <Link
                    href={`/data-sources/websites/${site.id}`}
                    className="text-xs font-semibold text-slate-700 hover:text-blue-600 flex items-center gap-1"
                  >
                    <span>View Pages & Index</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>

                  <button
                    onClick={() => handleTriggerCrawl(site.id)}
                    disabled={crawlingId === site.id}
                    className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${crawlingId === site.id ? "animate-spin" : ""}`} />
                    <span>{crawlingId === site.id ? "Crawling..." : "Start Crawl"}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add Website Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
              <h3 className="text-base font-bold text-slate-900 mb-1">Add Target Website</h3>
              <p className="text-xs text-slate-500 mb-4">Register an enterprise website for crawl indexing.</p>

              {errorMsg && (
                <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 font-medium">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleCreateWebsite} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Website Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. UrbanThread Storefront"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Starting URL</label>
                  <input
                    type="url"
                    required
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://urbanthread.local"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium font-mono"
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">Localhost and private IP addresses are automatically blocked by SSRF defense.</span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Description (Optional)</label>
                  <textarea
                    rows={2}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Primary catalog and policies storefront"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Max Pages to Crawl</label>
                  <input
                    type="number"
                    min={1}
                    max={200}
                    value={maxPages}
                    onChange={(e) => setMaxPages(parseInt(e.target.value) || 50)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-sm transition-colors disabled:opacity-50"
                  >
                    {submitting ? "Registering..." : "Save Website"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
