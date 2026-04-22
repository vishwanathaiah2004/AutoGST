"use client";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import Link from "next/link";
import { Zap, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<{ email: string; password: string }>();

  const onSubmit = async (data: { email: string; password: string }) => {
    setLoading(true);
    try {
      await login(data.email, data.password);
      toast.success("Welcome back!");
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-500 rounded-2xl mb-4 shadow-lg shadow-indigo-500/30">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">AutoGST Pro</h1>
          <p className="text-slate-400 text-sm mt-1">SmartTax AI · Sign in to continue</p>
        </div>

        {/* Card */}
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8 shadow-2xl">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <input
                {...register("email", { required: "Email is required", pattern: { value: /^\S+@\S+$/, message: "Invalid email" } })}
                type="email"
                placeholder="you@company.com"
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <input
                  {...register("password", { required: "Password is required" })}
                  type={showPw ? "text" : "password"}
                  placeholder="••••••••"
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2.5 pr-10 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-300">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2 shadow-lg shadow-indigo-600/30"
            >
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>

          <p className="text-center text-slate-400 text-sm mt-6">
            Don't have an account?{" "}
            <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-medium">
              Register
            </Link>
          </p>

          {/* Demo credentials */}
          <div className="mt-4 p-3 bg-indigo-900/30 border border-indigo-700/30 rounded-lg text-center">
            <p className="text-xs text-slate-400">Demo: <span className="text-indigo-300 font-mono">demo@autogst.pro</span> / <span className="text-indigo-300 font-mono">Demo@1234</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}
