# FOUND IT — Product Requirements & Agent Build Specification

**Document type:** Product requirements, technical specification, and implementation brief  
**Project:** University Lost-and-Found Portal  
**Version:** 1.0  
**Development approach:** Local-first course project  
**Primary coding agent:** Google Antigravity  

---

## 0. Instructions to the coding agent

Read this entire document before changing or creating files. Treat it as the source of truth for the first version of Found It.

Your task is to **implement the working application**, not merely produce a plan, mock-up, or static frontend. Build the frontend, backend, MySQL schema, migrations, seed data, authentication, image uploads, contact workflow, admin database dashboard, SQL Explorer, and setup documentation.

Before implementation:

1. Inspect the current workspace and available tools. Preserve any useful existing work.
2. Produce a short implementation plan and proposed folder structure.
3. Identify missing local prerequisites, especially whether MySQL 8 is installed and reachable. Do not silently replace MySQL with SQLite, Firebase, Supabase, MongoDB, JSON files, or an in-memory database.
4. Then implement in milestones. Run the backend, frontend, migrations, seed script, and tests where the environment permits.
5. If a required local service is unavailable, finish the code and provide exact Windows setup commands. Clearly identify what could not be executed.

Do not stop after scaffolding. Do not leave important features as non-functional buttons, static mock data, TODO comments, or hard-coded frontend arrays. Seed data must be inserted into MySQL and displayed through real API calls.

Use sensible engineering judgement for minor unspecified details. Do not expand the product with features explicitly excluded below.

## 1. Product summary

### 1.1 Product name

**Found It**

### 1.2 Product description

Found It is a university-focused portal where people can search for items that other users have reported as found. A person who finds an item that does not belong to them can sign up, upload a photograph and report the item. Someone who believes the item is theirs can search using location and category filters, open the listing, and contact the person who reported it through an in-app contact form.

The main use case is deliberately simple:

- Someone finds an item on campus and posts it on Found It.
- Someone who lost an item visits Found It and searches the existing found-item reports.
- If they identify a likely match, they sign up or log in and send a contact request referencing that exact item.
- The person who posted the item receives the request and decides how to coordinate its return.
- Once the item has been returned, the listing owner removes it from public search by marking it as returned/resolved or deleting their report.

### 1.3 Product objective

Build a usable campus portal while making MySQL a visible, demonstrable part of the project. The application must demonstrate relational database design and real SQL functionality through a dedicated administrator database dashboard and SQL Explorer.

### 1.4 Target environment

- Initial scope: one university campus.
- Initial runtime: local development on Windows.
- Future deployment: frontend can be deployed to Vercel and backend to Render. Deployment is not part of the first milestone.
- The database must remain MySQL in local development and in any future deployment.

## 2. Scope decisions

### 2.1 Included in version 1

- Public landing page and item search.
- Browse found-item reports after submitting search criteria.
- Search by campus location, category, item type/name, and optional quantity/date criteria.
- Guest browsing without an account.
- Account registration and login.
- Authenticated users can create found-item listings.
- At least one image is required when creating a new listing.
- Authenticated users can edit or remove only their own listings.
- Authenticated users can contact a listing owner through an in-app form.
- Listing owners can view contact requests related to their listings.
- Mark a listing as returned/resolved so it no longer appears in public results.
- MySQL relational database with multiple related tables, foreign keys, indexes, migrations, and synthetic seed data.
- Admin-only database dashboard, schema/table viewer, and predefined SQL Explorer.
- Synthetic data that is sufficiently varied to make dashboard statistics and SQL queries meaningful.
- Responsive, marketplace-style interface with minimal navigation and only the required features.

### 2.2 Explicitly excluded from version 1

Do not implement these unless requested later:

- A separate “I lost an item” report or lost-item submission workflow.
- A `lost_items` table. The main listing entity is `found_items`.
- AI-powered image recognition or semantic matching.
- Automatic lost/found matching recommendations.
- Compulsory admin approval of ownership claims.
- Public display of reporter phone numbers or email addresses.
- Real-time chat, video calls, or external email delivery.
- Multiple universities or a multi-tenant architecture.
- Separate staff, moderator, or department-admin roles.
- Payment, delivery, reward, or collection-fee features.
- Cloud image hosting in the first local version.
- Arbitrary unrestricted SQL execution from the browser.

## 3. Users, access, and permissions

There are only two account roles in version 1: `user` and `admin`.

### 3.1 Guest

A guest can:

- Open the website.
- Submit the search form.
- View matching found-item cards and item details.
- View public item information and reference codes.

