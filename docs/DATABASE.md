# PageTurn — Database Schema

**Engine**: PostgreSQL 16 on Neon (serverless)
**ORM**: SQLAlchemy 2.0 with async support
**Migrations**: Alembic

---

## Entity Relationship Diagram

```
users 1──∞ loans ∞──1 book_copies ∞──1 books
users 1──∞ reservations ∞──1 books
users 1──∞ fines ∞──1 loans
users 1──∞ reviews ∞──1 books
users 1──∞ api_keys
```

---

## Table Definitions (SQL)

### `users`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    max_loans INT NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT true,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_clerk_id ON users(clerk_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### `books`

```sql
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(500) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    isbn13 VARCHAR(20) UNIQUE,
    description TEXT,
    genre VARCHAR(100),
    genres TEXT[] DEFAULT '{}',
    item_type VARCHAR(50) NOT NULL DEFAULT 'book' CHECK (item_type IN ('book', 'audiobook', 'dvd', 'ebook', 'magazine')),
    cover_image_url VARCHAR(1000),
    page_count INT,
    publication_year INT,
    publisher VARCHAR(500),
    language VARCHAR(10) DEFAULT 'en',
    is_staff_pick BOOLEAN NOT NULL DEFAULT false,
    staff_pick_note TEXT,
    replacement_cost DECIMAL(10, 2),
    avg_rating DECIMAL(3, 2) DEFAULT 0.00,
    rating_count INT DEFAULT 0,
    search_vector TSVECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Full-text search index
CREATE INDEX idx_books_search ON books USING GIN(search_vector);

-- Partial indexes for common filters
CREATE INDEX idx_books_genre ON books(genre);
CREATE INDEX idx_books_item_type ON books(item_type);
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_publication_year ON books(publication_year);
CREATE INDEX idx_books_avg_rating ON books(avg_rating DESC);
CREATE INDEX idx_books_staff_pick ON books(is_staff_pick) WHERE is_staff_pick = true;
```

### Full-Text Search Trigger

```sql
-- Function to update search_vector
CREATE OR REPLACE FUNCTION books_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.author, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.genre, '')), 'D') ||
        setweight(to_tsvector('english', coalesce(array_to_string(NEW.genres, ' '), '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on insert/update
CREATE TRIGGER trg_books_search_vector
    BEFORE INSERT OR UPDATE OF title, author, description, genre, genres
    ON books
    FOR EACH ROW
    EXECUTE FUNCTION books_search_vector_update();
```

### `book_copies`

```sql
CREATE TABLE book_copies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    barcode VARCHAR(50) UNIQUE NOT NULL,
    condition VARCHAR(20) NOT NULL DEFAULT 'good' CHECK (condition IN ('new', 'good', 'fair', 'poor')),
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'checked_out', 'reserved', 'damaged', 'lost')),
    added_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_book_copies_book_id ON book_copies(book_id);
CREATE INDEX idx_book_copies_status ON book_copies(status);
CREATE INDEX idx_book_copies_book_status ON book_copies(book_id, status);
```

### `loans`

```sql
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    book_copy_id UUID NOT NULL REFERENCES book_copies(id),
    checked_out_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    due_date TIMESTAMPTZ NOT NULL,
    returned_at TIMESTAMPTZ,
    renewed_count INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'returned', 'overdue', 'lost')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_loans_user_id ON loans(user_id);
CREATE INDEX idx_loans_book_copy_id ON loans(book_copy_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loans_user_status ON loans(user_id, status);
CREATE INDEX idx_loans_due_date ON loans(due_date) WHERE status = 'active';
```

### `reservations`

```sql
CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    book_id UUID NOT NULL REFERENCES books(id),
    reserved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ready', 'fulfilled', 'expired', 'cancelled')),
    queue_position INT,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reservations_user_id ON reservations(user_id);
CREATE INDEX idx_reservations_book_id ON reservations(book_id);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_reservations_book_pending ON reservations(book_id, queue_position) WHERE status = 'pending';
```

### `fines`

```sql
CREATE TABLE fines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    loan_id UUID NOT NULL REFERENCES loans(id),
    amount DECIMAL(10, 2) NOT NULL,
    reason VARCHAR(100) NOT NULL CHECK (reason IN ('late_return', 'lost_item', 'damaged_item')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'waived')),
    paid_at TIMESTAMPTZ,
    waived_by UUID REFERENCES users(id),
    waived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_fines_user_id ON fines(user_id);
CREATE INDEX idx_fines_loan_id ON fines(loan_id);
CREATE INDEX idx_fines_status ON fines(status);
CREATE INDEX idx_fines_user_pending ON fines(user_id) WHERE status = 'pending';
```

