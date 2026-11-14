"use client";

import React, { useRef, useState } from "react";
import {
  Film,
  Music,
  Type,
  Layers,
  Lock,
  Unlock,
  Volume2,
  VolumeX,
  Eye,
  ZoomIn,
  ZoomOut,
  Sliders,
} from "lucide-react";
import { Timeline, Track, Clip, TrackType } from "../types/timeline";

interface TimelineEditorProps {
  timeline: Timeline | null;
  currentTimeMs: number;
  onTimeUpdate: (timeMs: number) => void;
  onSelectClip?: (clip: Clip) => void;
  selectedClipId?: string | null;
}

export const TimelineEditor: React.FC<TimelineEditorProps> = ({
  timeline,
  currentTimeMs,
  onTimeUpdate,
  onSelectClip,
  selectedClipId,
}) => {
  const [zoomFactor, setZoomFactor] = useState(1); // 1x to 3x
  const timelineRef = useRef<HTMLDivElement>(null);

  const durationMs = React.useMemo(() => {
    if (!timeline) return 15000;
    let max = 0;
    timeline.tracks.forEach((track) => {
      track.clips.forEach((clip) => {
        const end = clip.start_time_ms + clip.duration_ms;
        if (end > max) max = end;
      });
    });
    return max || 15000;
  }, [timeline]);

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, clickX / rect.width));
    const newTime = Math.round(percentage * durationMs);
    onTimeUpdate(newTime);
  };

  const getTrackIcon = (type: TrackType) => {
    switch (type) {
      case "video":
        return <Film className="w-3.5 h-3.5 text-blue-400" />;
      case "audio":
        return <Music className="w-3.5 h-3.5 text-emerald-400" />;
      case "caption":
        return <Type className="w-3.5 h-3.5 text-amber-400" />;
      default:
        return <Layers className="w-3.5 h-3.5 text-purple-400" />;
    }
  };

  const getClipStyle = (type: TrackType, isSelected: boolean) => {
    switch (type) {
      case "video":
        return isSelected
          ? "bg-blue-600/90 border-blue-300 ring-2 ring-blue-400 text-white"
          : "bg-blue-900/60 hover:bg-blue-800/80 border-blue-700/80 text-blue-100";
      case "audio":
        return isSelected
          ? "bg-emerald-600/90 border-emerald-300 ring-2 ring-emerald-400 text-white"
          : "bg-emerald-950/70 hover:bg-emerald-900/80 border-emerald-800/80 text-emerald-100";
      case "caption":
        return isSelected
          ? "bg-amber-600/90 border-amber-300 ring-2 ring-amber-400 text-white"
          : "bg-amber-950/70 hover:bg-amber-900/80 border-amber-800/80 text-amber-100";
      default:
        return isSelected
          ? "bg-purple-600/90 border-purple-300 ring-2 ring-purple-400 text-white"
          : "bg-purple-950/70 hover:bg-purple-900/80 border-purple-800/80 text-purple-100";
    }
  };

  // Generate tick marks (e.g. every 1 or 2 seconds)
  const ticks = React.useMemo(() => {
    const totalSeconds = Math.ceil(durationMs / 1000);
    const tickInterval = totalSeconds > 30 ? 5 : totalSeconds > 10 ? 2 : 1;
    const result: number[] = [];
    for (let s = 0; s <= totalSeconds; s += tickInterval) {
      result.push(s);
    }
    return result;
  }, [durationMs]);

  const playheadPercent = Math.min(100, Math.max(0, (currentTimeMs / durationMs) * 100));

  return (
    <div className="w-full flex flex-col bg-neutral-950 border border-neutral-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Header Bar */}
      <div className="px-4 py-2.5 bg-neutral-900 border-b border-neutral-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-neutral-400" />
          <span className="text-xs font-semibold text-neutral-200">
            Multi-Track Timeline (Level 4 NLE)
          </span>
          <span className="text-[11px] text-neutral-500 font-mono">
            {timeline?.tracks.length || 0} Tracks · {timeline?.fps || 30} FPS
          </span>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-1.5 bg-neutral-950 px-2 py-1 rounded-lg border border-neutral-800 text-neutral-400">
          <button
            onClick={() => setZoomFactor((z) => Math.max(1, z - 0.5))}
            className="hover:text-neutral-200"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[11px] font-mono px-1">{zoomFactor}x</span>
          <button
            onClick={() => setZoomFactor((z) => Math.min(3, z + 0.5))}
            className="hover:text-neutral-200"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Timeline Workspace */}
      <div className="flex flex-col relative overflow-x-auto select-none">
        {/* Time ruler */}
        <div className="flex border-b border-neutral-800 bg-neutral-950/80">
          {/* Header left spacer matching track headers */}
          <div className="w-48 shrink-0 px-3 py-1.5 text-[10px] font-mono text-neutral-500 uppercase tracking-wider border-r border-neutral-800">
            Track Name
          </div>
          {/* Ruler ticks */}
          <div
            ref={timelineRef}
            onClick={handleTimelineClick}
            className="flex-1 relative h-7 cursor-pointer"
            style={{ width: `${zoomFactor * 100}%` }}
          >
            {ticks.map((sec) => {
              const pct = (sec / (durationMs / 1000)) * 100;
              return (
                <div
                  key={sec}
                  className="absolute top-0 bottom-0 border-l border-neutral-800/80 text-[10px] font-mono text-neutral-500 pl-1 pt-1"
                  style={{ left: `${pct}%` }}
                >
                  {sec}s
                </div>
              );
            })}
          </div>
        </div>

        {/* Tracks Area */}
        <div className="relative">
          {/* Synchronized Playhead Needle */}
          <div
            className="absolute top-0 bottom-0 z-30 pointer-events-none flex flex-col items-center"
            style={{
              left: `calc(12rem + (100% - 12rem) * (${playheadPercent} / 100))`,
            }}
          >
            <div className="w-3 h-3 bg-rose-500 rotate-45 -mt-1 shadow-md shadow-rose-500/50" />
            <div className="w-[2px] flex-1 bg-rose-500 shadow-sm" />
          </div>

          {timeline?.tracks.map((track) => (
            <div
              key={track.track_id}
              className="flex border-b border-neutral-800/60 hover:bg-neutral-900/30 transition-colors h-14"
            >
              {/* Track Left Header */}
              <div className="w-48 shrink-0 px-3 py-2 flex items-center justify-between border-r border-neutral-800 bg-neutral-900/60 z-10">
                <div className="flex items-center gap-2 overflow-hidden">
                  {getTrackIcon(track.track_type)}
                  <span className="text-xs font-medium text-neutral-200 truncate">
                    {track.name}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-neutral-500">
                  {track.track_type === "audio" && (
                    <button
                      className="p-1 hover:text-neutral-300 rounded"
                      title={track.muted ? "Muted" : "Audio Active"}
                    >
                      {track.muted ? (
                        <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                      ) : (
                        <Volume2 className="w-3.5 h-3.5" />
                      )}
                    </button>
                  )}
                  <button
                    className="p-1 hover:text-neutral-300 rounded"
                    title={track.locked ? "Locked" : "Unlocked"}
                  >
                    {track.locked ? (
                      <Lock className="w-3.5 h-3.5 text-amber-400" />
                    ) : (
                      <Unlock className="w-3.5 h-3.5 opacity-40 hover:opacity-100" />
                    )}
                  </button>
                </div>
              </div>

              {/* Track Clips Canvas Row */}
              <div
                onClick={handleTimelineClick}
                className="flex-1 relative cursor-pointer bg-neutral-950/40 p-1"
                style={{ width: `${zoomFactor * 100}%` }}
              >
                {track.clips.map((clip) => {
                  const leftPct = (clip.start_time_ms / durationMs) * 100;
                  const widthPct = (clip.duration_ms / durationMs) * 100;
                  const isSelected = selectedClipId === clip.clip_id;

                  return (
                    <div
                      key={clip.clip_id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectClip?.(clip);
                      }}
                      className={`absolute top-1 bottom-1 rounded-lg border px-2 py-1 flex flex-col justify-between overflow-hidden shadow-sm transition-all text-[11px] ${getClipStyle(
                        track.track_type,
                        isSelected
                      )}`}
                      style={{
                        left: `${leftPct}%`,
                        width: `${Math.max(1.5, widthPct)}%`,
                      }}
                      title={`${clip.text_content || clip.asset_id || "Clip"}: ${clip.duration_ms / 1000}s`}
                    >
                      <div className="flex items-center justify-between font-semibold truncate leading-none">
                        <span className="truncate">
                          {clip.text_content
                            ? `"${clip.text_content}"`
                            : clip.asset_id || "Media Cut"}
                        </span>
                        <span className="text-[10px] opacity-75 font-mono ml-1">
                          {(clip.duration_ms / 1000).toFixed(1)}s
                        </span>
                      </div>

                      {/* Visual indicator (Waveform or Mini-bar) */}
                      {track.track_type === "audio" && (
                        <div className="flex items-end gap-0.5 h-2.5 opacity-60 overflow-hidden">
                          {Array.from({ length: 16 }).map((_, i) => (
                            <div
                              key={i}
                              className="w-1 bg-emerald-400 rounded-full"
                              style={{ height: `${30 + (i % 5) * 15}%` }}
                            />
                          ))}
                        </div>
                      )}

                      {track.track_type === "video" && (
                        <div className="text-[9px] opacity-75 font-mono truncate">
                          in: {(clip.source_in_ms || 0) / 1000}s
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

