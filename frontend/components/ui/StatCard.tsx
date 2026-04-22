import clsx from "clsx";
import { TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ReactNode;
  color?: "green" | "red" | "blue" | "amber" | "indigo";
}

const colorMap = {
  green: { bg: "bg-green-50", icon: "bg-green-100 text-green-600", value: "text-green-700" },
  red: { bg: "bg-red-50", icon: "bg-red-100 text-red-600", value: "text-red-700" },
  blue: { bg: "bg-blue-50", icon: "bg-blue-100 text-blue-600", value: "text-blue-700" },
  amber: { bg: "bg-amber-50", icon: "bg-amber-100 text-amber-600", value: "text-amber-700" },
  indigo: { bg: "bg-indigo-50", icon: "bg-indigo-100 text-indigo-600", value: "text-indigo-700" },
};

export default function StatCard({ title, value, subtitle, trend, icon, color = "indigo" }: StatCardProps) {
  const c = colorMap[color];
  return (
    <div className={clsx("card p-5", c.bg)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{title}</p>
          <p className={clsx("text-2xl font-bold mt-1", c.value)}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        {icon && (
          <div className={clsx("w-10 h-10 rounded-lg flex items-center justify-center", c.icon)}>
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <div className={clsx("flex items-center gap-1 mt-3 text-xs font-medium", trend === "up" ? "text-green-600" : trend === "down" ? "text-red-600" : "text-slate-500")}>
          {trend === "up" ? <TrendingUp className="w-3 h-3" /> : trend === "down" ? <TrendingDown className="w-3 h-3" /> : null}
        </div>
      )}
    </div>
  );
}
