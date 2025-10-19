"""
Configuration Settings for Patreon Vimeo Extractor

Edit these settings to customize the scraper's behavior.
"""

# ============================================================================
# AUTHENTICATION
# ============================================================================

# Directory where cookie files are stored
COOKIES_DIR = "cookies"

# Cookie filename (will be searched for in COOKIES_DIR)
# If cookies.json exists, it will be used. Otherwise, if exactly one .json
# file exists in COOKIES_DIR, it will be used automatically.
COOKIES_FILE = "cookies.json"


# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

# Directory where output files will be saved
OUTPUT_DIR = "output"

# Organize output files in creator-specific subfolders
# True: output/CREATOR/CREATOR_20251019_113223.json
# False: output/CREATOR_20251019_113223.json
OUTPUT_ORGANIZE_BY_CREATOR = True

# Enable/disable JSON export (with full metadata)
OUTPUT_JSON = True

# Enable/disable raw URL txt export (one URL per line)
OUTPUT_RAW_URLS = True

# Deduplicate URLs in raw txt export (independent from JSON deduplication)
DEDUPLICATE_RAW_URLS = True

# Output filename format (uses Python string formatting)
# Available variables: {creator_vanity}, {timestamp}
OUTPUT_FILENAME_FORMAT = "{creator_vanity}_{timestamp}.json"

# Timestamp format for output filenames (Python strftime format)
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


# ============================================================================
# SCRAPING SETTINGS
# ============================================================================

# Maximum number of posts to fetch per creator (None = all posts)
# Set to a number to limit scraping (e.g., 50 for most recent 50 posts)
MAX_POSTS_PER_CREATOR = None

# Show progress indicators during scraping
SHOW_PROGRESS = True

# Delay between API requests in seconds (to avoid rate limiting)
# Set to 0 for no delay, or increase if you get rate limited
REQUEST_DELAY = 0.0

# Number of retry attempts for failed API requests
MAX_RETRIES = 3

# Timeout for HTTP requests in seconds
REQUEST_TIMEOUT = 30


# ============================================================================
# POST PROCESSING
# ============================================================================

# Automatically fetch full details for video_embed posts
# (Required to get embed data for video posts)
ENRICH_VIDEO_EMBEDS = True

# Include posts without video URLs in output
INCLUDE_POSTS_WITHOUT_VIDEOS = True

# Skip saving output file if no video URLs found for creator
SKIP_EXPORT_IF_NO_VIDEOS = True

# Sort posts by date in output (True = newest first, False = keep API order)
SORT_POSTS_BY_DATE = True
SORT_DESCENDING = True  # True = newest first, False = oldest first


# ============================================================================
# VIDEO URL EXTRACTION
# ============================================================================
# Supports: Vimeo, YouTube

# Clean video URLs (remove tracking parameters like ?share=copy, &ab_channel, etc.)
CLEAN_VIDEO_URLS = True

# Deduplicate video URLs within each post
DEDUPLICATE_URLS = True


# ============================================================================
# HTTP HEADERS
# ============================================================================

# User-Agent string for HTTP requests
# Change this if you encounter issues (use your browser's user agent)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Accept-Language header
ACCEPT_LANGUAGE = "en-GB,en;q=0.9"


# ============================================================================
# API SETTINGS
# ============================================================================

# Patreon API version to use
API_VERSION = "1.0"

# Filter for draft posts (False = exclude drafts, True = include drafts)
INCLUDE_DRAFTS = False

# Sort order for posts from API
# Options: "-published_at" (newest first), "published_at" (oldest first)
API_SORT_ORDER = "-published_at"


# ============================================================================
# INTERACTIVE MODE SETTINGS
# ============================================================================

# Auto mode - skip ALL interactive prompts and use config values
# True = automated/batch mode (for cron/scheduled runs - no interaction required)
# False = interactive mode (ask user for preferences during runtime)
AUTO_MODE = False

# Creator selection (used when AUTO_MODE = True)
# List of creator vanity names to scrape: ['CREATOR1', 'CREATOR2', 'CREATOR3']
# Empty list [] = scrape all subscribed creators
# This setting is ignored when AUTO_MODE = False (interactive mode shows menu)
SELECTED_CREATORS = []

# Default choice for date range filter prompt
# Set to True to always apply, False to skip, None to ask user
DEFAULT_USE_DATE_FILTER = None

# Auto-confirm actions (dangerous - use with caution!)
# If True, will not prompt for confirmations
AUTO_CONFIRM = False


# ============================================================================
# LOGGING / DEBUG
# ============================================================================

# Print verbose debug information
VERBOSE = False

# Log API requests (prints URLs being fetched)
LOG_API_REQUESTS = False

# Print full error tracebacks
SHOW_FULL_ERRORS = True


# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Maximum concurrent API requests (for future multi-threading support)
MAX_CONCURRENT_REQUESTS = 1

# Cache API responses (for development/testing)
ENABLE_CACHING = False
CACHE_DIR = ".cache"

# Validate video URLs before adding to output
VALIDATE_VIDEO_URLS = True