A guest cannot:

- Create a found-item report.
- Send a contact request.
- View private account information or the admin database dashboard.

When a guest tries to post or contact someone, show a clear sign-up/login prompt. After successful authentication, return the user to the action they originally requested where practical.

### 3.2 Registered user

A registered user can:

- Search and browse like a guest.
- Create a found-item report.
- Upload one or more images; at least one image is required.
- Edit their own found-item reports.
- Mark their own listing as returned/resolved.
- Remove/delete their own listing, with a confirmation step.
- Send a contact request against a specific found-item reference.
- View contact requests sent to them for their listings.
- View contact requests they have sent.
- View a simple “My Listings” and “My Enquiries” area.

A registered user must not edit, remove, or view private contact data belonging to another user's account.

### 3.3 Admin

There is one seeded admin account for the project owner. The admin role exists primarily to access the database showcase.

Admin-only capabilities:

- Open the Admin Database Dashboard.
- View database overview statistics.
- View the list of MySQL tables and their columns.
- Browse safe, paginated table records.
- Open the SQL Explorer and run the predefined SQL query catalogue.
- View query text, a plain-language explanation, and live query results.
- Inspect basic schema information such as primary keys, foreign keys, and indexes where practical.

Do not create a large admin moderation system. Normal users manage their own listings. The admin database route and every admin API endpoint must be protected by backend authorization, not only by hiding frontend links.

### 3.4 Initial admin account configuration

Use this admin email as the seed configuration:

`manasteam@gmail.com`

Do **not** hard-code the admin password in source code, SQL seed files, README examples, frontend code, or this specification. Read it from a local environment variable named `ADMIN_PASSWORD`, hash it using a secure password-hashing algorithm, and store only the hash in MySQL. The project owner will set the value in their local `.env` file.

The admin seed operation must be idempotent: rerunning it must not create duplicate admin accounts or overwrite an existing admin password unexpectedly.

## 4. Core user journeys

### 4.1 Guest searches for an item

1. Open the Found It landing page.
2. The page does not immediately show every listing.
3. The visitor is asked to narrow the search using:
   - Campus location (required).
   - Category (required).
   - Item name/type or subcategory (recommended; allow a sensible “Any” option if needed).
   - Quantity/number of similar items (optional, if known).
   - Approximate found date or date range (optional).
4. Submit the search.
5. The frontend requests matching rows from the FastAPI backend using query parameters.
6. Display matching records in marketplace-style cards.
7. The visitor opens an item detail page.
8. The visitor selects “Contact reporter”.
9. If not authenticated, redirect to login/register and then return to the contact action.

The search form must use database-backed category and location options. Do not hard-code category or location options separately in the React frontend.

### 4.2 User posts an item they found

1. User registers or logs in.
2. Selects “Report a Found Item”.
3. Completes the report form.
4. Uploads at least one image.
5. Submits the form.
6. FastAPI validates the fields and image, writes the listing and image metadata to MySQL, and stores the image file locally.
7. The new listing appears in search results when its filters match.
8. The owner can later edit the report or mark it returned/resolved.

### 4.3 User contacts a reporter

1. User opens a specific item detail page.
2. Selects “Contact reporter”.
3. Completes a contact form containing a message and the item reference.
4. Backend verifies that the user is authenticated and the item is still contactable.
5. Backend creates a row in `contact_requests` linked to the item, sender, and recipient/listing owner.
6. The listing owner can see the request in “My Enquiries” or the relevant listing detail.
7. The requester can see the request in “My Enquiries”.

For the local first version, the contact form is an in-app database-backed workflow. Do not claim that it sends an email or SMS. Do not expose personal email addresses or phone numbers on public item pages. Show a clear success state after the request is stored.

### 4.4 User closes a listing after item recovery

1. The listing owner opens “My Listings”.
2. Selects “Mark as Returned” or “Remove Listing”.
3. Confirms the action.
4. Backend updates the item's status and records the status change.
5. Resolved/removed listings disappear from normal public search results.
6. The record remains available to the database dashboard and analytics where appropriate.

Prefer a soft-delete/archive approach for the normal user-facing remove action so the course-project database can preserve status history and report statistics. If a hard-delete action is provided, it must be explicit, confirmed, restricted to the owner for their own listing, and handle dependent image/contact rows safely.

## 5. Functional requirements by module

### 5.1 Public landing and search

