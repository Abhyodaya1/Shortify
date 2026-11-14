"use client";

import React, { useState, useEffect } from "react";
import {
  Calendar,
  Clock,
  Trash2,
  Rocket,
  RefreshCw,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  Play,
  ArrowRight,
} from "lucide-react";
import { YoutubeIcon } from "./YoutubeIcon";

interface SchedulerViewProps {
  currentChannel: any;
  onOpenConnectModal: () => void;
  onSwitchToStudio: () => void;
}

export function SchedulerView({
  currentChannel,
  onOpenConnectModal,
  onSwitchToStudio,
}: SchedulerViewProps) {
  const [queue, setQueue] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [workerStatus, setWorkerStatus] = useState<any>({
    is_running: true,
    emergency_stop: false,
    jobs_processed: 0,
  });

  useEffect(() => {
    fetchQueue();
    fetchWorkerStatus();
    const interval = setInterval(() => {
      fetchQueue();
      fetchWorkerStatus();
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchWorkerStatus = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/worker/status");
      if (res.ok) {
        const data = await res.json();
        setWorkerStatus(data);
      }
    } catch {
      // offline fallback
    }
  };

  const handleToggleEmergencyStop = async () => {
    const nextState = !workerStatus?.emergency_stop;
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/worker/emergency-stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stopped: nextState }),
      });
      if (res.ok) {
        const data = await res.json();
        setWorkerStatus(data.worker_status || { ...workerStatus, emergency_stop: nextState });
      }
    } catch (err: any) {
      alert(`Emergency stop failed: ${err.message}`);
    }
  };

  const fetchQueue = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/queue");
      if (res.ok) {
        const data = await res.json();
        setQueue(data.queue || []);
      }
    } catch {
      // offline fallback
    } finally {
      setIsLoading(false);
    }
  };

  const handlePublishNow = async (jobId: string) => {
    setActionInProgress(jobId);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/youtube/queue/${jobId}/publish-now`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchQueue();
      }
    } finally {
      setActionInProgress(null);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/youtube/queue/${jobId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setQueue((prev) => prev.filter((j) => j.job_id !== jobId));
      }
    } catch (err: any) {
      alert(`Cancel failed: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 bg-[#fbf9f4] text-[#1b1c19] font-body selection:bg-[#d5eb45]">
      {/* Top Banner / Channel Status (Neo-Brutalist Strip) */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 sm:p-5 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111]">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 border-2 border-primary bg-[#f0eee9] text-primary flex items-center justify-center shadow-[2px_2px_0px_#111111] shrink-0">
            <Calendar className="w-5 h-5 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="font-headline font-bold text-base text-primary uppercase tracking-tight">
                Automated Publishing Queue
              </h2>
              <span className="font-mono text-[10px] px-2 py-0.5 border border-primary bg-[#d5eb45] text-primary font-bold uppercase tracking-wider shadow-[1px_1px_0px_#111111]">
                PERSISTENT SCHEDULER
              </span>
              <span className="inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 border border-primary bg-surface-container font-bold uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00e297] animate-pulse"></span>
                POLLING: 15s LOOP
              </span>
            </div>
            <p className="font-mono text-xs text-outline-variant mt-1">
              Background daemon polls scheduled jobs every 15s and uploads directly to YouTube without manual intervention.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={fetchQueue}
            disabled={isLoading}
            className="px-3 py-2 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container text-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[1px_1px_0px_#111111] transition-all flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh Queue</span>
          </button>
          <button
            onClick={onSwitchToStudio}
            className="px-4 py-2 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary hover:shadow-[1px_1px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] transition-all flex items-center gap-2"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#d5eb45]" />
            <span>Create More Clips</span>
          </button>
        </div>
      </div>

      {/* Grid: 4 Metric & Worker Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {/* CARD 1: Autopilot Engine */}
        <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] space-y-2">
          <div className="flex items-center justify-between pb-1 border-b border-primary/20">
            <span className="font-mono text-[10px] font-bold text-outline uppercase tracking-wider">
              Autopilot Engine
            </span>
            <span className="font-mono text-[10px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold">
              ACTIVE
            </span>
          </div>
          <div className="font-headline text-xl font-bold text-primary tracking-tight">
            1 Clip / Day
          </div>
          <p className="font-body text-xs text-on-surface-variant leading-relaxed">
            Auto-packages top scored candidate via editorial agent at 18:00 UTC daily.
          </p>
        </div>

        {/* CARD 2: YouTube Quota */}
        <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] space-y-2">
          <div className="flex items-center justify-between pb-1 border-b border-primary/20">
            <span className="font-mono text-[10px] font-bold text-outline uppercase tracking-wider">
              YouTube Quota
            </span>
            <span className="font-mono text-[10px] text-outline font-bold">10,000 Limit</span>
          </div>
          <div className="font-headline text-xl font-bold text-primary tracking-tight">
            1,600 / 10,000
          </div>
          <div className="w-full h-2 border border-primary bg-surface-container overflow-hidden">
            <div className="h-full bg-[#d5eb45] w-[16%]" />
          </div>
          <p className="font-mono text-[10px] text-outline">
            Protected against quota depletion. Max 5 uploads / 24 hours.
          </p>
        </div>

        {/* CARD 3: Target Channel */}
        <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] space-y-2">
          <div className="flex items-center justify-between pb-1 border-b border-primary/20">
            <span className="font-mono text-[10px] font-bold text-outline uppercase tracking-wider">
              Target Channel
            </span>
            <button
              onClick={onOpenConnectModal}
              className="font-mono text-[10px] text-primary hover:underline font-bold uppercase"
            >
              [Change]
            </button>
          </div>
          <div className="flex items-center gap-2.5 pt-1">
            <img
              src={currentChannel?.thumbnail_url || "https://api.dicebear.com/7.x/bottts/svg?seed=AbhyodayaClips"}
              alt=""
              className="w-9 h-9 border border-primary shadow-[1px_1px_0px_#111111] object-cover"
            />
            <div className="truncate min-w-0">
              <span className="font-headline font-bold text-xs text-primary block truncate">
                {currentChannel?.channel_title || "Abhyodaya Singh Clips"}
              </span>
              <span className="font-mono text-[11px] text-outline truncate block">
                {currentChannel?.custom_url || "@AbhyodayaClips"}
              </span>
            </div>
          </div>
        </div>

        {/* CARD 4: Worker Daemon Status & Emergency Control */}
        <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] space-y-2">
          <div className="flex items-center justify-between pb-1 border-b border-primary/20">
            <span className="font-mono text-[10px] font-bold text-outline uppercase tracking-wider">
              Background Worker
            </span>
            <span
              className={`font-mono text-[10px] px-1.5 py-0.2 border border-primary font-bold ${
                workerStatus?.emergency_stop
                  ? "bg-red-200 text-red-900"
                  : "bg-[#00e297] text-primary"
              }`}
            >
              {workerStatus?.emergency_stop ? "PAUSED" : "ACTIVE (15s)"}
            </span>
          </div>
          <div className="flex items-center justify-between pt-1">
            <div>
              <span className="font-headline text-lg font-bold text-primary block tracking-tight">
                {workerStatus?.jobs_processed || 0} Published
              </span>
              <span className="font-mono text-[10px] text-outline">
                Atomic Lock Active
              </span>
            </div>
            <button
              onClick={handleToggleEmergencyStop}
              className={`px-2.5 py-1.5 border-2 border-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#111111] hover:translate-x-[1px] hover:translate-y-[1px] transition-all ${
                workerStatus?.emergency_stop
                  ? "bg-[#d5eb45] text-primary"
                  : "bg-surface-container hover:bg-red-100 text-red-700"
              }`}
            >
              {workerStatus?.emergency_stop ? "Resume" : "Stop"}
            </button>
          </div>
        </div>
      </div>

      {/* Scheduled Upload Queue Table (Focal Point of Scheduler) */}
      <div className="border-2 border-primary bg-surface-container-lowest shadow-[4px_4px_0px_#111111] overflow-hidden">
        <div className="p-3 sm:p-4 border-b-2 border-primary flex items-center justify-between bg-surface-container">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-primary" />
            <h3 className="font-headline font-bold text-sm uppercase text-primary tracking-tight">
              Upload Queue ({queue.length})
            </h3>
          </div>
          <span className="font-mono text-[11px] text-outline uppercase">
            Persistent SQLite queue with restart recovery
          </span>
        </div>

        {queue.length === 0 ? (
          <div className="py-12 text-center space-y-3 p-4">
            <Calendar className="w-10 h-10 text-outline mx-auto" />
            <div className="space-y-1">
              <h4 className="font-headline font-bold text-sm text-primary uppercase">No scheduled uploads pending</h4>
              <p className="font-body text-xs text-on-surface-variant max-w-sm mx-auto leading-relaxed">
                Open the Video Studio, generate candidate clips from your video, and click &ldquo;Post / Schedule&rdquo; to schedule automatic YouTube uploads.
              </p>
            </div>
            <button
              onClick={onSwitchToStudio}
              className="px-4 py-2 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all"
            >
              Open Video Studio
            </button>
          </div>
        ) : (
          <div className="divide-y-2 divide-primary">
            {queue.map((job) => {
              const isPublished = job.status === "published";
              return (
                <div
                  key={job.job_id}
                  className="p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-surface-container-low transition-colors"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="w-16 h-20 bg-primary shrink-0 relative flex items-center justify-center border-2 border-primary shadow-[2px_2px_0px_#111111] overflow-hidden">
                      {job.thumbnail_url ? (
                        <video
                          src={job.thumbnail_url}
                          className="w-full h-full object-cover"
                          muted
                        />
                      ) : (
                        <YoutubeIcon className="w-6 h-6 text-red-600" />
                      )}
                      <span className="absolute bottom-1 right-1 px-1 py-0.2 bg-primary text-on-primary font-mono text-[8px] font-bold border border-primary">
                        9:16
                      </span>
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h5 className="font-headline font-bold text-xs text-primary truncate max-w-md">
                          {job.title}
                        </h5>
                        <span
                          className={`font-mono text-[9px] px-2 py-0.5 border border-primary font-bold uppercase tracking-wider ${
                            isPublished
                              ? "bg-[#d5eb45] text-primary"
                              : "bg-surface-container text-primary"
                          }`}
                        >
                          {job.status}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 font-mono text-[11px] text-outline mt-1 flex-wrap">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-primary" />
                          {job.scheduled_time?.replace("T", " ")}
                        </span>
                        <span>•</span>
                        <span className="capitalize">{job.visibility}</span>
                        {job.youtube_url && (
                          <>
                            <span>•</span>
                            <a
                              href={job.youtube_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-primary hover:underline font-bold"
                            >
                              View on YouTube ➔
                            </a>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    {!isPublished && (
                      <button
                        onClick={() => handlePublishNow(job.job_id)}
                        disabled={actionInProgress === job.job_id}
                        className="px-3 py-1.5 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all flex items-center gap-1.5"
                      >
                        <Rocket className="w-3.5 h-3.5" />
                        <span>{actionInProgress === job.job_id ? "Publishing..." : "Publish Now"}</span>
                      </button>
                    )}
                    <button
                      onClick={() => handleCancelJob(job.job_id)}
                      className="p-1.5 border-2 border-primary bg-surface-container-lowest hover:bg-red-100 text-outline hover:text-red-700 shadow-[1px_1px_0px_#111111] transition-colors"
                      title="Delete from schedule"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
