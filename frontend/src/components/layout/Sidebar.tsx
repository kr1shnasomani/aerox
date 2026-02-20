import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Zap, Users, MessageSquare } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/process', label: 'Process Booking', icon: Zap },
  { to: '/agencies', label: 'Agencies', icon: Users },
  { to: '/negotiate', label: 'Negotiate', icon: MessageSquare },
];

export default function Sidebar() {
  return (
    <aside className="w-64 h-screen fixed left-0 top-0 flex flex-col border-r border-[#2d2d6b] bg-[#0a0a1a]">
      {/* Logo */}
      <div className="p-6 border-b border-[#2d2d6b]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#8b5cf6] to-[#3b82f6] flex items-center justify-center font-bold text-white text-lg">
            A
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide">AEROX</h1>
            <p className="text-[10px] text-[#8888bb] uppercase tracking-widest">Risk Orchestrator</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all ${
                isActive
                  ? 'bg-[#8b5cf6]/15 text-[#8b5cf6] font-medium'
                  : 'text-[#8888bb] hover:text-white hover:bg-white/5'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[#2d2d6b]">
        <p className="text-[10px] text-[#555] text-center">
          AEROX v1.0 - Hackathon Build
        </p>
      </div>
    </aside>
  );
}
