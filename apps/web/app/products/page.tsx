"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { api } from "@/lib/api";
import { 
  Package, 
  Search, 
  Tag, 
  Layers, 
  Plus, 
  ExternalLink,
  ChevronDown,
  Sparkles,
  CheckCircle2,
  X,
  BookOpen,
  Scissors,
  DollarSign
} from "lucide-react";

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);
  const [productDetailLoading, setProductDetailLoading] = useState(false);
  const [ragSyncing, setRagSyncing] = useState(false);
  const [ragMessage, setRagMessage] = useState<string | null>(null);

  const handleSyncRag = async () => {
    setRagSyncing(true);
    setRagMessage(null);
    try {
      const res = await api.knowledge.syncCatalog();
      setRagMessage(`RAG Trained! ${res.documents_count} documents & ${res.chunks_count} vector chunks indexed.`);
    } catch (err: any) {
      console.error("RAG Sync Error:", err);
      setRagMessage("Failed to sync RAG knowledge. Check server.");
    } finally {
      setRagSyncing(false);
    }
  };

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

  const filteredProducts = products.filter((p) => {
    const q = search.toLowerCase();
    return (
      p.name?.toLowerCase().includes(q) ||
      p.sku?.toLowerCase().includes(q) ||
      p.category?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar
          title="Product Catalog & Variants"
          subtitle="Apparel catalog, sizing variants, retail pricing, live studio generator, and RAG vector store"
        />

        <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Top Header & Fast Actions */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <Package className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">Apparel Catalog</h1>
                <p className="text-sm text-slate-400">Catalog of clothing styles, SKUs, care guides, and vector index.</p>
              </div>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <button
                onClick={handleSyncRag}
                disabled={ragSyncing}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-2 disabled:opacity-50"
                title="Re-index all products & SOPs into RAG vector store"
              >
                <Layers className={`w-4 h-4 text-indigo-400 ${ragSyncing ? 'animate-spin' : ''}`} />
                {ragSyncing ? "Syncing RAG..." : "Sync RAG Catalog"}
              </button>

              <Link
                href="/store"
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-2"
              >
                <ExternalLink className="w-4 h-4 text-emerald-400" />
                Storefront
              </Link>

              <Link
                href="/products/new"
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-blue-500/20 transition-all flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Product (Studio)
              </Link>
            </div>
          </div>

          {ragMessage && (
            <div className="p-4 rounded-xl bg-indigo-950/70 border border-indigo-500/30 text-indigo-200 text-xs flex items-center justify-between shadow-lg">
              <div className="flex items-center gap-2.5">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>{ragMessage}</span>
              </div>
              <button
                onClick={() => setRagMessage(null)}
                className="text-indigo-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Search bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex justify-between items-center">
            <div className="relative w-full max-w-md">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products by name, SKU, or category..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="text-xs text-slate-400">
              Total Products: <span className="font-bold text-white">{products.length}</span>
            </div>
          </div>

          {/* Product Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {loading ? (
              <div className="col-span-3 py-20 text-center text-slate-500 text-xs">
                Loading products catalog...
              </div>
            ) : filteredProducts.length === 0 ? (
              <div className="col-span-3 py-20 text-center text-slate-500 text-xs bg-slate-900/40 rounded-2xl border border-slate-800">
                No products match the search query.
              </div>
            ) : (
              filteredProducts.map((p) => {
                const img = (p.images && p.images[0]?.url) || "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&q=80";
                return (
                  <div
                    key={p.id}
                    className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700 transition-all flex flex-col group shadow-sm hover:shadow-lg hover:shadow-blue-500/5"
                  >
                    <div className="h-48 w-full relative bg-slate-950 overflow-hidden">
                      <img
                        src={img}
                        alt={p.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <span className="absolute top-3 right-3 px-2 py-0.5 text-[10px] font-bold rounded-full bg-slate-900/90 text-white border border-slate-700/80 backdrop-blur-sm">
                        {p.category || "Apparel"}
                      </span>
                    </div>

                    <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                      <div>
                        <div className="flex justify-between items-start">
                          <h3 className="font-bold text-sm text-white line-clamp-1">{p.name}</h3>
                          <span className="font-mono text-xs font-bold text-emerald-400">₹{p.base_price}</span>
                        </div>
                        <p className="text-xs text-slate-400 mt-1 line-clamp-2">{p.description}</p>
                      </div>

                      <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                        <span className="text-[11px] font-mono text-slate-500">{p.sku}</span>
                        <button
                          onClick={() => handleSelectProduct(p.id)}
                          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
                        >
                          Details
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </main>
      </div>

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Package className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">{selectedProduct.name}</h3>
                  <p className="text-xs text-slate-400 font-mono">SKU: {selectedProduct.sku}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedProduct(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                <div>
                  <span className="text-slate-500 block text-[11px]">Retail Base Price</span>
                  <span className="text-lg font-bold text-emerald-400 font-mono">₹{selectedProduct.base_price}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Category</span>
                  <span className="font-semibold text-white">{selectedProduct.category || "Apparel"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Status</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {selectedProduct.status || "ACTIVE"}
                  </span>
                </div>
              </div>

              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] block mb-1">
                  Product Description
                </span>
                <p className="text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800 leading-relaxed">
                  {selectedProduct.description}
                </p>
              </div>

              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] block mb-1">
                  Active Sizing Variants
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {(selectedProduct.variants || []).map((v: any) => (
                    <div key={v.id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-center">
                      <span className="font-bold text-white font-mono block text-xs">{v.size || "M"}</span>
                      <span className="text-[10px] text-slate-400 block mt-0.5">₹{v.price || selectedProduct.base_price}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-between items-center pt-3 border-t border-slate-800">
                <Link
                  href="/store"
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-emerald-400" />
                  View in Storefront
                </Link>

                <button
                  onClick={() => setSelectedProduct(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
