"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Clapperboard,
  Wand2,
  Scissors,
  Mic,
  FileText,
  Rocket,
  Video,
  User,
  Plus,
  ArrowUp,
  X,
  Play,
} from "lucide-react";

interface PromptStudioCardProps {
  onSubmit: (prompt: string, attachments: string[], preset: string) => void;
  isLoading?: boolean;
}

const PRESETS = [
  { id: "create-video", label: "Create a video", icon: Sparkles },
  { id: "edit-footage", label: "Edit footage", icon: Clapperboard },
  { id: "motion-design", label: "Motion design", icon: Wand2 },
  { id: "clip-highlights", label: "Clip highlights", icon: Scissors },
  { id: "talking-head", label: "Talking Head", icon: Mic },
  { id: "article-to-video", label: "Article → video", icon: FileText },
  { id: "launch-video", label: "Launch Video", icon: Rocket },
  { id: "multicam", label: "Multicam Footage", icon: Video },
  { id: "ai-avatar", label: "AI Avatar", icon: User },
];

export const PromptStudioCard: React.FC<PromptStudioCardProps> = ({ onSubmit, isLoading = false }) => {
  const [selectedPreset, setSelectedPreset] = useState("multicam");
  const [promptText, setPromptText] = useState(
    "Edit my multicam footage into a cohesive video. Sync the camera angles, cut to the active speaker, and use wide shots and close-ups to keep the conversation engaging."
  );
  const [attachments, setAttachments] = useState<Array<{ id: string; name: string; tag: string }>>([
    { id: "wide", name: "wide_angle_cam.mp4", tag: "WIDE" },
    { id: "guest", name: "guest_speaker_cam.mp4", tag: "GUEST" },
  ]);

  const handlePresetClick = (id: string) => {
    setSelectedPreset(id);
    if (id === "multicam") {
      setPromptText(
        "Edit my multicam footage into a cohesive video. Sync the camera angles, cut to the active speaker, and use wide shots and close-ups to keep the conversation engaging."
      );
    } else if (id === "article-to-video") {
      setPromptText(
        "Transform this editorial financial article into a dynamic captioned 60-second video with kinetic text highlights and clean stock transitions."
      );
    } else if (id === "launch-video") {
      setPromptText(
        "Build a high-energy 20-second product launch video showcasing our application features with sleek motion graphics and typography."
      );
    } else if (id === "talking-head") {
      setPromptText(
        "Isolate the speaker, remove background noise, apply auto-zoom on key emphasis phrases, and generate synchronized subtitle badges."
      );
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments(attachments.filter((a) => a.id !== id));
  };

  const addSimulatedAttachment = () => {
    const newId = `broll_${Date.now()}`;
    setAttachments([...attachments, { id: newId, name: "broll_footage.mp4", tag: "B-ROLL" }]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptText.trim()) return;
    onSubmit(promptText, attachments.map((a) => a.name), selectedPreset);
  };

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col items-center gap-6">
      {/* Title */}
      <div className="text-center space-y-1">
        <h1 className="font-serif text-5xl sm:text-6xl font-bold tracking-tight">Motion</h1>
        <p className="text-base sm:text-lg text-neutral-600 dark:text-neutral-400 font-normal">
          The General Video Agent
        </p>
      </div>

      {/* Hero Prompt Card */}
      <div className="w-full bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col gap-4">
        <textarea
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          placeholder="Describe your video..."
          rows={3}
          className="w-full bg-transparent resize-none text-base sm:text-lg font-normal text-neutral-800 dark:text-neutral-100 placeholder:text-neutral-400 focus:outline-none leading-relaxed"
        />

        {/* Media Attachments Chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap items-center gap-2.5">
            {attachments.map((att) => (
              <div
                key={att.id}
                className="relative group bg-neutral-900 text-white rounded-lg px-3 py-2 flex items-center gap-2 text-xs font-semibold shadow-sm overflow-hidden"
              >
                <div className="w-4 h-4 rounded-full bg-white/20 flex items-center justify-center">
                  <Play className="w-2.5 h-2.5 fill-current" />
                </div>
                <span>{att.tag}</span>
                <button
                  type="button"
                  onClick={() => removeAttachment(att.id)}
                  className="opacity-60 hover:opacity-100 p-0.5 rounded-full hover:bg-white/20 transition-all"
                  title="Remove attachment"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Card Footer Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-[var(--card-border)]/60">
          <button
            type="button"
            onClick={addSimulatedAttachment}
            className="w-8 h-8 rounded-full border border-[var(--card-border)] flex items-center justify-center text-neutral-500 hover:text-black dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            title="Add photos and files in Motion"
          >
            <Plus className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading || !promptText.trim()}
            className="w-9 h-9 rounded-full bg-neutral-900 dark:bg-neutral-100 text-white dark:text-black flex items-center justify-center hover:opacity-85 disabled:opacity-40 transition-opacity shadow-sm"
            title="Generate Video Cut"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Preset Modalities Carousel / Bar */}
      <div className="w-full flex items-center justify-start sm:justify-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {PRESETS.map((p) => {
          const Icon = p.icon;
          const isActive = selectedPreset === p.id;
          return (
            <button
              key={p.id}
              onClick={() => handlePresetClick(p.id)}
              className={`whitespace-nowrap px-3.5 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 border transition-all ${
                isActive
                  ? "bg-black text-white dark:bg-white dark:text-black border-transparent shadow-sm"
                  : "bg-transparent text-neutral-600 dark:text-neutral-400 border-[var(--card-border)] hover:border-neutral-400"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{p.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
