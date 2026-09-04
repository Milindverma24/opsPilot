"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  BadgePercent, 
  Tag, 
  Clock, 
  CheckCircle2, 
  XCircle,
  Percent,
  Plus
} from "lucide-react";

export default function CouponsPage() {
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchCoupons = async () => {
    setLoading(true);
    try {
      const res = await api.coupons.list();
      setCoupons(res.data || []);
    } catch (err) {
      console.error("Failed to load coupons:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoupons();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          <BadgePercent className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Promotional Coupons</h1>
          <p className="text-sm text-slate-400">Active voucher codes, usage caps, and checkout discounts.</p>
        </div>
      </div>

      {/* Grid of Coupons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-3 py-16 text-center text-slate-400">Loading coupons...</div>
        ) : coupons.map((c) => (
          <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-mono text-sm font-bold text-white bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800 tracking-wider">
                  {c.code}
                </span>
                <p className="text-xs text-slate-400 mt-2">{c.description}</p>
              </div>
              <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full ${c.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                {c.is_active ? "Active" : "Inactive"}
              </span>
            </div>

            <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-slate-500 block">Benefit</span>
                <span className="font-bold text-emerald-400">
                  {c.type === "PERCENTAGE" ? `${c.value}% OFF` : `₹${c.value} OFF`}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Min Order</span>
                <span className="text-slate-200">₹{c.minimum_order_value}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Max Cap</span>
                <span className="text-slate-200">{c.maximum_discount ? `₹${c.maximum_discount}` : "None"}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Usage Total</span>
                <span className="font-mono text-slate-200">{c.usage_count} {c.usage_limit ? `/ ${c.usage_limit}` : ""}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
