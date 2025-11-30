# Vocabulary Database Schema

This document describes the Entity-Relationship Diagram (ERD) and conceptual design for the vocabulary management system.

## Interactive API Documentation

**For complete endpoint documentation, visit:**
- **Interactive**: http://localhost:8000/docs (Swagger UI - try endpoints in browser)
- **Reading**: http://localhost:8000/redoc (Beautiful formatted docs)

## Quick Reference: API Features

✅ **Pagination**: All list/search endpoints return structured pagination metadata
✅ **Bulk Operations**: Create multiple records in a single transaction
✅ **Nested Routes**: RESTful hierarchical resource access
✅ **Prefix Search**: Fast, index-friendly search (e.g., "hap" finds "happy")
✅ **Related Words**: Get all related words in one query (avoids N+1 problem)
✅ **Filtering**: Filter by language, part of speech, definition, etc.
✅ **Sorting**: Customizable sort fields and order (asc/desc)
✅ **Complete CRUD**: All entities support Create, Read, Update, Delete operations
✅ **Secure Error Messages**: Generic user messages, detailed logs for developers

## ERD Diagram

```
┌─────────────────────┐
│       Word          │
├─────────────────────┤
│ PK id               │
│    word_text        │
│    language_code    │
│    created_at       │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│    Definition       │
├─────────────────────┤
│ PK id               │
│ FK word_id          │
│    definition_text  │
│    part_of_speech   │
│    order            │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│      Example        │
├─────────────────────┤
│ PK id               │
│ FK definition_id    │
│    example_text     │
│    source           │
└─────────────────────┘


┌─────────────────────┐              ┌─────────────────────┐
│       Word          │              │        Tag          │
│    (from above)     │              ├─────────────────────┤
└─────────────────────┘              │ PK id               │
         │                           │    name             │
         │ N:M                       │    description      │
         ▼                           └─────────────────────┘
┌─────────────────────┐                       ▲
│     WordTag         │                       │
│   (Junction)        │───────────────────────┘
├─────────────────────┤              N:M
│ FK word_id          │
│ FK tag_id           │
└─────────────────────┘


┌─────────────────────┐
│   WordRelation      │
│  (Self-Reference)   │
├─────────────────────┤
│ FK word_id_1        │──┐
│ FK word_id_2        │  │  Both reference
│    relation_type    │  │  Word.id
└─────────────────────┘  │
         │               │
         └───────────────┘
              N:M
```

## Entity Descriptions

### Word
The root entity representing a word in a specific language.

**Fields:**
- `id` (PK): Unique identifier
- `word_text`: The actual word (1-255 chars)
- `language_code`: ISO language code (2-10 chars, e.g., 'en', 'es', 'ga')
- `created_at`: Timestamp of creation

**Constraints:**
- word_text: min 1 char, max 255 chars
- language_code: min 2 chars, max 10 chars

### Definition
Represents a specific meaning/definition of a word. A word can have multiple definitions.

**Fields:**
- `id` (PK): Unique identifier
- `word_id` (FK): References Word.id
- `definition_text`: The definition text (1-10000 chars)
- `part_of_speech`: Enum (noun, verb, adjective, etc.)
- `order`: Display order for multiple definitions (0-indexed)

**Constraints:**
- definition_text: min 1 char, max 10000 chars
- order: >= 0

### Example
Usage examples for a specific definition.

**Fields:**
- `id` (PK): Unique identifier
- `definition_id` (FK): References Definition.id
- `example_text`: The example sentence (1-5000 chars)
- `source`: Optional attribution (max 255 chars, e.g., "Shakespeare, Hamlet")

**Constraints:**
- example_text: min 1 char, max 5000 chars
- source: optional, max 255 chars

### Tag
Categorical labels for words (e.g., 'medical', 'informal', 'archaic').

**Fields:**
- `id` (PK): Unique identifier
- `name`: Tag name (1-100 chars)
- `description`: Optional explanation (max 1000 chars)

