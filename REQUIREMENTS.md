# Technical Requirements

## Playback Service (All Books)

These apply to every book regardless of licensing status.

| Requirement | Details |
|-------------|---------|
| URL scheme | `read.fragforce.org/b/{book-id}` for random narrator, `/b/{book-id}/{narrator-id}` for specific |
| Book IDs | Opaque short identifiers (nanoid/short hash), not slugs |
| Audio format | MP3, 128kbps mono, max 20 minutes per recording |
| Device support | iOS Safari, Android Chrome, other mobile browsers |
| Layout | Responsive, mobile-first, Fragforce branding |
| Error state | Graceful fallback if audio unavailable |
| Load time target | Scan-to-play in under 3 seconds on mobile |
| Attribution display | Book title, author, illustrator on playback page; "As read by [narrator]" |
| QR code | Each physical book gets a QR code linking to its playback page |

## Public Domain Books

Public domain titles have no publisher restrictions. Playback is open to anyone with the QR link.

| Requirement | Details |
|-------------|---------|
| Access | No password required - scan QR and play immediately |
| Delivery | Standard HTML5 `<audio>` element is fine (no streaming protocol needed) |
| Indexing | Still use `noindex` to keep content focused on hospital audience, but not a legal requirement |
| Attribution (spoken) | Narrator states author and illustrator at beginning and end |
| Attribution (written) | Author and illustrator on playback page |
| Book text | Full text displayed in narrator portal for reading from screen |
| Rights | No permission needed, no expiry dates |

## Licensed Books (Publisher Permission Required)

These additional requirements apply only to books where publisher permission has been granted. They reflect commitments made in the formal permission letter.

| Requirement | Details |
|-------------|---------|
| Password gate | Unique password per QR code, server-side validation, short alphanumeric (4-6 chars, no ambiguous characters) |
| Signed URL delivery | Audio served through session-gated Django view, no direct file URLs exposed |
| No download | `Content-Disposition: inline`, URLs require valid session |
| No public indexing | `<meta name="robots" content="noindex">` and `X-Robots-Tag: noindex` header (legal requirement) |
| Publisher attribution (spoken) | Narrator states author, illustrator, AND publisher at beginning and end |
| Publisher attribution (written) | Publisher name/logo prominently displayed on playback page |
| Publisher phrasing | Configurable per book (e.g., "Recorded with permission from [Publisher]. All rights reserved.") |
| Copyright notice | Publisher's required copyright text displayed |
| License tracking | Expiry date per title; system must disable playback when license expires |
| ISBN tracking | 13-digit ISBN stored for each licensed title |
| Book text | NOT displayed in portal - narrators read from physical copy |

## Narrator Portal

| Requirement | Details |
|-------------|---------|
| Book queue | Browse available books, claim one, see recording count vs target |
| Pre-flight checklist | Quiet room, mic connected, water, phone silent, physical book ready (licensed) |
| Mic selection | Choose input device if multiple available |
| Level check | VU meter with test prompt before recording |
| Attribution script | Display exact opening/closing text to read, populated from book metadata |
| Book text display | Full text on screen (public domain) or "read from physical copy" (licensed) with page count |
| Expected duration | Show estimated reading time per book |
| Recording | Web Audio API / MediaRecorder, WAV locally, server-side transcode to MP3 |
| Controls | Pause/resume, re-record (discard current take), live elapsed timer |
| Auto-upload | Recording linked to book and attestation, uploaded on completion |
| Attestation form | Full name, email, book recorded (pre-populated), checkbox confirmation, auto-timestamp |

### Attestation Text

> "I confirm that I have read the complete, unabridged text of this book, stated the required attribution at the beginning and end of my recording, and followed all provided instructions."

### Attribution Script Templates

**Public domain - opening:**
> "This is [Book Title] by [Author], illustrated by [Illustrator]. As read by [Narrator Name]."

**Public domain - closing:**
> "This has been [Book Title] by [Author], illustrated by [Illustrator]. As read by [Narrator Name]."

**Licensed - opening:**
> "This is [Book Title] by [Author], illustrated by [Illustrator], published by [Publisher]. As read by [Narrator Name]."

**Licensed - closing:**
> "This has been [Book Title] by [Author], illustrated by [Illustrator]. Recorded with permission from [Publisher]. All rights reserved."

