import re

def get_shortcode_from_url(url: str) -> str | None:

    pattern = r"https?://(?:www\.)?instagram\.com/(?:[A-Za-z0-9._%-]+/)?(reel|reels|p)/([A-Za-z0-9_-]+)(?:/)?(?:\?.*)?$"

    match = re.match(pattern, url)
    if match:
        return match.group(2)
    return None