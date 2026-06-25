import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  BarChart3,
  Users,
  Inbox,
  PhoneCall,
  Radio,
  PlugZap,
  LogOut,
  X,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: typeof LayoutDashboard;
}

const NAV: NavItem[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "agents", label: "Agents", icon: Users },
  { id: "leads", label: "Enquiries", icon: Inbox },
  { id: "calls", label: "Calls", icon: PhoneCall },
  { id: "sessions", label: "Sessions", icon: Radio },
  { id: "integrations", label: "Integrations", icon: PlugZap },
];

interface SidebarProps {
  username: string | null;
  open: boolean;
  onClose: () => void;
  onLogout: () => void;
}

export function Sidebar({ username, open, onClose, onLogout }: SidebarProps) {
  const [active, setActive] = useState("overview");

  useEffect(() => {
    // active = the last section whose top has scrolled past the band under the top bar
    function update() {
      let current = NAV[0].id;
      for (const { id } of NAV) {
        const el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top <= 120) current = id;
      }
      setActive(current);
    }
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);

  return (
    <>
      <div
        className={`sidebar-scrim ${open ? "is-open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className={`sidebar ${open ? "is-open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-mark">
            <Radio size={18} />
          </div>
          <div className="sidebar-brand-text">
            <strong>Voice Ops</strong>
            <span>Lead response</span>
          </div>
          <button className="sidebar-close" type="button" onClick={onClose} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Sections">
          {NAV.map(({ id, label, icon: Icon }) => (
            <a
              key={id}
              href={`#${id}`}
              className={active === id ? "is-active" : ""}
              onClick={onClose}
            >
              <Icon size={17} />
              <span>{label}</span>
            </a>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{(username ?? "op").slice(0, 1).toUpperCase()}</div>
            <div className="sidebar-user-text">
              <strong>{username ?? "operator"}</strong>
              <span>Operator</span>
            </div>
          </div>
          <button className="ghost-button sidebar-logout" type="button" onClick={onLogout}>
            <LogOut size={15} />
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}
