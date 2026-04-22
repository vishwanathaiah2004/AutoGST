"use client";
import { useEffect, useState } from "react";
import { alertsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Bell, CheckCheck, AlertTriangle, Info, XCircle } from "lucide-react";
import clsx from "clsx";

const icons: any = { info: Info, warning: AlertTriangle, critical: XCircle };
const colors: any = { info: "text-blue-500 bg-blue-50", warning: "text-amber-500 bg-amber-50", critical: "text-red-500 bg-red-50" };

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const fetch = async () => {
    setLoading(true);
    try {
      const r = await alertsApi.list(unreadOnly);
      setAlerts(r.data);
    } catch { toast.error("Failed to load alerts"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, [unreadOnly]);

  const markRead = async (id: number) => {
    await alertsApi.markRead(id);
    setAlerts(a => a.map(x => x.id === id ? { ...x, is_read: true } : x));
  };

  const markAll = async () => {
    await alertsApi.markAllRead();
    setAlerts(a => a.map(x => ({ ...x, is_read: true })));
    toast.success("All alerts marked as read");
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  return (
    <div className="space-y-5 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
          <p className="text-slate-500 text-sm">{unreadCount} unread</p>
        </div>
        <div className="flex gap-3 items-center">
          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
            <input type="checkbox" checked={unreadOnly} onChange={e => setUnreadOnly(e.target.checked)} className="rounded" />
            Unread only
          </label>
          {unreadCount > 0 && (
            <button onClick={markAll} className="btn-secondary flex items-center gap-2 text-sm">
              <CheckCheck className="w-4 h-4" /> Mark all read
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400">Loading…</div>
      ) : alerts.length === 0 ? (
        <div className="card p-16 text-center">
          <Bell className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">No alerts{unreadOnly ? " unread" : ""}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map(alert => {
            const Icon = icons[alert.severity] || Info;
            return (
              <div
                key={alert.id}
                className={clsx(
                  "card p-4 flex gap-4 transition-all",
                  !alert.is_read && "border-indigo-200 shadow-sm"
                )}
              >
                <div className={clsx("w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5", colors[alert.severity])}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <p className={clsx("font-medium text-sm", !alert.is_read ? "text-slate-900" : "text-slate-600")}>{alert.title}</p>
                    {!alert.is_read && (
                      <button onClick={() => markRead(alert.id)} className="text-xs text-indigo-500 hover:text-indigo-700 whitespace-nowrap flex-shrink-0">Mark read</button>
                    )}
                  </div>
                  <p className="text-sm text-slate-500 mt-0.5">{alert.message}</p>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-xs text-slate-400">{new Date(alert.created_at).toLocaleString("en-IN")}</span>
                    {alert.category && <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{alert.category}</span>}
                    {!alert.is_read && <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
