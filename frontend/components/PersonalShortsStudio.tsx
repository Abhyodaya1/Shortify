"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  Upload,
  Play,
  Download,
  Scissors,
  GripVertical,
  CheckCircle2,
  RefreshCw,
  Flame,
  Clock,
  Rocket,
  Layers,
  FileVideo,
  Copy,
  Check,
  Settings,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Sliders,
  Type,
  Mic,
  Layout,
  Grid,
  List,
  Share2,
  X,
  ChevronRight,
  ChevronDown,
  Search,
  Plus,
  ArrowUp,
  Bell,
  Link as LinkIcon,
  HelpCircle,
  Folder,
  Video,
  Gamepad2,
  Eye,
  SlidersHorizontal,
  Heart,
  Trash2,
  Calendar,
  Sparkle,
  Music,
  Maximize2,
  Share,
  FileText,
  Home,
  Palette,
} from "lucide-react";
import { YoutubeIcon } from "./YoutubeIcon";
import { DashboardView } from "./DashboardView";
import { SchedulerView } from "./SchedulerView";
import { ChannelConnectModal } from "./ChannelConnectModal";
import { ScheduleModal } from "./ScheduleModal";
import { BulkPublishModal } from "./BulkPublishModal";
import { VisualStyleStudio } from "./visual-style-studio/VisualStyleStudio";
import { DEFAULT_VISUAL_STYLE_CONFIG, VisualStyleConfig } from "./visual-style-studio/types";


interface SubtitleArchetype {
  id: "hormozi" | "mrbeast" | "neon_punch" | "tweet_card" | "terminal_phosphor" | "swiss_clean";
  name: string;
  tagline: string;
  badge: string;
  color_val: string;
  font_name: string;
}

const SUBTITLE_ARCHETYPES: SubtitleArchetype[] = [
  {
    id: "hormozi",
    name: "Hormozi Bionic Pop",
    tagline: "High-contrast Acid Lime bounce, safe margin, 180wpm pacing badge",
    badge: "HIGH RETENTION",
    color_val: "&H0045EBD5&",
    font_name: "Arial Black",
  },
  {
    id: "mrbeast",
    name: "MrBeast Comic Punch",
    tagline: "Rotated explosive yellow banner with heavy black outline & drop cues",
    badge: "VIRAL PUNCH",
    color_val: "&H0000FFFF&",
    font_name: "Arial Black",
  },
  {
    id: "neon_punch",
    name: "Neon Stream Superchat",
    tagline: "Twitch/YouTube style live stream donation capsule with currency tag",
    badge: "STREAM FAVORITE",
    color_val: "&H0097E200&",
    font_name: "Impact",
  },
  {
    id: "tweet_card",
    name: "X / Twitter Thread Card",
    tagline: "Verified profile badge, handle, avatar, and kinetic multi-color underlines",
    badge: "THREAD HOOK",
    color_val: "&H00FFFFFF&",
    font_name: "Space Grotesk",
  },
  {
    id: "terminal_phosphor",
    name: "Terminal Green Phosphor",
    tagline: "Monospace typewriter green phosphor cadence with blinking live caret",
    badge: "DEV & TECH",
    color_val: "&H0000FF00&",
    font_name: "JetBrains Mono",
  },
  {
    id: "swiss_clean",
    name: "Swiss Editorial Clean",
    tagline: "Minimal frosted dark backdrop with refined typography & chapter tracker",
    badge: "EDITORIAL",
    color_val: "&H0045EBD5&",
    font_name: "Hanken Grotesk",
  },
];

interface BackgroundOption {
  id: string;
  name: string;
  category: "Minecraft" | "Subway Surfer" | "GTA 5" | "ASMR" | "Custom";
  duration: string;
  thumbnail: string;
  filename: string;
}

interface ClipCandidate {
  clip_id: string;
  index: number;
  duration_mode: string;
  start_sec: number;
  end_sec: number;
  duration_sec: number;
  main_topic: string;
  why_engaging: string;
  opening_hook: string;
  hook_score: number;
  hook_verdict: string;
  hook_formula: string;
  engagement_score: number;
  virality_score?: number;
  virality_breakdown?: {
    hook_score: number;
    engagement_score: number;
    value_score: number;
    shareability_score: number;
    total_virality: number;
  };
  title: string;
  description: string;
  hashtags: string[];
  tags?: string[];
  title_alternatives?: Array<{ text: string; angle?: string; accuracy_note?: string }>;
  metadata_warnings?: string[];
  rationale?: string;
  spoken_text: string;
  visual_headline?: string;
  key_hooks?: string[];
  why_viral?: string;
  crop_data?: {
    face_locked: boolean;
    face_detection_ratio: number;
  };
  rendered_video_url?: string;
  preview_url?: string;
  is_rendering?: boolean;
  qa_result?: {
    passed: boolean;
    issues: string[];
    total_duration_sec?: number;
    resolution?: string;
  };
  is_fallback?: boolean;
  passed_threshold?: boolean;
  candidate_rank?: number;
  selection_reason?: string;
  batch_message?: string;
  selection_mode?: string;
  layout_mode?: "split_screen" | "split_screen_comment" | "tweet_card" | "full_9_16" | "fit_ambient_blur" | "reddit_card" | "instagram_card" | "youtube_comment" | "floating" | "card" | "card_frame" | "blurred_bg" | "none" | string;
  card_type?: "none" | "reddit_card" | "tweet_card" | "instagram_card" | "youtube_comment" | string;
  background_id?: string;
  video_scale_percent?: number;
  subtitle_preset?: "hormozi" | "mrbeast" | "clean_minimal" | "neon_punch" | "terminal_phosphor" | "swiss_clean" | "tweet_card" | "tiktok_yellow" | "red_alert" | "bold_impact" | "neon_glow" | "3d_depth" | "cinematic" | "gradient_wordart" | "minimal_modern" | "karaoke_highlight" | "comic_pop" | "typewriter" | "creator_hormozi" | string;
  custom_font_name?: string;
  custom_active_color?: string;
  custom_text_color?: string;
  custom_animation?: string;
  custom_all_caps?: boolean;
  custom_outline_width?: number;
  enable_opening_hook?: boolean;
  opening_hook_text?: string;
  headline_text?: string;
  tts_voice?: string;
  social_author?: string;
  social_handle?: string;
  social_badge?: string;
  social_text?: string;
  card_vertical_position?: number;
  card_width_percent?: number;
  subtitle_vertical_position?: number;
}

