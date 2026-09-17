"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  ShoppingBag,
  Sparkles,
  CheckCircle2,
  Calendar,
  Clock,
  Truck,
  RotateCcw,
  Tag,
  ShieldCheck,
  ChevronRight,
  User,
  ArrowRight,
  Package,
  Layers,
  AlertCircle,
  HelpCircle,
  Scissors,
  Check,
  CreditCard,
  MapPin,
  Bot,
  Send,
  Headphones,
  BookOpen,
  MessageSquare,
  Search,
  Filter,
  ArrowLeft,
  Star,
  Eye,
  Info,
  X,
  RefreshCw,
  SlidersHorizontal,
  Ruler
} from "lucide-react";
import { api } from "@/lib/api";

interface ProductItem {
  id: string;
  name: string;
  category: string;
  subCategory: string;
  gender?: "MEN" | "WOMEN" | "UNISEX";
  basePrice: number;
  salePrice: number;
  description: string;
  fabricCare: string;
  material?: string;
  image: string;
  colors: string[];
  sizes: string[];
  sku: string;
  availableStock: number;
  featuredBadge?: string;
  rating?: number;
  reviewsCount?: number;
}

const MASTER_CLOTHING_CATALOG: ProductItem[] = [
  // --- T-SHIRTS VARIETY ---
  {
    id: "prod-tee-01",
    name: "Classic Organic Cotton Crewneck Tee",
    category: "T-Shirts",
    subCategory: "Men's T-Shirts",
    gender: "MEN",
    basePrice: 1299,
    salePrice: 999,
    description: "Combed 220 GSM ring-spun organic cotton with reinforced ribbed collar. Breathable everyday luxury.",
    fabricCare: "Machine wash cold (below 30°C). Air dry in shade. Do not tumble dry high.",
    material: "100% GOTS Organic Cotton • 220 GSM",
    image: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80",
    colors: ["Jet Black", "Chalk White", "Vintage Navy"],
    sizes: ["S", "M", "L", "XL", "XXL"],
    sku: "UT-TSH-001",
    availableStock: 52,
    featuredBadge: "Best Seller",
    rating: 4.9,
    reviewsCount: 88
  },
  {
    id: "prod-tee-02",
    name: "Eco-Blend Heavyweight Boxy Tee",
    category: "T-Shirts",
    subCategory: "T-Shirts",
    gender: "UNISEX",
    basePrice: 1499,
    salePrice: 1199,
    description: "260 GSM structured streetwear drop-shoulder fit. Ultra-durable preshrunk cotton weave.",
    fabricCare: "Gentle machine wash with mild liquid detergent. Hang dry inside out.",
    material: "100% Recycled Long-Staple Cotton • 260 GSM",
    image: "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&auto=format&fit=crop&q=80",
    colors: ["Sage Green", "Raw Ecru", "Charcoal Grey"],
    sizes: ["XS", "S", "M", "L", "XL"],
    sku: "UT-TSH-003",
    availableStock: 44,
    featuredBadge: "Trending",
    rating: 4.8,
    reviewsCount: 64
  },
  {
    id: "prod-tee-03",
    name: "Slub Cotton Button Henley Tee",
    category: "T-Shirts",
    subCategory: "Men's T-Shirts",
    gender: "MEN",
    basePrice: 1399,
    salePrice: 1099,
    description: "Textured slub knit with authentic wooden button placket. Relaxed coastal styling.",
    fabricCare: "Hand or machine wash cold on delicate cycle. Low heat reverse iron.",
    material: "100% Slub Yarn Combed Cotton",
    image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&auto=format&fit=crop&q=80",
    colors: ["Earth Brown", "Off-White", "Washed Indigo"],
    sizes: ["S", "M", "L", "XL"],
    sku: "UT-TSH-002",
    availableStock: 36,
    rating: 4.7,
    reviewsCount: 32
  },

  // --- CASUAL SHIRTS VARIETY ---
  {
    id: "prod-shirt-01",
    name: "Relaxed French Linen Camp Shirt",
    category: "Casual Shirts",
    subCategory: "Men's Casual Shirts",
    gender: "MEN",
    basePrice: 3199,
    salePrice: 2499,
    description: "100% Normandy flax linen with Cuban camp collar and coconut shell buttons. Natural cooling.",
    fabricCare: "Gentle machine wash cold. Iron while slightly damp or steam on high for a natural relaxed texture.",
    material: "100% European Flax Linen • 160 GSM",
    image: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800&auto=format&fit=crop&q=80",
    colors: ["Natural Sand", "Sky Chambray", "Olive Leaf"],
    sizes: ["S", "M", "L", "XL"],
    sku: "UT-SHR-001",
    availableStock: 28,
    featuredBadge: "Sustainable",
    rating: 4.9,
    reviewsCount: 76
  },
  {
    id: "prod-shirt-02",
    name: "Classic Oxford Cloth Button-Down",
    category: "Casual Shirts",
    subCategory: "Men's Casual Shirts",
    gender: "MEN",
    basePrice: 2599,
    salePrice: 1999,
    description: "Heavyweight pinpoint Oxford basket-weave with roll collar and single chest pocket. Timeless sartorial staple.",
    fabricCare: "Warm machine wash. Medium tumble dry or hang dry. Crisp warm iron.",
    material: "100% Combed Two-Ply Oxford Cotton",
    image: "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800&auto=format&fit=crop&q=80",
    colors: ["Ice Blue", "Optic White", "Candy Stripe"],
    sizes: ["S", "M", "L", "XL", "XXL"],
    sku: "UT-SHR-002",
    availableStock: 40,
    featuredBadge: "Workwear",
    rating: 4.8,
    reviewsCount: 52
  },
  {
    id: "prod-shirt-03",
    name: "Band Collar Indigo Chambray Shirt",
    category: "Casual Shirts",
    subCategory: "Men's Casual Shirts",
    gender: "MEN",
    basePrice: 2899,
    salePrice: 2299,
    description: "Natural indigo dyed lightweight chambray with mandarin band collar. Hand-finished contrast gussets.",
    fabricCare: "Wash separately for first 3 washes due to natural indigo. Cold gentle wash.",
    material: "100% Indigo Weft Cotton Chambray",
    image: "https://images.unsplash.com/photo-1603252109303-2751441dd157?w=800&auto=format&fit=crop&q=80",
    colors: ["Indigo Rinse", "Washed Blue"],
    sizes: ["S", "M", "L", "XL"],
    sku: "UT-SHR-003",
    availableStock: 22,
    rating: 4.7,
    reviewsCount: 29
  },

  // --- DENIM & JEANS VARIETY ---
  {
    id: "prod-denim-01",
    name: "Japanese Selvedge Raw Denim Slim Jeans",
    category: "Denim & Jeans",
    subCategory: "Men's Denim Jeans",
    gender: "MEN",
    basePrice: 4999,
    salePrice: 3999,
    description: "13.5 oz shuttle-loom red-line selvedge denim from Okayama. Rigid unwashed indigo that molds to your silhouette.",
    fabricCare: "Wear raw for first 4-6 months before initial soak. Wash inside out in cold water with woolite dark.",
    material: "100% Shuttle Loom Cotton Selvedge (13.5 oz)",
    image: "https://images.unsplash.com/photo-1542272604-780c96856592?w=800&auto=format&fit=crop&q=80",
    colors: ["Raw Deep Indigo"],
    sizes: ["30", "32", "34", "36"],
    sku: "UT-JNS-001",
    availableStock: 19,
    featuredBadge: "Artisan Denim",
    rating: 5.0,
    reviewsCount: 47
  },
  {
    id: "prod-denim-02",
    name: "Tapered Comfort Stretch Jeans",
    category: "Denim & Jeans",
    subCategory: "Men's Denim Jeans",
    gender: "MEN",
    basePrice: 2999,
    salePrice: 2299,
    description: "11.5 oz cotton denim with 2% elastane flex. Vintage stone wash with whiskering at the hips.",
    fabricCare: "Machine wash cold inside out. Tumble dry low or air dry.",
    material: "98% Cotton, 2% Spandex Stretch Denim",
    image: "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&auto=format&fit=crop&q=80",
    colors: ["Medium Vintage Wash", "Washed Black"],
    sizes: ["30", "32", "34", "36"],
    sku: "UT-JNS-002",
    availableStock: 38,
    rating: 4.7,
    reviewsCount: 65
  },
  {
    id: "prod-denim-03",
    name: "Relaxed Utility Carpenter Denim",
    category: "Denim & Jeans",
    subCategory: "Men's Denim Jeans",
    gender: "UNISEX",
    basePrice: 3499,
    salePrice: 2799,
    description: "Relaxed straight silhouette with hammer loop, utility ruler pocket, and triple-stitched felled seams.",
    fabricCare: "Machine wash cold with similar colors. Air dry.",
    material: "100% Heavy Duty Cotton Bull Denim",
    image: "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=800&auto=format&fit=crop&q=80",
    colors: ["Off-White Carpenter", "Stonewash Indigo"],
    sizes: ["28", "30", "32", "34", "36"],
    sku: "UT-JNS-003",
    availableStock: 25,
    featuredBadge: "Streetwear",
    rating: 4.8,
    reviewsCount: 39
  },

  // --- OUTERWEAR & JACKETS ---
  {
    id: "prod-jkt-01",
    name: "Urban Classic Denim Trucker Jacket",
    category: "Outerwear & Jackets",
    subCategory: "Outerwear",
    gender: "UNISEX",
    basePrice: 4299,
    salePrice: 3499,
    description: "Type III trucker design with brass shank buttons, adjustable waist tabs, and welt hand pockets.",
    fabricCare: "Cold machine wash inside out. Air dry in shade. Low-heat iron on reverse.",
    material: "100% Cotton 12.5 oz Denim",
    image: "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&auto=format&fit=crop&q=80",
    colors: ["Vintage Indigo", "Washed Charcoal"],
    sizes: ["S", "M", "L", "XL"],
    sku: "UT-JKT-001",
    availableStock: 28,
    featuredBadge: "Best Seller",
    rating: 4.9,
    reviewsCount: 112
  },
  {
    id: "prod-jkt-02",
    name: "Oversized Brushed Fleece Hoodie",
    category: "Outerwear & Jackets",
    subCategory: "Outerwear",
    gender: "UNISEX",
    basePrice: 3199,
    salePrice: 2499,
    description: "380 GSM ultra-cozy heavyweight French terry fleece with kangaroo pocket and double-layered drawstring hood.",
    fabricCare: "Machine wash cold on gentle cycle. Wash with similar colors. Do not dry clean.",
    material: "85% Organic Cotton, 15% Poly Fleece • 380 GSM",
    image: "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&auto=format&fit=crop&q=80",
    colors: ["Heather Grey", "Muted Lavender", "Jet Black"],
    sizes: ["S", "M", "L", "XL"],
    sku: "UT-HOD-001",
    availableStock: 42,
    featuredBadge: "Trending",
    rating: 4.8,
    reviewsCount: 94
  },
  {
    id: "prod-jkt-03",
    name: "Reversible Minimalist Bomber Jacket",
    category: "Outerwear & Jackets",
    subCategory: "Outerwear",
    gender: "MEN",
    basePrice: 4699,
    salePrice: 3899,
    description: "Water-resistant matte nylon shell reversing to quilted diamond insulator. Ribbed baseball collar.",
    fabricCare: "Dry clean recommended or gentle cold sponge wash.",
    material: "Water-Repellent Poly Shell + Recycled Polyfill",
    image: "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&auto=format&fit=crop&q=80",
    colors: ["Midnight Olive", "Obsidian Black"],
    sizes: ["M", "L", "XL"],
    sku: "UT-JKT-002",
    availableStock: 16,
    featuredBadge: "Winter Drop",
    rating: 4.9,
    reviewsCount: 41
  },

  // --- DRESSES & WOMEN'S TOPS ---
  {
    id: "prod-drs-01",
    name: "Aria Silk Wrap Maxi Dress",
    category: "Dresses & Tops",
    subCategory: "Women's Dresses",
    gender: "WOMEN",
    basePrice: 5499,
    salePrice: 4299,
    description: "Fluid cruelty-free vegan silk with adjustable waist tie and subtle side slit. Graceful drape for evening events.",
    fabricCare: "Dry clean or delicate hand wash in cold water with silk-safe detergent. Never wring or twist.",
    material: "100% Vegan Mulberry Silk & Cupro",
    image: "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&auto=format&fit=crop&q=80",
    colors: ["Emerald Jewel", "Black Rose", "Sunset Ochre"],
    sizes: ["XS", "S", "M", "L"],
    sku: "UT-DRS-001",
    availableStock: 12,
    featuredBadge: "Limited Edition",
    rating: 4.9,
    reviewsCount: 68
  },
  {
    id: "prod-drs-02",
    name: "Tiered Botanical Floral Midi Dress",
    category: "Dresses & Tops",
    subCategory: "Women's Dresses",
    gender: "WOMEN",
    basePrice: 3599,
    salePrice: 2799,
    description: "Tiered lightweight cotton voile with hand-block botanical print and smocked bodice for a forgiving fit.",
    fabricCare: "Machine wash cold with mild detergent. Line dry in shade.",
    material: "100% Pure Indian Cotton Voile",
    image: "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=800&auto=format&fit=crop&q=80",
    colors: ["Botanical Sage", "Terracotta Blossom"],
    sizes: ["XS", "S", "M", "L", "XL"],
    sku: "UT-DRS-002",
    availableStock: 24,
    featuredBadge: "Floral Collection",
    rating: 4.8,
    reviewsCount: 55
  },
  {
    id: "prod-drs-03",
    name: "Wrap Linen Belted Shirt Dress",
    category: "Dresses & Tops",
    subCategory: "Women's Dresses",
    gender: "WOMEN",
    basePrice: 4199,
    salePrice: 3299,
    description: "Breathable pure linen tailored with utility chest pockets and a wide tie belt. Smart work-to-weekend styling.",
    fabricCare: "Cold gentle machine cycle. Steam on reverse for soft drape.",
    material: "100% European Flax Linen",
    image: "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=800&auto=format&fit=crop&q=80",
    colors: ["Crisp Chalk", "Olive Drab", "Midnight Navy"],
    sizes: ["S", "M", "L"],
    sku: "UT-DRS-003",
    availableStock: 18,
    rating: 4.7,
    reviewsCount: 38
  },

  // --- BOTTOMS & CHINOS ---
  {
    id: "prod-chn-01",
    name: "Structured Pleated Chino Trousers",
    category: "Bottoms & Chinos",
    subCategory: "Bottoms",
    gender: "MEN",
    basePrice: 2699,
    salePrice: 1999,
    description: "Clean tapered silhouette with elastane flex. Water-repellent finish for unpredictable monsoon weather.",
    fabricCare: "Machine wash cold with similar darks. Turn inside out. Hang dry to maintain sharp front pleats.",
    material: "97% Twill Cotton, 3% Elastane",
    image: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800&auto=format&fit=crop&q=80",
    colors: ["Khaki Stone", "Navy Blue", "Dark Olive"],
    sizes: ["30", "32", "34", "36"],
    sku: "UT-CHN-001",
    availableStock: 34,
    rating: 4.8,
    reviewsCount: 49
  },
  {
    id: "prod-chn-02",
    name: "Relaxed Drawstring Linen Trousers",
    category: "Bottoms & Chinos",
    subCategory: "Bottoms",
    gender: "UNISEX",
    basePrice: 2799,
    salePrice: 2199,
    description: "Elasticated drawstring waistband with wide straight leg. Breezy linen drape for humid coastal heat.",
    fabricCare: "Cold gentle wash. Air dry flat.",
    material: "100% Pure Flax Linen",
    image: "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800&auto=format&fit=crop&q=80",
    colors: ["Raw Ecru", "Deep Charcoal"],
    sizes: ["S", "M", "L", "XL"],
    sku: "UT-CHN-003",
    availableStock: 26,
    featuredBadge: "Summer Breeze",
    rating: 4.9,
    reviewsCount: 42
  },

  // --- ACCESSORIES ---
  {
    id: "prod-tote-01",
    name: "Minimalist Vegan Leather Tote",
    category: "Accessories",
    subCategory: "Bags & Totes",
    gender: "UNISEX",
    basePrice: 3999,
    salePrice: 3199,
    description: "Supple water-resistant microfiber vegan leather with 15-inch laptop compartment and magnetic closure.",
    fabricCare: "Wipe clean with a damp microfiber cloth. Store in provided dust bag when not in use.",
    material: "Cruelty-Free Microfiber Vegan Leather",
    image: "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&auto=format&fit=crop&q=80",
    colors: ["Cognac Tan", "Obsidian Black", "Olive Suede"],
    sizes: ["One Size (18L)"],
    sku: "UT-BAG-001",
    availableStock: 25,
    featuredBadge: "Cruelty Free",
    rating: 4.9,
    reviewsCount: 56
  },
  {
    id: "prod-scarf-01",
    name: "Fine Merino Wool Knit Scarf",
    category: "Accessories",
    subCategory: "Winterwear",
    gender: "UNISEX",
    basePrice: 2299,
    salePrice: 1799,
    description: "100% pure Australian superfine merino wool. Ribbed texture with natural thermal regulation.",
    fabricCare: "Hand wash in cool water with wool-detergent. Lay flat on towel to dry. Do not hang.",
    material: "100% Australian Superfine Merino Wool",
    image: "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=800&auto=format&fit=crop&q=80",
    colors: ["Oatmeal Cream", "Slate Heather", "Burgundy Wine"],
    sizes: ["One Size (180x40cm)"],
    sku: "UT-SCF-001",
    availableStock: 30,
    rating: 4.8,
    reviewsCount: 33
  }
];

