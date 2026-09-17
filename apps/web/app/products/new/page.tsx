"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  Package,
  ArrowLeft,
  Sparkles,
  Check,
  Tag,
  Layers,
  Eye,
  ShoppingBag,
  RotateCcw,
  Truck,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
  Sliders,
  Scissors,
  HelpCircle
} from "lucide-react";
import { api, getToken } from "@/lib/api";

const PRESET_IMAGES = [
  { label: "Oversized Tee (White)", url: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80" },
  { label: "Oversized Tee (Sage)", url: "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&auto=format&fit=crop&q=80" },
  { label: "French Linen Shirt", url: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800&auto=format&fit=crop&q=80" },
  { label: "Oxford Button Down", url: "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800&auto=format&fit=crop&q=80" },
  { label: "Selvedge Denim Jacket", url: "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&auto=format&fit=crop&q=80" },
  { label: "Raw Indigo Jeans", url: "https://images.unsplash.com/photo-1542272604-780c96856592?w=800&auto=format&fit=crop&q=80" },
  { label: "Silk Wrap Maxi Dress", url: "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&auto=format&fit=crop&q=80" },
  { label: "Floral Summer Dress", url: "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=800&auto=format&fit=crop&q=80" },
  { label: "Heavy Streetwear Hoodie", url: "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&auto=format&fit=crop&q=80" },
  { label: "Structured Chino Pants", url: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800&auto=format&fit=crop&q=80" }
];

const QUICK_COLORS = [
  { name: "Jet Black", hex: "#18181b" },
  { name: "Off White", hex: "#fafafa" },
  { name: "Vintage Indigo", hex: "#2e3a59" },
  { name: "Sage Green", hex: "#7d8d7e" },
  { name: "Natural Sand", hex: "#d8cca3" },
  { name: "Charcoal Grey", hex: "#3f3f46" },
  { name: "Rust Terracotta", hex: "#b45309" },
  { name: "Olive Leaf", hex: "#4d5b3d" }
];

const STANDARD_SIZES = ["XS", "S", "M", "L", "XL", "XXL"];

export default function NewProductPage() {
  // Form State
  const [name, setName] = useState("Artisan Relaxed Hemp-Cotton Over-Shirt");
  const [sku, setSku] = useState("UT-SHR-088");
  const [category, setCategory] = useState("Men's Casual Shirts");
  const [gender, setGender] = useState<"MEN" | "WOMEN" | "UNISEX">("MEN");
  const [basePrice, setBasePrice] = useState<number>(2999);
  const [salePrice, setSalePrice] = useState<number>(2299);
  const [material, setMaterial] = useState("55% Organic Hemp, 45% Combed Cotton (220 GSM)");
  const [color, setColor] = useState("Vintage Indigo");
  const [careInstructions, setCareInstructions] = useState("Cold machine wash with mild liquid detergent. Air dry in shade. Low-heat reverse iron.");
  const [description, setDescription] = useState("Breathable dual-fiber weave engineered for year-round layering. Detailed with sustainably harvested horn buttons and utility chest pockets.");
  const [imageUrl, setImageUrl] = useState(PRESET_IMAGES[2].url);
  const [featuredBadge, setFeaturedBadge] = useState("Trending");
  const [selectedSizes, setSelectedSizes] = useState<string[]>(["S", "M", "L", "XL"]);
  const [initialStock, setInitialStock] = useState<number>(30);

  // Preview & Submission State
  const [previewMode, setPreviewMode] = useState<"card" | "detail">("card");
  const [submitting, setSubmitting] = useState(false);
  const [successResult, setSuccessResult] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Auto-generate random SKU
  const generateSku = () => {
    const prefixes: Record<string, string> = {
      "Men's T-Shirts": "UT-TSH",
      "Men's Casual Shirts": "UT-SHR",
      "Men's Denim Jeans": "UT-JNS",
      "Women's Dresses": "UT-DRS",
      "Women's Tops & Blouses": "UT-TOP",
      "Outerwear": "UT-JKT"
    };
    const pfx = prefixes[category] || "UT-APP";
    const num = Math.floor(100 + Math.random() * 900);
    setSku(`${pfx}-${num}`);
  };

  // Calculate discount percentage
  const discountPercent = useMemo(() => {
    if (basePrice > 0 && salePrice > 0 && salePrice < basePrice) {
      return Math.round(((basePrice - salePrice) / basePrice) * 100);
    }
    return 0;
  }, [basePrice, salePrice]);

  const toggleSize = (size: string) => {
    setSelectedSizes((prev) =>
      prev.includes(size) ? prev.filter((s) => s !== size) : [...prev, size]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = {
        sku: sku.trim().toUpperCase(),
        name: name.trim(),
        base_price: Number(basePrice),
        sale_price: Number(salePrice),
        brand: "UrbanThread",
        description: description.trim(),
        gender: gender,
        material: material.trim(),
        color: color.trim(),
        care_instructions: careInstructions.trim(),
        image_url: imageUrl.trim(),
        featured_badge: featuredBadge === "None" ? null : featuredBadge,
        sizes: selectedSizes,
        initial_stock: Number(initialStock)
      };

      const res = await api.products.create(payload);
      setSuccessResult(res.data);
    } catch (err: any) {
      console.error("Product creation error:", err);
      setErrorMessage(err.message || "Failed to produce product. Check server connection.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Navigation & Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div className="space-y-1">
            <Link
              href="/products"
              className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors mb-2"
            >
              <ArrowLeft className="w-4 h-4" /> Back to Product Catalog
            </Link>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20">
                <Package className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
                  Product Production Studio
                </h1>
                <p className="text-xs md:text-sm text-slate-400">
                  Produce new apparel, simulate live storefront card rendering, and synchronize RAG knowledge.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live Storefront Preview Active
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              Auto-RAG Vector Sync
            </div>
          </div>
        </div>

        {/* Success Modal Notification */}
        {successResult && (
          <div className="p-6 rounded-2xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-2xl backdrop-blur-md">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-bold text-base text-white">Product Successfully Produced & Published!</h3>
                <p className="text-xs text-emerald-300/90 mt-0.5">
                  SKU <span className="font-mono font-bold text-white">{successResult.sku}</span> has been stocked in warehouse with {successResult.variants_created} size variants and trained into the RAG vector store.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 w-full md:w-auto">
              <Link
                href="/store"
                target="_blank"
                className="flex-1 md:flex-none px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
              >
                View Live in Storefront <ExternalLink className="w-4 h-4" />
              </Link>
              <button
                onClick={() => {
                  setSuccessResult(null);
                  generateSku();
                }}
                className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-colors"
              >
                Produce Another
              </button>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="p-4 rounded-xl bg-red-950/60 border border-red-500/30 text-red-200 text-xs">
            {errorMessage}
          </div>
        )}

        {/* Studio Workspace: Split Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* LEFT: Production Inputs Form (7 Cols) */}
          <form
            onSubmit={handleSubmit}
            className="lg:col-span-7 bg-slate-900/80 border border-slate-800/80 rounded-2xl p-6 md:p-8 space-y-6 shadow-xl backdrop-blur-sm"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-blue-400" /> Apparel Specifications & Inventory
              </h2>
              <span className="text-[11px] font-mono text-slate-400">Step 1 of 1</span>
            </div>

            {/* Product Title & SKU */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2 space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Product Title / Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Oversized Heavyweight Cotton Tee"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-slate-300">Catalog SKU</label>
                  <button
                    type="button"
                    onClick={generateSku}
                    className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  >
                    <RefreshCw className="w-2.5 h-2.5" /> Auto
                  </button>
                </div>
                <input
                  type="text"
                  required
                  value={sku}
                  onChange={(e) => setSku(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm font-mono uppercase text-white focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            {/* Category & Gender */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Apparel Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="Men's T-Shirts">Men's T-Shirts</option>
                  <option value="Men's Casual Shirts">Men's Casual Shirts</option>
                  <option value="Men's Denim Jeans">Men's Denim Jeans</option>
                  <option value="Women's Dresses">Women's Dresses</option>
                  <option value="Women's Tops & Blouses">Women's Tops & Blouses</option>
                  <option value="Women's Denim">Women's Denim</option>
                  <option value="Outerwear & Jackets">Outerwear & Jackets</option>
                  <option value="Hoodies & Sweatshirts">Hoodies & Sweatshirts</option>
                  <option value="Canvas Bags & Accessories">Canvas Bags & Accessories</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Target Fit / Gender</label>
                <div className="grid grid-cols-3 gap-2">
                  {(["MEN", "WOMEN", "UNISEX"] as const).map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setGender(g)}
                      className={`py-2 text-xs font-semibold rounded-xl border transition-all ${
                        gender === g
                          ? "bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-500/20"
                          : "bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Pricing */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Base MRP Price (₹)</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={basePrice}
                  onChange={(e) => setBasePrice(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm font-semibold text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Sale / Offer Price (₹)</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={salePrice}
                  onChange={(e) => setSalePrice(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm font-semibold text-emerald-400 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="space-y-1.5 flex flex-col justify-end">
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Discount Calculated</div>
                  <div className="text-sm font-extrabold text-emerald-400">
                    {discountPercent > 0 ? `${discountPercent}% OFF` : "Full Retail"}
                  </div>
                </div>
              </div>
            </div>

            {/* Fabric Material & Care Instructions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Fabric & Material Composition</label>
                <input
                  type="text"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  placeholder="e.g. 100% Organic Cotton • 240 GSM"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Featured Storefront Badge</label>
                <select
                  value={featuredBadge}
                  onChange={(e) => setFeaturedBadge(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="None">None</option>
                  <option value="Trending">Trending</option>
                  <option value="Best Seller">Best Seller</option>
                  <option value="New Arrival">New Arrival</option>
                  <option value="Sustainable">Sustainable</option>
                  <option value="Limited Edition">Limited Edition</option>
                </select>
              </div>
            </div>

            {/* Color Selection */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">Primary Color</label>
              <div className="flex flex-wrap gap-2">
                {QUICK_COLORS.map((c) => (
                  <button
                    key={c.name}
                    type="button"
                    onClick={() => setColor(c.name)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs transition-all ${
                      color === c.name
                        ? "bg-slate-800 border-blue-500 text-white shadow-sm"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <span
                      className="w-3 h-3 rounded-full border border-slate-600 shadow-inner"
                      style={{ backgroundColor: c.hex }}
                    />
                    {c.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Sizes & Stock */}
            <div className="space-y-2 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-300">
                  Size Variants to Produce ({selectedSizes.length} Selected)
                </label>
                <span className="text-[11px] text-slate-400">
                  Initial stock: {initialStock} units/size
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {STANDARD_SIZES.map((s) => {
                  const active = selectedSizes.includes(s);
                  return (
                    <button
                      key={s}
                      type="button"
                      onClick={() => toggleSize(s)}
                      className={`w-12 h-10 rounded-xl text-xs font-bold border transition-all ${
                        active
                          ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-500/20"
                          : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      {s}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Image Presets & URL */}
            <div className="space-y-3">
              <label className="text-xs font-medium text-slate-300">Product Photograph (Storefront Image)</label>
              <div className="grid grid-cols-5 gap-2">
                {PRESET_IMAGES.slice(0, 5).map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setImageUrl(preset.url)}
                    className={`group relative rounded-lg overflow-hidden aspect-[4/5] border transition-all ${
                      imageUrl === preset.url
                        ? "border-blue-500 ring-2 ring-blue-500/40"
                        : "border-slate-800 opacity-60 hover:opacity-100"
                    }`}
                  >
                    <img src={preset.url} alt={preset.label} className="w-full h-full object-cover" />
                    <span className="absolute inset-x-0 bottom-0 bg-slate-950/80 text-[9px] text-slate-200 py-0.5 truncate px-1 text-center">
                      {preset.label.split(" ")[0]}
                    </span>
                  </button>
                ))}
              </div>
              <input
                type="url"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="Or paste custom image URL..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Description */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Design Story & Details</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Production Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm rounded-xl shadow-xl shadow-blue-500/25 transition-all flex items-center justify-center gap-2.5 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Producing, Stocking & Training RAG...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-blue-200" />
                    Produce & Publish to Storefront Website
                  </>
                )}
              </button>
              <p className="text-[11px] text-center text-slate-500 mt-2">
                Instantly reserves warehouse stock and embeds product specs into RAG knowledge.
              </p>
            </div>
          </form>

          {/* RIGHT: Real-Time Live Preview (5 Cols) */}
          <div className="lg:col-span-5 sticky top-8 space-y-4">
            <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-2 rounded-xl">
              <div className="flex items-center gap-2 text-xs font-semibold text-white pl-2">
                <Eye className="w-4 h-4 text-blue-400" /> Live Storefront Rendering
              </div>
              <div className="flex items-center bg-slate-950 rounded-lg p-1 border border-slate-800">
                <button
                  type="button"
                  onClick={() => setPreviewMode("card")}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    previewMode === "card"
                      ? "bg-blue-600 text-white"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Card View
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewMode("detail")}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    previewMode === "detail"
                      ? "bg-blue-600 text-white"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Detail View
                </button>
              </div>
            </div>

            {/* PREVIEW: STOREFRONT CARD VIEW */}
            {previewMode === "card" && (
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl transition-all group max-w-sm mx-auto">
                {/* Product Image Box with 3:4 Aspect Ratio */}
                <div className="relative aspect-[3/4] bg-slate-950 overflow-hidden">
                  <img
                    src={imageUrl}
                    alt={name}
                    className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                  />

                  {/* Badges Overlay */}
                  <div className="absolute top-3 left-3 flex flex-col gap-1.5 items-start">
                    {featuredBadge !== "None" && (
                      <span className="px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider rounded-md bg-slate-900/90 backdrop-blur-md text-amber-400 border border-amber-500/30 shadow-lg">
                        {featuredBadge}
                      </span>
                    )}
                    {discountPercent > 0 && (
                      <span className="px-2 py-0.5 text-[10px] font-black rounded-md bg-rose-600 text-white shadow-md">
                        -{discountPercent}% OFF
                      </span>
                    )}
                  </div>

                  {/* Stock & Gender Tag */}
                  <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[10px] font-medium text-white/90">
                    <span className="px-2 py-1 rounded-md bg-slate-950/80 backdrop-blur-md border border-white/10 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      In Stock ({selectedSizes.length * initialStock} units)
                    </span>
                    <span className="px-2 py-1 rounded-md bg-slate-950/80 backdrop-blur-md border border-white/10 uppercase font-bold text-slate-300">
                      {gender}
                    </span>
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                    <span>UrbanThread • {category}</span>
                    <span className="font-mono text-[10px] text-slate-500">{sku}</span>
                  </div>

                  <h3 className="font-bold text-sm text-white line-clamp-1 group-hover:text-blue-400 transition-colors">
                    {name || "Untitled Product"}
                  </h3>

                  <p className="text-[11px] text-slate-400 line-clamp-1">
                    {material || "Premium Handcrafted Apparel"}
                  </p>

                  {/* Sizing & Color Chips */}
                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                    <div className="flex items-center gap-1">
                      {selectedSizes.map((s) => (
                        <span key={s} className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-slate-300">
                          {s}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                      <span
                        className="w-2.5 h-2.5 rounded-full border border-slate-600"
                        style={{ backgroundColor: QUICK_COLORS.find(c => c.name === color)?.hex || "#3b82f6" }}
                      />
                      {color}
                    </div>
                  </div>

                  {/* Price & Action */}
                  <div className="pt-2 flex items-center justify-between border-t border-slate-800">
                    <div>
                      <div className="flex items-baseline gap-2">
                        <span className="text-base font-extrabold text-white">₹{salePrice.toLocaleString("en-IN")}</span>
                        {discountPercent > 0 && (
                          <span className="text-xs text-slate-500 line-through font-medium">
                            ₹{basePrice.toLocaleString("en-IN")}
                          </span>
                        )}
                      </div>
                      <span className="text-[9px] text-emerald-400 font-medium">Free express courier</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
                        title="Quick View Details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        className="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors flex items-center gap-1 shadow-md shadow-blue-500/20"
                      >
                        <ShoppingBag className="w-3.5 h-3.5" /> Buy
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* PREVIEW: STOREFRONT DETAIL MODAL VIEW */}
            {previewMode === "detail" && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-2xl max-w-sm mx-auto text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-16 h-20 rounded-lg overflow-hidden bg-slate-950 shrink-0">
                    <img src={imageUrl} alt={name} className="w-full h-full object-cover" />
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-blue-400">{category}</span>
                    <h4 className="font-bold text-white text-sm leading-snug">{name}</h4>
                    <div className="text-emerald-400 font-extrabold text-sm mt-0.5">
                      ₹{salePrice.toLocaleString("en-IN")}{" "}
                      <span className="text-slate-500 line-through text-xs font-normal">
                        ₹{basePrice.toLocaleString("en-IN")}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-slate-800">
                  <div className="font-semibold text-slate-300">Fabric & Material Science</div>
                  <p className="text-slate-400 text-[11px] leading-relaxed">{material}</p>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-slate-800">
                  <div className="font-semibold text-slate-300">Wash & Longevity Instructions</div>
                  <p className="text-slate-400 text-[11px] leading-relaxed">{careInstructions}</p>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-[11px]">
                  <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">Return Window</span>
                    <span className="font-bold text-white flex items-center gap-1">
                      <RotateCcw className="w-3 h-3 text-emerald-400" /> 14 Days Free
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">Dispatch Hub</span>
                    <span className="font-bold text-white flex items-center gap-1">
                      <Truck className="w-3 h-3 text-blue-400" /> Mumbai WH-01
                    </span>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-indigo-300 text-[11px] flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
                  <span>Aria AI knows this item's sizing and fabric specifications.</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