- Brand name: **Found It**.
- Short explanatory text: “Find something that may be yours, or report something you found.”
- Main call to action: “Find an Item”.
- Secondary call to action: “Report a Found Item”.
- Search controls for location, category, item type/subcategory or keyword, optional quantity, and optional date range.
- Location and category options must load from MySQL through the API.
- Do not show all item cards before the visitor submits a search.
- Include loading, no-results, validation, and error states.
- Search results must be paginated from the backend.
- Support filtering by location, category, subcategory, item keyword, and date range. Quantity can be used as a filter when supplied.
- Sort options: newest first, oldest first, and optionally category/location.

### 5.2 Found-item listing cards

Each card should show only useful information:

- Primary item image.
- Item title.
- Category/subcategory.
- Found location.
- Found date.
- Short description excerpt.
- Public reference code.
- Availability status, only when relevant.
- “View Details” action.

Do not show the reporter's private email address or phone number.

### 5.3 Item detail page

Show:

- Image gallery or primary image.
- Item title and description.
- Category and subcategory.
- Found location and found date/time.
- Quantity if supplied.
- Public reference code.
- “Contact Reporter” action.

Hide private fields such as password hashes, internal database IDs where not needed, and reporter contact details.

### 5.4 Authentication

- Registration: name, email, password, confirm password, and optional phone/department fields only if useful.
- Login: email and password.
- Validate email format and unique email at the backend.
- Hash passwords with Argon2 or bcrypt. Never store plain-text passwords.
- Use secure token-based authentication suitable for a local React + FastAPI application.
- Keep secrets in environment variables.
- Add logout and authenticated route handling.
- A guest can browse without registration.
- A signed-in user can post and contact.

### 5.5 Create/edit found-item report

Required fields:

- Item title/name.
- Category.
- Found location.
- Found date/time (date required; time can be optional/unknown).
- Description.
- At least one image.

Optional fields:

- Subcategory.
- Quantity/count (default 1; validate positive integer).
- Item condition.
- Additional distinguishing details.

Validation:

- Reject missing required fields.
- Require at least one valid image on creation.
- Allow an existing image to remain when editing text fields.
- Validate image MIME type and file size on the backend.
- Initially support JPEG, PNG, and WebP with a reasonable size limit (for example, 5 MB per image).
- Store a generated safe filename, not the raw user-supplied path.
- An owner may edit only their own record.

### 5.6 Contact workflow

- Contact form must reference a real `found_items` record.
- Store sender, listing owner/recipient, item, message, status, and timestamps.
- Do not allow users to contact themselves about their own listing.
- Reject contact requests for resolved or removed listings.
- Do not display private contact information publicly.
- Add an in-app notification or visible enquiry indicator for the listing owner.
- Include request statuses such as `new`, `read`, and `closed`.
- The owner can mark a request as read/closed.

### 5.7 My Listings and My Enquiries

“My Listings”:

- List only the signed-in user's reports.
- Show available/resolved/removed status.
- Provide edit, mark returned, and remove actions.
- Show the number of contact requests per listing if practical.

“My Enquiries”:

- Show requests the user has sent.
- Show requests received for their listings.
- Display item reference/title, message, other party's display name, status, and timestamp.
- Do not leak information belonging to unrelated users.

### 5.8 Admin database dashboard

Create a separate route such as `/admin/database`.

Dashboard sections:

1. **Overview** — total accounts, total found-item reports, active listings, resolved/removed listings, total contact requests, category count, location count.
2. **Table Explorer** — list database tables, columns, data types, primary/foreign keys where practical, and paginated rows.
3. **SQL Explorer** — predefined query catalogue. Each entry has a title, SQL text, explanation, Run button, result table, row count, and an error/loading state.
4. **Schema Overview** — show the relational table list and relationships; a simple ER diagram is useful but optional.
5. **Query Examples** — group the query library by SELECT/filtering, JOINs, aggregation, subqueries, views, and reporting.

Important safety and implementation constraints:

- Only an authenticated admin can access these routes and APIs.
- Do not send database credentials to React.
- Do not expose password hashes, token values, environment variables, or secret settings in table previews.
- Do not provide unrestricted arbitrary SQL execution from a browser text box.
- The first version should run a curated catalogue of parameterized, predefined read-only SQL queries. Show the actual SQL text so the MySQL functionality is visible for demonstration.
- Use a backend allowlist of query IDs. Never trust a query ID or table name without validation.
- Limit result sizes and paginate table browsing.
- All displayed rows/statistics must come from the live MySQL database, not hard-coded examples.

## 6. MySQL database design

Use MySQL 8 with InnoDB, `utf8mb4`, primary keys, foreign keys, unique constraints, sensible indexes, and timestamps. Use SQLAlchemy models and Alembic migrations, but ensure the application actually connects to MySQL.

