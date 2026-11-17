"use client";

import React, { useState } from "react";
import {
  VisualStyleConfig,
  CaptionPreset,
  VideoLayoutPreset,
  SocialCardPreset,
  BackgroundPreset,
  CAPTION_PRESETS,
  LAYOUT_PRESETS,
  SOCIAL_CARD_PRESETS,
  BACKGROUND_PRESETS,
  DEFAULT_VISUAL_STYLE_CONFIG,
} from "./types";
import { CaptionPresetCard } from "./CaptionPresetCard";
import { LayoutPresetCard } from "./LayoutPresetCard";
import { SocialCardView } from "./SocialCardView";
import { BackgroundPresetCard } from "./BackgroundPresetCard";
import { StylePreviewModal } from "./StylePreviewModal";
import { KineticHookPreview } from "./KineticHookPreview";
import {
  Sparkles,
  Eye,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  Volume2,
  RotateCcw,
  Palette,
  Check,
} from "lucide-react";

interface TitleAlternative {
  text: string;
  angle?: string;
  accuracy_note?: string;
}

interface Props {
  config: VisualStyleConfig;
  onChangeConfig: (config: VisualStyleConfig) => void;
  availableHook?: string;
  availableTitle?: string;
  titleAlternatives?: TitleAlternative[];
  keyHooks?: string[];
}

const DEFAULT_HOOK = "The single psychological trick behind 10M views";
const DEFAULT_TITLE = "The Unfair Advantage 99% Of People Never Realize";
const DEFAULT_TITLE_ALTERNATIVES: TitleAlternative[] = [
  { text: "The Unfair Advantage 99% Of People Never Realize", angle: "Curiosity" },
  { text: "Why Working Harder Is Keeping You Broke", angle: "Contrarian" },
  { text: "How To Hook Any Viewer In The First 3 Seconds", angle: "How-To" },
  { text: "The Single Psychological Shift Behind 10M Views", angle: "Story" },
  { text: "Stop Making This Critical Retention Mistake", angle: "Direct" },
];

