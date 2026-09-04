"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { ShieldCheck, Lock, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function RolesSettingsPage() {
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const data = await api.roles.list();
        setRoles(data.roles || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchRoles();
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Role-Based Access Control (RBAC)"
          subtitle="System governance, role permission definitions, and authorization boundaries"
        />

        <main className="p-6 space-y-6 max-w-6xl mx-auto w-full">
          <div className="grid grid-cols-1 gap-4">
            {roles.map((r) => (
              <div key={r.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-blue-600" />
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">{r.name}</h3>
                      <p className="text-xs text-slate-500">{r.description}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    r.is_system ? "bg-purple-50 text-purple-700 border border-purple-200" : "bg-blue-50 text-blue-700 border border-blue-200"
                  }`}>
                    {r.is_system ? "SYSTEM LOCKED" : "CUSTOM"}
                  </span>
                </div>

                <div>
                  <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Assigned Permissions ({r.permissions?.length || 0})
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {r.permissions?.map((p: string) => (
                      <span
                        key={p}
                        className="px-2 py-0.5 rounded-md font-mono text-[10px] bg-slate-100 text-slate-700 border border-slate-200"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