## Admin Panel

| Requirement | Details |
|-------------|---------|
| Authentication | TBD (Discord OAuth, shared password, or existing Fragforce auth) |
| Book management | Add/edit/remove books with metadata (title, author, illustrator, publisher, ISBN, copyright notice, permission phrasing, public domain flag, license expiry) |
| Recording management | Upload audio, assign to book/narrator, link attestation |
| QR generation | Generate QR code for a book (optionally locked to narrator), output printable image with "As read by" label; include password for licensed titles |
| Attestation review | View all submitted attestations, verify completeness |
| Narrator management | View narrators, their recordings, and queue claims |

## Data Model

### Book

| Field | Type | Notes |
|-------|------|-------|
| id | string (nanoid) | Opaque URL-safe identifier |
| slug | string | Internal human-readable name for admin |
| title | string | Display title |
| author | string | Original book author |
| illustrator | string | Book illustrator |
| publisher | string (nullable) | Publisher name (null for public domain) |
| isbn | string (nullable) | 13-digit ISBN for licensed titles |
| copyright_notice | string (nullable) | Publisher's required copyright text |
| permission_phrasing | string (nullable) | Custom phrasing required by publisher |
| public_domain | boolean | Whether the book is public domain |
| license_expiry | date (nullable) | When licensed rights expire |
| max_narrators | int (nullable) | Cap on recordings, or null for unlimited |
| estimated_duration | string (nullable) | Expected reading time (e.g., "8-12 minutes") |
| full_text | text (nullable) | Full book text for public domain titles |

### Recording

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | Unique recording identifier |
| book_id | string (FK) | Which book |
| narrator_name | string | Display name for "As read by" |
| audio_url | string | Path to audio file in storage |
| duration_seconds | int | Length of recording |
| created_at | datetime | Upload timestamp |

### QR Code

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | Unique QR identifier |
| book_id | string (FK) | Which book |
| narrator_id | uuid (nullable, FK) | Specific narrator, or null for random |
| password | string (nullable) | Unique password for licensed titles (null for public domain) |
| label_text | string | "As read by [name]" text for printing |

### Attestation

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | Unique attestation identifier |
| recording_id | uuid (FK) | Linked recording |
| narrator_name | string | Full legal name |
| narrator_email | string | Contact email |
| book_id | string (FK) | Which book was recorded |
| attested_at | datetime | Submission timestamp |
| attestation_text | string | The exact statement they agreed to |

## Infrastructure

| Requirement | Details |
|-------------|---------|
| Hosting | Existing Fragforce infrastructure, container-based |
| Caching | Cloudflare (DNS already configured) |
| Domain | `read.fragforce.org` |
| Deployment | CI/CD builds container images, manual promote to prod |
| Storage | Local/object storage on existing servers (~1 GB capacity needed) |
| Transcoding | Server-side WAV to MP3 (128kbps mono) |
| Audio storage | Single storage location for all recordings; access control at view layer |

## Decided

1. **Tech stack** - Django (Python), consistent with fragforce.org
2. **Deployment** - Docker containers, same pattern as other Fragforce services
3. **Licensed audio delivery** - Signed/expiring URLs via session-gated Django view. Prevents casual download and link sharing without the complexity of HLS/DRM.
4. **Audio storage** - All recordings (public domain and licensed) stored in the same location. Access control handled at the view layer, not the storage layer.

## Open Decisions

1. **Admin auth** - Discord OAuth, shared password, or existing Fragforce auth?
2. **Hotlinking mitigation** - Cloudflare hotlink protection, referrer blocking, rate limiting?

## Effort Estimate

| Component | Days |
|-----------|------|
| Playback page (public domain - simple audio player) | 1-2 |
| Playback page (licensed - password gate + signed URL delivery) | 2-3 |
| URL routing + narrator selection | 1 |
| Password generation + validation (licensed) | 1 |
| Narrator portal (recording, text display, attestation) | 5-7 |
| Admin panel (upload, manage, QR generation) | 3-5 |
| Audio storage + transcoding pipeline | 2 |
| Domain/DNS/deployment config | 1 |
| QR code + password print layout | 1-2 |
| Publisher attribution config (licensed) | 1 |
| Testing + polish | 2-3 |
| **Total** | **~22-31 days** |
