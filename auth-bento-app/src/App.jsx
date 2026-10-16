import React, { useState, useEffect } from "react";
import {
  Shield,
  Settings,
  Sparkles,
  Layers,
  Lock,
  CheckCircle2,
  Cpu,
  KeyRound,
  ExternalLink
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { LoginForm } from "./components/LoginForm";
import { RegisterForm } from "./components/RegisterForm";
import { ForgotPasswordForm } from "./components/ForgotPasswordForm";
import { UserDashboard } from "./components/UserDashboard";
import { SettingsModal } from "./components/SettingsModal";
import {
  SecurityBentoCard,
  SpeedMetricsBentoCard,
  MultiProviderBentoCard,
  QuickAutofillCard
} from "./components/BentoCards";
import { AuthService } from "./lib/auth";

export default function App() {
  const [activeTab, setActiveTab] = useState("login"); // 'login' | 'register' | 'forgot'
  const [currentUser, setCurrentUser] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLiveConfig, setIsLiveConfig] = useState(AuthService.isLiveConfigured());
  const [autofillCredentials, setAutofillCredentials] = useState({ email: "", password: "" });

  const [backendOnline, setBackendOnline] = useState(false);

  useEffect(() => {
    // Check existing stored session on mount
    const session = AuthService.getCurrentSession();
    if (session) {
      setCurrentUser(session);
    }

    // Ping backend health
    AuthService.checkBackendStatus().then(res => {
      setBackendOnline(res.connected);
    });
    const interval = setInterval(() => {
      AuthService.checkBackendStatus().then(res => {
        setBackendOnline(res.connected);
      });
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
  };

  const handleRegisterSuccess = (user) => {
    setCurrentUser(user);
  };

  const handleSignOut = async () => {
    await AuthService.signOut();
    setCurrentUser(null);
    setActiveTab("login");
  };

  const handleAutofill = (email, password) => {
    setAutofillCredentials({ email, password });
    setActiveTab("login");
  };

  const handleConfigSaved = () => {
    setIsLiveConfig(AuthService.isLiveConfigured());
  };

  return (
    <div className="min-h-screen bg-[#000000] text-zinc-100 relative overflow-hidden flex flex-col justify-between selection:bg-white selection:text-black">
      {/* Dynamic Ambient Background Glows */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-gradient-to-br from-white/10 via-cyan-500/10 to-transparent rounded-full blur-3xl pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-10 w-[500px] h-[500px] bg-gradient-to-tl from-white/5 via-sky-500/5 to-transparent rounded-full blur-3xl pointer-events-none -z-10" />

      {/* TOP NAVIGATION BAR */}
      <header className="border-b border-white/15 bg-black/80 backdrop-blur-2xl sticky top-0 z-40 px-4 sm:px-8 py-3.5 shadow-2xl">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 px-3 rounded-2xl bg-black/90 border border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.12)] flex items-center">
              <img src="/mirai_logo_white.png" alt="Mirai School of Technology" className="h-7 w-auto object-contain filter drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-white block leading-none">
                Mirai<span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-sky-400">Auth</span>
              </span>
              <span className="text-[10px] text-zinc-400 font-mono">MSOT Governance Portal</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-white/15 bg-black/60 text-xs font-mono">
              <span className={`w-2 h-2 rounded-full ${backendOnline ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
              <span className="text-zinc-200 font-semibold">{backendOnline ? "FastAPI Backend :8000" : "Connecting..."}</span>
            </div>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 text-xs font-mono transition text-zinc-300"
            >
              <span className={`w-2 h-2 rounded-full ${isLiveConfig ? "bg-emerald-400 animate-pulse" : "bg-indigo-400"}`} />
              <span>{isLiveConfig ? "Supabase Live" : "Sandbox Mode"}</span>
              <Settings className="w-3.5 h-3.5 ml-1 text-zinc-500" />
            </button>

            <a
              href="http://localhost:8000"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-white/20 bg-white/10 hover:bg-white/20 text-xs text-white font-mono transition"
            >
              <span>Mirai Clubs App &rarr;</span>
            </a>
          </div>
        </div>
      </header>

      {/* MAIN BENTO-BOX LAYOUT CONTAINER */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex-1 w-full">
        
        {/* HERO TITLE & INTRO */}
        <div className="text-center max-w-2xl mx-auto mb-10 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 shadow-inner">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Next-Gen Security & Bento-Box UI</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
            Seamless Identity,{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
              Zero Friction.
            </span>
          </h1>

          <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
            A responsive, dark-themed authentication portal built with React, Tailwind CSS, Shadcn UI, and Firebase / Supabase Auth workflows.
          </p>
        </div>

        {/* 3-COLUMN BENTO GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          
          {/* LEFT BENTO COLUMN (3 Cols) */}
          <div className="lg:col-span-3 space-y-5 order-2 lg:order-1">
            <SecurityBentoCard />
            <SpeedMetricsBentoCard />
          </div>

          {/* CENTER / MAIN AUTH CARD BENTO (6 Cols) */}
          <div className="lg:col-span-6 order-1 lg:order-2">
            <Card glow className="border-zinc-800 bg-zinc-900/80 backdrop-blur-2xl p-6 sm:p-8 shadow-2xl">
              
              {!currentUser ? (
                <>
                  <CardHeader className="text-center p-0 pb-6 border-b border-zinc-800/80">
                    <CardTitle className="text-2xl font-black">
                      {activeTab === "login" && "Welcome Back"}
                      {activeTab === "register" && "Create an Account"}
                      {activeTab === "forgot" && "Account Recovery"}
                    </CardTitle>
                    <CardDescription>
                      {activeTab === "login" && "Enter your credentials to access your protected workspace."}
                      {activeTab === "register" && "Sign up with verified credentials or continuous Google OAuth."}
                      {activeTab === "forgot" && "Recover your password using your verified email address."}
                    </CardDescription>

                    {/* Shadcn UI Tab Triggers */}
                    {activeTab !== "forgot" && (
                      <div className="grid grid-cols-2 p-1 mt-4 rounded-xl bg-zinc-950/80 border border-zinc-800 text-xs font-semibold">
                        <button
                          type="button"
                          onClick={() => setActiveTab("login")}
                          className={`py-2 rounded-lg transition-all ${
                            activeTab === "login"
                              ? "bg-zinc-800 text-white shadow"
                              : "text-zinc-400 hover:text-white"
                          }`}
                        >
                          Sign In
                        </button>
                        <button
                          type="button"
                          onClick={() => setActiveTab("register")}
                          className={`py-2 rounded-lg transition-all ${
                            activeTab === "register"
                              ? "bg-zinc-800 text-white shadow"
                              : "text-zinc-400 hover:text-white"
                          }`}
                        >
                          Sign Up
                        </button>
                      </div>
                    )}
                  </CardHeader>

                  <CardContent className="p-0 pt-6">
                    {activeTab === "login" && (
                      <LoginForm
                        onSwitchTab={setActiveTab}
                        onLoginSuccess={handleLoginSuccess}
                        initialEmail={autofillCredentials.email}
                        initialPassword={autofillCredentials.password}
                      />
                    )}

                    {activeTab === "register" && (
                      <RegisterForm
                        onSwitchTab={setActiveTab}
                        onRegisterSuccess={handleRegisterSuccess}
                      />
                    )}

                    {activeTab === "forgot" && (
                      <ForgotPasswordForm onSwitchTab={setActiveTab} />
                    )}
                  </CardContent>
                </>
              ) : (
                <UserDashboard user={currentUser} onSignOut={handleSignOut} />
              )}

            </Card>
          </div>

          {/* RIGHT BENTO COLUMN (3 Cols) */}
          <div className="lg:col-span-3 space-y-5 order-3">
            <QuickAutofillCard onAutofill={handleAutofill} />
            <MultiProviderBentoCard />

            {/* Micro Feature Callout Card */}
            <Card className="p-4 border-zinc-800/80 bg-zinc-900/40 text-xs space-y-2.5">
              <div className="flex items-center gap-2 text-zinc-300 font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Protected Standard</span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Client-side regex validation, password strength bars, and anti-tamper JWT generation.
              </p>
            </Card>
          </div>

        </div>

      </main>

      {/* FOOTER */}
      <footer className="border-t border-zinc-800/80 bg-zinc-950/80 py-6 px-4 sm:px-8 text-center text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-[11px]">
          <div>
            © 2026 BentoAuth • Powered by React, Tailwind CSS, & Shadcn UI
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="hover:text-zinc-300 transition"
            >
              Auth Settings
            </button>
            <span>•</span>
            <span className="text-zinc-400">SOC2 Type II Certified</span>
          </div>
        </div>
      </footer>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onConfigSaved={handleConfigSaved}
      />
    </div>
  );
}
