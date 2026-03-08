import { useState, useMemo, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { SignedOut } from '@clerk/clerk-react';
import { useBookSearch } from '../hooks/useBooks';
import BookCard from '../components/BookCard';
import ScrollCard from '../components/ScrollCard';
import CoverImage from '../components/CoverImage';
import StarRating from '../components/StarRating';
import Pagination from '../components/Pagination';
import LoadingSkeleton from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';

// ── Genre sections for browse mode ─────────────────────────────────────────

const GENRE_SECTIONS = [
  { label: 'Staff Picks', params: { staff_picks: 'true', limit: '20' } },
  { label: 'Top Rated', params: { sort: 'rating_desc', limit: '20' } },
  { label: 'Fiction', params: { genre: 'Fiction', sort: 'rating_desc', limit: '20' } },
  { label: 'Science Fiction & Fantasy', params: { genre: 'Science Fiction & Fantasy', sort: 'rating_desc', limit: '20' } },
  { label: 'Mystery & Thriller', params: { genre: 'Mystery & Thriller', sort: 'rating_desc', limit: '20' } },
  { label: 'Non-Fiction', params: { genre: 'Non-Fiction', sort: 'rating_desc', limit: '20' } },
  { label: 'Biography', params: { genre: 'Biography', sort: 'rating_desc', limit: '20' } },
  { label: 'History', params: { genre: 'History', sort: 'rating_desc', limit: '20' } },
];

const ITEM_TYPES = [
  { value: '', label: 'All' },
  { value: 'book', label: 'Books' },
  { value: 'ebook', label: 'E-Books' },
  { value: 'audiobook', label: 'Audiobooks' },
  { value: 'dvd', label: 'DVDs' },
  { value: 'magazine', label: 'Magazines' },
];

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'rating_desc', label: 'Highest Rated' },
  { value: 'rating_asc', label: 'Lowest Rated' },
  { value: 'title_asc', label: 'Title A-Z' },
  { value: 'title_desc', label: 'Title Z-A' },
  { value: 'newest', label: 'Newest First' },
];

