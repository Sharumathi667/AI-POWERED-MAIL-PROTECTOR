import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, 
  Mail, 
  LogIn, 
  AlertTriangle, 
  Cpu, 
  Settings, 
  LayoutDashboard,
  LogOut,
  User,
  ShieldCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/emails', label: 'Email Investigation', icon: Mail },
    { to: '/logins', label: 'Login Monitoring', icon: LogIn },
    { to: '/incidents', label: 'Incidents', icon: AlertTriangle },
    { to: '/models', label: 'ML Performance', icon: Cpu },
    { to: '/settings', label: 'Settings & Audit', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0a0f1d]/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Platform Info */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="h-10 w-10 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-sm shadow-sky-500/20">
              <ShieldAlert className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg text-slate-100 tracking-wider">ShieldSOC</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  PS 1.3
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Campus Phishing & Login Defense</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Auth / Profile Area */}
          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3 pl-2 border-l border-slate-800">
                <div className="flex items-center gap-2.5">
                  {user.picture_url ? (
                    <img 
                      src={user.picture_url} 
                      alt={user.full_name || user.email}
                      className="h-8 w-8 rounded-full border border-sky-500/40 object-cover shadow-sm"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-300">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                  <div className="hidden sm:block text-left leading-tight">
                    <p className="text-xs font-semibold text-slate-200 max-w-[130px] truncate">
                      {user.full_name || user.username}
                    </p>
                    <p className="text-[10px] text-slate-400 max-w-[130px] truncate font-mono">
                      {user.email}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={logout}
                  title="Sign Out"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <NavLink
                to="/login"
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-400 text-xs font-medium transition-all shadow-sm"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Sign In with Google</span>
              </NavLink>
            )}
          </div>

        </div>
      </div>
    </header>
  );
}
