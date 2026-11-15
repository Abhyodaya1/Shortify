"use client";

import React, { useState, useEffect } from "react";
import {
  Calendar,
  Globe,
  Lock,
  EyeOff,
  X,
  Rocket,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  Tag,
  AlertTriangle,
} from "lucide-react";
import { YoutubeIcon } from "./YoutubeIcon";

interface TitleAlternative {
  text: string;
  angle?: string;
  accuracy_note?: string;
}

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  clip: any;
  currentChannel: any;
  onScheduled: (job: any) => void;
  onMetadataUpdate?: (updatedFields: {
    title: string;
    description: string;
    tags: string[];
    title_alternatives?: TitleAlternative[];
  }) => void;
}

export function ScheduleModal({
  isOpen,
  onClose,
  clip,
  currentChannel,
  onScheduled,
  onMetadataUpdate,
}: ScheduleModalProps) {
  const [scheduledDate, setScheduledDate] = useState<string>(() => {
    const d = new Date();
    d.setHours(d.getHours() + 2);
    return d.toISOString().slice(0, 16);
  });
  const [visibility, setVisibility] = useState<"public" | "unlisted" | "private">("unlisted");
  const [title, setTitle] = useState<string>("");
  const [titleAlternatives, setTitleAlternatives] = useState<TitleAlternative[]>([]);
  const [description, setDescription] = useState<string>("");
  const [tags, setTags] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(false);
  const [metadataSource, setMetadataSource] = useState<string | null>(null);
  const [metadataWarnings, setMetadataWarnings] = useState<string[]>([]);

  // Function to fetch or force-regenerate transcript-grounded AI metadata from backend
  const fetchAiMetadata = async (forceRegenerate: boolean = false) => {
    if (!clip?.clip_id) return;
    setIsLoadingMetadata(true);
    try {
      const url = `http://localhost:8000/api/v1/shorts/clips/${clip.clip_id}/metadata${
        forceRegenerate ? "?regenerate=true" : ""
      }`;
      const payload = {
        transcript:
          clip.spoken_text ||
          clip.transcript_segment ||
          (clip.cues ? clip.cues.map((c: any) => c.text).join(" ") : ""),
        opening_hook: clip.opening_hook || clip.visual_headline || "",
        headline: clip.visual_headline || clip.headline || clip.title || "",
        title: clip.title || "",
        video_title: clip.video_title || currentChannel?.channel_title || "",
        regenerate: forceRegenerate,
      };
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        throw new Error(`Failed to load AI metadata (${res.status})`);
      }
      const data = await res.json();
      const newTitle = data.title || clip?.headline || "Viral Short";
      const newDesc = data.description || "";
      const newTagsList: string[] = Array.isArray(data.tags)
        ? data.tags
        : typeof data.tags === "string"
        ? data.tags.split(",").map((t: string) => t.trim())
        : [];
      const newTagsStr = newTagsList.join(", ");
      const alts: TitleAlternative[] = data.title_alternatives || [];

      setTitle(newTitle);
      setDescription(newDesc);
      setTags(newTagsStr);
      setTitleAlternatives(alts);
      setMetadataSource(data.source || (forceRegenerate ? "ai_generated" : "cached_session"));
      setMetadataWarnings(data.metadata_warnings || []);

      onMetadataUpdate?.({
        title: newTitle,
        description: newDesc,
        tags: newTagsList,
        title_alternatives: alts,
      });
    } catch (err: any) {
      console.warn("AI metadata fetch fallback:", err.message);
      // Clean fallback avoiding repetitive transcript excerpts and legacy templates
      const rawTitle = clip.title || clip.headline || "Viral Short";
      const cleanTitle = rawTitle.replace(/^#\d+\s*/, "").replace(/\s*\|\s*#Shorts.*$/, "");

      let cleanDesc = clip.description || "";
      if (
        !cleanDesc ||
        cleanDesc.includes("Key Takeaway from") ||
        cleanDesc.includes("Key Takeaway:") ||
        cleanDesc.includes("Did you know this? Drop a comment below!") ||
        cleanDesc.includes("#Knowledge #Productivity")
      ) {
        cleanDesc = `${cleanTitle}.\n\nAn unforgettable highlight with dynamic rhythm and energy.\n\n#Shorts #YouTubeShorts #Trending`;
      }

      let cleanTagsStr = "";
      if (Array.isArray(clip.tags) && clip.tags.length > 0) {
        cleanTagsStr = clip.tags.join(", ");
      } else {
        const titleWords = cleanTitle.replace(/[^a-zA-Z0-9\s]/g, "").split(/\s+/).filter((w: string) => w.length > 3);
        const autoTags = ["Shorts", "YouTubeShorts", "ViralVideo", "TrendingNow"];
        for (const tw of titleWords) {
          if (!autoTags.includes(tw)) autoTags.push(tw);
        }
        cleanTagsStr = autoTags.slice(0, 10).join(", ");
      }

      setTitle(rawTitle);
      setDescription(cleanDesc);
      setTags(cleanTagsStr);
    } finally {
      setIsLoadingMetadata(false);
    }
  };

  // Re-synchronize and hydrate metadata when clip or modal open state changes
  useEffect(() => {
    if (!isOpen || !clip) return;

    // Reset default schedule time to 2 hours from now
    const d = new Date();
    d.setHours(d.getHours() + 2);
    setScheduledDate(d.toISOString().slice(0, 16));

    // Detect if current clip description is stale legacy boilerplate
    const isStaleDesc =
      !clip.description ||
      clip.description.includes("Key Takeaway from") ||
      clip.description.includes("Key Takeaway:") ||
      clip.description.includes("Did you know this? Drop a comment below!") ||
      clip.description.includes("#Knowledge #Productivity");

    // If clip already has clean rich AI metadata with tags and alternatives, hydrate directly
    const hasRichMeta =
      !isStaleDesc &&
      Boolean(clip.title) &&
      Array.isArray(clip.tags) &&
      clip.tags.length >= 4 &&
      Array.isArray(clip.title_alternatives) &&
      clip.title_alternatives.length > 0;

    if (hasRichMeta) {
      setTitle(clip.title);
      setDescription(clip.description || "");
      setTags(clip.tags.join(", "));
      setTitleAlternatives(clip.title_alternatives || []);
      setMetadataSource("cached_session");
      setIsLoadingMetadata(false);
    } else {
      // Auto-fetch or regenerate clean transcript-grounded metadata from backend
      fetchAiMetadata(true);
    }
  }, [clip?.clip_id, isOpen]);

  if (!isOpen || !clip) return null;

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const tagList = tags
        .split(",")
        .map((t) => t.trim().replace(/^#/, ""))
        .filter(Boolean);

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

  const parsedTagCount = tags.split(",").map((t) => t.trim()).filter(Boolean).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-xl bg-surface-container-lowest border-2 border-primary shadow-[5px_5px_0px_#111111] overflow-hidden flex flex-col max-h-[92vh]">
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
                <span className="font-mono text-[10px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold flex items-center gap-1">
                  <Sparkles className="w-2.5 h-2.5" />
                  <span>AI GROUNDED</span>
                </span>
              </div>
              <p className="font-mono text-[11px] text-outline mt-0.5">
                Automated publishing with Role 06 search-optimized metadata
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
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fetchAiMetadata(true)}
                disabled={isLoadingMetadata}
                className="inline-flex items-center gap-1 px-2 py-1 border border-primary bg-surface-container hover:bg-[#d5eb45] text-primary font-mono text-[10px] font-bold uppercase transition-all shadow-[1px_1px_0px_#111111]"
              >
                <RefreshCw className={`w-3 h-3 ${isLoadingMetadata ? "animate-spin" : ""}`} />
                <span>{isLoadingMetadata ? "Generating..." : "Regenerate AI"}</span>
              </button>
              <span className="font-mono text-[10px] px-2 py-0.5 border border-primary bg-[#d5eb45] font-bold uppercase">
                ACTIVE
              </span>
            </div>
          </div>

          {/* AI Metadata Notice */}
          {isLoadingMetadata ? (
            <div className="p-2.5 border border-primary bg-surface-container font-mono text-[11px] text-primary flex items-center gap-2 animate-pulse">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary" />
              <span>Generating transcript-grounded title, SEO tags &amp; description...</span>
            </div>
          ) : metadataWarnings.length > 0 ? (
            <div className="p-2.5 border border-amber-600 bg-amber-50 font-mono text-[11px] text-amber-900 flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
              <span>{metadataWarnings.join(". ")}</span>
            </div>
          ) : null}

          {/* Title with Character & Mobile Safe Linting */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="font-mono text-xs font-bold text-primary uppercase">
                Short Title (AI Generated)
              </label>
              <span
                className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-primary ${
                  title.length <= 40
                    ? "bg-[#d5eb45] text-primary"
                    : title.length <= 60
                    ? "bg-surface-container text-primary"
                    : "bg-red-200 text-red-900"
                }`}
              >
                {title.length} chars{" "}
                {title.length <= 40
                  ? "• Mobile Safe (<40)"
                  : title.length <= 60
                  ? "• Optimal (<60)"
                  : "• May Truncate"}
              </span>
            </div>
            <input
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                onMetadataUpdate?.({
                  title: e.target.value,
                  description,
                  tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
                  title_alternatives: titleAlternatives,
                });
              }}
              placeholder="e.g. Stop Making This Editing Mistake | #Shorts"
              className="w-full px-3 py-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
            />

            {/* Alternative Titles Selector */}
            {titleAlternatives.length > 0 && (
              <div className="space-y-1 pt-1">
                <span className="font-mono text-[10px] uppercase font-bold text-outline block">
                  Select Alternative Title (Role 06 Packager):
                </span>
                <div className="grid grid-cols-1 gap-1">
                  {titleAlternatives.map((alt, idx) => {
                    const isSelected = title === alt.text;
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setTitle(alt.text);
                          onMetadataUpdate?.({
                            title: alt.text,
                            description,
                            tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
                            title_alternatives: titleAlternatives,
                          });
                        }}
                        className={`text-left px-2.5 py-1.5 border text-[11px] font-mono transition-all flex items-center justify-between gap-2 ${
                          isSelected
                            ? "bg-[#d5eb45] text-primary border-primary font-bold shadow-[1px_1px_0px_#111111]"
                            : "bg-surface-container-lowest text-primary border-outline/30 hover:border-primary hover:bg-surface-container"
                        }`}
                      >
                        <span className="truncate flex-1">
                          <span className="uppercase text-[9px] px-1 py-0.2 mr-1.5 border border-primary/40 bg-surface-container">
                            {alt.angle || `Alt ${idx + 1}`}
                          </span>
                          {alt.text}
                        </span>
                        {isSelected && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
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

          {/* Description & Hashtags */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="font-mono text-xs font-bold text-primary uppercase block">
                Description &amp; Hashtags
              </label>
              <span className="font-mono text-[10px] text-outline">
                Transcript grounded • Hashtags included
              </span>
            </div>
            <textarea
              rows={4}
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                onMetadataUpdate?.({
                  title,
                  description: e.target.value,
                  tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
                  title_alternatives: titleAlternatives,
                });
              }}
              placeholder="Summary and key takeaway with relevant #Shorts hashtags..."
              className="w-full p-2.5 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111] leading-relaxed"
            />
          </div>

          {/* SEO Tags */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="font-mono text-xs font-bold text-primary uppercase flex items-center gap-1">
                <Tag className="w-3 h-3 text-primary" />
                <span>YouTube Search Tags (Up to 15 Substantive Keywords)</span>
              </label>
              <span className="font-mono text-[10px] font-bold text-outline">
                {parsedTagCount} / 15 tags
              </span>
            </div>
            <input
              type="text"
              value={tags}
              onChange={(e) => {
                setTags(e.target.value);
                onMetadataUpdate?.({
                  title,
                  description,
                  tags: e.target.value.split(",").map((t) => t.trim()).filter(Boolean),
                  title_alternatives: titleAlternatives,
                });
              }}
              placeholder="Shorts, YouTubeShorts, VideoTips, Editing, Creator"
              className="w-full px-3 py-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
            />
            <p className="font-mono text-[10px] text-outline">
              Targeted search keywords (comma-separated, without #). Distinct from hashtags in the description.
            </p>
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
              disabled={isSubmitting || isLoadingMetadata}
              className="px-4 py-1.5 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all flex items-center gap-1.5 disabled:opacity-50"
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
