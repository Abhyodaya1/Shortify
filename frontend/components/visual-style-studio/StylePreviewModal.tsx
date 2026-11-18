"use client";

import React from "react";
import { VisualStyleConfig, CAPTION_PRESETS, LAYOUT_PRESETS, SOCIAL_CARD_PRESETS, BACKGROUND_PRESETS } from "./types";
import { X, Sparkles, Check, GripVertical } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  config: VisualStyleConfig;
  onChangeConfig: (newConfig: VisualStyleConfig) => void;
}

export const StylePreviewModal: React.FC<Props> = ({
  isOpen,
  onClose,
  config,
  onChangeConfig,
}) => {
  if (!isOpen) return null;

  const caption = CAPTION_PRESETS.find((c) => c.id === config.captionPresetId) || CAPTION_PRESETS[0];
  const layout = LAYOUT_PRESETS.find((l) => l.id === config.layoutPresetId) || LAYOUT_PRESETS[0];
  const card = SOCIAL_CARD_PRESETS.find((s) => s.id === config.socialCardPresetId) || SOCIAL_CARD_PRESETS[0];
  const bg = BACKGROUND_PRESETS.find((b) => b.id === config.backgroundPresetId) || BACKGROUND_PRESETS[0];
  const cardTextToDisplay = config.customCardText || card.cardText || "Hook / Title from Video";

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 animate-in fade-in duration-200">
      <div className="bg-[#111317] border-2 border-[#2A303C] rounded-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden shadow-2xl">
        {/* Modal Header */}
        <div className="p-4 border-b border-[#222730] flex items-center justify-between bg-[#161920]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#3B82F6]/20 border border-[#3B82F6]/40 flex items-center justify-center text-[#3B82F6]">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-sans font-bold text-sm text-white">
                Visual Style Studio • Live 9:16 Composite Preview
              </h3>
              <p className="font-sans text-xs text-neutral-400">
                Testing {caption.name} + {layout.name} + {card.name}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-[#2D333F] text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body: 2 Columns */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Left: 9:16 Phone Canvas Preview (6 cols) */}
          <div className="md:col-span-6 flex justify-center">
            <div className="relative w-64 sm:w-72 aspect-[9/16] rounded-2xl border-4 border-neutral-800 bg-black overflow-hidden shadow-2xl flex flex-col justify-between select-none">
              {/* Background Layer */}
              <div
                className="absolute inset-0 z-0"
                style={{ background: bg.cssValue }}
              >
                {layout.type === "split_50_50" && (
                  <div className="w-full h-full flex flex-col">
                    <div className="w-full h-1/2 bg-[#2D333F] border-b border-black flex items-center justify-center">
                      <span className="font-mono text-[10px] text-white/50 font-bold">SPEAKER 50%</span>
                    </div>
                    <div className="w-full h-1/2 bg-[#1A1D24] flex items-center justify-center">
                      <span className="font-mono text-[10px] text-white/40 font-bold">GAMEPLAY 50%</span>
                    </div>
                  </div>
                )}
                {layout.type === "full_screen" && (
                  <div
                    className="w-full h-full bg-cover bg-center"
                    style={{
                      backgroundImage: "url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80')",
                    }}
                  />
                )}
                {layout.type === "floating" && (
                  <div className="w-full h-full flex items-center justify-center p-3">
                    <div className="w-[88%] h-[58%] rounded-xl bg-neutral-700/80 border border-white/20 shadow-xl flex items-center justify-center">
                      <span className="font-mono text-[10px] text-white font-bold">FLOATING SPEAKER</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Reels Safe Zone Overlay */}
              <div className="absolute inset-0 pointer-events-none border-x border-dashed border-[#D5EB45]/20 m-2 flex flex-col justify-between p-1">
                <span className="font-mono text-[7px] text-[#D5EB45]/60 tracking-widest">[REELS SAFE BOUND]</span>
                <span className="font-mono text-[7px] text-[#D5EB45]/60 tracking-widest">[UI AVOIDANCE ZONE]</span>
              </div>

              {/* Social Card Layer */}
              {card.platform !== "none" ? (
                <div
                  style={{
                    top: `${config.cardVerticalPosition}%`,
                    width: `${config.cardWidthPercent}%`,
                    transform: "translate(-50%, 0)",
                  }}
                  className="absolute left-1/2 z-20 transition-all select-none"
                >
                  {/* Twitter Card */}
                  {card.platform === "twitter" && (
                    <div className="w-full bg-black/95 text-white p-2.5 rounded-lg border border-neutral-700 shadow-xl">
                      <div className="flex items-center gap-1.5 mb-1">
                        <div className="w-5 h-5 rounded-full bg-neutral-700 flex items-center justify-center text-[9px] font-bold">
                          A
                        </div>
                        <span className="font-sans font-bold text-[10px] truncate">{card.authorName}</span>
                        <img
                          src="/logos/twitter_verified.png"
                          alt="Verified"
                          className="w-3 h-3 object-contain inline-block"
                        />
                      </div>
                      <p className="font-sans text-[10px] font-medium leading-tight">
                        {cardTextToDisplay}
                      </p>
                    </div>
                  )}

                  {/* Reddit Card */}
                  {card.platform === "reddit" && (
                    <div className="w-full bg-white text-[#1A1A1B] p-2.5 rounded-lg border border-neutral-300 shadow-xl">
                      <div className="flex items-center gap-1.5 mb-1">
                        <img
                          src="/logos/reddit_logo.png"
                          alt="Reddit"
                          className="w-4 h-4 rounded-full object-cover"
                        />
                        <span className="font-sans font-bold text-[9px]">{card.authorHandle}</span>
                      </div>
                      <p className="font-sans text-[10px] font-bold leading-tight">
                        {cardTextToDisplay}
                      </p>
                    </div>
                  )}

                  {/* Instagram Card */}
                  {card.platform === "instagram" && (
                    <div className="w-full bg-[#121212] text-white p-2.5 rounded-lg border border-neutral-700 shadow-xl">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1.5">
                          <img
                            src="/logos/instagram_logo.png"
                            alt="Instagram"
                            className="w-4 h-4 rounded-xs object-cover"
                          />
                          <span className="font-sans font-bold text-[9px]">{card.authorHandle || "@creator"}</span>
                        </div>
                        <span className="text-[8px] bg-[#0095F6] text-white px-1.5 py-0.5 rounded-full font-bold">
                          Follow
                        </span>
                      </div>
                      <p className="font-sans text-[10px] font-medium leading-tight text-neutral-100">
                        {cardTextToDisplay}
                      </p>
                    </div>
                  )}

                  {/* YouTube Card */}
                  {card.platform === "youtube" && (
                    <div className="w-full bg-[#00E297] text-black p-2.5 rounded-lg border border-black shadow-xl">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1">
                          <img
                            src="/logos/youtube_logo.png"
                            alt="YouTube"
                            className="w-4 h-4 object-contain"
                          />
                          <span className="font-sans font-bold text-[9px]">{card.authorName}</span>
                        </div>
                        <span className="px-1.5 py-0.2 rounded-full bg-black text-[#D5EB45] font-mono text-[8px] font-bold">
                          {card.badgeText}
                        </span>
                      </div>
                      <p className="font-sans text-[10px] font-bold leading-tight">
                        &ldquo;{cardTextToDisplay}&rdquo;
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                /* Pure Video Floating Kinetic Hook (Phase 3) */
                <div
                  style={{
                    top: `${config.cardVerticalPosition}%`,
                    transform: "translate(-50%, 0)",
                  }}
                  className="absolute left-1/2 z-20 w-[90%] text-center transition-all select-none"
                >
                  <span className="font-sans font-black text-xs sm:text-sm text-[#FFE600] uppercase tracking-wide drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]">
                    {cardTextToDisplay}
                  </span>
                  {config.showSupportingCaption !== false && config.supportingCaptionText && (
                    <div className="mt-1 inline-block px-2.5 py-0.5 rounded-full bg-black/75 border border-white/20 text-[9px] text-neutral-200">
                      {config.supportingCaptionText}
                    </div>
                  )}
                </div>
              )}

              {/* Caption Typography Layer */}
              <div
                style={{
                  top: `${config.subtitleVerticalPosition}%`,
                  transform: "translate(-50%, -50%)",
                }}
                className="absolute left-1/2 z-20 text-center w-full px-4 transition-all pointer-events-none select-none"
              >
                <div
                  style={{
                    fontFamily: config.customFontName || caption.fontFamily || "Arial Black",
                    color: config.customTextColor || caption.textColor || "#FFFFFF",
                    textTransform: config.customAllCaps !== false ? "uppercase" : "none",
                  }}
                  className="text-base sm:text-lg font-black leading-tight drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]"
                >
                  <span>STOP </span>
                  <span
                    style={{
                      color: config.customActiveColor || caption.highlightColor || "#FFE600",
                      WebkitTextStroke: "1px #000000",
                      textShadow:
                        (config.customAnimation === "glow_pulse" || caption.hasGlow)
                          ? `0 0 8px ${config.customActiveColor || caption.highlightColor || "#00FFFF"}, 1px 1px 0 #000, -1px -1px 0 #000`
                          : "0 2px 0 #000",
                      display: "inline-block",
                    }}
                    className={`px-1 rounded-sm ${
                      (config.customAnimation === "glow_pulse" || caption.hasGlow)
                        ? "animate-pulse"
                        : "scale-105 transition-transform duration-150"
                    }`}
                  >
                    TRADING
                  </span>
                  <span> TIME!</span>
                </div>
              </div>

              {/* Phone Indicator Scrim */}
              <div className="relative z-10 p-2 text-center text-white/30 font-mono text-[8px]">
                PREVIEW SIMULATION
              </div>
            </div>
          </div>

          {/* Right: Fine-Tuning Controls (6 cols) */}
          <div className="md:col-span-6 space-y-4">
            <div className="p-4 rounded-xl bg-[#161920] border border-[#262C38] space-y-3">
              <h4 className="font-sans font-bold text-xs uppercase tracking-wider text-neutral-300">
                Interactive Placement Controls
              </h4>

              {/* Card Y Position */}
              <div>
                <div className="flex items-center justify-between font-mono text-xs text-neutral-300 mb-1">
                  <span>Card Vertical Position:</span>
                  <span className="text-[#3B82F6] font-bold">{config.cardVerticalPosition}%</span>
                </div>
                <input
                  type="range"
                  min={12}
                  max={84}
                  value={config.cardVerticalPosition}
                  onChange={(e) =>
                    onChangeConfig({
                      ...config,
                      cardVerticalPosition: parseInt(e.target.value, 10),
                    })
                  }
                  className="w-full accent-[#3B82F6] cursor-pointer"
                />
              </div>

              {/* Subtitle Y Position */}
              <div>
                <div className="flex items-center justify-between font-mono text-xs text-neutral-300 mb-1">
                  <span>Subtitle Vertical Position:</span>
                  <span className="text-[#D5EB45] font-bold">{config.subtitleVerticalPosition}%</span>
                </div>
                <input
                  type="range"
                  min={12}
                  max={84}
                  value={config.subtitleVerticalPosition}
                  onChange={(e) =>
                    onChangeConfig({
                      ...config,
                      subtitleVerticalPosition: parseInt(e.target.value, 10),
                    })
                  }
                  className="w-full accent-[#D5EB45] cursor-pointer"
                />
              </div>

              {/* Card Width */}
              <div>
                <div className="flex items-center justify-between font-mono text-xs text-neutral-300 mb-1">
                  <span>Card Width:</span>
                  <span className="font-bold">{config.cardWidthPercent}%</span>
                </div>
                <input
                  type="range"
                  min={75}
                  max={98}
                  value={config.cardWidthPercent}
                  onChange={(e) =>
                    onChangeConfig({
                      ...config,
                      cardWidthPercent: parseInt(e.target.value, 10),
                    })
                  }
                  className="w-full accent-[#3B82F6] cursor-pointer"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-[#2D333F] text-xs font-bold text-neutral-300 hover:bg-neutral-800 transition-all cursor-pointer"
              >
                Close Preview
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2 rounded-lg bg-[#3B82F6] text-white text-xs font-bold shadow-md hover:bg-[#2563EB] transition-all cursor-pointer"
              >
                Apply Style Configuration
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