interface ChatMessage {
  id: string;
  sender_type: "CUSTOMER" | "AI_AGENT" | "SYSTEM";
  content: string;
  message_type?: string;
  metadata?: any;
  created_at: string;
}

export default function StorefrontPage() {
  const [activeTab, setActiveTab] = useState<"shop" | "order" | "concierge" | "fitting" | "returns">("shop");
  const [catalog, setCatalog] = useState<ProductItem[]>(MASTER_CLOTHING_CATALOG);
  const [isLoadingCatalog, setIsLoadingCatalog] = useState<boolean>(false);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedGender, setSelectedGender] = useState<"ALL" | "MEN" | "WOMEN" | "UNISEX">("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"featured" | "price-asc" | "price-desc" | "rating">("featured");

  const [selectedProduct, setSelectedProduct] = useState<ProductItem>(MASTER_CLOTHING_CATALOG[0]);
  const [selectedSize, setSelectedSize] = useState<string>("M");
  const [selectedColor, setSelectedColor] = useState<string>(MASTER_CLOTHING_CATALOG[0].colors[0] || "Standard");
  const [quantity, setQuantity] = useState<number>(1);

  // Quick View & Sizing Matrix Modals
  const [quickViewProduct, setQuickViewProduct] = useState<ProductItem | null>(null);
  const [showSizingModal, setShowSizingModal] = useState<boolean>(false);

  // Cart & Order Booking State
  const [couponCode, setCouponCode] = useState<string>("");
  const [discountPercent, setDiscountPercent] = useState<number>(0);
  const [couponMessage, setCouponMessage] = useState<string>("");
  const [customerName, setCustomerName] = useState<string>("Rahul Sharma");
  const [customerAddress, setCustomerAddress] = useState<string>("Flat 402, Sea Breeze Heights, Bandra West, Mumbai 400050");
  const [paymentMethod, setPaymentMethod] = useState<string>("UPI");
  const [isOrdering, setIsOrdering] = useState<boolean>(false);
  const [confirmedOrder, setConfirmedOrder] = useState<any | null>(null);

  // Chatbot Concierge State
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>("");
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const [chatSuggestions, setChatSuggestions] = useState<string[]>([]);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Try-At-Home Appointment Booking State
  const [appointmentDate, setAppointmentDate] = useState<string>("2026-09-12");
  const [appointmentTime, setAppointmentTime] = useState<string>("14:00 - 16:00 (Afternoon)");
  const [fittingBooked, setFittingBooked] = useState<boolean>(false);

  // Return Pickup Booking State
  const [returnOrderId, setReturnOrderId] = useState<string>("ORD-DEMO-01-NORM");
  const [returnReason, setReturnReason] = useState<string>("Size slightly too tight in shoulders");
  const [pickupDate, setPickupDate] = useState<string>("2026-09-11");
  const [returnBooked, setReturnBooked] = useState<boolean>(false);

  // Fetch Public Catalog from Backend
  const loadPublicCatalog = async () => {
    try {
      setIsLoadingCatalog(true);
      const res = await fetch("http://localhost:8000/api/v1/products/public");
      if (res.ok) {
        const data = await res.json();
        const rawList = Array.isArray(data) ? data : (data.data || data.items || []);
        if (rawList.length > 0) {
          const normalizeCategory = (cat: string, name: string): string => {
            const c = (cat || "").toLowerCase();
            const n = (name || "").toLowerCase();
            if (c.includes("t-shirt") || n.includes("t-shirt") || n.includes("tee") || n.includes("henley")) return "T-Shirts";
            if (c.includes("casual shirt") || c.includes("shirt") || n.includes("shirt") || n.includes("oxford") || n.includes("chambray")) return "Casual Shirts";
            if (c.includes("denim") || c.includes("jean") || n.includes("denim") || n.includes("jean") || n.includes("carpenter")) return "Denim & Jeans";
            if (c.includes("jacket") || c.includes("outerwear") || c.includes("coat") || c.includes("blazer") || n.includes("jacket") || n.includes("coat") || n.includes("parka") || n.includes("bomber")) return "Outerwear & Jackets";
            if (c.includes("dress") || c.includes("top") || c.includes("blouse") || n.includes("dress") || n.includes("top") || n.includes("blouse") || n.includes("wrap")) return "Dresses & Tops";
            if (c.includes("bottom") || c.includes("chino") || c.includes("pant") || c.includes("short") || c.includes("trouser") || n.includes("chino") || n.includes("trouser") || n.includes("short")) return "Bottoms & Chinos";
            if (c.includes("accessor") || c.includes("bag") || c.includes("scarf") || n.includes("bag") || n.includes("scarf") || n.includes("tote") || n.includes("backpack")) return "Accessories";
            return "T-Shirts";
          };

          const mapped: ProductItem[] = rawList.map((p: any) => ({
            id: p.id,
            name: p.name,
            category: normalizeCategory(p.category, p.name),
            subCategory: p.category || p.sub_category || "Apparel",
            gender: (p.gender || "UNISEX") as "MEN" | "WOMEN" | "UNISEX",
            basePrice: p.base_price || p.price || 1999,
            salePrice: p.sale_price || p.price || p.base_price || 1499,
            description: p.description || "",
            fabricCare: p.care_instructions || p.fabric_care || "Machine wash cold inside out. Air dry in shade.",
            material: p.material || "100% Cotton",
            image: p.image_url || p.image || "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80",
            colors: p.colors && p.colors.length > 0 ? p.colors : [p.color || "Classic"],
            sizes: p.sizes && p.sizes.length > 0 ? p.sizes : ["S", "M", "L", "XL"],
            sku: p.sku,
            availableStock: p.total_stock ?? p.stock_level ?? 25,
            featuredBadge: p.featured_badge || (p.discount_percent > 15 ? `${p.discount_percent}% OFF` : undefined),
            rating: p.rating || 4.8,
            reviewsCount: p.reviews_count || 42
          }));

          const apiSkus = new Set(mapped.map((m) => m.sku));
          const combined = [
            ...mapped,
            ...MASTER_CLOTHING_CATALOG.filter((m) => !apiSkus.has(m.sku))
          ];
          setCatalog(combined);
        }
      }
    } catch (err) {
      console.warn("Using offline master clothing catalog fallback", err);
    } finally {
      setIsLoadingCatalog(false);
    }
  };

  useEffect(() => {
    loadPublicCatalog();
  }, []);

  // Load existing active order from localStorage if available
  useEffect(() => {
    try {
      const stored = localStorage.getItem("urbanthread_active_order");
      if (stored) {
        const parsed = JSON.parse(stored);
        setConfirmedOrder(parsed);
      }
    } catch (e) {}
  }, []);

  // Update selected size when product changes
  useEffect(() => {
    if (selectedProduct?.sizes && selectedProduct.sizes.length > 0) {
      setSelectedSize(selectedProduct.sizes[0]);
    }
    if (selectedProduct?.colors && selectedProduct.colors.length > 0) {
      setSelectedColor(selectedProduct.colors[0]);
    }
  }, [selectedProduct]);

  // Scroll chat to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatLoading]);

  // Real-time calculations
  const subtotal = selectedProduct.salePrice * quantity;
  const discountAmount = Math.round((subtotal * discountPercent) / 100);
  const taxableAmount = subtotal - discountAmount;
  const tax = Math.round(taxableAmount * 0.12); // 12% GST
  const shippingFee = taxableAmount >= 999 ? 0 : 100;
  const grandTotal = taxableAmount + tax + shippingFee;

  const handleApplyCoupon = () => {
    const code = couponCode.trim().toUpperCase();
    if (code === "URBAN10") {
      setDiscountPercent(10);
      setCouponMessage("✓ 10% First Order discount applied!");
    } else if (code === "THREAD20") {
      if (subtotal >= 2499) {
        setDiscountPercent(20);
        setCouponMessage("✓ 20% Mega Fashion discount applied!");
      } else {
        setCouponMessage("❌ THREAD20 requires a minimum order value of ₹2,499.");
      }
    } else {
      setDiscountPercent(0);
      setCouponMessage("❌ Invalid promotional coupon code.");
    }
  };

  // Start Personalized AI Chat Session
  const initPersonalizedChat = async (orderInfo: any) => {
    try {
      setChatLoading(true);
      const res = await api.customer.startConversation({
        channel: "WEBSITE_CHAT",
        customer_id: "cust-001",
        organization_slug: "urbanthread",
        order_details: {
          order_number: orderInfo.orderNumber,
          product_name: orderInfo.productName,
          sku: orderInfo.sku || selectedProduct.sku,
          size: orderInfo.size,
          color: orderInfo.color,
          quantity: orderInfo.quantity,
          total: orderInfo.total,
          carrier: orderInfo.carrier,
          tracking_number: orderInfo.trackingNumber,
          delivery_eta: orderInfo.deliveryEta,
          customer_name: orderInfo.customerName,
          fabric_care: selectedProduct.fabricCare
        }
      });

      const data = res?.data || res;
      setConversationId(data.conversation_id);
      if (data.suggested_actions) {
        setChatSuggestions(data.suggested_actions);
      }
      setChatMessages([
        {
          id: "init-msg",
          sender_type: "AI_AGENT",
          message_type: "GREETING",
          content: data.greeting || `Hello ${orderInfo.customerName}! 🎉 I'm Aria, your personal UrbanThread assistant. I see you've booked the ${orderInfo.productName} (Size ${orderInfo.size}, ${orderInfo.color}) under Order #${orderInfo.orderNumber}. How can I assist you with your delivery, fabric care, or return policy today?`,
          created_at: new Date().toISOString()
        }
      ]);
    } catch (err: any) {
      // Offline fallback
      setChatMessages([
        {
          id: "init-fallback",
          sender_type: "AI_AGENT",
          content: `Hello ${orderInfo.customerName}! 🎉 Congratulations on booking the **${orderInfo.productName} (Size: ${orderInfo.size}, ${orderInfo.color})** under Order **#${orderInfo.orderNumber}**!\n\nI'm Aria, your dedicated UrbanThread concierge. I have your order details loaded right here. Ask me anything about your package tracking, fabric wash care, sizing, or 30-day returns!`,
          created_at: new Date().toISOString()
        }
      ]);
      setChatSuggestions([
        `Where is my ${orderInfo.productName} right now?`,
        `Wash & care instructions for ${orderInfo.productName}`,
        `What is the return window for #${orderInfo.orderNumber}?`,
        `Can I exchange size ${orderInfo.size} if it doesn't fit?`
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handlePlaceOrder = async () => {
    setIsOrdering(true);
    try {
      const newOrderNumber = "ORD-" + Math.floor(100000 + Math.random() * 900000);
      const trackingNumber = "BD-URB-" + Math.floor(10000000 + Math.random() * 90000000);

      const confirmed = {
        orderNumber: newOrderNumber,
        trackingNumber: trackingNumber,
        carrier: "BlueDart Express Courier",
        productName: selectedProduct.name,
        sku: selectedProduct.sku,
        category: selectedProduct.category,
        subCategory: selectedProduct.subCategory,
        image: selectedProduct.image,
        size: selectedSize,
        color: selectedColor,
        quantity: quantity,
        unitPrice: selectedProduct.salePrice,
        subtotal: subtotal,
        discount: discountAmount,
        total: grandTotal,
        customerName: customerName,
        customerAddress: customerAddress,
        deliveryEta: "Within 2-4 business days (Mumbai Fulfillment Hub)",
        fabricCare: selectedProduct.fabricCare,
        timestamp: new Date().toISOString()
      };

      setConfirmedOrder(confirmed);
      try {
        localStorage.setItem("urbanthread_active_order", JSON.stringify(confirmed));
      } catch (e) {}

      // Automatically transition to the dedicated Concierge Chatbot mode!
      setActiveTab("concierge");
      await initPersonalizedChat(confirmed);
    } catch (err: any) {
      alert("Order booking failed: " + err.message);
    } finally {
      setIsOrdering(false);
    }
  };

  const handleSendChatMessage = async (textToSend?: string) => {
    const text = (textToSend || chatInput).trim();
    if (!text || chatLoading) return;

    setChatInput("");

    const userMsg: ChatMessage = {
      id: "u-" + Date.now(),
      sender_type: "CUSTOMER",
      content: text,
      created_at: new Date().toISOString()
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);

    try {
      let activeId = conversationId;
      if (!activeId && confirmedOrder) {
        const res = await api.customer.startConversation({
          channel: "WEBSITE_CHAT",
          customer_id: "cust-001",
          organization_slug: "urbanthread",
          order_details: confirmedOrder
        });
        activeId = res?.data?.conversation_id || res?.conversation_id;
        setConversationId(activeId);
      }

      if (!activeId) {
        throw new Error("Chat session unavailable");
      }

      const res = await api.customer.sendMessage(activeId, text);
      const data = res?.data || res || {};

      const aiMsg: ChatMessage = {
        id: "ai-" + Date.now(),
        sender_type: "AI_AGENT",
        message_type: data.message_type || "TEXT",
        content: data.message || data.content || "I am here to assist with your order!",
        metadata: data.card_data || data.metadata || {},
        created_at: new Date().toISOString()
      };

      setChatMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      // Local fallback personalized to ordered product
      const qLower = text.toLowerCase();
      let replyContent = `I am reviewing your order #${confirmedOrder?.orderNumber || "ORD-RECENT"}. How else can I assist you with your ${confirmedOrder?.productName || "item"}?`;
      let citations: any[] = [];

      if (qLower.includes("wash") || qLower.includes("care") || qLower.includes("clean") || qLower.includes("fabric")) {
        replyContent = `Here is the verified care routine for your **${confirmedOrder?.productName}**:\n• **Fabric**: ${confirmedOrder?.fabricCare || "Machine wash cold inside out. Air dry in shade."}\n• Avoid high heat drying to preserve color brilliance and tailored shape.`;
        citations = [{ source: `UrbanThread Care SOP: ${confirmedOrder?.productName}`, confidence: 0.98 }];
      } else if (qLower.includes("where") || qLower.includes("tracking") || qLower.includes("arrive") || qLower.includes("status")) {
        replyContent = `Your **${confirmedOrder?.productName}** (Order **#${confirmedOrder?.orderNumber}**) is packed and scheduled for dispatch via **${confirmedOrder?.carrier}**!\n• **Waybill**: \`${confirmedOrder?.trackingNumber}\`\n• **Estimated Arrival**: ${confirmedOrder?.deliveryEta}`;
        citations = [{ source: "UrbanThread BlueDart Logistics SLA", confidence: 0.97 }];
      } else if (qLower.includes("return") || qLower.includes("exchange") || qLower.includes("refund")) {
        replyContent = `You have a full **30-day return & exchange window** starting from the delivery of your **${confirmedOrder?.productName}**.\n• Keep original tags attached.\n• We provide free doorstep reverse pickup and instant size replacement if Size ${confirmedOrder?.size} needs adjustment!`;
        citations = [{ source: "UrbanThread 30-Day Customer Guarantee", confidence: 0.99 }];
      }

      const aiMsg: ChatMessage = {
        id: "ai-fallback-" + Date.now(),
        sender_type: "AI_AGENT",
        content: replyContent,
        metadata: { citations },
        created_at: new Date().toISOString()
      };
      setChatMessages((prev) => [...prev, aiMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  const filteredProducts = catalog
    .filter((p) => {
      if (selectedCategory !== "ALL" && p.category !== selectedCategory) return false;
      if (selectedGender !== "ALL" && p.gender && p.gender !== "UNISEX" && p.gender !== selectedGender) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = p.name.toLowerCase().includes(q);
        const matchCat = p.category.toLowerCase().includes(q) || (p.subCategory || "").toLowerCase().includes(q);
        const matchDesc = (p.description || "").toLowerCase().includes(q);
        const matchMat = (p.material || "").toLowerCase().includes(q);
        const matchSku = (p.sku || "").toLowerCase().includes(q);
        if (!matchName && !matchCat && !matchDesc && !matchMat && !matchSku) return false;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "price-asc") return a.salePrice - b.salePrice;
      if (sortBy === "price-desc") return b.salePrice - a.salePrice;
      if (sortBy === "rating") return (b.rating || 0) - (a.rating || 0);
      return 0;
    });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-600 to-purple-700 text-white text-xs font-semibold py-2 px-4 text-center tracking-wide flex items-center justify-center gap-2">
        <Sparkles className="w-3.5 h-3.5" />
        <span>Use code <strong>URBAN10</strong> for 10% off your first order • Free express delivery over ₹999 across India</span>
      </div>

      {/* Main Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button
              onClick={() => setActiveTab("shop")}
              className="flex items-center gap-2.5 text-left focus:outline-none"
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-black text-white text-base shadow-md shadow-blue-500/20">
                UT
              </div>
              <div>
                <span className="font-extrabold text-lg tracking-tight text-white">UrbanThread</span>
                <span className="text-[10px] block -mt-1 text-blue-400 font-medium tracking-wider uppercase">Sustainable Apparel & Lifestyle</span>
              </div>
            </button>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center gap-1.5 ml-4">
              <button
                onClick={() => setActiveTab("shop")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === "shop"
                    ? "bg-blue-600 text-white shadow-sm shadow-blue-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                🛍️ Browse & Book
              </button>

              <button
                onClick={() => {
                  if (confirmedOrder && chatMessages.length === 0) {
                    initPersonalizedChat(confirmedOrder);
                  }
                  setActiveTab("concierge");
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  activeTab === "concierge"
                    ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                <Bot className="w-3.5 h-3.5 text-blue-400" />
                <span>My Booked Order & AI Concierge</span>
                {confirmedOrder && (
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                )}
              </button>

              <button
                onClick={() => setActiveTab("fitting")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === "fitting"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                🧵 Try-At-Home
              </button>

              <button
                onClick={() => setActiveTab("returns")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === "returns"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                🔄 Courier Pickup
              </button>
            </nav>
          </div>

          {/* Right Header Controls */}
          <div className="flex items-center gap-3">
            {confirmedOrder && (
              <button
                onClick={() => {
                  if (chatMessages.length === 0) initPersonalizedChat(confirmedOrder);
                  setActiveTab("concierge");
                }}
                className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full text-xs font-medium hover:bg-emerald-500/20 transition-all"
              >
                <Package className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Active Order:</span>
                <span className="font-bold">#{confirmedOrder.orderNumber}</span>
              </button>
            )}

            <Link
              href="/"
              className="text-[11px] text-slate-400 hover:text-blue-400 border border-slate-800 hover:border-slate-700 px-2.5 py-1 rounded-lg transition-colors"
            >
              Operations Command ↗
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {/* ------------------------------------------------------------- */}
        {/* VIEW: PERSONALIZED CHATBOT & BOOKED ORDER ONLY (USER GOAL)   */}
        {/* ------------------------------------------------------------- */}
        {activeTab === "concierge" && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Header with Switcher */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-white flex items-center gap-2">
                      <span>Aria Personal Order Concierge</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold">
                        Online
                      </span>
                    </h2>
                    <p className="text-xs text-slate-400">
                      Personalized exclusively to your booked UrbanThread items and delivery schedule.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab("shop")}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Book Another Clothing Item</span>
                </button>
              </div>
            </div>

            {/* Main Split: Booked Order Card + Full Interactive Chatbot */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column (5 Cols): Booked Product Specs */}
              <div className="lg:col-span-5 space-y-4">
                {confirmedOrder ? (
                  <div className="bg-slate-900 border border-blue-500/30 rounded-2xl p-5 space-y-4 shadow-xl shadow-blue-900/10">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2">
                        <Package className="w-4 h-4 text-blue-400" />
                        <span className="text-xs font-bold text-white">Booked Order Summary</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                        {confirmedOrder.orderNumber}
                      </span>
                    </div>

                    {/* Product Card */}
                    <div className="flex gap-4 items-start bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                      <img
                        src={confirmedOrder.image || selectedProduct.image}
                        alt={confirmedOrder.productName}
                        className="w-20 h-24 rounded-lg object-cover border border-slate-800 shrink-0"
                      />
                      <div className="flex-1 min-w-0 space-y-1">
                        <span className="text-[10px] font-mono text-blue-400 uppercase tracking-wider block">
                          SKU: {confirmedOrder.sku || selectedProduct.sku}
                        </span>
                        <h4 className="text-sm font-bold text-white truncate">
                          {confirmedOrder.productName}
                        </h4>
                        <div className="text-xs text-slate-400 flex flex-wrap gap-2">
                          <span>Size: <strong className="text-slate-200">{confirmedOrder.size}</strong></span>
                          <span>•</span>
                          <span>Color: <strong className="text-slate-200">{confirmedOrder.color}</strong></span>
                        </div>
                        <div className="text-xs font-bold text-emerald-400 pt-0.5">
                          Total Paid: ₹{confirmedOrder.total}
                        </div>
                      </div>
                    </div>

                    {/* Logistics & Tracking Status */}
                    <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 space-y-2 text-xs">
                      <div className="flex justify-between items-center text-slate-300">
                        <span className="text-slate-400 flex items-center gap-1.5">
                          <Truck className="w-3.5 h-3.5 text-blue-400" />
                          <span>Delivery Carrier:</span>
                        </span>
                        <span className="font-semibold text-white">{confirmedOrder.carrier}</span>
                      </div>
                      <div className="flex justify-between items-center text-slate-300">
                        <span className="text-slate-400">Waybill Tracking:</span>
                        <span className="font-mono text-blue-400 font-bold">{confirmedOrder.trackingNumber}</span>
                      </div>
                      <div className="flex justify-between items-center text-slate-300">
                        <span className="text-slate-400">Estimated Arrival:</span>
                        <span className="font-medium text-amber-300">{confirmedOrder.deliveryEta}</span>
                      </div>
                      <div className="flex justify-between items-center text-slate-300">
                        <span className="text-slate-400">Delivery Address:</span>
                        <span className="text-slate-300 truncate max-w-[180px] text-right" title={confirmedOrder.customerAddress}>
                          {confirmedOrder.customerAddress}
                        </span>
                      </div>
                    </div>

                    {/* Fabric & Policy Perks */}
                    <div className="space-y-2 pt-1">
                      <div className="flex items-center gap-2 text-xs text-slate-300">
                        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>30-Day Hassle-Free Doorstep Return Window</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-300">
                        <RotateCcw className="w-4 h-4 text-blue-400 shrink-0" />
                        <span>Free Size Exchange (Complimentary reverse pickup)</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-300">
                        <Scissors className="w-4 h-4 text-purple-400 shrink-0" />
                        <span>In-Home Stylist Consultation Included</span>
                      </div>
                    </div>

                    {/* Fabric Care Sneak Peek */}
                    {confirmedOrder.fabricCare && (
                      <div className="bg-blue-950/20 border border-blue-900/40 rounded-xl p-3 text-[11px] text-slate-300 space-y-1">
                        <span className="font-semibold text-blue-300 block">🧼 Garment Care Note:</span>
                        <p>{confirmedOrder.fabricCare}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center space-y-4">
                    <ShoppingBag className="w-10 h-10 text-slate-600 mx-auto" />
                    <div>
                      <h4 className="text-sm font-bold text-white">No Booked Order Yet</h4>
                      <p className="text-xs text-slate-400 mt-1">
                        Book a clothing item or accessory from the collection to unlock your personalized AI concierge.
                      </p>
                    </div>
                    <button
                      onClick={() => setActiveTab("shop")}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all"
                    >
                      Browse UrbanThread Collection
                    </button>
                  </div>
                )}
              </div>

              {/* Right Column (7 Cols): Full-Screen Interactive Chatbot */}
              <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[650px] overflow-hidden shadow-2xl">
                {/* Chatbot Header */}
                <div className="bg-slate-950 px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="relative">
                      <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-md">
                        A
                      </div>
                      <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 border-2 border-slate-950 rounded-full"></span>
                    </div>
                    <div>
                      <span className="font-bold text-xs text-white block">Aria • Shopper Assistant</span>
                      <span className="text-[10px] text-slate-400 block">
                        {confirmedOrder ? `Personalized for Order #${confirmedOrder.orderNumber}` : "UrbanThread AI Care"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleSendChatMessage("I'd like to speak with a human support agent")}
                      className="px-2.5 py-1 text-[11px] text-slate-400 hover:text-amber-300 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 flex items-center gap-1 transition-colors"
                      title="Request Human Agent"
                    >
                      <Headphones className="w-3.5 h-3.5" />
                      <span className="hidden sm:inline">Human Queue</span>
                    </button>
                  </div>
                </div>

                {/* Messages Stream */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-950/40">
                  {chatMessages.map((msg) => {
                    const isUser = msg.sender_type === "CUSTOMER";
                    return (
                      <div
                        key={msg.id}
                        className={`flex gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}
                      >
                        {!isUser && (
                          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-sm mt-0.5">
                            A
                          </div>
                        )}

                        <div className="max-w-[85%] space-y-2">
                          <div
                            className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                              isUser
                                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-tr-none shadow-md"
                                : "bg-slate-900 text-slate-200 border border-slate-800 rounded-tl-none whitespace-pre-line"
                            }`}
                          >
                            {msg.content}
                          </div>

                          {/* Grounded RAG Citations */}
                          {msg.metadata?.citations && Array.isArray(msg.metadata.citations) && msg.metadata.citations.length > 0 && (
                            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2.5 text-[11px] space-y-1.5 shadow-xs">
                              <div className="text-[10px] uppercase font-bold text-blue-400 tracking-wider flex items-center gap-1">
                                <BookOpen className="w-3 h-3 text-blue-400" />
                                <span>Verified Policy Citations</span>
                              </div>
                              <div className="space-y-1">
                                {msg.metadata.citations.map((c: any, idx: number) => (
                                  <div key={idx} className="flex items-center justify-between text-[10px] bg-slate-950 px-2 py-1 rounded border border-slate-800/80">
                                    <span className="font-medium text-slate-300 truncate max-w-[220px]">
                                      {c.source}
                                    </span>
                                    <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold shrink-0">
                                      {Math.round((c.confidence || 0.95) * 100)}% Match
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Order Card Preview */}
                          {msg.metadata?.order && (
                            <div className="bg-slate-900 border border-blue-500/30 rounded-xl p-3 text-xs space-y-2">
                              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                                <span className="font-bold text-white flex items-center gap-1.5">
                                  <Package className="w-3.5 h-3.5 text-blue-400" />
                                  Order #{msg.metadata.order.order_number || msg.metadata.order.id}
                                </span>
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-400">
                                  {msg.metadata.order.status}
                                </span>
                              </div>
                              {msg.metadata.order.shipment && (
                                <div className="text-[11px] text-slate-400 flex justify-between">
                                  <span>{msg.metadata.order.shipment.carrier}</span>
                                  <span className="font-mono text-blue-400">{msg.metadata.order.shipment.tracking_number}</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {chatLoading && (
                    <div className="flex gap-2.5 items-center text-slate-400 text-xs py-2">
                      <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                        A
                      </div>
                      <div className="flex items-center gap-1.5 bg-slate-900 px-3 py-2 rounded-xl border border-slate-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce [animation-delay:0.2s]"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce [animation-delay:0.4s]"></span>
                        <span className="text-[11px] text-slate-400 ml-1">Aria is checking your order details...</span>
                      </div>
                    </div>
                  )}
                  <div ref={chatBottomRef} />
                </div>

                {/* Personalized Quick Suggestion Chips */}
                {chatSuggestions.length > 0 && (
                  <div className="p-2.5 bg-slate-950/80 border-t border-slate-800 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                    <span className="text-[10px] text-slate-500 font-semibold uppercase shrink-0 pl-1">Ask:</span>
                    {chatSuggestions.map((s, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendChatMessage(s)}
                        className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg text-[11px] font-medium border border-slate-800 shrink-0 transition-colors"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}

                {/* Chat Input Bar */}
                <div className="p-3 bg-slate-950 border-t border-slate-800">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendChatMessage();
                    }}
                    className="flex gap-2"
                  >
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder={confirmedOrder ? `Ask Aria about your ${confirmedOrder.productName} (#${confirmedOrder.orderNumber})...` : "Ask Aria a question..."}
                      className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                    />
                    <button
                      type="submit"
                      disabled={!chatInput.trim() || chatLoading}
                      className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-md shadow-blue-600/20"
                    >
                      <span>Send</span>
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 1: BROWSE & BOOK COLLECTION - CARDS SYSTEM                */}
        {/* ------------------------------------------------------------- */}
        {activeTab === "shop" && (
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* Storefront Hero Banner */}
            <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-8 shadow-2xl">
              <div className="relative z-10 max-w-3xl space-y-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Autumn/Winter 2026 Collection • 100% Sustainable & Handcrafted</span>
                </div>
                <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
                  Tailored Elegance, <span className="bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">Everyday Comfort.</span>
                </h1>
                <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
                  Explore UrbanThread&apos;s complete apparel line—from heavyweight combed Supima tees and artisan Okayama selvedge denim to pure linen shirts and tailored trench coats.
                </p>
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    onClick={() => setShowSizingModal(true)}
                    className="flex items-center gap-2 px-3.5 py-2 bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-all shadow-sm"
                  >
                    <Ruler className="w-3.5 h-3.5 text-blue-400" />
                    <span>Sizing & Fabric Care Matrix (RAG)</span>
                  </button>

                  <button
                    onClick={loadPublicCatalog}
                    disabled={isLoadingCatalog}
                    className="flex items-center gap-2 px-3.5 py-2 bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-all shadow-sm"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 text-indigo-400 ${isLoadingCatalog ? "animate-spin" : ""}`} />
                    <span>{isLoadingCatalog ? "Syncing..." : "Refresh Catalog"}</span>
                  </button>

                  <Link
                    href="/products/new"
                    className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 rounded-xl text-xs font-semibold transition-all"
                  >
                    <span>Admin Studio (Live Preview)</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
              <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-blue-600/10 to-transparent pointer-events-none hidden md:block"></div>
            </div>

            {/* Filter & Search Bar */}
            <div className="space-y-4 bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
              {/* Search & Gender Header */}
              <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
                {/* Search Input */}
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by name, fabric (cotton, linen, denim), SKU..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-9 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery("")}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Gender Filter Pills & Sort */}
                <div className="flex flex-wrap items-center gap-3">
                  {/* Gender Selector */}
                  <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
                    {(["ALL", "MEN", "WOMEN", "UNISEX"] as const).map((g) => (
                      <button
                        key={g}
                        onClick={() => setSelectedGender(g)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          selectedGender === g
                            ? "bg-blue-600 text-white shadow-sm"
                            : "text-slate-400 hover:text-white"
                        }`}
                      >
                        {g === "ALL" ? "All Genders" : g === "MEN" ? "Men" : g === "WOMEN" ? "Women" : "Unisex"}
                      </button>
                    ))}
                  </div>

                  {/* Sort By Dropdown */}
                  <div className="flex items-center gap-1.5 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 text-xs">
                    <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as any)}
                      className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
                    >
                      <option value="featured" className="bg-slate-900">Featured</option>
                      <option value="price-asc" className="bg-slate-900">Price: Low to High</option>
                      <option value="price-desc" className="bg-slate-900">Price: High to Low</option>
                      <option value="rating" className="bg-slate-900">Highest Rated</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Clothing Variety Category Pills */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 no-scrollbar">
                {[
                  { label: "All Items", value: "ALL", icon: "✨" },
                  { label: "T-Shirts", value: "T-Shirts", icon: "👕" },
                  { label: "Casual Shirts", value: "Casual Shirts", icon: "👔" },
                  { label: "Denim & Jeans", value: "Denim & Jeans", icon: "👖" },
                  { label: "Jackets & Outerwear", value: "Outerwear & Jackets", icon: "🧥" },
                  { label: "Dresses & Tops", value: "Dresses & Tops", icon: "👗" },
                  { label: "Bottoms & Chinos", value: "Bottoms & Chinos", icon: "🩳" },
                  { label: "Accessories", value: "Accessories", icon: "🎒" }
                ].map((cat) => {
                  const isCatActive = selectedCategory === cat.value;
                  const count = cat.value === "ALL"
                    ? catalog.length
                    : catalog.filter((p) => p.category === cat.value).length;

                  return (
                    <button
                      key={cat.value}
                      onClick={() => setSelectedCategory(cat.value)}
                      className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap flex items-center gap-2 border transition-all ${
                        isCatActive
                          ? "bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-600/20"
                          : "bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700 hover:text-white"
                      }`}
                    >
                      <span>{cat.icon}</span>
                      <span>{cat.label}</span>
                      <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                        isCatActive ? "bg-blue-700 text-white" : "bg-slate-800 text-slate-400"
                      }`}>
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Results Stats */}
              <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/60">
                <span>Showing <strong>{filteredProducts.length}</strong> clothing items</span>
                {(searchQuery || selectedCategory !== "ALL" || selectedGender !== "ALL") && (
                  <button
                    onClick={() => {
                      setSearchQuery("");
                      setSelectedCategory("ALL");
                      setSelectedGender("ALL");
                    }}
                    className="text-blue-400 hover:underline"
                  >
                    Reset all filters
                  </button>
                )}
              </div>
            </div>

            {/* Clothing Cards Grid */}
            {filteredProducts.length === 0 ? (
              <div className="text-center py-16 bg-slate-900/50 border border-slate-800 rounded-3xl space-y-3">
                <p className="text-4xl">🔍</p>
                <h3 className="text-lg font-bold text-white">No clothing items match your filters</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Try searching for another term like &quot;cotton&quot;, &quot;indigo&quot;, &quot;jacket&quot;, or reset your variety filter.
                </p>
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedCategory("ALL");
                    setSelectedGender("ALL");
                  }}
                  className="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl"
                >
                  Show All Items
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredProducts.map((product) => {
                  const isSelected = selectedProduct?.id === product.id;
                  const discountVal = product.basePrice > product.salePrice
                    ? Math.round(((product.basePrice - product.salePrice) / product.basePrice) * 100)
                    : 0;

                  return (
                    <div
                      key={product.id}
                      className={`bg-slate-900/90 border rounded-2xl overflow-hidden transition-all duration-300 flex flex-col group relative ${
                        isSelected
                          ? "border-blue-500 ring-2 ring-blue-500/20 shadow-xl shadow-blue-500/10"
                          : "border-slate-800 hover:border-slate-700 hover:shadow-2xl hover:shadow-blue-900/10"
                      }`}
                    >
                      {/* Product Image Stage (3:4 Portrait) */}
                      <div className="relative aspect-[3/4] w-full overflow-hidden bg-slate-950">
                        <img
                          src={product.image}
                          alt={product.name}
                          className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-700 ease-out"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-80 group-hover:opacity-60 transition-opacity"></div>

                        {/* Top Badges */}
                        <div className="absolute top-3 inset-x-3 flex items-start justify-between gap-2 pointer-events-none">
                          {product.featuredBadge ? (
                            <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg backdrop-blur-md">
                              {product.featuredBadge}
                            </span>
                          ) : (
                            <span></span>
                          )}

                          {discountVal > 0 && (
                            <span className="px-2 py-0.5 rounded-md text-[10px] font-black bg-rose-500/90 text-white shadow-md">
                              {discountVal}% OFF
                            </span>
                          )}
                        </div>

                        {/* Bottom Overlay Info & Quick View Button */}
                        <div className="absolute bottom-3 inset-x-3 flex items-center justify-between">
                          <span className="text-[10px] font-mono text-slate-300 bg-slate-950/80 backdrop-blur-md px-2 py-0.5 rounded border border-slate-800">
                            {product.sku}
                          </span>

                          <button
                            onClick={() => setQuickViewProduct(product)}
                            className="opacity-0 group-hover:opacity-100 transition-all duration-200 flex items-center gap-1 px-2.5 py-1 bg-slate-900/90 hover:bg-blue-600 text-white text-[11px] font-bold rounded-lg backdrop-blur-md border border-slate-700 shadow-md"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Quick View</span>
                          </button>
                        </div>
                      </div>

                      {/* Product Details */}
                      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                        <div className="space-y-1.5">
                          {/* SubCategory & Rating */}
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-blue-400 font-semibold truncate text-[11px]">
                              {product.subCategory}
                            </span>
                            <div className="flex items-center gap-1 text-[11px] text-amber-400 font-bold shrink-0">
                              <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                              <span>{product.rating || 4.8}</span>
                              <span className="text-slate-500 font-normal">({product.reviewsCount || 42})</span>
                            </div>
                          </div>

                          {/* Product Title */}
                          <h3
                            onClick={() => setQuickViewProduct(product)}
                            className="text-sm font-bold text-white group-hover:text-blue-300 transition-colors line-clamp-1 cursor-pointer"
                            title={product.name}
                          >
                            {product.name}
                          </h3>

                          {/* Material preview */}
                          {product.material && (
                            <p className="text-[11px] text-slate-400 line-clamp-1">
                              {product.material}
                            </p>
                          )}

                          {/* Size Pills */}
                          <div className="pt-1">
                            <div className="text-[10px] text-slate-400 font-medium mb-1">Sizes:</div>
                            <div className="flex flex-wrap gap-1">
                              {product.sizes.map((sz) => {
                                const isCurrentSize = isSelected && selectedSize === sz;
                                return (
                                  <button
                                    key={sz}
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setSelectedProduct(product);
                                      setSelectedSize(sz);
                                    }}
                                    className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-colors ${
                                      isCurrentSize
                                        ? "bg-blue-600 text-white border-blue-500"
                                        : "bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700"
                                    }`}
                                  >
                                    {sz}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        </div>

                        {/* Pricing & Booking Trigger */}
                        <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                          <div>
                            <div className="flex items-baseline gap-1.5">
                              <span className="text-base font-black text-white">₹{product.salePrice}</span>
                              {product.basePrice > product.salePrice && (
                                <span className="text-xs text-slate-500 line-through">₹{product.basePrice}</span>
                              )}
                            </div>
                            <div className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span>
                              <span>{product.availableStock} in stock</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => {
                                setSelectedProduct(product);
                                if (product.sizes.length > 0) setSelectedSize(product.sizes[0]);
                                setActiveTab("order");
                              }}
                              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-blue-600/20 flex items-center gap-1"
                            >
                              <span>Book</span>
                              <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 2: ORDER BOOKING & CHECKOUT                               */}
        {/* ------------------------------------------------------------- */}
        {activeTab === "order" && (
          <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <button
                onClick={() => setActiveTab("shop")}
                className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Collection</span>
              </button>
              <span className="text-xs text-blue-400 font-semibold">Step 2 of 2: Confirm Order & Launch Concierge</span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Order Form */}
              <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
                <div className="border-b border-slate-800 pb-4">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <ShoppingBag className="w-5 h-5 text-blue-500" />
                    <span>Booking Details</span>
                  </h3>
                  <p className="text-xs text-slate-400">Configure size, color, and delivery address.</p>
                </div>

                {/* Selected Item Review */}
                <div className="flex items-center gap-4 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <img
                    src={selectedProduct.image}
                    alt={selectedProduct.name}
                    className="w-20 h-20 rounded-lg object-cover border border-slate-800"
                  />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-bold text-sm text-white truncate">{selectedProduct.name}</h4>
                    <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                      <span>Category: <strong className="text-slate-200">{selectedProduct.category}</strong></span>
                      <span>•</span>
                      <span>SKU: <strong className="text-slate-200">{selectedProduct.sku}</strong></span>
                    </div>
                    <div className="text-xs font-bold text-emerald-400 mt-1">₹{selectedProduct.salePrice} each</div>
                  </div>
                </div>

                {/* Size & Color Selection */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Select Size / Dimension</label>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedProduct.sizes.map((sz) => (
                        <button
                          key={sz}
                          type="button"
                          onClick={() => setSelectedSize(sz)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                            selectedSize === sz
                              ? "bg-blue-600 text-white border-blue-500"
                              : "bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800"
                          }`}
                        >
                          {sz}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Select Color Variant</label>
                    <select
                      value={selectedColor}
                      onChange={(e) => setSelectedColor(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    >
                      {selectedProduct.colors.map((col) => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Customer Details Form */}
                <div className="space-y-4 pt-2 border-t border-slate-800">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Shopper Delivery Details</h4>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs text-slate-400">Recipient Full Name</label>
                      <input
                        type="text"
                        value={customerName}
                        onChange={(e) => setCustomerName(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs text-slate-400">Payment Preference</label>
                      <select
                        value={paymentMethod}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                      >
                        <option value="UPI">UPI / Instant NetBanking</option>
                        <option value="CARD">Credit / Debit Card</option>
                        <option value="COD">Cash On Delivery (COD)</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs text-slate-400">Delivery Address</label>
                    <textarea
                      rows={2}
                      value={customerAddress}
                      onChange={(e) => setCustomerAddress(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-blue-500 resize-none"
                    />
                  </div>
                </div>
              </div>

              {/* Right Column: Price Breakdown & Place Order */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 flex flex-col justify-between">
                <div className="space-y-4">
                  <h4 className="text-sm font-bold text-white border-b border-slate-800 pb-3">Order Price Summary</h4>

                  {/* Coupon Code Input */}
                  <div className="space-y-2">
                    <label className="text-xs text-slate-400">Promo Code</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={couponCode}
                        onChange={(e) => setCouponCode(e.target.value)}
                        placeholder="Try URBAN10"
                        className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white uppercase focus:outline-none focus:border-blue-500"
                      />
                      <button
                        type="button"
                        onClick={handleApplyCoupon}
                        className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white rounded-lg border border-slate-700 transition-colors"
                      >
                        Apply
                      </button>
                    </div>
                    {couponMessage && (
                      <p className={`text-[11px] ${couponMessage.startsWith("✓") ? "text-emerald-400" : "text-rose-400"}`}>
                        {couponMessage}
                      </p>
                    )}
                  </div>

                  {/* Cost Items */}
                  <div className="space-y-2 text-xs text-slate-400 border-t border-slate-800 pt-3">
                    <div className="flex justify-between">
                      <span>Item Price:</span>
                      <span className="text-white font-medium">₹{subtotal}</span>
                    </div>

                    {discountAmount > 0 && (
                      <div className="flex justify-between text-emerald-400 font-semibold">
                        <span>Discount ({discountPercent}%):</span>
                        <span>-₹{discountAmount}</span>
                      </div>
                    )}

                    <div className="flex justify-between">
                      <span>GST (12%):</span>
                      <span className="text-white font-medium">₹{tax}</span>
                    </div>

                    <div className="flex justify-between">
                      <span>Shipping (BlueDart Express):</span>
                      <span className={shippingFee === 0 ? "text-emerald-400 font-bold" : "text-white font-medium"}>
                        {shippingFee === 0 ? "FREE" : `₹${shippingFee}`}
                      </span>
                    </div>

                    <div className="flex justify-between border-t border-slate-800 pt-3 text-sm font-bold text-white">
                      <span>Grand Total:</span>
                      <span className="text-emerald-400 text-base">₹{grandTotal}</span>
                    </div>
                  </div>
                </div>

                {/* Submit Booking Button */}
                <div className="space-y-2 pt-4">
                  <button
                    onClick={handlePlaceOrder}
                    disabled={isOrdering}
                    className="w-full py-3.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:opacity-95 text-white rounded-xl text-xs font-black shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                  >
                    {isOrdering ? (
                      <span>Reserving Inventory & Booking...</span>
                    ) : (
                      <>
                        <span>Book & Launch Personalized Concierge</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                  <p className="text-[10px] text-slate-500 text-center">
                    Instant confirmation • 30-day doorstep return guarantee
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 3: TRY-AT-HOME APPOINTMENT BOOKING                        */}
        {/* ------------------------------------------------------------- */}
        {activeTab === "fitting" && (
          <div className="max-w-2xl mx-auto bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 animate-in fade-in duration-300">
            <div className="border-b border-slate-800 pb-4">
              <span className="text-xs uppercase font-bold tracking-wider text-purple-400">UrbanThread VIP Service</span>
              <h3 className="text-lg font-bold text-white mt-1 flex items-center gap-2">
                <Scissors className="w-5 h-5 text-purple-400" />
                <span>Book In-Home Custom Fitting Appointment</span>
              </h3>
              <p className="text-xs text-slate-400">
                A senior UrbanThread stylist brings multiple sizes and styling swatches right to your doorstep.
              </p>
            </div>

            {fittingBooked ? (
              <div className="bg-purple-950/30 border border-purple-800/50 rounded-2xl p-6 text-center space-y-4">
                <CheckCircle2 className="w-12 h-12 text-purple-400 mx-auto" />
                <h4 className="text-base font-bold text-white">Stylist Appointment Confirmed!</h4>
                <p className="text-xs text-slate-300 max-w-md mx-auto">
                  Senior stylist <strong>Priya Nair</strong> will arrive on <strong>{appointmentDate}</strong> during <strong>{appointmentTime}</strong>.
                </p>
                <button
                  onClick={() => {
                    setFittingBooked(false);
                    setActiveTab("shop");
                  }}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold"
                >
                  Return to Collection
                </button>
              </div>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); setFittingBooked(true); }} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs text-slate-400">Preferred Date</label>
                    <input
                      type="date"
                      value={appointmentDate}
                      onChange={(e) => setAppointmentDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-slate-400">Time Slot</label>
                    <select
                      value={appointmentTime}
                      onChange={(e) => setAppointmentTime(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
                    >
                      <option value="10:00 - 12:00 (Morning)">10:00 - 12:00 (Morning)</option>
                      <option value="14:00 - 16:00 (Afternoon)">14:00 - 16:00 (Afternoon)</option>
                      <option value="17:00 - 19:00 (Evening)">17:00 - 19:00 (Evening)</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Fitting Location Address</label>
                  <input
                    type="text"
                    defaultValue={customerAddress}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold shadow-md shadow-purple-600/20"
                >
                  Reserve Stylist Appointment (Complimentary)
                </button>
              </form>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 4: COURIER RETURN PICKUP BOOKING                          */}
        {/* ------------------------------------------------------------- */}
        {activeTab === "returns" && (
          <div className="max-w-2xl mx-auto bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 animate-in fade-in duration-300">
            <div className="border-b border-slate-800 pb-4">
              <span className="text-xs uppercase font-bold tracking-wider text-rose-400">Reverse Logistics</span>
              <h3 className="text-lg font-bold text-white mt-1 flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-rose-400" />
                <span>Book Doorstep Return Courier Pickup</span>
              </h3>
              <p className="text-xs text-slate-400">
                UrbanThread provides free 30-day return courier pickups directly from your doorstep.
              </p>
            </div>

            {returnBooked ? (
              <div className="bg-rose-950/30 border border-rose-800/50 rounded-2xl p-6 text-center space-y-4">
                <CheckCircle2 className="w-12 h-12 text-rose-400 mx-auto" />
                <h4 className="text-base font-bold text-white">Courier Pickup Scheduled!</h4>
                <p className="text-xs text-slate-300 max-w-md mx-auto">
                  BlueDart reverse courier is scheduled for pickup on <strong>{pickupDate}</strong> for order <strong>#{returnOrderId}</strong>. Keep tags attached.
                </p>
                <button
                  onClick={() => {
                    setReturnBooked(false);
                    setActiveTab("shop");
                  }}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold"
                >
                  Return to Collection
                </button>
              </div>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); setReturnBooked(true); }} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Order Number</label>
                  <input
                    type="text"
                    value={returnOrderId}
                    onChange={(e) => setReturnOrderId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Reason for Return or Exchange</label>
                  <select
                    value={returnReason}
                    onChange={(e) => setReturnReason(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
                  >
                    <option value="Size too small/large">Size too small or large (Exchange requested)</option>
                    <option value="Color looks different">Color appears different from online photos</option>
                    <option value="Changed styling preference">Changed styling preference</option>
                    <option value="Defect or stitching issue">Defect or stitching issue</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Pickup Date</label>
                  <input
                    type="date"
                    value={pickupDate}
                    onChange={(e) => setPickupDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-3 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold shadow-md shadow-rose-600/20"
                >
                  Schedule Free Doorstep Pickup
                </button>
              </form>
            )}
          </div>
        )}
        {/* ------------------------------------------------------------- */}
        {/* MODAL: QUICK VIEW PRODUCT CARD                                */}
        {/* ------------------------------------------------------------- */}
        {quickViewProduct && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row max-h-[90vh]">
              {/* Close Button */}
              <button
                onClick={() => setQuickViewProduct(null)}
                className="absolute top-4 right-4 z-10 p-2 bg-slate-950/80 hover:bg-slate-800 text-slate-400 hover:text-white rounded-full transition-colors border border-slate-800"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Product Visual */}
              <div className="md:w-1/2 relative bg-slate-950 overflow-hidden flex items-center justify-center min-h-[300px]">
                <img
                  src={quickViewProduct.image}
                  alt={quickViewProduct.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-transparent"></div>

                <div className="absolute top-4 left-4 flex flex-col gap-2">
                  {quickViewProduct.featuredBadge && (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-600 text-white shadow-lg">
                      {quickViewProduct.featuredBadge}
                    </span>
                  )}
                  {quickViewProduct.basePrice > quickViewProduct.salePrice && (
                    <span className="px-2.5 py-0.5 rounded-md text-xs font-black bg-rose-500 text-white shadow-md">
                      {Math.round(((quickViewProduct.basePrice - quickViewProduct.salePrice) / quickViewProduct.basePrice) * 100)}% OFF
                    </span>
                  )}
                </div>

                <span className="absolute bottom-4 left-4 font-mono text-xs text-slate-300 bg-slate-950/90 px-2.5 py-1 rounded-lg border border-slate-800">
                  {quickViewProduct.sku}
                </span>
              </div>

              {/* Product Details & Actions */}
              <div className="md:w-1/2 p-6 flex flex-col justify-between overflow-y-auto space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-blue-400 font-semibold">
                    <span>{quickViewProduct.subCategory} • {quickViewProduct.gender || "UNISEX"}</span>
                    <div className="flex items-center gap-1 text-amber-400 font-bold">
                      <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                      <span>{quickViewProduct.rating || 4.8}</span>
                    </div>
                  </div>

                  <h3 className="text-xl font-bold text-white leading-tight">
                    {quickViewProduct.name}
                  </h3>

                  {/* Price */}
                  <div className="flex items-baseline gap-2 pt-1">
                    <span className="text-2xl font-black text-white">₹{quickViewProduct.salePrice}</span>
                    {quickViewProduct.basePrice > quickViewProduct.salePrice && (
                      <span className="text-sm text-slate-500 line-through">₹{quickViewProduct.basePrice}</span>
                    )}
                    <span className="text-xs text-emerald-400 font-bold ml-2">
                      Save ₹{quickViewProduct.basePrice - quickViewProduct.salePrice}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {quickViewProduct.description}
                  </p>

                  {/* Fabric & Material Guide */}
                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2 text-xs">
                    <div>
                      <span className="text-slate-400 font-medium">Material Composition: </span>
                      <strong className="text-slate-200">{quickViewProduct.material || "100% Organic Fabric"}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium">Care Protocol: </span>
                      <span className="text-slate-300">{quickViewProduct.fabricCare}</span>
                    </div>
                  </div>

                  {/* Sizes */}
                  <div className="space-y-1.5 pt-1">
                    <div className="text-xs font-semibold text-slate-300">Available Sizes</div>
                    <div className="flex flex-wrap gap-1.5">
                      {quickViewProduct.sizes.map((sz) => (
                        <button
                          key={sz}
                          type="button"
                          onClick={() => setSelectedSize(sz)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                            selectedSize === sz
                              ? "bg-blue-600 text-white border-blue-500"
                              : "bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700"
                          }`}
                        >
                          {sz}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Bottom CTA */}
                <div className="pt-4 border-t border-slate-800 flex items-center gap-3">
                  <button
                    onClick={() => {
                      setSelectedProduct(quickViewProduct);
                      setQuickViewProduct(null);
                      setActiveTab("order");
                    }}
                    className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-blue-600/25 flex items-center justify-center gap-2"
                  >
                    <ShoppingBag className="w-4 h-4" />
                    <span>Book Order Now</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* MODAL: SIZING & FABRIC CARE MATRIX (RAG KNOWLEDGE)            */}
        {/* ------------------------------------------------------------- */}
        {showSizingModal && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl p-6 md:p-8 max-h-[90vh] overflow-y-auto space-y-6">
              {/* Modal Header */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                    <Ruler className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">Sizing & Fabric Care Matrix</h3>
                    <p className="text-xs text-blue-400">OpsPilot RAG Vectorized Knowledge Base (127 Chunks)</p>
                  </div>
                </div>

                <button
                  onClick={() => setShowSizingModal(false)}
                  className="p-2 bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-white rounded-full transition-colors border border-slate-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Sizing Matrix Section */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Standard Body Sizing Dimensions (Inches)
                </h4>

                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[10px]">
                      <tr>
                        <th className="px-4 py-2.5">Size Tag</th>
                        <th className="px-4 py-2.5">Chest / Bust</th>
                        <th className="px-4 py-2.5">Waist (Trousers)</th>
                        <th className="px-4 py-2.5">T-Shirt Length</th>
                        <th className="px-4 py-2.5">Shoulder Width</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                      <tr className="hover:bg-slate-800/40">
                        <td className="px-4 py-2 font-bold text-blue-400">XS</td>
                        <td className="px-4 py-2">34 - 36&quot;</td>
                        <td className="px-4 py-2">28&quot;</td>
                        <td className="px-4 py-2">26.5&quot;</td>
                        <td className="px-4 py-2">16.0&quot;</td>
                      </tr>
                      <tr className="hover:bg-slate-800/40">
                        <td className="px-4 py-2 font-bold text-blue-400">S</td>
                        <td className="px-4 py-2">36 - 38&quot;</td>
                        <td className="px-4 py-2">30&quot;</td>
                        <td className="px-4 py-2">27.5&quot;</td>
                        <td className="px-4 py-2">17.0&quot;</td>
                      </tr>
                      <tr className="hover:bg-slate-800/40 bg-blue-900/10">
                        <td className="px-4 py-2 font-bold text-blue-400">M (Standard)</td>
                        <td className="px-4 py-2 font-bold text-white">38 - 40&quot;</td>
                        <td className="px-4 py-2 font-bold text-white">32&quot;</td>
                        <td className="px-4 py-2 font-bold text-white">28.5&quot;</td>
                        <td className="px-4 py-2 font-bold text-white">18.0&quot;</td>
                      </tr>
                      <tr className="hover:bg-slate-800/40">
                        <td className="px-4 py-2 font-bold text-blue-400">L</td>
                        <td className="px-4 py-2">40 - 42&quot;</td>
                        <td className="px-4 py-2">34&quot;</td>
                        <td className="px-4 py-2">29.5&quot;</td>
                        <td className="px-4 py-2">19.0&quot;</td>
                      </tr>
                      <tr className="hover:bg-slate-800/40">
                        <td className="px-4 py-2 font-bold text-blue-400">XL</td>
                        <td className="px-4 py-2">42 - 44&quot;</td>
                        <td className="px-4 py-2">36&quot;</td>
                        <td className="px-4 py-2">30.5&quot;</td>
                        <td className="px-4 py-2">20.0&quot;</td>
                      </tr>
                      <tr className="hover:bg-slate-800/40">
                        <td className="px-4 py-2 font-bold text-blue-400">XXL</td>
                        <td className="px-4 py-2">44 - 46&quot;</td>
                        <td className="px-4 py-2">38&quot;</td>
                        <td className="px-4 py-2">31.5&quot;</td>
                        <td className="px-4 py-2">21.0&quot;</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Fabric Care Guidelines */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Fabric Maintenance & Care SOPs
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="font-bold text-blue-400">🌿 Combed & Supima Cotton</span>
                    <p className="text-slate-300 leading-relaxed">
                      Machine wash in cold water (max 30°C) with mild eco detergent. Air dry in shade to prevent shrinkage.
                    </p>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="font-bold text-blue-400">👖 Okayama Raw Selvedge Denim</span>
                    <p className="text-slate-300 leading-relaxed">
                      Wear raw for 4-6 months before first wash. Turn inside out, submerge in cold water with gentle dark detergent, hang dry.
                    </p>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="font-bold text-blue-400">🐑 Australian Superfine Merino Wool</span>
                    <p className="text-slate-300 leading-relaxed">
                      Hand wash in lukewarm water with wool detergent. Never wring or hang wet; lay flat on towel to retain structural shape.
                    </p>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="font-bold text-blue-400">🌾 French Normandy Linen</span>
                    <p className="text-slate-300 leading-relaxed">
                      Wash on gentle warm cycle. Linen softens with every laundering. Iron slightly damp for that relaxed, crisp drape.
                    </p>
                  </div>
                </div>
              </div>

              {/* RAG Note */}
              <div className="p-3 bg-blue-950/30 border border-blue-800/40 rounded-xl text-xs text-slate-300 flex items-center gap-2">
                <Bot className="w-4 h-4 text-blue-400 shrink-0" />
                <span>
                  Tip: Aria, your AI Concierge chatbot on the next tab, has direct vectorized access to these exact measurements and SOPs to answer any fit or care question.
                </span>
              </div>

              <div className="text-right">
                <button
                  onClick={() => setShowSizingModal(false)}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-blue-600/20"
                >
                  Got It, Thanks!
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>© 2026 UrbanThread Apparel Co. • Powered by OpsPilot Autonomous AI Operations Platform</p>
      </footer>
    </div>
  );
}
