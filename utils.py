"""
Utility Functions

Helper functions for file I/O, date parsing, and formatting.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import config


def clear_screen() -> None:
    """Clear terminal screen (cross-platform)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_startup_banner() -> None:
    """Print startup banner with ASCII logo and credits."""
    clear_screen()
    print("""
╔════════════════════════════════════════════════════════════════╗
║  ██████╗  █████╗ ████████╗██████╗ ███████╗ ██████╗ ███╗   ██╗ ║
║  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔═══██╗████╗  ██║ ║
║  ██████╔╝███████║   ██║   ██████╔╝█████╗  ██║   ██║██╔██╗ ██║ ║
║  ██╔═══╝ ██╔══██║   ██║   ██╔══██╗██╔══╝  ██║   ██║██║╚██╗██║ ║
║  ██║     ██║  ██║   ██║   ██║  ██║███████╗╚██████╔╝██║ ╚████║ ║
║  ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝ ║
║                                                                  ║
║                  Video Extractor v1.0                            ║
║            Extract Vimeo & YouTube URLs from Patreon             ║
║                                                                  ║
║                Created by: github.com/evenwebb                   ║
╚════════════════════════════════════════════════════════════════╝
""")


def save_results_to_json(
    data: Dict[str, Any],
    creator_vanity: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Save scraping results to a JSON file.

    Args:
        data: Dictionary containing scraping results
        creator_vanity: Creator's vanity URL (used in filename)
        output_dir: Output directory path (uses config.OUTPUT_DIR if None)

    Returns:
        Path to the saved file
    """
    if output_dir is None:
        output_dir = config.OUTPUT_DIR

    output_path = Path(output_dir)

    # Add creator subfolder if configured
    if config.OUTPUT_ORGANIZE_BY_CREATOR:
        output_path = output_path / creator_vanity

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime(config.TIMESTAMP_FORMAT)
    filename = config.OUTPUT_FILENAME_FORMAT.format(
        creator_vanity=creator_vanity,
        timestamp=timestamp
    )
    filepath = output_path / filename

    # Save to file
    with filepath.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return str(filepath)


def save_raw_urls_to_txt(
    urls: List[str],
    creator_vanity: str,
    output_dir: Optional[str] = None,
    deduplicate: bool = True
) -> str:
    """
    Save raw video URLs to a text file (one URL per line).

    Args:
        urls: List of video URLs
        creator_vanity: Creator's vanity URL (used in filename)
        output_dir: Output directory path (uses config.OUTPUT_DIR if None)
        deduplicate: Whether to deduplicate URLs before saving

    Returns:
        Path to the saved file
    """
    if output_dir is None:
        output_dir = config.OUTPUT_DIR

    output_path = Path(output_dir)

    # Add creator subfolder if configured
    if config.OUTPUT_ORGANIZE_BY_CREATOR:
        output_path = output_path / creator_vanity

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Deduplicate if requested
    if deduplicate:
        urls = list(dict.fromkeys(urls))  # Preserves order while deduplicating

    # Generate filename with timestamp (same as JSON but .txt)
    timestamp = datetime.now().strftime(config.TIMESTAMP_FORMAT)
    filename = f"{creator_vanity}_{timestamp}.txt"
    filepath = output_path / filename

    # Save to file (one URL per line)
    with filepath.open('w', encoding='utf-8') as f:
        for url in urls:
            f.write(f"{url}\n")

    return str(filepath)


def parse_date_input(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object.

    Supports formats:
    - YYYY-MM-DD
    - YYYY/MM/DD
    - DD-MM-YYYY
    - DD/MM/YYYY

    Args:
        date_str: Date string to parse

    Returns:
        datetime object

    Raises:
        ValueError: If date format is not recognized
    """
    if not date_str:
        raise ValueError("Empty date string")

    # Try different formats
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Could not parse date: {date_str}. Expected format: YYYY-MM-DD")


def format_post_for_output(post: dict, video_urls: List[str]) -> dict:
    """
    Format a post dictionary for JSON output.

    Args:
        post: Post dictionary from API
        video_urls: List of video URLs (Vimeo and YouTube) extracted from the post

    Returns:
        Formatted dictionary with relevant fields
    """
    attrs = post.get('attributes', {})

    return {
        'post_id': post.get('id'),
        'title': attrs.get('title', 'Untitled'),
        'post_type': attrs.get('post_type'),
        'published_at': attrs.get('published_at'),
        'url': attrs.get('url', f"https://www.patreon.com/posts/{post.get('id')}"),
        'video_urls': video_urls
    }


def print_banner(text: str) -> None:
    """
    Print a formatted banner.

    Args:
        text: Text to display in banner
    """
    width = max(60, len(text) + 4)
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)
    print()


def print_creator_list(creators: List[Dict[str, str]]) -> None:
    """
    Print a formatted list of creators with box borders.

    Args:
        creators: List of creator dictionaries
    """
    print()
    print("╭─────────────────────── Subscribed Creators ────────────────────────╮")
    for i, creator in enumerate(creators, 1):
        name = creator['name'][:28]  # Truncate if too long
        vanity = creator['vanity'][:15]  # Truncate if too long
        name_vanity = f"{name:28s} (@{vanity:15s})"

        # Check if compatibility was checked and mark incompatible creators
        if 'compatible' in creator and not creator['compatible']:
            print(f"│ {i:2d}. {name_vanity} ⚠️  [NOT SUPPORTED] │")
        else:
            print(f"│ {i:2d}. {name_vanity:52s} │")
    print("╰─────────────────────────────────────────────────────────────────────╯")

    # Show legend if any incompatible creators found
    if any('compatible' in c and not c['compatible'] for c in creators):
        print("  ⚠️  = Creator Website format (Patreon-hosted videos, not supported)")
        print()


def confirm_action(prompt: str) -> bool:
    """
    Ask user for yes/no confirmation.

    Args:
        prompt: Confirmation question

    Returns:
        True if user confirms, False otherwise
    """
    if config.AUTO_CONFIRM:
        return True

    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
