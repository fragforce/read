# Changelog

All notable changes to Fragforce Reads will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-07-01

### Fixed
- Production image workflow now triggers on release publication in addition to tag pushes

## [1.0.1] - 2026-07-01

### Fixed
- Release workflow now correctly extracts changelog content for single/first version entries
- Release workflow now tags the correct commit (main merge commit) instead of dev branch head
- Dev branch now automatically syncs after main merges to prevent divergence

## [1.0.0] - 2026-07-01

Initial MVP release of Fragforce Reads - an audio playback service for the VTO Book Reading project.

### Added

**Core Recording Features**
- Browser-based audio recording workflow with mic access checks
- Pre-flight checklist for copyright compliance before recording
- Upload progress bar with user-friendly error handling
- Automatic audio remux pipeline for seeking support with ffmpeg
- Recording status tracking (pending, processing, ready, failed)
- Narrator dashboard showing available books and personal recordings
- Recording detail page with playback and flag-for-review functionality
- Profile page for narrators to update name and email
- Re-record capability for flagged recordings

**QR Code System**
- Auto-generated QR codes with short codes and passwords
- QR code labels with book info, narrator name, and password
- Printable QR sheet view for admins
- Short URL redirect (`/q/<code>`) to playback pages
- Case-insensitive password entry with rate limiting

**Playback & Security**
- Public playback page with password protection
- Range request support for audio seeking
- License expiry enforcement at playback time
- Session-based password unlocking (7-day sessions)
- Rate limiting on password attempts (5 attempts, 5-minute lockout)
- Narrator attribution visible before password entry
- Duration display in mm:ss format

**Registration & Authentication**
- Event code registration with rate limiting
- Invite link registration system
- Passphrase login with rate limiting
- Case-insensitive login
- Logout endpoint
- Welcome/login flow at `/login/`

**Admin Features**
- Book management with max narrator limits
- Narrator management with passphrase generation
- Recording admin with status filters and retry action
- QR code management with admin links
- Event code and invite link management

**Infrastructure & Deployment**
- Docker containerization (dev and prod variants)
- PostgreSQL 18.3 support
- GitHub Actions CI/CD (lint, test, coverage, SonarCloud)
- Docker image builds for dev and prod
- Whitenoise static file serving
- SSL security settings with SECURE_SSL flag
- Health check endpoint (`/healthz/`) for internal networks
- Persistent database connections (CONN_MAX_AGE=600)
- Non-root container execution
- Media file storage and serving

**Testing & Quality**
- Comprehensive test suite (146+ tests)
- Coverage reporting
- SonarCloud quality gate integration
- Per-app test package structure
- CODEOWNERS for CI/build config protection

### Security
- Rate limiting on login, event registration, and playback passwords
- Upload size validation (100MB limit)
- Recording duration bounds validation (max 3600s)
- Attestation text length validation (max 5000 chars)
- HTTP method restrictions on all views
- CSRF protection
- Session security with 7-day expiry
- File handle cleanup in range-request serving
- Healthz endpoint restricted to internal networks only

### Changed
- Simplified QR password format from `4alphanumeric-word-word` to `word-word-2digits`
- Narrator attribution now visible before password entry
- Audio files served through view with auth checks (no direct static serving)
- Recovered stuck recordings on app startup (gunicorn/runserver only)

### Fixed
- N+1 query optimization in dashboard view
- File handle leak in range-request audio serving
- Max narrators check when set to 0
- Visited link color on buttons
- Audio URL routing conflicts
- Admin retry action queryset re-evaluation
- Remux claim race condition with SELECT FOR UPDATE SKIP LOCKED
- Signal registration and file cleanup on recording delete
- HTML accessibility and CSS deprecation warnings
- Cognitive complexity in views (SonarCloud)

[1.0.2]: https://github.com/fragforce/read/releases/tag/v1.0.2
[1.0.1]: https://github.com/fragforce/read/releases/tag/v1.0.1
[1.0.0]: https://github.com/fragforce/read/releases/tag/v1.0.0