**Constraints:**
- name: min 1 char, max 100 chars
- description: optional, max 1000 chars

### WordTag (Junction Table)
Many-to-many relationship between Words and Tags.

**Fields:**
- `word_id` (FK): References Word.id
- `tag_id` (FK): References Tag.id

### WordRelation (Self-Referencing)
Captures relationships between words (synonyms, antonyms, etc.).

**Fields:**
- `word_id_1` (FK): First word, references Word.id
- `word_id_2` (FK): Second word, references Word.id
- `relation_type`: Enum (synonym, antonym, related, etc.)

## Key Relationships

### 1. Word → Definition (One-to-Many)
- One word can have multiple definitions
- Each definition belongs to exactly one word
- Definitions are ordered via the `order` field

**Example:** The word "bank" might have:
1. Definition (order=0): "financial institution"
2. Definition (order=1): "edge of a river"

### 2. Definition → Example (One-to-Many)
- One definition can have multiple usage examples
- Each example belongs to exactly one definition

**Example:** For "bank" (financial institution):
- Example 1: "I went to the bank to deposit money"
- Example 2: "The bank approved my loan application"

### 3. Word ↔ Tag (Many-to-Many via WordTag)
- A word can have multiple tags
- A tag can apply to multiple words
- Useful for categorization and filtering

**Example:** Word "stethoscope":
- Tags: [medical, technical, noun]

### 4. Word ↔ Word (Many-to-Many via WordRelation)
- Self-referential relationship
- Captures semantic relationships between words
- Relation types defined by RelationType enum

**Example:**
- "happy" SYNONYM "joyful"
- "hot" ANTONYM "cold"
- "doctor" RELATED "physician"

## Enums

### PartOfSpeech
Defined in `db/models/vocabulary.py`:
- noun
- verb
- adjective
- adverb
- pronoun
- preposition
- conjunction
- interjection

### RelationType
Defined in `db/models/vocabulary.py`:
- synonym
- antonym
- related
- derived_from
- see_also

## Schema Hierarchies

### Complete Word Response
The API supports multiple response depths:

1. **WordOut**: Basic word info (id, word_text, language_code, created_at)
2. **WordWithDefinitions**: Word + definitions (no examples)
3. **WordFull**: Word + definitions + examples
4. **WordWithTags**: Word + associated tags

### Create Operations
Following the Create/Update/Out pattern:

- **Create schemas**: Require all mandatory fields + foreign keys
- **Update schemas**: All fields optional (partial updates)
- **Out schemas**: Include primary keys and computed fields

### Pagination
All list and search endpoints return paginated responses using `PaginatedResponse[T]`:

```json
{
  "data": [...],           // Array of items for current page
  "total": 1000,          // Total number of items across all pages
  "page": 1,              // Current page number (1-indexed)
  "page_size": 100,       // Number of items per page
  "total_pages": 10,      // Total number of pages
  "has_more": true        // Whether there are more pages available
}
```

**Pagination Parameters (all list/search endpoints):**
- `page`: Page number (default: 1, min: 1)
- `page_size`: Items per page (default: 100, min: 1, max: 1000)

## Performance Optimizations

### 1. Prefix Search (Index-Friendly)
All search endpoints use **prefix matching** for optimal database performance:
- Search for `"hap"` → finds `"happy"`, `"happiness"`, `"happen"`
- Does NOT find `"unhappy"` (no leading wildcard)
- **Why**: Allows database indexes to be used, making searches 10-100x faster on large datasets

### 2. Related Words Endpoint (Avoids N+1 Queries)
**New endpoint**: `GET /vocabulary/words/{word_id}/related`
- Fetches all related words in a **single query** (not N separate queries)
- Optional `relation_type` filter (synonym, antonym, etc.)
- Works bidirectionally (finds relations where word is on either side)

