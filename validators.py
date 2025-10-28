import re

def instagram_url(url: str) -> bool:
    pattern = r"https?:\/\/(www\.)?instagram\.com\/reels\/[A-Za-z0-9_-]+\/?$"

    return  (re.fullmatch(pattern, url) is not None)


## fullmatch return MATCH OBJECT if url == pattern and NONE if url != pattern