export const VisualStyleStudio: React.FC<Props> = ({
  config,
  onChangeConfig,
  availableHook,
  availableTitle,
  titleAlternatives,
  keyHooks,
}) => {
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [activeCaptionCategory, setActiveCaptionCategory] = useState<string>("all");

  const cardMode = config.cardTextMode || "hook";
  const effectiveHook = availableHook || DEFAULT_HOOK;
  const effectiveTitle = availableTitle || DEFAULT_TITLE;
  const activeTitleAlts =
    titleAlternatives && titleAlternatives.length > 0
      ? titleAlternatives
      : DEFAULT_TITLE_ALTERNATIVES;

  const effectiveCardText =
    cardMode === "custom" && config.customCardText !== undefined
      ? config.customCardText
      : cardMode === "title"
      ? (config.customCardText || effectiveTitle)
      : (config.customCardText || effectiveHook);

  const selectedCaption =
    CAPTION_PRESETS.find((c) => c.id === config.captionPresetId) || CAPTION_PRESETS[0];
  const selectedLayout =
    LAYOUT_PRESETS.find((l) => l.id === config.layoutPresetId) || LAYOUT_PRESETS[0];
  const selectedSocialCard =
    SOCIAL_CARD_PRESETS.find((s) => s.id === config.socialCardPresetId) || SOCIAL_CARD_PRESETS[0];
  const selectedBg =
    BACKGROUND_PRESETS.find((b) => b.id === config.backgroundPresetId) || BACKGROUND_PRESETS[0];

  const handleSelectCaption = (preset: CaptionPreset) => {
    onChangeConfig({
      ...config,
      captionPresetId: preset.id,
      customFontName: preset.fontFamily,
      customActiveColor: preset.highlightColor,
      customTextColor: preset.textColor,
      customAnimation: preset.animationType,
      customAllCaps: preset.allCaps,
      customOutlineWidth: preset.outlineWidth,
    });
  };

  const handleSelectLayout = (preset: VideoLayoutPreset) => {
    const isGameplayOrAmbient = ["floating", "card", "card_frame", "blurred_bg", "blurred", "split_50_50", "split_60_40"].includes(preset.id);
    onChangeConfig({
      ...config,
      layoutPresetId: preset.id,
      backgroundPresetId: isGameplayOrAmbient ? "minecraft" : config.backgroundPresetId,
    });
  };

  const handleSelectSocialCard = (preset: SocialCardPreset) => {
    onChangeConfig({
      ...config,
      socialCardPresetId: preset.id,
      customCardAuthor: preset.authorName,
      customCardHandle: preset.authorHandle,
      customCardText: preset.id === "none" ? "" : (config.customCardText || effectiveCardText),
    });
  };

  const handleSelectBackground = (preset: BackgroundPreset) => {
    onChangeConfig({
      ...config,
      backgroundPresetId: preset.id,
    });
  };

  const handleResetToDefault = () => {
    onChangeConfig({ ...DEFAULT_VISUAL_STYLE_CONFIG });
  };

  const filteredCaptions =
    activeCaptionCategory === "all"
      ? CAPTION_PRESETS
      : CAPTION_PRESETS.filter((c) => {
          if (activeCaptionCategory === "viral") return ["bold", "creator", "comic"].includes(c.category);
          if (activeCaptionCategory === "modern") return ["neon", "minimal", "gradient"].includes(c.category);
          if (activeCaptionCategory === "cinematic") return ["cinematic", "typewriter", "depth"].includes(c.category);
          return true;
        });

  return (
    <div className="w-full rounded-xl bg-[#0D0F14] border border-[#222732] shadow-xl overflow-hidden my-3">
      {/* ------------------------------------------------------------------- */}
      {/* COMPACT STUDIO HEADER */}
      {/* ------------------------------------------------------------------- */}
      <div className="px-3.5 py-3 border-b border-[#1E232E] bg-gradient-to-r from-[#11141A] to-[#0D0F14] flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-[#3B82F6] animate-pulse"></div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-sans font-bold text-sm sm:text-base text-white tracking-tight">
                Visual Style Studio
              </h3>
              <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-md bg-[#3B82F6]/15 border border-[#3B82F6]/30 text-[#3B82F6] font-bold hidden sm:inline">
                CONFIGURED UPFRONT
              </span>
            </div>
            <p className="font-sans text-[11px] text-neutral-400">
              Customize caption WordArt, video composition, and social card hooks.
            </p>
          </div>
        </div>

        {/* Action Header Pills */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleResetToDefault}
            className="px-2.5 py-1 rounded-md border border-[#2A313E] text-neutral-400 hover:text-white hover:bg-[#181C24] font-mono text-[11px] transition-colors flex items-center gap-1"
            title="Reset options to defaults"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset</span>
          </button>

          <button
            type="button"
            onClick={() => setIsPreviewModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-[#3B82F6] hover:bg-[#2563EB] text-white font-sans font-semibold text-xs shadow-[0_0_12px_rgba(59,130,246,0.35)] transition-all flex items-center gap-1.5"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Live 9:16 Preview</span>
          </button>
        </div>
      </div>

      <div className="p-3.5 sm:p-4 space-y-4">
        {/* ----------------------------------------------------------------- */}
        {/* SECTION 1: CAPTION STYLES (Interactive Horizontal Scroll Strip) */}
        {/* ----------------------------------------------------------------- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-md bg-[#3B82F6]/15 border border-[#3B82F6]/30 font-mono text-[10px] font-bold text-[#3B82F6] flex items-center justify-center">
                1
              </span>
              <h4 className="font-sans font-bold text-xs text-neutral-200 uppercase tracking-wider">
                Caption Styles
              </h4>
              <span className="font-sans text-[11px] text-neutral-400 hidden md:inline">
                • {selectedCaption.name} ({selectedCaption.description})
              </span>
            </div>

            {/* Quick Filter Tabs */}
            <div className="flex items-center gap-1 bg-[#13161C] p-0.5 rounded-md border border-[#1E232E]">
              {[
                { id: "all", label: "All (10)" },
                { id: "viral", label: "Viral Pop" },
                { id: "modern", label: "Modern" },
                { id: "cinematic", label: "Cinematic" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveCaptionCategory(tab.id)}
                  className={`px-2 py-0.5 rounded font-sans text-[11px] font-medium transition-colors ${
                    activeCaptionCategory === tab.id
                      ? "bg-[#252A36] text-white font-bold"
                      : "text-neutral-400 hover:text-neutral-200"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Horizontal Scroll Rail */}
          <div className="flex gap-2.5 overflow-x-auto pb-2 pt-0.5 scrollbar-thin scrollbar-thumb-neutral-700">
            {filteredCaptions.map((preset) => (
              <div key={preset.id} className="min-w-[190px] sm:min-w-[210px] flex-shrink-0">
                <CaptionPresetCard
                  preset={preset}
                  isSelected={config.captionPresetId === preset.id}
                  onSelect={handleSelectCaption}
                />
              </div>
            ))}
          </div>

          {/* Dedicated Caption Customizer: Colors, Font & Animation Engine (Upfront) */}
          <div className="p-3 sm:p-3.5 rounded-xl bg-[#12151D] border border-[#262D3D] space-y-3 shadow-md mt-2">
            {/* Header & Live Mini Preview Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-[#1E232E]">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#FFE600]" />
                <div>
                  <h5 className="font-sans font-bold text-xs text-white uppercase tracking-wider">
                    Caption Engine: Colors, Font &amp; Motion
                  </h5>
                  <p className="font-sans text-[11px] text-neutral-400">
                    Customize active highlight color, rest-of-text color, font family, and animation before generating.
                  </p>
                </div>
              </div>

              {/* Live Interactive Caption Simulation Badge */}
              <div className="px-3 py-1.5 rounded-lg bg-black/80 border border-neutral-700 flex items-center justify-center shrink-0">
                <span
                  style={{
                    fontFamily: config.customFontName || selectedCaption.fontFamily || "Arial Black",
                    color: config.customTextColor || selectedCaption.textColor || "#FFFFFF",
                    textTransform: config.customAllCaps !== false ? "uppercase" : "none",
                  }}
                  className="text-xs font-black tracking-wide"
                >
                  <span>THIS IS </span>
                  <span
                    style={{
                      color: config.customActiveColor || selectedCaption.highlightColor || "#FFE600",
                      textShadow:
                        (config.customAnimation === "glow_pulse" || selectedCaption.hasGlow)
                          ? `0 0 12px ${config.customActiveColor || selectedCaption.highlightColor || "#FFE600"}`
                          : "0 1px 0 #000",
                      display: "inline-block",
                    }}
                    className={`px-1 rounded-sm ${
                      config.customAnimation === "glow_pulse" || selectedCaption.hasGlow
                        ? "animate-pulse"
                        : config.customAnimation === "word_pop" || config.customAnimation === "bounce"
                        ? "animate-bounce"
                        : ""
                    }`}
                  >
                    HIGHLIGHTED
                  </span>
                  <span> CAPTION</span>
                </span>
              </div>
            </div>

            {/* Grid of Controls: Colors, Font, Animation & Casing */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* 1. HIGHLIGHTED CAPTION COLOR */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-sans text-[11px] font-bold text-neutral-300">
                    Highlight Color
                  </label>
                  <span className="font-mono text-[10px] text-neutral-400">
                    {config.customActiveColor || selectedCaption.highlightColor}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  {[
                    { name: "Cyber Yellow", hex: "#FFE600" },
                    { name: "Acid Lime", hex: "#D5EB45" },
                    { name: "Electric Mint", hex: "#00E297" },
                    { name: "Neon Cyan", hex: "#00FFFF" },
                    { name: "Hot Pink", hex: "#FF2A85" },
                    { name: "Crimson Red", hex: "#FF334B" },
                    { name: "Pure White", hex: "#FFFFFF" },
                  ].map((swatch) => {
                    const isSelected = (config.customActiveColor || selectedCaption.highlightColor) === swatch.hex;
                    return (
                      <button
                        key={swatch.hex}
                        type="button"
                        title={swatch.name}
                        onClick={() => onChangeConfig({ ...config, customActiveColor: swatch.hex })}
                        className={`w-5 h-5 rounded-md border transition-transform cursor-pointer ${
                          isSelected
                            ? "ring-2 ring-white scale-110 border-white shadow-sm"
                            : "border-black/60 hover:scale-105"
                        }`}
                        style={{ backgroundColor: swatch.hex }}
                      />
                    );
                  })}
                  {/* Custom Color Input */}
                  <label className="relative w-5 h-5 rounded-md border border-neutral-600 bg-neutral-800 flex items-center justify-center cursor-pointer hover:border-neutral-400" title="Custom color picker">
                    <input
                      type="color"
                      value={config.customActiveColor || selectedCaption.highlightColor || "#FFE600"}
                      onChange={(e) => onChangeConfig({ ...config, customActiveColor: e.target.value })}
                      className="opacity-0 absolute inset-0 w-full h-full cursor-pointer"
                    />
                    <Palette className="w-3 h-3 text-neutral-300" />
                  </label>
                </div>
              </div>

              {/* 2. REST OF TEXT COLOR */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-sans text-[11px] font-bold text-neutral-300">
                    Rest of Text Color
                  </label>
                  <span className="font-mono text-[10px] text-neutral-400">
                    {config.customTextColor || selectedCaption.textColor}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  {[
                    { name: "Pure White", hex: "#FFFFFF" },
                    { name: "Snow Silver", hex: "#F8FAFC" },
                    { name: "Light Slate", hex: "#E2E8F0" },
                    { name: "Warm Cream", hex: "#FAF7F2" },
                    { name: "Pitch Dark", hex: "#111111" },
                    { name: "Mint Tint", hex: "#00E297" },
                  ].map((swatch) => {
                    const isSelected = (config.customTextColor || selectedCaption.textColor) === swatch.hex;
                    return (
                      <button
                        key={swatch.hex}
                        type="button"
                        title={swatch.name}
                        onClick={() => onChangeConfig({ ...config, customTextColor: swatch.hex })}
                        className={`w-5 h-5 rounded-md border transition-transform cursor-pointer ${
                          isSelected
                            ? "ring-2 ring-white scale-110 border-white shadow-sm"
                            : "border-black/60 hover:scale-105"
                        }`}
                        style={{ backgroundColor: swatch.hex }}
                      />
                    );
                  })}
                  <label className="relative w-5 h-5 rounded-md border border-neutral-600 bg-neutral-800 flex items-center justify-center cursor-pointer hover:border-neutral-400" title="Custom color picker">
                    <input
                      type="color"
                      value={config.customTextColor || selectedCaption.textColor || "#FFFFFF"}
                      onChange={(e) => onChangeConfig({ ...config, customTextColor: e.target.value })}
                      className="opacity-0 absolute inset-0 w-full h-full cursor-pointer"
                    />
                    <Palette className="w-3 h-3 text-neutral-300" />
                  </label>
                </div>
              </div>

              {/* 3. FONT FAMILY */}
              <div className="space-y-1.5">
                <label className="font-sans text-[11px] font-bold text-neutral-300 block">
                  Font Family
                </label>
                <div className="relative">
                  <select
                    value={config.customFontName || selectedCaption.fontFamily || "Arial Black"}
                    onChange={(e) => onChangeConfig({ ...config, customFontName: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded-lg border border-[#262D3D] bg-[#161B24] text-xs font-bold text-white outline-none cursor-pointer hover:border-[#3B82F6] focus:border-[#3B82F6]"
                  >
                    <option value="Impact">Impact (Heavy Punch)</option>
                    <option value="Arial Black">Arial Black (Hormozi / MrBeast)</option>
                    <option value="Space Grotesk">Space Grotesk (Tech Modern)</option>
                    <option value="Inter">Inter (Clean Sans)</option>
                    <option value="Montserrat">Montserrat (Geometric Bold)</option>
                    <option value="Georgia">Georgia (Cinematic Serif)</option>
                    <option value="Courier New">Courier New (Terminal Hacker)</option>
                    <option value="Trebuchet MS">Trebuchet MS (Dynamic Casual)</option>
                  </select>
                </div>
              </div>

              {/* 4. ANIMATION STYLE (FADE, POP, GLOW, SLIDE) */}
              <div className="space-y-1.5">
                <label className="font-sans text-[11px] font-bold text-neutral-300 block">
                  Motion &amp; Animation
                </label>
                <div className="grid grid-cols-3 gap-1">
                  {[
                    { id: "word_pop", label: "💥 Pop", title: "Word Bounce / Pop (Hormozi / MrBeast)" },
                    { id: "glow_pulse", label: "✨ Glow", title: "Neon Glow Aura" },
                    { id: "fade_in", label: "🎬 Fade", title: "Cinematic Soft Fade" },
                    { id: "slide_up", label: "⬆️ Slide", title: "Kinetic Slide Up" },
                    { id: "karaoke", label: "🎤 Karaoke", title: "Karaoke Color Wipe" },
                  ].map((anim) => {
                    const isSelected = (config.customAnimation || selectedCaption.animationType || "word_pop") === anim.id;
                    return (
                      <button
                        key={anim.id}
                        type="button"
                        title={anim.title}
                        onClick={() => onChangeConfig({ ...config, customAnimation: anim.id as any })}
                        className={`px-1.5 py-1 rounded text-[10px] sm:text-[11px] font-semibold transition-all cursor-pointer truncate ${
                          isSelected
                            ? "bg-[#3B82F6] text-white font-bold shadow-xs"
                            : "bg-[#181D26] text-neutral-400 hover:text-white hover:bg-[#202734]"
                        }`}
                      >
                        {anim.label}
                      </button>
                    );
                  })}
                  {/* ALL CAPS toggle */}
                  <button
                    type="button"
                    onClick={() => onChangeConfig({ ...config, customAllCaps: !(config.customAllCaps !== false) })}
                    className={`px-1.5 py-1 rounded text-[10px] sm:text-[11px] font-semibold transition-all cursor-pointer ${
                      config.customAllCaps !== false
                        ? "bg-[#D5EB45] text-black font-black"
                        : "bg-[#181D26] text-neutral-400 hover:text-white"
                    }`}
                    title="Toggle ALL CAPS vs sentence case"
                  >
                    {config.customAllCaps !== false ? "CAPS ON" : "Caps Off"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* SECTION 2: VIDEO LAYOUTS (Miniature 9:16 Wireframe Rail) */}
        {/* ----------------------------------------------------------------- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-md bg-[#3B82F6]/15 border border-[#3B82F6]/30 font-mono text-[10px] font-bold text-[#3B82F6] flex items-center justify-center">
                2
              </span>
              <h4 className="font-sans font-bold text-xs text-neutral-200 uppercase tracking-wider">
                Video Layouts
              </h4>
              <span className="font-sans text-[11px] text-neutral-400 hidden sm:inline">
                • {selectedLayout.name}
              </span>
            </div>
            <span className="font-mono text-[10px] text-neutral-500">
              [SCROLL FOR ALL 10 PRESETS]
            </span>
          </div>

          {/* Horizontal scroll of wireframe cards */}
          <div className="flex gap-3 overflow-x-auto pb-2 pt-0.5 scrollbar-thin scrollbar-thumb-neutral-700">
            {LAYOUT_PRESETS.map((preset) => (
              <LayoutPresetCard
                key={preset.id}
                preset={preset}
                isSelected={config.layoutPresetId === preset.id}
                onSelect={handleSelectLayout}
              />
            ))}
          </div>
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* SECTION 3: SOCIAL CARDS (Authentic Post Cards with Real Logos) */}
        {/* ----------------------------------------------------------------- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-md bg-[#3B82F6]/15 border border-[#3B82F6]/30 font-mono text-[10px] font-bold text-[#3B82F6] flex items-center justify-center">
                3
              </span>
              <h4 className="font-sans font-bold text-xs text-neutral-200 uppercase tracking-wider">
                Social Card Hooks
              </h4>
              <span className="font-sans text-[11px] text-neutral-400 hidden sm:inline">
                • {selectedSocialCard.name}
              </span>
            </div>
            <span className="font-mono text-[10px] text-neutral-500">
              [AUTHENTIC PLATFORM LOGOS]
            </span>
          </div>

          {/* Card Hook / Title Source Switcher & Live Input (Aligned with Post Scheduling) */}
          <div className="bg-[#13161D] border border-[#222834] p-3 rounded-lg space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-[#3B82F6]" />
                <span className="font-sans font-bold text-xs text-neutral-200">
                  Card Hook / Title:
                </span>
                <span className="font-sans text-[10px] text-neutral-400">
                  (Same title/hook used in YouTube post scheduling)
                </span>
              </div>

              {/* Source Switcher Buttons */}
              <div className="flex items-center gap-1 bg-[#0D0F14] p-0.5 rounded-md border border-[#1E232E]">
                <button
                  type="button"
                  onClick={() => {
                    onChangeConfig({
                      ...config,
                      cardTextMode: "hook",
                      customCardText: effectiveHook,
                    });
                  }}
                  className={`px-2.5 py-1 rounded font-sans text-[11px] font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                    (config.cardTextMode || "hook") === "hook"
                      ? "bg-[#3B82F6] text-white shadow-xs"
                      : "text-neutral-400 hover:text-white"
                  }`}
                  title="Use viral hook for social cards"
                >
                  <span>🪝 AI Hook</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    onChangeConfig({
                      ...config,
                      cardTextMode: "title",
                      customCardText: effectiveTitle,
                    });
                  }}
                  className={`px-2.5 py-1 rounded font-sans text-[11px] font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                    config.cardTextMode === "title"
                      ? "bg-[#3B82F6] text-white shadow-xs"
                      : "text-neutral-400 hover:text-white"
                  }`}
                  title="Use post scheduling title for social cards"
                >
                  <span>📌 Post Title</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    onChangeConfig({
                      ...config,
                      cardTextMode: "custom",
                    });
                  }}
                  className={`px-2.5 py-1 rounded font-sans text-[11px] font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                    config.cardTextMode === "custom"
                      ? "bg-[#3B82F6] text-white shadow-xs"
                      : "text-neutral-400 hover:text-white"
                  }`}
                  title="Type custom text for social cards"
                >
                  <span>✍️ Custom</span>
                </button>
              </div>
            </div>

            {/* Character & Mobile Safe Linting Bar (Matches ScheduleModal) */}
            <div className="flex items-center justify-between">
              <label className="font-mono text-[11px] font-bold text-neutral-300 uppercase flex items-center gap-1.5">
                <span>
                  {cardMode === "title"
                    ? "Short Title (From Post Scheduling)"
                    : cardMode === "hook"
                    ? "Opening Viral Hook (AI Detected)"
                    : "Custom Card Text"}
                </span>
              </label>
              <span
                className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                  effectiveCardText.length <= 40
                    ? "bg-[#d5eb45] text-black border-[#d5eb45]"
                    : effectiveCardText.length <= 60
                    ? "bg-[#3B82F6]/20 text-[#3B82F6] border-[#3B82F6]/40"
                    : "bg-red-950/60 text-red-300 border-red-700/50"
                }`}
              >
                {effectiveCardText.length} chars{" "}
                {effectiveCardText.length <= 40
                  ? "• Mobile Safe (<40)"
                  : effectiveCardText.length <= 60
                  ? "• Optimal (<60)"
                  : "• May Truncate"}
              </span>
            </div>

            {/* Live Editable Text Input */}
            <div className="relative">
              <input
                type="text"
                value={effectiveCardText}
                onChange={(e) => {
                  onChangeConfig({
                    ...config,
                    cardTextMode: "custom",
                    customCardText: e.target.value,
                  });
                }}
                placeholder="e.g. Stop Making This Editing Mistake | #Shorts"
                className="w-full px-3 py-2 rounded-md border border-[#2A313E] bg-[#0A0C10] font-sans text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-[#3B82F6] transition-colors"
              />
            </div>

            {/* Alternative Titles Selector (Role 06 Packager) — Identical to Post Scheduling */}
            {cardMode === "title" && activeTitleAlts.length > 0 && (
              <div className="space-y-1.5 pt-1 border-t border-[#1E232E]">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase font-bold text-neutral-400 flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-[#3B82F6]" />
                    <span>Select Alternative Title (Role 06 Packager):</span>
                  </span>
                  <span className="font-mono text-[9px] text-[#3B82F6]">
                    Matches Post Scheduling
                  </span>
                </div>
                <div className="grid grid-cols-1 gap-1">
                  {activeTitleAlts.map((alt, idx) => {
                    const isSelected = effectiveCardText === alt.text;
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          onChangeConfig({
                            ...config,
                            cardTextMode: "title",
                            customCardText: alt.text,
                          });
                        }}
                        className={`text-left px-2.5 py-1.5 rounded-md border text-[11px] font-mono transition-all flex items-center justify-between gap-2 cursor-pointer ${
                          isSelected
                            ? "bg-[#3B82F6]/15 text-white border-[#3B82F6] font-bold shadow-xs"
                            : "bg-[#0D0F14] text-neutral-300 border-[#1E232E] hover:border-[#3B82F6]/50 hover:bg-[#151922]"
                        }`}
                      >
                        <span className="truncate flex-1">
                          <span className="uppercase text-[9px] px-1.5 py-0.5 mr-1.5 rounded-xs border border-[#3B82F6]/40 bg-[#3B82F6]/10 text-[#3B82F6] font-bold">
                            {alt.angle || `Alt ${idx + 1}`}
                          </span>
                          {alt.text}
                        </span>
                        {isSelected && (
                          <Check className="w-3.5 h-3.5 text-[#3B82F6] shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Alternative Hooks Selector (If keyHooks provided) */}
            {cardMode === "hook" && keyHooks && keyHooks.length > 0 && (
              <div className="space-y-1.5 pt-1 border-t border-[#1E232E]">
                <span className="font-mono text-[10px] uppercase font-bold text-neutral-400 flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3 text-[#00E297]" />
                  <span>Select Detected Hook Variant:</span>
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {keyHooks.map((h, idx) => {
                    const isSelected = effectiveCardText === h;
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          onChangeConfig({
                            ...config,
                            cardTextMode: "hook",
                            customCardText: h,
                          });
                        }}
                        className={`px-2.5 py-1 rounded-md border text-[11px] font-mono transition-all cursor-pointer ${
                          isSelected
                            ? "bg-[#00E297]/15 text-[#00E297] border-[#00E297] font-bold"
                            : "bg-[#0D0F14] text-neutral-400 border-[#1E232E] hover:text-white"
                        }`}
                      >
                        {h}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Horizontal / Grid Scroll of Social Cards */}
          <div className="flex gap-3 overflow-x-auto pb-2 pt-0.5 scrollbar-thin scrollbar-thumb-neutral-700">
            {SOCIAL_CARD_PRESETS.map((preset) => (
              <div key={preset.id} className="min-w-[280px] sm:min-w-[320px] max-w-[360px] flex-shrink-0">
                <SocialCardView
                  preset={preset}
                  isSelected={config.socialCardPresetId === preset.id}
                  onSelect={handleSelectSocialCard}
                  customText={effectiveCardText}
                  customAuthor={config.customCardAuthor}
                />
              </div>
            ))}
          </div>

          {/* Phase 3: Kinetic Hook & Title Animation Studio */}
          <KineticHookPreview
            config={config}
            onChangeConfig={onChangeConfig}
            hookText={effectiveCardText}
          />
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* SECTION 4: BACKGROUND & EFFECTS (Compact Swatches) */}
        {/* ----------------------------------------------------------------- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-md bg-[#3B82F6]/15 border border-[#3B82F6]/30 font-mono text-[10px] font-bold text-[#3B82F6] flex items-center justify-center">
                4
              </span>
              <h4 className="font-sans font-bold text-xs text-neutral-200 uppercase tracking-wider">
                Canvas Background
              </h4>
              <span className="font-sans text-[11px] text-neutral-400 hidden sm:inline">
                • {selectedBg.name}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {BACKGROUND_PRESETS.map((preset) => (
              <BackgroundPresetCard
                key={preset.id}
                preset={preset}
                isSelected={config.backgroundPresetId === preset.id}
                onSelect={handleSelectBackground}
              />
            ))}
          </div>
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* COLLAPSIBLE FINE-TUNING PANEL (Position Sliders & AI Voice) */}
        {/* ----------------------------------------------------------------- */}
        <div className="border border-[#1E232E] rounded-lg overflow-hidden bg-[#11141A]">
          <button
            type="button"
            onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
            className="w-full px-3.5 py-2.5 flex items-center justify-between text-left hover:bg-[#151922] transition-colors"
          >
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-3.5 h-3.5 text-[#3B82F6]" />
              <span className="font-sans font-bold text-xs text-neutral-200">
                Fine-Tune Coordinates &amp; AI Neural Voice Hook
              </span>
              <span className="font-mono text-[10px] text-neutral-500 hidden sm:inline">
                (Card Y: {config.cardVerticalPosition}%, Sub Y: {config.subtitleVerticalPosition}%)
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-neutral-400">
              <span className="font-mono text-[11px]">
                {showAdvancedSettings ? "Collapse" : "Expand"}
              </span>
              {showAdvancedSettings ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </div>
          </button>

          {showAdvancedSettings && (
            <div className="p-3.5 sm:p-4 border-t border-[#1E232E] bg-[#0E1015] space-y-4 animate-in slide-in-from-top-1 duration-150">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 1. Card Vertical Position */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-sans font-medium text-neutral-300">
                      Card Vertical Position (Y)
                    </span>
                    <span className="font-mono font-bold text-[#3B82F6]">
                      {config.cardVerticalPosition}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="80"
                    step="2"
                    value={config.cardVerticalPosition}
                    onChange={(e) =>
                      onChangeConfig({
                        ...config,
                        cardVerticalPosition: Number(e.target.value),
                      })
                    }
                    className="w-full h-1 bg-[#222732] rounded appearance-none cursor-pointer accent-[#3B82F6]"
                  />
                  <div className="flex justify-between font-mono text-[9px] text-neutral-500">
                    <span>Top (15%)</span>
                    <span>Center (48%)</span>
                    <span>Lower (75%)</span>
                  </div>
                </div>

                {/* 2. Subtitle Vertical Position */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-sans font-medium text-neutral-300">
                      Subtitle Vertical Anchor
                    </span>
                    <span className="font-mono font-bold text-[#D5EB45]">
                      {config.subtitleVerticalPosition}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="30"
                    max="88"
                    step="2"
                    value={config.subtitleVerticalPosition}
                    onChange={(e) =>
                      onChangeConfig({
                        ...config,
                        subtitleVerticalPosition: Number(e.target.value),
                      })
                    }
                    className="w-full h-1 bg-[#222732] rounded appearance-none cursor-pointer accent-[#D5EB45]"
                  />
                  <div className="flex justify-between font-mono text-[9px] text-neutral-500">
                    <span>Mid (50%)</span>
                    <span>Standard Sub (76%)</span>
                    <span>Bottom (85%)</span>
                  </div>
                </div>

                {/* 3. Card Width */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-sans font-medium text-neutral-300">
                      Card Width Scale
                    </span>
                    <span className="font-mono font-bold text-[#3B82F6]">
                      {config.cardWidthPercent}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="75"
                    max="98"
                    step="1"
                    value={config.cardWidthPercent}
                    onChange={(e) =>
                      onChangeConfig({
                        ...config,
                        cardWidthPercent: Number(e.target.value),
                      })
                    }
                    className="w-full h-1 bg-[#222732] rounded appearance-none cursor-pointer accent-[#3B82F6]"
                  />
                  <div className="flex justify-between font-mono text-[9px] text-neutral-500">
                    <span>Slim (75%)</span>
                    <span>Default (92%)</span>
                    <span>Wide (98%)</span>
                  </div>
                </div>
              </div>

              {/* Neural Voice & Voiceover Hook Option */}
              <div className="p-3 rounded-lg border border-[#222732] bg-[#12151C] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Volume2 className="w-3.5 h-3.5 text-[#D5EB45]" />
                    <span className="font-sans font-bold text-xs text-white">
                      AI Neural Voiceover Hook Synthesis
                    </span>
                  </div>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.enableVoiceHook}
                      onChange={(e) =>
                        onChangeConfig({
                          ...config,
                          enableVoiceHook: e.target.checked,
                        })
                      }
                      className="w-3.5 h-3.5 rounded accent-[#D5EB45] cursor-pointer"
                    />
                    <span className="font-sans text-xs text-neutral-300 font-medium">
                      Synthesize Audio Hook
                    </span>
                  </label>
                </div>

                {/* Voice Selection Chips */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                  {[
                    { id: "en-US-ChristopherNeural", name: "Christopher", desc: "Punchy & Energetic" },
                    { id: "en-US-JennyNeural", name: "Jenny", desc: "Clear & Crisp" },
                    { id: "en-US-GuyNeural", name: "Guy", desc: "Casual & Relatable" },
                    { id: "en-US-AriaNeural", name: "Aria", desc: "Narrative & Deep" },
                  ].map((v) => (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() =>
                        onChangeConfig({
                          ...config,
                          ttsVoice: v.id,
                        })
                      }
                      className={`p-2 rounded-lg border text-left transition-all ${
                        config.ttsVoice === v.id
                          ? "bg-[#3B82F6]/15 border-[#3B82F6] text-white"
                          : "bg-[#161922] border-[#222732] text-neutral-400 hover:text-neutral-200"
                      }`}
                    >
                      <div className="font-sans text-xs font-bold text-white">{v.name}</div>
                      <div className="font-sans text-[10px] text-neutral-400">{v.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* 9:16 LIVE INTERACTIVE PREVIEW MODAL */}
      {/* ------------------------------------------------------------------- */}
      <StylePreviewModal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        config={config}
        onChangeConfig={onChangeConfig}
      />
    </div>
  );
};
