import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


def _build_html(subreddit: str, posts: list[dict]) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    items = ""
    for post in posts:
        body_html = ""
        if post.get("selftext"):
            excerpt = post["selftext"][:300] + ("..." if len(post["selftext"]) > 300 else "")
            body_html = f'<p style="color:#555;font-size:14px;margin:6px 0 0;">{excerpt}</p>'

        flair_html = ""
        if post.get("flair"):
            flair_html = f'<span style="background:#ff4500;color:#fff;font-size:11px;padding:2px 6px;border-radius:3px;margin-left:6px;">{post["flair"]}</span>'

        items += f"""
        <div style="border-left:3px solid #ff4500;padding:12px 16px;margin:16px 0;background:#fafafa;">
            <a href="{post['permalink']}" style="color:#1a1a1b;text-decoration:none;font-size:16px;font-weight:600;line-height:1.4;">
                {post['title']}
            </a>{flair_html}
            <p style="color:#878a8c;font-size:13px;margin:6px 0 0;">
                ▲ {post['score']} &nbsp;·&nbsp; 💬 {post['num_comments']} comments &nbsp;·&nbsp; u/{post['author']}
            </p>
            {body_html}
        </div>
        """

    return f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:680px;margin:0 auto;padding:20px;color:#1a1a1b;">

        <div style="border-bottom:2px solid #ff4500;padding-bottom:16px;margin-bottom:24px;">
            <h1 style="margin:0;color:#ff4500;">Reddit Digest Agent</h1>
            <p style="margin:4px 0 0;color:#878a8c;font-size:14px;">r/{subreddit} &mdash; {date_str}</p>
        </div>

        <p style="font-size:15px;line-height:1.6;margin-bottom:24px;">
            Hey there,<br><br>
            This is your <strong>Reddit Digest Agent</strong>. As requested, please find below a curated summary
            of the top posts from <strong>r/{subreddit}</strong> over the last 24 hours. Sit back and enjoy the highlights!
        </p>

        {items}

        <div style="border-top:1px solid #edeff1;margin-top:32px;padding-top:20px;">
            <p style="font-size:15px;line-height:1.6;margin:0 0 12px;">
                That's all for today's digest. Hope you found something worth reading!<br><br>
                Warm regards,<br>
                <strong>Reddit Digest Agent</strong>
            </p>
            <p style="color:#878a8c;font-size:12px;margin:0;">
                You're receiving this because you subscribed to r/{subreddit} on Reddit Digest.
            </p>
        </div>

    </body></html>
    """


def _build_plain(subreddit: str, posts: list[dict]) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    lines = [
        f"Reddit Digest Agent — r/{subreddit} — {date_str}",
        "=" * 55,
        "",
        f"Hey there,",
        "",
        f"This is your Reddit Digest Agent. As requested, please find below a curated summary",
        f"of the top posts from r/{subreddit} over the last 24 hours.",
        "",
        "-" * 55,
        "",
    ]
    for post in posts:
        lines.append(f"▲ {post['score']}  {post['title']}")
        lines.append(f"   {post['permalink']}")
        lines.append(f"   by u/{post['author']} · {post['num_comments']} comments")
        if post.get("selftext"):
            lines.append(f"   {post['selftext'][:200]}...")
        lines.append("")
    lines += [
        "-" * 55,
        "",
        "That's all for today's digest. Hope you found something worth reading!",
        "",
        "Warm regards,",
        "Reddit Digest Agent",
    ]
    return "\n".join(lines)


def send_digest_email(to_email: str, subreddit: str, posts: list[dict]):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reddit Digest Agent for r/{subreddit} -- {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    msg.attach(MIMEText(_build_plain(subreddit, posts), "plain"))
    msg.attach(MIMEText(_build_html(subreddit, posts), "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