### `reviews`

```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    book_id UUID NOT NULL REFERENCES books(id),
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, book_id)
);

CREATE INDEX idx_reviews_book_id ON reviews(book_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_book_rating ON reviews(book_id, rating);
```

### `api_keys`

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('user', 'admin')),
    name VARCHAR(100) NOT NULL,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
```

---

## Utility Functions

### Calculate fine for a loan

```sql
CREATE OR REPLACE FUNCTION calculate_fine(
    p_due_date TIMESTAMPTZ,
    p_return_date TIMESTAMPTZ,
    p_item_type VARCHAR
) RETURNS DECIMAL AS $$
DECLARE
    days_overdue INT;
    daily_rate DECIMAL;
    max_fine DECIMAL := 25.00;
    fine_amount DECIMAL;
BEGIN
    days_overdue := GREATEST(0, EXTRACT(DAY FROM (p_return_date - p_due_date))::INT);

    IF days_overdue = 0 THEN
        RETURN 0;
    END IF;

    daily_rate := CASE p_item_type
        WHEN 'book' THEN 0.25
        WHEN 'ebook' THEN 0.25
        WHEN 'dvd' THEN 1.00
        WHEN 'audiobook' THEN 0.50
        WHEN 'magazine' THEN 0.10
        ELSE 0.25
    END;

    fine_amount := days_overdue * daily_rate;
    RETURN LEAST(fine_amount, max_fine);
END;
$$ LANGUAGE plpgsql;
```

### Update book average rating

```sql
CREATE OR REPLACE FUNCTION update_book_rating() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE books SET
            avg_rating = COALESCE((SELECT AVG(rating)::DECIMAL(3,2) FROM reviews WHERE book_id = OLD.book_id), 0),
            rating_count = (SELECT COUNT(*) FROM reviews WHERE book_id = OLD.book_id),
            updated_at = now()
        WHERE id = OLD.book_id;
        RETURN OLD;
    ELSE
        UPDATE books SET
            avg_rating = COALESCE((SELECT AVG(rating)::DECIMAL(3,2) FROM reviews WHERE book_id = NEW.book_id), 0),
            rating_count = (SELECT COUNT(*) FROM reviews WHERE book_id = NEW.book_id),
            updated_at = now()
        WHERE id = NEW.book_id;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_book_rating
    AFTER INSERT OR UPDATE OR DELETE ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_book_rating();
```

### Updated_at auto-update trigger

```sql
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_books_updated_at BEFORE UPDATE ON books FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_reviews_updated_at BEFORE UPDATE ON reviews FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## Seed Data Specification

### Books (~1,000 from Kaggle CSV)

**Source**: `7k-books-with-metadata.csv`

**Column Mapping** (CSV → DB):
| CSV Column | DB Column | Transform |
|-----------|-----------|-----------|
| title | title | Direct |
| subtitle | (append to title if exists) | `title + ": " + subtitle` |
| authors | author | Direct |
| categories | genre (first), genres (all) | Split by `;` or `,` |
| description | description | Direct, truncate to 2000 chars |
| isbn13 | isbn13 | Direct |
| thumbnail | cover_image_url | Direct |
| average_rating | avg_rating | Direct (float) |
| ratings_count | rating_count | Direct (int) |
| num_pages | page_count | Direct (int) |
| published_year | publication_year | Direct (int) |

**Filtering**:
- Skip rows missing title or author
- Skip rows missing description AND thumbnail (we want rich data)
- Deduplicate by isbn13
- Target genre distribution:
  - Fiction: 150, Science Fiction: 100, Fantasy: 100, Mystery/Thriller: 100
  - Romance: 80, Non-Fiction: 120, History: 60, Science: 60
  - Biography: 60, Children's: 60, Horror: 40, Poetry: 30, Self-Help: 40
  - Fill remaining with whatever genres are available
- All items set to `item_type='book'` initially; randomly assign 5% as 'audiobook', 3% as 'dvd', 2% as 'ebook' for variety

