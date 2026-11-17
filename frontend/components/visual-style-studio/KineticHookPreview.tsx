"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  VisualStyleConfig,
  WORDART_PRESETS,
  WordArtStyleDefinition,
} from "./types";
import { WordArtBadgeView } from "./WordArtBadgeView";
import { computeAnimationPhase } from "./easing";
import { Play, RotateCcw, Sparkles, Type, Film, Layers } from "lucide-react";

interface Props {
  config: VisualStyleConfig;
  onChangeConfig: (newConfig: VisualStyleConfig) => void;
  hookText: string;
}

export const KineticHookPreview: React.FC<Props> = ({
  config,
  onChangeConfig,
  hookText,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0.0);
  const animFrameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);

  const durationSec = config.hookDurationSec || 3.0;
  const animType = config.hookAnimationType || "slam_in";
  const wordartStyleId = config.hookWordArtStyle || "slam_in";
  const selectedPreset: WordArtStyleDefinition =
    WORDART_PRESETS.find((p) => p.id === wordartStyleId) || WORDART_PRESETS[0];

  const effectiveHookText = hookText || "THE PSYCHOLOGICAL TRICK BEHIND 10M VIEWS";
  const supportingText = config.supportingCaptionText ?? "Watch until the end";
  const showSupporting = config.showSupportingCaption !== false;

  // Playback loop using requestAnimationFrame and exact deterministic easing
  const startPlayback = () => {
    setIsPlaying(true);
    setCurrentTime(0.0);
    startTimeRef.current = performance.now();
  };

  useEffect(() => {
    if (!isPlaying) return;

    const animate = (now: number) => {
      if (!startTimeRef.current) startTimeRef.current = now;
      const elapsed = (now - startTimeRef.current) / 1000.0;

      if (elapsed >= durationSec) {
        setCurrentTime(durationSec);
        setIsPlaying(false);
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        return;
      }

      setCurrentTime(elapsed);
      animFrameRef.current = requestAnimationFrame(animate);
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, durationSec]);

  // Compute current animated frame parameters
  const phaseInfo = computeAnimationPhase(
    currentTime,
    0.0,
    durationSec,
    0.4,
    0.35,
    animType === "slam_in" ? "slam_in" : "ease_out_back",
    "ease_in_cubic"
  );

  // Typewriter text slicing
  let renderedText = effectiveHookText;
  if (animType === "typewriter") {
    if (phaseInfo.phase === "enter") {
      const charCount = Math.max(1, Math.floor(effectiveHookText.length * phaseInfo.progress));
      const cursor = Math.floor(currentTime * 6) % 2 === 0 ? "|" : "";
      renderedText = effectiveHookText.slice(0, charCount) + cursor;
    } else if (phaseInfo.phase === "before") {
      renderedText = "|";
    }
  }

  // Animation transforms
  let translateY = phaseInfo.translateY;
  if (animType === "slide_up" && phaseInfo.phase === "enter") {
    translateY = (1.0 - phaseInfo.easedProgress) * 60;
  }
  let scale = phaseInfo.scale;
  if (animType === "fade_zoom") {
    scale = 0.95 + 0.08 * Math.min(1.0, currentTime / durationSec);
  }

  return (
    <div className="bg-[#101319] border border-[#1E2430] rounded-xl p-3.5 space-y-3 shadow-md">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1C222C] pb-2.5">
        <div className="flex items-center gap-2">
          <Film className="w-4 h-4 text-[#3B82F6]" />
          <h4 className="font-sans font-bold text-xs text-white uppercase tracking-wider">
            Animated Hook &amp; Title Studio (Phase 3)
          </h4>
          <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm bg-[#3B82F6]/15 border border-[#3B82F6]/40 text-[#3B82F6] font-bold">
            Realtime Preview
          </span>
        </div>

        {/* Play / Replay button */}
        <button
          type="button"
          onClick={startPlayback}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-[#3B82F6] hover:bg-[#2563EB] text-white font-mono text-[11px] font-bold shadow-xs transition-all cursor-pointer"
        >
          {isPlaying ? (
            <>
              <RotateCcw className="w-3.5 h-3.5 animate-spin" />
              <span>Playing {currentTime.toFixed(1)}s</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Replay Animation</span>
            </>
          )}
        </button>
      </div>

      {/* Kinetic Canvas Display Box */}
      <div className="relative w-full h-36 bg-[#080A0E] rounded-lg border border-[#1C222C] overflow-hidden flex flex-col items-center justify-center p-3 select-none">
        {/* Subtle grid background */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(#3B82F6 1px, transparent 1px), radial-gradient(#3B82F6 1px, transparent 1px)",
            backgroundSize: "20px 20px",
            backgroundPosition: "0 0, 10px 10px",
          }}
        />

        {/* Phase & Progress Indicator */}
        <div className="absolute top-2 left-2 flex items-center gap-2 font-mono text-[9px] text-neutral-400">
          <span className="px-1.5 py-0.5 rounded-xs bg-[#161B24] border border-[#262F3E]">
            Phase: <strong className="text-white uppercase">{phaseInfo.phase}</strong>
          </span>
          <span className="px-1.5 py-0.5 rounded-xs bg-[#161B24] border border-[#262F3E]">
            Progress: {(phaseInfo.progress * 100).toFixed(0)}%
          </span>
        </div>

        {/* Safe-area line indicator */}
        <div className="absolute inset-x-4 top-1/2 -translate-y-1/2 border-t border-dashed border-neutral-700/40 pointer-events-none" />

        {/* Animated Badge Container */}
        <div
          className="flex flex-col items-center justify-center transition-transform"
          style={{
            opacity: phaseInfo.opacity,
            transform: `translateY(${translateY}px) scale(${scale})`,
            transition: isPlaying ? "none" : "all 0.15s ease-out",
          }}
        >
          <WordArtBadgeView
            text={renderedText}
            preset={selectedPreset}
            fontSize={24}
            className="text-center"
          />

          {/* Supporting Subtitle */}
          {showSupporting && supportingText && (
            <div
              className="mt-2.5 px-3 py-1 rounded-full bg-[#161C26]/90 border border-white/10 shadow-md backdrop-blur-xs transition-opacity"
              style={{
                opacity: phaseInfo.phase === "enter" ? Math.max(0, phaseInfo.progress - 0.2) / 0.8 : phaseInfo.opacity,
              }}
            >
              <span className="font-sans text-[11px] font-medium text-neutral-200">
                {supportingText}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Animation Revealer Controls */}
      <div className="space-y-2 pt-1">
        {/* 1. Kinetic Reveal Style Selector */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="font-mono text-[10px] uppercase font-bold text-neutral-400 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-[#3B82F6]" />
            <span>Kinetic Animation Type:</span>
          </span>
          <div className="flex items-center gap-1 bg-[#0A0D12] p-0.5 rounded-md border border-[#1E232E]">
            {[
              { id: "slam_in", label: "Slam In" },
              { id: "typewriter", label: "Typewriter" },
              { id: "slide_up", label: "Slide Up" },
              { id: "kinetic_pop", label: "Pop Bounce" },
              { id: "fade_zoom", label: "Cinematic" },
            ].map((anim) => {
              const isSelected = animType === anim.id;
              return (
                <button
                  key={anim.id}
                  type="button"
                  onClick={() => {
                    onChangeConfig({
                      ...config,
                      hookAnimationType: anim.id as any,
                    });
                    startPlayback();
                  }}
                  className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all cursor-pointer ${
                    isSelected
                      ? "bg-[#3B82F6] text-white shadow-xs"
                      : "text-neutral-400 hover:text-white"
                  }`}
                >
                  {anim.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. WordArt Preset Selector */}
        <div className="space-y-1">
          <span className="font-mono text-[10px] uppercase font-bold text-neutral-400 flex items-center gap-1">
            <Layers className="w-3 h-3 text-[#00E297]" />
            <span>WordArt Preset Style:</span>
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
            {WORDART_PRESETS.map((preset) => {
              const isSel = wordartStyleId === preset.id;
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => {
                    onChangeConfig({
                      ...config,
                      hookWordArtStyle: preset.id,
                    });
                    startPlayback();
                  }}
                  className={`px-2 py-1.5 rounded-md border text-left transition-all cursor-pointer flex flex-col gap-0.5 ${
                    isSel
                      ? "bg-[#3B82F6]/15 border-[#3B82F6] text-white shadow-xs"
                      : "bg-[#0D0F14] border-[#1C222C] text-neutral-400 hover:text-white hover:border-neutral-700"
                  }`}
                >
                  <span className="font-sans font-bold text-[11px] truncate">
                    {preset.name}
                  </span>
                  <span className="font-mono text-[8px] text-neutral-500 truncate">
                    {preset.fontFamily}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Supporting Subtitle Toggle & Input */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#1C222C]">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showSupporting}
              onChange={(e) => {
                onChangeConfig({
                  ...config,
                  showSupportingCaption: e.target.checked,
                });
              }}
              className="rounded-xs border-[#2A313E] text-[#3B82F6] focus:ring-0 cursor-pointer"
            />
            <span className="font-mono text-[10px] font-bold text-neutral-300 uppercase">
              Supporting Sub-Caption
            </span>
          </label>

          {showSupporting && (
            <div className="flex-1 min-w-[200px]">
              <input
                type="text"
                value={supportingText}
                onChange={(e) => {
                  onChangeConfig({
                    ...config,
                    supportingCaptionText: e.target.value,
                  });
                }}
                placeholder="e.g. Watch until the end · 3-minute breakdown"
                className="w-full px-2.5 py-1 rounded-md border border-[#242C3A] bg-[#0A0D12] font-sans text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-[#3B82F6]"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
