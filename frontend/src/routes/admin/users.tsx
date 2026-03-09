import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { apiFetch } from '../../lib/api';
import QueryError from '../../components/QueryError';

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminUser {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: 'user' | 'admin';
  active_loans: number;
  outstanding_fines: number;
  created_at: string;
}

interface AdminUsersResponse {
  users: AdminUser[];
  total: number;
  page: number;
}

const filterTabs = ['All', 'Admins'] as const;

const roleMap: Record<string, string | undefined> = {
  All: undefined,
  Admins: 'admin',
};

// ── Admin Users Page ──────────────────────────────────────────────────────────

export default function AdminUsersPage() {
  const navigate = useNavigate();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<string>('All');
  const limit = 25;

  const role = roleMap[activeTab];

  // Fetch users
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin', 'users', page, search, role],
    queryFn: () =>
      apiFetch<AdminUsersResponse>('/api/admin/users', {
        params: {
          page: String(page),
          limit: String(limit),
          q: search || undefined,
          role,
        },
      }),
  });

  const users = data?.users ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / limit)) : 1;

  function displayName(u: AdminUser): string {
    const parts = [u.first_name, u.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(' ') : u.email;
  }

  return (
    <div className="text-[13px]">
      {/* KPI bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center divide-x divide-gray-200">
          <div className="pr-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Total Users</div>
            <div className="text-2xl font-heading font-bold">{data?.total?.toLocaleString() ?? '--'}</div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="px-6 py-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-1">
          {filterTabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => { setActiveTab(tab); setPage(1); }}
              className={clsx(
                'px-3 py-1.5 text-[13px] font-medium border-b-2 transition-colors cursor-pointer',
                activeTab === tab
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700',
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="Search users..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="w-[200px] h-[32px] px-3 text-[13px] bg-white border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
        />
      </div>

      {/* Table */}
      <div className="px-6">
        <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Name</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Email</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Role</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Active Loans</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Outstanding Fines</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Joined</th>
              </tr>
            </thead>
            <tbody>
              {isError ? (
                <tr>
                  <td colSpan={6}>
                    <QueryError message="Failed to load users." onRetry={() => refetch()} />
                  </td>
                </tr>
              ) : isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-100 h-[44px]">
                    <td className="px-4" colSpan={6}>
                      <div className="h-3 w-2/3 bg-gray-100 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr
                    key={user.id}
                    onClick={() => navigate(`/admin/users/${user.id}`)}
                    className="border-b border-gray-100 h-[44px] hover:bg-gray-50 cursor-pointer group"
                  >
                    <td className="px-4">
                      <span className="font-medium text-gray-900">{displayName(user)}</span>
                    </td>
                    <td className="px-4 text-gray-600">{user.email}</td>
                    <td className="px-4">
                      <span className={clsx(
                        'inline-flex items-center gap-1.5',
                        user.role === 'admin' ? 'text-purple-600' : 'text-gray-500',
                      )}>
                        <span className={clsx(
                          'w-[6px] h-[6px] rounded-full',
                          user.role === 'admin' ? 'bg-purple-500' : 'bg-gray-300',
                        )} />
                        {user.role === 'admin' ? 'Admin' : 'User'}
                      </span>
                    </td>
                    <td className="px-4 text-gray-600">{user.active_loans}</td>
                    <td className="px-4">
                      {Number(user.outstanding_fines) > 0 ? (
                        <span className="text-primary font-medium">${Number(user.outstanding_fines).toFixed(2)}</span>
                      ) : (
                        <span className="text-gray-300">$0.00</span>
                      )}
                    </td>
                    <td className="px-4 text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between py-4">
            <div className="text-gray-400">
              Page {page} of {totalPages} ({data?.total ?? 0} total)
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className={clsx(
                  'px-3 py-1.5 text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer',
                  page <= 1 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600 hover:bg-white',
                )}
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className={clsx(
                  'px-3 py-1.5 text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer',
                  page >= totalPages ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600 hover:bg-white',
                )}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
