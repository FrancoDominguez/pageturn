import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { apiFetch } from '../../lib/api';
import { useToast } from '../../components/Toast';
import QueryError from '../../components/QueryError';

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminFineUser {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

interface AdminFine {
  id: string;
  user: AdminFineUser;
  book_title: string;
  amount: number;
  reason: 'late_return' | 'lost_item' | 'damaged_item';
  status: 'pending' | 'paid' | 'waived';
  created_at: string;
}

interface AdminFinesResponse {
  fines: AdminFine[];
  total: number;
  total_outstanding_amount: number;
}

const filterTabs = ['All', 'Pending', 'Paid', 'Waived'] as const;

const filterMap: Record<string, string | undefined> = {
  All: undefined,
  Pending: 'pending',
  Paid: 'paid',
  Waived: 'waived',
};

const reasonLabels: Record<string, string> = {
  late_return: 'Late Return',
  lost_item: 'Lost Item',
  damaged_item: 'Damaged',
};

const statusConfig: Record<string, { color: string; dot: string; label: string }> = {
  pending: { color: 'text-amber-600', dot: 'bg-amber-500', label: 'Pending' },
  paid: { color: 'text-emerald-600', dot: 'bg-emerald-500', label: 'Paid' },
  waived: { color: 'text-blue-600', dot: 'bg-blue-500', label: 'Waived' },
};

// ── Admin Fines Page ──────────────────────────────────────────────────────────

export default function AdminFinesPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<string>('All');

  const status = filterMap[activeTab];
  const limit = 25;

  // Fetch fines
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin', 'fines', page, status],
    queryFn: () =>
      apiFetch<AdminFinesResponse>('/api/admin/fines', {
        params: {
          page: String(page),
          limit: String(limit),
          status,
        },
      }),
  });

  const fines = data?.fines ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / limit)) : 1;

  // Waive mutation
  const waiveMutation = useMutation({
    mutationFn: (fineId: string) =>
      apiFetch(`/api/admin/fines/${fineId}/waive`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'fines'] });
      toast('Fine waived', 'success');
    },
    onError: () => {
      toast('Failed to waive fine', 'error');
    },
  });

  function handleWaive(fine: AdminFine) {
    if (window.confirm(`Waive $${fine.amount.toFixed(2)} fine for "${fine.book_title}"?`)) {
      waiveMutation.mutate(fine.id);
    }
  }

  return (
    <div className="text-[13px]">
      {/* KPI bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center divide-x divide-gray-200">
          <div className="pr-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Outstanding</div>
            <div className="text-2xl font-heading font-bold text-primary">
              {data ? `$${data.total_outstanding_amount.toFixed(2)}` : '--'}
            </div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Total Fines</div>
            <div className="text-2xl font-heading font-bold">
              {data?.total?.toLocaleString() ?? '--'}
            </div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="px-6 py-4 flex items-center gap-1">
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

      {/* Table */}
      <div className="px-6">
        <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">User</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Book</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Reason</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Amount</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Status</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Date</th>
                <th className="text-right text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {isError ? (
                <tr>
                  <td colSpan={7}>
                    <QueryError message="Failed to load fines." onRetry={() => refetch()} />
                  </td>
                </tr>
              ) : isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-100 h-[44px]">
                    <td className="px-4" colSpan={7}>
                      <div className="h-3 w-2/3 bg-gray-100 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : fines.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                    No fines found
                  </td>
                </tr>
              ) : (
                fines.map((fine) => {
                  const sc = statusConfig[fine.status] ?? statusConfig.pending;
                  return (
                    <tr key={fine.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50 group">
                      <td className="px-4">
                        <div className="font-medium text-gray-900">
                          {[fine.user.first_name, fine.user.last_name].filter(Boolean).join(' ') || fine.user.email}
                        </div>
                        <div className="text-gray-400">{fine.user.email}</div>
                      </td>
                      <td className="px-4">
                        <div className="font-medium text-gray-900">{fine.book_title}</div>
                      </td>
                      <td className="px-4 text-gray-600">
                        {reasonLabels[fine.reason] ?? fine.reason}
                      </td>
                      <td className="px-4">
                        <span className={clsx(
                          'font-medium',
                          fine.status === 'pending' ? 'text-primary' : 'text-gray-400',
                        )}>
                          ${fine.amount.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-4">
                        <span className={clsx('inline-flex items-center gap-1.5', sc.color)}>
                          <span className={clsx('w-[6px] h-[6px] rounded-full', sc.dot)} />
                          {sc.label}
                        </span>
                      </td>
                      <td className="px-4 text-gray-500">
                        {new Date(fine.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 text-right">
                        {fine.status === 'pending' && (
                          <button
                            type="button"
                            onClick={() => handleWaive(fine)}
                            disabled={waiveMutation.isPending}
                            className="opacity-0 group-hover:opacity-100 text-primary text-[13px] font-medium hover:underline cursor-pointer transition-opacity"
                          >
                            Waive
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
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
