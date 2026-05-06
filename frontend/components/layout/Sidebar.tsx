"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  LayoutDashboard, ArrowLeftRight, Upload, FileBarChart2,
  Calculator, Bell, LogOut, Zap, ChevronRight, Sparkles, Menu, X
} from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/upload", label: "Upload & OCR", icon: Upload },
  { href: "/reports", label: "GST Reports", icon: FileBarChart2 },
  { href: "/tax-assistant", label: "Tax Calculator", icon: Calculator },
  { href: "/ai-assistant", label: "AI Assistant", icon: Sparkles },
  { href: "/alerts", label: "Alerts", icon: Bell },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <aside style={{
          position: 'fixed', top: 0, left: 0,
          width: '256px', height: '100vh',
          backgroundColor: '#0f172a',
          display: 'flex', flexDirection: 'column',
          zIndex: 30,
        }}>
          <SidebarInner pathname={pathname} user={user} logout={logout} onClose={() => {}} showClose={false} />
        </aside>
      </div>

      {/* Mobile top bar */}
      <div className="lg:hidden" style={{
        position: 'fixed', top: 0, left: 0, right: 0,
        height:'56px',
        backgroundColor: '#0f172a',
        borderBottom: '1px solid #334155',
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '0 16px', zIndex: 40,
      }}>
        <button onClick={() => setOpen(true)} style={{ color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}>
          <Menu className="w-5 h-5" />
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '24px', height: '24px', backgroundColor: '#6366f1',
            borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap className="w-3 h-3 text-white" />
          </div>
          <p style={{ color: 'white', fontWeight: 'bold', fontSize: '14px', margin: 0 }}>AutoGST Pro</p>
        </div>
      </div>

      {/* Mobile drawer */}
      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{
            position: 'fixed', inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 998,
          }} />
          <aside style={{
            position: 'fixed', top: 0, left: 0,
            width: '256px', height: '100vh',
            backgroundColor: '#0f172a',
            display: 'flex', flexDirection: 'column',
            zIndex: 999,
          }}>
            <SidebarInner pathname={pathname} user={user} logout={logout} onClose={() => setOpen(false)} showClose={true} />
          </aside>
        </>
      )}
    </>
  );
}

function SidebarInner({ pathname, user, logout, onClose, showClose }: {
  pathname: string;
  user: any;
  logout: () => void;
  onClose: () => void;
  showClose: boolean;
}) {
  return (
    <>
      {/* Logo */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '20px 24px', borderBottom: '1px solid #334155'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px', backgroundColor: '#6366f1',
            borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <p style={{ color: 'white', fontWeight: 'bold', fontSize: '14px', margin: 0, lineHeight: '1' }}>AutoGST Pro</p>
            <p style={{ color: '#94a3b8', fontSize: '12px', margin: '2px 0 0 0' }}>SmartTax AI</p>
          </div>
        </div>
        {showClose && (
          <button onClick={onClose} style={{ color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}>
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href} onClick={onClose} style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '10px 12px', borderRadius: '8px',
              marginBottom: '2px', textDecoration: 'none',
              fontSize: '14px', fontWeight: 500,
              backgroundColor: active ? '#4f46e5' : 'transparent',
              color: active ? 'white' : '#94a3b8',
            }}>
              <Icon style={{ width: '16px', height: '16px', flexShrink: 0 }} />
              <span style={{ flex: 1 }}>{label}</span>
              {active && <ChevronRight style={{ width: '12px', height: '12px', opacity: 0.6 }} />}
            </Link>
          );
        })}
      </nav>

      {/* User + Logout */}
      <div style={{ padding: '16px 12px', borderTop: '1px solid #334155' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 12px', marginBottom: '4px' }}>
          <div style={{
            width: '32px', height: '32px', backgroundColor: '#6366f1',
            borderRadius: '50%', display: 'flex', alignItems: 'center',
            justifyContent: 'center', color: 'white', fontSize: '12px',
            fontWeight: 'bold', flexShrink: 0
          }}>
            {user?.full_name?.[0]?.toUpperCase() ?? "U"}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ color: 'white', fontSize: '12px', fontWeight: 500, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.full_name}
            </p>
            <p style={{ color: '#94a3b8', fontSize: '12px', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.email}
            </p>
          </div>
        </div>
        <button onClick={logout} style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: '12px',
          padding: '8px 12px', borderRadius: '8px', border: 'none',
          backgroundColor: 'transparent', color: '#94a3b8',
          cursor: 'pointer', fontSize: '14px',
        }}>
          <LogOut style={{ width: '16px', height: '16px' }} />
          <span>Logout</span>
        </button>
      </div>
    </>
  );
}