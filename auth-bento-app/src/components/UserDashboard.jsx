import React from "react";
import { User, LogOut, ShieldCheck, Key, CheckCircle, Copy, Sparkles, ExternalLink } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Alert, AlertTitle, AlertDescription } from "./ui/alert";

export function UserDashboard({ user, onSignOut }) {
  const [copied, setCopied] = React.useState(false);

  const copyToken = () => {
    navigator.clipboard.writeText(user.token || `jwt_${user.id}_sec_${Date.now()}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <Alert variant="success" className="border-emerald-500/30 bg-emerald-950/20">
        <AlertTitle>Authenticated Successfully</AlertTitle>
        <AlertDescription>
          Session active and cryptographically verified. All protected dashboard routes unlocked.
        </AlertDescription>
      </Alert>

      {/* User Card */}
      <div className="p-5 rounded-2xl bg-zinc-900/90 border border-zinc-800 space-y-4">
        <div className="flex items-center gap-4">
          <div className="relative">
            <img
              src={user.avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${user.email}`}
              alt={user.name}
              className="w-16 h-16 rounded-2xl object-cover border-2 border-indigo-500/40 bg-zinc-950 shadow-lg"
            />
            <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-zinc-900 rounded-full" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-lg font-bold text-white truncate">{user.name}</h3>
              <Badge variant="success" className="text-[10px]">Active Session</Badge>
              <Badge variant="outline" className="text-[10px] uppercase font-mono">{user.provider || "email"}</Badge>
            </div>
            <p className="text-xs text-zinc-400 truncate mt-0.5">{user.email}</p>
            <p className="text-[11px] text-zinc-500 font-mono mt-1">ID: {user.id}</p>
          </div>
        </div>

        {/* Security Specs */}
        <div className="grid grid-cols-2 gap-2 pt-3 border-t border-zinc-800/80 text-xs font-mono">
          <div className="p-2.5 rounded-xl bg-zinc-950/60 border border-zinc-800/60">
            <span className="text-zinc-500 block text-[10px] uppercase">Auth Provider</span>
            <span className="text-zinc-200 font-bold capitalize">{user.provider || "Credentials"}</span>
          </div>
          <div className="p-2.5 rounded-xl bg-zinc-950/60 border border-zinc-800/60">
            <span className="text-zinc-500 block text-[10px] uppercase">Access Level</span>
            <span className="text-indigo-400 font-bold">Verified Member</span>
          </div>
        </div>

        {/* Session Token Box */}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center justify-between text-[11px] text-zinc-400 font-mono">
            <span>Bearer Session Token</span>
            <button
              onClick={copyToken}
              className="hover:text-white flex items-center gap-1 text-[10px] text-indigo-400"
            >
              {copied ? <CheckCircle className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Copied" : "Copy Token"}</span>
            </button>
          </div>
          <div className="p-2.5 rounded-xl bg-zinc-950 font-mono text-[10px] text-zinc-400 border border-zinc-800/80 break-all select-all">
            {user.token || `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${btoa(JSON.stringify({ sub: user.id, email: user.email }))}.mock_signature`}
          </div>
        </div>

        {/* Actions */}
        <div className="pt-2 flex items-center gap-3">
          <Button
            type="button"
            variant="destructive"
            onClick={onSignOut}
            className="flex-1 flex items-center justify-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out Session</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
