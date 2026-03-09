import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { apiFetch } from '../../lib/api';
import { useToast } from '../../components/Toast';
import Modal from '../../components/Modal';
import QueryError from '../../components/QueryError';
import type { Book, BooksResponse } from '../../types';

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminBooksStats {
  total_books: number;
  total_copies: number;
  checked_out: number;
  staff_picks: number;
}

interface BookFormData {
  title: string;
  author: string;
  isbn: string;
  description: string;
  genre: string;
  item_type: Book['item_type'];
  cover_image_url: string;
  page_count: string;
  publication_year: string;
  publisher: string;
  total_copies: string;
  condition: string;
  is_staff_pick: boolean;
  staff_pick_note: string;
}

const emptyForm: BookFormData = {
  title: '',
  author: '',
  isbn: '',
  description: '',
  genre: '',
  item_type: 'book',
  cover_image_url: '',
  page_count: '',
  publication_year: '',
  publisher: '',
  total_copies: '1',
  condition: 'new',
  is_staff_pick: false,
  staff_pick_note: '',
};

const typeFilters = ['All', 'Books', 'Audiobooks', 'DVDs', 'Ebooks', 'Magazines'] as const;

const typeFilterMap: Record<string, string | undefined> = {
  All: undefined,
  Books: 'book',
  Audiobooks: 'audiobook',
  DVDs: 'dvd',
  Ebooks: 'ebook',
  Magazines: 'magazine',
};

// ── Admin Books Page ──────────────────────────────────────────────────────────

