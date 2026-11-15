"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Sparkles,
  Calendar,
  Globe,
  Lock,
  EyeOff,
  Rocket,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Send,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { YoutubeIcon } from "./YoutubeIcon";

interface BulkPublishModalProps {
  isOpen: boolean;
  onClose: () => void;
  clips: any[];
  renderedClips: any[];
  currentChannel: any;
  onSuccess?: () => void;
}

export function BulkPublishModal({
  isOpen,
  onClose,
  clips,
  renderedClips,
  currentChannel,
  onSuccess,
}: BulkPublishModalProps) {
  const [activeTab, setActiveTab] = useState<"publish" | "schedule">("publish");

  // Scheduling state (IST)
  const [startIstTime, setStartIstTime] = useState<string>(() => {
    const now = new Date();
    // Default to +2 hours lead in IST
    const istTime = new Date(now.getTime() + (5.5 + 2) * 3600 * 1000);
    return istTime.toISOString().slice(0, 16);
  });
  const [intervalMinutes, setIntervalMinutes] = useState<number>(30);
  const [bulkVisibility, setBulkVisibility] = useState<"public" | "unlisted" | "private">("unlisted");

  // Scheduled sequence preview
  interface ScheduleRow {
    clip_id: string;
    title: string;
    description: string;
    tags: string[];
    video_file_path: string;
    ist_display: string;
    utc_iso: string;
    scheduled_time: string;
    visibility: "public" | "unlisted" | "private";
    status?: string;
  }
  const [scheduleRows, setScheduleRows] = useState<ScheduleRow[]>([]);

  // Bulk publish execution state
  interface PublishStatus {
    clip_id: string;
    title: string;
    status: "idle" | "publishing" | "published" | "failed";
    youtube_url?: string;
    error?: string;
  }
  const [publishStatuses, setPublishStatuses] = useState<Record<string, PublishStatus>>({});
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishSummary, setPublishSummary] = useState<{ total: number; published: number; failed: number } | null>(null);

  // Recalculate IST Schedule rows whenever target clips, start time, or interval changes
  useEffect(() => {
    if (!isOpen || clips.length === 0) return;

    try {
      // Calculate sequence from start time
      const startDate = new Date(startIstTime);
      const rows: ScheduleRow[] = clips.map((clip, index) => {
        const itemDate = new Date(startDate.getTime() + index * intervalMinutes * 60 * 1000);
        const isoLocal = itemDate.toISOString().slice(0, 16);

        // Compute UTC instant assuming startIstTime was input as IST (+05:30)
        // itemDate in UTC is itemDate - 5.5 hours
        const utcInstant = new Date(itemDate.getTime() - 5.5 * 3600 * 1000);
        const utcStr = utcInstant.toISOString().replace(/\.\d{3}/, "");

        const formattedIst = itemDate.toLocaleString("en-IN", {
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        }) + " IST";

        return {
          clip_id: clip.clip_id,
          title: clip.title || clip.headline || `Short #${index + 1}`,
          description: clip.description || "",
          tags: Array.isArray(clip.tags) ? clip.tags : [],
          video_file_path: clip.rendered_video_url || `short_${clip.clip_id}.mp4`,
          ist_display: formattedIst,
          utc_iso: utcStr,
          scheduled_time: isoLocal,
          visibility: bulkVisibility,
        };
      });

      setScheduleRows(rows);
    } catch (e) {
      console.error("Error generating IST schedule sequence:", e);
    }
  }, [isOpen, clips, startIstTime, intervalMinutes, bulkVisibility]);

  if (!isOpen) return null;

  // Execute Bulk Publish Now (Part C)
  const handleExecuteBulkPublish = async () => {
    if (renderedClips.length === 0) return;
    setIsPublishing(true);
    setPublishSummary(null);

    const initialStatuses: Record<string, PublishStatus> = {};
    renderedClips.forEach((c) => {
      initialStatuses[c.clip_id] = {
        clip_id: c.clip_id,
        title: c.title || `Short #${c.index}`,
        status: "publishing",
      };
    });
    setPublishStatuses(initialStatuses);

    try {
      const payload = {
        items: renderedClips.map((c) => ({
          clip_id: c.clip_id,
          title: c.title || c.headline || "Viral Short",
          description: c.description || "",
          tags: Array.isArray(c.tags) ? c.tags : [],
          video_file_path: c.rendered_video_url || `short_${c.clip_id}.mp4`,
          thumbnail_url: c.preview_url || "",
          visibility: bulkVisibility,
          target_channel_id: currentChannel?.channel_id || "UC_abhyodaya_clips_sandbox",
        })),
      };

      const res = await fetch("http://localhost:8000/api/v1/youtube/bulk-publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Bulk publish failed with status ${res.status}`);
      }

      const data = await res.json();
      const updated = { ...initialStatuses };

      // Mark successes
      (data.published || []).forEach((p: any) => {
        if (updated[p.clip_id]) {
          updated[p.clip_id].status = "published";
          updated[p.clip_id].youtube_url = p.youtube_url;
        }
      });

      // Mark failures
      (data.failed || []).forEach((f: any) => {
        if (updated[f.clip_id]) {
          updated[f.clip_id].status = "failed";
          updated[f.clip_id].error = f.error;
        }
      });

      setPublishStatuses(updated);
      setPublishSummary({
        total: data.total_requested || renderedClips.length,
        published: data.published_count || 0,
        failed: data.failed_count || 0,
      });

      onSuccess?.();
    } catch (err: any) {
      alert(`Bulk Publish Error: ${err.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  // Execute Bulk Schedule (Parts D & E)
  const handleExecuteBulkSchedule = async () => {
    if (scheduleRows.length === 0) return;
    setIsPublishing(true);

    try {
      const payload = {
        start_time_ist: startIstTime,
        interval_minutes: intervalMinutes,
        items: scheduleRows.map((r) => ({
          clip_id: r.clip_id,
          title: r.title,
          description: r.description,
          tags: r.tags,
          video_file_path: r.video_file_path,
          scheduled_time: r.scheduled_time,
          visibility: r.visibility,
          target_channel_id: currentChannel?.channel_id || "UC_abhyodaya_clips_sandbox",
        })),
      };

      const res = await fetch("http://localhost:8000/api/v1/youtube/bulk-schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Bulk scheduling failed with status ${res.status}`);
      }

      const data = await res.json();
      alert(
        `Successfully scheduled ${data.total_scheduled} Shorts in Indian Standard Time (IST — Asia/Kolkata)!`
      );
      onSuccess?.();
      onClose();
    } catch (err: any) {
      alert(`Bulk Schedule Error: ${err.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-3xl bg-surface-container-lowest border-2 border-primary shadow-[6px_6px_0px_#111111] overflow-hidden flex flex-col max-h-[92vh]">
        {/* Architectural Modal Header */}
        <div className="p-4 border-b-2 border-primary bg-surface-container flex items-center justify-between text-primary">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 border-2 border-primary bg-surface-container-lowest flex items-center justify-center shadow-[2px_2px_0px_#111111]">
              <YoutubeIcon className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-headline font-bold text-sm uppercase tracking-tight text-primary">
                  Bulk YouTube Operations
                </h3>
                <span className="font-mono text-[10px] px-2 py-0.5 bg-[#d5eb45] border border-primary font-bold">
                  IST (Asia/Kolkata)
                </span>
              </div>
              <p className="font-mono text-[11px] text-outline mt-0.5">
                Channel: {currentChannel?.channel_title || "Sandbox Channel"} • Dynamic Workflow
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 border border-primary flex items-center justify-center hover:bg-surface-container-high transition-colors"
          >
            <X className="w-4 h-4 text-primary" />
          </button>
        </div>

        {/* Tab Strip */}
        <div className="flex border-b-2 border-primary bg-surface-container-low font-mono text-xs">
          <button
            onClick={() => setActiveTab("publish")}
            className={`flex-1 py-3 px-4 font-bold border-r-2 border-primary transition-all flex items-center justify-center gap-2 ${
              activeTab === "publish"
                ? "bg-primary text-on-primary shadow-inner"
                : "text-on-surface hover:bg-surface-container"
            }`}
          >
            <Rocket className="w-4 h-4" />
            <span>Publish All Rendered ({renderedClips.length} Shorts)</span>
          </button>

          <button
            onClick={() => setActiveTab("schedule")}
            className={`flex-1 py-3 px-4 font-bold transition-all flex items-center justify-center gap-2 ${
              activeTab === "schedule"
                ? "bg-primary text-on-primary shadow-inner"
                : "text-on-surface hover:bg-surface-container"
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>IST Automated Scheduling ({clips.length} Shorts)</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          {/* TAB 1: BULK PUBLISH NOW */}
          {activeTab === "publish" && (
            <div className="space-y-4">
              <div className="p-3 border border-primary bg-surface-container flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold font-headline uppercase block text-primary">
                    Verified Rendered Clips Pool
                  </span>
                  <span className="text-secondary font-mono text-[11px]">
                    Only Shorts with verified output files on disk are eligible for immediate publishing.
                  </span>
                </div>
                <span className="px-2 py-1 font-mono font-bold text-xs bg-surface-container-lowest border border-primary">
                  {renderedClips.length} Eligible
                </span>
              </div>

              {renderedClips.length === 0 ? (
                <div className="p-8 border-2 border-dashed border-primary text-center space-y-2">
                  <AlertCircle className="w-8 h-8 text-amber-600 mx-auto" />
                  <p className="font-mono text-xs font-bold text-primary">
                    No Rendered Shorts Available to Publish
                  </p>
                  <p className="font-mono text-[11px] text-outline">
                    Please click "Render All" on the main studio screen to generate video files first.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="max-h-60 overflow-y-auto border border-primary divide-y divide-primary">
                    {renderedClips.map((clip, idx) => {
                      const st = publishStatuses[clip.clip_id];
                      return (
                        <div
                          key={clip.clip_id}
                          className="p-3 bg-surface-container-lowest flex items-center justify-between gap-3 text-xs"
                        >
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <span className="font-mono font-bold text-[11px] px-1.5 py-0.5 bg-surface-container border border-primary">
                              #{idx + 1}
                            </span>
                            <span className="font-bold truncate text-primary">
                              {clip.title || clip.headline || `Short #${idx + 1}`}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            {st?.status === "publishing" && (
                              <span className="font-mono text-[10px] text-blue-600 font-bold flex items-center gap-1">
                                <RefreshCw className="w-3 h-3 animate-spin" /> Publishing...
                              </span>
                            )}
                            {st?.status === "published" && (
                              <a
                                href={st.youtube_url || "#"}
                                target="_blank"
                                rel="noreferrer"
                                className="font-mono text-[10px] text-green-700 font-bold flex items-center gap-1 hover:underline"
                              >
                                <CheckCircle2 className="w-3 h-3 text-green-600" /> Published{" "}
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                            {st?.status === "failed" && (
                              <span className="font-mono text-[10px] text-red-600 font-bold flex items-center gap-1" title={st.error}>
                                <AlertCircle className="w-3 h-3 text-red-600" /> Failed
                              </span>
                            )}
                            {!st && (
                              <span className="font-mono text-[10px] text-secondary font-bold">
                                Ready
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {publishSummary && (
                    <div className="p-3 border-2 border-primary bg-[#d5eb45]/20 flex items-center justify-between text-xs font-mono">
                      <span>
                        Result: <strong>{publishSummary.published} published</strong>,{" "}
                        <strong>{publishSummary.failed} failed</strong> of {publishSummary.total} Shorts.
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: IST AUTOMATED SCHEDULING */}
          {activeTab === "schedule" && (
            <div className="space-y-4">
              {/* Configuration Controls */}
              <div className="p-4 border-2 border-primary bg-surface-container space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-primary" />
                  <span className="font-headline font-bold text-xs uppercase text-primary">
                    Indian Standard Time (IST — Asia/Kolkata) Parameters
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="font-mono text-[11px] font-bold text-primary uppercase block">
                      First Short Time (IST)
                    </label>
                    <input
                      type="datetime-local"
                      value={startIstTime}
                      onChange={(e) => setStartIstTime(e.target.value)}
                      className="w-full px-2.5 py-1.5 border border-primary bg-surface-container-lowest font-mono text-xs text-primary"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-mono text-[11px] font-bold text-primary uppercase block">
                      Publishing Interval
                    </label>
                    <select
                      value={intervalMinutes}
                      onChange={(e) => setIntervalMinutes(Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 border border-primary bg-surface-container-lowest font-mono text-xs text-primary"
                    >
                      <option value={15}>Every 15 Minutes</option>
                      <option value={30}>Every 30 Minutes</option>
                      <option value={45}>Every 45 Minutes</option>
                      <option value={60}>Every 1 Hour</option>
                      <option value={120}>Every 2 Hours</option>
                      <option value={1440}>Every 24 Hours (Daily)</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="font-mono text-[11px] font-bold text-primary uppercase block">
                      Visibility
                    </label>
                    <select
                      value={bulkVisibility}
                      onChange={(e) => setBulkVisibility(e.target.value as any)}
                      className="w-full px-2.5 py-1.5 border border-primary bg-surface-container-lowest font-mono text-xs text-primary"
                    >
                      <option value="unlisted">Unlisted (Recommended)</option>
                      <option value="public">Public</option>
                      <option value="private">Private</option>
                    </select>
                  </div>
                </div>

                <p className="font-mono text-[10px] text-secondary">
                  * All timestamps are computed in Indian Standard Time (UTC+05:30) and converted to UTC RFC 3339 for YouTube Data API status.publishAt compliance.
                </p>
              </div>

              {/* Sequence Preview Table */}
              <div className="space-y-2">
                <span className="font-mono text-[11px] font-bold uppercase text-primary block">
                  Generated Schedule Sequence ({scheduleRows.length} Shorts)
                </span>
                <div className="max-h-60 overflow-y-auto border border-primary divide-y divide-primary font-mono text-xs">
                  {scheduleRows.map((row, idx) => (
                    <div
                      key={row.clip_id}
                      className="p-2.5 bg-surface-container-lowest flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="font-bold px-1.5 py-0.5 bg-surface-container border border-primary text-[10px]">
                          #{idx + 1}
                        </span>
                        <span className="truncate font-medium">{row.title}</span>
                      </div>

                      <div className="flex items-center gap-3 shrink-0 text-right">
                        <span className="text-primary font-bold">{row.ist_display}</span>
                        <span className="text-[10px] text-outline hidden sm:inline">
                          ({row.utc_iso.slice(11, 16)} UTC)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t-2 border-primary bg-surface-container flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 border-2 border-primary bg-surface-container-lowest text-primary font-mono text-xs font-bold hover:bg-surface-container transition-colors"
          >
            Cancel
          </button>

          {activeTab === "publish" ? (
            <button
              onClick={handleExecuteBulkPublish}
              disabled={renderedClips.length === 0 || isPublishing}
              className="inline-flex items-center gap-2 px-5 py-2 border-2 border-primary bg-[#d5eb45] text-primary font-mono text-xs font-bold shadow-[2px_2px_0px_#111111] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-none transition-all disabled:opacity-50"
            >
              {isPublishing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Publishing Shorts...</span>
                </>
              ) : (
                <>
                  <Rocket className="w-3.5 h-3.5" />
                  <span>Publish All Rendered ({renderedClips.length} Shorts)</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleExecuteBulkSchedule}
              disabled={scheduleRows.length === 0 || isPublishing}
              className="inline-flex items-center gap-2 px-5 py-2 border-2 border-primary bg-primary text-on-primary font-mono text-xs font-bold shadow-[2px_2px_0px_#d5eb45] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-none transition-all disabled:opacity-50"
            >
              {isPublishing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Scheduling in IST...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Confirm Bulk Schedule ({scheduleRows.length} Shorts)</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
