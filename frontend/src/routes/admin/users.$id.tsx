import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { apiFetch } from '../../lib/api';
import { useToast } from '../../components/Toast';
import QueryError from '../../components/QueryError';

// ── Types matching actual backend response ───────────────────────────────────

interface UserInfo {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: 'user' | 'admin';
  max_loans: number;
  created_at: string;
}

interface ActiveLoan {
  id: string;
  book_title: string;
  due_date: string;
  status: string;
}

interface LoanHistoryItem {
  id: string;
  book_title: string;
  returned_at: string | null;
}

interface UserFine {
  id: string;
  amount: number;
  reason: string;
  status: string;
}

interface UserReview {
  id: string;
  book_title: string;
  rating: number;
}

interface AdminUserDetailResponse {
  user: UserInfo;
  active_loans: ActiveLoan[];
  loan_history: LoanHistoryItem[];
  reservations: { id: string; book_title: string; status: string; queue_position: number }[];
  fines: UserFine[];
  reviews: UserReview[];
}

const tabs = ['Loans', 'Fines', 'Reviews'] as const;
type Tab = (typeof tabs)[number];

const reasonLabels: Record<string, string> = {
  late_return: 'Late Return',
  lost_item: 'Lost Item',
  damaged_item: 'Damaged',
};

const fineStatusConfig: Record<string, { color: string; dot: string; label: string }> = {
  pending: { color: 'text-amber-600', dot: 'bg-amber-500', label: 'Pending' },
  paid: { color: 'text-emerald-600', dot: 'bg-emerald-500', label: 'Paid' },
  waived: { color: 'text-blue-600', dot: 'bg-blue-500', label: 'Waived' },
};

// ── Admin User Detail ─────────────────────────────────────────────────────────

