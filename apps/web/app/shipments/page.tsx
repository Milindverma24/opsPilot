"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  Truck, 
  Search, 
  Filter, 
  MapPin, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw 
} from "lucide-react";

export default function ShipmentsPage() {
  const [shipments, setShipments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  const fetchShipments = async () => {
    setLoading(true);
    try {
      const res = await api.shipments.list({ status: statusFilter || undefined });
      setShipments(res.data || []);
    } catch (err) {
      console.error("Failed to load shipments:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShipments();
  }, [statusFilter]);

  const handleSimulateDelay = async (id: string) => {
    try {
      await api.shipments.updateStatus(id, {
        status: "DELAYED",
        last_location: "Severe Monsoon Rail Incline Transit Hub"
      });
      await fetchShipments();
    } catch (err: any) {
      alert(err.message || "Failed to update shipment status");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Shipments & Logistics</h1>
              <p className="text-sm text-slate-400">Live courier tracking, dispatch status, and delay mitigations.</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Logistics Statuses</option>
            <option value="PACKED">Packed</option>
            <option value="SHIPPED">Shipped</option>
            <option value="IN_TRANSIT">In Transit</option>
            <option value="DELIVERED">Delivered</option>
            <option value="DELAYED">Delayed</option>
          </select>
          <button 
            onClick={fetchShipments}
            className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Shipments Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-3.5">Tracking Number</th>
                <th className="px-6 py-3.5">Carrier</th>
                <th className="px-6 py-3.5">Order</th>
                <th className="px-6 py-3.5">Last Known Hub</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">Loading shipments...</td></tr>
              ) : shipments.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">No shipments found.</td></tr>
              ) : shipments.map((s) => (
                <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-white">
                    {s.tracking_number}
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-200">
                    {s.carrier}
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-blue-400">
                    {s.order_number || "—"}
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      <span>{s.last_location || "Fulfillment Hub"}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {s.status === "DELAYED" ? (
                      <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center gap-1 w-fit">
                        <AlertTriangle className="w-3 h-3" /> Delayed
                      </span>
                    ) : s.status === "DELIVERED" ? (
                      <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1 w-fit">
                        <CheckCircle2 className="w-3 h-3" /> Delivered
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        {s.status}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {s.status !== "DELAYED" && s.status !== "DELIVERED" && (
                      <button
                        onClick={() => handleSimulateDelay(s.id)}
                        className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                      >
                        Simulate Delay
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
