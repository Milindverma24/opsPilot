"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { 
  ShoppingBag, 
  Search, 
  Filter, 
  ChevronRight, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Truck,
  RotateCcw
} from "lucide-react";

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await api.orders.list({
        page,
        page_size: 20,
        status: statusFilter || undefined,
        search: search || undefined
      });
      setOrders(res.data || []);
      setTotal(res.meta?.total || 0);
    } catch (err) {
      console.error("Failed to load orders:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchOrders();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "CONFIRMED":
        return <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">Confirmed</span>;
      case "PROCESSING":
        return <span className="px-2 py-0.5 text-xs rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">Processing</span>;
      case "SHIPPED":
        return <span className="px-2 py-0.5 text-xs rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">Shipped</span>;
      case "DELIVERED":
        return <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 font-semibold">Delivered</span>;
      case "CANCELLED":
        return <span className="px-2 py-0.5 text-xs rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium">Cancelled</span>;
      default:
        return <span className="px-2 py-0.5 text-xs rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20">{status}</span>;
    }
  };

  const getPaymentBadge = (status: string) => {
    switch (status) {
      case "PAID":
        return <span className="text-xs text-emerald-400 font-medium flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Paid</span>;
      case "REFUNDED":
        return <span className="text-xs text-amber-400 font-medium flex items-center gap-1"><RotateCcw className="w-3 h-3" /> Refunded</span>;
      case "FAILED":
        return <span className="text-xs text-rose-400 font-medium flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Failed</span>;
      default:
        return <span className="text-xs text-slate-400 flex items-center gap-1"><Clock className="w-3 h-3" /> {status}</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <ShoppingBag className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Orders Management</h1>
              <p className="text-sm text-slate-400">Track lifecycle, payment settlements, and fulfillment for UrbanThread.</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
          <span>Total Orders:</span>
          <span className="font-semibold text-white">{total}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 justify-between items-center">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by order number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="PROCESSING">Processing</option>
            <option value="SHIPPED">Shipped</option>
            <option value="DELIVERED">Delivered</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-3.5">Order</th>
                <th className="px-6 py-3.5">Customer</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Payment</th>
                <th className="px-6 py-3.5">Items</th>
                <th className="px-6 py-3.5 text-right">Total</th>
                <th className="px-6 py-3.5 text-right">Date</th>
                <th className="px-6 py-3.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                    Loading orders...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                    No orders found matching criteria.
                  </td>
                </tr>
              ) : (
                orders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 font-mono font-semibold text-white">
                      <Link href={`/orders/${ord.id}`} className="hover:text-blue-400 transition-colors">
                        {ord.order_number}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-200">{ord.customer_name}</div>
                      <div className="text-xs text-slate-400">{ord.customer_email}</div>
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(ord.status)}</td>
                    <td className="px-6 py-4">{getPaymentBadge(ord.payment_status)}</td>
                    <td className="px-6 py-4 text-slate-400">{ord.items_count} item{ord.items_count > 1 ? "s" : ""}</td>
                    <td className="px-6 py-4 text-right font-semibold text-white">
                      ₹{ord.total_amount?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 text-right text-xs text-slate-400 whitespace-nowrap">
                      {ord.placed_at ? new Date(ord.placed_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        href={`/orders/${ord.id}`}
                        className="inline-flex items-center gap-1 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        Detail <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
