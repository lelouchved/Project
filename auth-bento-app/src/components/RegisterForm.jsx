import React, { useState } from "react";
import { User, Mail, Lock, Check, ShieldCheck, ArrowRight } from "lucide-react";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import { Alert, AlertTitle, AlertDescription } from "./ui/alert";
import { AuthService } from "../lib/auth";

export function RegisterForm({ onSwitchTab, onRegisterSuccess }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  // Password strength calculator
  const calculateStrength = (pwd) => {
    if (!pwd) return { score: 0, label: "Empty", color: "bg-zinc-800" };
    let score = 0;
    if (pwd.length >= 8) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    if (score <= 1) return { score: 1, label: "Weak", color: "bg-red-500", text: "text-red-400" };
    if (score === 2) return { score: 2, label: "Fair", color: "bg-amber-500", text: "text-amber-400" };
    if (score === 3) return { score: 3, label: "Good", color: "bg-blue-500", text: "text-blue-400" };
    return { score: 4, label: "Strong", color: "bg-emerald-500", text: "text-emerald-400" };
  };

  const strength = calculateStrength(password);

  const validate = () => {
    const errs = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!name.trim()) {
      errs.name = "Full name is required.";
    } else if (name.trim().length < 2) {
      errs.name = "Name must be at least 2 characters.";
    }

    if (!email.trim()) {
      errs.email = "Email address is required.";
    } else if (!emailRegex.test(email.trim())) {
      errs.email = "Please enter a valid email address.";
    }

    if (!password) {
      errs.password = "Password is required.";
    } else if (password.length < 8) {
      errs.password = "Password must be at least 8 characters.";
    }

    if (!confirmPassword) {
      errs.confirmPassword = "Please confirm your password.";
    } else if (password !== confirmPassword) {
      errs.confirmPassword = "Passwords do not match.";
    }

    if (!agreedToTerms) {
      errs.terms = "You must agree to the Security Terms & Privacy Policy.";
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
      const { user } = await AuthService.signUp({ email, password, name });
      onRegisterSuccess(user);
    } catch (err) {
      setServerError(err.message || "Failed to create account. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setServerError("");
    setIsGoogleLoading(true);
    try {
      const { user } = await AuthService.signInWithGoogle();
      onRegisterSuccess(user);
    } catch (err) {
      setServerError(err.message || "Google registration failed.");
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {serverError && (
        <Alert variant="destructive">
          <AlertTitle>Registration Error</AlertTitle>
          <AlertDescription>{serverError}</AlertDescription>
        </Alert>
      )}

      {/* Google Sign Up Button */}
      <Button
        type="button"
        variant="outline"
        onClick={handleGoogleSignUp}
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
        <span>Sign up with Google</span>
      </Button>

      <Separator label="or register with credentials" />

      {/* Registration Form */}
      <form onSubmit={handleSubmit} className="space-y-3.5" noValidate>
        {/* Full Name */}
        <div className="space-y-1">
          <Label htmlFor="reg-name" required>
            Full Name
          </Label>
          <Input
            id="reg-name"
            placeholder="Alex Chen"
            icon={User}
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              if (errors.name) setErrors({ ...errors, name: null });
            }}
            error={Boolean(errors.name)}
            autoComplete="name"
          />
          {errors.name && (
            <p className="text-[11px] font-medium text-red-400">{errors.name}</p>
          )}
        </div>

        {/* Email */}
        <div className="space-y-1">
          <Label htmlFor="reg-email" required>
            Work / College Email
          </Label>
          <Input
            id="reg-email"
            type="email"
            placeholder="name@company.com"
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
            <p className="text-[11px] font-medium text-red-400">{errors.email}</p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <Label htmlFor="reg-password" required>
              Password (8+ characters)
            </Label>
            {password && (
              <span className={`text-[10px] font-mono font-bold ${strength.text}`}>
                {strength.label}
              </span>
            )}
          </div>
          <Input
            id="reg-password"
            type="password"
            showPasswordToggle
            placeholder="Create a strong password"
            icon={Lock}
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (errors.password) setErrors({ ...errors, password: null });
            }}
            error={Boolean(errors.password)}
            autoComplete="new-password"
          />

          {/* Password Strength Meter Bar */}
          {password && (
            <div className="pt-1 space-y-1">
              <div className="flex h-1.5 w-full gap-1 overflow-hidden rounded-full bg-zinc-800">
                <div
                  className={`h-full transition-all duration-300 ${strength.score >= 1 ? strength.color : "bg-transparent"}`}
                  style={{ width: "25%" }}
                />
                <div
                  className={`h-full transition-all duration-300 ${strength.score >= 2 ? strength.color : "bg-transparent"}`}
                  style={{ width: "25%" }}
                />
                <div
                  className={`h-full transition-all duration-300 ${strength.score >= 3 ? strength.color : "bg-transparent"}`}
                  style={{ width: "25%" }}
                />
                <div
                  className={`h-full transition-all duration-300 ${strength.score >= 4 ? strength.color : "bg-transparent"}`}
                  style={{ width: "25%" }}
                />
              </div>
            </div>
          )}

          {errors.password && (
            <p className="text-[11px] font-medium text-red-400">{errors.password}</p>
          )}
        </div>

        {/* Confirm Password */}
        <div className="space-y-1">
          <Label htmlFor="reg-confirm" required>
            Confirm Password
          </Label>
          <Input
            id="reg-confirm"
            type="password"
            showPasswordToggle
            placeholder="Re-enter password"
            icon={Lock}
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: null });
            }}
            error={Boolean(errors.confirmPassword)}
            autoComplete="new-password"
          />
          {errors.confirmPassword && (
            <p className="text-[11px] font-medium text-red-400">{errors.confirmPassword}</p>
          )}
        </div>

        {/* Terms Checkbox */}
        <div className="pt-1">
          <label className="flex items-start gap-2.5 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={agreedToTerms}
              onChange={(e) => {
                setAgreedToTerms(e.target.checked);
                if (errors.terms) setErrors({ ...errors, terms: null });
              }}
              className="mt-0.5 h-4 w-4 rounded border-zinc-700 bg-zinc-950 text-indigo-500 focus:ring-indigo-400 accent-indigo-500"
            />
            <span className="text-xs text-zinc-400 leading-tight">
              I accept the{" "}
              <span className="text-zinc-200 underline">Terms of Service</span> and acknowledge cryptographic storage.
            </span>
          </label>
          {errors.terms && (
            <p className="text-[11px] font-medium text-red-400 mt-1">{errors.terms}</p>
          )}
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
          className="w-full h-11 text-white font-semibold flex items-center justify-center gap-2 group mt-2"
        >
          <span>Create Secure Account</span>
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Button>
      </form>

      {/* Footer Switch */}
      <div className="pt-2 text-center text-xs text-zinc-400">
        Already registered?{" "}
        <button
          type="button"
          onClick={() => onSwitchTab("login")}
          className="font-bold text-white hover:text-indigo-300 underline underline-offset-4 transition"
        >
          Sign in here
        </button>
      </div>
    </div>
  );
}
