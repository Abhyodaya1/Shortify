"use client";

import React, { useState } from "react";
import {
  Search,
  Sparkles,
  UploadCloud,
  Clock,
  Zap,
  Flame,
  FileText,
  Volume2,
  Plus,
  Link as LinkIcon,
  Crop,
  Type,
  TrendingUp,
  FolderOpen,
  ArrowRight,
} from "lucide-react";
import { YoutubeIcon } from "./YoutubeIcon";

interface DashboardViewProps {
  currentChannel: any;
  onOpenConnectModal: () => void;
  onStartClipping: (url: string, clipType?: string) => void;
  onOpenStudio: () => void;
  recentVideos: any[];
}

export function DashboardView({
  currentChannel,
  onOpenConnectModal,
  onStartClipping,
  onOpenStudio,
  recentVideos,
}: DashboardViewProps) {
  const [videoUrl, setVideoUrl] = useState("");
  const [selectedClipType, setSelectedClipType] = useState<"viral" | "summary" | "action" | "talking_head">("viral");
  const [searchQuery, setSearchQuery] = useState("");

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoUrl.trim()) return;
    onStartClipping(videoUrl.trim(), selectedClipType);
  };

  const filteredVideos = recentVideos.filter((v) =>
    v.title?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 bg-[#fbf9f4] text-[#1b1c19] font-body selection:bg-[#d5eb45]">
      {/* TOP BREADCRUMB & STATUS STRIP (Architectural Neo-Brutalist) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b-2 border-primary pb-4">
        <div className="flex items-center gap-3 font-mono text-xs tracking-wider uppercase text-on-surface flex-wrap">
          <span className="px-2.5 py-1 bg-primary text-on-primary font-bold shadow-[2px_2px_0px_#111111]">
            [INGEST // 01]
          </span>
          <span className="text-outline">/</span>
          <span className="font-bold tracking-tight">AUTONOMOUS VIDEO REPURPOSING WORKSTATION</span>
        </div>
        <div className="flex items-center gap-3 font-mono text-[11px] flex-wrap">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-container-lowest border-2 border-primary shadow-[2px_2px_0px_#111111]">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00e297] animate-pulse"></span>
            <span className="font-bold">WHISPER-LARGE v3: ACTIVE</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#d5eb45] border-2 border-primary shadow-[2px_2px_0px_#111111] text-primary">
            <span className="font-bold">QUOTA: 420m REMAINING</span>
          </div>
        </div>
      </div>

      {/* CONNECT YOUTUBE CHANNEL BANNER (Neo-Brutalist Tactile Surface) */}
      <div className="p-4 sm:p-5 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="w-11 h-11 border-2 border-primary bg-[#f0eee9] flex items-center justify-center shrink-0 shadow-[2px_2px_0px_#111111]">
            <YoutubeIcon className="w-6 h-6 text-red-600" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-headline font-bold text-base text-primary uppercase tracking-tight">
                {currentChannel ? currentChannel.channel_title : "YouTube Channel Sync"}
              </span>
              <span className="font-mono text-[10px] px-2 py-0.5 border border-primary bg-[#d5eb45] text-primary font-bold uppercase tracking-wider shadow-[1px_1px_0px_#111111]">
                {currentChannel ? `${(currentChannel.subscriber_count || 24500).toLocaleString()} Subs` : "OAuth Verified"}
              </span>
              <span className="inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 border border-primary bg-surface-container font-bold uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00e297]"></span>
                AUTO-QUEUE ACTIVE
              </span>
            </div>
            <p className="font-mono text-xs text-outline-variant truncate mt-1">
              {currentChannel
                ? `${currentChannel.custom_url || "@peakheistclips"} • Auto-publishing queue active & quota protected`
                : "Connect your channel to import long-form videos directly and publish scheduled vertical Shorts"}
            </p>
          </div>
        </div>

        <button
          onClick={onOpenConnectModal}
          className="px-4 py-2 border-2 border-primary bg-surface-container-lowest hover:bg-[#d5eb45] text-primary font-mono text-xs uppercase font-bold shrink-0 shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[1px_1px_0px_#111111] transition-all flex items-center gap-2"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{currentChannel ? "Channel Details & Uploads" : "Connect Channel"}</span>
        </button>
      </div>

      {/* SECTION 1: RELAXED HERO INGEST CENTERPIECE (Focal Point) */}
      <div className="flex flex-col bg-surface-container-lowest border-2 border-primary shadow-[4px_4px_0px_#111111] p-6 lg:p-8 relative">
        <div className="absolute -top-3.5 right-6 px-3 py-1 bg-[#d5eb45] border-2 border-primary font-mono text-[10px] font-bold uppercase tracking-wider shadow-[2px_2px_0px_#111111]">
          AI MULTI-MODAL PIPELINE
        </div>

        {/* Hero Header */}
        <div className="max-w-3xl mb-6">
          <div className="flex items-center gap-2 mb-2 font-mono text-xs uppercase font-bold tracking-widest text-outline">
            <Sparkles className="w-4 h-4 text-primary" />
            <span>Autonomous High-Velocity Ingestion</span>
          </div>
          <h1 className="font-headline text-2xl sm:text-3xl lg:text-4xl text-primary uppercase font-bold tracking-tight leading-tight mb-3">
            Turn raw footage into viral{" "}
            <span className="bg-[#d5eb45] px-2.5 py-0.5 border-2 border-primary shadow-[2px_2px_0px_#111111] inline-block">
              9:16
            </span>{" "}
            cultural moments.
          </h1>
          <p className="font-body text-sm sm:text-base text-on-surface-variant leading-relaxed">
            Paste any video URL or drop footage. Whisper audio diarization, auto-reframe computer vision, and kinetic typography instantly craft broadcast-ready vertical shorts.
          </p>
        </div>

        {/* Large Tactile URL Ingest Bar & Action Button */}
        <form onSubmit={handleFormSubmit} className="space-y-4">
          <div className="flex flex-col lg:flex-row items-stretch gap-2 p-2 bg-surface-container-low border-2 border-primary shadow-[3px_3px_0px_#111111]">
            <div className="flex items-center pl-2 pr-1 text-outline">
              <LinkIcon className="w-5 h-5 text-primary" />
            </div>
            <input
              type="text"
              placeholder="Paste YouTube, Twitch, Google Drive, or Zoom URL..."
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              className="w-full bg-surface-container-lowest border-2 border-primary px-3 py-3 font-mono text-xs sm:text-sm text-primary placeholder:text-outline focus:outline-none focus:shadow-[2px_2px_0px_#111111] transition-all"
            />
            <button
              type="submit"
              className="flex items-center justify-center gap-2 px-6 py-3 bg-primary text-on-primary font-mono text-xs sm:text-sm font-bold uppercase tracking-wider border-2 border-primary shadow-[3px_3px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary hover:shadow-[1px_1px_0px_#111111] hover:translate-x-[2px] hover:translate-y-[2px] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all whitespace-nowrap cursor-pointer"
            >
              <Zap className="w-4 h-4 text-[#d5eb45]" />
              <span>GET VIRAL CLIPS ⚡</span>
            </button>
          </div>

          {/* Intent Engine Pill Selector & Alternate Drag Trigger */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-2 border-t border-primary/20">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs uppercase font-bold tracking-wider text-outline mr-1">
                Intent Mode:
              </span>
              <button
                type="button"
                onClick={() => setSelectedClipType("viral")}
                className={`px-3 py-1.5 border-2 border-primary font-mono text-xs font-bold transition-all cursor-pointer ${
                  selectedClipType === "viral"
                    ? "bg-primary text-on-primary shadow-[2px_2px_0px_#111111]"
                    : "bg-surface-container-lowest text-on-surface hover:bg-surface-container-high shadow-[1px_1px_0px_#111111]"
                }`}
              >
                ★ Viral Moments
              </button>
              <button
                type="button"
                onClick={() => setSelectedClipType("action")}
                className={`px-3 py-1.5 border-2 border-primary font-mono text-xs font-bold transition-all cursor-pointer ${
                  selectedClipType === "action"
                    ? "bg-primary text-on-primary shadow-[2px_2px_0px_#111111]"
                    : "bg-surface-container-lowest text-on-surface hover:bg-surface-container-high shadow-[1px_1px_0px_#111111]"
                }`}
              >
                ⚡ Action Highlights
              </button>
              <button
                type="button"
                onClick={() => setSelectedClipType("talking_head")}
                className={`px-3 py-1.5 border-2 border-primary font-mono text-xs font-bold transition-all cursor-pointer ${
                  selectedClipType === "talking_head"
                    ? "bg-primary text-on-primary shadow-[2px_2px_0px_#111111]"
                    : "bg-surface-container-lowest text-on-surface hover:bg-surface-container-high shadow-[1px_1px_0px_#111111]"
                }`}
              >
                🎙 Speaker Focus
              </button>
              <button
                type="button"
                onClick={() => setSelectedClipType("summary")}
                className={`px-3 py-1.5 border-2 border-primary font-mono text-xs font-bold transition-all cursor-pointer ${
                  selectedClipType === "summary"
                    ? "bg-primary text-on-primary shadow-[2px_2px_0px_#111111]"
                    : "bg-surface-container-lowest text-on-surface hover:bg-surface-container-high shadow-[1px_1px_0px_#111111]"
                }`}
              >
                📑 Fast Summary
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onOpenStudio}
                className="flex items-center gap-2 px-3 py-1.5 bg-surface-container border-2 border-dashed border-primary hover:bg-surface-container-high cursor-pointer transition-colors"
              >
                <UploadCloud className="w-4 h-4 text-primary" />
                <span className="font-mono text-xs font-bold text-primary uppercase">
                  Drop Master File (MP4/MOV up to 4K)
                </span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* SECTION 2: PRE-EXTRACTION PRESETS & DIRECTIVES */}
      <div className="flex flex-col gap-3 my-2">
        <div className="flex items-center justify-between pb-2 border-b-2 border-primary">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-primary"></span>
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-primary">
              Pre-Extraction Presets &amp; Directives
            </span>
          </div>
          <span className="font-mono text-[10px] text-outline uppercase tracking-wider">
            [TAILORED EDITORIAL RULES]
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* PRESET A: DURATION WINDOW */}
          <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-primary/20">
                <span className="font-mono text-xs uppercase font-bold text-primary">Duration Window</span>
                <span className="font-mono text-[10px] font-bold text-[#586400]">[RETENTION PEAK]</span>
              </div>
              <p className="font-body text-xs text-on-surface-variant mb-3 leading-relaxed">
                Constrains target clips to high-velocity algorithmic intervals optimal for TikTok, Reels, and Shorts.
              </p>
              <div className="grid grid-cols-4 gap-1 p-1 bg-surface-container border border-primary">
                <span className="py-1 text-center font-mono text-[10px] font-bold text-outline">AUTO</span>
                <span className="py-1 text-center font-mono text-[10px] font-bold bg-primary text-on-primary shadow-[1px_1px_0px_#111111]">30-60s</span>
                <span className="py-1 text-center font-mono text-[10px] font-bold text-outline">60-90s</span>
                <span className="py-1 text-center font-mono text-[10px] font-bold text-outline">2-3m</span>
              </div>
            </div>
            <div className="mt-3 pt-2 border-t border-primary/20 flex items-center justify-between text-outline font-mono text-[10px]">
              <span>Optimal: <strong className="text-primary font-bold">42s - 58s</strong></span>
              <TrendingUp className="w-3.5 h-3.5 text-primary" />
            </div>
          </div>

          {/* PRESET B: ASPECT & REFRAMING */}
          <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-primary/20">
                <span className="font-mono text-xs uppercase font-bold text-primary">Aspect &amp; Framing</span>
                <span className="font-mono text-[10px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold">[AUTO-TRACK]</span>
              </div>
              <p className="font-body text-xs text-on-surface-variant mb-3 leading-relaxed">
                Dynamic facial centering with adaptive smart-crop to convert wide raw feeds to native 9:16.
              </p>
              <div className="flex items-center gap-2.5 p-2 border border-primary bg-surface-container-low">
                <Crop className="w-4 h-4 text-primary shrink-0" />
                <div className="flex flex-col">
                  <span className="font-mono text-xs font-bold text-primary">Split Screen 9:16</span>
                  <span className="font-mono text-[10px] text-outline">Speaker Top + Gameplay B-roll Bottom</span>
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2 border-t border-primary/20 flex items-center justify-between text-outline font-mono text-[10px]">
              <span>Face Mesh: <strong className="text-primary font-bold">120 FPS</strong></span>
              <span className="text-[#00e297] font-bold">● ONLINE</span>
            </div>
          </div>

          {/* PRESET C: KINETIC TYPOGRAPHY */}
          <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-primary/20">
                <span className="font-mono text-xs uppercase font-bold text-primary">Kinetic Typography</span>
                <span className="font-mono text-[10px] font-bold text-primary">[STYLE v2]</span>
              </div>
              <p className="font-body text-xs text-on-surface-variant mb-3 leading-relaxed">
                Per-word sync animated captions with real-time dynamic pop and high-contrast neo-strokes.
              </p>
              <div className="p-2 border border-primary bg-surface-container-low flex items-center justify-between">
                <div className="flex flex-col">
                  <span className="font-mono text-xs font-bold uppercase tracking-tight text-primary">Hormozi Pop / Acid Lime</span>
                  <span className="font-mono text-[10px] text-outline">Arial Black + 3.0px Black Shadow</span>
                </div>
                <div className="px-2 py-0.5 bg-[#d5eb45] border border-primary font-mono text-[10px] font-bold shadow-[1px_1px_0px_#111111]">
                  ACTIVE
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2 border-t border-primary/20 flex items-center justify-between text-outline font-mono text-[10px]">
              <span>Lexicon: <strong className="text-primary font-bold">Slang &amp; Emojis</strong></span>
              <Type className="w-3.5 h-3.5 text-primary" />
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: ACTIVE STUDIO ARCHIVE (Video Table) */}
      <div className="flex flex-col gap-3 my-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b-2 border-primary">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-primary" />
            <h2 className="font-headline text-base uppercase font-bold tracking-tight text-primary">
              Active Studio Archive
            </h2>
            <span className="px-2 py-0.5 bg-surface-container-highest border border-primary font-mono text-[10px] font-bold">
              [{filteredVideos.length.toString().padStart(2, "0")} INGESTS READY]
            </span>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-outline absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Filter projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary placeholder:text-outline focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
            />
          </div>
        </div>

        {/* Spacious Bento Rows */}
        <div className="flex flex-col gap-2.5">
          {filteredVideos.length === 0 ? (
            <div className="p-8 text-center border-2 border-dashed border-primary bg-surface-container-lowest font-mono text-xs text-outline">
              No matching video ingests found. Paste a URL above to start clipping.
            </div>
          ) : (
            filteredVideos.map((vid) => (
              <div
                key={vid.id}
                className="p-3 sm:p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] hover:bg-surface-container-low transition-all flex flex-col lg:flex-row lg:items-center justify-between gap-4"
              >
                <div className="flex items-center gap-4 min-w-0">
                  {/* Thumbnail with duration badge */}
                  <div className="w-28 sm:w-36 aspect-video bg-primary relative border-2 border-primary shadow-[2px_2px_0px_#111111] overflow-hidden shrink-0">
                    <img
                      src={vid.thumbnail}
                      alt={vid.title}
                      className="w-full h-full object-cover"
                    />
                    <span className="absolute bottom-1 right-1 px-1.5 py-0.5 bg-primary text-on-primary font-mono text-[9px] font-bold border border-primary shadow-[1px_1px_0px_#111111]">
                      {vid.duration_min || "14:20"}
                    </span>
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="font-mono text-[10px] px-1.5 py-0.5 border border-primary bg-red-100 text-red-700 font-bold flex items-center gap-1">
                        <YoutubeIcon className="w-2.5 h-2.5 text-red-600" />
                        YouTube
                      </span>
                      <span className="font-mono text-[10px] px-1.5 py-0.5 border border-primary bg-surface font-bold">
                        9:16 VERTICAL
                      </span>
                      <span className="font-mono text-[10px] px-1.5 py-0.5 border border-primary bg-[#d5eb45] text-primary font-bold uppercase">
                        {vid.video_type || "Viral Clips"}
                      </span>
                    </div>

                    <h3 className="font-headline font-bold text-sm text-primary truncate max-w-lg">
                      {vid.title}
                    </h3>
                    <p className="font-mono text-[11px] text-outline mt-0.5">
                      Imported: {vid.created_date || "Today"} • {vid.clip_count || 3} Clips Generated • High-Retention Pool Ready
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end lg:self-center">
                  <button
                    onClick={onOpenStudio}
                    className="flex items-center gap-2 px-4 py-2 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary hover:shadow-[1px_1px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] transition-all"
                  >
                    <span>OPEN STUDIO</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
