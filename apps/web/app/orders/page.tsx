"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
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
  RotateCcw,
  XCircle,
  CreditCard,
  User,
  MapPin,
  Calendar,
  X,
  Plus,
  ExternalLink,
  ShieldCheck,
  Package
} from "lucide-react";

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  // Order Details Modal
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [orderModalOpen, setOrderModalOpen] = useState(false);
  const [orderDetailLoading, setOrderDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await api.orders.list({
        page,
        page_size: 50,
        status: statusFilter === "ALL" ? undefined : statusFilter,
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
    fetchOrders();
  };

  const handleOpenOrderDetail = async (orderId: string) => {
    setOrderModalOpen(true);
    setOrderDetailLoading(true);
    try {
      const res = await api.orders.get(orderId);
      setSelectedOrder(res.data);
    } catch (err) {
      console.error("Failed to load order details:", err);
    } finally {
      setOrderDetailLoading(false);
    }
  };

  const handleMarkShipped = async (id: string) => {
    setActionLoading("ship");
    try {
      await api.orders.markShipped(id);
      await fetchOrders();
      if (selectedOrder?.id === id) {
        setSelectedOrder((prev: any) => ({ ...prev, status: "SHIPPED", fulfillment_status: "SHIPPED" }));
      }
    } catch (err: any) {
      alert(err.message || "Failed to mark order as shipped");
    } finally {
      setActionLoading(null);
    }
  };

  const handleMarkDelivered = async (id: string) => {
    setActionLoading("deliver");
    try {
      await api.orders.markDelivered(id);
      await fetchOrders();
      if (selectedOrder?.id === id) {
        setSelectedOrder((prev: any) => ({ ...prev, status: "DELIVERED", fulfillment_status: "DELIVERED" }));
      }
    } catch (err: any) {
      alert(err.message || "Failed to mark order as delivered");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancelOrder = async (id: string) => {
    if (!confirm("Are you sure you want to cancel this order and release inventory?")) return;
    setActionLoading("cancel");
    try {
      await api.orders.cancel(id);
      await fetchOrders();
      if (selectedOrder?.id === id) {
        setSelectedOrder((prev: any) => ({ ...prev, status: "CANCELLED" }));
      }
    } catch (err: any) {
      alert(err.message || "Failed to cancel order");
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PENDING":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold flex items-center gap-1"><Clock className="w-3 h-3" /> Pending</span>;
      case "CONFIRMED":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Confirmed</span>;
      case "SHIPPED":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-semibold flex items-center gap-1"><Truck className="w-3 h-3" /> Shipped</span>;
      case "DELIVERED":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Delivered</span>;
      case "CANCELLED":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold flex items-center gap-1"><XCircle className="w-3 h-3" /> Cancelled</span>;
      default:
        return <span className="px-2.5 py-1 text-xs rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20">{status}</span>;
    }
  };

  const totalRevenue = orders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
  const pendingOrders = orders.filter((o) => o.status === "PENDING" || o.status === "CONFIRMED").length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Orders & Fulfillment"
          subtitle="Order processing pipeline, payment settlement, reverse logistics, and customer tracking"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metrics Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <ShoppingBag className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Orders</span>
                <div className="text-2xl font-bold text-white mt-0.5">{total || orders.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CreditCard className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Gross GMV</span>
                <div className="text-2xl font-bold text-emerald-400 mt-0.5">₹{Math.round(totalRevenue).toLocaleString()}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Clock className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pending Fulfillment</span>
                <div className="text-2xl font-bold text-amber-400 mt-0.5">{pendingOrders}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
                <Truck className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Shipments</span>
                <div className="text-sm font-bold text-white mt-1">Delhivery & BlueDart</div>
              </div>
            </div>
          </div>

          {/* Filter and Search Bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row gap-4 justify-between items-center">
            <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search order #, customer..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
              />
            </form>

            <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
              {["ALL", "PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all shrink-0 ${
                    statusFilter === st
                      ? "bg-blue-600 text-white shadow-md shadow-blue-600/20"
                      : "bg-slate-950 border border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  {st === "ALL" ? "All Orders" : st}
                </button>
              ))}
            </div>
          </div>

          {/* Orders Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Order Details</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Customer</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Items</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Total Amount</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Payment</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Status</th>
                    <th className="py-3.5 px-4 font-semibold uppercase tracking-wider text-[11px] text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="py-16 text-center text-slate-500">
                        Loading orders ledger...
                      </td>
                    </tr>
                  ) : orders.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-16 text-center text-slate-500">
                        No orders found matching criteria.
                      </td>
                    </tr>
                  ) : (
                    orders.map((o) => (
                      <tr key={o.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <span className="font-mono text-xs font-bold text-white bg-slate-950 px-2 py-1 rounded border border-slate-800">
                            {o.order_number}
                          </span>
                          <span className="text-[11px] text-slate-500 block mt-1">
                            {o.placed_at ? new Date(o.placed_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Recent"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-white text-xs">{o.customer?.name || "Customer"}</div>
                          <div className="text-[11px] text-slate-400">{o.customer?.email || ""}</div>
                        </td>
                        <td className="py-3.5 px-4 text-slate-300 font-mono">
                          {o.items_count || (o.items ? o.items.length : 1)} item(s)
                        </td>
                        <td className="py-3.5 px-4 font-bold text-white font-mono text-xs">
                          ₹{o.total_amount || o.subtotal}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            o.payment_status === "PAID"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}>
                            {o.payment_status || "PAID"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">{getStatusBadge(o.status)}</td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => handleOpenOrderDetail(o.id)}
                            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-colors"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      {/* Order Details Modal */}
      {orderModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <ShoppingBag className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">
                    Order Details: {selectedOrder?.order_number || "Loading..."}
                  </h3>
                  <p className="text-xs text-slate-400">Customer purchase receipt and dispatch actions</p>
                </div>
              </div>
              <button
                onClick={() => setOrderModalOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {orderDetailLoading || !selectedOrder ? (
              <div className="py-20 text-center text-slate-500 text-xs">Loading order details...</div>
            ) : (
              <div className="space-y-5 text-xs">
                {/* Status and Action Buttons */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                  <div>
                    <span className="text-slate-500 block text-[11px]">Current Lifecycle Status</span>
                    <div className="mt-1">{getStatusBadge(selectedOrder.status)}</div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    {selectedOrder.status !== "SHIPPED" && selectedOrder.status !== "DELIVERED" && selectedOrder.status !== "CANCELLED" && (
                      <button
                        onClick={() => handleMarkShipped(selectedOrder.id)}
                        disabled={actionLoading === "ship"}
                        className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-md shadow-purple-600/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
                      >
                        <Truck className="w-3.5 h-3.5" />
                        Mark Shipped
                      </button>
                    )}

                    {selectedOrder.status === "SHIPPED" && (
                      <button
                        onClick={() => handleMarkDelivered(selectedOrder.id)}
                        disabled={actionLoading === "deliver"}
                        className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Mark Delivered
                      </button>
                    )}

                    {selectedOrder.status !== "CANCELLED" && selectedOrder.status !== "DELIVERED" && (
                      <button
                        onClick={() => handleCancelOrder(selectedOrder.id)}
                        disabled={actionLoading === "cancel"}
                        className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 font-semibold text-xs transition-colors disabled:opacity-50"
                      >
                        Cancel Order
                      </button>
                    )}
                  </div>
                </div>

                {/* Customer Information */}
                <div className="grid grid-cols-2 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div>
                    <span className="text-slate-500 block text-[11px]">Customer</span>
                    <span className="font-bold text-white block mt-0.5">{selectedOrder.customer?.name}</span>
                    <span className="text-slate-400 block text-[11px]">{selectedOrder.customer?.email}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Shipping Destination</span>
                    <span className="text-slate-200 block mt-0.5">
                      {selectedOrder.customer?.phone || "Mumbai, Maharashtra"}
                    </span>
                    <span className="text-emerald-400 font-medium block text-[11px]">Standard Express Surface</span>
                  </div>
                </div>

                {/* Items in Order */}
                <div className="space-y-2">
                  <span className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] block">
                    Ordered Line Items
                  </span>
                  <div className="space-y-2">
                    {(selectedOrder.items || []).map((itm: any) => (
                      <div
                        key={itm.id}
                        className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between"
                      >
                        <div>
                          <span className="font-bold text-white">{itm.product_name}</span>
                          <span className="text-[11px] text-slate-400 block font-mono mt-0.5">
                            SKU: {itm.sku} • Size: {itm.size || "M"} • Qty: {itm.quantity}
                          </span>
                        </div>
                        <span className="font-bold text-white font-mono">₹{itm.total_price || itm.unit_price}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Financial Breakdown */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex justify-between text-slate-400">
                    <span>Subtotal:</span>
                    <span className="font-mono text-white">₹{selectedOrder.subtotal || 0}</span>
                  </div>
                  {selectedOrder.discount_amount > 0 && (
                    <div className="flex justify-between text-emerald-400">
                      <span>Voucher Discount:</span>
                      <span className="font-mono">-₹{selectedOrder.discount_amount}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-slate-400">
                    <span>Shipping Charges:</span>
                    <span className="font-mono text-white">₹{selectedOrder.shipping_amount || 0}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>GST (Taxes):</span>
                    <span className="font-mono text-white">₹{selectedOrder.tax_amount || 0}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-slate-800 font-bold text-sm text-white">
                    <span>Grand Total:</span>
                    <span className="text-emerald-400 font-mono">₹{selectedOrder.total_amount || selectedOrder.subtotal}</span>
                  </div>
                </div>

                {/* Operations Quick Links */}
                <div className="flex justify-between items-center pt-2">
                  <div className="flex gap-2">
                    <Link
                      href="/returns"
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 text-xs font-semibold transition-colors flex items-center gap-1.5"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      Initiate Return
                    </Link>
                    <Link
                      href="/refunds"
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 text-xs font-semibold transition-colors flex items-center gap-1.5"
                    >
                      <CreditCard className="w-3.5 h-3.5" />
                      Issue Refund
                    </Link>
                  </div>

                  <button
                    type="button"
                    onClick={() => setOrderModalOpen(false)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
