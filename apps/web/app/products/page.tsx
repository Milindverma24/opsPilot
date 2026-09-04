"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  Package, 
  Search, 
  Tag, 
  Layers, 
  Plus, 
  ExternalLink,
  ChevronDown
} from "lucide-react";

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);
  const [productDetailLoading, setProductDetailLoading] = useState(false);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const res = await api.products.list({ search: search || undefined });
      setProducts(res.data || []);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSelectProduct = async (id: string) => {
    setProductDetailLoading(true);
    try {
      const res = await api.products.get(id);
      setSelectedProduct(res.data);
    } catch (err) {
      console.error("Failed to load product details:", err);
    } finally {
      setProductDetailLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Package className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Product Catalog</h1>
              <p className="text-sm text-slate-400">Apparel catalog, sizing variants, and retail pricing.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Left Product List, Right Product Detail with Variants */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Products List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search products by SKU or title..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchProducts()}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <button 
              onClick={fetchProducts}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold"
            >
              Search
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Product</th>
                  <th className="px-5 py-3.5">Category</th>
                  <th className="px-5 py-3.5 text-right">Base Price</th>
                  <th className="px-5 py-3.5 text-right">Sale Price</th>
                  <th className="px-5 py-3.5 text-center">Variants</th>
                  <th className="px-5 py-3.5 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr><td colSpan={6} className="px-6 py-10 text-center text-slate-400">Loading catalog...</td></tr>
                ) : products.map((p) => (
                  <tr 
                    key={p.id}
                    onClick={() => handleSelectProduct(p.id)}
                    className={`cursor-pointer hover:bg-slate-800/50 transition-colors ${selectedProduct?.id === p.id ? 'bg-blue-950/30 border-l-2 border-blue-500' : ''}`}
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-white">{p.name}</div>
                      <div className="text-xs font-mono text-slate-400">{p.sku}</div>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-300">{p.category || "General"}</td>
                    <td className="px-5 py-3.5 text-right font-mono text-xs text-slate-400">₹{p.base_price}</td>
                    <td className="px-5 py-3.5 text-right font-mono font-bold text-white">
                      {p.sale_price ? `₹${p.sale_price}` : "—"}
                    </td>
                    <td className="px-5 py-3.5 text-center text-xs text-blue-400 font-medium">
                      {p.variants_count} sizes
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Product Detail & Variants Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
          {productDetailLoading ? (
            <div className="py-20 text-center text-slate-400 text-sm">Loading product details...</div>
          ) : selectedProduct ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-start">
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-800 rounded text-slate-400">
                    {selectedProduct.sku}
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">{selectedProduct.status}</span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1">{selectedProduct.name}</h2>
                <p className="text-xs text-slate-400 mt-1">{selectedProduct.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500 block">Gender</span>
                  <span className="font-medium text-slate-200">{selectedProduct.gender}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Material</span>
                  <span className="font-medium text-slate-200">{selectedProduct.material || "—"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Care</span>
                  <span className="font-medium text-slate-200">{selectedProduct.care_instructions || "—"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Pricing</span>
                  <span className="font-bold text-white">₹{selectedProduct.sale_price || selectedProduct.base_price}</span>
                </div>
              </div>

              {/* Variants List */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-blue-400" /> Sizing & Inventory Variants
                </h3>
                <div className="space-y-1.5 max-h-80 overflow-y-auto">
                  {selectedProduct.variants?.map((v: any) => (
                    <div key={v.id} className="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex justify-between items-center text-xs">
                      <div>
                        <span className="font-bold text-white">{v.size}</span>
                        <span className="text-slate-400 ml-1.5">({v.color})</span>
                        <div className="text-[10px] font-mono text-slate-500">{v.sku}</div>
                      </div>
                      <div className="text-right">
                        <span className={`font-mono font-semibold ${v.available_quantity === 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {v.available_quantity} avail
                        </span>
                        <div className="text-[10px] text-slate-500">({v.quantity_on_hand} on-hand)</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-24 text-center text-slate-400 text-sm">
              <Package className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              Select a product to view variants and inventory stock breakdown.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