The following is the recommended initial relational model. The agent may refine field types and naming if relationships and required behaviours remain intact.

### 6.1 `users`

Purpose: authentication and account identity.

Suggested columns:

- `id` — primary key.
- `full_name` — display name.
- `email` — unique, indexed.
- `password_hash` — never returned by APIs.
- `role` — `user` or `admin`.
- `phone` — optional and private.
- `department` — optional display/profile information; not required for registration.
- `is_active` — boolean.
- `created_at`, `updated_at`.

Guests are not stored as users. Do not require a university email domain because the product allows anyone to use the portal within the university use case.

### 6.2 `categories`

Purpose: broad item categories.

Suggested columns: `id`, `name` (unique), `slug`, `description`, `is_active`, timestamps.

### 6.3 `subcategories`

Purpose: more specific item types within a category.

Suggested columns: `id`, `category_id` (FK), `name`, `slug`, `is_active`.

Add a unique constraint on `(category_id, name)`.

### 6.4 `campus_locations`

Purpose: standardized campus locations for search and reporting.

Suggested columns: `id`, `name`, `building_or_area`, `description`, `is_active`.

Examples: Library, Main Block, Canteen, Cafeteria, Auditorium, Computer Lab, Sports Ground, Parking Area, Hostel, Seminar Hall, Department Block, and Reception.

### 6.5 `found_items`

Purpose: the central listing table.

Suggested columns:

- `id` — primary key.
- `reference_code` — unique human-readable code such as `FI-2026-000123`.
- `title`.
- `description`.
- `category_id` — FK to `categories`.
- `subcategory_id` — nullable FK to `subcategories`.
- `location_id` — FK to `campus_locations`.
- `reporter_id` — FK to `users`.
- `found_at` — date/time item was found.
- `quantity` — positive integer, default 1.
- `condition` — optional.
- `status` — for example `available`, `returned`, or `removed`.
- `created_at`, `updated_at`, `resolved_at` (nullable).

Public search must return only listings with status `available`. A user marking an item returned/resolved must make it disappear from normal public search.

Add indexes useful for common filters, at minimum on `status`, `category_id`, `location_id`, `found_at`, and a composite index for common status/category/location filtering where appropriate.

### 6.6 `item_images`

Purpose: image metadata for found-item listings.

Suggested columns: `id`, `item_id` (FK), `image_path`, `original_filename` (sanitized), `is_primary`, `uploaded_at`.

Store image files in local storage for the first version and store only the relative path/URL in MySQL. Do not store image binaries in a database BLOB for this project.

### 6.7 `contact_requests`

Purpose: a user's in-app message to the reporter of a specific listing.

Suggested columns: `id`, `item_id` (FK), `sender_id` (FK to users), `recipient_id` (FK to users), `message`, `status` (`new`, `read`, `closed`), `created_at`, `updated_at`.

Add indexes on `item_id`, `sender_id`, `recipient_id`, and `status`.

### 6.8 `notifications`

Purpose: lightweight in-app notifications.

Suggested columns: `id`, `user_id` (FK), `type`, `title`, `message`, `related_item_id` (nullable FK), `related_contact_request_id` (nullable FK), `is_read`, `created_at`.

At minimum, create a notification when a user receives a new contact request.

### 6.9 `item_status_history`

Purpose: preserve a record of listing status changes.

Suggested columns: `id`, `item_id` (FK), `changed_by_user_id` (FK), `old_status`, `new_status`, `note` (nullable), `created_at`.

Create a history row when a listing is marked returned or removed. Use a transaction so the listing update and history insert succeed or fail together.

### 6.10 `admin_audit_logs`

Purpose: record important admin database-dashboard actions.

Suggested columns: `id`, `admin_user_id` (FK), `action`, `target_type`, `target_reference`, `created_at`.

Do not store passwords, tokens, or sensitive query parameters in audit logs.

### 6.11 Optional `departments` table

A normalized departments table is optional. Add it only if it is genuinely used by user profiles or reporting. Do not create tables solely to inflate the table count.

### 6.12 Relationship summary

- One `category` has many `subcategories`.
- One `category` has many `found_items`.
- One `subcategory` can be assigned to many `found_items`.
- One `campus_location` has many `found_items`.
- One `user` can report many `found_items`.
- One `found_item` has many `item_images`.
- One `found_item` can have many `contact_requests`.
- A user can send many contact requests and receive many contact requests.
- One user has many notifications.
- One found item has many status-history rows.
- One admin user can have many admin audit log rows.

## 7. Categories and seed reference data

