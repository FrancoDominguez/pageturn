import { useState, type FormEvent } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { SignedIn, SignedOut, UserButton } from '@clerk/clerk-react';
import { useMyFines } from '../hooks/useFines';
import { useUserProfile } from '../hooks/useUser';
import SubNav from './SubNav';

// ── Paths that show the user sub-navigation ──────────────────────────────────
const subNavPaths = ['/loans', '/history', '/fines', '/reviews', '/ai-assistant'];

function useShowSubNav(): boolean {
  const { pathname } = useLocation();
  return subNavPaths.some((p) => pathname.startsWith(p));
}

// ── Navbar ───────────────────────────────────────────────────────────────────

function Navbar() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) {
      navigate(`/?q=${encodeURIComponent(trimmed)}`);
    }
  };

  return (
    <header className="sticky top-0 z-40 h-[72px] bg-[#0d1117] flex items-center px-4 sm:px-6">
      <div className="w-full max-w-7xl mx-auto flex items-center gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-0 flex-shrink-0">
          <span className="font-heading text-xl font-bold text-white">Page</span>
          <span className="font-heading text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Turn
          </span>
        </Link>

        {/* Search */}
        <form
          onSubmit={handleSearch}
          className="flex-1 max-w-xl mx-auto flex items-center"
        >
          <div className="relative flex items-center w-full">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search books, authors, ISBN..."
              className="w-full h-10 pl-4 pr-24 bg-white text-text-primary text-sm rounded-pill border-0 outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-text-muted"
            />
            <button
              type="submit"
              className="absolute right-1 h-8 px-4 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-pill transition-colors cursor-pointer"
            >
              Search
            </button>
          </div>
        </form>

        {/* Auth */}
        <div className="flex items-center flex-shrink-0">
          <SignedOut>
            <Link
              to="/sign-in"
              className="inline-flex items-center px-5 py-2 border border-white/60 text-white text-sm font-medium rounded-pill hover:bg-white/10 transition-colors"
            >
              Sign In
            </Link>
          </SignedOut>

          <SignedIn>
            <UserButtonWithMenu />
          </SignedIn>
        </div>
      </div>
    </header>
  );
}

// ── User Button with custom menu items ───────────────────────────────────────

function UserButtonWithMenu() {
  const { data: fines } = useMyFines();
  const { data: profile } = useUserProfile();

  const fineAmount = fines?.total_outstanding ?? 0;

  return (
    <UserButton
      afterSignOutUrl="/"
      appearance={{
        elements: {
          avatarBox: 'w-9 h-9',
        },
      }}
    >
      <UserButton.MenuItems>
        <UserButton.Link label="My Loans" labelIcon={<LoanIcon />} href="/loans" />
        <UserButton.Link label="History" labelIcon={<HistoryIcon />} href="/history" />
        <UserButton.Link
          label={fineAmount > 0 ? `Fines & Dues ($${fineAmount.toFixed(2)})` : 'Fines & Dues'}
          labelIcon={<FineIcon />}
          href="/fines"
        />
        <UserButton.Link label="Reviews" labelIcon={<ReviewIcon />} href="/reviews" />
        <UserButton.Link label="AI Assistant" labelIcon={<AiIcon />} href="/ai-assistant" />
        {profile?.role === 'admin' && (
          <UserButton.Link label="Admin" labelIcon={<AdminIcon />} href="/admin" />
        )}
      </UserButton.MenuItems>
    </UserButton>
  );
}

// ── Tiny icons for Clerk menu ────────────────────────────────────────────────

function LoanIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
  );
}

function HistoryIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function FineIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ReviewIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  );
}

function AiIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-1.39 4.17a2.25 2.25 0 01-2.135 1.58H8.525a2.25 2.25 0 01-2.135-1.58L5 14.5m14 0H5" />
    </svg>
  );
}

function AdminIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

// ── Footer ───────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="bg-[#0d1117] text-white/70 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          {/* Branding */}
          <div>
            <div className="flex items-center gap-0 mb-1.5">
              <span className="font-heading text-lg font-bold text-white">Page</span>
              <span className="font-heading text-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Turn
              </span>
            </div>
            <p className="text-sm text-white/50">Your modern library catalogue</p>
          </div>

          {/* Nav links */}
          <nav className="flex items-center gap-6">
            <Link to="/" className="text-sm hover:text-white transition-colors">
              Browse
            </Link>
            <Link to="/loans" className="text-sm hover:text-white transition-colors">
              My Loans
            </Link>
            <Link to="/privacy" className="text-sm hover:text-white transition-colors">
              Privacy
            </Link>
            <Link to="/terms" className="text-sm hover:text-white transition-colors">
              Terms
            </Link>
          </nav>
        </div>

        <div className="mt-8 pt-6 border-t border-white/10 text-sm text-white/40 text-center">
          &copy; 2026 PageTurn Library
        </div>
      </div>
    </footer>
  );
}

// ── Layout ───────────────────────────────────────────────────────────────────

export default function Layout() {
  const showSubNav = useShowSubNav();
  const { data: fines } = useMyFines();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      {showSubNav && (
        <SignedIn>
          <SubNav fineAmount={fines?.total_outstanding} />
        </SignedIn>
      )}

      <main className="flex-1">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
