#!/usr/bin/env python3
"""
Patreon Video Extractor

A tool to scrape Patreon posts and extract video URLs from Vimeo and YouTube.
"""

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

import api_client
import auth
import config
import utils
import video_extractor


def main() -> int:
    """Main entry point for the scraper."""
    utils.print_startup_banner()

    # Step 1: Authenticate
    print("Authenticating with Patreon...")
    try:
        session: requests.Session
        csrf_token: str
        user_info: Dict[str, Any]
        session, csrf_token, user_info = auth.setup_authenticated_session()
        print(f"✓ Logged in as: {user_info['name']}")
        print(f"  Email: {user_info['email']}")
        print(f"  Active memberships: {user_info['pledge_count']}")
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease export your Patreon cookies using a browser extension:")
        print("  1. Install 'Cookie-Editor' or 'EditThisCookie' extension")
        print("  2. Log into Patreon in your browser")
        print("  3. Export cookies as JSON")
        print(f"  4. Save to {config.COOKIES_DIR}/{config.COOKIES_FILE}")
        return 1
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
        if config.SHOW_FULL_ERRORS:
            import traceback
            traceback.print_exc()
        return 1

    # Step 2: Get creators
    print("\nFetching subscribed creators...")
    client: api_client.PatreonClient = api_client.PatreonClient(session, csrf_token)

    try:
        # Check compatibility in interactive mode (shows warnings in list)
        # Skip in auto mode to save time
        check_compat: bool = not config.AUTO_MODE
        creators: List[Dict[str, Any]] = client.get_creators(check_compatibility=check_compat)

        if check_compat:
            print(f"✓ Found {len(creators)} creator(s) - checking compatibility...")
        else:
            print(f"✓ Found {len(creators)} creator(s)")
    except Exception as e:
        print(f"\n✗ Failed to fetch creators: {e}")
        return 1

    if not creators:
        print("\n✗ No creators found. Make sure you have active memberships.")
        return 1

    # Step 3: Select creator (AUTO_MODE or interactive)
    selected_creators: List[Dict[str, Any]]
    if config.AUTO_MODE:
        # AUTO MODE - use config settings, no prompts
        print("\n" + "=" * 60)
        print("Running in AUTO MODE (non-interactive)")
        print("=" * 60)

        if config.SELECTED_CREATORS:
            # Filter creators based on SELECTED_CREATORS list
            selected_creators = []
            for creator in creators:
                if creator['vanity'] in config.SELECTED_CREATORS:
                    selected_creators.append(creator)

            if not selected_creators:
                print(f"\n✗ None of the configured creators found: {config.SELECTED_CREATORS}")
                print(f"Available creators: {[c['vanity'] for c in creators]}")
                return 1

            creator_names = [c['name'] for c in selected_creators]
            print(f"Creators: {', '.join(creator_names)}")
        else:
            # Empty list = scrape all
            selected_creators = creators
            print(f"Creators: ALL ({len(creators)} creators)")

        # Output format from config
        formats = []
        if config.OUTPUT_JSON:
            formats.append("JSON")
        if config.OUTPUT_RAW_URLS:
            formats.append("TXT")
        print(f"Output: {' + '.join(formats) if formats else 'None (check config!)'}")
        print(f"Deduplication: {'enabled' if config.DEDUPLICATE_RAW_URLS else 'disabled'}")
        print("=" * 60)
    else:
        # INTERACTIVE MODE - show menu
        utils.print_creator_list(creators)

        print("\nSelect a creator to scrape:")
        print("  - Enter a number (1-{})".format(len(creators)))
        print("  - Enter 'all' to scrape all creators")
        print("  - Enter 'q' to quit")

        while True:
            choice = input("\nYour choice: ").strip().lower()

            if choice == 'q':
                print("Exiting...")
                return 0

            if choice == 'all':
                selected_creators = creators
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(creators):
                    selected_creators = [creators[idx]]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(creators)}")
            except ValueError:
                print("Invalid input. Please enter a number, 'all', or 'q'")

    # Step 4: Optional date filtering
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    if not config.AUTO_MODE:
        # Check if we should ask for date filter based on config
        should_filter = config.DEFAULT_USE_DATE_FILTER
        if should_filter is None:
            # Ask user
            should_filter = input("\nApply date range filter? (y/n): ").strip().lower() == 'y'

        if should_filter:
            try:
                start_str = input("Start date (YYYY-MM-DD) or press Enter to skip: ").strip()
                if start_str:
                    start_date = utils.parse_date_input(start_str)

                end_str = input("End date (YYYY-MM-DD) or press Enter to skip: ").strip()
                if end_str:
                    end_date = utils.parse_date_input(end_str)

                if start_date and end_date and start_date > end_date:
                    print("Warning: Start date is after end date. Swapping...")
                    start_date, end_date = end_date, start_date

                print(f"\n✓ Date filter: {start_date or 'any'} to {end_date or 'any'}")
            except Exception as e:
                print(f"Warning: Invalid date format: {e}")
                print("Proceeding without date filter...")

    # Step 5: Output format selection (interactive mode only)
    use_json: bool = config.OUTPUT_JSON
    use_txt: bool = config.OUTPUT_RAW_URLS
    dedupe_txt: bool = config.DEDUPLICATE_RAW_URLS

    if not config.AUTO_MODE:
        print("\nSelect output format:")
        print("  1. JSON only (with metadata)")
        print("  2. TXT only (raw URLs)")
        print("  3. Both JSON and TXT")

        while True:
            choice = input("\nYour choice (1-3): ").strip()

            if choice == '1':
                use_json = True
                use_txt = False
                break
            elif choice == '2':
                use_json = False
                use_txt = True
                break
            elif choice == '3':
                use_json = True
                use_txt = True
                break
            else:
                print("Invalid input. Please enter 1, 2, or 3")

        # Ask about deduplication if TXT is enabled
        if use_txt:
            dedupe_choice = input("\nDeduplicate URLs in raw TXT export? (y/n): ").strip().lower()
            dedupe_txt = dedupe_choice == 'y'

        # Show summary
        formats = []
        if use_json:
            formats.append("JSON")
        if use_txt:
            formats.append(f"TXT ({'deduplicated' if dedupe_txt else 'with duplicates'})")
        print(f"\n✓ Output format: {' + '.join(formats)}")

    # Store selections for scraper to use
    config.OUTPUT_JSON = use_json
    config.OUTPUT_RAW_URLS = use_txt
    config.DEDUPLICATE_RAW_URLS = dedupe_txt

    # Step 6: Scrape posts
    print("\n" + "=" * 60)
    print("Starting scrape...")
    print("=" * 60)

    for creator in selected_creators:
        scrape_creator(client, creator, start_date, end_date)

    print("\n" + "=" * 60)
    print("Scraping complete!")
    print("=" * 60)

    return 0


