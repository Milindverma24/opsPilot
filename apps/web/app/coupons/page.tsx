"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { api } from "@/lib/api";
import { 
  BadgePercent, 
  Tag, 
  Clock, 
  CheckCircle2, 
  XCircle,
  Percent,
  Plus,
  Copy,
  Check,
  Search,
  Sparkles,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  ShoppingBag,
  X
} from "lucide-react";

export default function CouponsPage() {
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCode, setNewCode] = useState("");
  const [newType, setNewType] = useState<"PERCENTAGE" | "FIXED_AMOUNT">("PERCENTAGE");
  const [newValue, setNewValue] = useState("20");
  const [newMinOrder, setNewMinOrder] = useState("999");
  const [newMaxDiscount, setNewMaxDiscount] = useState("500");
  const [newUsageLimit, setNewUsageLimit] = useState("1000");
  const [newDescription, setNewDescription] = useState("Seasonal festive promotion for apparel");
  const [createSubmitting, setCreateSubmitting] = useState(false);

  // Sandbox Validator
  const [sandboxCode, setSandboxCode] = useState("URBAN10");
  const [sandboxAmount, setSandboxAmount] = useState("2500");
  const [sandboxResult, setSandboxResult] = useState<any | null>(null);
  const [sandboxValidating, setSandboxValidating] = useState(false);

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

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleCreateCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCode.trim()) return;
    setCreateSubmitting(true);
    try {
      await api.coupons.create({
        code: newCode.toUpperCase().trim(),
        type: newType,
        value: parseFloat(newValue) || 0,
        minimum_order_value: parseFloat(newMinOrder) || 0,
        maximum_discount: newMaxDiscount ? parseFloat(newMaxDiscount) : undefined,
        usage_limit: newUsageLimit ? parseInt(newUsageLimit) : undefined,
        description: newDescription,
        is_active: true
      });
      setShowCreateModal(false);
      setNewCode("");
      await fetchCoupons();
    } catch (err: any) {
      alert(err.message || "Failed to create coupon");
    } finally {
      setCreateSubmitting(false);
    }
  };

  const handleRunValidation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sandboxCode.trim()) return;
    setSandboxValidating(true);
    setSandboxResult(null);
    try {
      const res = await api.coupons.validate({
        code: sandboxCode.toUpperCase().trim(),
        subtotal: parseFloat(sandboxAmount) || 1000
      });
      setSandboxResult(res);
    } catch (err: any) {
      setSandboxResult({
        valid: false,
        discount_amount: 0,
        reason: err.message || "Invalid coupon or order criteria unmet"
      });
    } finally {
      setSandboxValidating(false);
    }
  };

  const filteredCoupons = coupons.filter((c) => {
    const matchesFilter = 
      filter === "ALL" ? true :
      filter === "ACTIVE" ? c.is_active :
      !c.is_active;
    const matchesSearch = 
      c.code?.toLowerCase().includes(search.toLowerCase()) ||
      c.description?.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const totalRedemptions = coupons.reduce((sum, c) => sum + (c.usage_count || 0), 0);
  const activeCount = coupons.filter((c) => c.is_active).length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Promotional Coupons & Vouchers"
          subtitle="Voucher campaigns, percentage/flat discounts, usage caps, and checkout validation sandbox"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metrics Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <BadgePercent className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Codes</span>
                <div className="text-2xl font-bold text-white mt-0.5">{activeCount}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Redemptions</span>
                <div className="text-2xl font-bold text-white mt-0.5">{totalRedemptions}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
                <Percent className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Catalog Vouchers</span>
                <div className="text-2xl font-bold text-white mt-0.5">{coupons.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">RAG Integrated</span>
                <div className="text-sm font-bold text-emerald-400 mt-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Policy Aware
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Sandbox & Header Controls */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Live Coupon Validation Sandbox */}
            <div className="lg:col-span-1 bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Validation Sandbox</h3>
                  <p className="text-[11px] text-slate-400">Test promo rules against order baskets</p>
                </div>
              </div>

              <form onSubmit={handleRunValidation} className="space-y-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Coupon Code</label>
                  <input
                    type="text"
                    value={sandboxCode}
                    onChange={(e) => setSandboxCode(e.target.value)}
                    placeholder="e.g. URBAN10"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono uppercase focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Cart Subtotal (₹)</label>
                  <input
                    type="number"
                    value={sandboxAmount}
                    onChange={(e) => setSandboxAmount(e.target.value)}
                    placeholder="2500"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={sandboxValidating}
                  className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {sandboxValidating ? "Evaluating Rules..." : "Validate Promo Code"}
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </form>

              {sandboxResult && (
                <div className={`p-3.5 rounded-xl border text-xs space-y-2 animate-in fade-in duration-200 ${
                  sandboxResult.valid !== false 
                    ? "bg-emerald-950/40 border-emerald-500/30 text-emerald-200" 
                    : "bg-rose-950/40 border-rose-500/30 text-rose-200"
                }`}>
                  <div className="flex items-center gap-2 font-bold">
                    {sandboxResult.valid !== false ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    )}
                    <span>{sandboxResult.valid !== false ? "Coupon Applied Successfully!" : "Coupon Rejected"}</span>
                  </div>

                  {sandboxResult.valid !== false ? (
                    <div className="space-y-1 text-[11px] pt-1 border-t border-emerald-500/20">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Discount Savings:</span>
                        <span className="font-bold text-emerald-300">₹{sandboxResult.discount_amount}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Final Payable:</span>
                        <span className="font-bold text-white">
                          ₹{Math.max(0, (parseFloat(sandboxAmount) || 0) - (sandboxResult.discount_amount || 0))}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-[11px] text-rose-300">{sandboxResult.reason || "Minimum order criteria not met or code expired."}</p>
                  )}
                </div>
              )}
            </div>

            {/* Coupons List Header & Filter */}
            <div className="lg:col-span-2 flex flex-col justify-between space-y-4">
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="relative w-full sm:w-72">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search promo codes..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                    <button
                      onClick={() => setFilter("ALL")}
                      className={`px-3 py-1.5 rounded-lg font-medium transition-all ${filter === "ALL" ? "bg-slate-800 text-white shadow-sm" : "text-slate-400 hover:text-white"}`}
                    >
                      All ({coupons.length})
                    </button>
                    <button
                      onClick={() => setFilter("ACTIVE")}
                      className={`px-3 py-1.5 rounded-lg font-medium transition-all ${filter === "ACTIVE" ? "bg-emerald-500/20 text-emerald-400 font-bold" : "text-slate-400 hover:text-white"}`}
                    >
                      Active
                    </button>
                    <button
                      onClick={() => setFilter("INACTIVE")}
                      className={`px-3 py-1.5 rounded-lg font-medium transition-all ${filter === "INACTIVE" ? "bg-rose-500/20 text-rose-400 font-bold" : "text-slate-400 hover:text-white"}`}
                    >
                      Inactive
                    </button>
                  </div>

                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-md shadow-emerald-600/20 transition-all flex items-center gap-1.5 shrink-0"
                  >
                    <Plus className="w-4 h-4" />
                    Create Coupon
                  </button>
                </div>
              </div>

              {/* Coupons Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
                {loading ? (
                  <div className="col-span-2 py-16 text-center text-slate-500 text-xs">
                    Loading promotional vouchers...
                  </div>
                ) : filteredCoupons.length === 0 ? (
                  <div className="col-span-2 py-16 text-center text-slate-500 text-xs bg-slate-900/40 rounded-2xl border border-slate-800/80">
                    No vouchers matched your filter criteria.
                  </div>
                ) : (
                  filteredCoupons.map((c) => (
                    <div
                      key={c.id}
                      className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 relative overflow-hidden group hover:border-slate-700 transition-all hover:shadow-lg hover:shadow-emerald-500/5"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-white bg-slate-950 px-3 py-1 rounded-lg border border-slate-800 tracking-wider">
                            {c.code}
                          </span>
                          <button
                            onClick={() => handleCopy(c.code)}
                            title="Copy voucher code"
                            className="p-1 rounded-md text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                          >
                            {copiedCode === c.code ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                        <span
                          className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${
                            c.is_active
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          }`}
                        >
                          {c.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>

                      <p className="text-xs text-slate-400 line-clamp-2 min-h-[32px]">
                        {c.description || "Applies discount across eligible apparel."}
                      </p>

                      <div className="pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2.5 text-xs">
                        <div>
                          <span className="text-[11px] text-slate-500 block">Benefit</span>
                          <span className="font-bold text-emerald-400">
                            {c.type === "PERCENTAGE" ? `${c.value}% OFF` : `₹${c.value} OFF`}
                          </span>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 block">Min Order</span>
                          <span className="font-semibold text-slate-200">₹{c.minimum_order_value || 0}</span>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 block">Max Cap</span>
                          <span className="font-semibold text-slate-200">
                            {c.maximum_discount ? `₹${c.maximum_discount}` : "Uncapped"}
                          </span>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 block">Usage Total</span>
                          <span className="font-mono text-slate-300">
                            {c.usage_count || 0} {c.usage_limit ? `/ ${c.usage_limit}` : ""}
                          </span>
                        </div>
                      </div>

                      <div className="pt-2 flex items-center justify-between">
                        <button
                          onClick={() => {
                            setSandboxCode(c.code);
                            window.scrollTo({ top: 0, behavior: "smooth" });
                          }}
                          className="text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
                        >
                          Test in Sandbox
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Create Coupon Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <BadgePercent className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Create Voucher Campaign</h3>
                  <p className="text-xs text-slate-400">Launch a new promotional discount</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCoupon} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Coupon Code *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. FLASH30"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono uppercase focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Type</label>
                  <select
                    value={newType}
                    onChange={(e: any) => setNewType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="PERCENTAGE">Percentage (%)</option>
                    <option value="FIXED_AMOUNT">Fixed Amount (₹)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Value {newType === "PERCENTAGE" ? "(%)" : "(₹)"} *
                  </label>
                  <input
                    type="number"
                    required
                    value={newValue}
                    onChange={(e) => setNewValue(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Min Order (₹)</label>
                  <input
                    type="number"
                    value={newMinOrder}
                    onChange={(e) => setNewMinOrder(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Max Cap (₹)</label>
                  <input
                    type="number"
                    value={newMaxDiscount}
                    onChange={(e) => setNewMaxDiscount(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Usage Limit</label>
                <input
                  type="number"
                  value={newUsageLimit}
                  onChange={(e) => setNewUsageLimit(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Campaign Description</label>
                <textarea
                  rows={2}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-emerald-500 resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-lg shadow-emerald-600/20 disabled:opacity-50"
                >
                  {createSubmitting ? "Deploying..." : "Launch Voucher"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
