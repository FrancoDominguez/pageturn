import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { BooksResponse, BookDetail, ReviewsResponse } from '../types';

export function useBookSearch(params: Record<string, string | undefined>) {
  return useQuery({
    queryKey: ['books', params],
    queryFn: () => apiFetch<BooksResponse>('/api/books', { params }),
    staleTime: 30_000,
  });
}

export function useBookDetail(bookId: string) {
  return useQuery({
    queryKey: ['book', bookId],
    queryFn: () => apiFetch<BookDetail>(`/api/books/${bookId}`),
    enabled: !!bookId,
  });
}

export function useBookReviews(bookId: string, params?: Record<string, string | undefined>) {
  return useQuery({
    queryKey: ['book-reviews', bookId, params],
    queryFn: () => apiFetch<ReviewsResponse>(`/api/books/${bookId}/reviews`, { params }),
    enabled: !!bookId,
  });
}

export function useCheckout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (bookId: string) =>
      apiFetch('/api/loans', { method: 'POST', body: JSON.stringify({ book_id: bookId }) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-loans'] });
      qc.invalidateQueries({ queryKey: ['book'] });
      qc.invalidateQueries({ queryKey: ['books'] });
    },
  });
}

export function useReserveBook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (bookId: string) =>
      apiFetch('/api/reservations', { method: 'POST', body: JSON.stringify({ book_id: bookId }) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-reservations'] });
      qc.invalidateQueries({ queryKey: ['book'] });
      qc.invalidateQueries({ queryKey: ['books'] });
    },
  });
}
