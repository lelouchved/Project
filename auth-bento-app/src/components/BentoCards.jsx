import React from "react";
import { ShieldCheck, Zap, Lock, KeyRound, Sparkles, CheckCircle, Fingerprint, Layers, Cpu } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";

export function SecurityBentoCard() {
  return (
    <Card className="flex flex-col justify-between overflow-hidden relative group hover:border-zinc-700/80 transition-all duration-300">
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all pointer-events-none" />
      
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <Badge variant="success" className="gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            SOC2 Ready
          </Badge>
        </div>

        <div>
          <h4 className="text-sm font-bold text-white">Zero-Knowledge Vault</h4>
          <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
            End-to-end encrypted session tokens stored with hardware-level biometric integrity.
          </p>
        </div>
      </div>

      <div className="pt-4 mt-2 border-t border-zinc-800/80 flex items-center justify-between text-[11px] font-mono text-zinc-400">
        <span className="flex items-center gap-1.5">
          <Lock className="w-3.5 h-3.5 text-indigo-400" />
          <span>AES-256-GCM</span>
        </span>
        <span className="text-zinc-500">SHA-512 Hash</span>
      </div>
    </Card>
  );
}

export function SpeedMetricsBentoCard() {
  return (
    <Card className="flex flex-col justify-between overflow-hidden relative group hover:border-zinc-700/80 transition-all duration-300">
      <div className="absolute bottom-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-2xl group-hover:bg-purple-500/20 transition-all pointer-events-none" />

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
            <Zap className="w-5 h-5" />
          </div>
          <span className="text-[11px] font-mono text-zinc-400">Edge Auth</span>
        </div>

        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black tracking-tight text-white font-mono">&lt; 38ms</span>
            <span className="text-[11px] text-emerald-400 font-semibold font-mono">p99 Handshake</span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Global distributed edge nodes ensuring sub-50ms sign-in verification worldwide.
          </p>
        </div>
      </div>

      <div className="pt-3 border-t border-zinc-800/80 flex items-center gap-2">
        <div className="flex -space-x-1.5 overflow-hidden">
          <span className="inline-block h-5 w-5 rounded-full ring-2 ring-zinc-900 bg-zinc-700 text-[9px] font-bold text-center leading-5 text-white">US</span>
          <span className="inline-block h-5 w-5 rounded-full ring-2 ring-zinc-900 bg-zinc-600 text-[9px] font-bold text-center leading-5 text-white">EU</span>
          <span className="inline-block h-5 w-5 rounded-full ring-2 ring-zinc-900 bg-indigo-600 text-[9px] font-bold text-center leading-5 text-white">AP</span>
        </div>
        <span className="text-[11px] text-zinc-400 font-mono">14 Global Edges</span>
      </div>
    </Card>
  );
}

export function MultiProviderBentoCard() {
  return (
    <Card className="flex flex-col justify-between overflow-hidden relative group hover:border-zinc-700/80 transition-all duration-300">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="w-9 h-9 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400 flex items-center justify-center">
            <Fingerprint className="w-5 h-5" />
          </div>
          <Badge variant="outline" className="text-zinc-400 border-zinc-800 font-mono text-[10px]">
            OAuth 2.0
          </Badge>
        </div>

        <div>
          <h4 className="text-sm font-bold text-white">Federated Providers</h4>
          <p className="text-xs text-zinc-400 mt-1">
            Instant 1-click authentication via Google, GitHub, Supabase Auth, and Email tokens.
          </p>
        </div>
      </div>

      <div className="pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
        <span className="flex items-center gap-1.5 font-medium text-white">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>PKCE Flow</span>
        </span>
        <span className="text-[11px] font-mono text-zinc-500">RFC 7636</span>
      </div>
    </Card>
  );
}

export function QuickAutofillCard({ onAutofill }) {
  return (
    <Card className="border-indigo-500/30 bg-gradient-to-br from-indigo-950/20 via-zinc-900/60 to-purple-950/20 relative overflow-hidden">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">Fast Demo Login</span>
        </div>
        <Badge variant="warning">Click to Test</Badge>
      </div>

      <p className="text-xs text-zinc-300 leading-relaxed mb-3">
        Need to test right away without registering a new email? Click below to instantly load demo credentials:
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => onAutofill("alex.chen@msot.edu", "Password123!")}
          className="p-2.5 rounded-xl border border-zinc-800 hover:border-indigo-500/50 bg-zinc-900/80 text-left transition group hover:bg-zinc-800/60"
        >
          <div className="text-xs font-bold text-zinc-200 group-hover:text-indigo-300 truncate">
            Alex Chen (Lead Eng)
          </div>
          <div className="text-[10px] font-mono text-zinc-500 truncate">
            alex.chen@msot.edu
          </div>
        </button>

        <button
          type="button"
          onClick={() => onAutofill("sarah.connor@cyber.org", "Password123!")}
          className="p-2.5 rounded-xl border border-zinc-800 hover:border-purple-500/50 bg-zinc-900/80 text-left transition group hover:bg-zinc-800/60"
        >
          <div className="text-xs font-bold text-zinc-200 group-hover:text-purple-300 truncate">
            Sarah Connor (Security)
          </div>
          <div className="text-[10px] font-mono text-zinc-500 truncate">
            sarah.connor@cyber.org
          </div>
        </button>
      </div>
    </Card>
  );
}
