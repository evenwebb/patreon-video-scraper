"""
Video URL Extraction Module

Extracts video URLs (Vimeo and YouTube) from Patreon posts using different methods
depending on the post type.
"""

import re
from typing import Dict, List, Optional, Set

import config


# Video URL regex patterns
VIMEO_PATTERN = r'https://vimeo\.com/\d+(?:/[a-z0-9]+)?(?:\?share=copy)?(?:&[^\s<"]*)?'
YOUTUBE_PATTERN = r'https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/|v/|live/)|youtu\.be/)([a-zA-Z0-9_-]{11})(?:[?&][^\s<"]*)?'


def extract_from_content(content: Optional[str]) -> List[str]:
    """
    Extract video URLs from post content using regex.

    This works for text posts that have video links in their content.
    Supports both Vimeo and YouTube.

    Args:
        content: HTML content from post

    Returns:
        List of unique video URLs found
    """
    if not content:
        return []

    # Find all video URLs (both Vimeo and YouTube)
    vimeo_urls: List[str] = re.findall(VIMEO_PATTERN, str(content))
    youtube_matches: List[str] = re.findall(YOUTUBE_PATTERN, str(content))

    # Reconstruct full YouTube URLs from matched IDs
    youtube_urls: List[str] = [
        f'https://www.youtube.com/watch?v={video_id}'
        for video_id in youtube_matches
    ]

    # Combine both
    urls: List[str] = vimeo_urls + youtube_urls

    # Deduplicate if configured
    if config.DEDUPLICATE_URLS:
        urls = list(set(urls))

    # Clean URLs if configured
    if config.CLEAN_VIDEO_URLS:
        cleaned_urls = []
        for url in urls:
            # Remove tracking parameters
            # For Vimeo: remove ?share=copy and other params
            # For YouTube: remove &ab_channel and other tracking params
            if 'vimeo.com' in url:
                url = re.sub(r'\?share=copy', '', url)
                url = re.sub(r'&.*$', '', url)
            elif 'youtube.com' in url or 'youtu.be' in url:
                # Keep ?v= but remove other parameters
                url = re.sub(r'&.*$', '', url)
            cleaned_urls.append(url)
        urls = cleaned_urls

    # Final deduplication after cleaning (in case cleaning created duplicates)
    if config.DEDUPLICATE_URLS:
        urls = list(set(urls))

    return sorted(urls)


