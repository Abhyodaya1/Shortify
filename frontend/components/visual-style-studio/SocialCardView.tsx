"use client";

import React from "react";
import { SocialCardPreset } from "./types";
import { Check, Heart, MessageSquare, Send, Play } from "lucide-react";

interface Props {
  preset: SocialCardPreset;
  isSelected: boolean;
  onSelect: (preset: SocialCardPreset) => void;
  customText?: string;
  customAuthor?: string;
}

export const SocialCardView: React.FC<Props> = ({
  preset,
  isSelected,
  onSelect,
  customText,
  customAuthor,
}) => {
  const displayText = customText || preset.cardText;
  const displayAuthor = customAuthor || preset.authorName;

  if (preset.platform === "none") {
    return (
      <div
        onClick={() => onSelect(preset)}
        className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex items-center justify-between select-none ${
          isSelected
            ? "bg-[#181B20] border-[#3B82F6] shadow-[0_0_12px_rgba(59,130,246,0.35)]"
            : "bg-[#121418] border-[#222730] hover:border-[#384152]"
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-neutral-800 flex items-center justify-center font-mono text-xs text-neutral-400 font-bold">
            ∅
          </div>
          <div>
            <h4 className="font-sans font-bold text-sm text-neutral-200">None (Pure Video)</h4>
            <p className="font-sans text-xs text-neutral-400">No social card overlay, clean full-frame video</p>
          </div>
        </div>
        {isSelected && (
          <span className="font-mono text-[9px] px-2 py-0.5 rounded-md bg-[#00E297]/15 border border-[#00E297]/40 text-[#00E297] font-bold">
            Selected
          </span>
        )}
      </div>
    );
  }

  return (
    <div
      onClick={() => onSelect(preset)}
      className={`relative rounded-xl border-2 transition-all cursor-pointer p-4 select-none ${
        isSelected
          ? "border-[#3B82F6] shadow-[0_0_14px_rgba(59,130,246,0.4)] translate-y-[-1px]"
          : "border-[#222730] hover:border-[#384152]"
      }`}
    >
      {/* 1. REDDIT STYLE CARD */}
      {preset.platform === "reddit" && (
        <div className="w-full bg-[#FFFFFF] text-[#1A1A1B] p-4 rounded-xl shadow-md border border-neutral-200 flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Real Reddit Logo */}
              <img
                src="/logos/reddit_logo.png"
                alt="Reddit"
                className="w-7 h-7 rounded-full object-cover shrink-0 shadow-xs"
              />
              <div className="flex flex-col">
                <span className="font-sans font-bold text-xs text-[#1A1A1B]">
                  {preset.authorHandle || "r/technology"}
                </span>
                <span className="font-sans text-[10px] text-neutral-500">
                  {displayAuthor || "u/example"} • {preset.badgeText || "2 hours ago"}
                </span>
              </div>
            </div>
            {isSelected && (
              <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-black text-[#D5EB45] font-bold">
                ACTIVE
              </span>
            )}
          </div>

          <h4 className="font-sans font-bold text-sm text-[#1A1A1B] leading-snug">
            {displayText}
          </h4>

          {preset.bodyText && (
            <p className="font-sans text-xs text-neutral-600 leading-relaxed">
              {preset.bodyText}
            </p>
          )}

          <div className="flex items-center gap-2 pt-1 font-sans text-xs font-semibold text-neutral-500">
            <span>↑ {preset.upvotesCount || "2.4k"}</span>
            <span>•</span>
            <span>{preset.commentsCount || "183"} comments</span>
          </div>
        </div>
      )}

      {/* 2. X / TWITTER STYLE CARD */}
      {preset.platform === "twitter" && (
        <div className="w-full bg-[#000000] text-white p-4 rounded-xl border border-neutral-800 shadow-md flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-neutral-700 flex items-center justify-center font-bold text-xs text-white">
                {displayAuthor ? displayAuthor[0].toUpperCase() : "A"}
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-sans font-bold text-xs text-white">
                    {displayAuthor || "Alex Morgan"}
                  </span>
                  <span className="text-[11px] text-neutral-400">
                    {preset.authorHandle || "@example"}
                  </span>
                  {/* Real Verified Blue Tick Logo */}
                  <img
                    src="/logos/twitter_verified.png"
                    alt="Verified"
                    className="w-4 h-4 object-contain shrink-0 inline-block"
                  />
                </div>
                <span className="font-sans text-[10px] text-neutral-500">
                  {preset.badgeText || "X-inspired post"}
                </span>
              </div>
            </div>
            {/* Top Right X logo */}
            <span className="font-mono text-xs text-neutral-400 font-bold">𝕏</span>
          </div>

          <p className="font-sans font-bold text-sm text-white leading-snug">
            {displayText}
          </p>

          {preset.bodyText && (
            <p className="font-sans text-xs text-neutral-300 leading-relaxed">
              {preset.bodyText}
            </p>
          )}

          {preset.likesCount && (
            <div className="flex items-center gap-4 pt-1 font-sans text-xs text-neutral-400">
              <span className="flex items-center gap-1">
                <Heart className="w-3 h-3 text-red-500" /> {preset.likesCount}
              </span>
              <span className="flex items-center gap-1">
                <MessageSquare className="w-3 h-3 text-neutral-400" /> {preset.commentsCount || "892"}
              </span>
            </div>
          )}
        </div>
      )}

      {/* 3. INSTAGRAM REEL STYLE CARD */}
      {preset.platform === "instagram" && (
        <div className="w-full bg-[#121212] text-white p-4 rounded-xl border border-neutral-800 shadow-md flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              {/* Real Instagram Logo */}
              <img
                src="/logos/instagram_logo.png"
                alt="Instagram"
                className="w-7 h-7 rounded-lg object-cover shrink-0 shadow-xs"
              />
              <div className="flex flex-col">
                <span className="font-sans font-bold text-xs text-white">
                  {displayAuthor || "creator.vibes"}
                </span>
                <span className="font-sans text-[10px] text-neutral-400">
                  {preset.metaText || "♫ Original Audio • Trending Sound"}
                </span>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-[#0095F6] text-white font-sans text-[10px] font-bold">
              Follow
            </span>
          </div>

          <p className="font-sans text-xs sm:text-sm text-neutral-100 font-medium leading-snug">
            {displayText}
          </p>

          <div className="flex items-center justify-between pt-1 font-sans text-xs text-neutral-300 border-t border-neutral-800">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1 text-red-500 font-bold">
                <Heart className="w-3.5 h-3.5 fill-red-500" /> {preset.likesCount || "184K"}
              </span>
              <span className="flex items-center gap-1">
                <MessageSquare className="w-3.5 h-3.5" /> {preset.commentsCount || "2,410"}
              </span>
              <span className="flex items-center gap-1">
                <Send className="w-3.5 h-3.5" /> Share
              </span>
            </div>
            <span className="font-mono text-[9px] text-[#FF2A85] font-bold">INSTAGRAM</span>
          </div>
        </div>
      )}

      {/* 4. YOUTUBE SUPERCHAT STYLE CARD */}
      {preset.platform === "youtube" && (
        <div className="w-full bg-[#00E297] text-[#111111] p-4 rounded-xl border-2 border-black shadow-md flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Real YouTube Logo */}
              <img
                src="/logos/youtube_logo.png"
                alt="YouTube"
                className="w-6 h-6 object-contain shrink-0"
              />
              <span className="font-sans font-bold text-xs text-black">
                {displayAuthor || "Billu bhsanda"}
              </span>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-black text-[#D5EB45] font-mono text-[10px] font-bold">
              {preset.badgeText || "CA$ 14.99 SUPERCHAT"}
            </span>
          </div>

          <p className="font-sans font-bold text-xs sm:text-sm text-black leading-tight">
            &ldquo;{displayText}&rdquo;
          </p>

          <div className="flex items-center justify-between pt-1 border-t border-black/20 font-mono text-[10px]">
            <span>👍 4.2K • Pinned by Creator</span>
            <span className="font-bold">YOUTUBE SHORTS</span>
          </div>
        </div>
      )}
    </div>
  );
};

