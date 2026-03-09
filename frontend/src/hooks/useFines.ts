import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { FinesResponse } from '../types';

export function useMyFines(enabled: boolean | undefined = true) {
  return useQuery({
    queryKey: ['my-fines'],
    queryFn: () => apiFetch<FinesResponse>('/api/fines'),
    enabled: !!enabled,
  });
}
