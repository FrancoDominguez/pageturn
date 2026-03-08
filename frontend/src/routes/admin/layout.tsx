import { NavLink, Outlet } from 'react-router-dom';
import { clsx } from 'clsx';

// ── Sidebar nav items ─────────────────────────────────────────────────────────

const navItems = [
  {
    to: '/admin',
    label: 'Dashboard',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    ),
    end: true,
  },
  {
    to: '/admin/books',
    label: 'Books',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    to: '/admin/users',
    label: 'Users',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    to: '/admin/fines',
    label: 'Fines',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

// ── Admin Layout ──────────────────────────────────────────────────────────────

export default function AdminLayout() {
  return (
    <div className="flex min-h-screen bg-[#f9fafb]">
      {/* Sidebar */}
      <aside className="group fixed top-0 left-0 z-30 h-screen w-[48px] hover:w-[200px] bg-[#1e2330] transition-all duration-200 overflow-hidden flex flex-col">
        {/* Logo area */}
        <div className="flex items-center h-[48px] px-3 flex-shrink-0">
          <div className="w-6 h-6 rounded bg-primary flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold">P</span>
          </div>
          <span className="ml-2.5 text-white text-sm font-heading font-semibold whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            Admin
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 mt-2 flex flex-col gap-0.5 px-1.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center h-10 px-2.5 rounded-md transition-colors whitespace-nowrap relative',
                  isActive
                    ? 'text-white bg-white/10 before:absolute before:left-0 before:top-1.5 before:bottom-1.5 before:w-[2px] before:bg-primary before:rounded-full'
                    : 'text-gray-400 hover:text-white hover:bg-white/5',
                )
              }
            >
              <span className="flex-shrink-0">{item.icon}</span>
              <span className="ml-3 text-[13px] font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                {item.label}
              </span>
            </NavLink>
          ))}
        </nav>

        {/* Back to site */}
        <div className="px-1.5 pb-3">
          <NavLink
            to="/"
            className="flex items-center h-10 px-2.5 rounded-md text-gray-400 hover:text-white hover:bg-white/5 transition-colors whitespace-nowrap"
          >
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
            </svg>
            <span className="ml-3 text-[13px] font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              Back to Site
            </span>
          </NavLink>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 ml-[48px] min-h-screen">
        <Outlet />
      </div>
    </div>
  );
}
