export interface CaptionPreset {
  id: string;
  name: string;
  category: "bold" | "neon" | "gradient" | "depth" | "minimal" | "karaoke" | "cinematic" | "comic" | "typewriter" | "creator";
  description: string;
  fontFamily: string;
  fontSizeRatio: number;
  textColor: string;
  highlightColor: string;
  outlineColor: string;
  outlineWidth: number;
  shadowDepth: number;
  hasGlow?: boolean;
  glowColor?: string;
  is3D?: boolean;
  isGradient?: boolean;
  gradientColors?: [string, string];
  animationType: "word_pop" | "bounce" | "glow_pulse" | "fade_in" | "karaoke" | "typewriter" | "slide_up";
  scalePop: number;
  allCaps: boolean;
  letterSpacing?: string;
}

export interface VideoLayoutPreset {
  id: string;
  name: string;
  description: string;
  type: "full_screen" | "split_50_50" | "split_60_40" | "pip" | "floating" | "blurred_bg" | "card_frame" | "stacked" | "side_by_side" | "custom";
  splitRatio: number; // e.g. 50, 60, 100
  speakerScalePercent: number;
  backgroundTreatment: "none" | "gameplay" | "blur" | "dark" | "gradient" | "card";
  cornerRadius?: number;
  hasCardBorder?: boolean;
  pipPosition?: "bottom_right" | "top_right" | "center";
}

export interface SocialCardPreset {
  id: string;
  name: string;
  platform: "reddit" | "twitter" | "instagram" | "youtube" | "quote" | "news" | "creator" | "none";
  authorName: string;
  authorHandle: string;
  badgeText?: string;
  cardText: string;
  bodyText?: string;
  metaText?: string;
  upvotesCount?: string;
  commentsCount?: string;
  likesCount?: string;
  verified: boolean;
  theme: "dark" | "light" | "colored";
}

export interface BackgroundPreset {
  id: string;
  name: string;
  type: "dark" | "gradient" | "blur" | "custom" | "gameplay";
  cssValue: string;
  blurStrength?: number;
  gameplayId?: string;
}

export interface VisualStyleConfig {
  captionPresetId: string;
  layoutPresetId: string;
  socialCardPresetId: string;
  backgroundPresetId: string;
  // Caption Typography, Colors & Motion Engine
  customActiveColor?: string; // Highlighted word color (e.g. #FFE600, #D5EB45, #00E297, #00FFFF, #FF2A85)
  customTextColor?: string;   // Rest of caption words color (e.g. #FFFFFF, #F8FAFC, #111111)
  customFontName?: string;    // Font family (e.g. Arial Black, Impact, Space Grotesk, Inter, Montserrat, Georgia, Courier New)
  customAnimation?: "word_pop" | "bounce" | "glow_pulse" | "fade_in" | "slide_up" | "karaoke" | "typewriter"; // Animation type
  customAllCaps?: boolean;    // Force all caps vs sentence case
  customOutlineWidth?: number;// Outline thickness (0 to 8)
  // Fine tuning overrides
  customCardText?: string;
  customCardAuthor?: string;
  customCardHandle?: string;
  cardVerticalPosition: number; // 12-84 %
  cardWidthPercent: number; // 75-98 %
  subtitleVerticalPosition: number; // 12-84 %
  enableVoiceHook: boolean;
  ttsVoice: string;
}

