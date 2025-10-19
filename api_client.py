"""
Patreon API Client Module

Handles all interactions with Patreon's website and API endpoints.
"""

import json
import re
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime

import config


class PatreonClient:
    """Client for interacting with Patreon's API and web pages."""

    def __init__(self, session: requests.Session, csrf_token: str):
        """
        Initialize Patreon client.

        Args:
            session: Authenticated requests session
            csrf_token: CSRF signature token
        """
        self.session = session
        self.csrf_token = csrf_token

    def _extract_next_data(self, html: str) -> dict:
        """
        Extract __NEXT_DATA__ JSON from HTML page.

        Args:
            html: HTML page content

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If __NEXT_DATA__ cannot be extracted
        """
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html,
            re.DOTALL
        )

        if not match:
            raise ValueError("Could not find __NEXT_DATA__ in page")

        return json.loads(match.group(1))

    def _find_all_objects_by_type(self, obj, type_name: str, results: Optional[List] = None) -> List[dict]:
        """
        Recursively find all objects with a specific type in nested JSON.

        Args:
            obj: JSON object to search
            type_name: Type to search for (e.g., 'post', 'campaign')
            results: Accumulator list

        Returns:
            List of matching objects
        """
        if results is None:
            results = []

        if isinstance(obj, dict):
            if obj.get('type') == type_name and 'attributes' in obj:
                results.append(obj)
            for value in obj.values():
                self._find_all_objects_by_type(value, type_name, results)
        elif isinstance(obj, list):
            for item in obj:
                self._find_all_objects_by_type(item, type_name, results)

        return results

    def check_creator_compatibility(self, vanity: str) -> bool:
        """
        Check if a creator's page format is compatible with this tool.

        Args:
            vanity: Creator's vanity URL

        Returns:
            True if compatible (standard format), False if incompatible (Creator Website)
        """
        try:
            page_url = f'https://www.patreon.com/c/{vanity}/posts'
            # Use HEAD request for speed, but fall back to GET if needed
            response = self.session.head(page_url, allow_redirects=True, timeout=5)

            # Check if redirected to /cw/ URL
            if '/cw/' in response.url:
                return False

            # For some creators, HEAD doesn't redirect, so do a quick GET
            if response.status_code == 405:  # Method not allowed
                response = self.session.get(page_url, timeout=5)
                if '/cw/' in response.url or 'creator-page-v2' in response.text:
                    return False

            return True
        except Exception:
            # If we can't check, assume compatible (will fail later with clear message)
            return True

    def get_creators(self, check_compatibility: bool = False) -> List[Dict[str, str]]:
        """
        Get list of creators the user is subscribed to.

        Args:
            check_compatibility: If True, check each creator's page format and add 'compatible' field

        Returns:
            List of creator dictionaries with keys: name, vanity, campaign_id, url, compatible (optional)
        """
        response = self.session.get('https://www.patreon.com/settings/memberships')
        response.raise_for_status()

        data = self._extract_next_data(response.text)

        # Find all users (creators)
        users = self._find_all_objects_by_type(data, 'user')

        creators = []
        for user in users:
            attrs = user.get('attributes', {})
            user_id = user.get('id')

            # Skip the logged-in user
            if not attrs.get('is_creator'):
                continue

            vanity = attrs.get('vanity')
            if not vanity:
                continue

            # Get campaign ID from relationships
            campaign_rel = user.get('relationships', {}).get('campaign', {}).get('data', {})
            campaign_id = campaign_rel.get('id')

            creators.append({
                'name': attrs.get('full_name', vanity),
                'vanity': vanity,
                'campaign_id': campaign_id,
                'url': f'https://www.patreon.com/{vanity}'
            })

        # Deduplicate by vanity
        seen = set()
        unique_creators = []
        for creator in creators:
            if creator['vanity'] not in seen:
                seen.add(creator['vanity'])
                unique_creators.append(creator)

        # Check compatibility if requested (for interactive mode)
        if check_compatibility:
            for creator in unique_creators:
                creator['compatible'] = self.check_creator_compatibility(creator['vanity'])

        return sorted(unique_creators, key=lambda x: x['name'])

    def get_creator_posts(self, vanity: str, max_posts: Optional[int] = None, show_progress: bool = True) -> List[dict]:
        """
        Get all posts from a creator using the Patreon API with pagination.

        Args:
            vanity: Creator's vanity URL (e.g., 'GIFGAS')
            max_posts: Maximum number of posts to fetch (None = all)
            show_progress: Whether to print progress updates

        Returns:
            List of post dictionaries
        """
        # First, get the campaign ID from the creator page
        page_url = f'https://www.patreon.com/c/{vanity}/posts'
        response = self.session.get(page_url)
        response.raise_for_status()

        # Check if this is a Creator Website (Netflix-style format)
        # These use /cw/ URLs and have a completely different layout
        if '/cw/' in response.url or 'creator-page-v2' in response.text:
            raise ValueError(
                f"Creator '{vanity}' uses Patreon Creator Website format (Netflix-style layout). "
                f"This format is not supported by this tool as it uses Patreon-hosted videos "
                f"rather than Vimeo/YouTube embeds."
            )

        data = self._extract_next_data(response.text)

        # Find campaign ID
        campaigns = self._find_all_objects_by_type(data, 'campaign')
        if not campaigns:
            raise ValueError(f"Could not find campaign for creator: {vanity}")

        campaign_id = campaigns[0].get('id')
        if not campaign_id:
            raise ValueError(f"Could not extract campaign ID for creator: {vanity}")

        # Now fetch posts via API with pagination
        all_posts = []
        cursor = None
        page_num = 0
        total_posts = None

        while True:
            page_num += 1

            # Build API URL
            api_url = (
                f'https://www.patreon.com/api/posts'
                f'?filter[campaign_id]={campaign_id}'
                f'&filter[is_draft]={str(config.INCLUDE_DRAFTS).lower()}'
                f'&sort={config.API_SORT_ORDER}'
                f'&json-api-use-default-includes=false'
                f'&json-api-version={config.API_VERSION}'
            )

            if cursor:
                api_url += f'&page[cursor]={cursor}'

            # Fetch page
            headers = {
                'Accept': 'application/json',
                'x-csrf-signature': self.csrf_token,
                'Referer': page_url
            }

            response = self.session.get(api_url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            page_data = response.json()

            # Add delay between requests if configured
            if config.REQUEST_DELAY > 0:
                time.sleep(config.REQUEST_DELAY)

            # Get total count from first page
            if page_num == 1:
                meta = page_data.get('meta', {})
                pagination = meta.get('pagination', {})
                total_posts = pagination.get('total')

            # Get posts from this page
            posts = page_data.get('data', [])
            if not posts:
                break

            all_posts.extend(posts)

            # Show progress
            if show_progress and total_posts:
                print(f"    Fetched {len(all_posts)}/{total_posts} posts...", end='\r')

            # Check if we've reached max_posts
            if max_posts and len(all_posts) >= max_posts:
                all_posts = all_posts[:max_posts]
                break

            # Check for next page
            meta = page_data.get('meta', {})
            pagination = meta.get('pagination', {})
            cursors = pagination.get('cursors', {})

            cursor = cursors.get('next')
            if not cursor:
                # No more pages
                break

        if show_progress and total_posts:
            print(f"    Fetched {len(all_posts)}/{total_posts} posts... Done!")

        return all_posts

    def get_post_details(self, post_id: str) -> dict:
        """
        Get full details for a specific post via API.

        This is necessary for video_embed posts to get the embed data.

        Args:
            post_id: Patreon post ID

        Returns:
            Post dictionary with full details including embed data
        """
        # Update headers for API call
        headers = {
            'Accept': 'application/json',
            'x-csrf-signature': self.csrf_token,
            'Referer': 'https://www.patreon.com/'
        }

        url = f'https://www.patreon.com/api/posts/{post_id}'
        response = self.session.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if 'data' in data:
            return data['data']

        return {}

    def enrich_post_with_details(self, post: dict) -> dict:
        """
        Enrich a post with full details from API if needed.

        For video_embed posts, fetches the full post data to get embed information.

        Args:
            post: Basic post dictionary

        Returns:
            Enriched post dictionary
        """
        attrs = post.get('attributes', {})
        post_type = attrs.get('post_type')
        post_id = post.get('id')

        # If it's a video_embed post and has no embed data, fetch from API
        if config.ENRICH_VIDEO_EMBEDS and post_type == 'video_embed' and not attrs.get('embed'):
            try:
                full_post = self.get_post_details(post_id)
                # Merge the full data
                if full_post:
                    return full_post
            except Exception as e:
                if config.VERBOSE or config.LOG_API_REQUESTS:
                    print(f"Warning: Could not fetch details for post {post_id}: {e}")

        return post

    def filter_posts_by_date(
        self,
        posts: List[dict],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        Filter posts by publication date range.

        Args:
            posts: List of post dictionaries
            start_date: Minimum publication date (inclusive)
            end_date: Maximum publication date (inclusive)

        Returns:
            Filtered list of posts
        """
        if not start_date and not end_date:
            return posts

        filtered = []
        for post in posts:
            attrs = post.get('attributes', {})
            published_str = attrs.get('published_at')

            if not published_str:
                continue

            # Parse ISO date
            try:
                published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            except Exception:
                continue

            # Check date range
            if start_date and published < start_date:
                continue
            if end_date and published > end_date:
                continue

            filtered.append(post)

        return filtered
