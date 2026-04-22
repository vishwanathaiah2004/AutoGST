"use client";
import { useEffect, useState } from "react";
import { dashboardApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import StatCard from "@/components/ui/StatCard";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, PieChart, Pie, Cell
} from "recharts";
import {
  IndianRupee, TrendingUp, TrendingDown, AlertTriangle,
  Bell, Activity, PieChart as PieIcon, BarChart2
} from "lucide-react";
import toast from "react-hot-toast";

const fmt = (v: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v);

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.stats()
      .then(r => setStats(r.data))
      .catch(() => toast.error("Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
    </div>
  );

  if (!stats) return <div className="text-center text-slate-500 py-20">No data available</div>;

  const monthly = [...(stats.monthly_summary || [])].reverse();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome back, {user?.full_name?.split(" ")[0]} 👋
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          {user?.business_name || "Your Business"} · GSTIN: {user?.gstin || "Not set"}
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          title="Total Income"
          value={fmt(stats.total_income)}
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
        />
        <StatCard
          title="Total Expense"
          value={fmt(stats.total_expense)}
          icon={<TrendingDown className="w-5 h-5" />}
          color="red"
        />
        <StatCard
          title="Net Balance"
          value={fmt(stats.net_balance)}
          icon={<IndianRupee className="w-5 h-5" />}
          color={stats.net_balance >= 0 ? "indigo" : "amber"}
        />
        <StatCard
          title="Net GST Liability"
          value={fmt(stats.net_gst_liability)}
          subtitle={`Collected: ${fmt(stats.total_gst_collected)} · Paid: ${fmt(stats.total_gst_paid)}`}
          icon={<Activity className="w-5 h-5" />}
          color="blue"
        />
      </div>

      {/* Secondary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          title="Total Transactions"
          value={stats.transaction_count.toString()}
          icon={<BarChart2 className="w-5 h-5" />}
          color="indigo"
        />
        <StatCard
          title="Anomalies Detected"
          value={stats.anomaly_count.toString()}
          icon={<AlertTriangle className="w-5 h-5" />}
          color={stats.anomaly_count > 0 ? "amber" : "green"}
        />
        <StatCard
          title="Pending Alerts"
          value={stats.pending_alerts.toString()}
          icon={<Bell className="w-5 h-5" />}
          color={stats.pending_alerts > 0 ? "red" : "green"}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Area Chart */}
        <div className="col-span-2 card p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-indigo-500" /> Monthly Income vs Expense
          </h2>
          {monthly.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={monthly}>
                <defs>
                  <linearGradient id="income" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="expense" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: any) => fmt(v)} />
                <Legend />
                <Area type="monotone" dataKey="income" stroke="#22c55e" fill="url(#income)" name="Income" />
                <Area type="monotone" dataKey="expense" stroke="#ef4444" fill="url(#expense)" name="Expense" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">No monthly data yet</div>
          )}
        </div>

        {/* Pie Chart */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-indigo-500" /> Top Categories
          </h2>
          {stats.top_categories?.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={stats.top_categories} dataKey="total" nameKey="category" cx="50%" cy="50%" innerRadius={40} outerRadius={70}>
                    {stats.top_categories.map((_: any, i: number) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: any) => fmt(v)} />
                </PieChart>
              </ResponsiveContainer>
              <ul className="space-y-1 mt-2">
                {stats.top_categories.slice(0, 4).map((c: any, i: number) => (
                  <li key={i} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                      <span className="text-slate-600 truncate max-w-[100px]">{c.category}</span>
                    </span>
                    <span className="font-medium text-slate-800">{fmt(c.total)}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">No data</div>
          )}
        </div>
      </div>

      {/* GST Summary Bar */}
      {monthly.length > 0 && (
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-500" /> Monthly GST Collection
          </h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={monthly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: any) => fmt(v)} />
              <Bar dataKey="gst" fill="#6366f1" radius={[4, 4, 0, 0]} name="GST Collected" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
