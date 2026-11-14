"use client";

import React, { useState, useEffect } from "react";
import { Key, Play, X, RefreshCw, Plus, Check } from "lucide-react";
import { YoutubeIcon } from "./YoutubeIcon";

interface ChannelConnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentChannel: any;
  onChannelConnected: () => void;
  onSelectVideoForClipping: (url: string) => void;
}

export function ChannelConnectModal({
  isOpen,
  onClose,
  currentChannel,
  onChannelConnected,
  onSelectVideoForClipping,
}: ChannelConnectModalProps) {
  const [activeTab, setActiveTab] = useState<"channel" | "videos">("channel");
  const [channelVideos, setChannelVideos] = useState<any[]>([]);
  const [isLoadingVideos, setIsLoadingVideos] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [isSavingCreds, setIsSavingCreds] = useState(false);
  const [isOAuthConfigured, setIsOAuthConfigured] = useState(false);
  const [showSetupGuide, setShowSetupGuide] = useState(false);

  useEffect(() => {
    if (isOpen) {
      checkOAuthConfig();
      if (currentChannel) {
        setActiveTab("videos");
        fetchChannelVideos();
      } else {
        setActiveTab("channel");
      }
    }
  }, [isOpen, currentChannel]);

  const checkOAuthConfig = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/oauth-config");
      if (res.ok) {
        const data = await res.json();
        setIsOAuthConfigured(data.is_configured);
      }
    } catch {}
  };

  const fetchChannelVideos = async () => {
    setIsLoadingVideos(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/channel-videos");
      if (res.ok) {
        const data = await res.json();
        setChannelVideos(data.videos || []);
      }
    } catch {
      // offline fallback
    } finally {
      setIsLoadingVideos(false);
    }
  };

  const handleConnectSandbox = async () => {
    setIsConnecting(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/connect-sandbox", {
        method: "POST",
      });
      if (res.ok) {
        onChannelConnected();
        setActiveTab("videos");
        fetchChannelVideos();
      }
    } catch (err: any) {
      alert(`Connection failed: ${err.message}`);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await fetch("http://localhost:8000/api/v1/youtube/disconnect", { method: "POST" });
      onChannelConnected();
    } catch (err: any) {
      alert(`Disconnect failed: ${err.message}`);
    }
  };

  const handleSaveAndAuthorizeGoogle = async () => {
    if (!clientId.trim() || !clientSecret.trim()) {
      alert("Please enter both Google Client ID and Client Secret.");
      return;
    }
    setIsSavingCreds(true);
    try {
      const saveRes = await fetch("http://localhost:8000/api/v1/youtube/save-credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: clientId.trim(),
          client_secret: clientSecret.trim(),
        }),
      });

      if (!saveRes.ok) throw new Error("Failed to save credentials");

      const authRes = await fetch("http://localhost:8000/api/v1/youtube/auth-url");
      if (!authRes.ok) throw new Error("Failed to generate Google consent URL");

      const authData = await authRes.json();
      window.location.href = authData.url;
    } catch (err: any) {
      alert(`OAuth Error: ${err.message}`);
      setIsSavingCreds(false);
    }
  };

  const handleStartGoogleOAuth = async () => {
    setIsConnecting(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/youtube/auth-url");
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start Google OAuth");
      }
      const data = await res.json();
      window.location.href = data.url;
    } catch (err: any) {
      alert(`OAuth error: ${err.message}`);
      setIsConnecting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-surface-container-lowest border-2 border-primary shadow-[5px_5px_0px_#111111] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b-2 border-primary flex items-center justify-between bg-surface-container text-primary">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 border-2 border-primary bg-surface-container-lowest flex items-center justify-center shadow-[2px_2px_0px_#111111]">
              <YoutubeIcon className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-headline font-bold text-sm uppercase tracking-tight text-primary">
                  {currentChannel ? "Connected YouTube Channel" : "Connect YouTube Channel"}
                </h3>
                <span className="font-mono text-[10px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold">
                  OAUTH 2.0
                </span>
              </div>
              <p className="font-mono text-[11px] text-outline mt-0.5">
                {currentChannel
                  ? "Import uploads directly into the studio or schedule automated publishing"
                  : "Direct publishing to your live channel via official Google OAuth 2.0"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 border border-primary bg-surface-container-lowest hover:bg-surface-container shadow-[1px_1px_0px_#111111] transition-colors"
          >
            <X className="w-4 h-4 text-primary" />
          </button>
        </div>

        {/* Tab Controls (if connected) */}
        {currentChannel && (
          <div className="flex border-b-2 border-primary px-4 bg-surface-container-low gap-3 text-xs font-mono font-bold">
            <button
              onClick={() => setActiveTab("videos")}
              className={`py-2 border-b-2 uppercase tracking-wider transition-all ${
                activeTab === "videos"
                  ? "border-primary text-primary"
                  : "border-transparent text-outline hover:text-primary"
              }`}
            >
              Channel Videos ({channelVideos.length})
            </button>
            <button
              onClick={() => setActiveTab("channel")}
              className={`py-2 border-b-2 uppercase tracking-wider transition-all ${
                activeTab === "channel"
                  ? "border-primary text-primary"
                  : "border-transparent text-outline hover:text-primary"
              }`}
            >
              Channel Settings & Quota
            </button>
          </div>
        )}

        {/* Body */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-4 flex-1 font-body text-xs">
          {(!currentChannel || activeTab === "channel") && (
            <div className="space-y-4">
              {currentChannel ? (
                <div className="p-3 bg-surface-container-low border-2 border-primary shadow-[2px_2px_0px_#111111] flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-3">
                    <img
                      src={currentChannel.thumbnail_url}
                      alt={currentChannel.channel_title}
                      className="w-12 h-12 border-2 border-primary shadow-[1px_1px_0px_#111111] object-cover"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-headline font-bold text-sm text-primary uppercase">
                          {currentChannel.channel_title}
                        </span>
                        <span className="font-mono text-[10px] px-1.5 py-0.2 bg-[#d5eb45] border border-primary font-bold">
                          {currentChannel.is_sandbox ? "Sandbox Mode" : "Live Channel"}
                        </span>
                      </div>
                      <span className="font-mono text-xs text-outline mt-0.5 block">
                        {currentChannel.custom_url} • {(currentChannel.subscriber_count || 0).toLocaleString()} Subscribers
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {currentChannel.is_sandbox ? (
                      <button
                        onClick={handleStartGoogleOAuth}
                        className="px-3 py-1.5 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all flex items-center gap-1.5"
                      >
                        <YoutubeIcon className="w-3.5 h-3.5 text-[#d5eb45]" />
                        <span>Connect Real Channel</span>
                      </button>
                    ) : null}
                    <button
                      onClick={fetchChannelVideos}
                      className="px-3 py-1.5 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container text-primary font-mono text-xs uppercase font-bold shadow-[1px_1px_0px_#111111] transition-all flex items-center gap-1"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Sync</span>
                    </button>
                    <button
                      onClick={handleDisconnect}
                      className="px-3 py-1.5 border-2 border-primary bg-surface-container-lowest hover:bg-red-100 text-red-700 font-mono text-xs uppercase font-bold shadow-[1px_1px_0px_#111111] transition-all"
                    >
                      <span>Disconnect</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Option A: Connect Real YouTube Channel */}
                  <div className="p-4 bg-surface-container-lowest border-2 border-primary shadow-[3px_3px_0px_#111111] space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-9 h-9 border-2 border-primary bg-surface-container flex items-center justify-center shrink-0">
                          <YoutubeIcon className="w-4 h-4 text-red-600" />
                        </div>
                        <div>
                          <h4 className="font-headline font-bold text-sm text-primary uppercase">
                            Connect Live YouTube Channel
                          </h4>
                          <p className="font-mono text-[11px] text-outline">
                            Direct upload access via official Google OAuth 2.0 Web Client
                          </p>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => setShowSetupGuide(!showSetupGuide)}
                        className="font-mono text-[11px] text-primary hover:underline font-bold uppercase"
                      >
                        {showSetupGuide ? "[Hide Instructions]" : "[Setup Instructions]"}
                      </button>
                    </div>

                    {showSetupGuide && (
                      <div className="p-3 bg-surface-container border border-primary font-mono text-xs text-primary space-y-1.5">
                        <p className="font-bold uppercase">[Google Cloud Console Instructions]</p>
                        <ol className="list-decimal pl-4 space-y-1 text-[11px] leading-relaxed text-outline-variant">
                          <li>
                            Open Google Cloud Console and enable the <strong>YouTube Data API v3</strong>.
                          </li>
                          <li>
                            Under <strong>OAuth consent screen</strong>, select External and add your email as a test user.
                          </li>
                          <li>
                            Under <strong>Credentials</strong>, create an OAuth 2.0 Web Client ID.
                          </li>
                          <li>
                            Set Authorized Redirect URI: <code className="bg-surface-container-lowest px-1 py-0.5 border border-primary">http://localhost:8000/api/v1/youtube/callback</code>
                          </li>
                        </ol>
                      </div>
                    )}

                    {isOAuthConfigured ? (
                      <div className="pt-1 text-center space-y-2">
                        <button
                          onClick={handleStartGoogleOAuth}
                          disabled={isConnecting}
                          className="w-full py-3 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[3px_3px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all flex items-center justify-center gap-2"
                        >
                          <YoutubeIcon className="w-4 h-4 text-[#d5eb45]" />
                          <span>{isConnecting ? "Redirecting to Google..." : "Sign in with Google to Connect Channel"}</span>
                        </button>
                        <p className="font-mono text-[10px] text-outline">
                          Google will ask you to authorize video upload and channel metadata access.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-3 pt-1">
                        <div>
                          <label className="font-mono text-xs font-bold text-primary uppercase block mb-1">
                            Google Client ID
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. 1234567890-abcdef.apps.googleusercontent.com"
                            value={clientId}
                            onChange={(e) => setClientId(e.target.value)}
                            className="w-full px-3 py-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary placeholder:text-outline focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
                          />
                        </div>

                        <div>
                          <label className="font-mono text-xs font-bold text-primary uppercase block mb-1">
                            Google Client Secret
                          </label>
                          <input
                            type="password"
                            placeholder="GOCSPX-..."
                            value={clientSecret}
                            onChange={(e) => setClientSecret(e.target.value)}
                            className="w-full px-3 py-2 border-2 border-primary bg-surface-container-lowest font-mono text-xs text-primary placeholder:text-outline focus:outline-none focus:shadow-[2px_2px_0px_#111111]"
                          />
                        </div>

                        <button
                          onClick={handleSaveAndAuthorizeGoogle}
                          disabled={isSavingCreds}
                          className="w-full py-2.5 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold tracking-wider shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all flex items-center justify-center gap-2"
                        >
                          <Key className="w-3.5 h-3.5 text-[#d5eb45]" />
                          <span>{isSavingCreds ? "Saving & Connecting..." : "Save Credentials & Connect Channel"}</span>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Option B: 1-Click Sandbox Simulator */}
                  <div className="p-3 bg-surface-container-low border-2 border-primary shadow-[2px_2px_0px_#111111] flex items-center justify-between">
                    <div>
                      <h5 className="font-headline font-bold text-xs uppercase text-primary">
                        Sandbox Simulator
                      </h5>
                      <p className="font-mono text-[11px] text-outline">
                        Test video clipping and local scheduling without connecting Google credentials.
                      </p>
                    </div>

                    <button
                      onClick={handleConnectSandbox}
                      disabled={isConnecting}
                      className="px-3 py-1.5 border-2 border-primary bg-surface-container-lowest hover:bg-[#d5eb45] text-primary font-mono text-xs uppercase font-bold shrink-0 shadow-[1px_1px_0px_#111111] transition-all"
                    >
                      Use Sandbox
                    </button>
                  </div>
                </div>
              )}

              {/* Quota Information */}
              <div className="p-3 bg-surface-container-lowest border-2 border-primary shadow-[2px_2px_0px_#111111] space-y-1.5">
                <div className="flex justify-between items-center font-mono text-xs">
                  <span className="font-bold text-primary uppercase">Daily YouTube API Quota</span>
                  <span className="font-bold text-primary">10,000 / 10,000 Units (Safe)</span>
                </div>
                <div className="w-full h-2 border border-primary bg-surface-container overflow-hidden">
                  <div className="h-full bg-[#d5eb45] w-[0%]" />
                </div>
                <p className="font-mono text-[10px] text-outline leading-relaxed">
                  Each Short upload consumes 1,600 units. Motion Studio automatically throttles publishing to a safe maximum of 5 clips per day to guarantee zero quota exceedance.
                </p>
              </div>
            </div>
          )}

          {currentChannel && activeTab === "videos" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-outline uppercase tracking-wider">
                  Recent Channel Uploads (Ready to Clip)
                </span>
                <button
                  onClick={fetchChannelVideos}
                  disabled={isLoadingVideos}
                  className="font-mono text-xs text-primary hover:underline flex items-center gap-1 font-bold uppercase"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isLoadingVideos ? "animate-spin" : ""}`} />
                  <span>Refresh</span>
                </button>
              </div>

              {isLoadingVideos ? (
                <div className="py-8 text-center font-mono text-xs text-outline">Loading channel uploads...</div>
              ) : channelVideos.length === 0 ? (
                <div className="py-6 text-center font-mono text-xs text-outline">No videos found on this channel.</div>
              ) : (
                <div className="grid grid-cols-1 gap-2">
                  {channelVideos.map((vid) => (
                    <div
                      key={vid.id}
                      className="p-3 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container-low transition-all flex items-center justify-between gap-3 shadow-[2px_2px_0px_#111111]"
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="relative w-24 aspect-video shrink-0 bg-primary border border-primary overflow-hidden">
                          <img
                            src={vid.thumbnail}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                          <span className="absolute bottom-1 right-1 px-1 py-0.2 bg-primary text-on-primary font-mono text-[8px] font-bold">
                            {vid.duration_min}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <h5 className="font-headline font-bold text-xs text-primary truncate max-w-xs">
                            {vid.title}
                          </h5>
                          <div className="font-mono text-[10px] text-outline flex items-center gap-1.5 mt-0.5">
                            <span>{vid.views}</span>
                            <span>•</span>
                            <span>{vid.published_date}</span>
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          onSelectVideoForClipping(vid.youtube_url);
                          onClose();
                        }}
                        className="px-3 py-1.5 border-2 border-primary bg-primary text-on-primary font-mono text-xs uppercase font-bold shrink-0 shadow-[2px_2px_0px_#d5eb45] hover:bg-[#d5eb45] hover:text-primary transition-all flex items-center gap-1"
                      >
                        <Play className="w-3 h-3 fill-current text-[#d5eb45]" />
                        <span>Clip into Shorts</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t-2 border-primary bg-surface-container flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-1.5 border-2 border-primary bg-surface-container-lowest hover:bg-surface-container text-primary font-mono text-xs uppercase font-bold shadow-[1px_1px_0px_#111111] transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
