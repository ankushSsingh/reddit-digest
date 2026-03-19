import requests

HEADERS = {"User-Agent": "reddit-digest-app:v1.0"}


def fetch_top_posts(subreddit: str, limit: int = 10) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json"
    params = {"t": "day", "limit": limit}

    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()

    posts = []
    for child in response.json()["data"]["children"]:
        p = child["data"]
        posts.append({
            "title": p["title"],
            "author": p["author"],
            "score": p["score"],
            "upvote_ratio": p["upvote_ratio"],
            "url": p["url"],
            "permalink": f"https://www.reddit.com{p['permalink']}",
            "num_comments": p["num_comments"],
            "flair": p.get("link_flair_text"),
            "selftext": p.get("selftext", ""),
            "thumbnail": p.get("thumbnail") if str(p.get("thumbnail", "")).startswith("http") else None,
        })
    return posts


def validate_subreddit(subreddit: str) -> bool:
    try:
        resp = requests.get(
            f"https://www.reddit.com/r/{subreddit}/about.json",
            headers=HEADERS,
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False
