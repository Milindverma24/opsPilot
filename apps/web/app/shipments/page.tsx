"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { api } from "@/lib/api";
import { 
  Truck, 
  Search, 
  Filter, 
  MapPin, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw,
  Plus,
  Navigation,
  ExternalLink,
  Calendar,
  X,
  ArrowRight,
  ShieldCheck,
  Package
} from "lucide-react";

export default function ShipmentsPage() {
  const [shipments, setShipments] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Dispatch Shipment Modal
  const [showDispatchModal, setShowDispatchModal] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState("");
  const [selectedCarrier, setSelectedCarrier] = useState("Delhivery Express");
  const [dispatchSubmitting, setDispatchSubmitting] = useState(false);

  const fetchShipments = async () => {
    setLoading(true);
    try {
      const res = await api.shipments.list({
        status: statusFilter === "ALL" ? undefined : statusFilter
      });
      setShipments(res.data || []);
    } catch (err) {
      console.error("Failed to load shipments:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrdersForDispatch = async () => {
    try {
      const res = await api.orders.list({ page_size: 20 });
      const active = (res.data || []).filter((o: any) => o.status !== "CANCELLED");
      setOrders(active);
      if (active.length > 0 && !selectedOrderId) {
        setSelectedOrderId(active[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch orders for dispatch:", err);
    }
  };

  useEffect(() => {
    fetchShipments();
  }, [statusFilter]);

  useEffect(() => {
    fetchOrdersForDispatch();
  }, []);

  const handleSimulateDelay = async (id: string) => {
    setActionLoading(id);
    try {
      await api.shipments.updateStatus(id, {
        status: "DELAYED",
        last_location: "Severe Weather Rail Crossing Delay, Northern Incline Hub"
      });
      await fetchShipments();
    } catch (err: any) {
      alert(err.message || "Failed to update shipment status");
    } finally {
      setActionLoading(null);
    }
  };

  const handleMarkDelivered = async (id: string) => {
    setActionLoading(id);
    try {
      await api.shipments.updateStatus(id, {
        status: "DELIVERED",
        last_location: "Delivered to Customer Front Gate (Signature Verified)"
      });
      await fetchShipments();
    } catch (err: any) {
      alert(err.message || "Failed to mark shipment delivered");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateShipment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrderId) return;
    setDispatchSubmitting(true);
    try {
      await api.shipments.create({
        order_id: selectedOrderId,
        carrier: selectedCarrier
      });
      setShowDispatchModal(false);
      await fetchShipments();
    } catch (err: any) {
      alert(err.message || "Failed to dispatch shipment");
    } finally {
      setDispatchSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "DELIVERED":
        return (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Delivered
          </span>
        );
      case "IN_TRANSIT":
        return (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center gap-1.5">
            <Truck className="w-3.5 h-3.5" /> In Transit
          </span>
        );
      case "DELAYED":
        return (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> Delayed
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> {status}
          </span>
        );
    }
  };

  const filteredShipments = shipments.filter((s) => {
    const matchesSearch = 
      s.tracking_number?.toLowerCase().includes(search.toLowerCase()) ||
      s.order_number?.toLowerCase().includes(search.toLowerCase()) ||
      s.carrier?.toLowerCase().includes(search.toLowerCase()) ||
      s.destination_city?.toLowerCase().includes(search.toLowerCase());
    return matchesSearch;
  });

  const inTransitCount = shipments.filter((s) => s.status === "IN_TRANSIT").length;
  const delayedCount = shipments.filter((s) => s.status === "DELAYED").length;
  const deliveredCount = shipments.filter((s) => s.status === "DELIVERED").length;

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Shipments & Logistics"
          subtitle="Autonomous courier dispatch, live GPS milestone tracking, and SLA delay mitigations"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
                <Truck className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Consignments</span>
                <div className="text-2xl font-bold text-white mt-0.5">{shipments.length}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
                <Navigation className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">In Transit</span>
                <div className="text-2xl font-bold text-blue-400 mt-0.5">{inTransitCount}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Delayed Alerts</span>
                <div className="text-2xl font-bold text-rose-400 mt-0.5">{delayedCount}</div>
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Delivered</span>
                <div className="text-2xl font-bold text-emerald-400 mt-0.5">{deliveredCount}</div>
              </div>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search tracking #, order, carrier..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="flex items-center gap-2.5 w-full md:w-auto">
              <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs overflow-x-auto">
                {["ALL", "IN_TRANSIT", "DELAYED", "DELIVERED"].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                      statusFilter === st
                        ? "bg-slate-800 text-white font-bold shadow-sm"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {st === "ALL" ? "All Shipments" : st.replace("_", " ")}
                  </button>
                ))}
              </div>

              <button
                onClick={() => {
                  fetchOrdersForDispatch();
                  setShowDispatchModal(true);
                }}
                className="px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-md shadow-purple-600/20 transition-all flex items-center gap-1.5 shrink-0"
              >
                <Plus className="w-4 h-4" />
                Dispatch Shipment
              </button>
            </div>
          </div>

          {/* Shipments List */}
          <div className="space-y-4">
            {loading ? (
              <div className="py-20 text-center text-slate-500 text-xs bg-slate-900/40 rounded-2xl border border-slate-800">
                Loading shipments pipeline...
              </div>
            ) : filteredShipments.length === 0 ? (
              <div className="py-20 text-center text-slate-500 text-xs bg-slate-900/40 rounded-2xl border border-slate-800">
                No shipments found matching criteria.
              </div>
            ) : (
              filteredShipments.map((s) => (
                <div
                  key={s.id}
                  className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all space-y-4 shadow-sm"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
                        <Truck className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-white bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 tracking-wider">
                            {s.tracking_number}
                          </span>
                          <span className="text-xs text-slate-400">• Order {s.order_number || s.order_id?.slice(0, 8)}</span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{s.carrier} — {s.shipping_method || "Express Surface"}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {getStatusBadge(s.status)}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                    <div>
                      <span className="text-slate-500 block text-[11px]">Last Known Location</span>
                      <div className="flex items-center gap-1.5 text-slate-200 mt-0.5">
                        <MapPin className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                        <span className="font-medium line-clamp-1">{s.current_location || s.last_location || "Dispatched from Mumbai Central Fulfillment"}</span>
                      </div>
                    </div>

                    <div>
                      <span className="text-slate-500 block text-[11px]">Est. Delivery</span>
                      <div className="flex items-center gap-1.5 text-slate-200 mt-0.5">
                        <Calendar className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                        <span className="font-medium">
                          {s.estimated_delivery ? new Date(s.estimated_delivery).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" }) : "In 2-3 days"}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center sm:justify-end gap-2 pt-1 sm:pt-0">
                      {s.status !== "DELIVERED" && (
                        <>
                          <button
                            onClick={() => handleSimulateDelay(s.id)}
                            disabled={actionLoading === s.id}
                            className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 font-semibold text-xs transition-colors disabled:opacity-50"
                          >
                            Simulate Delay
                          </button>
                          <button
                            onClick={() => handleMarkDelivered(s.id)}
                            disabled={actionLoading === s.id}
                            className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Mark Delivered
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </main>
      </div>

      {/* Dispatch Shipment Modal */}
      {showDispatchModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                  <Truck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Dispatch Shipment</h3>
                  <p className="text-xs text-slate-400">Assign courier and generate consignment manifest</p>
                </div>
              </div>
              <button
                onClick={() => setShowDispatchModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateShipment} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Select Order *</label>
                <select
                  value={selectedOrderId}
                  onChange={(e) => setSelectedOrderId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-purple-500"
                >
                  {orders.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.order_number} — ₹{o.total_amount || o.subtotal} ({o.customer?.name || "Customer"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Logistics Courier</label>
                <select
                  value={selectedCarrier}
                  onChange={(e) => setSelectedCarrier(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="Delhivery Express">Delhivery Express (Surface / Air)</option>
                  <option value="BlueDart Air Priority">BlueDart Air Priority</option>
                  <option value="DTDC Express Premium">DTDC Express Premium</option>
                  <option value="Shadowfax Hyperlocal">Shadowfax Hyperlocal</option>
                  <option value="XpressBees Logistics">XpressBees Logistics</option>
                </select>
              </div>

              <div className="p-3 bg-purple-950/30 border border-purple-500/20 rounded-xl text-xs text-purple-200">
                <span className="font-semibold text-purple-300">Automated Dispatch SOP:</span> Tracking ID will be generated, customer notified via SMS, and warehouse pickup scheduled.
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowDispatchModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={dispatchSubmitting || !selectedOrderId}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-bold text-white shadow-lg shadow-purple-600/20 disabled:opacity-50"
                >
                  {dispatchSubmitting ? "Generating Waybill..." : "Confirm Dispatch"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
