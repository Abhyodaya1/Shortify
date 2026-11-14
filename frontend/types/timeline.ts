export type TrackType = "video" | "audio" | "caption" | "graphics" | "overlay";

export interface ClipTransform {
  x: number;
  y: number;
  scale_x: number;
  scale_y: number;
  rotation: number;
  opacity: number;
}

export interface Clip {
  clip_id: string;
  asset_id?: string | null;
  start_time_ms: number;
  duration_ms: number;
  source_in_ms?: number;
  source_out_ms?: number | null;
  volume?: number;
  playback_rate?: number;
  transform?: ClipTransform;
  text_content?: string | null;
  style_props?: Record<string, any>;
}

export interface Track {
  track_id: string;
  name: string;
  track_type: TrackType;
  order: number;
  muted?: boolean;
  locked?: boolean;
  clips: Clip[];
}

export interface Timeline {
  timeline_id: string;
  project_id: string;
  title: string;
  fps: number;
  width: number;
  height: number;
  tracks: Track[];
}

export interface Annotation {
  id: string;
  timestamp_ms: number;
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  note?: string;
  color?: string;
}