Create these initial categories and relevant subcategories. Categories and subcategories must be database-backed and editable through migrations/seed data, not a hard-coded React array.

1. **Electronics** — mobile phones, chargers, earphones, headphones, laptops, USB drives, calculators, power banks.
2. **Bottles & Drinkware** — water bottles, tumblers, flasks, bottle caps.
3. **Clothing & Accessories** — jackets, caps, hats, shoes, umbrellas, watches, sunglasses.
4. **Bags** — backpacks, laptop bags, wallets, pouches.
5. **Stationery** — notebooks, pens, pencil cases, files, folders, geometry boxes.
6. **Books & Documents** — textbooks, notebooks, ID cards, access cards, certificates, printed documents.
7. **Keys & Cards** — keys, keychains, access cards, transport cards.
8. **Sports Equipment** — balls, rackets, shoes, gym accessories.
9. **Personal Items** — spectacles cases, grooming items, lunch boxes.
10. **Miscellaneous** — items that do not fit the above categories.

The agent may normalize categories/subcategories further but must preserve these examples.

## 8. Synthetic data requirements

The database must be useful for demonstrating the dashboard and SQL queries immediately after setup. Seed data must be synthetic and clearly fictional. Never insert real personal information other than the configured admin email.

Suggested seed volume:

| Entity | Suggested rows |
|---|---:|
| Synthetic user accounts | 100–150 |
| Categories | 10 |
| Subcategories | 30–45 |
| Campus locations | 15–20 |
| Found-item listings | 180–250 |
| Item image records | At least 25 useful demo image records; more if simple |
| Contact requests | 60–100 |
| Notifications | 40–80 |
| Item status history | 50–100 |

Requirements:

- Use fictional names and reserved/example email domains for synthetic users.
- Distribute found items across all categories and campus locations.
- Use a realistic mix of recent and older found dates.
- Include available, returned, and removed statuses so status analytics have meaningful results.
- Include contact requests in `new`, `read`, and `closed` states.
- Give demo listings local image assets. Reusing a small set of category-specific demo images is acceptable.
- Newly created user listings must support actual user-uploaded images dynamically.
- Make the seed script repeatable without duplicating records. Use stable identifiers/upsert logic or clear-and-reseed logic with an explicit warning.
- Do not use a hard-coded array of frontend listings as the primary data source.

## 9. SQL functionality and SQL Explorer

MySQL functionality is a major course-project deliverable. The interface must visibly demonstrate the SQL being used and show results from the actual MySQL database.

### 9.1 Minimum SQL concepts to demonstrate

- `CREATE TABLE` through schema migrations.
- Primary keys and foreign keys.
- `INSERT` through registration, report creation, contact requests, and seed data.
- `SELECT` for retrieving listings and records.
- `WHERE` for location/category/status/date filtering.
- `UPDATE` for editing a listing and changing statuses.
- `DELETE` or a documented soft-delete strategy for removing reports.
- `ORDER BY` for sorting search results.
- `LIMIT` and pagination.
- `INNER JOIN` and `LEFT JOIN` for related records.
- `GROUP BY` for category, location, status, and monthly summaries.
- `HAVING` for filtered aggregate results.
- Aggregate functions such as `COUNT`, `AVG`, `MIN`, and `MAX`.
- Subqueries for more advanced reports.
- At least one CTE if supported cleanly by MySQL 8.
- At least one useful database view.
- Indexes for frequently filtered fields.
- Transactions for multi-step operations such as status update plus history insertion.

### 9.2 Minimum predefined SQL query catalogue

Create at least 15 named, working query examples. The exact SQL must be MySQL 8 compatible. Each query entry should include a title, category/concept, short explanation, SQL text, and a live Run action.

Recommended catalogue:

1. Total number of found-item reports.
2. Number of currently available items.
3. Found-item count grouped by category (`GROUP BY`).
4. Found-item count grouped by campus location (`GROUP BY`).
5. Most recently reported items (`ORDER BY`).
6. Listings with reporter names (`JOIN` users to found_items).
7. Listings with category and location names (`JOIN` multiple tables).
8. Contact-request count per listing (`LEFT JOIN` and aggregation).
9. Categories with more than a chosen number of reports (`HAVING`).
10. Users who have reported more than the average number of items (subquery).
11. Monthly found-item reporting trend (date aggregation).
12. Counts by listing status (conditional aggregation or `GROUP BY`).
13. Subcategory-level report counts.
14. Listings that have not received any contact requests (`LEFT JOIN` plus `IS NULL`).
15. Users with the highest number of reports.
16. Found items with more than one image.
17. Contact requests grouped by status.
18. Available listings older than a selected number of days.

