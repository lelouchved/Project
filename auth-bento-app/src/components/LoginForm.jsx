import React, { useState } from "react";
import { Mail, Lock, ArrowRight, ShieldAlert } from "lucide-react";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import { Alert, AlertTitle, AlertDescription } from "./ui/alert";
import { AuthService } from "../lib/auth";

export function LoginForm({ onSwitchTab, onLoginSuccess, initialEmail = "", initialPassword = "" }) {
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState(initialPassword);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  // Sync when autofilled from external props
  React.useEffect(() => {
    if (initialEmail) setEmail(initialEmail);
    if (initialPassword) setPassword(initialPassword);
  }, [initialEmail, initialPassword]);

  const validate = () => {
    const errs = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email.trim()) {
      errs.email = "Email address is required.";
    } else if (!emailRegex.test(email.trim())) {
      errs.email = "Please enter a valid email address (e.g. name@domain.com).";
    }

    if (!password) {
      errs.password = "Password is required.";
    } else if (password.length < 6) {
      errs.password = "Password must be at least 6 characters.";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError("");

    if (!validate()) return;

    setIsLoading(true);
    try {
      const { user } = await AuthService.signIn({ email, password });
      onLoginSuccess(user);
    } catch (err) {
      setServerError(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setServerError("");
    setIsGoogleLoading(true);
    try {
      const { user } = await AuthService.signInWithGoogle();
      onLoginSuccess(user);
    } catch (err) {
      setServerError(err.message || "Google sign-in encountered an error.");
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {serverError && (
        <Alert variant="destructive">
          <AlertTitle>Authentication Failed</AlertTitle>
          <AlertDescription>{serverError}</AlertDescription>
        </Alert>
      )}

      {/* Google Sign In Button */}
      <Button
        type="button"
        variant="outline"
        onClick={handleGoogleSignIn}
        isLoading={isGoogleLoading}
        className="w-full flex items-center justify-center gap-2.5 h-11 border-zinc-800 hover:border-zinc-700 bg-zinc-900/80 hover:bg-zinc-800/80 text-zinc-200"
      >
        <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
          <path
            fill="#EA4335"
            d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z"
          />
          <path
            fill="#4285F4"
            d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
          />
          <path
            fill="#FBBC05"
            d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15.1s.7 5.4 1.9 7.8l3.7-2.9c-.2-.7-.4-1.5-.4-2.3z"
          />
          <path
            fill="#34A853"
            d="M12 23.5c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2-6.4-4.8L1.9 17C3.7 20.7 7.5 23.5 12 23.5z"
          />
        </svg>
        <span>Sign in with Google</span>
      </Button>

      <Separator label="or continue with email" />

      {/* Traditional Email / Password Form */}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Email Field */}
        <div className="space-y-1.5">
          <Label htmlFor="login-email" required>
            Email Address
          </Label>
          <Input
            id="login-email"
            type="email"
            placeholder="alex.chen@msot.edu"
            icon={Mail}
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (errors.email) setErrors({ ...errors, email: null });
            }}
            error={Boolean(errors.email)}
            autoComplete="email"
          />
          {errors.email && (
            <p className="text-[11px] font-medium text-red-400 mt-1">{errors.email}</p>
          )}
        </div>

        {/* Password Field */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="login-password" required>
              Password
            </Label>
            <button
              type="button"
              onClick={() => onSwitchTab("forgot")}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors font-medium hover:underline"
            >
              Forgot password?
            </button>
          </div>
          <Input
            id="login-password"
            type="password"
            showPasswordToggle
            placeholder="••••••••••••"
            icon={Lock}
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (errors.password) setErrors({ ...errors, password: null });
            }}
            error={Boolean(errors.password)}
            autoComplete="current-password"
          />
          {errors.password && (
            <p className="text-[11px] font-medium text-red-400 mt-1">{errors.password}</p>
          )}
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
          className="w-full h-11 text-white font-semibold flex items-center justify-center gap-2 group"
        >
          <span>Sign In to Dashboard</span>
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Button>
      </form>

      {/* Footer Switch */}
      <div className="pt-2 text-center text-xs text-zinc-400">
        Don't have an account?{" "}
        <button
          type="button"
          onClick={() => onSwitchTab("register")}
          className="font-bold text-white hover:text-indigo-300 underline underline-offset-4 transition"
        >
          Create an account
        </button>
      </div>
    </div>
  );
}
