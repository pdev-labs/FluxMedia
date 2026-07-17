# LAN QR Share Portal

FluxMedia includes a built-in local HTTP web server allowing you to stream or download media files onto phones, tablets, or other devices on the same local network.

## How it Works
1. Starts a Python `socketserver.TCPServer` serving files directly from the configured downloads directory.
2. Generates a QR code in the terminal containing the local network address (e.g. `http://192.168.1.100:8000`).
3. Port auto-allocation: If default port `8000` is already in use, the server automatically scans and overrides to an open port (up to `8020`).

---

## Security & Authentication

By default, the server is password-protected:
- **Username**: Configured via `config.json` (Default: `admin`)
- **Password**: Configured via `config.json` (Default: `admin`)
- **Token Authorization**: On successful authentication, the server returns a temporary Hex Token. Client requests must supply this token in the `Authorization: Bearer <token>` header or as a `?token=<token>` query parameter to access API endpoints.

---

## REST API Endpoints

The HTTP handler maps custom request routes:

* `GET /api/meta`: Returns server info (profile display name, avatar image link, theme colors, and password requirements).
* `POST /api/auth`: Authenticates clients by checking passwords and returns access tokens.
* `GET /api/files`: Lists all downloaded media filenames, sizes, upload dates, and types.
* `GET /api/file/<id>`: Streams or downloads media files. Supports **HTTP Range Requests** (`206 Partial Content`) for fluid video seek/scrubbing on mobile players.
* `GET /api/thumbnail/<id>`: Generates or extracts 320px thumbnail images from videos via FFmpeg, caching them in the `.fluxmedia_thumbs` folder for faster web dashboard load times.
* `GET /api/subtitles/<id>`: Serves `.vtt` / `.srt` subtitle files matching video names.
* `GET /profile_photo`: Serves the user's custom avatar picture.
