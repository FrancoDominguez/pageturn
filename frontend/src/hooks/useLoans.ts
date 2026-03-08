import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { LoansResponse, LoanHistoryResponse, ReservationsResponse } from '../types';

export function useMyLoans() {
  return useQuery({
    queryKey: ['my-loans'],
    queryFn: () => apiFetch<LoansResponse>('/api/loans'),
  });
}

export function useLoanHistory(page: number = 1) {
  return useQuery({
    queryKey: ['loan-history', page],
    queryFn: () => apiFetch<LoanHistoryResponse>('/api/loans/history', { params: { page: String(page), limit: '20' } }),
  });
}

export function useMyReservations() {
  return useQuery({
    queryKey: ['my-reservations'],
    queryFn: () => apiFetch<ReservationsResponse>('/api/reservations'),
  });
}

export function useRenewLoan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (loanId: string) => apiFetch(`/api/loans/${loanId}/renew`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-loans'] }),
  });
}

export function useCancelReservation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reservationId: string) => apiFetch(`/api/reservations/${reservationId}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-reservations'] }),
  });
}
