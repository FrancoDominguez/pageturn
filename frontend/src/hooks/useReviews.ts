import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { MyReviewsResponse } from '../types';

export function useMyReviews() {
  return useQuery({
    queryKey: ['my-reviews'],
    queryFn: () => apiFetch<MyReviewsResponse>('/api/reviews/mine'),
  });
}

export function useCreateReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { book_id: string; rating: number; review_text?: string }) =>
      apiFetch('/api/reviews', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-reviews'] });
      qc.invalidateQueries({ queryKey: ['book-reviews'] });
      qc.invalidateQueries({ queryKey: ['book'] });
    },
  });
}

export function useUpdateReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ reviewId, ...data }: { reviewId: string; rating: number; review_text?: string }) =>
      apiFetch(`/api/reviews/${reviewId}`, { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-reviews'] });
      qc.invalidateQueries({ queryKey: ['book-reviews'] });
      qc.invalidateQueries({ queryKey: ['book'] });
    },
  });
}

export function useDeleteReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reviewId: string) => apiFetch(`/api/reviews/${reviewId}`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-reviews'] });
      qc.invalidateQueries({ queryKey: ['book-reviews'] });
      qc.invalidateQueries({ queryKey: ['book'] });
    },
  });
}