export const PersonalShortsStudio: React.FC = () => {
  // Input states
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Scalereach / OpusClip Pre-configuration states
  const [clipTypeTab, setClipTypeTab] = useState<"templates" | "custom">("templates");
  const [selectedTemplate, setSelectedTemplate] = useState<string>("Viral Clips");
  const [customPrompt, setCustomPrompt] = useState<string>("");
  const [autoHook, setAutoHook] = useState<boolean>(false);
  const [smartReframing, setSmartReframing] = useState<boolean>(true);
  const [aiMusic, setAiMusic] = useState<boolean>(false);
  const [clipDurationPill, setClipDurationPill] = useState<string>("30 - 60s");
  const [splitScreenEnabled, setSplitScreenEnabled] = useState<boolean>(true);
  const [selectedBgCategory, setSelectedBgCategory] = useState<string>("All");
  const [selectedBgId, setSelectedBgId] = useState<string>("minecraft_parkour");
  const [splitRatio, setSplitRatio] = useState<number>(50);
  const [startTimeStr, setStartTimeStr] = useState<string>("0:00");
  const [endTimeStr, setEndTimeStr] = useState<string>("10:00");

  // Upfront Pre-Extraction Viral Packaging Directives (Configured at paste/upload before discovery)
  const [upfrontSubtitlePreset, setUpfrontSubtitlePreset] = useState<"hormozi" | "mrbeast" | "swiss_clean" | "terminal_phosphor">("hormozi");
  const [upfrontCardType, setUpfrontCardType] = useState<"none" | "tweet_card" | "reddit_card" | "instagram_card" | "youtube_comment">("tweet_card");
  const [upfrontCardPosition, setUpfrontCardPosition] = useState<number>(18);
  const [upfrontCardWidth, setUpfrontCardWidth] = useState<number>(92);
  const [upfrontVoice, setUpfrontVoice] = useState<string>("en-US-ChristopherNeural");
  const [upfrontCardAuthor, setUpfrontCardAuthor] = useState<string>("Peak Heist Clips");
  const [upfrontCardHandle, setUpfrontCardHandle] = useState<string>("@peakheistclips");
  const [upfrontCardSubreddit, setUpfrontCardSubreddit] = useState<string>("r/AskReddit");
  const [upfrontCardBadge, setUpfrontCardBadge] = useState<string>("CA$ 14.99");
  const [visualStyleConfig, setVisualStyleConfig] = useState<VisualStyleConfig>(DEFAULT_VISUAL_STYLE_CONFIG);

  // Predefined Backgrounds (Directly backed by real video files on disk with rich presets matching Image 8)
  const [backgroundList, setBackgroundList] = useState<BackgroundOption[]>([
    {
      id: "minecraft_parkour",
      name: "Minecraft Parkour 4K",
      category: "Minecraft",
      duration: "7:00",
      thumbnail: "http://localhost:8000/api/v1/shorts/backgrounds/minecraft_parkour/thumbnail",
      filename: "minecraft_parkour.mp4",
    },
    {
      id: "subway_surfer_city",
      name: "Subway Surfer City",
      category: "Subway Surfer",
      duration: "1:30",
      thumbnail: "http://localhost:8000/api/v1/shorts/backgrounds/subway_surfer_city/thumbnail",
      filename: "minecraft_parkour.mp4",
    },
    {
      id: "subway_surfer_night",
      name: "Subway Surfer Night",
      category: "Subway Surfer",
      duration: "1:20",
      thumbnail: "http://localhost:8000/api/v1/shorts/backgrounds/subway_surfer_night/thumbnail",
      filename: "minecraft_parkour.mp4",
    },
    {
      id: "gta5_ramp",
      name: "GTA 5 Mega Ramp",
      category: "GTA 5",
      duration: "2:00",
      thumbnail: "http://localhost:8000/api/v1/shorts/backgrounds/gta5_ramp/thumbnail",
      filename: "minecraft_parkour.mp4",
    },
    {
      id: "asmr_kinetic_sand",
      name: "ASMR Kinetic Sand",
      category: "ASMR",
      duration: "1:30",
      thumbnail: "http://localhost:8000/api/v1/shorts/backgrounds/asmr_kinetic_sand/thumbnail",
      filename: "minecraft_parkour.mp4",
    },
    {
      id: "asmr_soap_slice",
      name: "ASMR Soap Slicing",
      category: "ASMR",
      duration: "1:30",
      thumbnail: "http://localhost:8000/api/v1/shorts/backgrounds/asmr_soap_slice/thumbnail",
      filename: "minecraft_parkour.mp4",
    },
  ]);

  // Phase 2: Navigation, Channel & Scheduling state (Image 7 & Motion Hybrid)
  const [activeMainView, setActiveMainView] = useState<"dashboard" | "studio" | "scheduler">("dashboard");
  const [currentChannel, setCurrentChannel] = useState<any>(null);
  const [isChannelModalOpen, setIsChannelModalOpen] = useState(false);
  const [schedulingClip, setSchedulingClip] = useState<ClipCandidate | null>(null);
  const [isBulkPublishModalOpen, setIsBulkPublishModalOpen] = useState(false);
  const [recentVideos, setRecentVideos] = useState<any[]>([
    {
      id: "vid_sanatana",
      title: "The Hidden Foundation of Sanatana Dharma",
      thumbnail: "https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop&q=80",
      duration_min: "14:20",
      created_date: "Nov 11",
      clip_count: 3,
      video_type: "Viral Clips",
    },
    {
      id: "vid_lessons",
      title: "35 Years of Life Lessons in Just 5 Minutes",
      thumbnail: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&auto=format&fit=crop&q=80",
      duration_min: "09:16",
      created_date: "Nov 11",
      clip_count: 5,
      video_type: "Viral Clips",
    },
    {
      id: "vid_students",
      title: "TYPES OF BACK TO SCHOOL STUDENTS || Relatable comedy by 5-Minute Crafts",
      thumbnail: "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&auto=format&fit=crop&q=80",
      duration_min: "12:10",
      created_date: "Nov 10",
      clip_count: 4,
      video_type: "Viral Clips",
    },
  ]);

  // Feature 2: Layout mode & social overlays state
  const [selectedLayoutMode, setSelectedLayoutMode] = useState<"split_screen" | "split_screen_comment" | "tweet_card" | "fit_ambient_blur" | "full_9_16">("split_screen");
  const [socialAuthor, setSocialAuthor] = useState<string>("Peak Heist Clips");
  const [socialHandle, setSocialHandle] = useState<string>("@peakheistclips");
  const [socialBadge, setSocialBadge] = useState<string>("verified");
  const [socialText, setSocialText] = useState<string>("");

  // Feature 4: Batch export states
  const [isBatchRendering, setIsBatchRendering] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });

  // Operational states
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStep, setActiveStep] = useState<string>("");
  const [currentVideo, setCurrentVideo] = useState<any>(null);
  const [clips, setClips] = useState<ClipCandidate[]>([]);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [activeCardTabs, setActiveCardTabs] = useState<Record<string, "transcript" | "viral">>({});
  const [likedClips, setLikedClips] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const bgFileInputRef = useRef<HTMLInputElement>(null);

  // Editor Modal states (Image 1)
  const [editingClip, setEditingClip] = useState<ClipCandidate | null>(null);
  const [voiceoverScriptMode, setVoiceoverScriptMode] = useState<"Hook" | "Title" | "Both">("Hook");
  const [isModalRendering, setIsModalRendering] = useState(false);
  const [modalStatusMsg, setModalStatusMsg] = useState<string | null>(null);
  const [modalViewTab, setModalViewTab] = useState<"canvas" | "preview">("canvas");
  const [isDraggingCard, setIsDraggingCard] = useState(false);
  const [isDraggingSubtitle, setIsDraggingSubtitle] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Restore clips from localStorage on mount so customized work is never lost
  useEffect(() => {
    try {
      const saved = localStorage.getItem("shortify_clips_v2");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setClips(parsed);
        }
      }
    } catch (e) {
      console.warn("Failed to restore clips from localStorage", e);
    }
  }, []);

  // Save clips to state & localStorage
  const persistClipsState = (updatedClips: ClipCandidate[]) => {
    setClips(updatedClips);
    try {
      localStorage.setItem("shortify_clips_v2", JSON.stringify(updatedClips));
    } catch (e) {
      console.warn("Failed to persist clips to localStorage", e);
    }
  };

  const handleCloseModal = () => {
    if (editingClip) {
      const updatedList = clips.map((c) =>
        c.clip_id === editingClip.clip_id ? editingClip : c
      );
      persistClipsState(updatedList);
    }
    setEditingClip(null);
    setModalStatusMsg(null);
    setModalViewTab("canvas");
  };

  const assToHexColor = (assColor?: string): string => {
    if (!assColor) return "#D5EB45";
    const map: Record<string, string> = {
      "&H0045EBD5&": "#D5EB45",
      "&H0097E200&": "#00E297",
      "&H0000E6FF&": "#FFE600",
      "&H00852AFF&": "#FF2A85",
      "&H00FFFFFF&": "#FFFFFF",
      "&H0000FFFF&": "#FFE600",
      "&H0000D7FF&": "#FFD700",
      "&H00FFFF00&": "#00FFFF",
      "&H0000FF00&": "#00E297",
    };
    return map[assColor] || "#D5EB45";
  };

  useEffect(() => {
    fetchBackgrounds();
    fetchChannelStatus();
    fetchChannelVideos();

    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("youtube_connected") === "true") {
        fetchChannelStatus();
        fetchChannelVideos();
        window.history.replaceState({}, document.title, window.location.pathname);
      } else if (params.get("oauth_error")) {
        alert(`Google OAuth error: ${params.get("oauth_error")}`);
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  }, []);

  const fetchChannelStatus = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/status");
      if (res.ok) {
        const data = await res.json();
        setCurrentChannel(data.channel);
      }
    } catch {}
  };

  const fetchChannelVideos = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/channel-videos");
      if (res.ok) {
        const data = await res.json();
        if (data.videos && data.videos.length > 0) {
          setRecentVideos(data.videos);
        }
      }
    } catch {}
  };

  const fetchBackgrounds = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/shorts/backgrounds");
      if (res.ok) {
        const data = await res.json();
        if (data.backgrounds && data.backgrounds.length > 0) {
          const apiBgs = data.backgrounds.map((b: any) => ({
            id: b.id,
            name: b.name,
            category: (b.id.toLowerCase().includes("minecraft") || b.id.toLowerCase().includes("parkour")) ? "Minecraft" : "Custom",
            duration: "Full",
            thumbnail: b.thumbnail_url || `http://localhost:8000/api/v1/shorts/backgrounds/${b.id}/thumbnail`,
            filename: b.filename,
          }));
          setBackgroundList(apiBgs);
          if (!apiBgs.some((b: any) => b.id === selectedBgId)) {
            setSelectedBgId(apiBgs[0].id);
          }
        }
      }
    } catch {
      // Backend offline or starting up
    }
  };

  const handleUploadBackground = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("http://localhost:8000/api/v1/shorts/upload-background", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        await fetchBackgrounds();
        setSelectedBgId(data.id);
      }
    } catch (e: any) {
      alert(`Background upload failed: ${e.message}`);
    }
  };

  // Step 1: Ingest Video and Discover Clips ("Get clips in 1 click")
  const handleGetClips = async () => {
    if (!youtubeUrl && !selectedFile) {
      alert("Please paste a video link or choose a video file.");
      return;
    }

    setIsProcessing(true);
    setActiveStep("Transcribing speech with Groq Whisper audio model...");
    setClips([]);
    setCurrentVideo(null);

    try {
      let videoData: any = null;
      if (youtubeUrl) {
        const res = await fetch("http://localhost:8000/api/v1/shorts/ingest-url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: youtubeUrl.trim() }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Failed to download and transcribe video");
        }
        videoData = await res.json();
      } else if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        const res = await fetch("http://localhost:8000/api/v1/shorts/upload-file", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Failed to upload and transcribe video file");
        }
        videoData = await res.json();
      }

      setCurrentVideo(videoData);

      // Step 2: Discover viral moments with selected layout & timeframe
      setActiveStep("Analyzing dialogue, applying hook strategies, and reframing speaker...");
      const durationModeParam = clipDurationPill === "0 - 30s" ? "31s" : "45s";

      // Map visualStyleConfig to backend directives
      const cardTypeMap: Record<string, string> = {
        reddit_card: "reddit_card",
        twitter_card: "tweet_card",
        tweet_card: "tweet_card",
        instagram_card: "instagram_card",
        youtube_card: "youtube_comment",
        youtube_comment: "youtube_comment",
        quote_card: "tweet_card",
        none: "none",
      };

      const layoutMap: Record<string, string> = {
        full_screen: "full_9_16",
        split_50_50: "split_screen",
        split_60_40: "split_screen",
        pip: "pip",
        floating: "floating",
        blurred_bg: "fit_ambient_blur",
        card_frame: "card",
        blurred: "fit_ambient_blur",
        card: "card",
        stacked: "split_screen",
        side_by_side: "split_screen",
        custom: "split_screen",
      };

      const resolvedCardType = cardTypeMap[visualStyleConfig.socialCardPresetId] || (visualStyleConfig.socialCardPresetId === "none" ? "none" : "reddit_card");
      const resolvedLayoutMode = layoutMap[visualStyleConfig.layoutPresetId] || (splitScreenEnabled ? "split_screen" : "full_9_16");

      // Filter out dummy template placeholder texts
      const dummyPresetTexts = [
        "what happens when ai changes",
        "most people are thinking about this",
        "the #1 secret",
        "if you produce 10 shorts daily",
        "what formula do you use",
        "every creator gets asked",
        "code and media are permissionless",
      ];
      const hasRealCustomCardText = visualStyleConfig.customCardText && !dummyPresetTexts.some(d => (visualStyleConfig.customCardText || "").toLowerCase().includes(d));

      const discRes = await fetch("http://localhost:8000/api/v1/shorts/discover-clips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoData.video_id,
          duration_mode: durationModeParam,
          layout_mode: resolvedLayoutMode,
          card_type: resolvedCardType,
          background_id: (visualStyleConfig.backgroundPresetId === "minecraft" || ["floating", "card", "card_frame", "blurred", "blurred_bg"].includes(visualStyleConfig.layoutPresetId)) ? "minecraft_parkour" : selectedBgId,
          video_scale_percent: visualStyleConfig.layoutPresetId === "split_60_40" ? 60 : splitRatio,
          auto_hook: visualStyleConfig.enableVoiceHook || autoHook,
          social_author: resolvedCardType === "none" ? undefined : (visualStyleConfig.customCardAuthor || "Peak Heist Clips"),
          social_handle: resolvedCardType === "none" ? undefined : (visualStyleConfig.customCardHandle || "@peakheistclips"),
          social_badge: "CA$ 14.99",
          social_text: hasRealCustomCardText ? visualStyleConfig.customCardText : undefined,
          card_vertical_position: visualStyleConfig.cardVerticalPosition,
          card_width_percent: visualStyleConfig.cardWidthPercent,
          subtitle_vertical_position: visualStyleConfig.subtitleVerticalPosition,
          subtitle_preset: visualStyleConfig.captionPresetId,
          custom_font_name: visualStyleConfig.customFontName || "Arial Black",
          custom_active_color: visualStyleConfig.customActiveColor || "#FFE600",
          custom_primary_color: visualStyleConfig.customTextColor || "#FFFFFF",
          custom_animation: visualStyleConfig.customAnimation || "word_pop",
          custom_all_caps: visualStyleConfig.customAllCaps !== false,
          custom_outline_width: visualStyleConfig.customOutlineWidth || 5.0,
          tts_voice: visualStyleConfig.ttsVoice || upfrontVoice,
        }),
      });

      if (!discRes.ok) {
        const err = await discRes.json();
        throw new Error(err.detail || "Failed to discover clips");
      }

      const discData = await discRes.json();
      const discovered = (discData.clips || []).map((c: any) => ({
        ...c,
        layout_mode: resolvedLayoutMode,
        card_type: resolvedCardType,
        background_id: (visualStyleConfig.backgroundPresetId === "minecraft" || ["floating", "card", "card_frame", "blurred", "blurred_bg"].includes(visualStyleConfig.layoutPresetId)) ? "minecraft_parkour" : selectedBgId,
        video_scale_percent: visualStyleConfig.layoutPresetId === "split_60_40" ? 60 : splitRatio,
        subtitle_preset: visualStyleConfig.captionPresetId,
        custom_font_name: visualStyleConfig.customFontName || "Arial Black",
        custom_active_color: visualStyleConfig.customActiveColor || "#FFE600",
        custom_text_color: visualStyleConfig.customTextColor || "#FFFFFF",
        custom_animation: visualStyleConfig.customAnimation || "word_pop",
        custom_all_caps: visualStyleConfig.customAllCaps !== false,
        custom_outline_width: visualStyleConfig.customOutlineWidth || 5.0,
        enable_opening_hook: visualStyleConfig.enableVoiceHook || autoHook,
        card_vertical_position: visualStyleConfig.cardVerticalPosition,
        card_width_percent: visualStyleConfig.cardWidthPercent,
        subtitle_vertical_position: visualStyleConfig.subtitleVerticalPosition,
        tts_voice: visualStyleConfig.ttsVoice || upfrontVoice,
        key_hooks: c.key_hooks || ["Bold contrarian claim", "Relatable pain point"],
        social_author: resolvedCardType === "none" ? undefined : (visualStyleConfig.customCardAuthor || upfrontCardAuthor),
        social_handle: resolvedCardType === "none" ? undefined : (visualStyleConfig.customCardHandle || upfrontCardHandle),
        social_badge: upfrontCardBadge,
        social_text: hasRealCustomCardText ? visualStyleConfig.customCardText : (c.opening_hook || c.visual_headline || c.title),
      }));
      persistClipsState(discovered);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setActiveStep("");
    }
  };

  // Render a clip to 9:16 vertical MP4
  const handleRenderClip = async (clip: ClipCandidate) => {
    setClips((prev) =>
      prev.map((c) => (c.clip_id === clip.clip_id ? { ...c, is_rendering: true } : c))
    );

    try {
      const res = await fetch("http://localhost:8000/api/v1/shorts/render-clip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clip_id: clip.clip_id,
          layout_mode: clip.layout_mode || selectedLayoutMode,
          card_type: clip.card_type ?? (clip.layout_mode === "reddit_card" ? "reddit_card" : "none"),
          background_id: clip.background_id || selectedBgId,
          video_scale_percent: clip.video_scale_percent || splitRatio,
          enable_opening_hook: clip.enable_opening_hook ?? false,
          opening_hook_text: clip.opening_hook_text || clip.opening_hook,
          enable_ending_hook: false,
          headline_text: clip.headline_text || clip.visual_headline || clip.title,
          tts_voice: clip.tts_voice || "en-US-ChristopherNeural",
          subtitle_preset: clip.subtitle_preset || "mrbeast",
          custom_font_name: clip.custom_font_name || visualStyleConfig.customFontName || "Arial Black",
          custom_active_color: clip.custom_active_color || visualStyleConfig.customActiveColor || "#FFE600",
          custom_primary_color: clip.custom_text_color || visualStyleConfig.customTextColor || "#FFFFFF",
          custom_animation: clip.custom_animation || visualStyleConfig.customAnimation || "word_pop",
          custom_all_caps: clip.custom_all_caps ?? visualStyleConfig.customAllCaps ?? true,
          custom_outline_width: clip.custom_outline_width ?? visualStyleConfig.customOutlineWidth ?? 5.0,
          social_author: clip.card_type === "none" ? undefined : (clip.social_author || socialAuthor),
          social_handle: clip.card_type === "none" ? undefined : (clip.social_handle || socialHandle),
          social_badge: clip.social_badge || socialBadge,
          social_text: clip.card_type === "none" ? undefined : (clip.social_text || undefined),
          card_vertical_position: clip.card_vertical_position ?? visualStyleConfig.cardVerticalPosition,
          card_width_percent: clip.card_width_percent ?? visualStyleConfig.cardWidthPercent,
          subtitle_vertical_position: clip.subtitle_vertical_position ?? visualStyleConfig.subtitleVerticalPosition,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Video rendering failed");
      }

      const data = await res.json();
      const finalDownloadUrl = data.download_url?.startsWith("http")
        ? data.download_url
        : `http://localhost:8000${data.download_url}`;
      const finalPreviewUrl = data.preview_url?.startsWith("http")
        ? data.preview_url
        : `http://localhost:8000${data.preview_url}`;

      setClips((prev) => {
        const nextList = prev.map((c) =>
          c.clip_id === clip.clip_id
            ? {
                ...c,
                is_rendering: false,
                rendered_video_url: finalDownloadUrl,
                preview_url: finalPreviewUrl,
                qa_result: data.qa_result,
                title: data.title || c.title,
                title_alternatives: data.title_alternatives || c.title_alternatives,
                description: data.description || c.description,
                hashtags: data.hashtags || c.hashtags,
                tags: data.tags || c.tags,
              }
            : c
        );
        persistClipsState(nextList);
        return nextList;
      });

      if (editingClip && editingClip.clip_id === clip.clip_id) {
        setEditingClip((prev) => (prev ? { ...prev, rendered_video_url: finalDownloadUrl } : null));
      }
    } catch (err: any) {
      alert(`Render error: ${err.message}`);
      setClips((prev) =>
        prev.map((c) => (c.clip_id === clip.clip_id ? { ...c, is_rendering: false } : c))
      );
    }
  };


  // Customization Re-Render Handler with resilient fallback, positioning & cache-busting
  const handleApplyAndReRender = async () => {
    if (!editingClip) return;
    setIsModalRendering(true);
    setModalStatusMsg(null);

    // 1. Immediately persist all edits into parent clips list & localStorage
    const updatedDraft: ClipCandidate = {
      ...editingClip,
      card_vertical_position: editingClip.card_vertical_position ?? 20,
      card_width_percent: editingClip.card_width_percent ?? 92,
      subtitle_vertical_position: editingClip.subtitle_vertical_position ?? (editingClip.card_vertical_position ?? 76),
    };
    const updatedList = clips.map((c) =>
      c.clip_id === updatedDraft.clip_id ? updatedDraft : c
    );
    persistClipsState(updatedList);

    try {
      const res = await fetch("http://localhost:8000/api/v1/shorts/render-clip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clip_id: updatedDraft.clip_id,
          layout_mode: updatedDraft.layout_mode || selectedLayoutMode,
          card_type: updatedDraft.card_type ?? (updatedDraft.layout_mode === "reddit_card" ? "reddit_card" : "none"),
          background_id: updatedDraft.background_id || selectedBgId,
          video_scale_percent: updatedDraft.video_scale_percent || splitRatio,
          enable_opening_hook: updatedDraft.enable_opening_hook ?? false,
          opening_hook_text: updatedDraft.opening_hook_text || updatedDraft.opening_hook,
          enable_ending_hook: false,
          headline_text: updatedDraft.headline_text || updatedDraft.visual_headline || updatedDraft.title,
          tts_voice: updatedDraft.tts_voice || "en-US-ChristopherNeural",
          subtitle_preset: updatedDraft.subtitle_preset || "hormozi",
          custom_font_name: updatedDraft.custom_font_name || visualStyleConfig.customFontName || "Arial Black",
          custom_active_color: updatedDraft.custom_active_color || visualStyleConfig.customActiveColor || "#FFE600",
          custom_primary_color: updatedDraft.custom_text_color || visualStyleConfig.customTextColor || "#FFFFFF",
          custom_animation: updatedDraft.custom_animation || visualStyleConfig.customAnimation || "word_pop",
          custom_all_caps: updatedDraft.custom_all_caps ?? visualStyleConfig.customAllCaps ?? true,
          custom_outline_width: updatedDraft.custom_outline_width ?? visualStyleConfig.customOutlineWidth ?? 5.0,
          social_author: updatedDraft.card_type === "none" ? undefined : (updatedDraft.social_author || socialAuthor),
          social_handle: updatedDraft.card_type === "none" ? undefined : (updatedDraft.social_handle || socialHandle),
          social_badge: updatedDraft.social_badge || socialBadge,
          social_text: updatedDraft.card_type === "none" ? undefined : (updatedDraft.social_text || undefined),
          card_vertical_position: updatedDraft.card_vertical_position,
          card_width_percent: updatedDraft.card_width_percent,
          subtitle_vertical_position: updatedDraft.subtitle_vertical_position,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const cacheBuster = `?t=${Date.now()}`;
        const finalDownloadUrl = (data.download_url?.startsWith("http")
          ? data.download_url
          : `http://localhost:8000${data.download_url}`) + cacheBuster;
        const finalPreviewUrl = (data.preview_url?.startsWith("http")
          ? data.preview_url
          : `http://localhost:8000${data.preview_url}`) + cacheBuster;

        const finalClip: ClipCandidate = {
          ...updatedDraft,
          is_rendering: false,
          rendered_video_url: finalDownloadUrl,
          preview_url: finalPreviewUrl,
          qa_result: data.qa_result,
          title: data.title || updatedDraft.title,
          title_alternatives: data.title_alternatives || updatedDraft.title_alternatives,
          description: data.description || updatedDraft.description,
          hashtags: data.hashtags || updatedDraft.hashtags,
          tags: data.tags || updatedDraft.tags,
        };

        const finalizedList = clips.map((c) =>
          c.clip_id === finalClip.clip_id ? finalClip : c
        );
        persistClipsState(finalizedList);
        setEditingClip(finalClip);
        setModalStatusMsg("✓ 9:16 vertical render completed! High-retention MP4 ready to preview & download.");
        // Automatically switch to compiled video preview tab so user sees it instantly!
        setModalViewTab("preview");
      } else {
        const err = await res.json().catch(() => ({}));
        setModalStatusMsg(`✓ Customizations saved to Clip #${updatedDraft.index}! (${err.detail || "Ready to render"})`);
      }
    } catch {
      // Resilient local fallback when backend is offline
      setModalStatusMsg(`✓ Customizations applied to Clip #${updatedDraft.index}! (Run backend to compile MP4 video)`);
    } finally {
      setIsModalRendering(false);
    }
  };

    // Feature 4: Batch Render All Clips
  const handleBatchRenderAll = async () => {
    if (clips.length === 0) return;
    setIsBatchRendering(true);
    setBatchProgress({ current: 0, total: clips.length });
    try {
      for (let i = 0; i < clips.length; i++) {
        setBatchProgress({ current: i + 1, total: clips.length });
        await handleRenderClip(clips[i]);
      }
    } finally {
      setIsBatchRendering(false);
    }
  };

  // Filter verified rendered clips eligible for Bulk Publishing (Part C)
  const renderedClips = clips.filter((c) => Boolean(c.rendered_video_url));

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const availableCategories = ["All", ...Array.from(new Set(backgroundList.map((b) => b.category)))];
  const filteredBackgrounds = selectedBgCategory === "All"
    ? backgroundList
    : backgroundList.filter((b) => b.category === selectedBgCategory);

  return (
    <div className="flex h-screen w-full bg-[var(--color-dominant)] text-[var(--color-emphasis)] overflow-hidden font-sans">
      {/* ------------------------------------------------------------- */}
      {/* LEFT SIDEBAR (Scalereach / Motion Hybrid) */}
      {/* ------------------------------------------------------------- */}
      <aside
        className={`${
          sidebarCollapsed ? "w-16" : "w-64"
        } h-full bg-[var(--color-surface)] border-r border-[var(--color-border)] flex flex-col justify-between transition-all duration-200 z-20 shrink-0 select-none shadow-xs`}
      >
        <div>
          {/* Workspace Header: Architectural Neo-Brutalist */}
          <div className="p-4 flex items-center justify-between border-b-2 border-primary bg-surface-container-low select-none">
            {!sidebarCollapsed && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-secondary-container text-primary font-mono font-black text-xs flex items-center justify-center border-2 border-primary shadow-[2px_2px_0px_#111111]">
                  M
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-secondary-container border border-primary inline-block"></span>
                    <h3 className="font-headline font-bold text-xs text-primary leading-tight uppercase tracking-tight">
                      Shortify Studio
                    </h3>
                  </div>
                  <span className="font-mono text-[9px] uppercase font-bold text-secondary tracking-wider block mt-0.5">
                    [PRO ARCHITECT]
                  </span>
                </div>
              </div>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1.5 border border-primary bg-surface hover:bg-surface-container text-primary shadow-[1px_1px_0px_#111111] transition-all"
            >
              <ChevronRight className={`w-3.5 h-3.5 transition-transform duration-200 ${sidebarCollapsed ? "" : "rotate-180"}`} />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 flex flex-col gap-2 text-xs font-normal">
            <button
              onClick={() => setActiveMainView("dashboard")}
              className={`flex items-center gap-3 px-3 py-2 border-2 border-primary uppercase font-mono text-xs tracking-wide transition-all ${
                activeMainView === "dashboard"
                  ? "bg-primary text-on-primary shadow-[3px_3px_0px_#111111] translate-x-[-1px] font-bold"
                  : "bg-surface-container-lowest text-on-surface hover:bg-surface-container shadow-[2px_2px_0px_#111111]"
              }`}
            >
              <Home className="w-4 h-4" />
              {!sidebarCollapsed && <span>Home / Dashboard</span>}
            </button>

            <button
              onClick={() => setActiveMainView("studio")}
              className={`flex items-center gap-3 px-3 py-2 border-2 border-primary uppercase font-mono text-xs tracking-wide transition-all ${
                activeMainView === "studio"
                  ? "bg-primary text-on-primary shadow-[3px_3px_0px_#111111] translate-x-[-1px] font-bold"
                  : "bg-surface-container-lowest text-on-surface hover:bg-surface-container shadow-[2px_2px_0px_#111111]"
              }`}
            >
              <Video className="w-4 h-4" />
              {!sidebarCollapsed && <span>Video Studio</span>}
            </button>

            <button
              onClick={() => setActiveMainView("scheduler")}
              className={`flex items-center gap-3 px-3 py-2 border-2 border-primary uppercase font-mono text-xs tracking-wide transition-all ${
                activeMainView === "scheduler"
                  ? "bg-primary text-on-primary shadow-[3px_3px_0px_#111111] translate-x-[-1px] font-bold"
                  : "bg-surface-container-lowest text-on-surface hover:bg-surface-container shadow-[2px_2px_0px_#111111]"
              }`}
            >
              <Calendar className="w-4 h-4" />
              {!sidebarCollapsed && <span>Social Scheduler</span>}
            </button>

            <button
              onClick={() => setIsChannelModalOpen(true)}
              className="flex items-center gap-3 px-3 py-2 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container text-on-surface uppercase font-mono text-xs tracking-wide shadow-[2px_2px_0px_#111111] transition-all"
            >
              <YoutubeIcon className="w-4 h-4 text-red-600" />
              {!sidebarCollapsed && (
                <span className="flex items-center justify-between w-full">
                  <span>{currentChannel ? "Channel" : "Connect Channel"}</span>
                  <span className="text-[9px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold text-primary">
                    {currentChannel ? "Live" : "+10m"}
                  </span>
                </span>
              )}
            </button>
          </nav>

          {/* Tools Section */}
          {!sidebarCollapsed && (
            <div className="px-4 pt-4 border-t border-[var(--color-border)]">
              <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-emphasis)]/50 mb-2">
                Video Tools
              </p>
              <div className="flex flex-col gap-1 text-xs text-[var(--color-emphasis)]/80 font-normal">
                <div className="px-3 py-2 rounded-lg hover:bg-[var(--color-surface-alt)] cursor-pointer flex items-center justify-between transition-colors">
                  <span>Brand Templates</span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-[var(--color-accent)] font-bold text-[var(--color-emphasis)]">Pro</span>
                </div>
                <div className="px-3 py-2 rounded-lg hover:bg-[var(--color-surface-alt)] cursor-pointer transition-colors">
                  Subway Surfer Library
                </div>
                <div className="px-3 py-2 rounded-lg hover:bg-[var(--color-surface-alt)] cursor-pointer transition-colors">
                  Minecraft Gameplay 4K
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-[var(--color-border)] flex flex-col gap-2">
          {!sidebarCollapsed && (
            <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-xs shadow-xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-[var(--color-emphasis)]">Creator Plan</span>
                <span className="text-[10px] font-bold text-[var(--color-emphasis)]/70">Unlimited</span>
              </div>
              <p className="text-[11px] text-[var(--color-emphasis)]/70 mb-3 leading-relaxed">Full 1080p 60fps rendering with zero watermarks</p>
              <button className="w-full py-2 rounded-lg bg-[var(--color-emphasis)] hover:bg-[var(--color-secondary)] text-white text-xs font-bold shadow-xs transition-colors">
                Workspace Settings
              </button>
            </div>
          )}
          <div className="flex items-center justify-between text-xs text-[var(--color-emphasis)]/70 px-2 py-1">
            <button className="flex items-center gap-2 hover:text-[var(--color-emphasis)] transition-colors">
              <Settings className="w-4 h-4" />
              {!sidebarCollapsed && <span>Preferences</span>}
            </button>
            {!sidebarCollapsed && <span className="text-[11px] font-light">v2.4</span>}
          </div>
        </div>
      </aside>

      {/* ------------------------------------------------------------- */}
      {/* MAIN VIEWPORT CANVAS */}
      {/* ------------------------------------------------------------- */}
      <div className="flex-1 flex flex-col h-full overflow-y-auto bg-[var(--color-dominant)]">
        {/* Top Architectural Operational Ribbon */}
        <header className="h-16 border-b-2 border-primary bg-surface px-6 flex items-center justify-between shrink-0 shadow-sm z-30 select-none">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 border border-primary bg-surface-container font-mono text-[11px] uppercase">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary-fixed opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-tertiary-fixed"></span>
              </span>
              <span className="font-bold text-primary">STREAM_SYNC: YOUTUBE LIVE</span>
            </div>

            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 border border-primary bg-surface-container-low font-mono text-[11px] text-primary">
              <span className="font-bold">WHISPER-V3 [60FPS ACTIVE]</span>
              <span className="text-outline">/</span>
              <span className="font-bold text-secondary uppercase">+38% RETENTION BOOST</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 border border-primary bg-surface font-mono text-[11px]">
              <Clock className="w-3.5 h-3.5 text-primary" />
              <span>QUOTA:</span>
              <span className="font-bold">420 MINS</span>
              <span className="text-outline">/</span>
              <span className="font-bold uppercase text-secondary">PRO STUDIO</span>
            </div>

            {currentChannel ? (
              <button
                onClick={() => setIsChannelModalOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 border border-primary bg-surface hover:bg-surface-container-low text-xs font-mono font-bold text-primary shadow-[2px_2px_0px_#111111] transition-all"
              >
                <YoutubeIcon className="w-3.5 h-3.5 text-red-600" />
                <span>{currentChannel.custom_url || "@peakheistclips"}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </button>
            ) : (
              <button
                onClick={() => setIsChannelModalOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 border-2 border-primary bg-secondary-container text-xs font-mono font-bold text-primary shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] transition-all"
              >
                <YoutubeIcon className="w-3.5 h-3.5 text-red-600" />
                <span>Connect Channel (+10m)</span>
              </button>
            )}

            <button
              onClick={() => setActiveMainView("studio")}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 border-2 border-primary bg-secondary-container text-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[1px_1px_0px_#111111] transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Ingest</span>
            </button>

            <div className="w-8 h-8 rounded-full bg-primary text-on-primary font-bold text-xs flex items-center justify-center border-2 border-primary shadow-[2px_2px_0px_#d5eb45]">
              AS
            </div>
          </div>
        </header>

        {activeMainView === "dashboard" ? (
          <DashboardView
            currentChannel={currentChannel}
            onOpenConnectModal={() => setIsChannelModalOpen(true)}
            onStartClipping={(url, clipType) => {
              setYoutubeUrl(url);
              if (clipType) {
                setSelectedTemplate(
                  clipType === "summary"
                    ? "Fast Summary"
                    : clipType === "action"
                    ? "Action Highlights"
                    : "Viral Clips"
                );
              }
              setActiveMainView("studio");
              setTimeout(() => {
                const processBtn = document.getElementById("start-processing-btn");
                if (processBtn) processBtn.click();
              }, 200);
            }}
            onOpenStudio={() => setActiveMainView("studio")}
            recentVideos={recentVideos}
          />
        ) : activeMainView === "scheduler" ? (
          <SchedulerView
            currentChannel={currentChannel}
            onOpenConnectModal={() => setIsChannelModalOpen(true)}
            onSwitchToStudio={() => setActiveMainView("studio")}
          />
        ) : (
          /* Content Container */
          <div className="max-w-5xl w-full mx-auto px-4 py-3 sm:px-6 sm:py-4 flex flex-col gap-3.5">
            {/* Greeting Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl sm:text-2xl font-black text-[var(--color-emphasis)] tracking-tight">
                  Video Studio
                </h1>
                <p className="text-xs text-[var(--color-emphasis)]/70 mt-0.5 leading-relaxed">
                  Autonomous 9:16 virality clipping, speaker auto-framing, and kinetic subtitles
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-xs font-bold text-[var(--color-emphasis)] shadow-xs">
                  <Clock className="w-3.5 h-3.5 text-[var(--color-emphasis)]/70" />
                  <span>10 min quota</span>
                </div>
                <button className="px-3.5 py-1.5 rounded-lg bg-[var(--color-surface)] hover:bg-[var(--color-surface-alt)] border border-[var(--color-border)] text-[var(--color-emphasis)] text-xs font-bold shadow-xs transition-colors">
                  Quota Details
                </button>
              </div>
            </div>

            {/* Central Input Box & One-Click Button */}
            <div className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] p-3.5 sm:p-4 flex flex-col gap-3 shadow-sm">
              {/* YouTube Connect Banner */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-accent-tint)] border border-[var(--color-accent)]/40 text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-red-600 flex items-center justify-center text-white text-[10px] font-bold">
                    ▶
                  </div>
                  <span className="font-normal text-[var(--color-emphasis)]">
                    Connect your YouTube channel to import and publish videos directly
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-[var(--color-accent)] text-[var(--color-emphasis)] font-bold text-[10px]">
                    +10 min bonus
                  </span>
                </div>
                <button
                  onClick={() => setIsChannelModalOpen(true)}
                  className="text-xs font-bold text-[var(--color-emphasis)] hover:underline"
                >
                  Connect Channel
                </button>
              </div>

              {/* URL Input Bar */}
              <div className="relative flex items-center">
                <input
                  type="text"
                  value={youtubeUrl}
                  onChange={(e) => {
                    setYoutubeUrl(e.target.value);
                    if (e.target.value) setSelectedFile(null);
                  }}
                  placeholder="Paste a YouTube, Twitch, Drive, Dropbox or direct video link"
                  className="w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-alt)] text-sm text-[var(--color-emphasis)] placeholder-[var(--color-emphasis)]/40 outline-none focus:border-[var(--color-emphasis)] focus:bg-[var(--color-surface)] focus:ring-1 focus:ring-[var(--color-accent)] transition-all"
                />
              </div>

              {/* Selected File Banner */}
              {selectedFile && (
                <div className="px-4 py-2 rounded-lg bg-[var(--color-accent-tint)] border border-[var(--color-accent)]/40 text-xs flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileVideo className="w-4 h-4 text-[var(--color-emphasis)]" />
                    <span className="font-bold text-[var(--color-emphasis)]">{selectedFile.name}</span>
                    <span className="text-[var(--color-emphasis)]/60">({(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)</span>
                  </div>
                  <button onClick={() => setSelectedFile(null)} className="text-[var(--color-emphasis)]/60 hover:text-[var(--color-emphasis)]">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* ------------------------------------------------------------------------- */}
              {/* VISUAL STYLE STUDIO: Caption Styles, Layouts, Social Cards & Backgrounds  */}
              {/* ------------------------------------------------------------------------- */}
              <VisualStyleStudio
                config={visualStyleConfig}
                onChangeConfig={setVisualStyleConfig}
              />

              {/* BIG PROMINENT ACTION BUTTON: Neo-Brutalist Acid Lime CTA */}
              <button
                id="start-processing-btn"
                onClick={handleGetClips}
                disabled={isProcessing || (!youtubeUrl && !selectedFile)}
                className="w-full py-3 px-6 border-2 border-primary bg-primary text-on-primary font-mono text-sm uppercase tracking-wider font-bold shadow-[4px_4px_0px_#d5eb45] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_#d5eb45] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none disabled:opacity-40 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-secondary-container" />
                    <span className="text-secondary-container">{activeStep || "Analyzing Virality & Compiling Kinetic Subtitles..."}</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-secondary-container" />
                    <span>[GET CLIPS IN 1 CLICK]</span>
                  </>
                )}
              </button>

              {/* Upload file link + Supported platforms */}
              <div className="flex flex-wrap items-center justify-between text-xs text-[var(--color-emphasis)]/60 pt-0.5">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="video/mp4,video/quicktime"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      setSelectedFile(f);
                      setYoutubeUrl("");
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 font-bold text-[var(--color-emphasis)] hover:underline"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload local video file</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--color-accent)] text-[var(--color-emphasis)] font-bold">1080p</span>
                </button>

                <div className="flex items-center gap-2 text-[11px] text-[var(--color-emphasis)]/60">
                  <span>Compatible with YouTube, Google Drive, Zoom & MP4/MOV files</span>
                </div>
              </div>
            </div>

            {/* ----------------------------------------------------------- */}
            {/* STREAMLINED AI CLIP EXTRACTION & REFRAMING BAR */}
            {/* ----------------------------------------------------------- */}
            <div className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] p-3 sm:p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
              {/* Target Duration Pills */}
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-[var(--color-emphasis)]">Target Clip Window:</span>
                <div className="flex items-center gap-1 bg-[var(--color-surface-alt)] p-0.5 rounded-lg border border-[var(--color-border)]">
                  {["Auto", "0 - 30s", "30 - 60s", "1 - 2 min"].map((pill) => (
                    <button
                      key={pill}
                      type="button"
                      onClick={() => setClipDurationPill(pill)}
                      className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer ${
                        clipDurationPill === pill
                          ? "bg-[var(--color-emphasis)] text-white shadow-xs"
                          : "text-[var(--color-emphasis)]/70 hover:text-[var(--color-emphasis)]"
                      }`}
                    >
                      {pill}
                    </button>
                  ))}
                </div>
              </div>

              {/* Toggles: Smart Reframing & Voice Hook */}
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-1.5 text-xs font-bold text-[var(--color-emphasis)] cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={smartReframing}
                    onChange={(e) => setSmartReframing(e.target.checked)}
                    className="w-3.5 h-3.5 accent-[var(--color-emphasis)]"
                  />
                  <span>Smart Auto-Framing</span>
                </label>
                <label className="flex items-center gap-1.5 text-xs font-bold text-[var(--color-emphasis)] cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={autoHook}
                    onChange={(e) => setAutoHook(e.target.checked)}
                    className="w-3.5 h-3.5 accent-[var(--color-emphasis)]"
                  />
                  <span>Opening Hook Voice</span>
                </label>
              </div>
            </div>

            {/* ----------------------------------------------------------- */}
            {/* RESULTS SCREEN */}
            {/* ----------------------------------------------------------- */}
            {clips.length > 0 && (
              <div className="flex flex-col gap-6">
                {/* Top Banner */}
                <div className="flex flex-col gap-3">
                  {/* Video Info Header */}
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-bold text-[var(--color-emphasis)]">
                        {currentVideo?.title || "35 Years of Life Lessons in Just 5 Minutes"}
                      </h2>
                      <div className="flex items-center gap-2 text-xs font-normal text-[var(--color-emphasis)]/60 mt-1">
                        <span className="px-2.5 py-0.5 rounded-full bg-red-50 text-red-700 font-bold border border-red-200">YouTube</span>
                        <span className="px-2.5 py-0.5 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-emphasis)]">9:16 Vertical</span>
                        <span className="px-2.5 py-0.5 rounded-full bg-[var(--color-accent-tint)] text-[var(--color-emphasis)] border border-[var(--color-accent)]/60 font-bold">Viral Clips</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={handleBatchRenderAll}
                        disabled={isBatchRendering || clips.length === 0}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-emphasis)] hover:bg-[var(--color-secondary)] text-white text-xs font-bold shadow-xs disabled:opacity-50 transition-colors"
                      >
                        {isBatchRendering ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin text-[var(--color-accent)]" />
                            <span>Rendering ({batchProgress.current}/{batchProgress.total})...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                            <span>Render All ({clips.length} Shorts)</span>
                          </>
                        )}
                      </button>

                      {/* Dynamic Bulk Publish & Schedule Action (Parts C & E) */}
                      <button
                        onClick={() => setIsBulkPublishModalOpen(true)}
                        disabled={renderedClips.length === 0}
                        title={
                          renderedClips.length === 0
                            ? "No rendered Shorts available to publish. Render clips first."
                            : `Publish or schedule all ${renderedClips.length} rendered Shorts`
                        }
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-xs disabled:opacity-40 transition-colors"
                      >
                        <Rocket className="w-3.5 h-3.5 text-white" />
                        <span>Publish All Rendered ({renderedClips.length} Shorts)</span>
                      </button>

                      <a
                        href="http://localhost:8000/api/v1/shorts/batch-download-zip"
                        download="motion_shorts_bundle.zip"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-accent-tint)] border border-[var(--color-accent)] hover:bg-[var(--color-accent-hover)]/30 text-[var(--color-emphasis)] text-xs font-bold shadow-xs transition-colors"
                      >
                        <Download className="w-3.5 h-3.5 text-[var(--color-emphasis)]" />
                        <span>Download All (ZIP)</span>
                      </a>

                      <div className="flex items-center bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-0.5 ml-1">
                        <button
                          onClick={() => setViewMode("list")}
                          className={`p-1.5 rounded-md transition-colors ${viewMode === "list" ? "bg-[var(--color-accent)] text-[var(--color-emphasis)]" : "text-[var(--color-emphasis)]/60 hover:text-[var(--color-emphasis)]"}`}
                        >
                          <List className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setViewMode("grid")}
                          className={`p-1.5 rounded-md transition-colors ${viewMode === "grid" ? "bg-[var(--color-accent)] text-[var(--color-emphasis)]" : "text-[var(--color-emphasis)]/60 hover:text-[var(--color-emphasis)]"}`}
                        >
                          <Grid className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Batch Selection Transparency Banner (Part A) */}
                  {clips.length > 0 && (
                    <div className="p-3.5 rounded-lg border-2 border-primary bg-surface-container flex flex-wrap items-center justify-between gap-3 text-xs shadow-[3px_3px_0px_#111111]">
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-2.5 py-1 border border-primary font-mono font-bold text-[10px] uppercase tracking-wider ${
                            clips[0]?.is_fallback
                              ? "bg-amber-300 text-primary"
                              : "bg-[#d5eb45] text-primary"
                          }`}
                        >
                          {clips[0]?.is_fallback ? "TOP-5 FALLBACK" : "QUALIFIED (>60)"}
                        </span>
                        <span className="font-mono text-xs font-bold text-primary">
                          {clips[0]?.batch_message ||
                            (clips[0]?.is_fallback
                              ? `No Shorts scored above 60. Showing the top ${clips.length} available candidates.`
                              : `Selected all ${clips.length} Shorts with virality scores above 60.`)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 font-mono text-[11px] text-secondary">
                        <span className="px-2 py-0.5 border border-primary bg-surface-container-lowest">
                          Strict Condition: virality_score &gt; 60
                        </span>
                        <span className="font-bold text-primary px-2 py-0.5 border border-primary bg-[#d5eb45]/30">
                          IST (Asia/Kolkata)
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Clip Cards List */}
                <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 gap-6" : "flex flex-col gap-6"}>
                  {clips.map((clip) => {
                    const cardTab = activeCardTabs[clip.clip_id] || "transcript";
                    const isLiked = likedClips[clip.clip_id] || false;

                    return (
                      <div
                        key={clip.clip_id}
                        className="border-2 border-primary bg-surface-container-lowest shadow-[4px_4px_0px_#000000] flex flex-col overflow-hidden"
                      >
                        {/* Architectural Card Header Strip */}
                        <div className="p-3 px-4 border-b-2 border-primary bg-surface-container flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="px-2 py-0.5 border border-primary bg-[#d5eb45] text-primary font-mono text-[10px] font-bold uppercase tracking-wider shadow-[1px_1px_0px_#111111]">
                              {clip.candidate_rank ? `RANK #${String(clip.candidate_rank).padStart(2, "0")}` : (clip.index === 1 ? "RANK #01 • TOP CANDIDATE" : `RANK #${String(clip.index).padStart(2, "0")}`)}
                            </span>
                            <span
                              className={`px-2 py-0.5 border border-primary font-mono text-[10px] font-bold uppercase tracking-wider shadow-[1px_1px_0px_#111111] ${
                                clip.is_fallback
                                  ? "bg-amber-300 text-primary"
                                  : "bg-emerald-300 text-primary"
                              }`}
                            >
                              {clip.is_fallback ? "TOP-5 FALLBACK" : "QUALIFIED (>60)"}
                            </span>
                            <span className="font-mono text-[10px] text-outline font-bold">
                              SOURCE TC: {Math.floor(clip.start_sec / 60)}:{String(Math.floor(clip.start_sec % 60)).padStart(2, "0")} → {Math.floor(clip.end_sec / 60)}:{String(Math.floor(clip.end_sec % 60)).padStart(2, "0")}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className="px-2.5 py-0.5 border border-primary bg-surface-container-lowest text-xs font-mono font-bold text-primary flex items-center gap-1 shadow-[1px_1px_0px_#111111]"
                              title={clip.selection_reason || `Virality Score: ${clip.virality_score || 95}/100`}
                            >
                              🔥 {clip.virality_breakdown?.total_virality || clip.virality_score || clip.engagement_score || 95}/100
                            </span>
                          </div>
                        </div>

                        {/* Card Body: 2 Columns */}
                        <div className="p-4 sm:p-6 grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                          {/* Left: 9:16 Vertical Video Preview (5 cols) */}
                          <div className="md:col-span-5 aspect-[9/16] bg-primary border-2 border-primary shadow-[3px_3px_0px_#000000] relative flex flex-col items-center justify-center overflow-hidden">
                            {clip.rendered_video_url ? (
                              <div className="relative w-full h-full">
                                <span className="absolute top-2 left-2 px-2 py-0.5 bg-primary text-on-primary font-mono text-[9px] font-bold z-10 border border-primary">
                                  {clip.layout_mode === "tweet_card" ? "X / Twitter Card" : clip.layout_mode === "split_screen_comment" ? "Superchat Badge" : "Split Screen 9:16"}
                                </span>
                                <video
                                  src={clip.rendered_video_url}
                                  controls
                                  className="w-full h-full object-cover"
                                />
                              </div>
                            ) : (
                              <div className="flex flex-col items-center gap-3 p-4 text-center">
                                <div className="w-12 h-12 border-2 border-[#d5eb45] bg-surface-container flex items-center justify-center shadow-[2px_2px_0px_#d5eb45]">
                                  <Scissors className="w-5 h-5 text-primary" />
                                </div>
                                <span className="font-mono text-xs text-on-primary font-bold">
                                  {clip.duration_sec.toFixed(0)}s Segment ({clip.start_sec.toFixed(1)}s → {clip.end_sec.toFixed(1)}s)
                                </span>
                                <button
                                  onClick={() => handleRenderClip(clip)}
                                  disabled={clip.is_rendering}
                                  className="px-4 py-2 border-2 border-primary bg-[#d5eb45] hover:bg-surface-container text-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] disabled:opacity-50 flex items-center gap-2 transition-all cursor-pointer"
                                >
                                  {clip.is_rendering ? (
                                    <>
                                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                      <span>Rendering 9:16...</span>
                                    </>
                                  ) : (
                                    <>
                                      <Play className="w-3.5 h-3.5 fill-current" />
                                      <span>Render 9:16 MP4</span>
                                    </>
                                  )}
                                </button>
                              </div>
                            )}
                          </div>

                          {/* Right: Tabs & Hooks Details (7 cols) */}
                          <div className="md:col-span-7 flex flex-col justify-between gap-4 h-full">
                            <div>
                              <h3 className="font-headline font-bold text-sm sm:text-base uppercase tracking-tight text-primary leading-snug line-clamp-2 mb-3">
                                #{clip.index} {clip.visual_headline || clip.title}
                              </h3>

                              {/* Tabs Strip */}
                              <div className="flex items-center gap-2 mb-3">
                                <button
                                  onClick={() =>
                                    setActiveCardTabs((prev) => ({ ...prev, [clip.clip_id]: "transcript" }))
                                  }
                                  className={`px-3 py-1.5 border-2 border-primary font-mono text-xs uppercase font-bold transition-all ${
                                    cardTab === "transcript"
                                      ? "bg-primary text-on-primary shadow-[2px_2px_0px_#111111]"
                                      : "bg-surface-container-lowest text-on-surface hover:bg-surface-container"
                                  }`}
                                >
                                  <FileText className="w-3.5 h-3.5 inline mr-1" />
                                  <span>Transcript</span>
                                </button>
                                <button
                                  onClick={() =>
                                    setActiveCardTabs((prev) => ({ ...prev, [clip.clip_id]: "viral" }))
                                  }
                                  className={`px-3 py-1.5 border-2 border-primary font-mono text-xs uppercase font-bold transition-all ${
                                    cardTab === "viral"
                                      ? "bg-primary text-on-primary shadow-[2px_2px_0px_#111111]"
                                      : "bg-surface-container-lowest text-on-surface hover:bg-surface-container"
                                  }`}
                                >
                                  <Sparkles className="w-3.5 h-3.5 inline mr-1 text-[#d5eb45]" />
                                  <span>Virality Breakdown</span>
                                </button>
                              </div>

                              {/* Dialogue or Why Viral Content Box */}
                              {cardTab === "transcript" ? (
                                <div className="p-3 bg-surface-container-low border-2 border-primary font-mono text-xs text-primary leading-relaxed max-h-48 overflow-y-auto">
                                  {clip.spoken_text}
                                </div>
                              ) : (
                                <div className="p-3 bg-surface-container-low border-2 border-primary space-y-3">
                                  <p className="font-body text-xs text-on-surface-variant leading-relaxed">
                                    {clip.why_viral || clip.why_engaging || "This clip opens with an engaging premise and maintains strong retention throughout the sequence."}
                                  </p>

                                  {/* 4-Vector Virality Breakdown Bars */}
                                  <div className="pt-2 border-t border-primary/20">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-outline">
                                        4-Vector Virality Analysis
                                      </span>
                                      <span className="font-mono text-xs font-bold text-primary">
                                        {clip.virality_breakdown?.total_virality || clip.virality_score || clip.engagement_score || 90}/100
                                      </span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                                      {/* Hook */}
                                      <div className="bg-surface-container-lowest p-2 border border-primary">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-outline">🪝 Hook</span>
                                          <span className="font-bold text-primary">
                                            {clip.virality_breakdown?.hook_score || 23}/25
                                          </span>
                                        </div>
                                        <div className="w-full bg-surface-container h-1.5 border border-primary/40 overflow-hidden">
                                          <div
                                            className="bg-primary h-full"
                                            style={{ width: `${((clip.virality_breakdown?.hook_score || 23) / 25) * 100}%` }}
                                          />
                                        </div>
                                      </div>
                                      {/* Engagement */}
                                      <div className="bg-surface-container-lowest p-2 border border-primary">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-outline">⚡ Engagement</span>
                                          <span className="font-bold text-primary">
                                            {clip.virality_breakdown?.engagement_score || 22}/25
                                          </span>
                                        </div>
                                        <div className="w-full bg-surface-container h-1.5 border border-primary/40 overflow-hidden">
                                          <div
                                            className="bg-[#d5eb45] h-full"
                                            style={{ width: `${((clip.virality_breakdown?.engagement_score || 22) / 25) * 100}%` }}
                                          />
                                        </div>
                                      </div>
                                      {/* Value */}
                                      <div className="bg-surface-container-lowest p-2 border border-primary">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-outline">💎 Value</span>
                                          <span className="font-bold text-primary">
                                            {clip.virality_breakdown?.value_score || 24}/25
                                          </span>
                                        </div>
                                        <div className="w-full bg-surface-container h-1.5 border border-primary/40 overflow-hidden">
                                          <div
                                            className="bg-primary h-full"
                                            style={{ width: `${((clip.virality_breakdown?.value_score || 24) / 25) * 100}%` }}
                                          />
                                        </div>
                                      </div>
                                      {/* Shareability */}
                                      <div className="bg-surface-container-lowest p-2 border border-primary">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-outline">🚀 Shareability</span>
                                          <span className="font-bold text-primary">
                                            {clip.virality_breakdown?.shareability_score || 21}/25
                                          </span>
                                        </div>
                                        <div className="w-full bg-surface-container h-1.5 border border-primary/40 overflow-hidden">
                                          <div
                                            className="bg-[#d5eb45] h-full"
                                            style={{ width: `${((clip.virality_breakdown?.shareability_score || 21) / 25) * 100}%` }}
                                          />
                                        </div>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="pt-2 border-t border-primary/20">
                                    <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-outline block mb-1.5">
                                      Key Narrative Hooks
                                    </span>
                                    <div className="flex flex-wrap items-center gap-1.5">
                                      {(clip.key_hooks || ["Contrarian thesis", "Relatable problem"]).map((kh) => (
                                        <div
                                          key={kh}
                                          className="flex items-center gap-1.5 px-2 py-0.5 border border-primary bg-surface-container-lowest font-mono text-[10px] font-bold text-primary"
                                        >
                                          <span className="w-1.5 h-1.5 rounded-full bg-[#d5eb45]" />
                                          <span>{kh}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Card Bottom Actions Bar: [Download] [Edit] [Post/Schedule] + Icons */}
                            <div className="pt-3 border-t-2 border-primary flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2 flex-wrap">
                                <a
                                  href={clip.rendered_video_url || `http://localhost:8000/api/v1/shorts/download/short_${clip.clip_id}.mp4`}
                                  download={`short_${clip.clip_id}.mp4`}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1.5 px-3.5 py-2 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all"
                                >
                                  <Download className="w-3.5 h-3.5 text-[#d5eb45]" />
                                  <span>Download</span>
                                </a>

                                <button
                                  onClick={() => setEditingClip(clip)}
                                  className="inline-flex items-center gap-1.5 px-3 py-2 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container text-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] transition-all"
                                >
                                  <SlidersHorizontal className="w-3.5 h-3.5" />
                                  <span>Customize</span>
                                </button>

                                <button
                                  onClick={() => setSchedulingClip(clip)}
                                  className="inline-flex items-center gap-1.5 px-3 py-2 border-2 border-primary bg-[#d5eb45] hover:bg-surface-container text-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] transition-all"
                                >
                                  <Share className="w-3.5 h-3.5 text-primary" />
                                  <span>Post / Schedule</span>
                                </button>
                              </div>

                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() => setLikedClips((prev) => ({ ...prev, [clip.clip_id]: !isLiked }))}
                                  className={`p-1.5 border border-primary bg-surface-container-lowest hover:bg-surface-container transition-colors ${
                                    isLiked ? "text-red-600 fill-red-600" : "text-outline"
                                  }`}
                                  title="Like clip"
                                >
                                  <Heart className={`w-4 h-4 ${isLiked ? "fill-red-600" : ""}`} />
                                </button>
                                <button
                                  onClick={() => copyToClipboard(clip.spoken_text, clip.clip_id)}
                                  className="p-1.5 border border-primary bg-surface-container-lowest hover:bg-surface-container text-outline hover:text-primary transition-colors"
                                  title="Copy dialogue"
                                >
                                  <Copy className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => setClips((prev) => prev.filter((c) => c.clip_id !== clip.clip_id))}
                                  className="p-1.5 border border-primary bg-surface-container-lowest hover:bg-red-100 text-outline hover:text-red-700 transition-colors"
                                  title="Dismiss clip"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------- */}
      {/* ------------------------------------------------------------- */}
      {/* CUSTOMIZE / EDIT MODAL (Architectural Neo-Brutalist Studio) */}
      {/* ------------------------------------------------------------- */}
      {editingClip && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4 overflow-y-auto animate-in fade-in duration-200">
          <div className="bg-surface-container-lowest border-2 border-primary shadow-[6px_6px_0px_#111111] max-w-6xl w-full max-h-[94vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-3.5 sm:p-4 border-b-2 border-primary flex items-center justify-between bg-surface-container text-primary">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 border-2 border-primary bg-[#d5eb45] flex items-center justify-center font-mono font-bold text-xs shadow-[2px_2px_0px_#111111]">
                  #{editingClip.index}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-headline font-bold text-sm uppercase tracking-tight text-primary">
                      Kinetic Subtitles &amp; Social Card Studio
                    </h3>
                    <span className="font-mono text-[10px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold">
                      {editingClip.subtitle_preset ? editingClip.subtitle_preset.toUpperCase() : "HORMOZI POP"}
                    </span>
                  </div>
                  <p className="font-mono text-[11px] text-outline mt-0.5">
                    Live draggable canvas, 3 viral archetype formats, and instant MP4 preview
                  </p>
                </div>
              </div>

              {/* View Switcher Tabs inside header */}
              <div className="flex items-center gap-2">
                <div className="inline-flex border-2 border-primary shadow-[2px_2px_0px_#111111] overflow-hidden bg-surface-container-lowest">
                  <button
                    type="button"
                    onClick={() => setModalViewTab("canvas")}
                    className={`px-3 py-1.5 font-mono text-xs font-bold uppercase transition-colors cursor-pointer ${
                      modalViewTab === "canvas"
                        ? "bg-[#d5eb45] text-primary"
                        : "bg-surface-container-lowest text-primary hover:bg-surface-container"
                    }`}
                  >
                    1. Canvas &amp; Drag
                  </button>
                  <button
                    type="button"
                    onClick={() => setModalViewTab("preview")}
                    className={`px-3 py-1.5 font-mono text-xs font-bold uppercase transition-colors cursor-pointer flex items-center gap-1.5 border-l-2 border-primary ${
                      modalViewTab === "preview"
                        ? "bg-[#d5eb45] text-primary"
                        : "bg-surface-container-lowest text-primary hover:bg-surface-container"
                    }`}
                  >
                    <span>2. Compiled MP4</span>
                    {editingClip.rendered_video_url && (
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    )}
                  </button>
                </div>

                <button
                  onClick={handleCloseModal}
                  className="p-1.5 border border-primary bg-surface-container-lowest hover:bg-surface-container shadow-[1px_1px_0px_#111111] transition-colors cursor-pointer ml-2"
                  title="Save and close"
                >
                  <X className="w-4 h-4 text-primary" />
                </button>
              </div>
            </div>

            {/* Modal Body: 2 Columns */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* LEFT COLUMN: 9:16 Interactive Simulation Canvas (5 cols) */}
              <div className="lg:col-span-5 flex flex-col gap-3">
                <div className="bg-surface-container-lowest border-2 border-primary shadow-[4px_4px_0px_#111111] p-3 flex flex-col">
                  {/* Viewport Info Bar */}
                  <div className="flex items-center justify-between pb-2 mb-2 border-b-2 border-primary font-mono text-[10px]">
                    <div className="flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 inline-block border border-primary ${modalViewTab === "preview" ? "bg-emerald-500" : "bg-red-600"}`}></span>
                      <span className="font-bold text-primary">
                        {modalViewTab === "canvas" ? "LIVE DRAGGABLE CANVAS" : "COMPILED 9:16 MP4"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-outline">1080×1920 (9:16)</span>
                      <span className="px-1 py-0.2 bg-[#d5eb45] border border-primary font-bold">4K READY</span>
                    </div>
                  </div>

                  {/* 9:16 Phone Frame */}
                  <div className="relative w-full aspect-[9/16] bg-black border-2 border-primary shadow-[3px_3px_0px_#111111] overflow-hidden select-none">
                    {modalViewTab === "canvas" ? (
                      /* TAB 1: INTERACTIVE DRAGGABLE CANVAS (Decoupled Card & Subtitles) */
                      <div
                        ref={canvasRef}
                        onPointerMove={(e) => {
                          if (!canvasRef.current) return;
                          const rect = canvasRef.current.getBoundingClientRect();
                          const relY = e.clientY - rect.top;
                          const pct = Math.max(10, Math.min(88, Math.round((relY / rect.height) * 100)));
                          if (isDraggingCard) {
                            setEditingClip({
                              ...editingClip,
                              card_vertical_position: pct,
                            });
                          } else if (isDraggingSubtitle) {
                            setEditingClip({
                              ...editingClip,
                              subtitle_vertical_position: pct,
                            });
                          }
                        }}
                        onPointerUp={() => {
                          setIsDraggingCard(false);
                          setIsDraggingSubtitle(false);
                        }}
                        className="relative w-full h-full overflow-hidden flex flex-col justify-between"
                      >
                        {/* Background clean ambient layer */}
                        <div className="absolute inset-0 z-0">
                          <div
                            className="w-full h-full bg-cover bg-center"
                            style={{
                              backgroundImage: "url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80')",
                            }}
                          />
                          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/85 pointer-events-none" />
                          {/* Reels Safe Zone Bounds */}
                          <div className="absolute inset-0 pointer-events-none border-x-2 border-dashed border-[#d5eb45]/30 m-3 flex flex-col justify-between p-2">
                            <span className="font-mono text-[8px] text-[#d5eb45]/80 tracking-widest">[REELS SAFE BOUND]</span>
                            <div className="w-full border-b border-dashed border-[#d5eb45]/30 pb-1">
                              <span className="font-mono text-[8px] text-[#d5eb45]/80 tracking-widest">[HUD AVOIDANCE ZONE]</span>
                            </div>
                          </div>
                        </div>

                        {/* Top Phone Header Simulation */}
                        <div className="relative z-20 flex items-center justify-between p-2.5 text-white font-mono text-[10px]">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-bold">5G STUDIO</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="px-1.5 py-0.2 bg-black/80 border border-white/40 text-[8px]">9:16 FEED</span>
                          </div>
                        </div>

                        {/* 1. INDEPENDENT DRAGGABLE HOOK CARD (Only if card_type is not 'none') */}
                        {editingClip.card_type && editingClip.card_type !== "none" && editingClip.card_type !== "pure_video" && (
                          <div
                            style={{
                              top: `${editingClip.card_vertical_position ?? 18}%`,
                              width: `${editingClip.card_width_percent ?? 92}%`,
                              transform: "translate(-50%, 0)",
                            }}
                            className="absolute left-1/2 z-30 transition-all select-none"
                          >
                            {/* Card Drag Handle Bar */}
                            <div
                              onPointerDown={(e) => {
                                try { (e.target as HTMLElement).setPointerCapture(e.pointerId); } catch {}
                                setIsDraggingCard(true);
                              }}
                              onPointerUp={(e) => {
                                try { (e.target as HTMLElement).releasePointerCapture(e.pointerId); } catch {}
                                setIsDraggingCard(false);
                              }}
                              className="flex items-center justify-between px-2 py-0.5 bg-[#d5eb45] text-primary border border-primary font-mono text-[9px] font-black cursor-grab active:cursor-grabbing mb-1 shadow-[1px_1px_0px_#111111]"
                              title="Drag up or down to reposition card vertically"
                            >
                              <span className="flex items-center gap-1">
                                <GripVertical className="w-3 h-3 text-primary" />
                                <span>[DRAG CARD Y]</span>
                              </span>
                              <span>Y: {editingClip.card_vertical_position ?? 18}%</span>
                            </div>

                            {/* X / Twitter Card */}
                            {(editingClip.card_type === "tweet_card" || editingClip.card_type === "twitter_card") && (
                              <div className="w-full bg-black/95 border border-white/20 p-2.5 rounded-lg shadow-xl">
                                <div className="flex items-center gap-2 mb-1">
                                  <div className="w-6 h-6 rounded-full bg-neutral-700 flex items-center justify-center font-bold text-xs text-white">
                                    {(editingClip.social_author || "A")[0].toUpperCase()}
                                  </div>
                                  <div className="flex flex-col">
                                    <div className="flex items-center gap-1">
                                      <span className="font-sans font-bold text-xs text-white truncate max-w-[130px]">
                                        {editingClip.social_author || "Peak Heist Clips"}
                                      </span>
                                      <img src="/logos/twitter_verified.png" alt="Verified" className="w-3.5 h-3.5 inline-block shrink-0" />
                                    </div>
                                    <span className="font-mono text-[8px] text-neutral-400">
                                      {editingClip.social_handle || "@peakheistclips"}
                                    </span>
                                  </div>
                                </div>
                                <p className="font-sans text-xs text-white font-medium leading-snug">
                                  {editingClip.opening_hook_text || editingClip.opening_hook || editingClip.headline_text || editingClip.visual_headline || editingClip.title}
                                </p>
                              </div>
                            )}

                            {/* Reddit Card */}
                            {editingClip.card_type === "reddit_card" && (
                              <div className="w-full bg-white text-black border border-neutral-300 p-2.5 rounded-lg shadow-xl">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <img src="/logos/reddit_logo.png" alt="Reddit" className="w-5 h-5 rounded-full object-cover shrink-0" />
                                  <div className="flex flex-col">
                                    <span className="font-sans font-bold text-xs text-black">
                                      {editingClip.social_author || "r/peakheistclips"}
                                    </span>
                                    <span className="font-sans text-[8px] text-neutral-500">
                                      {editingClip.social_handle || "u/peakheistclips"} • 2h ago
                                    </span>
                                  </div>
                                </div>
                                <p className="font-sans text-xs font-bold text-black leading-snug">
                                  {editingClip.opening_hook_text || editingClip.opening_hook || editingClip.headline_text || editingClip.visual_headline || editingClip.title}
                                </p>
                                <div className="mt-1 text-[8px] font-sans text-neutral-500">
                                  ↑ 2.4k • 183 comments
                                </div>
                              </div>
                            )}

                            {/* Instagram Card */}
                            {editingClip.card_type === "instagram_card" && (
                              <div className="w-full bg-[#121212] text-white border border-white/20 p-2.5 rounded-lg shadow-xl">
                                <div className="flex items-center justify-between mb-1">
                                  <div className="flex items-center gap-1.5">
                                    <img src="/logos/instagram_logo.png" alt="Instagram" className="w-5 h-5 rounded-xs object-cover shrink-0" />
                                    <span className="font-sans font-bold text-xs text-white">{editingClip.social_handle || "@peakheistclips"}</span>
                                  </div>
                                  <span className="text-[8px] bg-[#0095F6] text-white px-2 py-0.5 rounded-full font-bold">Follow</span>
                                </div>
                                <p className="font-sans text-xs text-neutral-100 font-medium leading-snug">
                                  {editingClip.opening_hook_text || editingClip.opening_hook || editingClip.headline_text || editingClip.visual_headline || editingClip.title}
                                </p>
                                <div className="mt-1 text-[8px] text-neutral-400">
                                  ❤️ 184K • 💬 2,410 • ✈ Share
                                </div>
                              </div>
                            )}

                            {/* YouTube Card */}
                            {(editingClip.card_type === "youtube_comment" || editingClip.card_type === "split_screen_comment") && (
                              <div className="w-full bg-[#00E297] text-black border-2 border-black p-2.5 shadow-xl">
                                <div className="flex items-center justify-between mb-1 pb-1 border-b border-black/20">
                                  <div className="flex items-center gap-1.5">
                                    <img src="/logos/youtube_logo.png" alt="YouTube" className="w-4 h-4 object-contain shrink-0" />
                                    <span className="font-sans text-xs font-bold">{editingClip.social_author || "Peak Heist Clips"}</span>
                                  </div>
                                  <span className="px-1.5 py-0.2 bg-black text-[#D5EB45] font-mono text-[8px] font-bold">
                                    {editingClip.social_badge || "CA$ 14.99 SUPERCHAT"}
                                  </span>
                                </div>
                                <p className="font-sans text-xs font-bold leading-tight">
                                  &ldquo;{editingClip.opening_hook_text || editingClip.opening_hook || editingClip.headline_text || editingClip.visual_headline || editingClip.title}&rdquo;
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {/* 2. INDEPENDENT DRAGGABLE KINETIC SUBTITLES (Always draggable) */}
                        <div
                          style={{
                            top: `${editingClip.subtitle_vertical_position ?? 74}%`,
                            width: "92%",
                            transform: "translate(-50%, 0)",
                          }}
                          className="absolute left-1/2 z-30 transition-all select-none"
                        >
                          {/* Subtitle Drag Handle Bar */}
                          <div
                            onPointerDown={(e) => {
                              try { (e.target as HTMLElement).setPointerCapture(e.pointerId); } catch {}
                              setIsDraggingSubtitle(true);
                            }}
                            onPointerUp={(e) => {
                              try { (e.target as HTMLElement).releasePointerCapture(e.pointerId); } catch {}
                              setIsDraggingSubtitle(false);
                            }}
                            className="flex items-center justify-between px-2 py-0.5 bg-[#00E297] text-black border border-black font-mono text-[9px] font-black cursor-grab active:cursor-grabbing mb-1 shadow-[1px_1px_0px_#111111]"
                            title="Drag up or down to reposition subtitles vertically"
                          >
                            <span className="flex items-center gap-1">
                              <GripVertical className="w-3 h-3 text-black" />
                              <span>[DRAG SUBTITLES Y]</span>
                            </span>
                            <span>Y: {editingClip.subtitle_vertical_position ?? 74}%</span>
                          </div>

                          <div className="flex flex-col items-center justify-center text-center">
                            {editingClip.headline_text && (!editingClip.card_type || editingClip.card_type === "none") && (
                              <div
                                className="inline-block px-2.5 py-0.5 border-2 border-black font-headline font-black uppercase text-xs shadow-[2px_2px_0px_#000] transform -rotate-1 max-w-[240px] mb-1"
                                style={{ backgroundColor: assToHexColor(editingClip.custom_active_color), color: "#000" }}
                              >
                                {editingClip.headline_text}
                              </div>
                            )}
                            <div
                              style={{
                                fontFamily: editingClip.custom_font_name || "Arial Black",
                                color: editingClip.custom_text_color || "#FFFFFF",
                                textTransform: editingClip.custom_all_caps !== false ? "uppercase" : "none",
                              }}
                              className="flex flex-wrap items-center justify-center gap-1 max-w-[260px] drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]"
                            >
                              <span className="font-headline text-base sm:text-lg font-black">
                                THIS
                              </span>
                              <span
                                style={{
                                  color: assToHexColor(editingClip.custom_active_color) || "#FFE600",
                                  backgroundColor: editingClip.subtitle_preset === "mrbeast" ? "#000" : undefined,
                                  textShadow: editingClip.custom_animation === "glow_pulse"
                                    ? `0 0 12px ${assToHexColor(editingClip.custom_active_color) || "#FFE600"}`
                                    : undefined,
                                }}
                                className={`font-headline text-base sm:text-lg font-black px-1.5 rounded-sm transform scale-110 ${
                                  editingClip.custom_animation === "glow_pulse"
                                    ? "animate-pulse"
                                    : (editingClip.custom_animation === "word_pop" || !editingClip.custom_animation)
                                    ? "animate-bounce"
                                    : ""
                                }`}
                              >
                                VIRAL
                              </span>
                              <span className="font-headline text-base sm:text-lg font-black">
                                MOMENT
                              </span>
                            </div>
                            <div className="mt-1 flex items-center gap-1 font-mono text-[8px] text-white bg-black/80 px-2 py-0.5 border border-white/20">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#d5eb45] animate-pulse"></span>
                              <span>ANIMATION: {(editingClip.custom_animation || "WORD POP").toUpperCase()}</span>
                            </div>
                          </div>
                        </div>

                        {/* Bottom Scrim indicator */}
                        <div className="relative z-20 p-2 text-center text-white/40 font-mono text-[9px]">
                          SWIPE UP TO PROGRESS
                        </div>
                      </div>
                    ) : (
                      /* TAB 2: COMPILED REAL MP4 VIDEO PREVIEW */
                      <div className="relative w-full h-full flex flex-col justify-between bg-black">
                        {editingClip.rendered_video_url ? (
                          <div className="relative w-full h-full flex flex-col">
                            <video
                              key={editingClip.rendered_video_url}
                              src={editingClip.rendered_video_url}
                              controls
                              autoPlay
                              loop
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute top-2 left-2 z-20 flex items-center gap-1.5">
                              <span className="px-2 py-0.5 bg-black/85 border border-primary text-[#d5eb45] font-mono text-[9px] font-bold">
                                COMPILED 9:16 MP4
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-white">
                            <div className="w-12 h-12 border-2 border-[#d5eb45] bg-[#d5eb45]/20 flex items-center justify-center mb-3">
                              <Sparkles className="w-6 h-6 text-[#d5eb45]" />
                            </div>
                            <h4 className="font-headline font-bold text-sm uppercase text-white mb-1">
                              No Rendered MP4 Yet
                            </h4>
                            <p className="font-mono text-xs text-neutral-400 mb-4 max-w-xs">
                              Click &ldquo;Apply &amp; Re-Render&rdquo; below to compile your customized card &amp; subtitles into a broadcast 9:16 video.
                            </p>
                            <button
                              type="button"
                              onClick={handleApplyAndReRender}
                              disabled={isModalRendering}
                              className="px-4 py-2 border-2 border-primary bg-[#d5eb45] text-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#111111] hover:bg-white transition-all cursor-pointer"
                            >
                              Render MP4 Now
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Quick-Snap Anchors Under Canvas */}
                  <div className="mt-3 space-y-2 border-t-2 border-primary pt-2.5">
                    {/* Card Positioning Hot-Snaps (if card active) */}
                    {editingClip.card_type && editingClip.card_type !== "none" && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between font-mono text-[10px]">
                          <span className="font-bold text-primary">Card Vertical (Y):</span>
                          <span className="font-bold text-[#d5eb45] bg-black px-1.5 py-0.2">
                            {editingClip.card_vertical_position ?? 18}%
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-1">
                          <button
                            type="button"
                            onClick={() => setEditingClip({ ...editingClip, card_vertical_position: 16 })}
                            className={`py-0.5 border border-primary font-mono text-[8px] font-bold uppercase transition-all cursor-pointer ${
                              (editingClip.card_vertical_position ?? 18) <= 20
                                ? "bg-[#d5eb45] text-primary shadow-[1px_1px_0px_#111111]"
                                : "bg-surface-container hover:bg-surface-container-highest"
                            }`}
                          >
                            Top (16%)
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditingClip({ ...editingClip, card_vertical_position: 28 })}
                            className={`py-0.5 border border-primary font-mono text-[8px] font-bold uppercase transition-all cursor-pointer ${
                              (editingClip.card_vertical_position ?? 18) > 20 && (editingClip.card_vertical_position ?? 18) <= 38
                                ? "bg-[#d5eb45] text-primary shadow-[1px_1px_0px_#111111]"
                                : "bg-surface-container hover:bg-surface-container-highest"
                            }`}
                          >
                            Upper (28%)
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditingClip({ ...editingClip, card_vertical_position: 46 })}
                            className={`py-0.5 border border-primary font-mono text-[8px] font-bold uppercase transition-all cursor-pointer ${
                              (editingClip.card_vertical_position ?? 18) > 38
                                ? "bg-[#d5eb45] text-primary shadow-[1px_1px_0px_#111111]"
                                : "bg-surface-container hover:bg-surface-container-highest"
                            }`}
                          >
                            Center (46%)
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Subtitle Positioning Hot-Snaps */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="font-bold text-primary">Subtitle Vertical (Y):</span>
                        <span className="font-bold text-[#00E297] bg-black px-1.5 py-0.2">
                          {editingClip.subtitle_vertical_position ?? 74}%
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-1">
                        <button
                          type="button"
                          onClick={() => setEditingClip({ ...editingClip, subtitle_vertical_position: 55 })}
                          className={`py-0.5 border border-primary font-mono text-[8px] font-bold uppercase transition-all cursor-pointer ${
                            (editingClip.subtitle_vertical_position ?? 74) <= 62
                              ? "bg-[#00E297] text-black shadow-[1px_1px_0px_#111111]"
                              : "bg-surface-container hover:bg-surface-container-highest"
                          }`}
                        >
                          Upper (55%)
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingClip({ ...editingClip, subtitle_vertical_position: 74 })}
                          className={`py-0.5 border border-primary font-mono text-[8px] font-bold uppercase transition-all cursor-pointer ${
                            (editingClip.subtitle_vertical_position ?? 74) > 62 && (editingClip.subtitle_vertical_position ?? 74) <= 78
                              ? "bg-[#00E297] text-black shadow-[1px_1px_0px_#111111]"
                              : "bg-surface-container hover:bg-surface-container-highest"
                          }`}
                        >
                          Lower Third (74%)
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingClip({ ...editingClip, subtitle_vertical_position: 82 })}
                          className={`py-0.5 border border-primary font-mono text-[8px] font-bold uppercase transition-all cursor-pointer ${
                            (editingClip.subtitle_vertical_position ?? 74) > 78
                              ? "bg-[#00E297] text-black shadow-[1px_1px_0px_#111111]"
                              : "bg-surface-container hover:bg-surface-container-highest"
                          }`}
                        >
                          Bottom Safe (82%)
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Direct Download in Left Column if MP4 is ready */}
                  {editingClip.rendered_video_url && (
                    <div className="mt-3 p-2 bg-surface-container border border-primary flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className="font-mono text-[10px] font-bold text-primary uppercase">MP4 Export Ready</span>
                        <span className="font-mono text-[9px] text-outline">1080×1920 60FPS</span>
                      </div>
                      <a
                        href={editingClip.rendered_video_url}
                        download={`short_${editingClip.clip_id}.mp4`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 border border-primary bg-[#d5eb45] text-primary font-mono text-[10px] uppercase font-bold tracking-wider shadow-[1px_1px_0px_#111111] hover:bg-white transition-all cursor-pointer"
                      >
                        <Download className="w-3 h-3 text-primary" />
                        <span>Download MP4</span>
                      </a>
                    </div>
                  )}
                </div>
              </div>

              {/* RIGHT COLUMN: Architectural Subtitle Archetype & Editing Controls (7 cols) */}
              <div className="lg:col-span-7 flex flex-col gap-4">
                {/* 1. SELECT SOCIAL CARD ARCHETYPE (5 REAL PLATFORMS WITH AUTHENTIC LOGOS) */}
                <div className="p-3.5 bg-surface-container-low border-2 border-primary space-y-2.5 shadow-[2px_2px_0px_#111111]">
                  <div className="flex items-center justify-between pb-1 border-b border-primary/20">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary" />
                      <span className="font-mono text-xs font-bold uppercase tracking-wider text-primary">
                        Hook Card Archetype (5 Real Formats)
                      </span>
                    </div>
                    <span className="font-mono text-[10px] text-outline">[SYNCED WITH RENDER ENGINE]</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                    {/* REDDIT */}
                    <button
                      type="button"
                      onClick={() => setEditingClip({
                        ...editingClip,
                        card_type: "reddit_card",
                        social_author: "r/peakheistclips",
                        social_handle: "u/peakheistclips",
                      })}
                      className={`p-2 border-2 border-primary transition-all flex flex-col items-center gap-1 text-center cursor-pointer ${
                        editingClip.card_type === "reddit_card"
                          ? "bg-surface-container-lowest shadow-[2px_2px_0px_#111111] border-black font-bold"
                          : "bg-surface-container hover:bg-surface-container-highest"
                      }`}
                    >
                      <img src="/logos/reddit_logo.png" alt="Reddit" className="w-5 h-5 rounded-full object-cover" />
                      <span className="font-mono text-[10px]">Reddit</span>
                    </button>

                    {/* X / TWITTER */}
                    <button
                      type="button"
                      onClick={() => setEditingClip({
                        ...editingClip,
                        card_type: "tweet_card",
                        social_author: "Peak Heist Clips",
                        social_handle: "@peakheistclips",
                      })}
                      className={`p-2 border-2 border-primary transition-all flex flex-col items-center gap-1 text-center cursor-pointer ${
                        editingClip.card_type === "tweet_card" || editingClip.card_type === "twitter_card"
                          ? "bg-surface-container-lowest shadow-[2px_2px_0px_#111111] border-black font-bold"
                          : "bg-surface-container hover:bg-surface-container-highest"
                      }`}
                    >
                      <img src="/logos/twitter_verified.png" alt="Twitter" className="w-4 h-4 object-contain" />
                      <span className="font-mono text-[10px]">X / Twitter</span>
                    </button>

                    {/* INSTAGRAM */}
                    <button
                      type="button"
                      onClick={() => setEditingClip({
                        ...editingClip,
                        card_type: "instagram_card",
                        social_handle: "@peakheistclips",
                      })}
                      className={`p-2 border-2 border-primary transition-all flex flex-col items-center gap-1 text-center cursor-pointer ${
                        editingClip.card_type === "instagram_card"
                          ? "bg-surface-container-lowest shadow-[2px_2px_0px_#111111] border-black font-bold"
                          : "bg-surface-container hover:bg-surface-container-highest"
                      }`}
                    >
                      <img src="/logos/instagram_logo.png" alt="Instagram" className="w-5 h-5 rounded-xs object-cover" />
                      <span className="font-mono text-[10px]">Instagram</span>
                    </button>

                    {/* YOUTUBE */}
                    <button
                      type="button"
                      onClick={() => setEditingClip({
                        ...editingClip,
                        card_type: "youtube_comment",
                        social_badge: "CA$ 14.99 SUPERCHAT",
                      })}
                      className={`p-2 border-2 border-primary transition-all flex flex-col items-center gap-1 text-center cursor-pointer ${
                        editingClip.card_type === "youtube_comment" || editingClip.card_type === "split_screen_comment"
                          ? "bg-surface-container-lowest shadow-[2px_2px_0px_#111111] border-black font-bold"
                          : "bg-surface-container hover:bg-surface-container-highest"
                      }`}
                    >
                      <img src="/logos/youtube_logo.png" alt="YouTube" className="w-5 h-5 object-contain" />
                      <span className="font-mono text-[10px]">YouTube</span>
                    </button>

                    {/* NONE */}
                    <button
                      type="button"
                      onClick={() => setEditingClip({
                        ...editingClip,
                        card_type: "none",
                      })}
                      className={`p-2 border-2 border-primary transition-all flex flex-col items-center gap-1 text-center cursor-pointer ${
                        editingClip.card_type === "none" || !editingClip.card_type
                          ? "bg-surface-container-lowest shadow-[2px_2px_0px_#111111] border-black font-bold"
                          : "bg-surface-container hover:bg-surface-container-highest"
                      }`}
                    >
                      <span className="w-5 h-5 rounded-full border border-neutral-400 flex items-center justify-center font-mono text-[10px]">∅</span>
                      <span className="font-mono text-[10px]">Pure Video</span>
                    </button>
                  </div>
                </div>

                {/* 2. SELECT VIDEO LAYOUT MODE (Independent from card!) */}
                <div className="p-3 bg-surface-container-low border-2 border-primary space-y-2 shadow-[2px_2px_0px_#111111]">
                  <div className="flex items-center justify-between pb-1 border-b border-primary/20">
                    <div className="flex items-center gap-2">
                      <Video className="w-4 h-4 text-primary" />
                      <span className="font-mono text-xs font-bold uppercase tracking-wider text-primary">
                        Video Layout Mode
                      </span>
                    </div>
                    <span className="font-mono text-[10px] text-outline">
                      {editingClip.layout_mode === "split_screen" || editingClip.layout_mode === "split_50_50"
                        ? "50:50 Gameplay"
                        : editingClip.layout_mode === "floating" || editingClip.layout_mode === "card"
                        ? "Floating (Minecraft BG)"
                        : editingClip.layout_mode === "fit_ambient_blur"
                        ? "Ambient Blur"
                        : "Full 9:16"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <button
                      type="button"
                      onClick={() => setEditingClip({ ...editingClip, layout_mode: "split_screen" })}
                      className={`p-2 border-2 border-primary transition-all text-center cursor-pointer ${
                        editingClip.layout_mode === "split_screen" || editingClip.layout_mode === "split_50_50"
                          ? "bg-[#d5eb45] text-primary font-bold shadow-[2px_2px_0px_#111111]"
                          : "bg-surface-container hover:bg-surface-container-highest font-mono text-[10px]"
                      }`}
                    >
                      <div className="font-bold font-mono text-[10px]">50:50 Split</div>
                      <div className="text-[9px] text-outline">Gameplay B-Roll</div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingClip({ ...editingClip, layout_mode: "full_9_16" })}
                      className={`p-2 border-2 border-primary transition-all text-center cursor-pointer ${
                        editingClip.layout_mode === "full_9_16"
                          ? "bg-[#d5eb45] text-primary font-bold shadow-[2px_2px_0px_#111111]"
                          : "bg-surface-container hover:bg-surface-container-highest font-mono text-[10px]"
                      }`}
                    >
                      <div className="font-bold font-mono text-[10px]">Full 9:16</div>
                      <div className="text-[9px] text-outline">Speaker Crop</div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingClip({ ...editingClip, layout_mode: "floating", background_id: "minecraft_parkour" })}
                      className={`p-2 border-2 border-primary transition-all text-center cursor-pointer ${
                        editingClip.layout_mode === "floating" || editingClip.layout_mode === "card"
                          ? "bg-[#d5eb45] text-primary font-bold shadow-[2px_2px_0px_#111111]"
                          : "bg-surface-container hover:bg-surface-container-highest font-mono text-[10px]"
                      }`}
                    >
                      <div className="font-bold font-mono text-[10px]">Floating Card</div>
                      <div className="text-[9px] text-outline">Minecraft Blurred</div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingClip({ ...editingClip, layout_mode: "fit_ambient_blur" })}
                      className={`p-2 border-2 border-primary transition-all text-center cursor-pointer ${
                        editingClip.layout_mode === "fit_ambient_blur" || editingClip.layout_mode === "blurred_bg"
                          ? "bg-[#d5eb45] text-primary font-bold shadow-[2px_2px_0px_#111111]"
                          : "bg-surface-container hover:bg-surface-container-highest font-mono text-[10px]"
                      }`}
                    >
                      <div className="font-bold font-mono text-[10px]">Ambient Blur</div>
                      <div className="text-[9px] text-outline">Soft Mirror</div>
                    </button>
                  </div>
                </div>

                {/* 3. DEDICATED POSITIONING & SIZING DIRECTIVES */}
                <div className="p-3.5 bg-surface-container-low border-2 border-primary space-y-3 shadow-[2px_2px_0px_#111111]">
                  <div className="flex items-center justify-between pb-1 border-b border-primary/20">
                    <div className="flex items-center gap-2">
                      <SlidersHorizontal className="w-4 h-4 text-primary" />
                      <span className="font-mono text-xs font-bold uppercase tracking-wider text-primary">
                        Positioning &amp; Sizing Directives
                      </span>
                    </div>
                    <span className="font-mono text-[10px] text-outline">[INDEPENDENT Y &amp; SIZE]</span>
                  </div>

                  <div className={`grid grid-cols-1 ${editingClip.card_type && editingClip.card_type !== "none" ? "sm:grid-cols-3" : "sm:grid-cols-1"} gap-3`}>
                    {/* Card Y Position (only if card active) */}
                    {editingClip.card_type && editingClip.card_type !== "none" && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between font-mono text-[10px]">
                          <span className="font-bold text-primary">Card Vertical (Y):</span>
                          <span className="font-bold text-[#d5eb45] bg-black px-1.5 py-0.2">
                            {editingClip.card_vertical_position ?? 18}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min={10}
                          max={85}
                          value={editingClip.card_vertical_position ?? 18}
                          onChange={(e) =>
                            setEditingClip({
                              ...editingClip,
                              card_vertical_position: parseInt(e.target.value, 10),
                            })
                          }
                          className="w-full accent-[#d5eb45] cursor-pointer"
                        />
                        <div className="flex justify-between font-mono text-[8px] text-outline">
                          <span>Top 18%</span>
                          <span>Center 48%</span>
                          <span>Low 75%</span>
                        </div>
                      </div>
                    )}

                    {/* Card Size / Width (only if card active) */}
                    {editingClip.card_type && editingClip.card_type !== "none" && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between font-mono text-[10px]">
                          <span className="font-bold text-primary">Card Width Scale:</span>
                          <span className="font-bold text-[#d5eb45] bg-black px-1.5 py-0.2">
                            {editingClip.card_width_percent ?? 92}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min={75}
                          max={98}
                          value={editingClip.card_width_percent ?? 92}
                          onChange={(e) =>
                            setEditingClip({
                              ...editingClip,
                              card_width_percent: parseInt(e.target.value, 10),
                            })
                          }
                          className="w-full accent-[#d5eb45] cursor-pointer"
                        />
                        <div className="flex justify-between font-mono text-[8px] text-outline">
                          <span>75% Slim</span>
                          <span>92% Default</span>
                          <span>98% Edge</span>
                        </div>
                      </div>
                    )}

                    {/* Subtitle Vertical Position */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="font-bold text-primary">Subtitle Anchor (Y):</span>
                        <span className="font-bold text-[#00E297] bg-black px-1.5 py-0.2">
                          {editingClip.subtitle_vertical_position ?? 74}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min={25}
                        max={88}
                        value={editingClip.subtitle_vertical_position ?? 74}
                        onChange={(e) =>
                          setEditingClip({
                            ...editingClip,
                            subtitle_vertical_position: parseInt(e.target.value, 10),
                          })
                        }
                        className="w-full accent-[#00E297] cursor-pointer"
                      />
                      <div className="flex justify-between font-mono text-[8px] text-outline">
                        <span>Top 30%</span>
                        <span>Center 55%</span>
                        <span>Bottom 74%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2. ACCENT COLOR PALETTE, REST-OF-TEXT & TYPOGRAPHY */}
                <div className="p-4 bg-surface-container-low border-2 border-primary space-y-3.5 shadow-[2px_2px_0px_#111111]">
                  <div className="flex items-center justify-between pb-1 border-b border-primary/20">
                    <span className="font-mono text-xs font-bold uppercase tracking-wider text-primary">
                      Caption Colors, Typography &amp; Motion
                    </span>
                    <span className="font-mono text-[10px] text-outline">[CUSTOMIZABLE]</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    {/* Active Highlight Color */}
                    <div>
                      <label className="font-mono text-[10px] font-bold text-primary uppercase block mb-1">
                        Active Highlight Color:
                      </label>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {[
                          { name: "Yellow", hex: "#FFE600" },
                          { name: "Lime", hex: "#D5EB45" },
                          { name: "Mint", hex: "#00E297" },
                          { name: "Cyan", hex: "#00FFFF" },
                          { name: "Pink", hex: "#FF2A85" },
                          { name: "White", hex: "#FFFFFF" },
                        ].map((c) => {
                          const isSel = (editingClip.custom_active_color || "#FFE600") === c.hex;
                          return (
                            <button
                              key={c.hex}
                              type="button"
                              title={c.name}
                              onClick={() => setEditingClip({ ...editingClip, custom_active_color: c.hex })}
                              className={`w-6 h-6 border-2 border-black transition-all cursor-pointer ${
                                isSel ? "ring-2 ring-primary scale-110 shadow-xs" : "hover:scale-105"
                              }`}
                              style={{ backgroundColor: c.hex }}
                            />
                          );
                        })}
                        <label className="w-6 h-6 border-2 border-black bg-surface-container flex items-center justify-center cursor-pointer hover:bg-white" title="Custom color">
                          <input
                            type="color"
                            value={editingClip.custom_active_color || "#FFE600"}
                            onChange={(e) => setEditingClip({ ...editingClip, custom_active_color: e.target.value })}
                            className="opacity-0 absolute w-0 h-0"
                          />
                          <Palette className="w-3 h-3 text-primary" />
                        </label>
                      </div>
                    </div>

                    {/* Rest of Caption Text Color */}
                    <div>
                      <label className="font-mono text-[10px] font-bold text-primary uppercase block mb-1">
                        Rest of Caption Text Color:
                      </label>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {[
                          { name: "White", hex: "#FFFFFF" },
                          { name: "Snow", hex: "#F8FAFC" },
                          { name: "Silver", hex: "#E2E8F0" },
                          { name: "Cream", hex: "#FAF7F2" },
                          { name: "Dark", hex: "#111111" },
                        ].map((c) => {
                          const isSel = (editingClip.custom_text_color || "#FFFFFF") === c.hex;
                          return (
                            <button
                              key={c.hex}
                              type="button"
                              title={c.name}
                              onClick={() => setEditingClip({ ...editingClip, custom_text_color: c.hex })}
                              className={`w-6 h-6 border-2 border-black transition-all cursor-pointer ${
                                isSel ? "ring-2 ring-primary scale-110 shadow-xs" : "hover:scale-105"
                              }`}
                              style={{ backgroundColor: c.hex }}
                            />
                          );
                        })}
                        <label className="w-6 h-6 border-2 border-black bg-surface-container flex items-center justify-center cursor-pointer hover:bg-white" title="Custom color">
                          <input
                            type="color"
                            value={editingClip.custom_text_color || "#FFFFFF"}
                            onChange={(e) => setEditingClip({ ...editingClip, custom_text_color: e.target.value })}
                            className="opacity-0 absolute w-0 h-0"
                          />
                          <Palette className="w-3 h-3 text-primary" />
                        </label>
                      </div>
                    </div>

                    {/* Font Family Dropdown */}
                    <div>
                      <label className="font-mono text-[10px] font-bold text-primary uppercase block mb-1">
                        Font Family:
                      </label>
                      <div className="relative">
                        <select
                          value={editingClip.custom_font_name || "Arial Black"}
                          onChange={(e) => setEditingClip({ ...editingClip, custom_font_name: e.target.value })}
                          className="w-full appearance-none px-3 py-2 pr-9 border-2 border-primary bg-surface-container-lowest font-mono text-xs font-bold uppercase tracking-wider text-primary shadow-[2px_2px_0px_#111111] hover:bg-surface-container focus:outline-none cursor-pointer"
                        >
                          <option value="Arial Black">Arial Black (Hormozi / Bold Punch)</option>
                          <option value="Impact">Impact (MrBeast / Loud Comic)</option>
                          <option value="Space Grotesk">Space Grotesk (Editorial / Modern)</option>
                          <option value="Inter">Inter (Clean Sans)</option>
                          <option value="Montserrat">Montserrat (Geometric Bold)</option>
                          <option value="Georgia">Georgia (Cinematic Serif)</option>
                          <option value="Courier New">Courier New (Terminal Hacker)</option>
                          <option value="Trebuchet MS">Trebuchet MS (Dynamic Casual)</option>
                        </select>
                        <div className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none w-5 h-5 border border-primary bg-[#d5eb45] flex items-center justify-center shadow-[1px_1px_0px_#111111]">
                          <ChevronDown className="w-3 h-3 text-primary stroke-[2.5]" />
                        </div>
                      </div>
                    </div>

                    {/* Motion Animation Style */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="font-mono text-[10px] font-bold text-primary uppercase">
                          Motion Animation:
                        </label>
                        <button
                          type="button"
                          onClick={() => setEditingClip({ ...editingClip, custom_all_caps: !(editingClip.custom_all_caps !== false) })}
                          className={`px-1.5 py-0.2 border border-primary font-mono text-[9px] font-bold uppercase transition-all cursor-pointer ${
                            editingClip.custom_all_caps !== false ? "bg-[#d5eb45] text-primary" : "bg-white text-neutral-600"
                          }`}
                        >
                          {editingClip.custom_all_caps !== false ? "CAPS ON" : "Caps Off"}
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-1">
                        {[
                          { id: "word_pop", label: "💥 Pop" },
                          { id: "glow_pulse", label: "✨ Glow" },
                          { id: "fade_in", label: "🎬 Fade" },
                          { id: "slide_up", label: "⬆️ Slide" },
                          { id: "karaoke", label: "🎤 Karaoke" },
                        ].map((a) => {
                          const isSel = (editingClip.custom_animation || "word_pop") === a.id;
                          return (
                            <button
                              key={a.id}
                              type="button"
                              onClick={() => setEditingClip({ ...editingClip, custom_animation: a.id })}
                              className={`py-1 border border-primary font-mono text-[9px] font-bold uppercase transition-all cursor-pointer truncate ${
                                isSel
                                  ? "bg-primary text-on-primary shadow-[1px_1px_0px_#111111]"
                                  : "bg-surface-container hover:bg-surface-container-highest"
                              }`}
                            >
                              {a.label}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. HEADLINE & SPOKEN HOOK DIRECTIVES */}
                <div className="p-4 bg-surface-container-low border-2 border-primary space-y-3 shadow-[2px_2px_0px_#111111]">
                  <div className="flex items-center justify-between pb-1 border-b border-primary/20">
                    <span className="font-mono text-xs font-bold uppercase tracking-wider text-primary">
                      Hook Directives &amp; Social Copy
                    </span>
                    <span className="font-mono text-[10px] text-outline">[EDITABLE]</span>
                  </div>

                  <div>
                    <label className="font-mono text-[10px] font-bold text-primary uppercase block mb-1">
                      Visual Headline / Card Hook:
                    </label>
                    <input
                      type="text"
                      value={editingClip.headline_text || editingClip.visual_headline || editingClip.title}
                      onChange={(e) =>
                        setEditingClip({ ...editingClip, headline_text: e.target.value })
                      }
                      className="w-full p-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
                      placeholder="e.g. STOP TRADING YOUR TIME!"
                    />
                  </div>

                  <div>
                    <label className="font-mono text-[10px] font-bold text-primary uppercase block mb-1">
                      Social Card Author, Handle &amp; Badge:
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <input
                        type="text"
                        value={editingClip.social_author || "Peak Heist Clips"}
                        onChange={(e) =>
                          setEditingClip({ ...editingClip, social_author: e.target.value })
                        }
                        className="w-full p-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none"
                        placeholder="Author name"
                      />
                      <input
                        type="text"
                        value={editingClip.social_handle || "@peakheistclips"}
                        onChange={(e) =>
                          setEditingClip({ ...editingClip, social_handle: e.target.value })
                        }
                        className="w-full p-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none"
                        placeholder="Handle e.g. @peakheistclips"
                      />
                      <input
                        type="text"
                        value={editingClip.social_badge || "verified"}
                        onChange={(e) =>
                          setEditingClip({ ...editingClip, social_badge: e.target.value })
                        }
                        className="w-full p-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary focus:outline-none"
                        placeholder="Badge / Superchat amount"
                      />
                    </div>
                  </div>
                </div>

                {/* Status Message Banner */}
                {modalStatusMsg && (
                  <div className="p-3 bg-[#d5eb45] border-2 border-primary shadow-[2px_2px_0px_#111111] font-mono text-xs font-bold text-primary flex items-center justify-between animate-in fade-in">
                    <span>{modalStatusMsg}</span>
                    <button
                      onClick={() => setModalStatusMsg(null)}
                      className="p-1 hover:bg-surface-container transition-colors cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5 text-primary" />
                    </button>
                  </div>
                )}

                {/* Footer Actions */}
                <div className="pt-2 flex items-center justify-between gap-3 mt-auto border-t-2 border-primary/20">
                  <span className="font-mono text-[10px] text-outline">
                    Work auto-saved to clip state &amp; storage.
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      className="px-4 py-2 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container font-mono text-xs uppercase font-bold text-primary shadow-[1px_1px_0px_#111111] transition-all cursor-pointer"
                    >
                      Save &amp; Close
                    </button>
                    <button
                      type="button"
                      onClick={handleApplyAndReRender}
                      disabled={isModalRendering}
                      className="px-6 py-2.5 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[3px_3px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary hover:shadow-[1px_1px_0px_#111111] disabled:opacity-50 transition-all cursor-pointer flex items-center gap-2"
                    >
                      {isModalRendering ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#d5eb45]" />
                          <span>Re-Rendering 9:16 MP4...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5 text-[#d5eb45]" />
                          <span>Apply &amp; Re-Render ⚡</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Phase 2: Channel Connection & Scheduling Modals */}
      <ChannelConnectModal
        isOpen={isChannelModalOpen}
        onClose={() => setIsChannelModalOpen(false)}
        onChannelConnected={() => {
          fetchChannelStatus();
        }}
        onSelectVideoForClipping={(url) => {
          setYoutubeUrl(url);
          setActiveMainView("studio");
          setTimeout(() => {
            const processBtn = document.getElementById("start-processing-btn");
            if (processBtn) processBtn.click();
          }, 200);
        }}
        currentChannel={currentChannel}
      />

      <ScheduleModal
        isOpen={Boolean(schedulingClip)}
        onClose={() => setSchedulingClip(null)}
        clip={schedulingClip}
        currentChannel={currentChannel}
        onScheduled={(job) => {
          alert(`Successfully scheduled Short: "${job.title}"!`);
          setActiveMainView("scheduler");
        }}
        onMetadataUpdate={(updatedFields) => {
          if (!schedulingClip) return;
          const updatedClips = clips.map((c) =>
            c.clip_id === schedulingClip.clip_id
              ? {
                  ...c,
                  title: updatedFields.title,
                  description: updatedFields.description,
                  tags: updatedFields.tags,
                  title_alternatives: updatedFields.title_alternatives || c.title_alternatives,
                }
              : c
          );
          persistClipsState(updatedClips);
          setSchedulingClip((prev) =>
            prev
              ? {
                  ...prev,
                  title: updatedFields.title,
                  description: updatedFields.description,
                  tags: updatedFields.tags,
                  title_alternatives: updatedFields.title_alternatives || prev.title_alternatives,
                }
              : null
          );
        }}
      />

      <BulkPublishModal
        isOpen={isBulkPublishModalOpen}
        onClose={() => setIsBulkPublishModalOpen(false)}
        clips={clips}
        renderedClips={renderedClips}
        currentChannel={currentChannel}
        onSuccess={() => {
          fetchChannelStatus();
          setActiveMainView("scheduler");
        }}
      />
    </div>
  );
};
