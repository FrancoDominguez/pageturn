import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiFetch } from '../../lib/api';

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminStats {
  total_books: number;
  total_users: number;
  active_loans: number;
  overdue_loans: number;
  outstanding_fines: number;
  collected_fines: number;
  new_users_this_month: number;
  books_added_this_month: number;
}

// ── Admin Dashboard ───────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => apiFetch<AdminStats>('/api/admin/stats'),
  });

  return (
    <div className="text-[13px]">
      {/* KPI bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center divide-x divide-gray-200">
          <div className="pr-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Total Books</div>
            <div className="text-2xl font-heading font-bold">{isLoading ? '--' : stats?.total_books?.toLocaleString()}</div>
            <div className="text-[12px] text-gray-400">{isLoading ? '' : `+${stats?.books_added_this_month ?? 0} this month`}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Total Users</div>
            <div className="text-2xl font-heading font-bold">{isLoading ? '--' : stats?.total_users?.toLocaleString()}</div>
            <div className="text-[12px] text-gray-400">{isLoading ? '' : `+${stats?.new_users_this_month ?? 0} this month`}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Active Loans</div>
            <div className="text-2xl font-heading font-bold">{isLoading ? '--' : stats?.active_loans?.toLocaleString()}</div>
            <div className="text-[12px] text-gray-400">{isLoading ? '' : `${stats?.overdue_loans ?? 0} overdue`}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Outstanding Fines</div>
            <div className="text-2xl font-heading font-bold text-primary">{isLoading ? '--' : `$${(stats?.outstanding_fines ?? 0).toFixed(2)}`}</div>
            <div className="text-[12px] text-gray-400">{isLoading ? '' : `$${(stats?.collected_fines ?? 0).toFixed(2)} collected`}</div>
          </div>
        </div>
      </div>

      {/* Page content */}
      <div className="px-6 py-6">
        <h1 className="font-heading font-bold text-xl text-gray-900 mb-1">Dashboard</h1>
        <p className="text-gray-500 mb-6">Overview of your library system</p>

        {/* Quick actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            to="/admin/books"
            className="bg-white border border-gray-200 rounded-[8px] p-5 hover:border-gray-300 hover:shadow-sm transition-all group"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-[6px] bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-100 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <span className="font-heading font-semibold text-gray-900">Manage Books</span>
            </div>
            <p className="text-gray-500 text-[13px]">Add, edit, and manage your catalogue inventory</p>
          </Link>

          <Link
            to="/admin/users"
            className="bg-white border border-gray-200 rounded-[8px] p-5 hover:border-gray-300 hover:shadow-sm transition-all group"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-[6px] bg-emerald-50 flex items-center justify-center text-emerald-600 group-hover:bg-emerald-100 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <span className="font-heading font-semibold text-gray-900">Manage Users</span>
            </div>
            <p className="text-gray-500 text-[13px]">View user accounts, roles, and activity</p>
          </Link>

          <Link
            to="/admin/fines"
            className="bg-white border border-gray-200 rounded-[8px] p-5 hover:border-gray-300 hover:shadow-sm transition-all group"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-[6px] bg-amber-50 flex items-center justify-center text-amber-600 group-hover:bg-amber-100 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="font-heading font-semibold text-gray-900">Manage Fines</span>
            </div>
            <p className="text-gray-500 text-[13px]">Review and manage outstanding fines and payments</p>
          </Link>
        </div>

        {/* Overdue loans alert */}
        {stats && stats.overdue_loans > 0 && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-[6px] px-4 py-3 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
            <p className="text-[13px] text-red-800">
              <span className="font-semibold">{stats.overdue_loans} overdue loan{stats.overdue_loans !== 1 ? 's' : ''}</span> require attention.{' '}
              <Link to="/admin/books" className="underline hover:no-underline">
                View details
              </Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