**Staff Picks**: After importing books, mark 15-20 books across genres as `is_staff_pick = true` with a `staff_pick_note` from a "librarian". Pick well-known, highly-rated titles. Example notes:
- "A timeless meditation on the American Dream — our most-requested title" (The Great Gatsby)
- "Orwell's chilling prophecy never stops being relevant" (1984)
- "The perfect gateway into fantasy literature" (The Hobbit)
- "Harper Lee at her finest — essential reading for everyone" (To Kill a Mockingbird)
- Generate similar 1-sentence notes for remaining staff picks using templates

**Cover Image Handling**:
- **Primary filter**: Only import books that have a non-empty `thumbnail` field from the CSV. This ensures ~95% of imported books have covers.
- **Validation during seed**: For each book, HTTP HEAD check the `thumbnail` URL. If it returns non-200, try Open Library fallback: `https://covers.openlibrary.org/b/isbn/{isbn13}-M.jpg`
- **Frontend fallback**: For any book where `cover_image_url` is NULL or the image fails to load, display a CSS-generated placeholder cover showing the book title and author on a gradient background (coral-to-blue gradient, white text, Space Grotesk font). Use an `onError` handler on the `<img>` tag to swap to the placeholder.
- **Target**: 100% of seeded books should have either a working cover URL or be handled gracefully by the frontend placeholder.

### Book Copies

For each book, create copies:
- Books with `avg_rating >= 4.0`: 3 copies
- Books with `avg_rating >= 3.0`: 2 copies
- Others: 1 copy
- Barcode format: `PT-{book_index:04d}-{copy_number:02d}` (e.g., "PT-0001-01")
- Condition: 70% 'good', 15% 'new', 10% 'fair', 5% 'poor'

### Users (50 mock)

Generate with Python `faker` library:
```python
{
    "clerk_id": f"mock_clerk_{i:03d}",  # Not real Clerk IDs
    "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
    "first_name": faker.first_name(),
    "last_name": faker.last_name(),
    "role": "admin" if i < 5 else "user",
    "max_loans": random.choice([3, 5, 5, 5, 7, 10]),
    "created_at": faker.date_time_between(start_date="-2y", end_date="-1m")
}
```

### Loans (500 mock)

Distribution:
- 400 returned (status='returned')
- 75 active (status='active', within due date)
- 25 overdue (status='overdue', past due date, not returned)

For returned loans:
```python
{
    "user_id": random_user,
    "book_copy_id": random_copy,
    "checked_out_at": random_date_in_last_12_months,
    "due_date": checked_out_at + loan_period,
    "returned_at": due_date + random(-3, 14) days,  # Some early, some late
    "renewed_count": random.choice([0, 0, 0, 1, 1, 2]),
    "status": "returned"
}
```

For active loans:
```python
{
    "checked_out_at": random_date_in_last_3_weeks,
    "due_date": checked_out_at + 14 days,
    "returned_at": None,
    "status": "active"
    # Set the book_copy.status = 'checked_out'
}
```

For overdue loans:
```python
{
    "checked_out_at": random_date_30_to_60_days_ago,
    "due_date": checked_out_at + 14 days,  # So due_date is in the past
    "returned_at": None,
    "status": "overdue"
    # Set the book_copy.status = 'checked_out'
}
```

### Reservations (30 mock)

- 15 pending: linked to books where all copies are checked_out
- 10 ready: linked to a reserved copy, expires_at in the future
- 5 fulfilled: linked to a loan that was created from the reservation

### Fines (40 mock)

- Only for loans where `returned_at > due_date` (late returns)
- 24 pending, 10 paid, 6 waived
- Amount calculated using `calculate_fine()` logic
- Waived fines: set `waived_by` to a random admin user

### Reviews (200 mock)

- Distributed across 30 users and ~150 books
- Rating distribution: bell curve centered on 3.7
  - 5★: 15%, 4★: 35%, 3★: 30%, 2★: 15%, 1★: 5%
- 60% include review_text (generated with faker or short templates), 40% rating only
- Only create reviews for books the user has a returned loan for (maintain data integrity)
- After all reviews inserted, the `trg_update_book_rating` trigger handles avg_rating updates

---

## Alembic Configuration

**`alembic.ini`** — connection string from `DATABASE_URL` env var

**Initial migration** creates all tables, indexes, functions, and triggers in a single migration file.

**Migration naming convention**: `{rev}_{slug}.py` (e.g., `001_initial_schema.py`)

**SQLAlchemy model location**: `api/app/models/`

The implementation agent should use `alembic revision --autogenerate` after defining all SQLAlchemy models, then manually add the SQL functions and triggers to the generated migration (since Alembic doesn't auto-detect raw SQL functions).