def scrape_creator(
    client: api_client.PatreonClient,
    creator: Dict[str, Any],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> None:
    """
    Scrape posts from a single creator.

    Args:
        client: Patreon API client
        creator: Creator dictionary
        start_date: Optional start date filter
        end_date: Optional end date filter
    """
    print(f"\n{'─' * 60}")
    print(f"Scraping: {creator['name']} (@{creator['vanity']})")
    print(f"{'─' * 60}")

    # Fetch posts
    try:
        posts = client.get_creator_posts(
            creator['vanity'],
            max_posts=config.MAX_POSTS_PER_CREATOR,
            show_progress=config.SHOW_PROGRESS
        )
        print(f"  ✓ Fetched {len(posts)} post(s)")
    except ValueError as e:
        error_msg = str(e)
        # Check if this is the Creator Website format error
        if "Creator Website format" in error_msg or "Netflix-style" in error_msg:
            print(f"  ⚠️  INCOMPATIBLE FORMAT")
            print(f"  ⓘ  This creator uses Patreon's Creator Website (Netflix-style layout)")
            print(f"  ⓘ  Videos are hosted on Patreon, not Vimeo/YouTube")
            print(f"  ⓘ  This format is not supported by this tool")
            print(f"  →  Skipping {creator['name']}")
        else:
            print(f"  ✗ Failed to fetch posts: {e}")
            if config.SHOW_FULL_ERRORS:
                import traceback
                traceback.print_exc()
        return
    except Exception as e:
        print(f"  ✗ Failed to fetch posts: {e}")
        if config.SHOW_FULL_ERRORS:
            import traceback
            traceback.print_exc()
        return

    # Apply date filter
    if start_date or end_date:
        posts = client.filter_posts_by_date(posts, start_date, end_date)
        print(f"  ✓ {len(posts)} post(s) after date filtering")

    if not posts:
        print("  No posts to process.")
        return

    # Process each post
    print(f"  Processing posts and extracting video URLs...")

    results: List[Dict[str, Any]] = []
    total_video_urls: int = 0

    for i, post in enumerate(posts, 1):
        post_id = post.get('id')
        attrs = post.get('attributes', {})
        title = attrs.get('title', 'Untitled')
        post_type = attrs.get('post_type')

        # Enrich video_embed posts with API data
        if post_type == 'video_embed':
            post = client.enrich_post_with_details(post)

        # Extract video URLs (Vimeo and YouTube)
        video_urls = video_extractor.extract_all_video_urls(post)

        if video_urls:
            total_video_urls += len(video_urls)
            print(f"    [{i}/{len(posts)}] \"{title}\" - {len(video_urls)} URL(s)")

        # Format for output
        post_data = utils.format_post_for_output(post, video_urls)

        # Include post based on configuration
        if video_urls or config.INCLUDE_POSTS_WITHOUT_VIDEOS:
            results.append(post_data)

    # Sort posts by date if configured
    if config.SORT_POSTS_BY_DATE:
        results.sort(
            key=lambda x: x.get('published_at') or '',
            reverse=config.SORT_DESCENDING
        )

    # Validate at least one output format is enabled
    if not config.OUTPUT_JSON and not config.OUTPUT_RAW_URLS:
        print("\n  ⚠️  Warning: Both OUTPUT_JSON and OUTPUT_RAW_URLS are disabled in config.py")
        print("  ⚠️  No files will be saved. Enable at least one output format to save results.")
        print(f"  ✓ Total video URLs found: {total_video_urls}")
        return

    # Prepare output data
    output_data = {
        'creator': creator['name'],
        'creator_vanity': creator['vanity'],
        'creator_url': creator['url'],
        'scrape_date': datetime.now().isoformat(),
        'total_posts': len(results),
        'posts_with_videos': len([p for p in results if p['video_urls']]),
        'total_video_urls': total_video_urls,
        'date_filter': {
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        },
        'posts': results
    }

    # Collect all video URLs for raw export
    all_video_urls: List[str] = [url for post in results for url in post['video_urls']]

    # Check if we should save (based on whether we found videos)
    should_save = total_video_urls > 0 or not config.SKIP_EXPORT_IF_NO_VIDEOS

    if not should_save:
        print(f"\n  ⓘ No video URLs found - skipping export (change SKIP_EXPORT_IF_NO_VIDEOS in config.py to export anyway)")
        print(f"  ✓ Total video URLs found: {total_video_urls}")
        return

    # Save files based on configuration
    print()
    saved_any: bool = False

    # Save JSON if enabled
    if config.OUTPUT_JSON:
        try:
            filepath = utils.save_results_to_json(
                output_data,
                creator['vanity']
            )
            print(f"  ✓ JSON saved to: {filepath}")
            saved_any = True
        except Exception as e:
            print(f"  ✗ Failed to save JSON: {e}")
            if config.SHOW_FULL_ERRORS:
                import traceback
                traceback.print_exc()

    # Save raw URLs if enabled
    if config.OUTPUT_RAW_URLS:
        try:
            filepath = utils.save_raw_urls_to_txt(
                all_video_urls,
                creator['vanity'],
                deduplicate=config.DEDUPLICATE_RAW_URLS
            )
            print(f"  ✓ Raw URLs saved to: {filepath}")
            saved_any = True
        except Exception as e:
            print(f"  ✗ Failed to save raw URLs: {e}")
            if config.SHOW_FULL_ERRORS:
                import traceback
                traceback.print_exc()

    if saved_any:
        print(f"  ✓ Total video URLs found: {total_video_urls}")


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        if config.SHOW_FULL_ERRORS:
            import traceback
            traceback.print_exc()
        sys.exit(1)