At least 15 must be fully implemented; implementing all 18 is preferred.

### 9.3 Views

Create at least one useful MySQL view, preferably:

- `v_active_found_items` — available listings joined with category, subcategory, location, and reporter display name; exclude private credentials and contact fields.
- Optionally `v_category_listing_summary` — listing counts grouped by category.

Show views in the schema/table explorer if practical.

### 9.4 SQL Explorer execution rules

- Query text must be visible in the UI for learning/demonstration.
- Query results must be fetched from MySQL when Run is clicked.
- Use predefined query IDs and a server-side allowlist.
- Use bound parameters for filters.
- Do not accept arbitrary SQL from untrusted frontend input in version 1.
- Never expose secrets or password hashes in results.
- Return structured result columns/rows and handle empty results cleanly.

## 10. Recommended technology stack

### Frontend

- React.
- Vite.
- TypeScript preferred.
- Tailwind CSS or a consistent CSS module design system.
- React Router for routing.
- A small reusable component system for forms, cards, modals, alerts, and tables.
- Use a real API client to communicate with FastAPI.

### Backend

- Python 3.11+.
- FastAPI.
- Pydantic for request/response validation.
- SQLAlchemy 2.x for database access.
- Alembic for schema migrations.
- PyMySQL or another reliable MySQL driver.
- Secure password hashing (Argon2 preferred, bcrypt acceptable).
- JWT-based authentication or another well-implemented token approach.

### Database

- MySQL 8.
- InnoDB.
- `utf8mb4` character set.

### Image storage

- Local filesystem for the first version.
- Store uploaded images under a backend-managed `uploads/` directory.
- Store relative file paths in MySQL.
- Serve uploaded images through a controlled FastAPI static route.
- Do not use Cloudinary or an external storage service for the first local build.

### Testing and quality

- Pytest for backend API/database tests.
- Basic frontend tests where useful.
- Linting/formatting where practical.
- Environment-based configuration.
- Meaningful API errors and frontend loading/error/empty states.

## 11. Suggested project structure

The agent may adjust names, but keep frontend and backend clearly separated.

```text
found-it/
├── frontend/
│   ├── public/
│   │   └── demo-images/
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── context/ or stores/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── styles/
│   │   ├── types/
│   │   └── utils/
│   ├── .env.example
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── crud/ or services/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── queries/
│   │   └── main.py
│   ├── alembic/
│   ├── uploads/
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── docs/
│   ├── DATABASE_SCHEMA.md
│   └── SQL_QUERY_CATALOGUE.md
├── .gitignore
└── README.md
```

## 12. API requirements

Use a consistent `/api` prefix, JSON responses, correct HTTP status codes, and Pydantic schemas. Names may be refined while preserving functionality.

### Public/authentication endpoints

- `GET /api/health` — backend health and safe database connectivity status.
- `GET /api/categories` — categories and subcategories.
- `GET /api/locations` — active campus locations.
- `GET /api/items` — paginated public search with filters such as `location_id`, `category_id`, `subcategory_id`, `q`, `quantity`, `date_from`, `date_to`, `sort`, `page`, and `page_size`.
- `GET /api/items/{reference_code}` — public item detail.
- `POST /api/auth/register` — create user account.
- `POST /api/auth/login` — authenticate.
- `GET /api/auth/me` — current user profile.

### Authenticated user endpoints

- `POST /api/items` — create found-item listing with image upload.
- `PATCH /api/items/{id}` — edit own listing.
- `POST /api/items/{id}/images` — add image to own listing if implemented separately.
- `PATCH /api/items/{id}/status` — mark own listing returned/resolved or otherwise update allowed status.
- `DELETE /api/items/{id}` — remove own listing with safe soft-delete/archive behaviour.
- `GET /api/me/items` — user's listings.
- `POST /api/items/{id}/contact` — create contact request for the listing.
- `GET /api/me/contact-requests/sent` — sent requests.
- `GET /api/me/contact-requests/received` — received requests for the user's listings.
- `PATCH /api/contact-requests/{id}/status` — recipient marks request read/closed.
- `GET /api/me/notifications` — current user's notifications.
- `PATCH /api/me/notifications/{id}/read` — mark notification read.

### Admin-only endpoints

