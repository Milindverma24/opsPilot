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
      <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
        {/* Left: Page Title */}
        <div>
          <h2 className="text-base font-bold text-slate-800 leading-tight">
            {title || "Operations Command"}
          </h2>
          {subtitle && (
            <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {/* AI Command Center Trigger */}
          <button
            onClick={() => setCommandOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200/80 text-slate-600 rounded-lg text-xs font-medium border border-slate-200 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>AI Command Center</span>
            <kbd className="text-[10px] bg-white px-1.5 py-0.5 rounded border border-slate-300 text-slate-400 font-sans">
              ⌘K
            </kbd>
          </button>

          {/* Autonomy Level Indicator */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 border border-blue-100 rounded-md text-[11px] font-semibold text-blue-700">
            <Shield className="w-3.5 h-3.5 text-blue-600" />
            <span>Autonomy: Level 2</span>
          </div>

          {/* Upload Shortcut */}
          {onUploadClick && (
            <button
              onClick={onUploadClick}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </button>
          )}

          {/* Notifications */}
          <button
            title="Notifications"
            className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white" />
            )}
          </button>
        </div>
      </header>

      <CommandModal isOpen={commandOpen} onClose={() => setCommandOpen(false)} />
    </>
  );
}
