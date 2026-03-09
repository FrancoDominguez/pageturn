import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { apiFetch } from '../../lib/api';
import { useToast } from '../../components/Toast';
import QueryError from '../../components/QueryError';
import type { Loan, Fine, MyReview } from '../../types';

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminUserDetail {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: 'user' | 'admin';
  active_loan_count: number;
  total_loans: number;
  outstanding_fines: number;
  total_fines_paid: number;
  review_count: number;
  is_blocked: boolean;
  created_at: string;
  loans: Loan[];
  fines: Fine[];
  reviews: MyReview[];
}

const tabs = ['Loans', 'Fines', 'Reviews'] as const;
type Tab = (typeof tabs)[number];

// ── Admin User Detail ─────────────────────────────────────────────────────────

export default function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('Loans');

  const { data: user, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin', 'users', id],
    queryFn: () => apiFetch<AdminUserDetail>(`/api/admin/users/${id}`),
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
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', 'stats'] });
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

  if (isLoading || !user) {
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

  const displayName = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email;

  return (
    <div className="text-[13px]">
      {/* KPI bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center divide-x divide-gray-200">
          <div className="pr-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Active Loans</div>
            <div className="text-2xl font-heading font-bold">{user.active_loan_count}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Total Loans</div>
            <div className="text-2xl font-heading font-bold">{user.total_loans}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Outstanding Fines</div>
            <div className="text-2xl font-heading font-bold text-primary">${Number(user.outstanding_fines).toFixed(2)}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Reviews</div>
            <div className="text-2xl font-heading font-bold">{user.review_count}</div>
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
              {(user.first_name?.[0] ?? user.email[0]).toUpperCase()}
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
                {user.is_blocked && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-red-50 text-red-700">
                    Blocked
                  </span>
                )}
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
              {tab === 'Loans' && user.loans.length > 0 && (
                <span className="ml-1.5 text-[11px] text-gray-400">({user.loans.length})</span>
              )}
              {tab === 'Fines' && user.fines.length > 0 && (
                <span className="ml-1.5 text-[11px] text-gray-400">({user.fines.length})</span>
              )}
              {tab === 'Reviews' && user.reviews.length > 0 && (
                <span className="ml-1.5 text-[11px] text-gray-400">({user.reviews.length})</span>
              )}
            </button>
          ))}
        </div>

        {/* Loans tab */}
        {activeTab === 'Loans' && (
          <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
            {user.loans.length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">No loans</div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Book</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Checked Out</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Due Date</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Status</th>
                    <th className="text-right text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {user.loans.map((loan) => (
                    <tr key={loan.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50 group">
                      <td className="px-4">
                        <div className="font-medium text-gray-900">{loan.book.title}</div>
                        <div className="text-gray-400">{loan.book.author}</div>
                      </td>
                      <td className="px-4 text-gray-600">{new Date(loan.checked_out_at).toLocaleDateString()}</td>
                      <td className="px-4 text-gray-600">{new Date(loan.due_date).toLocaleDateString()}</td>
                      <td className="px-4">
                        <span className={clsx(
                          'inline-flex items-center gap-1.5',
                          loan.status === 'active' && 'text-emerald-600',
                          loan.status === 'overdue' && 'text-red-600',
                          loan.status === 'returned' && 'text-gray-400',
                        )}>
                          <span className={clsx(
                            'w-[6px] h-[6px] rounded-full',
                            loan.status === 'active' && 'bg-emerald-500',
                            loan.status === 'overdue' && 'bg-red-500',
                            loan.status === 'returned' && 'bg-gray-300',
                          )} />
                          {loan.status === 'active' ? 'Active' : loan.status === 'overdue' ? 'Overdue' : 'Returned'}
                        </span>
                      </td>
                      <td className="px-4 text-right">
                        {loan.status !== 'returned' && (
                          <span className="inline-flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
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
                                if (window.confirm('Mark this book as lost? This will generate a fine.')) {
                                  lostMutation.mutate(loan.id);
                                }
                              }}
                              disabled={lostMutation.isPending}
                              className="text-red-600 text-[13px] font-medium hover:underline cursor-pointer"
                            >
                              Mark Lost
                            </button>
                          </span>
                        )}
                      </td>
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
            {user.fines.length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">No fines</div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Book</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Reason</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Amount</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Status</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Date</th>
                    <th className="text-right text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {user.fines.map((fine) => (
                    <tr key={fine.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50 group">
                      <td className="px-4">
                        <div className="font-medium text-gray-900">{fine.book_title}</div>
                        <div className="text-gray-400">{fine.book_author}</div>
                      </td>
                      <td className="px-4 text-gray-600">
                        {fine.reason === 'late_return' ? 'Late Return' : fine.reason === 'lost_item' ? 'Lost Item' : 'Damaged'}
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
                        <span className={clsx(
                          'inline-flex items-center gap-1.5',
                          fine.status === 'pending' && 'text-amber-600',
                          fine.status === 'paid' && 'text-emerald-600',
                          fine.status === 'waived' && 'text-blue-600',
                        )}>
                          <span className={clsx(
                            'w-[6px] h-[6px] rounded-full',
                            fine.status === 'pending' && 'bg-amber-500',
                            fine.status === 'paid' && 'bg-emerald-500',
                            fine.status === 'waived' && 'bg-blue-500',
                          )} />
                          {fine.status === 'pending' ? 'Pending' : fine.status === 'paid' ? 'Paid' : 'Waived'}
                        </span>
                      </td>
                      <td className="px-4 text-gray-500">{new Date(fine.created_at).toLocaleDateString()}</td>
                      <td className="px-4 text-right">
                        {fine.status === 'pending' && (
                          <button
                            type="button"
                            onClick={() => waiveMutation.mutate(fine.id)}
                            disabled={waiveMutation.isPending}
                            className="opacity-0 group-hover:opacity-100 text-primary text-[13px] font-medium hover:underline cursor-pointer transition-opacity"
                          >
                            Waive
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Reviews tab */}
        {activeTab === 'Reviews' && (
          <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
            {user.reviews.length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">No reviews</div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Book</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Rating</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Review</th>
                    <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {user.reviews.map((review) => (
                    <tr key={review.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50">
                      <td className="px-4">
                        <div className="font-medium text-gray-900">{review.book.title}</div>
                        <div className="text-gray-400">{review.book.author}</div>
                      </td>
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
                      <td className="px-4 text-gray-600 max-w-xs truncate">{review.review_text || '--'}</td>
                      <td className="px-4 text-gray-500">{new Date(review.created_at).toLocaleDateString()}</td>
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