**Example:**
```bash
# OLD way (N+1 problem):
GET /words/123                      # 1 query
GET /word-relations?word_id=123     # 1 query → returns 5 relations
GET /words/456                      # 5 more queries (one per related word)
GET /words/789
...

# NEW way (single query):
GET /words/123/related              # 1 query → returns all related words
GET /words/123/related?relation_type=synonym  # Filter by type
```

### 3. Pagination Performance
- Uses `query.count()` for total counts (acceptable with proper indexes)
- For datasets >1M records, consider caching total counts
- Recommendation: Add database indexes on frequently searched columns

### 4. Error Handling Security
- **Users see**: Generic error messages (`"Failed to create word"`)
- **Developers see**: Full stack traces in server logs (terminal/Railway dashboard)
- **Why**: Prevents leaking database schema, file paths, or SQL errors to users

## Database Implementation

The actual database models are defined in `db/models/vocabulary.py` using SQLAlchemy.
The Pydantic schemas in `schemas/vocabulary.py` handle API validation and serialization.

## Quick Usage Examples

**For detailed examples and to try endpoints interactively, visit http://localhost:8000/docs**

### Bulk Import Words
```bash
POST /vocabulary/words/bulk
[
  {"word_text": "hello", "language_code": "en"},
  {"word_text": "hola", "language_code": "es"}
]
```

### Search with Filters
```bash
# Prefix search for English words starting with "hap"
GET /vocabulary/words/search?q=hap&language=en&sort_by=word_text&page=1&page_size=20
```

### Get Related Words (New!)
```bash
# Get all words related to word ID 123
GET /vocabulary/words/123/related

# Get only synonyms
GET /vocabulary/words/123/related?relation_type=synonym
```

### Using Nested Routes
```bash
# Create definition for word 123
POST /vocabulary/words/123/definitions
{
  "definition_text": "A greeting",
  "part_of_speech": "noun",
  "order": 0
}

# Get all definitions for word 123
GET /vocabulary/words/123/definitions
```

## Migration Management

Database migrations are managed using Alembic:

```bash
# Create a new migration
make migrate MSG="add new column"

# Apply migrations
make upgrade

# Rollback last migration
make downgrade

# Reset database (development only!)
make db-reset
```

**Workflow:**
1. Update `db/models/vocabulary.py`
2. Update `schemas/vocabulary.py` (if needed)
3. Run `make migrate MSG="description"`
4. Run `make upgrade`

## Best Practices

### 1. Use Bulk Operations for Large Imports
- Use `/bulk` endpoints for importing datasets
- **Benefits**: Atomic transactions, better performance, duplicate checking
- Entire batch succeeds or fails together

### 2. Use Related Words Endpoint
- **NEW**: Use `GET /words/{id}/related` instead of manual joins
- Avoids N+1 query problem
- Single database query for all related words

### 3. Leverage Nested Routes
- Prefer `POST /words/123/definitions` over `POST /definitions`
- Makes API self-documenting and enforces relationships
- Automatic foreign key validation

### 4. Understand Search Behavior
- Search uses **prefix matching**: `"hap"` finds `"happy"` but not `"unhappy"`
- Optimized for speed with database indexes
- For full-text search, use definition/example search endpoints

### 5. Implement Pagination
- Always handle `has_more` and `total_pages` in UI
- Default page size is 100, max is 1000
- Use appropriate page sizes based on use case

### 6. Filter Before Paginating
- Apply filters (`language`, `part_of_speech`) to reduce result set
- Improves performance and user experience

### 7. Monitor Logs for Errors
- User-facing errors are generic (security)
- Check server logs (terminal/Railway) for detailed error messages
- Logs include full stack traces for debugging

### 8. Use Appropriate Sort Options
- **Dictionaries**: Sort by `word_text` (alphabetical)
- **Recent additions**: Sort by `created_at`
- Definitions: Use `order` field for proper sequencing
