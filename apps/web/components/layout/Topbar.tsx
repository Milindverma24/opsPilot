"use client";

import { useState } from "react";
import { Search, Bell, Sparkles, UploadCloud, Shield, HelpCircle } from "lucide-react";
import { CommandModal } from "./CommandModal";

interface TopbarProps {
  title?: string;
  subtitle?: string;
  onUploadClick?: () => void;
}

export function Topbar({ title, subtitle, onUploadClick }: TopbarProps) {
  const [commandOpen, setCommandOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(2);

  return (
    <>
      <header className="h-16 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80 px-6 flex items-center justify-between shrink-0 sticky top-0 z-30">
        {/* Left: Page Title */}
        <div>
          <h2 className="text-base font-bold text-white leading-tight tracking-tight">
            {title || "Operations Command"}
          </h2>
          {subtitle && (
            <p className="text-xs text-slate-400 font-medium mt-0.5">{subtitle}</p>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {/* AI Command Center Trigger */}
          <button
            onClick={() => setCommandOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/90 hover:bg-slate-800/90 text-slate-200 rounded-xl text-xs font-medium border border-slate-700/60 shadow-sm transition-all hover:border-indigo-500/40"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Command Center</span>
            <kbd className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700 text-slate-400 font-mono">
              ⌘K
            </kbd>
          </button>

          {/* Autonomy Level Indicator */}
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-[11px] font-semibold text-indigo-300 shadow-[0_0_12px_rgba(99,102,241,0.2)]">
            <Shield className="w-3.5 h-3.5 text-indigo-400" />
            <span>Autonomy: Level 2</span>
          </div>

          {/* Upload Shortcut */}
          {onUploadClick && (
            <button
              onClick={onUploadClick}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </button>
          )}

          {/* Notifications */}
          <button
            title="Notifications"
            className="relative p-2 text-slate-400 hover:text-white hover:bg-slate-900 rounded-xl border border-transparent hover:border-slate-800 transition-colors"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-slate-950 animate-pulse" />
            )}
          </button>
        </div>
      </header>

      <CommandModal isOpen={commandOpen} onClose={() => setCommandOpen(false)} />
    </>
  );
}