export const CAPTION_PRESETS: CaptionPreset[] = [
  {
    id: "bold_impact",
    name: "BOLD IMPACT",
    category: "bold",
    description: "White · Yellow · Pop",
    fontFamily: "Impact",
    fontSizeRatio: 0.044,
    textColor: "#FFFFFF",
    highlightColor: "#FFE600",
    outlineColor: "#000000",
    outlineWidth: 6.0,
    shadowDepth: 3.8,
    animationType: "word_pop",
    scalePop: 118,
    allCaps: true,
  },
  {
    id: "neon_glow",
    name: "NEON GLOW",
    category: "neon",
    description: "Glow · Cyan · Shadow",
    fontFamily: "Space Grotesk",
    fontSizeRatio: 0.040,
    textColor: "#00FFFF",
    highlightColor: "#00E297",
    outlineColor: "#000000",
    outlineWidth: 4.5,
    shadowDepth: 2.0,
    hasGlow: true,
    glowColor: "#00FFFF",
    animationType: "glow_pulse",
    scalePop: 112,
    allCaps: true,
  },
  {
    id: "3d_depth",
    name: "3D DEPTH",
    category: "depth",
    description: "Layered · Bold · Shadow",
    fontFamily: "Arial Black",
    fontSizeRatio: 0.042,
    textColor: "#FFFFFF",
    highlightColor: "#D5EB45",
    outlineColor: "#000000",
    outlineWidth: 5.5,
    shadowDepth: 6.0,
    is3D: true,
    animationType: "bounce",
    scalePop: 120,
    allCaps: true,
  },
  {
    id: "cinematic",
    name: "CINEMATIC",
    category: "cinematic",
    description: "Elegant · Minimal · Fade",
    fontFamily: "Space Grotesk",
    fontSizeRatio: 0.035,
    textColor: "#FAF7F2",
    highlightColor: "#E2CFAD",
    outlineColor: "#111111",
    outlineWidth: 2.0,
    shadowDepth: 1.5,
    animationType: "fade_in",
    scalePop: 104,
    allCaps: false,
    letterSpacing: "0.08em",
  },
  {
    id: "gradient_wordart",
    name: "GRADIENT POP",
    category: "gradient",
    description: "Gradient · Outline · 3D",
    fontFamily: "Arial Black",
    fontSizeRatio: 0.042,
    textColor: "#FFE600",
    highlightColor: "#FF2A85",
    outlineColor: "#000000",
    outlineWidth: 5.0,
    shadowDepth: 4.0,
    isGradient: true,
    gradientColors: ["#FFE600", "#FF6B00"],
    animationType: "word_pop",
    scalePop: 116,
    allCaps: true,
  },
  {
    id: "minimal_modern",
    name: "MINIMAL MODERN",
    category: "minimal",
    description: "Sans-Serif · Clean · Smooth",
    fontFamily: "Inter",
    fontSizeRatio: 0.036,
    textColor: "#FFFFFF",
    highlightColor: "#00E297",
    outlineColor: "#111111",
    outlineWidth: 2.5,
    shadowDepth: 1.0,
    animationType: "slide_up",
    scalePop: 105,
    allCaps: false,
  },
  {
    id: "karaoke_highlight",
    name: "KARAOKE SYNC",
    category: "karaoke",
    description: "Word Sync · Smooth Fill",
    fontFamily: "Poppins",
    fontSizeRatio: 0.038,
    textColor: "#E2E8F0",
    highlightColor: "#D5EB45",
    outlineColor: "#000000",
    outlineWidth: 4.0,
    shadowDepth: 2.5,
    animationType: "karaoke",
    scalePop: 110,
    allCaps: true,
  },
  {
    id: "comic_pop",
    name: "COMIC POP ART",
    category: "comic",
    description: "Playful · Punchy · Slanted",
    fontFamily: "Impact",
    fontSizeRatio: 0.044,
    textColor: "#FFE600",
    highlightColor: "#FF2A85",
    outlineColor: "#000000",
    outlineWidth: 6.5,
    shadowDepth: 4.5,
    animationType: "bounce",
    scalePop: 122,
    allCaps: true,
  },
  {
    id: "typewriter",
    name: "TYPEWRITER",
    category: "typewriter",
    description: "Monospace · Green · Caret",
    fontFamily: "JetBrains Mono",
    fontSizeRatio: 0.034,
    textColor: "#00E297",
    highlightColor: "#D5EB45",
    outlineColor: "#052015",
    outlineWidth: 3.0,
    shadowDepth: 1.5,
    animationType: "typewriter",
    scalePop: 100,
    allCaps: false,
  },
  {
    id: "creator_hormozi",
    name: "HORMOZI BIONIC",
    category: "creator",
    description: "High-Pacing · Acid Lime",
    fontFamily: "Arial Black",
    fontSizeRatio: 0.043,
    textColor: "#FFFFFF",
    highlightColor: "#D5EB45",
    outlineColor: "#000000",
    outlineWidth: 5.8,
    shadowDepth: 3.5,
    animationType: "word_pop",
    scalePop: 118,
    allCaps: true,
  },
];

export const LAYOUT_PRESETS: VideoLayoutPreset[] = [
  {
    id: "full_screen",
    name: "Full screen",
    description: "Primary video fills entire 9:16 canvas with smart face tracking",
    type: "full_screen",
    splitRatio: 100,
    speakerScalePercent: 100,
    backgroundTreatment: "none",
  },
  {
    id: "split_50_50",
    name: "50/50",
    description: "Speaker on top 50%, secondary background / gameplay lower 50%",
    type: "split_50_50",
    splitRatio: 50,
    speakerScalePercent: 50,
    backgroundTreatment: "gameplay",
  },
  {
    id: "split_60_40",
    name: "60/40 Split",
    description: "Speaker 60% dominant view, supporting b-roll 40%",
    type: "split_60_40",
    splitRatio: 60,
    speakerScalePercent: 60,
    backgroundTreatment: "gameplay",
  },
  {
    id: "floating",
    name: "Floating",
    description: "Speaker in centered floating window with ambient background",
    type: "floating",
    splitRatio: 65,
    speakerScalePercent: 65,
    backgroundTreatment: "blur",
    cornerRadius: 20,
    hasCardBorder: true,
  },
  {
    id: "blurred",
    name: "Blurred",
    description: "Centered video in native ratio over blurred duplicate backdrop",
    type: "blurred_bg",
    splitRatio: 60,
    speakerScalePercent: 60,
    backgroundTreatment: "blur",
  },
  {
    id: "card",
    name: "Card",
    description: "Framed card with rounded borders and brutalist shadow",
    type: "card_frame",
    splitRatio: 55,
    speakerScalePercent: 55,
    backgroundTreatment: "dark",
    cornerRadius: 18,
    hasCardBorder: true,
  },
  {
    id: "stacked",
    name: "Stacked",
    description: "Speaker pinned at top, high-retention gameplay at bottom",
    type: "stacked",
    splitRatio: 48,
    speakerScalePercent: 48,
    backgroundTreatment: "gameplay",
  },
  {
    id: "pip",
    name: "Picture in Picture",
    description: "Gameplay fills canvas with speaker floating in bottom corner",
    type: "pip",
    splitRatio: 35,
    speakerScalePercent: 35,
    backgroundTreatment: "gameplay",
    cornerRadius: 16,
    pipPosition: "bottom_right",
  },
];

