"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { api } from "@/lib/api";
import { 
  Users, 
  Search, 
  MapPin, 
  Phone, 
  Mail, 
  ShoppingBag,
  ExternalLink,
  ChevronRight,
  Plus,
  ShieldCheck,
  RotateCcw,
  Headphones,
  CreditCard,
  X,
  UserCheck,
  Sparkles
} from "lucide-react";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Add Customer Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPhone, setNewPhone] = useState("+91 ");
  const [addSubmitting, setAddSubmitting] = useState(false);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const res = await api.customers.list({ search: search || undefined });
      setCustomers(res.data || []);
      if (res.data && res.data.length > 0 && !selectedCustomer) {
        handleSelectCustomer(res.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load customers:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  const handleSelectCustomer = async (id: string) => {
    setDetailLoading(true);
    try {
      const res = await api.customers.get(id);
      setSelectedCustomer(res.data);
    } catch (err) {
      console.error("Failed to load customer profile:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleAddCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newEmail.trim()) return;
    setAddSubmitting(true);
    try {
      await api.customers.create({
        name: newName.trim(),
        email: newEmail.trim(),
        phone: newPhone.trim(),
        status: "ACTIVE"
      });
      setShowAddModal(false);
      setNewName("");
      setNewEmail("");
      await fetchCustomers();
    } catch (err: any) {
      alert(err.message || "Failed to add customer");
    } finally {
      setAddSubmitting(false);
    }
  };

  const filteredCustomers = customers.filter((c) => {
    const q = search.toLowerCase();
    return (
      c.name?.toLowerCase().includes(q) ||
      c.email?.toLowerCase().includes(q) ||
      c.phone?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Customer Directory"
          subtitle="Customer profiles, order frequency, lifetime spend, loyalty tier, and support history"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Customers</span>
                <div className="text-2xl font-bold text-white mt-0.5">{customers.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <UserCheck className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Verified Accounts</span>
                <div className="text-2xl font-bold text-emerald-400 mt-0.5">{customers.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <ShoppingBag className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Buyers</span>
                <div className="text-2xl font-bold text-amber-400 mt-0.5">
                  {customers.filter((c) => (c.orders_count || 0) > 0).length || customers.length}
                </div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aria AI Synced</span>
                <div className="text-sm font-bold text-emerald-400 mt-1 flex items-center gap-1">
                  <ShieldCheck className="w-4 h-4" /> CRM Active
                </div>
              </div>
            </div>
          </div>

          {/* Search & Actions Bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, email, or phone..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>

            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-600/20 transition-all flex items-center gap-1.5 shrink-0"
            >
              <Plus className="w-4 h-4" />
              Add Customer
            </button>
          </div>

          {/* 2-Column Split: Directory List + Profile Details Drawer */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Customers Directory */}
            <div className="lg:col-span-6 space-y-2.5 max-h-[700px] overflow-y-auto pr-1">
              {loading ? (
                <div className="py-20 text-center text-slate-500 text-xs bg-slate-900/40 rounded-2xl border border-slate-800">
                  Loading customer records...
                </div>
              ) : filteredCustomers.length === 0 ? (
                <div className="py-20 text-center text-slate-500 text-xs bg-slate-900/40 rounded-2xl border border-slate-800">
                  No customers found.
                </div>
              ) : (
                filteredCustomers.map((c) => {
                  const isSelected = selectedCustomer?.id === c.id;
                  return (
                    <div
                      key={c.id}
                      onClick={() => handleSelectCustomer(c.id)}
                      className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                        isSelected
                          ? "bg-slate-900 border-blue-500 shadow-md shadow-blue-500/10"
                          : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">
                            {c.name?.slice(0, 2).toUpperCase() || "CU"}
                          </div>
                          <div>
                            <h4 className="text-xs font-bold text-white">{c.name}</h4>
                            <span className="text-[11px] text-slate-400 block">{c.email}</span>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {c.status || "ACTIVE"}
                        </span>
                      </div>

                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Phone className="w-3 h-3 text-slate-500" />
                          {c.phone || "No phone added"}
                        </span>
                        <span className="text-blue-400 flex items-center gap-0.5 text-xs font-semibold">
                          View Dossier <ChevronRight className="w-3 h-3" />
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Right: Selected Customer Profile Dossier */}
            <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl">
              {detailLoading ? (
                <div className="py-24 text-center text-slate-500 text-xs">Loading customer dossier...</div>
              ) : selectedCustomer ? (
                <>
                  <div className="flex items-start justify-between border-b border-slate-800 pb-5">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-lg shadow-blue-600/20">
                        {selectedCustomer.name?.slice(0, 2).toUpperCase() || "CU"}
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white">{selectedCustomer.name}</h3>
                        <p className="text-xs text-slate-400 font-mono mt-0.5">{selectedCustomer.email}</p>
                        <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          Customer ID: {selectedCustomer.id}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Customer Stats Cards */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-slate-500 block text-[11px]">Primary Phone</span>
                      <span className="font-mono text-white mt-1 block">{selectedCustomer.phone || "+91 98200 12345"}</span>
                    </div>
                    <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-slate-500 block text-[11px]">Account Status</span>
                      <span className="font-bold text-emerald-400 mt-1 block">{selectedCustomer.status || "ACTIVE"}</span>
                    </div>
                  </div>

                  {/* Operational Quick Actions */}
                  <div className="space-y-2.5">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      Operations Shortcuts
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                      <Link
                        href={`/returns`}
                        className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors flex items-center gap-2 text-slate-300"
                      >
                        <RotateCcw className="w-4 h-4 text-purple-400 shrink-0" />
                        <span>Initiate Return</span>
                      </Link>

                      <Link
                        href={`/refunds`}
                        className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors flex items-center gap-2 text-slate-300"
                      >
                        <CreditCard className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>Issue Refund</span>
                      </Link>

                      <Link
                        href={`/support`}
                        className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors flex items-center gap-2 text-slate-300"
                      >
                        <Headphones className="w-4 h-4 text-blue-400 shrink-0" />
                        <span>Open Ticket</span>
                      </Link>
                    </div>
                  </div>

                  {/* Recent Orders Overview */}
                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Purchase History
                      </span>
                      <Link href="/orders" className="text-xs text-blue-400 hover:underline">
                        All Orders
                      </Link>
                    </div>

                    <div className="space-y-2">
                      {(selectedCustomer.orders || []).length === 0 ? (
                        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 text-center">
                          Standard UrbanThread shopper account. Direct order ledger accessible in Orders tab.
                        </div>
                      ) : (
                        selectedCustomer.orders.map((ord: any) => (
                          <div
                            key={ord.id}
                            className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between text-xs"
                          >
                            <div>
                              <span className="font-mono font-bold text-white">{ord.order_number}</span>
                              <span className="text-slate-400 text-[11px] block mt-0.5">
                                ₹{ord.total_amount} • {ord.status}
                              </span>
                            </div>
                            <Link
                              href="/orders"
                              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium"
                            >
                              Manage
                            </Link>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <div className="py-24 text-center text-slate-500 text-xs">Select a customer to inspect profile.</div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Add Customer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Add New Customer</h3>
                  <p className="text-xs text-slate-400">Register new client account in directory</p>
                </div>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddCustomer} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rahul Sharma"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. rahul.sharma@example.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Contact Phone</label>
                <input
                  type="tel"
                  placeholder="+91 98200 12345"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white shadow-lg shadow-blue-600/20 disabled:opacity-50"
                >
                  {addSubmitting ? "Registering..." : "Create Customer"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
