"use client";

import React, { useState } from "react";
import {
  Send,
  Sparkles,
  Download,
  FileCode,
  FileText,
  History,
  CheckCircle2,
  RefreshCw,
  Coins,
  ChevronDown,
} from "lucide-react";
import { Timeline } from "../types/timeline";

interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  text: string;
  diffSummary?: string;
  timestamp: string;
}

interface ConversationalSidebarProps {
  jobId: string | null;
  timeline: Timeline | null;
  onSendFollowup: (instruction: string) => Promise<void>;
  isProcessing?: boolean;
}

export const ConversationalSidebar: React.FC<ConversationalSidebarProps> = ({
  jobId,
  timeline,
  onSendFollowup,
  isProcessing = false,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-1",
      sender: "agent",
      text: "I've assembled the multicam sequence synchronized to the speaker audio, trimmed dead air, and added dynamic animated captions.",
      timestamp: "Just now",
    },
  ]);
  const [inputVal, setInputVal] = useState("");
  const [exportLoading, setExportLoading] = useState<string | null>(null);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputVal;
    if (!text.trim() || !jobId) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputVal("");

    try {
      await onSendFollowup(text);
      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: "agent",
        text: `Applied revision: "${text}". Timeline updated with surgical patch.`,
        diffSummary: "Updated sequence cut and transforms without full regeneration.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: "agent",
        text: `Error updating timeline: ${err.message || "Failed to process revision"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  const handleExport = async (format: "remotion" | "fcpxml") => {
    if (!jobId) return;
    setExportLoading(format);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/videos/${jobId}/export/${format}`);
      if (!res.ok) throw new Error("Export failed");
      const data = await res.json();
      
      // Trigger download in browser
      const element = document.createElement("a");
      const file = new Blob([data.content], { type: "text/plain" });
      element.href = URL.createObjectURL(file);
      element.download = format === "remotion" ? "Composition.tsx" : "Timeline_Export.xml";
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    } catch (e: any) {
      alert(`Export error: ${e.message}`);
    } finally {
      setExportLoading(null);
    }
  };

  const QUICK_PROMPTS = [
    "Trim intro for snappier pacing",
    "Change captions to bright yellow",
    "Make captions larger",
    "Mute audio track",
  ];

  return (
    <div className="w-full h-full flex flex-col bg-neutral-950 border border-neutral-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Top Header */}
      <div className="p-4 bg-neutral-900 border-b border-neutral-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-rose-500" />
          <h2 className="text-sm font-semibold text-neutral-100">AI Video Co-Director</h2>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-neutral-800 text-neutral-300 text-xs font-mono">
          <Coins className="w-3.5 h-3.5 text-amber-400" />
          <span>1,000 credits</span>
        </div>
      </div>

      {/* Export / Roundtrip Tool Header */}
      <div className="px-4 py-2 bg-neutral-900/60 border-b border-neutral-800 flex items-center justify-between text-xs">
        <span className="text-neutral-400 font-medium">Roundtrip Export:</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport("remotion")}
            disabled={!jobId || exportLoading !== null}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-200 transition-colors disabled:opacity-50"
            title="Download Remotion React TSX Composition"
          >
            <FileCode className="w-3.5 h-3.5 text-cyan-400" />
            {exportLoading === "remotion" ? "Exporting..." : "Remotion (.tsx)"}
          </button>
          <button
            onClick={() => handleExport("fcpxml")}
            disabled={!jobId || exportLoading !== null}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-200 transition-colors disabled:opacity-50"
            title="Download Premiere Pro / DaVinci Resolve FCPXML"
          >
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            {exportLoading === "fcpxml" ? "Exporting..." : "Premiere (.xml)"}
          </button>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${
              m.sender === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 leading-relaxed ${
                m.sender === "user"
                  ? "bg-rose-600 text-white"
                  : "bg-neutral-900 border border-neutral-800 text-neutral-200"
              }`}
            >
              <p>{m.text}</p>
              {m.diffSummary && (
                <div className="mt-2 pt-2 border-t border-neutral-800/80 flex items-center gap-1.5 text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{m.diffSummary}</span>
                </div>
              )}
            </div>
            <span className="text-[10px] text-neutral-500 mt-1 px-1">{m.timestamp}</span>
          </div>
        ))}

        {isProcessing && (
          <div className="flex items-center gap-2 text-neutral-400 italic">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-rose-500" />
            <span>AI Co-Director is patching timeline...</span>
          </div>
        )}
      </div>

      {/* Quick suggestions */}
      <div className="px-4 py-2 border-t border-neutral-800 bg-neutral-950/60 flex items-center gap-1.5 overflow-x-auto text-[11px] no-scrollbar">
        {QUICK_PROMPTS.map((promptText, i) => (
          <button
            key={i}
            onClick={() => handleSend(promptText)}
            disabled={!jobId || isProcessing}
            className="whitespace-nowrap px-2.5 py-1 rounded-full bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border border-neutral-800 transition-colors disabled:opacity-40"
          >
            {promptText}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 bg-neutral-900 border-t border-neutral-800 flex items-center gap-2"
      >
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          disabled={!jobId || isProcessing}
          placeholder={jobId ? "Ask for revisions (e.g. trim intro, change caption font)..." : "Create video to start editing..."}
          className="flex-1 bg-neutral-950 border border-neutral-800 rounded-xl px-3.5 py-2 text-xs text-neutral-200 placeholder:text-neutral-500 focus:outline-none focus:border-rose-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!jobId || !inputVal.trim() || isProcessing}
          className="p-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white disabled:opacity-50 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

