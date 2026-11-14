"use client";

import React, { useState } from "react";
import { Sun, Moon, ArrowRight } from "lucide-react";

export const Navbar: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  return (
    <header className="w-full flex flex-col border-b border-[var(--card-border)] bg-[var(--background)]">
      {/* Announcement bar */}
      <div className="w-full py-2 px-4 text-center text-xs sm:text-sm font-medium border-b border-[var(--card-border)]/60 text-neutral-600 dark:text-neutral-400 flex items-center justify-center gap-1.5 hover:text-black dark:hover:text-white transition-colors cursor-pointer">
        <span>Introducing Motion, the General Video Agent</span>
        <ArrowRight className="w-3.5 h-3.5 inline" />
      </div>

      {/* Main navigation */}
      <div className="max-w-7xl w-full mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-black dark:bg-white flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-white dark:bg-black" />
          </div>
          <span className="font-serif text-2xl font-bold tracking-tight">Motion</span>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-xs font-semibold tracking-wider text-neutral-600 dark:text-neutral-400 uppercase">
          <a href="#enterprise" className="hover:text-black dark:hover:text-white transition-colors">Enterprise</a>
          <a href="#studio" className="hover:text-black dark:hover:text-white transition-colors">Studio</a>
          <a href="#affiliates" className="hover:text-black dark:hover:text-white transition-colors">Affiliates</a>
          <a href="#api" className="hover:text-black dark:hover:text-white transition-colors">API & MCP</a>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="w-9 h-9 rounded-full flex items-center justify-center border border-[var(--card-border)] hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            title="Toggle theme"
          >
            {isDark ? <Sun className="w-4 h-4 text-neutral-200" /> : <Moon className="w-4 h-4 text-neutral-700" />}
          </button>

          <button className="px-4 py-2 rounded-full bg-black text-white dark:bg-white dark:text-black text-xs sm:text-sm font-medium hover:opacity-90 transition-opacity">
            Try Motion
          </button>
        </div>
      </div>
    </header>
  );
};

