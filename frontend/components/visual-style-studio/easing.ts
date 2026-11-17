/**
 * Shared Deterministic Easing & Animation Timing Engine
 * Provides mathematical parity with backend/app/services/easing.py
 */

export type EasingType =
  | "linear"
  | "ease_in_quad"
  | "ease_out_quad"
  | "ease_in_out_quad"
  | "ease_in_cubic"
  | "ease_out_cubic"
  | "ease_in_out_cubic"
  | "ease_out_back"
  | "ease_out_elastic"
  | "ease_out_bounce"
  | "smoothstep"
  | "slam_in";

export interface AnimationPhaseResult {
  phase: "before" | "enter" | "hold" | "exit" | "after";
  progress: number;       // Raw progress within current phase [0.0, 1.0]
  easedProgress: number;  // Eased progress within current phase [0.0, 1.0]
  opacity: number;        // Opacity multiplier [0.0, 1.0]
  scale: number;          // Scale factor (e.g. 1.0 = normal, 1.25 = punch)
  translateY: number;     // Vertical translation offset
  isVisible: boolean;     // Whether element should be drawn
}

export function evaluateEasing(type: EasingType | string, t: number): number {
  const clampedT = Math.max(0.0, Math.min(1.0, t));

  switch (type) {
    case "linear":
      return clampedT;

    case "ease_in_quad":
      return clampedT * clampedT;

    case "ease_out_quad":
      return clampedT * (2.0 - clampedT);

    case "ease_in_out_quad":
      return clampedT < 0.5
        ? 2.0 * clampedT * clampedT
        : -1.0 + (4.0 - 2.0 * clampedT) * clampedT;

    case "ease_in_cubic":
      return clampedT * clampedT * clampedT;

    case "ease_out_cubic": {
      const f = clampedT - 1.0;
      return f * f * f + 1.0;
    }

    case "ease_in_out_cubic":
      return clampedT < 0.5
        ? 4.0 * clampedT * clampedT * clampedT
        : (clampedT - 1.0) * (2.0 * clampedT - 2.0) * (2.0 * clampedT - 2.0) + 1.0;

    case "ease_out_back": {
      const c1 = 1.70158;
      const c3 = c1 + 1.0;
      const f = clampedT - 1.0;
      return 1.0 + c3 * (f * f * f) + c1 * (f * f);
    }

    case "ease_out_elastic": {
      if (clampedT === 0.0) return 0.0;
      if (clampedT === 1.0) return 1.0;
      const p = 0.3;
      const s = p / 4.0;
      return Math.pow(2.0, -10.0 * clampedT) * Math.sin(((clampedT - s) * (2.0 * Math.PI)) / p) + 1.0;
    }

    case "ease_out_bounce": {
      let x = clampedT;
      const n1 = 7.5625;
      const d1 = 2.75;
      if (x < 1.0 / d1) {
        return n1 * x * x;
      } else if (x < 2.0 / d1) {
        x -= 1.5 / d1;
        return n1 * x * x + 0.75;
      } else if (x < 2.5 / d1) {
        x -= 2.25 / d1;
        return n1 * x * x + 0.9375;
      } else {
        x -= 2.625 / d1;
        return n1 * x * x + 0.984375;
      }
    }

    case "smoothstep":
      return clampedT * clampedT * (3.0 - 2.0 * clampedT);

    case "slam_in": {
      // Fast hard impact with brief settle overshoot
      if (clampedT < 0.7) {
        // Hard drop from 0.0 to 1.15
        const sub = clampedT / 0.7;
        return sub * sub * 1.15;
      } else {
        // Settle from 1.15 back to 1.0
        const sub = (clampedT - 0.7) / 0.3;
        return 1.15 - 0.15 * Math.sin((sub * Math.PI) / 2.0);
      }
    }

    default:
      return clampedT;
  }
}

/**
 * Three-phase animation calculator: Enter -> Hold -> Exit
 */
export function computeAnimationPhase(
  currentTimeSec: number,
  startTimeSec: number,
  durationSec: number,
  enterDurationSec: number = 0.35,
  exitDurationSec: number = 0.3,
  enterEasing: EasingType | string = "ease_out_back",
  exitEasing: EasingType | string = "ease_in_cubic"
): AnimationPhaseResult {
  const endTimeSec = startTimeSec + durationSec;

  if (currentTimeSec < startTimeSec) {
    return {
      phase: "before",
      progress: 0.0,
      easedProgress: 0.0,
      opacity: 0.0,
      scale: 0.0,
      translateY: 0.0,
      isVisible: false,
    };
  }

  if (currentTimeSec >= endTimeSec) {
    return {
      phase: "after",
      progress: 1.0,
      easedProgress: 1.0,
      opacity: 0.0,
      scale: 1.0,
      translateY: 0.0,
      isVisible: false,
    };
  }

  const elapsed = currentTimeSec - startTimeSec;
  const clampedEnterDur = Math.max(0.01, Math.min(enterDurationSec, durationSec * 0.45));
  const clampedExitDur = Math.max(0.01, Math.min(exitDurationSec, durationSec * 0.45));
  const holdStartSec = clampedEnterDur;
  const exitStartSec = durationSec - clampedExitDur;

  // Phase 1: Enter
  if (elapsed < holdStartSec) {
    const rawProgress = elapsed / clampedEnterDur;
    const eased = evaluateEasing(enterEasing, rawProgress);
    return {
      phase: "enter",
      progress: rawProgress,
      easedProgress: eased,
      opacity: Math.min(1.0, rawProgress * 2.0),
      scale: 0.7 + 0.3 * eased,
      translateY: (1.0 - eased) * 40.0,
      isVisible: true,
    };
  }

  // Phase 3: Exit
  if (elapsed >= exitStartSec) {
    const exitElapsed = elapsed - exitStartSec;
    const rawProgress = exitElapsed / clampedExitDur;
    const eased = evaluateEasing(exitEasing, rawProgress);
    return {
      phase: "exit",
      progress: rawProgress,
      easedProgress: eased,
      opacity: Math.max(0.0, 1.0 - eased),
      scale: 1.0 - 0.15 * eased,
      translateY: -eased * 30.0,
      isVisible: true,
    };
  }

  // Phase 2: Hold
  const holdDuration = exitStartSec - holdStartSec;
  const holdElapsed = elapsed - holdStartSec;
  const rawProgress = holdDuration > 0 ? holdElapsed / holdDuration : 1.0;

  return {
    phase: "hold",
    progress: rawProgress,
    easedProgress: 1.0,
    opacity: 1.0,
    scale: 1.0,
    translateY: 0.0,
    isVisible: true,
  };
}
