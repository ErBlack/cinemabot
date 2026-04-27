import re

import httpx
from bs4 import BeautifulSoup

MOVIE_DOMAINS = [
    r"kinopoisk\.ru",
    r"imdb\.com",
    r"letterboxd\.com",
]

_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:" + "|".join(MOVIE_DOMAINS) + r")\S+"
)


def extract_movie_links(text: str) -> list[str]:
    return _URL_PATTERN.findall(text)


async def fetch_og_title(url: str) -> str:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
            soup = BeautifulSoup(response.text, "html.parser")
            tag = soup.find("meta", property="og:title")
            if tag and tag.get("content"):
                return tag["content"].strip()
    except Exception:
        pass
    return url