export const SOCIAL_CARD_PRESETS: SocialCardPreset[] = [
  {
    id: "reddit_card",
    name: "Reddit Community",
    platform: "reddit",
    authorName: "u/peakheistclips",
    authorHandle: "r/peakheistclips",
    badgeText: "2 hours ago",
    cardText: "What happens when AI changes everything?",
    bodyText: "The biggest shift might not be the technology itself, but how we use it.",
    upvotesCount: "2.4k",
    commentsCount: "183",
    verified: false,
    theme: "light",
  },
  {
    id: "twitter_card",
    name: "X / Twitter Post",
    platform: "twitter",
    authorName: "Peak Heist Clips",
    authorHandle: "@peakheistclips",
    badgeText: "X-inspired post",
    cardText: "Most people are thinking about this completely wrong.",
    bodyText: "When algorithms reward retention over pedigree, single creators outpace media studios.",
    likesCount: "14.2K",
    commentsCount: "892",
    verified: true,
    theme: "dark",
  },
  {
    id: "instagram_card",
    name: "Instagram Reel",
    platform: "instagram",
    authorName: "peakheistclips",
    authorHandle: "@peakheistclips",
    badgeText: "Follow",
    cardText: "This single psychological trigger is why some reels get 10M views:",
    metaText: "♫ Original Audio • Trending Sound",
    likesCount: "184K",
    commentsCount: "2,410",
    verified: true,
    theme: "dark",
  },
  {
    id: "youtube_card",
    name: "YouTube Superchat",
    platform: "youtube",
    authorName: "Peak Heist Clips",
    authorHandle: "@peakheistclips",
    badgeText: "CA$ 14.99 SUPERCHAT",
    cardText: "If you produce 10 shorts daily with AI, what happens to channel velocity?",
    likesCount: "4.2K",
    commentsCount: "381",
    verified: true,
    theme: "colored",
  },
  {
    id: "quote_card",
    name: "Quote Card",
    platform: "quote",
    authorName: "Naval Ravikant",
    authorHandle: "@naval",
    cardText: "“Code and media are permissionless leverage. They're the leverage behind the newly rich.”",
    verified: false,
    theme: "dark",
  },
  {
    id: "none",
    name: "None (Pure Video)",
    platform: "none",
    authorName: "",
    authorHandle: "",
    cardText: "",
    verified: false,
    theme: "dark",
  },
];

export const BACKGROUND_PRESETS: BackgroundPreset[] = [
  {
    id: "dark",
    name: "Dark",
    type: "dark",
    cssValue: "#121212",
  },
  {
    id: "gradient",
    name: "Gradient",
    type: "gradient",
    cssValue: "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)",
  },
  {
    id: "blur",
    name: "Blur",
    type: "blur",
    cssValue: "rgba(30, 41, 59, 0.7)",
    blurStrength: 25,
  },
  {
    id: "custom",
    name: "Custom (Mint)",
    type: "custom",
    cssValue: "#00E297",
  },
  {
    id: "minecraft",
    name: "Minecraft 4K",
    type: "gameplay",
    cssValue: "#111111",
    gameplayId: "minecraft_parkour",
  },
];

export const DEFAULT_VISUAL_STYLE_CONFIG: VisualStyleConfig = {
  captionPresetId: "bold_impact",
  layoutPresetId: "full_screen",
  socialCardPresetId: "reddit_card",
  backgroundPresetId: "dark",
  customActiveColor: "#FFE600",
  customTextColor: "#FFFFFF",
  customFontName: "Impact",
  customAnimation: "word_pop",
  customAllCaps: true,
  customOutlineWidth: 5.0,
  cardVerticalPosition: 18,
  cardWidthPercent: 92,
  subtitleVerticalPosition: 76,
  enableVoiceHook: false,
  ttsVoice: "en-US-ChristopherNeural",
};

