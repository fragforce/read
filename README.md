# Fragforce Read

Audio playback service for the VTO Book Reading project. Salesforce/Fragforce volunteers record themselves reading children's books aloud, and this service delivers those recordings to patients at Children's Miracle Network hospitals via QR codes.

## How It Works

1. A donated children's book has a QR code + password printed inside
2. A child or caregiver at the hospital scans the QR code
3. They enter the password on the playback page
4. The recording streams in their mobile browser - no app, no login

## Components

| Component | Description |
|-----------|-------------|
| **Playback service** | Password-gated page at `read.fragforce.org/b/{id}` that streams audio via HLS/MSE |
| **Narrator portal** | Web interface where volunteers select a book, record in-browser, and submit attestation |
| **Admin panel** | Manage books, narrators, recordings, QR codes, and passwords |

## Architecture

```
QR Code + Password -> read.fragforce.org/b/{id} -> Password Gate -> Stream-Only Playback (HLS/MSE)

Narrator Portal -> Book Queue -> Pre-flight -> In-Browser Recording -> Attestation -> Upload

Admin Panel -> Book/Narrator Management -> QR + Password Generation -> Attestation Review
```

## Key Constraints

- **Password-gated access** - each QR code has a unique password, server-side validated
- **Stream-only playback** - HLS or MSE, no direct file download links
- **No public indexing** - `noindex` meta tags and `X-Robots-Tag` headers
- **Attribution** - publisher, author, illustrator displayed on page and spoken at beginning/end of each recording
- **Opaque URLs** - short random IDs (nanoid), not human-readable slugs

These are commitments made in the publisher permission letter.

## Infrastructure

- Hosted on existing Fragforce infrastructure (container-based)
- Cloudflare for DNS and caching
- `read.fragforce.org` subdomain
- CI/CD builds images, manual deploy to dev/prod
- Expected scale: 10-50 audio files, under 1 GB total

## Development

Built with Django 6.0, Python 3.13, deployed as Docker containers.

```bash
docker compose up -d          # start dev server
docker compose run --rm test  # run tests
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for full setup and workflow documentation, and [REQUIREMENTS.md](REQUIREMENTS.md) for technical requirements.

## Timeline

- **September 2026** - publisher permissions deadline
- **October 2026** - VTO event (recordings happen here)

## License

MIT - see [LICENSE](LICENSE)