// ── Chevron Icon ───────────────────────────────────────────────────────────

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      className={`w-5 h-5 text-text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

// ── Genre Accordion Section ────────────────────────────────────────────────

function GenreSection({ label, params }: { label: string; params: Record<string, string | undefined> }) {
  const [open, setOpen] = useState(true);
  const { data, isLoading } = useBookSearch(params);
  const scrollRef = useRef<HTMLDivElement>(null);

  if (!isLoading && (!data?.books || data.books.length === 0)) return null;

  return (
    <section className="border-b border-border last:border-0">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between py-4 px-1 cursor-pointer group"
      >
        <h2 className="font-heading font-semibold text-lg text-text-primary group-hover:text-primary transition-colors">
          {label}
        </h2>
        <ChevronIcon open={open} />
      </button>

      {open && (
        <div className="pb-6">
          {isLoading ? (
            <div className="flex gap-3 overflow-hidden">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="w-40 flex-shrink-0 bg-surface rounded-card shadow-card overflow-hidden">
                  <div className="animate-pulse bg-gray-200 w-full h-56 rounded-t-card" />
                  <div className="p-2.5 space-y-1.5">
                    <div className="animate-pulse bg-gray-200 h-3 w-3/4 rounded" />
                    <div className="animate-pulse bg-gray-200 h-2.5 w-1/2 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div
              ref={scrollRef}
              className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide snap-x snap-mandatory"
            >
              {data?.books.map((book) => (
                <div key={book.id} className="snap-start">
                  <ScrollCard book={book} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

// ── Hero Section ───────────────────────────────────────────────────────────

function HeroSection() {
  const { data } = useBookSearch({ staff_picks: 'true', limit: '10' });

  const heroBook = useMemo(() => {
    if (!data?.books?.length) return null;
    return data.books[Math.floor(Math.random() * data.books.length)];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.books?.length]);

  if (!heroBook) return null;

  return (
    <section className="bg-[#0d1117] text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 md:py-16">
        <div className="flex flex-col md:flex-row items-center gap-8 md:gap-12">
          {/* Cover with glow */}
          <div className="relative flex-shrink-0">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/30 to-secondary/20 blur-3xl rounded-full scale-150" />
            <div className="relative transform rotate-[-3deg] hover:rotate-0 transition-transform duration-500">
              <CoverImage
                src={heroBook.cover_image_url}
                title={heroBook.title}
                author={heroBook.author}
                className="w-48 md:w-56 aspect-[2/3] rounded-card shadow-hover"
              />
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 text-center md:text-left space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-pill text-xs font-medium text-white/80">
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Staff Pick
            </div>

            <h1 className="font-heading text-3xl md:text-4xl font-bold leading-tight">
              {heroBook.title}
            </h1>
            <p className="text-white/70 text-lg">{heroBook.author}</p>
            {heroBook.description && (
              <p className="text-white/50 text-sm leading-relaxed line-clamp-3 max-w-lg">
                {heroBook.description}
              </p>
            )}

            <div className="flex items-center gap-4 justify-center md:justify-start">
              <StarRating rating={heroBook.avg_rating} count={heroBook.rating_count} size="md" />
            </div>

            <Link
              to={`/books/${heroBook.id}`}
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition-opacity shadow-hover"
            >
              Check Out
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

// ── Search Mode ────────────────────────────────────────────────────────────

function SearchResults() {
  const [searchParams, setSearchParams] = useSearchParams();

  const q = searchParams.get('q') || undefined;
  const genre = searchParams.get('genre') || undefined;
  const itemType = searchParams.get('item_type') || undefined;
  const sort = searchParams.get('sort') || undefined;
  const page = searchParams.get('page') || '1';

  const { data, isLoading } = useBookSearch({
    q,
    genre,
    item_type: itemType,
    sort,
    page,
    limit: '20',
  });

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    // Reset to page 1 on filter change
    if (key !== 'page') {
      next.delete('page');
    }
    setSearchParams(next);
  };

  const clearSearch = () => {
    setSearchParams({});
  };

  const genreChips = [
    'Fiction',
    'Science Fiction & Fantasy',
    'Mystery & Thriller',
    'Non-Fiction',
    'Biography',
    'History',
    'Romance',
    'Horror',
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Results header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="font-heading font-bold text-2xl text-text-primary">
            {q ? `Results for "${q}"` : genre ? `Genre: ${genre}` : 'Search Results'}
          </h1>
          {data && (
            <p className="text-text-muted text-sm mt-1">
              {data.total.toLocaleString()} {data.total === 1 ? 'result' : 'results'} found
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <select
            value={sort || 'relevance'}
            onChange={(e) => updateParam('sort', e.target.value === 'relevance' ? '' : e.target.value)}
            className="h-9 px-3 pr-8 bg-surface border border-border rounded-button text-sm text-text-primary cursor-pointer focus:ring-2 focus:ring-primary/40 focus:outline-none"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={clearSearch}
            className="h-9 px-4 text-sm font-medium text-text-secondary border border-border rounded-button hover:bg-gray-50 transition-colors cursor-pointer"
          >
            Clear search
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="space-y-3 mb-8">
        {/* Genre chips */}
        <div className="flex flex-wrap gap-2">
          {genreChips.map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => updateParam('genre', genre === g ? '' : g)}
              className={`inline-flex items-center px-3 py-1.5 rounded-pill text-xs font-medium transition-colors cursor-pointer ${
                genre === g
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-text-secondary hover:bg-gray-200'
              }`}
            >
              {g}
            </button>
          ))}
        </div>

        {/* Item type toggles */}
        <div className="flex flex-wrap gap-1.5">
          {ITEM_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => updateParam('item_type', itemType === t.value ? '' : t.value)}
              className={`px-3 py-1.5 rounded-button text-xs font-medium transition-colors cursor-pointer ${
                (itemType || '') === t.value
                  ? 'bg-secondary text-white'
                  : 'bg-surface border border-border text-text-secondary hover:border-secondary/40'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results grid */}
      {isLoading ? (
        <LoadingSkeleton type="card" count={8} />
      ) : !data?.books?.length ? (
        <EmptyState
          title="No books found"
          description="Try adjusting your search or filters."
          action={{ label: 'Browse Library', href: '/' }}
          icon={
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data.books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>

          {data.pages > 1 && (
            <div className="mt-8">
              <Pagination
                page={data.page}
                pages={data.pages}
                onPageChange={(p) => updateParam('page', String(p))}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function HomePage() {
  const [searchParams] = useSearchParams();
  const isSearchMode = searchParams.has('q') || searchParams.has('genre') || searchParams.has('author');

  if (isSearchMode) {
    return <SearchResults />;
  }

  return (
    <div>
      {/* Hero */}
      <HeroSection />

      {/* Genre accordion sections */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {GENRE_SECTIONS.map((section) => (
          <GenreSection key={section.label} label={section.label} params={section.params} />
        ))}
      </div>

      {/* CTA banner for signed-out users */}
      <SignedOut>
        <section className="bg-gradient-to-r from-primary to-secondary">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 text-center">
            <h2 className="font-heading text-2xl md:text-3xl font-bold text-white mb-3">
              Ready to start reading?
            </h2>
            <p className="text-white/80 text-sm mb-6 max-w-md mx-auto">
              Sign up for a free account to check out books, write reviews, and get personalized recommendations.
            </p>
            <Link
              to="/sign-up"
              className="inline-flex items-center px-8 py-3 bg-white text-primary font-semibold text-sm rounded-pill hover:bg-white/90 transition-colors shadow-hover"
            >
              Get Started
            </Link>
          </div>
        </section>
      </SignedOut>
    </div>
  );
}