- `GET /api/admin/database/overview` — live database counts.
- `GET /api/admin/database/tables` — safe table/schema list.
- `GET /api/admin/database/tables/{table_name}/rows` — validated, paginated table viewer.
- `GET /api/admin/sql/queries` — predefined query catalogue metadata and SQL display text.
- `POST /api/admin/sql/queries/{query_id}/run` — execute one allowlisted read-only query with validated parameters.
- Optional `GET /api/admin/database/relationships` — relationship/schema metadata.

All user-specific and admin-specific endpoints must enforce authorization in FastAPI dependencies. Frontend route guards alone are insufficient.

## 13. UI and visual direction

### 13.1 Overall style

Use a minimal marketplace-style interface. Prioritize discoverability and clear item imagery over decorative dashboard elements.

Design characteristics:

- Clean, modern, uncluttered layout.
- Strong item photographs and readable listing cards.
- Neutral background with one consistent accent colour.
- Clear typography and spacing.
- Responsive on laptop, tablet, and mobile widths.
- Consistent button, form, modal, table, and status styles.
- Use accessible labels, keyboard focus states, and sufficient contrast.

### 13.2 Suggested navigation

- Found It logo/name.
- Find Items.
- Report Found Item (visible to guests, but prompts login when selected).
- My Listings (authenticated).
- My Enquiries (authenticated).
- Login/Register or profile menu.
- Admin Database (admin only).

### 13.3 Required pages

1. Landing/search page.
2. Search results page or search results section.
3. Found-item detail page.
4. Register page.
5. Login page.
6. Report a Found Item page/form.
7. Edit listing page/form.
8. My Listings page.
9. My Enquiries page.
10. Admin Database Dashboard.
11. Admin Table Explorer.
12. Admin SQL Explorer.

Do not add pages for excluded features such as reporting a lost item or AI matches.

## 14. Local configuration and setup

The first build must run locally on Windows. Document exact PowerShell commands in `README.md`.

### 14.1 Prerequisites

- Python 3.11 or newer.
- Node.js LTS and npm.
- MySQL Server 8.x running locally.
- Git recommended.

### 14.2 Database

Use a database named `found_it_db`. Document the SQL to create a dedicated local application user and grant privileges only on this database. Do not put real database passwords in committed files.

Example database creation:

```sql
CREATE DATABASE found_it_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
```

### 14.3 Backend environment variables

Create `backend/.env.example` with placeholders similar to:

```env
APP_ENV=development
APP_NAME=Found It API
DATABASE_URL=mysql+pymysql://foundit_app:CHANGE_ME@localhost:3306/found_it_db
JWT_SECRET_KEY=CHANGE_ME_TO_A_LONG_RANDOM_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_EMAIL=manasteam@gmail.com
ADMIN_PASSWORD=SET_THIS_LOCALLY
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=5
FRONTEND_ORIGIN=http://localhost:5173
```

The real `backend/.env` must be ignored by Git. Never commit it.

### 14.4 Frontend environment variables

Create `frontend/.env.example` with:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Do not store secrets in Vite environment variables. Anything beginning with `VITE_` is exposed to the browser.

### 14.5 Expected run commands

Document commands equivalent to these, adapting them to the final folder structure:

Backend (PowerShell):

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with local MySQL and admin secrets
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

Frontend (a separate PowerShell terminal):

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Use the actual seed module name created by the implementation. Include a documented way to create the first admin account from environment variables. Include a documented reset/reseed command with a warning before destructive actions.

## 15. Security, privacy, and reliability

- Never store plain-text passwords.
- Never commit `.env` files or secrets.
- Never expose database credentials to the React application.
- Validate every user-provided field on the backend.
- Use parameterized SQL/ORM queries for user-controlled search parameters.
- Validate image file type and size on the backend; generate safe filenames.
- Users can modify only their own listings and contact requests.
- Admin APIs require the admin role.
- Do not expose email/phone publicly on item cards or detail pages.
- Do not return `password_hash` from any API or table-view response.
- Paginate large lists and table views.
- Use database transactions for multi-step state changes.
- Use foreign keys and sensible delete behaviour.
- Handle missing images, missing records, invalid filters, expired sessions, and database connection errors gracefully.
- Do not silently fall back to SQLite if MySQL is unavailable.

## 16. Acceptance criteria

The first version is considered complete only when all of the following work:

### Main product

