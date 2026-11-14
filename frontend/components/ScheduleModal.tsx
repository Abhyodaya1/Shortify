"use client";

import React, { useState } from "react";
import { Calendar, Globe, Lock, EyeOff, X, Rocket } from "lucide-react";
import { YoutubeIcon } from "./YoutubeIcon";

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  clip: any;
  currentChannel: any;
  onScheduled: (job: any) => void;
}

export function ScheduleModal({
  isOpen,
  onClose,
  clip,
  currentChannel,
  onScheduled,
}: ScheduleModalProps) {
  const [scheduledDate, setScheduledDate] = useState<string>(() => {
    const d = new Date();
    d.setHours(d.getHours() + 2);
    return d.toISOString().slice(0, 16);
  });
  const [visibility, setVisibility] = useState<"public" | "unlisted" | "private">("unlisted");
  const [title, setTitle] = useState<string>(clip?.headline || "Viral Short");
  const [description, setDescription] = useState<string>(() => {
    return `${clip?.headline || "Exciting Moment"}\n\nProduced with Motion Video Agent.\n\n#Shorts #CreatorGrowth #Viral`;
  });
  const [tags, setTags] = useState<string>("Shorts, Creator, Growth, HighPerformance, Storytelling");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !clip) return null;

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const tagList = tags.split(",").map((t) => t.trim()).filter(Boolean);
      const res = await fetch("http://localhost:8000/api/v1/youtube/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clip_id: clip.clip_id,
          title: title,
          description: description,
          tags: tagList,
          video_file_path: clip.rendered_video_url || `short_${clip.clip_id}.mp4`,
          thumbnail_url: clip.preview_url || "",
          scheduled_time: scheduledDate,
          target_channel_id: currentChannel?.channel_id || "UC_abhyodaya_clips_sandbox",
          visibility: visibility,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to schedule clip");
      }

      const data = await res.json();
      onScheduled(data.scheduled_job);
      onClose();
    } catch (err: any) {
      alert(`Scheduling error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-xl bg-surface-container-lowest border-2 border-primary shadow-[5px_5px_0px_#111111] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b-2 border-primary flex items-center justify-between bg-surface-container text-primary">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 border-2 border-primary bg-surface-container-lowest flex items-center justify-center shadow-[2px_2px_0px_#111111]">
              <YoutubeIcon className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-headline font-bold text-sm uppercase tracking-tight text-primary">
                  Schedule YouTube Short
                </h3>
                <span className="font-mono text-[10px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold">
                  AUTOPILOT
                </span>
              </div>
              <p className="font-mono text-[11px] text-outline mt-0.5">
                Automated publishing via persistent background queue
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 border border-primary bg-surface-container-lowest hover:bg-surface-container shadow-[1px_1px_0px_#111111] transition-colors"
          >
            <X className="w-4 h-4 text-primary" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-4 text-xs font-body">
          {/* Target Channel Banner */}
          <div className="p-3 bg-surface-container-low border-2 border-primary shadow-[2px_2px_0px_#111111] flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <img
                src={currentChannel?.thumbnail_url || "https://api.dicebear.com/7.x/bottts/svg?seed=AbhyodayaClips"}
                alt=""
                className="w-8 h-8 border border-primary shadow-[1px_1px_0px_#111111] object-cover"
              />
              <div>
                <span className="font-headline font-bold text-xs uppercase text-primary block">
                  {currentChannel?.channel_title || "Abhyodaya Singh Clips"}
                </span>
                <span className="font-mono text-[10px] text-outline">
                  {currentChannel?.custom_url || "@AbhyodayaClips"} • Quota Protected
                </span>
              </div>
            </div>
            <span className="font-mono text-[10px] px-2 py-0.5 border border-primary bg-[#d5eb45] font-bold uppercase">
              ACTIVE
            </span>
          </div>

          {/* Title with Character Linting */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="font-mono text-xs font-bold text-primary uppercase">
                Short Title (Packaging Linter)
              </label>
              <span className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-primary ${
                title.length <= 40
                  ? "bg-[#d5eb45] text-primary"
                  : title.length <= 60
                  ? "bg-surface-container text-primary"
                  : "bg-red-200 text-red-900"
              }`}>
                {title.length} chars {title.length <= 40 ? "• Mobile Safe" : title.length <= 60 ? "• Desktop Only" : "• Truncated"}
              </span>
            </div>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
            />
          </div>

          {/* Schedule Date & Time */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="font-mono text-xs font-bold text-primary uppercase flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-primary" />
                <span>Publish Time (Local)</span>
              </label>
              <input
                type="datetime-local"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full px-3 py-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
              />
            </div>

            {/* Visibility */}
            <div className="space-y-1">
              <label className="font-mono text-xs font-bold text-primary uppercase block">
                Visibility
              </label>
              <div className="grid grid-cols-3 gap-1.5">
                <button
                  type="button"
                  onClick={() => setVisibility("public")}
                  className={`py-2 px-1 border-2 border-primary text-center transition-all flex flex-col items-center justify-center gap-1 ${
                    visibility === "public"
                      ? "bg-primary text-on-primary shadow-[2px_2px_0px_#d5eb45] font-bold"
                      : "bg-surface-container-lowest text-on-surface hover:bg-surface-container"
                  }`}
                >
                  <Globe className="w-3.5 h-3.5" />
                  <span className="font-mono text-[10px] uppercase font-bold">Public</span>
                </button>
                <button
                  type="button"
                  onClick={() => setVisibility("unlisted")}
                  className={`py-2 px-1 border-2 border-primary text-center transition-all flex flex-col items-center justify-center gap-1 ${
                    visibility === "unlisted"
                      ? "bg-primary text-on-primary shadow-[2px_2px_0px_#d5eb45] font-bold"
                      : "bg-surface-container-lowest text-on-surface hover:bg-surface-container"
                  }`}
                >
                  <EyeOff className="w-3.5 h-3.5" />
                  <span className="font-mono text-[10px] uppercase font-bold">Unlisted</span>
                </button>
                <button
                  type="button"
                  onClick={() => setVisibility("private")}
                  className={`py-2 px-1 border-2 border-primary text-center transition-all flex flex-col items-center justify-center gap-1 ${
                    visibility === "private"
                      ? "bg-primary text-on-primary shadow-[2px_2px_0px_#d5eb45] font-bold"
                      : "bg-surface-container-lowest text-on-surface hover:bg-surface-container"
                  }`}
                >
                  <Lock className="w-3.5 h-3.5" />
                  <span className="font-mono text-[10px] uppercase font-bold">Private</span>
                </button>
              </div>
            </div>
          </div>

          {/* Description & Tags */}
          <div className="space-y-1">
            <label className="font-mono text-xs font-bold text-primary uppercase block">
              Description &amp; Hashtags
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full p-2.5 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111] leading-relaxed"
            />
          </div>

          <div className="space-y-1">
            <label className="font-mono text-xs font-bold text-primary uppercase block">
              SEO Tags (Comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-3 py-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t-2 border-primary bg-surface-container flex items-center justify-between">
          <span className="font-mono text-[11px] text-outline uppercase font-bold">
            Cost: 1,600 Quota Units
          </span>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container text-primary font-mono text-xs uppercase font-bold shadow-[1px_1px_0px_#111111] transition-all"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-4 py-1.5 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all flex items-center gap-1.5"
            >
              <Rocket className="w-3.5 h-3.5 text-[#d5eb45]" />
              <span>{isSubmitting ? "Scheduling..." : "Confirm Schedule"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