export default function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('Loans');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin', 'users', id],
    queryFn: () => apiFetch<AdminUserDetailResponse>(`/api/admin/users/${id}`),
    enabled: !!id,
  });

  // Promote / Demote
  const roleMutation = useMutation({
    mutationFn: (newRole: 'user' | 'admin') =>
      apiFetch(`/api/admin/users/${id}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', id] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast('Role updated', 'success');
    },
    onError: () => toast('Failed to update role', 'error'),
  });

  // Return a loan
  const returnMutation = useMutation({
    mutationFn: (loanId: string) =>
      apiFetch(`/api/admin/loans/${loanId}/return`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', id] });
      toast('Book returned', 'success');
    },
    onError: () => toast('Failed to return book', 'error'),
  });

  // Mark lost
  const lostMutation = useMutation({
    mutationFn: (loanId: string) =>
      apiFetch(`/api/admin/loans/${loanId}/lost`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', id] });
      toast('Marked as lost', 'success');
    },
    onError: () => toast('Failed to mark as lost', 'error'),
  });

  // Waive fine
  const waiveMutation = useMutation({
    mutationFn: (fineId: string) =>
      apiFetch(`/api/admin/fines/${fineId}/waive`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', id] });
      toast('Fine waived', 'success');
    },
    onError: () => toast('Failed to waive fine', 'error'),
  });

  if (isError) {
    return (
      <div className="text-[13px] px-6 py-6">
        <QueryError message="Failed to load user details." onRetry={() => refetch()} />
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="text-[13px]">
        <div className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex items-center divide-x divide-gray-200">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className={clsx(i === 0 ? 'pr-8' : 'px-8')}>
                <div className="h-3 w-16 bg-gray-100 rounded animate-pulse mb-1" />
                <div className="h-6 w-12 bg-gray-100 rounded animate-pulse" />
              </div>
            ))}
          </div>
        </div>
        <div className="px-6 py-6">
          <div className="h-6 w-48 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  const user = data.user;
  const { active_loans, loan_history, fines, reviews } = data;
  const allLoans = [...active_loans.map((l) => ({ ...l, type: 'active' as const }))];
  const pendingFines = fines.filter((f) => f.status === 'pending');
  const outstandingAmount = pendingFines.reduce((sum, f) => sum + Number(f.amount), 0);

  const displayName = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email;
  const initial = (user.first_name?.[0] ?? user.email[0] ?? '?').toUpperCase();

  return (
    <div className="text-[13px]">
      {/* KPI bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center divide-x divide-gray-200">
          <div className="pr-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Active Loans</div>
            <div className="text-2xl font-heading font-bold">{active_loans.length}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Returned</div>
            <div className="text-2xl font-heading font-bold">{loan_history.length}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Outstanding Fines</div>
            <div className="text-2xl font-heading font-bold text-primary">${outstandingAmount.toFixed(2)}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Reviews</div>
            <div className="text-2xl font-heading font-bold">{reviews.length}</div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-1.5 text-gray-400 mb-4">
          <Link to="/admin/users" className="hover:text-gray-600 transition-colors">Users</Link>
          <span>/</span>
          <span className="text-gray-700">{displayName}</span>
        </div>

        {/* User info bar */}
        <div className="bg-white border border-gray-200 rounded-[8px] px-5 py-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 font-heading font-bold text-sm">
              {initial}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-heading font-semibold text-gray-900 text-[15px]">{displayName}</span>
                <span className={clsx(
                  'inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full',
                  user.role === 'admin'
                    ? 'bg-purple-50 text-purple-700'
                    : 'bg-gray-100 text-gray-600',
                )}>
                  {user.role === 'admin' ? 'Admin' : 'User'}
                </span>
              </div>
              <div className="text-gray-400 mt-0.5">
                {user.email} &middot; Joined {new Date(user.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => roleMutation.mutate(user.role === 'admin' ? 'user' : 'admin')}
            disabled={roleMutation.isPending}
            className={clsx(
              'h-[32px] px-4 text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer border',
              user.role === 'admin'
                ? 'border-red-200 text-red-600 hover:bg-red-50'
                : 'border-purple-200 text-purple-600 hover:bg-purple-50',
              roleMutation.isPending && 'opacity-50',
            )}
          >
            {roleMutation.isPending
              ? 'Updating...'
              : user.role === 'admin'
                ? 'Demote to User'
                : 'Promote to Admin'}
          </button>
        </div>

        {/* Tab bar */}
        <div className="flex items-center gap-1 mb-4 border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={clsx(
                'px-4 py-2 text-[13px] font-medium border-b-2 -mb-px transition-colors cursor-pointer',
                activeTab === tab
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700',
              )}
            >
              {tab}
              {tab === 'Loans' && active_loans.length > 0 && (
                <span className="ml-1.5 text-[11px] text-gray-400">({active_loans.length})</span>
              )}
              {tab === 'Fines' && fines.length > 0 && (
                <span className="ml-1.5 text-[11px] text-gray-400">({fines.length})</span>
              )}
              {tab === 'Reviews' && reviews.length > 0 && (
                <span className="ml-1.5 text-[11px] text-gray-400">({reviews.length})</span>
              )}
            </button>
          ))}
        </div>

        {/* Loans tab */}
        {activeTab === 'Loans' && (
          <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
            {allLoans.length === 0 && loan_history.length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">No loans</div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Book</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Due / Returned</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Status</th>
                    <th className="text-right text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {active_loans.map((loan) => (
                    <tr key={loan.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50 group">
                      <td className="px-4 font-medium text-gray-900">{loan.book_title}</td>
                      <td className="px-4 text-gray-600">{new Date(loan.due_date).toLocaleDateString()}</td>
                      <td className="px-4">
                        <span className="inline-flex items-center gap-1.5 text-emerald-600">
                          <span className="w-[6px] h-[6px] rounded-full bg-emerald-500" />
                          Active
                        </span>
                      </td>
                      <td className="px-4 text-right">
                        <span className="inline-flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => returnMutation.mutate(loan.id)}
                            disabled={returnMutation.isPending}
                            className="text-primary text-[13px] font-medium hover:underline cursor-pointer"
                          >
                            Return
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              if (window.confirm(`Mark "${loan.book_title}" as lost? This will generate a fine.`)) {
                                lostMutation.mutate(loan.id);
                              }
                            }}
                            disabled={lostMutation.isPending}
                            className="text-red-600 text-[13px] font-medium hover:underline cursor-pointer"
                          >
                            Mark Lost
                          </button>
                        </span>
                      </td>
                    </tr>
                  ))}
                  {loan_history.map((loan) => (
                    <tr key={loan.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50">
                      <td className="px-4 font-medium text-gray-900">{loan.book_title}</td>
                      <td className="px-4 text-gray-600">
                        {loan.returned_at ? new Date(loan.returned_at).toLocaleDateString() : '--'}
                      </td>
                      <td className="px-4">
                        <span className="inline-flex items-center gap-1.5 text-gray-400">
                          <span className="w-[6px] h-[6px] rounded-full bg-gray-300" />
                          Returned
                        </span>
                      </td>
                      <td className="px-4" />
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Fines tab */}
        {activeTab === 'Fines' && (
          <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
            {fines.length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">No fines</div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Reason</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Amount</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Status</th>
                    <th className="text-right text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {fines.map((fine) => {
                    const sc = fineStatusConfig[fine.status] ?? fineStatusConfig.pending;
                    return (
                      <tr key={fine.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50 group">
                        <td className="px-4 text-gray-600">
                          {reasonLabels[fine.reason] ?? fine.reason}
                        </td>
                        <td className="px-4">
                          <span className={clsx(
                            'font-medium',
                            fine.status === 'pending' ? 'text-primary' : 'text-gray-400',
                          )}>
                            ${Number(fine.amount).toFixed(2)}
                          </span>
                        </td>
                        <td className="px-4">
                          <span className={clsx('inline-flex items-center gap-1.5', sc.color)}>
                            <span className={clsx('w-[6px] h-[6px] rounded-full', sc.dot)} />
                            {sc.label}
                          </span>
                        </td>
                        <td className="px-4 text-right">
                          {fine.status === 'pending' && (
                            <button
                              type="button"
                              onClick={() => waiveMutation.mutate(fine.id)}
                              disabled={waiveMutation.isPending}
                              className="text-primary text-[13px] font-medium hover:underline cursor-pointer"
                            >
                              Waive
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Reviews tab */}
        {activeTab === 'Reviews' && (
          <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
            {reviews.length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">No reviews</div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Book</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Rating</th>
                  </tr>
                </thead>
                <tbody>
                  {reviews.map((review) => (
                    <tr key={review.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50">
                      <td className="px-4 font-medium text-gray-900">{review.book_title}</td>
                      <td className="px-4">
                        <span className="inline-flex items-center gap-1 text-amber-500">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <svg
                              key={i}
                              className={clsx('w-3.5 h-3.5', i < review.rating ? 'fill-current' : 'fill-gray-200')}
                              viewBox="0 0 20 20"
                            >
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
