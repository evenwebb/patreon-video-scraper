# Patreon Video Extractor

A Python tool to scrape Patreon posts and extract video URLs (Vimeo and YouTube) from creators you're subscribed to.

## Features

- ✅ Cookie-based authentication (no password required)
- ✅ List all subscribed creators
- ✅ **Automatic pagination** - fetches ALL posts from creators (not just the initial page)
- ✅ Bulk scrape posts from single or multiple creators
- ✅ **Dual platform support** - Extract URLs from both Vimeo and YouTube
- ✅ Extract video URLs from text posts and video embeds
- ✅ Date range filtering
- ✅ JSON output with metadata
- ✅ Progress indicators during scraping
- ✅ Handles both public and privacy-protected video links

**Note:** This tool extracts URLs from Vimeo and YouTube videos embedded in posts. It does not support videos hosted directly on Patreon.

## Requirements

- Python 3.7+
- Browser extension to export cookies (Cookie-Editor, EditThisCookie, etc.)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup

### 1. Export Your Patreon Cookies

You need to export your Patreon session cookies to authenticate:

**Using Cookie-Editor (Recommended):**
1. Install [Cookie-Editor](https://cookie-editor.com/) extension for your browser
2. Log into Patreon in your browser
3. Click the Cookie-Editor extension icon
4. Click "Export" → Choose "JSON" format
5. Save the exported data to `cookies.json` in this directory

**Using EditThisCookie:**
1. Install EditThisCookie extension
2. Log into Patreon
3. Click the extension icon
4. Click "Export Cookies"
5. Save to `cookies.json`

**Important:** The `cookies.json` file contains your session data. Keep it secure and never commit it to version control!

## Usage

### Basic Usage

Run the scraper:
```bash
python3 patreon_scraper.py
```

The script will:
1. Authenticate using your cookies
2. List all creators you're subscribed to
3. Prompt you to select a creator (or "all")
4. Optionally apply date filters
5. Scrape posts and extract Vimeo URLs
6. Save results to `output/{creator}_{timestamp}.json`

### Date Range Filtering

When prompted "Apply date range filter?", enter `y` to filter posts by date:

```
Apply date range filter? (y/n): y
Start date (YYYY-MM-DD) or press Enter to skip: 2024-01-01
End date (YYYY-MM-DD) or press Enter to skip: 2024-12-31
```

Supported date formats:
- `YYYY-MM-DD` (e.g., 2024-10-19)
- `YYYY/MM/DD`
- `DD-MM-YYYY`
- `DD/MM/YYYY`

## Project Structure

```
patreon_scraper/
├── patreon_scraper.py      # Main CLI script
├── auth.py                 # Cookie authentication module
├── api_client.py           # Patreon API interactions
├── video_extractor.py      # Video URL extraction (Vimeo & YouTube)
├── utils.py                # Helper functions
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── cookies.json            # Your cookies (not in git)
├── .gitignore              # Git ignore rules
├── README.md               # This file
└── output/                 # Output directory for JSON results
```

## Troubleshooting

### "cookies.json not found"
Make sure you've exported your Patreon cookies and saved them as `cookies.json` in the project directory.

### "Authentication failed"
Your cookies may have expired. Export fresh cookies from your browser.

### "No creators found"
Make sure you have active Patreon memberships and are logged in when exporting cookies.

### "403 Forbidden" errors
This usually means your session has expired. Re-export your cookies.

## Supported Platforms

Currently supports the extraction of video URLs from:
- **Vimeo** - Both public and privacy-protected links
- **YouTube** - All formats (watch, embed, shorts, youtu.be)

**⚠️ Important Limitation:**
This tool **only extracts URLs** from Vimeo and YouTube videos embedded in Patreon posts. It **does NOT extract or download** videos that are hosted directly on Patreon (posts with "Patreon Video" type). To access Patreon-hosted videos, you would need to use a different tool or manually download them from Patreon's website.

## Future Enhancements

Possible features for future versions:
- JDownloader API integration
- Progress bars with tqdm
- Resume/incremental scraping mode
- Multi-threading for faster scraping
- History monitoring to avoid excess scraping when run regularly

## Security Notes

- **Never share your `cookies.json` file** - it contains your session credentials
- The file is automatically excluded from git via `.gitignore`
- Cookies will eventually expire, requiring re-export
- This tool only accesses content you already have permission to view

## Legal Disclaimer

This tool is for personal use only. Only download content from creators you are subscribed to and have permission to access. Respect creators' rights and Patreon's Terms of Service.

## License

This project is provided as-is for personal use.
