"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Inbox,
  FileText,
  GitBranch,
  CheckSquare,
  Bot,
  BookOpen,
  ShieldCheck,
  BarChart3,
  History,
  FlaskConical,
  Settings,
  LogOut,
  Building2,
  ShieldAlert,
  ShoppingBag,
  Package,
  Boxes,
  Users,
  Truck,
  RotateCcw,
  BadgePercent,
  Headphones,
  Globe,
  Mail,
  UploadCloud,
  FileText as FileTextIcon,
  Radio,
  Cpu,
  AlertTriangle,
  Activity,
  Sparkles,
  Brain,
  Lock,
  ThumbsUp,
  CheckCircle2,
  Database,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { removeToken } from "@/lib/api";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  highlight?: boolean;
  pulse?: boolean;
  badge?: string;
}

const commandNavItems: NavItem[] = [
  { name: "Command Center", href: "/command-center", icon: Radio, highlight: true, pulse: true },
  { name: "Employee Tasks", href: "/employee/tasks", icon: CheckSquare, badge: "Live", highlight: true },
  { name: "AI Workforce", href: "/ai/employees", icon: Cpu },
  { name: "Alert Center", href: "/alerts", icon: AlertTriangle, badge: "Live" },
  { name: "Observability", href: "/observability/traces", icon: Activity },
];

const aiLearningNavItems: NavItem[] = [
  { name: "Security & Kill Switch", href: "/security", icon: Lock, highlight: true, badge: "Safety" },
  { name: "AI Test Lab", href: "/ai/test-lab", icon: FlaskConical, highlight: true },
  { name: "AI Improvements", href: "/ai/improvements", icon: Sparkles, badge: "Gated" },
  { name: "Regression Evals", href: "/ai/evaluations", icon: CheckCircle2 },
  { name: "AI Memory Store", href: "/ai/memory", icon: Brain },
  { name: "Curated Learning", href: "/ai/learning", icon: Database },
  { name: "Human Feedback", href: "/ai/feedback", icon: ThumbsUp },
  { name: "Customer AI (Aria)", href: "/customer/chat", icon: Headphones, badge: "Aria" },
];

const coreNavItems: NavItem[] = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Operations", href: "/operations", icon: Inbox },
  { name: "System Errors", href: "/operations/errors", icon: AlertTriangle },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Workflows", href: "/workflows", icon: GitBranch },
  { name: "Approvals", href: "/approvals", icon: CheckSquare, badge: "Pending" },
  { name: "Escalations", href: "/escalations", icon: ShieldAlert, badge: "SLA" },
  { name: "Agents Fleet", href: "/agents", icon: Bot },
  { name: "Knowledge & RAG", href: "/knowledge", icon: BookOpen },
  { name: "Policies", href: "/policies", icon: ShieldCheck },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Audit Trail", href: "/audit", icon: History },
  { name: "Tool Registry", href: "/settings/tools", icon: Settings },
  { name: "Settings", href: "/settings", icon: Settings },
];

const ingestionNavItems: NavItem[] = [
  { name: "Websites", href: "/data-sources/websites", icon: Globe },
  { name: "Documents", href: "/documents", icon: FileTextIcon },
  { name: "Inbound Emails", href: "/emails", icon: Mail },
  { name: "Data Imports", href: "/imports", icon: UploadCloud },
];

const ecommerceNavItems: NavItem[] = [
  { name: "Orders", href: "/orders", icon: ShoppingBag },
  { name: "Refunds", href: "/refunds", icon: RotateCcw },
  { name: "Purchase Orders", href: "/purchase-orders", icon: Boxes },
  { name: "Products", href: "/products", icon: Package },
  { name: "Inventory", href: "/inventory", icon: Boxes },
  { name: "Customers", href: "/customers", icon: Users },
  { name: "Shipments", href: "/shipments", icon: Truck },
  { name: "Returns", href: "/returns", icon: RotateCcw },
  { name: "Coupons", href: "/coupons", icon: BadgePercent },
  { name: "Customer Support", href: "/support", icon: Headphones },
];