- [ ] A guest can open Found It and use the search form without registering.
- [ ] The application does not show every listing before search criteria are submitted.
- [ ] Search controls load categories and locations from MySQL.
- [ ] Search results are retrieved from MySQL through FastAPI and support multiple filters.
- [ ] Item cards and detail pages show images, category, location, found date, and reference code.
- [ ] A guest trying to post or contact is directed to sign up/login.
- [ ] A registered user can log in and create a found-item report.
- [ ] A new listing cannot be submitted without at least one valid image.
- [ ] The uploaded image is stored locally and its path is recorded in MySQL.
- [ ] The new listing appears in search results without rebuilding or editing frontend code.
- [ ] A user can edit only their own listing.
- [ ] A user can mark their own listing returned/resolved or remove it.
- [ ] Resolved/removed listings no longer appear in public search.
- [ ] A user can contact the reporter of a specific available listing.
- [ ] The contact request is stored in MySQL with the correct item, sender, and recipient references.
- [ ] The listing owner can see received requests; the sender can see sent requests.
- [ ] No public listing reveals personal email/phone details.

### MySQL and admin demonstration

- [ ] The application uses MySQL 8 in local development; no SQLite substitute is used.
- [ ] Schema migrations create the required related tables and constraints.
- [ ] Seed script creates varied synthetic data and can be run safely more than once.
- [ ] Admin login is created from local environment variables and passwords are hashed.
- [ ] A normal user cannot access admin database pages or APIs.
- [ ] Admin dashboard cards show counts from live MySQL queries.
- [ ] Table Explorer lists real MySQL tables and displays safe, paginated records.
- [ ] SQL Explorer shows at least 15 actual MySQL query examples.
- [ ] Clicking Run executes the selected query against MySQL and displays live results.
- [ ] SQL examples visibly demonstrate SELECT, WHERE, JOIN, LEFT JOIN, GROUP BY, HAVING, subqueries, aggregates, and views.
- [ ] Creating, editing, resolving, and removing listings changes the database and relevant dashboard/query results.
- [ ] Password hashes and secrets are never shown in the dashboard.

### Engineering and handover

- [ ] Backend and frontend can be started locally using README instructions.
- [ ] API health endpoint works and reports safe database connectivity status.
- [ ] Backend tests cover authentication, item ownership, listing creation, contact requests, and admin access where practical.
- [ ] No major buttons are placeholders.
- [ ] No core page depends on hard-coded mock listings.
- [ ] README explains architecture, database setup, migrations, seed data, demo admin setup, and run commands.
- [ ] `DATABASE_SCHEMA.md` explains tables and relationships.
- [ ] `SQL_QUERY_CATALOGUE.md` documents the SQL demonstrations.

## 17. Implementation milestones

Build and verify in this order. Keep the application runnable after each milestone.

**Milestone 1 — Foundation and MySQL**

- Set up frontend and backend folders.
- Configure MySQL connection and health check.
- Create SQLAlchemy models and Alembic migrations.
- Add categories, subcategories, locations, users, found items, images, contact requests, notifications, history, and audit tables.
- Add idempotent synthetic seed script.
- Verify records exist in MySQL directly.

**Milestone 2 — Authentication and core item API**

- Register/login/logout/current-user flow.
- Password hashing and admin seed.
- Category/location endpoints.
- Search/filter/pagination endpoints.
- Create/edit/status/remove found-item endpoints with ownership checks.
- Local image upload and static file serving.

**Milestone 3 — Student-facing React portal**

- Landing page and search gate.
- Search results and item detail page.
- Registration/login.
- Report/edit found item forms.
- My Listings.
- Responsive marketplace-style components.

**Milestone 4 — Contact workflow**

- Contact form linked to an item reference.
- Contact request persistence.
- My Enquiries for sent and received requests.
- Notifications or enquiry indicators.
- Request status updates.

**Milestone 5 — Admin database showcase**

- Admin route and backend authorization.
- Live database overview.
- Safe table/schema viewer.
- At least 15 predefined SQL query examples.
- SQL Explorer result tables.
- Views and schema documentation.

**Milestone 6 — Verification and handover**

- Test all key journeys.
- Fix errors and empty/loading states.
- Verify SQL results update after CRUD operations.
- Confirm no secrets are committed.
- Complete README and database/SQL documentation.
- Provide a concise handover: features completed, files created, setup commands, test results, and anything that remains blocked.

## 18. Final instruction to Antigravity

Implement **Found It** according to this specification. Prioritize a genuinely working end-to-end local application over decorative complexity. MySQL is mandatory and must power the portal, seed data, analytics, table viewer, and SQL Explorer. Keep the public experience focused on searching found-item reports and posting items that were found. Do not add a lost-item submission flow or automatic matching system.

Start by inspecting the workspace and confirming the local prerequisites. Then implement the milestones in order, test each one, and keep the README updated as you go. If MySQL is not available in the environment, do not substitute another database: complete the MySQL implementation and give exact Windows instructions for connecting it locally.
