"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Maximize2,
  Pencil,
  Trash2,
  Check,
  Sparkles,
} from "lucide-react";
import { Timeline, Track, Clip, Annotation } from "../types/timeline";

interface InteractivePlayerProps {
  timeline: Timeline | null;
  currentTimeMs: number;
  onTimeUpdate: (timeMs: number) => void;
  annotations: Annotation[];
  onAddAnnotation: (annotation: Annotation) => void;
  onDeleteAnnotation?: (id: string) => void;
  onApplyAnnotationEdit?: (annotation: Annotation, instruction: string) => void;
}

export const InteractivePlayer: React.FC<InteractivePlayerProps> = ({
  timeline,
  currentTimeMs,
  onTimeUpdate,
  annotations,
  onAddAnnotation,
  onDeleteAnnotation,
  onApplyAnnotationEdit,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [drawMode, setDrawMode] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [currentBox, setCurrentBox] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [annotationPrompt, setAnnotationPrompt] = useState("");
  const [pendingAnnotation, setPendingAnnotation] = useState<Annotation | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);
  const timeRef = useRef<number>(currentTimeMs);

  useEffect(() => {
    timeRef.current = currentTimeMs;
  }, [currentTimeMs]);

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

  // Format milliseconds into MM:SS.S
  const formatTime = (ms: number) => {
    const totalSeconds = ms / 1000;
    const mins = Math.floor(totalSeconds / 60);
    const secs = (totalSeconds % 60).toFixed(1);
    return `${mins.toString().padStart(2, "0")}:${secs.padStart(4, "0")}`;
  };

  // Playback loop
  useEffect(() => {
    if (!isPlaying) {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      lastTimeRef.current = null;
      return;
    }

    const tick = (now: number) => {
      if (!lastTimeRef.current) lastTimeRef.current = now;
      const delta = now - lastTimeRef.current;
      lastTimeRef.current = now;

      const nextTime = timeRef.current + delta;
      if (nextTime >= durationMs) {
        setIsPlaying(false);
        onTimeUpdate(0);
      } else {
        onTimeUpdate(nextTime);
      }

      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isPlaying, durationMs, onTimeUpdate]);

  // Extract active clips at currentTimeMs
  const activeVideoClip = React.useMemo(() => {
    if (!timeline) return null;
    const videoTrack = timeline.tracks.find((t) => t.track_type === "video");
    if (!videoTrack) return null;
    return videoTrack.clips.find(
      (c) => c.start_time_ms <= currentTimeMs && currentTimeMs < c.start_time_ms + c.duration_ms
    );
  }, [timeline, currentTimeMs]);

  const activeCaptionClip = React.useMemo(() => {
    if (!timeline) return null;
    const captionTrack = timeline.tracks.find((t) => t.track_type === "caption");
    if (!captionTrack) return null;
    return captionTrack.clips.find(
      (c) => c.start_time_ms <= currentTimeMs && currentTimeMs < c.start_time_ms + c.duration_ms
    );
  }, [timeline, currentTimeMs]);

  // Handle canvas drawing for annotations
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawMode) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsDrawing(true);
    setStartPoint({ x, y });
    setCurrentBox({ x, y, w: 0, h: 0 });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPoint || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    const x = Math.min(startPoint.x, currentX);
    const y = Math.min(startPoint.y, currentY);
    const w = Math.abs(currentX - startPoint.x);
    const h = Math.abs(currentY - startPoint.y);

    setCurrentBox({ x, y, w, h });
  };

  const handleMouseUp = () => {
    if (!isDrawing || !currentBox || !canvasRef.current) return;
    setIsDrawing(false);

    if (currentBox.w > 20 && currentBox.h > 20) {
      const canvas = canvasRef.current;
      // Normalize bounds relative to canvas width & height (0.0 to 1.0)
      const normalizedBounds = {
        x: Number((currentBox.x / canvas.width).toFixed(3)),
        y: Number((currentBox.y / canvas.height).toFixed(3)),
        width: Number((currentBox.w / canvas.width).toFixed(3)),
        height: Number((currentBox.h / canvas.height).toFixed(3)),
      };

      const newAnnotation: Annotation = {
        id: `annot_${Date.now()}`,
        timestamp_ms: Math.round(currentTimeMs),
        bounds: normalizedBounds,
        color: "var(--color-destructive)",
      };

      setPendingAnnotation(newAnnotation);
      setAnnotationPrompt("Isolate speaker and auto-zoom on this section");
    }
    setStartPoint(null);
  };

  const confirmPendingAnnotation = () => {
    if (!pendingAnnotation) return;
    onAddAnnotation(pendingAnnotation);
    if (onApplyAnnotationEdit && annotationPrompt.trim()) {
      onApplyAnnotationEdit(pendingAnnotation, annotationPrompt.trim());
    }
    setPendingAnnotation(null);
    setCurrentBox(null);
    setDrawMode(false);
    setAnnotationPrompt("");
  };

  const cancelPendingAnnotation = () => {
    setPendingAnnotation(null);
    setCurrentBox(null);
  };

  // Render canvas overlay annotations
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw saved annotations visible around current timestamp (+-1.5s)
    annotations.forEach((annot) => {
      if (Math.abs(annot.timestamp_ms - currentTimeMs) < 1500) {
        ctx.strokeStyle = annot.color || "var(--color-destructive)";
        ctx.lineWidth = 3;
        ctx.setLineDash([6, 4]);
        const bx = annot.bounds.x * canvas.width;
        const by = annot.bounds.y * canvas.height;
        const bw = annot.bounds.width * canvas.width;
        const bh = annot.bounds.height * canvas.height;
        ctx.strokeRect(bx, by, bw, bh);

        // Label
        ctx.fillStyle = annot.color || "var(--color-destructive)";
        ctx.font = "bold 11px var(--font-sans)";
        ctx.fillText(`Target (${formatTime(annot.timestamp_ms)})`, bx + 4, by - 6);
      }
    });

    // Draw active drawing box
    if (currentBox) {
      ctx.strokeStyle = "var(--color-accent)";
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 2]);
      ctx.strokeRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
      ctx.fillStyle = "rgba(129, 225, 218, 0.15)";
      ctx.fillRect(currentBox.x, currentBox.y, currentBox.w, currentBox.h);
    }
  }, [annotations, currentTimeMs, currentBox]);

  const isWide = (timeline?.width || 1920) >= (timeline?.height || 1080);

  return (
    <div className="w-full flex flex-col bg-neutral-950 border border-neutral-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Top Bar / Inspector header */}
      <div className="px-4 py-2.5 bg-neutral-900 border-b border-neutral-800 flex items-center justify-between text-xs text-neutral-400">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-medium text-neutral-200">
            {timeline?.title || "Agent Preview"}
          </span>
          <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 font-mono">
            {timeline?.width || 1920}x{timeline?.height || 1080} ({isWide ? "16:9" : "9:16"})
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setDrawMode(!drawMode)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              drawMode
                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                : "bg-neutral-800 hover:bg-neutral-700 text-neutral-300"
            }`}
            title="Spatial Annotation Pen"
          >
            <Pencil className="w-3.5 h-3.5" />
            {drawMode ? "Annotate Active" : "Annotate (Draw)"}
          </button>
        </div>
      </div>

      {/* Main Viewport Screen */}
      <div
        ref={containerRef}
        className="relative w-full aspect-video bg-neutral-950 flex items-center justify-center overflow-hidden select-none"
      >
        {/* Dynamic Mock Video Footage Renderer */}
        <div
          className={`relative overflow-hidden shadow-inner flex flex-col items-center justify-center ${
            isWide ? "w-full h-full" : "h-full aspect-[9/16]"
          } bg-gradient-to-br from-neutral-900 via-neutral-950 to-neutral-900`}
        >
          {/* Simulated Scene Graphic Background */}
          <div className="absolute inset-0 opacity-30 bg-[radial-gradient(var(--color-accent)_1px,transparent_1px)] [background-size:var(--space-2)_var(--space-2)]" />

          {/* Active Clip Status / Scene Simulator */}
          {activeVideoClip ? (
            <div className="z-10 flex flex-col items-center gap-3 p-6 text-center animate-fade-in">
              <div
                className="w-28 h-28 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg transition-transform duration-300"
                style={{
                  transform: `scale(${activeVideoClip.transform?.scale_x || 1}) translate(${
                    activeVideoClip.transform?.x || 0
                  }px, ${activeVideoClip.transform?.y || 0}px)`,
                }}
              >
                <Sparkles className="w-12 h-12 text-white/90" />
              </div>
              <div>
                <p className="text-sm font-semibold text-neutral-200">
                  {activeVideoClip.asset_id || "Active Video Angle"}
                </p>
                <p className="text-xs text-neutral-400 font-mono mt-0.5">
                  Clip: {activeVideoClip.clip_id.slice(0, 8)} | Speed: {activeVideoClip.playback_rate || 1.0}x
                </p>
              </div>
            </div>
          ) : (
            <div className="z-10 text-neutral-500 text-sm font-medium">
              No clip on playhead
            </div>
          )}

          {/* Kinetic Captions Overlay */}
          {activeCaptionClip?.text_content && (
            <div className="absolute bottom-12 px-6 py-2.5 max-w-xl text-center z-20">
              <span
                className="inline-block px-4 py-1.5 rounded-lg font-black tracking-wide shadow-2xl backdrop-blur-md"
                style={{
                  backgroundColor: "rgba(0,0,0,0.75)",
                  color: activeCaptionClip.style_props?.color || "var(--color-white)",
                  fontSize: activeCaptionClip.style_props?.font_size || "18px",
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                {activeCaptionClip.text_content}
              </span>
            </div>
          )}

          {/* Drawing Canvas Overlay */}
          <canvas
            ref={canvasRef}
            width={854}
            height={480}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className={`absolute inset-0 w-full h-full z-30 ${
              drawMode ? "cursor-crosshair pointer-events-auto" : "pointer-events-none"
            }`}
          />
        </div>

        {/* Modal Prompt on Completed Annotation Drawing */}
        {pendingAnnotation && (
          <div className="absolute top-4 right-4 z-40 bg-neutral-900/95 backdrop-blur-md border border-neutral-700 rounded-xl p-4 shadow-2xl w-80 flex flex-col gap-3 animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                <Pencil className="w-3.5 h-3.5" />
                Annotation at {formatTime(pendingAnnotation.timestamp_ms)}
              </span>
              <button
                onClick={cancelPendingAnnotation}
                className="text-neutral-400 hover:text-neutral-200"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs text-neutral-400">
              Selected area: ({pendingAnnotation.bounds.width * 100}% ×{" "}
              {pendingAnnotation.bounds.height * 100}%)
            </p>
            <input
              type="text"
              value={annotationPrompt}
              onChange={(e) => setAnnotationPrompt(e.target.value)}
              placeholder="e.g. Isolate speaker, remove mic..."
              className="w-full bg-neutral-950 border border-neutral-700 rounded-lg px-2.5 py-1.5 text-xs text-neutral-200 placeholder:text-neutral-500 focus:outline-none focus:border-rose-500"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={cancelPendingAnnotation}
                className="px-2.5 py-1 rounded bg-neutral-800 text-xs text-neutral-300 hover:bg-neutral-700"
              >
                Cancel
              </button>
              <button
                onClick={confirmPendingAnnotation}
                className="px-3 py-1 rounded bg-rose-600 text-xs font-medium text-white hover:bg-rose-500 flex items-center gap-1"
              >
                <Check className="w-3.5 h-3.5" /> Apply Edit
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Transport Controls Bar */}
      <div className="px-4 py-3 bg-neutral-900 border-t border-neutral-800 flex items-center justify-between gap-4">
        {/* Playback buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onTimeUpdate(0)}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition-colors"
            title="Rewind to start"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-2.5 rounded-full bg-neutral-100 hover:bg-white text-neutral-950 transition-transform active:scale-95 shadow-md"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
          </button>
          <div className="font-mono text-xs text-neutral-300">
            <span>{formatTime(currentTimeMs)}</span>
            <span className="text-neutral-600 mx-1">/</span>
            <span className="text-neutral-500">{formatTime(durationMs)}</span>
          </div>
        </div>

        {/* Global Progress Scrubber */}
        <div className="flex-1 max-w-xl mx-4">
          <input
            type="range"
            min={0}
            max={durationMs}
            value={currentTimeMs}
            onChange={(e) => onTimeUpdate(Number(e.target.value))}
            className="w-full h-1.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-rose-500 hover:accent-rose-400"
          />
        </div>

        {/* Audio & Display controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition-colors"
            title={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <button
            onClick={() => {
              if (containerRef.current) {
                if (document.fullscreenElement) {
                  document.exitFullscreen();
                } else {
                  containerRef.current.requestFullscreen();
                }
              }
            }}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition-colors"
            title="Toggle Fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

