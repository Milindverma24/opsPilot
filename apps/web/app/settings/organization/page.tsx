"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { Building2, Globe, Mail, MapPin, Clock, Coins, Save, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function OrganizationSettingsPage() {
  const [org, setOrg] = useState<any>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrg = async () => {
      try {
        const data = await api.organization.get();
        setOrg(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchOrg();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.organization.update({
        industry: org.industry,
        description: org.description,
        website_url: org.website_url,
        email_domain: org.email_domain
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Organization Profile & Multi-Tenant Context"
          subtitle="Tenant boundary metadata, corporate domain restrictions, and operational defaults"
        />

        <main className="p-6 space-y-6 max-w-4xl mx-auto w-full">
          {saved && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Organization profile updated successfully!</span>
            </div>
          )}

          {org && (
            <form onSubmit={handleSave} className="space-y-6">
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
                <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                  <Building2 className="w-5 h-5 text-blue-600" />
                  <h3 className="text-sm font-bold text-slate-900">Tenant Identity</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Company Name</label>
                    <input
                      type="text"
                      disabled
                      value={org.name || ""}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 font-medium cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Tenant Slug (Identifier)</label>
                    <input
                      type="text"
                      disabled
                      value={org.slug || ""}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 font-mono cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Industry</label>
                    <input
                      type="text"
                      value={org.industry || ""}
                      onChange={(e) => setOrg({ ...org, industry: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Corporate Email Domain</label>
                    <input
                      type="text"
                      value={org.email_domain || ""}
                      onChange={(e) => setOrg({ ...org, email_domain: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Corporate Website URL</label>
                    <input
                      type="text"
                      value={org.website_url || ""}
                      onChange={(e) => setOrg({ ...org, website_url: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Timezone</label>
                    <input
                      type="text"
                      disabled
                      value={org.timezone || "Asia/Kolkata"}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 font-medium cursor-not-allowed"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1 text-xs">Description</label>
                  <textarea
                    rows={3}
                    value={org.description || ""}
                    onChange={(e) => setOrg({ ...org, description: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-sm transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    <span>Save Organization Changes</span>
                  </button>
                </div>
              </div>
            </form>
          )}
        </main>
      </div>
    </div>
  );
}
