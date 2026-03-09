import { useAuth } from '@clerk/clerk-react';
import { Link } from 'react-router-dom';
import { useUserProfile } from '../hooks/useUser';

interface ProtectedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
}

export default function ProtectedRoute({ children, adminOnly }: ProtectedRouteProps) {
  const { isSignedIn, isLoaded } = useAuth();
  const { data: profile, isLoading: profileLoading, isError: profileError } = useUserProfile();

  // Wait for Clerk to initialize
  if (!isLoaded || (isSignedIn && profileLoading && !profileError)) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Not signed in
  if (!isSignedIn) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
        <svg className="w-16 h-16 text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
          />
        </svg>
        <h2 className="font-heading font-semibold text-xl text-text-primary mb-2">
          Sign in required
        </h2>
        <p className="text-text-muted text-sm mb-6 max-w-sm">
          You need to be signed in to view this page. Sign in to access your loans, reservations, and more.
        </p>
        <Link
          to="/"
          className="inline-flex items-center px-6 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors"
        >
          Go to Home
        </Link>
      </div>
    );
  }

  // Admin check
  if (adminOnly && profile?.role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
        <svg className="w-16 h-16 text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 0A9 9 0 015.636 18.364"
          />
        </svg>
        <h2 className="font-heading font-semibold text-xl text-text-primary mb-2">
          Access denied
        </h2>
        <p className="text-text-muted text-sm mb-6 max-w-sm">
          You don't have permission to view this page. This area is restricted to administrators.
        </p>
        <Link
          to="/"
          className="inline-flex items-center px-6 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors"
        >
          Go to Home
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
