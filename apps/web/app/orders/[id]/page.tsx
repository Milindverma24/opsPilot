"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { 
  ArrowLeft, 
  ShoppingBag, 
  CreditCard, 
  Truck, 
  RotateCcw, 
  User, 
  Tag, 
  CheckCircle2, 
  AlertCircle, 
  XCircle,
  Clock
} from "lucide-react";

export default function OrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrderDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.orders.get(id);
      setOrder(res.data);
    } catch (err: any) {
      setError(err.message || "Failed to load order.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchOrderDetail();
  }, [id]);

  const handleCancelOrder = async () => {
    if (!confirm("Are you sure you want to cancel this order? Reserved stock will be released.")) return;
    setCancelling(true);
    try {
      await api.orders.cancel(id);
      await fetchOrderDetail();
    } catch (err: any) {
      alert(err.message || "Failed to cancel order.");
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto text-slate-400">
        Loading order details...
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-4">
        <Link href="/orders" className="text-xs text-blue-400 flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Orders
        </Link>
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl">
          {error || "Order not found."}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Back button & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Link href="/orders" className="text-xs text-slate-400 hover:text-white flex items-center gap-1 mb-2 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Orders
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white tracking-tight font-mono">{order.order_number}</h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              {order.status}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Placed on {order.placed_at ? new Date(order.placed_at).toLocaleString() : "—"}
          </p>
        </div>

        {order.status !== "CANCELLED" && order.status !== "DELIVERED" && (
          <button
            onClick={handleCancelOrder}
            disabled={cancelling}
            className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <XCircle className="w-4 h-4" />
            {cancelling ? "Cancelling..." : "Cancel Order"}
          </button>
        )}
      </div>

      {/* Grid Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Customer Information */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <User className="w-4 h-4 text-blue-400" /> Customer Details
          </div>
          <div className="space-y-1">
            <div className="text-sm font-semibold text-white">{order.customer?.name}</div>
            <div className="text-xs text-slate-400">{order.customer?.email}</div>
            <div className="text-xs text-slate-400">{order.customer?.phone}</div>
          </div>
        </div>

        {/* Payment Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <CreditCard className="w-4 h-4 text-emerald-400" /> Settlement
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Payment Status:</span>
              <span className="font-semibold text-white">{order.payment_status}</span>
            </div>
            <div className="flex justify-between text-xs text-slate-400">
              <span>Total Amount:</span>
              <span className="font-bold text-white">₹{order.total_amount?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
            {order.coupon_code && (
              <div className="flex justify-between text-xs text-emerald-400">
                <span>Coupon Applied:</span>
                <span className="font-mono">{order.coupon_code}</span>
              </div>
            )}
          </div>
        </div>

        {/* Fulfillment Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <Truck className="w-4 h-4 text-purple-400" /> Dispatch
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Fulfillment:</span>
              <span className="font-semibold text-white">{order.fulfillment_status}</span>
            </div>
            {order.shipments && order.shipments.length > 0 && (
              <div className="text-xs text-purple-300 font-mono">
                {order.shipments[0].carrier}: {order.shipments[0].tracking_number}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Items Snapshot Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 bg-slate-950/60 border-b border-slate-800 font-semibold text-sm text-white flex items-center gap-2">
          <ShoppingBag className="w-4 h-4 text-blue-400" /> Order Items Snapshot
        </div>
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/40 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="px-6 py-3">Product</th>
              <th className="px-6 py-3">SKU</th>
              <th className="px-6 py-3">Variant</th>
              <th className="px-6 py-3 text-center">Qty</th>
              <th className="px-6 py-3 text-right">Price</th>
              <th className="px-6 py-3 text-right">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {order.items?.map((item: any) => (
              <tr key={item.id}>
                <td className="px-6 py-3.5 font-medium text-white">{item.product_name}</td>
                <td className="px-6 py-3.5 font-mono text-xs text-slate-400">{item.sku}</td>
                <td className="px-6 py-3.5 text-xs text-slate-300">{item.size} • {item.color}</td>
                <td className="px-6 py-3.5 text-center text-slate-300">{item.quantity}</td>
                <td className="px-6 py-3.5 text-right font-mono text-slate-300">₹{item.unit_price}</td>
                <td className="px-6 py-3.5 text-right font-semibold text-white">₹{item.total_amount}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pricing Calculation Breakdown */}
        <div className="bg-slate-950/40 p-5 border-t border-slate-800 flex justify-end">
          <div className="w-64 space-y-2 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Subtotal:</span>
              <span>₹{order.subtotal?.toFixed(2)}</span>
            </div>
            {order.discount_amount > 0 && (
              <div className="flex justify-between text-emerald-400">
                <span>Discount:</span>
                <span>-₹{order.discount_amount?.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-slate-400">
              <span>Tax (GST 12%):</span>
              <span>₹{order.tax_amount?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Shipping:</span>
              <span>₹{order.shipping_amount?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm font-bold text-white pt-2 border-t border-slate-800">
              <span>Final Total:</span>
              <span>₹{order.total_amount?.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Shipment & Tracking Details */}
      {order.shipments && order.shipments.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Truck className="w-4 h-4 text-purple-400" /> Carrier Dispatch & Transit Records
          </h3>
          <div className="space-y-3">
            {order.shipments.map((s: any) => (
              <div key={s.id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                <div>
                  <div className="font-semibold text-white text-sm">{s.carrier} — {s.tracking_number}</div>
                  <div className="text-xs text-slate-400">Current Location: {s.last_location || "Fulfillment Hub"}</div>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${s.status === 'DELAYED' ? 'bg-amber-500/20 text-amber-300' : 'bg-purple-500/20 text-purple-300'}`}>
                    {s.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Returns & Refunds */}
      {(order.returns?.length > 0 || order.refunds?.length > 0) && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-amber-400" /> Returns & Financial Adjustments
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {order.returns?.map((r: any) => (
              <div key={r.id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs font-semibold text-white">{r.return_number}</span>
                  <span className="px-2 py-0.5 text-[10px] rounded-full bg-amber-500/20 text-amber-300 font-medium">{r.status}</span>
                </div>
                <p className="text-xs text-slate-400">Reason: {r.reason}</p>
              </div>
            ))}
            {order.refunds?.map((rf: any) => (
              <div key={rf.id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs font-semibold text-white">{rf.refund_number}</span>
                  <span className="px-2 py-0.5 text-[10px] rounded-full bg-emerald-500/20 text-emerald-300 font-medium">{rf.status}</span>
                </div>
                <p className="text-xs font-bold text-white">Amount: ₹{rf.amount}</p>
                <p className="text-xs text-slate-400">{rf.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