export default function AdminBooksPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<string>('All');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [form, setForm] = useState<BookFormData>(emptyForm);

  const itemType = typeFilterMap[activeTab];

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['admin', 'books', 'stats'],
    queryFn: () => apiFetch<AdminBooksStats>('/api/admin/books/stats'),
  });

  // Fetch books
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin', 'books', page, search, itemType],
    queryFn: () =>
      apiFetch<BooksResponse>('/api/books', {
        params: {
          page: String(page),
          limit: '25',
          q: search || undefined,
          item_type: itemType,
        },
      }),
  });

  const books = data?.books ?? [];
  const totalPages = data?.pages ?? 1;

  // Create/update mutation
  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => {
      if (editingBook) {
        return apiFetch(`/api/admin/books/${editingBook.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      }
      return apiFetch('/api/admin/books', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'books'] });
      toast(editingBook ? 'Book updated' : 'Book created', 'success');
      closeModal();
    },
    onError: () => {
      toast('Failed to save book', 'error');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/admin/books/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'books'] });
      toast('Book deleted', 'success');
    },
    onError: () => {
      toast('Failed to delete book', 'error');
    },
  });

  function openAdd() {
    setEditingBook(null);
    setForm(emptyForm);
    setIsModalOpen(true);
  }

  function openEdit(book: Book) {
    setEditingBook(book);
    setForm({
      title: book.title,
      author: book.author,
      isbn: book.isbn ?? '',
      description: book.description ?? '',
      genre: book.genres?.[0] ?? book.genre ?? '',
      item_type: book.item_type,
      cover_image_url: book.cover_image_url ?? '',
      page_count: book.page_count ? String(book.page_count) : '',
      publication_year: book.publication_year ? String(book.publication_year) : '',
      publisher: book.publisher ?? '',
      total_copies: String(book.total_copies),
      condition: 'good',
      is_staff_pick: book.is_staff_pick,
      staff_pick_note: book.staff_pick_note ?? '',
    });
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingBook(null);
    setForm(emptyForm);
  }

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    saveMutation.mutate({
      title: form.title,
      author: form.author,
      isbn: form.isbn || undefined,
      description: form.description || undefined,
      genre: form.genre || undefined,
      item_type: form.item_type,
      cover_image_url: form.cover_image_url || undefined,
      page_count: form.page_count ? Number(form.page_count) : undefined,
      publication_year: form.publication_year ? Number(form.publication_year) : undefined,
      publisher: form.publisher || undefined,
      total_copies: Number(form.total_copies),
      condition: form.condition,
      is_staff_pick: form.is_staff_pick,
      staff_pick_note: form.staff_pick_note || undefined,
    });
  }

  function handleDelete(book: Book) {
    if (window.confirm(`Delete "${book.title}"? This cannot be undone.`)) {
      deleteMutation.mutate(book.id);
    }
  }

  const updateField = (field: keyof BookFormData, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="text-[13px]">
      {/* KPI bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center divide-x divide-gray-200">
          <div className="pr-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Total Titles</div>
            <div className="text-2xl font-heading font-bold">{stats?.total_books?.toLocaleString() ?? '--'}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Total Copies</div>
            <div className="text-2xl font-heading font-bold">{stats?.total_copies?.toLocaleString() ?? '--'}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Checked Out</div>
            <div className="text-2xl font-heading font-bold">{stats?.checked_out?.toLocaleString() ?? '--'}</div>
          </div>
          <div className="px-8">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Staff Picks</div>
            <div className="text-2xl font-heading font-bold">{stats?.staff_picks?.toLocaleString() ?? '--'}</div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="px-6 py-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-1">
          {typeFilters.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => { setActiveTab(tab); setPage(1); }}
              className={clsx(
                'px-3 py-1.5 text-[13px] font-medium border-b-2 transition-colors cursor-pointer',
                activeTab === tab
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700',
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-[200px] h-[32px] px-3 text-[13px] bg-white border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
          />
          <button
            type="button"
            onClick={openAdd}
            className="h-[32px] px-4 bg-primary hover:bg-primary-hover text-white text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer"
          >
            Add Book
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="px-6">
        <div className="bg-white border border-gray-200 rounded-[8px] overflow-hidden">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Title & Author</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Genre</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Type</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Copies</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Rating</th>
                <th className="text-left text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Staff Pick</th>
                <th className="text-right text-[11px] uppercase tracking-wider text-gray-500 py-3 px-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isError ? (
                <tr>
                  <td colSpan={7}>
                    <QueryError message="Failed to load books." onRetry={() => refetch()} />
                  </td>
                </tr>
              ) : isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-100 h-[44px]">
                    <td className="px-4" colSpan={7}>
                      <div className="h-3 w-2/3 bg-gray-100 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : books.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                    No books found
                  </td>
                </tr>
              ) : (
                books.map((book) => (
                  <tr key={book.id} className="border-b border-gray-100 h-[44px] hover:bg-gray-50 group">
                    <td className="px-4">
                      <div className="min-w-0">
                        <div className="font-medium text-gray-900 truncate">{book.title}</div>
                        <div className="text-gray-400 truncate">{book.author}</div>
                      </div>
                    </td>
                    <td className="px-4 text-gray-600">{book.genres?.[0] ?? book.genre ?? '--'}</td>
                    <td className="px-4">
                      <span className="inline-flex items-center px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-[12px]">
                        {book.item_type}
                      </span>
                    </td>
                    <td className="px-4 text-gray-600">
                      <span className={clsx(book.available_copies === 0 && 'text-red-600 font-medium')}>
                        {book.available_copies}
                      </span>
                      <span className="text-gray-400">/{book.total_copies}</span>
                    </td>
                    <td className="px-4 text-gray-600">
                      {book.avg_rating > 0 ? (
                        <span>{Number(book.avg_rating).toFixed(1)} <span className="text-gray-400">({book.rating_count})</span></span>
                      ) : (
                        <span className="text-gray-300">--</span>
                      )}
                    </td>
                    <td className="px-4">
                      {book.is_staff_pick ? (
                        <span className="inline-flex items-center gap-1 text-amber-600">
                          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          Yes
                        </span>
                      ) : (
                        <span className="text-gray-300">--</span>
                      )}
                    </td>
                    <td className="px-4 text-right">
                      <span className="inline-flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          type="button"
                          onClick={() => openEdit(book)}
                          className="text-primary text-[13px] font-medium hover:underline cursor-pointer"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(book)}
                          className="text-red-600 text-[13px] font-medium hover:underline cursor-pointer"
                        >
                          Delete
                        </button>
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between py-4">
            <div className="text-gray-400">
              Page {page} of {totalPages} ({data?.total ?? 0} total)
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className={clsx(
                  'px-3 py-1.5 text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer',
                  page <= 1 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600 hover:bg-white',
                )}
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className={clsx(
                  'px-3 py-1.5 text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer',
                  page >= totalPages ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600 hover:bg-white',
                )}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={closeModal} title={editingBook ? 'Edit Book' : 'Add Book'}>
        <form onSubmit={handleSave} className="space-y-4 text-[13px]">
          <div className="grid grid-cols-2 gap-4">
            {/* Title */}
            <div className="col-span-2">
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Title *</label>
              <input
                type="text"
                required
                value={form.title}
                onChange={(e) => updateField('title', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Author */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Author *</label>
              <input
                type="text"
                required
                value={form.author}
                onChange={(e) => updateField('author', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* ISBN */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">ISBN</label>
              <input
                type="text"
                value={form.isbn}
                onChange={(e) => updateField('isbn', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Description */}
            <div className="col-span-2">
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => updateField('description', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200 resize-none"
              />
            </div>

            {/* Genre */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Genre</label>
              <input
                type="text"
                value={form.genre}
                onChange={(e) => updateField('genre', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Item Type */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Type *</label>
              <select
                value={form.item_type}
                onChange={(e) => updateField('item_type', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200 bg-white"
              >
                <option value="book">Book</option>
                <option value="audiobook">Audiobook</option>
                <option value="dvd">DVD</option>
                <option value="ebook">Ebook</option>
                <option value="magazine">Magazine</option>
              </select>
            </div>

            {/* Cover URL */}
            <div className="col-span-2">
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Cover Image URL</label>
              <input
                type="url"
                value={form.cover_image_url}
                onChange={(e) => updateField('cover_image_url', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Pages */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Pages</label>
              <input
                type="number"
                value={form.page_count}
                onChange={(e) => updateField('page_count', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Year */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Year</label>
              <input
                type="number"
                value={form.publication_year}
                onChange={(e) => updateField('publication_year', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Publisher */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Publisher</label>
              <input
                type="text"
                value={form.publisher}
                onChange={(e) => updateField('publisher', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Copies */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Copies *</label>
              <input
                type="number"
                required
                min={1}
                value={form.total_copies}
                onChange={(e) => updateField('total_copies', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
              />
            </div>

            {/* Condition */}
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Condition</label>
              <select
                value={form.condition}
                onChange={(e) => updateField('condition', e.target.value)}
                className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200 bg-white"
              >
                <option value="new">New</option>
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                <option value="poor">Poor</option>
              </select>
            </div>

            {/* Staff Pick */}
            <div className="col-span-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_staff_pick}
                  onChange={(e) => updateField('is_staff_pick', e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-[13px] text-gray-700">Staff Pick</span>
              </label>
            </div>

            {/* Staff Pick Note */}
            {form.is_staff_pick && (
              <div className="col-span-2">
                <label className="block text-[11px] uppercase tracking-wider text-gray-500 mb-1">Staff Pick Note</label>
                <input
                  type="text"
                  value={form.staff_pick_note}
                  onChange={(e) => updateField('staff_pick_note', e.target.value)}
                  className="w-full h-[34px] px-3 text-[13px] border border-gray-200 rounded-[6px] outline-none focus:border-gray-300 focus:ring-1 focus:ring-gray-200"
                />
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={closeModal}
              className="h-[34px] px-4 text-[13px] font-medium text-gray-600 hover:bg-gray-100 rounded-[6px] transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="h-[34px] px-4 bg-primary hover:bg-primary-hover text-white text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer disabled:opacity-50"
            >
              {saveMutation.isPending ? 'Saving...' : editingBook ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
