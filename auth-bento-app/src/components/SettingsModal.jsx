import React, { useState } from "react";
import { X, Database, Save, RotateCcw, Check, Sparkles } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { AuthService } from "../lib/auth";

export function SettingsModal({ isOpen, onClose, onConfigSaved }) {
  const currentConfig = AuthService.getSavedConfig();
  const [url, setUrl] = useState(currentConfig.url);
  const [key, setKey] = useState(currentConfig.key);
  const [status, setStatus] = useState("");

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    const res = AuthService.saveConfig(url.trim(), key.trim());
    if (res.success) {
      setStatus("Config updated successfully!");
      setTimeout(() => {
        setStatus("");
        onConfigSaved();
        onClose();
      }, 1000);
    } else {
      setStatus("Error: " + res.error);
    }
  };

  const handleReset = () => {
    AuthService.saveConfig("", "");
    setUrl("");
    setKey("");
    setStatus("Reset to built-in cryptographic simulation sandbox.");
    setTimeout(() => {
      setStatus("");
      onConfigSaved();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-md p-6 rounded-2xl bg-zinc-900 border border-zinc-800 shadow-2xl relative space-y-5">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-zinc-800"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Backend Auth Configuration</h3>
            <p className="text-xs text-zinc-400">Connect to live Supabase / Firebase or use Sandbox</p>
          </div>
        </div>

        {status && (
          <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs text-indigo-300 font-mono">
            {status}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-4 text-xs">
          <div className="space-y-1">
            <Label htmlFor="cfg-url">Supabase / Backend Project URL</Label>
            <Input
              id="cfg-url"
              placeholder="https://your-project.supabase.co"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <p className="text-[10px] text-zinc-500">Leave blank to use the built-in local sandbox.</p>
          </div>

          <div className="space-y-1">
            <Label htmlFor="cfg-key">Anon / Public API Key</Label>
            <Input
              id="cfg-key"
              type="password"
              placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
          </div>

          <div className="pt-2 flex items-center gap-2">
            <Button type="submit" variant="primary" className="flex-1 flex items-center justify-center gap-1.5">
              <Save className="w-4 h-4" />
              <span>Save & Connect</span>
            </Button>
            <Button type="button" variant="outline" onClick={handleReset} title="Reset to Sandbox">
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
