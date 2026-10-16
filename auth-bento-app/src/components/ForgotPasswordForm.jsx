import React, { useState } from "react";
import { Mail, ArrowLeft, Send, CheckCircle2 } from "lucide-react";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Alert, AlertTitle, AlertDescription } from "./ui/alert";
import { AuthService } from "../lib/auth";

export function ForgotPasswordForm({ onSwitchTab }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [successInfo, setSuccessInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessInfo(null);

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) {
      setError("Please enter your registered email address.");
      return;
    }
    if (!emailRegex.test(email.trim())) {
      setError("Please provide a valid email format.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await AuthService.resetPassword(email.trim());
      setSuccessInfo(res);
    } catch (err) {
      setError(err.message || "Failed to process recovery request.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h4 className="text-base font-bold text-white">Reset Account Password</h4>
        <p className="text-xs text-zinc-400 leading-relaxed">
          Enter the email associated with your account and we will send you a secure recovery link.
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Recovery Notice</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {successInfo && (
        <Alert variant="success">
          <AlertTitle>Recovery Email Dispatched</AlertTitle>
          <AlertDescription>
            {successInfo.message}
            {successInfo.recoveryToken && (
              <div className="mt-2 p-2 rounded-lg bg-zinc-950/80 border border-emerald-500/30 font-mono text-[10px] text-emerald-300 select-all">
                Recovery Ticket: {successInfo.recoveryToken}
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {!successInfo ? (
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="forgot-email" required>
              Account Email
            </Label>
            <Input
              id="forgot-email"
              type="email"
              placeholder="alex.chen@msot.edu"
              icon={Mail}
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (error) setError("");
              }}
              error={Boolean(error)}
              autoComplete="email"
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            className="w-full h-11 text-white font-semibold flex items-center justify-center gap-2 group"
          >
            <Send className="w-4 h-4" />
            <span>Send Password Reset Link</span>
          </Button>
        </form>
      ) : (
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            setSuccessInfo(null);
            setEmail("");
          }}
          className="w-full text-xs text-zinc-300"
        >
          Send to a different email
        </Button>
      )}

      <div className="pt-2 text-center">
        <button
          type="button"
          onClick={() => onSwitchTab("login")}
          className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Sign In</span>
        </button>
      </div>
    </div>
  );
}
