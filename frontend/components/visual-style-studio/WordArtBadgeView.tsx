"use client";

import React from "react";
import { WordArtStyleDefinition } from "./types";

interface Props {
  text: string;
  preset: WordArtStyleDefinition;
  fontSize?: number;
  className?: string;
}

export const WordArtBadgeView: React.FC<Props> = ({
  text,
  preset,
  fontSize = 32,
  className = "",
}) => {
  const t = text || "VIRAL HOOK";

  // Style 1: Neon Glow
  if (preset.id === "neon_glow") {
    return (
      <span
        className={`inline-block font-sans font-black tracking-tight uppercase select-none ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          color: "#FFFFFF",
          textShadow: `
            0 0 4px #FFFFFF,
            0 0 10px ${preset.secondaryColor},
            0 0 20px ${preset.secondaryColor},
            0 0 35px ${preset.secondaryColor}
          `,
          WebkitTextStroke: "1px rgba(0,0,0,0.8)",
        }}
      >
        {t}
      </span>
    );
  }

  // Style 2: Slam In / Bold Punch
  if (preset.id === "slam_in") {
    return (
      <span
        className={`inline-block font-sans font-black tracking-wider uppercase select-none ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          color: preset.secondaryColor,
          WebkitTextStroke: `${Math.max(1, fontSize * 0.05)}px #000000`,
          filter: "drop-shadow(4px 4px 0px #000000)",
        }}
      >
        {t}
      </span>
    );
  }

  // Style 3: 3D Extrude
  if (preset.id === "3d_extrude") {
    const s = Math.max(1, Math.round(fontSize * 0.03));
    return (
      <span
        className={`inline-block font-sans font-black tracking-wider uppercase select-none ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          color: preset.secondaryColor,
          textShadow: `
            1px 1px 0 #1A1A1A,
            2px 2px 0 #1A1A1A,
            3px 3px 0 #1A1A1A,
            4px 4px 0 #1A1A1A,
            5px 5px 0 #000000,
            6px 6px 0 #000000
          `,
          WebkitTextStroke: `${s}px #000000`,
        }}
      >
        {t}
      </span>
    );
  }

  // Style 4: Comic Pop
  if (preset.id === "comic_pop") {
    return (
      <span
        className={`inline-block font-sans font-black tracking-wider uppercase select-none transform -rotate-1 ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          color: preset.primaryColor,
          WebkitTextStroke: "2px #000000",
          filter: "drop-shadow(5px 5px 0px #000000)",
        }}
      >
        {t}
      </span>
    );
  }

  // Style 5: Soft Pill Badge
  if (preset.id === "soft_pill") {
    return (
      <span
        className={`inline-flex items-center px-4 py-1.5 rounded-full border-2 bg-[#12161D]/90 backdrop-blur-xs select-none ${className}`}
        style={{
          borderColor: preset.secondaryColor,
          boxShadow: `0 4px 14px rgba(0,0,0,0.5)`,
        }}
      >
        <span
          className="font-sans font-bold tracking-tight text-white"
          style={{ fontSize: `${Math.round(fontSize * 0.8)}px` }}
        >
          {t}
        </span>
      </span>
    );
  }

  // Style 6: Cyber Terminal
  if (preset.id === "cyber_terminal") {
    return (
      <span
        className={`inline-block font-mono font-bold tracking-widest uppercase select-none ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          color: preset.secondaryColor,
          textShadow: `0 0 8px ${preset.secondaryColor}, 0 0 16px rgba(0,255,128,0.4)`,
          WebkitTextStroke: "1px #002814",
        }}
      >
        {t}
      </span>
    );
  }

  // Style 7: Gradient Fire
  if (preset.id === "gradient_fire") {
    return (
      <span
        className={`inline-block font-sans font-black tracking-tight uppercase select-none ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          backgroundImage: "linear-gradient(180deg, #FF3C00 0%, #FFE600 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.9)) drop-shadow(0 0 8px rgba(255,60,0,0.5))",
        }}
      >
        {t}
      </span>
    );
  }

  // Style 8: Metallic Chrome
  if (preset.id === "metallic_chrome") {
    return (
      <span
        className={`inline-block font-sans font-black tracking-tight uppercase select-none ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          backgroundImage: "linear-gradient(180deg, #FFFFFF 0%, #A0B2C6 50%, #465569 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          filter: "drop-shadow(2px 2px 2px rgba(0,0,0,0.8))",
        }}
      >
        {t}
      </span>
    );
  }

  // Style 9: Golden Luxury
  if (preset.id === "golden_luxury") {
    return (
      <span
        className={`inline-block font-sans font-black tracking-tight uppercase select-none ${className}`}
        style={{
          fontFamily: preset.fontFamily,
          fontSize: `${fontSize}px`,
          backgroundImage: "linear-gradient(180deg, #FFE178 0%, #E5A823 50%, #8C5300 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          filter: "drop-shadow(0 0 8px rgba(229,168,35,0.4)) drop-shadow(2px 2px 0px #000000)",
        }}
      >
        {t}
      </span>
    );
  }

  // Style 10 / Default: Duotone Split
  return (
    <span
      className={`inline-block font-sans font-black tracking-tight uppercase select-none ${className}`}
      style={{
        fontFamily: preset.fontFamily,
        fontSize: `${fontSize}px`,
        backgroundImage: `linear-gradient(180deg, ${preset.primaryColor} 0%, ${preset.secondaryColor} 100%)`,
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        filter: "drop-shadow(2px 2px 0px #000000)",
      }}
    >
      {t}
    </span>
  );
};