export function Sidebar() {
  const pathname = usePathname();
  const [currentUser, setCurrentUser] = useState<any>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("opspilot_user");
      if (stored) {
        setCurrentUser(JSON.parse(stored));
      }
    } catch {}
  }, []);

  const handleLogout = () => {
    removeToken();
    localStorage.removeItem("opspilot_user");
    window.location.href = "/login";
  };

  const orgName = currentUser?.email?.includes("urbanthread")
    ? "UrbanThread"
    : currentUser?.email?.includes("globex")
    ? "Globex Mfg"
    : "Acme Industries";

  const userInitials = currentUser?.full_name
    ? currentUser.full_name
        .split(" ")
        .map((n: string) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "OP";

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen border-r border-slate-800 shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex flex-col gap-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-black text-white text-lg tracking-tight shadow-md shadow-blue-500/20">
            OP
          </div>
          <div>
            <h1 className="font-bold text-white text-base tracking-tight leading-tight">
              OpsPilot
            </h1>
            <span className="text-[10px] font-medium text-blue-400 uppercase tracking-wider">
              Autonomous Operations
            </span>
          </div>
        </div>

        {/* Organization selector pill */}
        <div className="mt-3 flex items-center justify-between px-2.5 py-1.5 bg-slate-800/60 rounded-md border border-slate-700/50 text-xs">
          <div className="flex items-center gap-2 truncate">
            <Building2 className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold text-slate-200 truncate">{orgName}</span>
          </div>
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            LIVE
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {/* Command Center & Fleet */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-semibold text-blue-400 uppercase tracking-wider flex items-center justify-between">
            <span>24/7 Operations</span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <div className="space-y-0.5">
            {commandNavItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors group",
                    isActive
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold shadow-sm shadow-blue-600/30"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/70"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={cn("w-4 h-4", isActive ? "text-white" : "text-blue-400 group-hover:text-blue-300")} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[9px] rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-semibold">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* AI Learning & Security */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-semibold text-purple-400 uppercase tracking-wider flex items-center justify-between">
            <span>AI Learning & Security</span>
            <span className="text-[9px] px-1 py-0.2 rounded bg-purple-500/20 text-purple-300 font-mono">v2.4</span>
          </div>
          <div className="space-y-0.5">
            {aiLearningNavItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors group",
                    isActive
                      ? "bg-purple-600 text-white font-semibold shadow-sm shadow-purple-600/30"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/70",
                    item.highlight && !isActive && "text-amber-400 hover:text-amber-300 font-medium"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={cn("w-4 h-4", isActive ? "text-white" : item.highlight ? "text-amber-400" : "text-purple-400 group-hover:text-purple-300")} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className={cn(
                      "px-1.5 py-0.5 text-[9px] rounded-full font-semibold border",
                      item.badge === "Safety" ? "bg-red-500/20 text-red-300 border-red-500/30" :
                      item.badge === "Gated" ? "bg-purple-500/20 text-purple-300 border-purple-500/30" :
                      "bg-blue-500/20 text-blue-300 border-blue-500/30"
                    )}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* E-Commerce Operations */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            E-Commerce Operations
          </div>
          <div className="space-y-0.5">
            {ecommerceNavItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors group",
                    isActive
                      ? "bg-blue-600 text-white font-semibold shadow-sm shadow-blue-600/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={cn("w-4 h-4", isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200")} />
                    <span>{item.name}</span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Ingestion & Data Sources */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Ingestion & Observability
          </div>
          <div className="space-y-0.5">
            {ingestionNavItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors group",
                    isActive
                      ? "bg-blue-600 text-white font-semibold shadow-sm shadow-blue-600/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={cn("w-4 h-4", isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200")} />
                    <span>{item.name}</span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Platform Systems */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Platform Engine
          </div>
          <div className="space-y-0.5">
            {coreNavItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors group",
                    isActive
                      ? "bg-blue-600 text-white font-semibold shadow-sm shadow-blue-600/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60",
                    item.highlight && !isActive && "text-emerald-400 hover:text-emerald-300"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={cn("w-4 h-4", isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200", item.highlight && !isActive && "text-emerald-400")} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Footer User Profile */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2.5 truncate">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-xs text-white shrink-0">
            {userInitials}
          </div>
          <div className="truncate">
            <div className="text-xs font-medium text-slate-200 truncate">
              {currentUser?.full_name || "Operations Staff"}
            </div>
            <div className="text-[10px] text-slate-400 truncate">
              {currentUser?.email || "staff@urbanthread.local"}
            </div>
          </div>
        </div>

        <button
          onClick={handleLogout}
          title="Sign Out"
          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-md transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
