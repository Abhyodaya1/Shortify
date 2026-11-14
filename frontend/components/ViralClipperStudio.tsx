"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Scissors,
  Flame,
  CheckCircle2,
  AlertTriangle,
  Play,
  Clock,
  ArrowRight,
  TrendingUp,
  FileText,
} from "lucide-react";
import { Timeline } from "../types/timeline";

interface ViralClipperStudioProps {
  onLoadTimeline: (timeline: Timeline, jobId: string) => void;
}

const SAMPLE_TRANSCRIPT = `1
00:00:00,000 --> 00:00:03,500
Um, basically today we are going to look at YouTube hooks.

2
00:00:05,000 --> 00:00:10,200
You are losing 14 hours every single week editing clips manually before you discover this AI tool.

3
00:00:11,500 --> 00:00:17,800
Here is the exact mechanism that saves your channel from dying on the 0:30 retention cliff.

4
00:00:18,200 --> 00:00:24,500
We tested this across 50 videos and the completion rate jumped by 42 percent immediately.

5
00:00:25,000 --> 00:00:30,000
So stop doing it by hand and let the autonomous pipeline assemble your vertical compositions.`;

export const ViralClipperStudio: React.FC<ViralClipperStudioProps> = ({ onLoadTimeline }) => {
  const [transcript, setTranscript] = useState(SAMPLE_TRANSCRIPT);
  const [customHook, setCustomHook] = useState("Stop editing videos manually in 2026 before you lose 40 hours a week");
  const [hookScoreResult, setHookScoreResult] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isScoringHook, setIsScoringHook] = useState(false);

  // Score arbitrary hook in real-time
  const handleScoreHook = async () => {
    if (!customHook.trim()) return;
    setIsScoringHook(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/viral/score-hook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hook_text: customHook }),
      });
      if (res.ok) {
        const data = await res.json();
        setHookScoreResult(data);
      }
    } catch (e: any) {
      alert(`Scoring error: ${e.message}`);
    } finally {
      setIsScoringHook(false);
    }
  };

  // Run full transcript dead-air and candidate extraction
  const handleAnalyzeTranscript = async () => {
    if (!transcript.trim()) return;
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/viral/analyze-transcript", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript_text: transcript, target_platform: "shorts" }),
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysisResult(data);
      }
    } catch (e: any) {
      alert(`Analysis error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Load candidate into Workstation
  const handleLoadCandidate = async (candidate: any) => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/viral/create-short", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_data: candidate,
          aspect_ratio: "9:16",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        onLoadTimeline(data.timeline, data.job_id);
      }
    } catch (e: any) {
      alert(`Creation error: ${e.message}`);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col gap-8 pb-12">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold">
          <Flame className="w-3.5 h-3.5" />
          Powered by YouTube Agent Skill & 21 Hook Formulas
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-100 font-serif">
          Viral Shorts & Hook Engine
        </h2>
        <p className="text-sm text-neutral-400 max-w-xl mx-auto">
          Cuts dead-air from your transcript, generates hooks against 21 proven formulas, scores retention
          resistance, and creates 9:16 vertical cuts with kinetic typography.
        </p>
      </div>

      {/* Real-time Hook Score Tester Card */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-lg flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-neutral-200">
              Instant Hook Scorer (Weakest-Link Panel)
            </h3>
          </div>
          <span className="text-xs text-neutral-500 font-mono">Formula Classifier</span>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={customHook}
            onChange={(e) => setCustomHook(e.target.value)}
            placeholder="Type your opening line to score..."
            className="flex-1 bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-2.5 text-xs text-neutral-200 placeholder:text-neutral-500 focus:outline-none focus:border-amber-500"
          />
          <button
            onClick={handleScoreHook}
            disabled={isScoringHook}
            className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-neutral-950 font-bold text-xs transition-colors flex items-center gap-1.5"
          >
            {isScoringHook ? "Scoring..." : "Score Hook"}
          </button>
        </div>

        {hookScoreResult && (
          <div className="bg-neutral-950 border border-neutral-800/80 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-black ${
                    hookScoreResult.verdict === "STRONG"
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : hookScoreResult.verdict === "WORKABLE"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                  }`}
                >
                  {hookScoreResult.verdict} ({hookScoreResult.overall_score}/100)
                </span>
                <span className="text-xs font-semibold text-neutral-200">
                  Formula: {hookScoreResult.formula_name}
                </span>
              </div>
              <p className="text-[11px] text-neutral-400 italic">
                Shape: "{hookScoreResult.formula_shape}"
              </p>
              <p className="text-[11px] text-rose-400 mt-1">
                Weakest Link: {hookScoreResult.weakest}
              </p>
            </div>

            {/* Metric Bars */}
            <div className="grid grid-cols-5 gap-2 text-center w-full sm:w-auto">
              {Object.entries(hookScoreResult.metrics).map(([key, val]: [string, any]) => (
                <div key={key} className="flex flex-col items-center bg-neutral-900 px-2 py-1.5 rounded-lg border border-neutral-800">
                  <span className="text-[9px] uppercase tracking-wider text-neutral-400">
                    {key.slice(0, 4)}
                  </span>
                  <span className="text-xs font-mono font-bold text-neutral-200 mt-0.5">
                    {val}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Transcript to Viral Shorts Card */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Scissors className="w-4 h-4 text-rose-400" />
            <h3 className="text-sm font-semibold text-neutral-200">
              Transcript Input (SRT / VTT / Text)
            </h3>
          </div>
          <span className="text-xs text-neutral-400">Dead-Air Auto Removal & Viral Selection</span>
        </div>

        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          rows={7}
          placeholder="Paste timestamped transcript (SRT, VTT, or plain text)..."
          className="w-full bg-neutral-950 border border-neutral-800 rounded-xl p-3.5 text-xs text-neutral-300 font-mono focus:outline-none focus:border-rose-500 resize-none leading-relaxed"
        />

        <div className="flex justify-end">
          <button
            onClick={handleAnalyzeTranscript}
            disabled={isLoading}
            className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-colors flex items-center gap-2 shadow-lg disabled:opacity-50"
          >
            {isLoading ? <Sparkles className="w-4 h-4 animate-spin" /> : <Flame className="w-4 h-4" />}
            {isLoading ? "Analyzing Retention & Hooks..." : "Extract Viral Shorts & Remove Dead Air"}
          </button>
        </div>

        {/* Results Stream */}
        {analysisResult && (
          <div className="mt-4 flex flex-col gap-6 border-t border-neutral-800 pt-6 animate-in fade-in">
            {/* Dead Air Report */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-neutral-950 p-3 rounded-xl border border-neutral-800 flex flex-col">
                <span className="text-[10px] text-neutral-500 uppercase font-mono">Total Cuts</span>
                <span className="text-lg font-bold text-neutral-200">
                  {analysisResult.dead_air_analysis.total_cuts}
                </span>
              </div>
              <div className="bg-neutral-950 p-3 rounded-xl border border-neutral-800 flex flex-col">
                <span className="text-[10px] text-neutral-500 uppercase font-mono">Time Saved</span>
                <span className="text-lg font-bold text-emerald-400">
                  -{analysisResult.dead_air_analysis.time_saved_sec}s
                </span>
              </div>
              <div className="bg-neutral-950 p-3 rounded-xl border border-neutral-800 flex flex-col">
                <span className="text-[10px] text-neutral-500 uppercase font-mono">Tightened Take</span>
                <span className="text-lg font-bold text-neutral-200">
                  {analysisResult.dead_air_analysis.tightened_duration_sec}s
                </span>
              </div>
              <div className="bg-neutral-950 p-3 rounded-xl border border-neutral-800 flex flex-col">
                <span className="text-[10px] text-neutral-500 uppercase font-mono">Viral Candidates</span>
                <span className="text-lg font-bold text-rose-400">
                  {analysisResult.top_candidates.length}
                </span>
              </div>
            </div>

            {/* Candidates List */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-neutral-300 uppercase tracking-wider">
                Ranked Viral Shorts Candidates
              </h4>
              {analysisResult.top_candidates.map((cand: any, idx: number) => (
                <div
                  key={cand.candidate_id}
                  className="bg-neutral-950 border border-neutral-800 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:border-neutral-700 transition-colors"
                >
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-neutral-800 text-neutral-300 text-[10px] flex items-center justify-center font-bold">
                        #{idx + 1}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[11px] font-bold">
                        Virality: {cand.best_hook.overall_score}/100
                      </span>
                      <span className="text-xs text-neutral-400 font-mono">
                        {cand.duration_sec}s duration ({cand.start_sec}s → {cand.end_sec}s)
                      </span>
                    </div>

                    <div className="space-y-1">
                      <p className="text-xs font-bold text-amber-300">
                        Hook ({cand.best_hook.formula_name}): "{cand.best_hook.hook}"
                      </p>
                      <p className="text-[11px] text-neutral-400 line-clamp-2">
                        Transcript: "{cand.spoken_text}"
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleLoadCandidate(cand)}
                    className="px-4 py-2 rounded-xl bg-neutral-100 hover:bg-white text-neutral-950 text-xs font-bold transition-all shadow-md flex items-center gap-1.5 whitespace-nowrap"
                  >
                    Open in 9:16 Workstation
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

