"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  Users, 
  Search, 
  MapPin, 
  Phone, 
  Mail, 
  ShoppingBag,
  ExternalLink,
  ChevronRight
} from "lucide-react";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const res = await api.customers.list({ search: search || undefined });
      setCustomers(res.data || []);
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

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
          <Users className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Customer Directory</h1>
          <p className="text-sm text-slate-400">Customer purchase history, delivery addresses, and support interactions.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer Directory Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search customers by name or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchCustomers()}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <button 
              onClick={fetchCustomers}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold"
            >
              Search
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Customer</th>
                  <th className="px-5 py-3.5">Contact</th>
                  <th className="px-5 py-3.5 text-center">Orders</th>
                  <th className="px-5 py-3.5 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr><td colSpan={4} className="px-6 py-10 text-center text-slate-400">Loading directory...</td></tr>
                ) : customers.map((c) => (
                  <tr 
                    key={c.id}
                    onClick={() => handleSelectCustomer(c.id)}
                    className={`cursor-pointer hover:bg-slate-800/50 transition-colors ${selectedCustomer?.id === c.id ? 'bg-blue-950/30 border-l-2 border-blue-500' : ''}`}
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-white">{c.name}</div>
                      <div className="text-xs font-mono text-slate-400">{c.customer_number}</div>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-300">
                      <div>{c.email}</div>
                      <div className="text-slate-500">{c.phone}</div>
                    </td>
                    <td className="px-5 py-3.5 text-center font-bold text-white">
                      {c.orders_count}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Customer Profile & Address Book */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
          {detailLoading ? (
            <div className="py-20 text-center text-slate-400 text-sm">Loading customer profile...</div>
          ) : selectedCustomer ? (
            <div className="space-y-4">
              <div>
                <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-800 rounded text-slate-400">
                  {selectedCustomer.customer_number}
                </span>
                <h2 className="text-lg font-bold text-white mt-1">{selectedCustomer.name}</h2>
                <div className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                  <Mail className="w-3 h-3 text-slate-500" /> {selectedCustomer.email}
                </div>
                <div className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                  <Phone className="w-3 h-3 text-slate-500" /> {selectedCustomer.phone}
                </div>
              </div>

              {/* Saved Shipping Addresses */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-emerald-400" /> Delivery Addresses
                </h3>
                <div className="space-y-2">
                  {selectedCustomer.addresses?.map((a: any) => (
                    <div key={a.id} className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 text-xs text-slate-300">
                      <div className="font-semibold text-white">{a.name} ({a.type})</div>
                      <div>{a.line1}</div>
                      <div>{a.city}, {a.state} - {a.postal_code}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Orders */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <ShoppingBag className="w-3.5 h-3.5 text-blue-400" /> Order History
                </h3>
                <div className="space-y-1.5 max-h-56 overflow-y-auto">
                  {selectedCustomer.orders?.map((o: any) => (
                    <div key={o.id} className="p-2.5 bg-slate-950/70 rounded-lg border border-slate-800 flex justify-between items-center text-xs">
                      <div>
                        <span className="font-mono font-semibold text-white">{o.order_number}</span>
                        <div className="text-[10px] text-slate-400">{o.status}</div>
                      </div>
                      <div className="text-right font-bold text-white">
                        ₹{o.total_amount}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-24 text-center text-slate-400 text-sm">
              <Users className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              Select a customer to view address book and past purchase orders.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
