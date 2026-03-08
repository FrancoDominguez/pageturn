import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/clerk-react';
import { apiFetch } from '../lib/api';
import type { UserProfile } from '../types';

export function useUserProfile() {
  const { isSignedIn } = useAuth();
  return useQuery({
    queryKey: ['me'],
    queryFn: () => apiFetch<UserProfile>('/api/me'),
    enabled: !!isSignedIn,
  });
}
