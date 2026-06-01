# VDL — Project Rules

## Architecture

```
VideoDownloader (core.py)
├── PlatformManager
│   ├── YtDlpExtractor        ← primary, covers 6 platforms
│   ├── BilibiliExtractor      ← fallback for Bilibili
│   └── DouyinExtractor        ← 3-tier fallback chain
├── CookieStore                ← Netscape format cookies
├── DownloadManager            ← HTTP download + DASH merge via ffmpeg
└── BrowserFingerprint         ← factory, generates Fingerprint dataclass
```

## Key Rules

- **VideoMetadata** fields: `url`, `platform`, `video_id`, `title`, `author`, `duration`, `thumbnail_url`, `description`, `upload_date`, `quality_options`, `content_type`, `gallery_images`
- **DownloadResult** fields: `success`, `file_path`, `file_size`, `duration`, `error`
- **DownloadOptions** fields: `quality`, `output_path`, `filename_template`, `audio_only`, `custom_headers`
- Old field names (`error_message`, `download_time`, `output_dir`, `available_qualities`, `extra_data`) are **deleted**. Do not reintroduce.
- `ExtractionContext.fingerprint` must be a `Fingerprint` dataclass, not `BrowserFingerprint` factory. Use `browser_fingerprint.generate_fingerprint(platform)`.
- `get_download_urls` takes `*, context: ExtractionContext = None` as keyword-only arg. Extract cookies from context, not from kwargs.
- Bilibili DASH returns [video_url, audio_url] — `core.py` detects 2 URLs + VIDEO type → calls `merge_dash_files` with ffmpeg.
- `{id}` filename template uses `metadata.video_id` first, falls back to URL parsing.

## Commands

```bash
pip install -e .                    # install
vdl <url>                           # download
vdl --metadata-only <url>           # info only
python -m pytest tests/ -v          # run tests (skip playwright: --ignore=tests/test_browser_automation.py)
```

## Red Lines

- Do not add `video_id`, `extra_data`, `available_qualities`, `error_message`, `output_dir` (to DownloadOptions) back to models.
- Do not use `datetime.now()` for upload_date — use actual API timestamps.
- Do not swallow exceptions with bare `except: pass` — always log.
- Do not pass `BrowserFingerprint` where `Fingerprint` is expected.
