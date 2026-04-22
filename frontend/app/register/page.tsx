"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { authApi } from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";
import { Zap } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<any>();

  const onSubmit = async (data: any) => {
    setLoading(true);
    try {
      await authApi.register(data);
      toast.success("Account created! Please sign in.");
      router.push("/login");
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-500 rounded-2xl mb-4">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Create Account</h1>
          <p className="text-slate-400 text-sm mt-1">AutoGST Pro + SmartTax AI</p>
        </div>

        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {[
              { name: "full_name", label: "Full Name", type: "text", placeholder: "Rahul Sharma", rules: { required: "Required", minLength: { value: 2, message: "Min 2 chars" } } },
              { name: "email", label: "Email", type: "email", placeholder: "you@company.com", rules: { required: "Required", pattern: { value: /^\S+@\S+$/, message: "Invalid email" } } },
              { name: "password", label: "Password", type: "password", placeholder: "Min 8 characters", rules: { required: "Required", minLength: { value: 8, message: "Min 8 characters" } } },
              { name: "business_name", label: "Business Name", type: "text", placeholder: "Acme India Pvt Ltd", rules: {} },
              { name: "gstin", label: "GSTIN (optional)", type: "text", placeholder: "27AAPFU0939F1ZV", rules: {} },
            ].map(({ name, label, type, placeholder, rules }) => (
              <div key={name}>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">{label}</label>
                <input
                  {...register(name as any, rules)}
                  type={type}
                  placeholder={placeholder}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {(errors as any)[name] && (
                  <p className="text-red-400 text-xs mt-1">{(errors as any)[name]?.message}</p>
                )}
              </div>
            ))}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition-all disabled:opacity-50 mt-2"
            >
              {loading ? "Creating account…" : "Create Account"}
            </button>
          </form>
          <p className="text-center text-slate-400 text-sm mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
