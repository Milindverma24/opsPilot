"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Globe, 
  ArrowLeft, 
  RefreshCw, 
  ExternalLink, 
  ShieldAlert, 
  CheckCircle2, 
  FileText,
  Hash,
  Clock
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function WebsiteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [site, setSite] = useState<any>(null);
  const [pages, setPages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [siteRes, pagesRes] = await Promise.all([
        api.websites.get(id),
        api.websites.pages(id)
      ]);
      setSite(siteRes.data);
      setPages(pagesRes.data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchData();
  }, [id]);

  const handleTriggerCrawl = async () => {
    try {
      setCrawling(true);
      await api.websites.crawl(id);
      await fetchData();
    } catch (err: any) {
      alert("Crawl trigger failed: " + err.message);
    } finally {
      setCrawling(false);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="py-16 text-center text-xs text-slate-400">Loading website pages...</div>
      </AppLayout>
    );
  }

  if (!site) {
    return (
      <AppLayout>
        <div className="py-16 text-center">
          <p className="text-xs text-rose-600 font-semibold">Website not found</p>
          <Link href="/data-sources/websites" className="text-xs text-blue-600 underline mt-2 block">
            Return to Websites List
          </Link>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <Link
            href="/data-sources/websites"
            className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Websites</span>
          </Link>
          <button
            onClick={handleTriggerCrawl}
            disabled={crawling}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${crawling ? "animate-spin" : ""}`} />
            <span>{crawling ? "Crawling Target..." : "Re-Crawl Target"}</span>
          </button>
        </div>

        {/* Target Header Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Globe className="w-5 h-5 text-blue-600" />
                <h1 className="text-lg font-bold text-slate-900">{site.name}</h1>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                  site.crawl_status === "COMPLETED"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-blue-50 text-blue-700 border-blue-200"
                }`}>
                  {site.crawl_status}
                </span>
              </div>
              <a 
                href={site.url} 
                target="_blank" 
                rel="noreferrer" 
                className="text-xs text-blue-600 hover:underline flex items-center gap-1 font-mono"
              >
                <span>{site.url}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <div className="flex items-center gap-6 text-xs text-slate-600 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Indexed</span>
                <span className="font-bold text-slate-800 text-sm">{pages.length} Pages</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Allowed Domains</span>
                <span className="font-mono text-slate-700 font-semibold">{site.allowed_domains?.join(", ") || "Self"}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Robots.txt</span>
                <span className="text-emerald-600 font-bold">Respected</span>
              </div>
            </div>
          </div>
        </div>

        {/* Indexed Pages Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Normalized Indexed Pages ({pages.length})
            </h3>
            <span className="text-[11px] text-slate-400">Deterministic SHA-256 change detection active</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                  <th className="py-3 px-4">Page Title & Path</th>
                  <th className="py-3 px-4">HTTP Status</th>
                  <th className="py-3 px-4">Security Classification</th>
                  <th className="py-3 px-4">Content Hash (SHA-256)</th>
                  <th className="py-3 px-4">Last Crawled</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pages.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{p.title || "Untitled Page"}</div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">{p.url}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {p.http_status} OK
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        {p.security_classification || "UNTRUSTED_EXTERNAL_DATA"}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                        {p.content_hash?.slice(0, 16)}...
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 text-[11px]">
                      {p.last_crawled_at ? new Date(p.last_crawled_at).toLocaleString() : "Recently"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