def extract_from_embed(embed_data: Optional[Dict]) -> List[str]:
    """
    Extract video URL from embed data.

    This works for video_embed type posts that have an embed object.
    Supports both Vimeo and YouTube embeds.

    Args:
        embed_data: Embed dictionary from post attributes

    Returns:
        List containing the video URL (single item or empty)
    """
    if not embed_data:
        return []

    # Check if this is a supported video embed
    provider = embed_data.get('provider', '')
    if not provider:
        return []

    provider_lower = provider.lower()

    if provider_lower not in ['vimeo', 'youtube']:
        return []

    # Get the URL
    url = embed_data.get('url')

    # For Vimeo, if no direct URL, try extracting from iframe HTML
    if provider_lower == 'vimeo' and not url:
        html = embed_data.get('html', '')
        if html:
            # Extract from iframe src
            match = re.search(r'player\.vimeo\.com/video/(\d+)(?:\?h=([a-z0-9]+))?', html)
            if match:
                video_id = match.group(1)
                privacy_hash = match.group(2)
                if privacy_hash:
                    url = f'https://vimeo.com/{video_id}/{privacy_hash}'
                else:
                    url = f'https://vimeo.com/{video_id}'

    # For YouTube, extract video ID and normalize URL
    elif provider_lower == 'youtube' and url:
        video_id = extract_youtube_id(url)
        if video_id:
            url = f'https://www.youtube.com/watch?v={video_id}'

    if not url:
        return []

    # Clean URL if configured
    if config.CLEAN_VIDEO_URLS:
        if 'vimeo.com' in url:
            url = re.sub(r'\?share=copy', '', url)
            url = re.sub(r'&.*$', '', url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            url = re.sub(r'&.*$', '', url)

    # Validate URL if configured
    if config.VALIDATE_VIDEO_URLS and not is_video_url(url):
        return []

    return [url]


def extract_youtube_id(url: Optional[str]) -> str:
    """
    Extract YouTube video ID from various YouTube URL formats.

    Args:
        url: YouTube URL string

    Returns:
        Video ID (11 characters) or empty string if not found
    """
    if not url:
        return ''

    # Try different YouTube URL patterns
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/live/([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return ''


def parse_vimeo_url(url: str) -> Dict[str, Optional[str]]:
    """
    Parse a Vimeo URL to extract video ID and privacy hash.

    Args:
        url: Vimeo URL string

    Returns:
        Dictionary with 'video_id' and 'hash' (hash may be None)
    """
    if 'vimeo.com' not in url:
        return {'video_id': None, 'hash': None}

    # Pattern: https://vimeo.com/VIDEO_ID or https://vimeo.com/VIDEO_ID/HASH
    match = re.search(r'vimeo\.com/(\d+)(?:/([a-z0-9]+))?', url)
    if match:
        return {
            'video_id': match.group(1),
            'hash': match.group(2)  # Will be None if no hash
        }

    return {'video_id': None, 'hash': None}


def deduplicate_vimeo_urls(urls: List[str]) -> List[str]:
    """
    Deduplicate Vimeo URLs, preferring versions with privacy hash.

    When the same Vimeo video appears with and without a privacy hash,
    keep only the version with the hash (as the version without may not work).

    Args:
        urls: List of video URLs

    Returns:
        Deduplicated list with hash versions preferred
    """
    # Separate Vimeo and non-Vimeo URLs
    vimeo_urls = [url for url in urls if 'vimeo.com' in url]
    other_urls = [url for url in urls if 'vimeo.com' not in url]

    # Group Vimeo URLs by video ID
    vimeo_by_id = {}
    for url in vimeo_urls:
        parsed = parse_vimeo_url(url)
        video_id = parsed['video_id']

        if not video_id:
            continue

        if video_id not in vimeo_by_id:
            vimeo_by_id[video_id] = []
        vimeo_by_id[video_id].append({'url': url, 'hash': parsed['hash']})

    # For each video ID, prefer the version with hash
    deduplicated_vimeo = []
    for video_id, versions in vimeo_by_id.items():
        # Find version with hash
        with_hash = [v for v in versions if v['hash']]

        if with_hash:
            # Prefer version with hash
            deduplicated_vimeo.append(with_hash[0]['url'])
        else:
            # No hash version exists, keep the version without hash
            deduplicated_vimeo.append(versions[0]['url'])

    return other_urls + deduplicated_vimeo


def extract_all_video_urls(post: Dict) -> List[str]:
    """
    Extract all video URLs from a post using all available methods.

    Supports both Vimeo and YouTube.
    Automatically deduplicates Vimeo URLs, preferring versions with privacy hash.

    Args:
        post: Post dictionary with 'attributes' key

    Returns:
        List of unique video URLs found
    """
    attrs = post.get('attributes', {})
    all_urls: Set[str] = set()

    # Method 1: Check embed data (for video_embed posts)
    if 'embed' in attrs and attrs['embed']:
        embed_urls: List[str] = extract_from_embed(attrs['embed'])
        all_urls.update(embed_urls)

    # Method 2: Check content (for text posts or posts with video links)
    if 'content' in attrs and attrs['content']:
        content_urls: List[str] = extract_from_content(attrs['content'])
        all_urls.update(content_urls)

    # Convert to list and deduplicate Vimeo URLs (prefer hash versions)
    urls_list: List[str] = list(all_urls)
    urls_list = deduplicate_vimeo_urls(urls_list)

    return sorted(urls_list)


def is_vimeo_url(url: str) -> bool:
    """
    Check if a URL is a valid Vimeo URL.

    Args:
        url: URL string to check

    Returns:
        True if URL matches Vimeo pattern
    """
    return bool(re.match(VIMEO_PATTERN, url))


def is_youtube_url(url: str) -> bool:
    """
    Check if a URL is a valid YouTube URL.

    Args:
        url: URL string to check

    Returns:
        True if URL matches YouTube pattern
    """
    return bool(extract_youtube_id(url))


def is_video_url(url: str) -> bool:
    """
    Check if a URL is a valid video URL (Vimeo or YouTube).

    Args:
        url: URL string to check

    Returns:
        True if URL matches either Vimeo or YouTube pattern
    """
    return is_vimeo_url(url) or is_youtube_url(url)
