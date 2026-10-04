"""Blog build for jeremyscheurer.com.

Posts are markdown files in posts/, named YYYY-MM-DD-slug.md, with a first line
`# Title`. Running this script renders each post to /writing/<slug>.html in the
site style, writes writing.html (the index) and feed.xml (RSS), and prints a
reminder to re-add the Writing nav link the first time a post exists.

Requires: pip install markdown
Run from the repo root:  python3 tools/build_posts.py
"""
import datetime
import email.utils
import html
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).parent.parent
SITE = "https://jeremyscheurer.com"

POST_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Jérémy Scheurer</title>
<link rel="alternate" type="application/rss+xml" title="Jérémy Scheurer" href="/feed.xml">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400..600;1,400..500&display=swap">
<style>
  :root {{
    --bg: #fbfaf8; --card: #ffffff; --ink: #20232a; --ink-soft: #5d6169;
    --accent: #2c4a6e; --rule: #dcdcd6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #16181c; --card: #1d2025; --ink: #e3e2dc; --ink-soft: #999e94;
             --accent: #8fb0d4; --rule: #2f3236; }}
  }}
  body {{ background: var(--bg); color: var(--ink);
    font-family: "EB Garamond", Garamond, Georgia, serif;
    font-size: 20px; line-height: 1.6; margin: 0; padding: 0 20px; }}
  .page {{ max-width: 640px; margin: 0 auto; padding: 56px 0 64px; }}
  header.topbar {{ text-align: center; margin-bottom: 64px; }}
  .topbar a.home {{ font-size: 32px; font-weight: 500; color: var(--ink); text-decoration: none; }}
  .topbar a.home:hover {{ color: var(--accent); }}
  .topbar nav {{ margin-top: 20px; display: flex; justify-content: center; gap: 32px; }}
  .topbar nav a {{ color: var(--ink-soft); text-decoration: none; font-size: 15px;
    letter-spacing: 0.09em; text-transform: uppercase; }}
  .topbar nav a:hover {{ color: var(--accent); }}
  h1 {{ font-size: 40px; font-weight: 500; line-height: 1.15; margin: 0 0 10px; text-align: center; }}
  .date {{ text-align: center; font-style: italic; color: var(--ink-soft); margin-bottom: 48px; }}
  article p {{ margin: 0 0 1.1em; }}
  article a {{ color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 3px; }}
  article h2 {{ font-size: 26px; font-weight: 500; margin: 44px 0 14px; }}
  article img {{ max-width: 100%; border-radius: 6px; }}
  article blockquote {{ margin: 0; padding-left: 20px; border-left: 3px solid var(--rule);
    color: var(--ink-soft); font-style: italic; }}
  article pre {{ background: var(--card); border: 1px solid var(--rule); border-radius: 6px;
    padding: 14px 16px; overflow-x: auto; font-size: 15px; }}
  article code {{ font-family: ui-monospace, Menlo, monospace; font-size: 0.85em; }}
  footer {{ margin-top: 72px; padding-top: 24px; border-top: 1px solid var(--rule);
    text-align: center; font-size: 16px; color: var(--ink-soft); }}
</style>
</head>
<body>
<div class="page">
  <header class="topbar">
    <a class="home" href="/">Jérémy Scheurer</a>
    <nav>
      <a href="/#research">Research</a>
      <a href="/writing.html">Writing</a>
      <a href="/about.html">About</a>
    </nav>
  </header>
  <h1>{title}</h1>
  <div class="date">{date_pretty}</div>
  <article>
{body}
  </article>
  <footer>Jérémy Scheurer</footer>
</div>
</body>
</html>
"""


def parse_post(path: pathlib.Path):
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", path.name)
    if not m:
        raise SystemExit(f"post filename must be YYYY-MM-DD-slug.md, got {path.name}")
    date = datetime.date.fromisoformat(m.group(1))
    slug = m.group(2)
    text = path.read_text()
    first, _, rest = text.partition("\n")
    if not first.startswith("# "):
        raise SystemExit(f"{path.name}: first line must be '# Title'")
    return {"date": date, "slug": slug, "title": first[2:].strip(), "md": rest.strip()}


def main():
    posts = sorted((parse_post(p) for p in (ROOT / "posts").glob("*.md")),
                   key=lambda p: p["date"], reverse=True)
    if not posts:
        print("no posts yet; nothing to build")
        return
    outdir = ROOT / "writing"
    outdir.mkdir(exist_ok=True)
    items = []
    for p in posts:
        body = markdown.markdown(p["md"], extensions=["fenced_code", "tables"])
        date_pretty = p["date"].strftime("%B %-d, %Y")
        (outdir / f"{p['slug']}.html").write_text(
            POST_TEMPLATE.format(title=html.escape(p["title"]), date_pretty=date_pretty, body=body))
        url = f"{SITE}/writing/{p['slug']}.html"
        pub = email.utils.format_datetime(
            datetime.datetime.combine(p["date"], datetime.time(9, 0), tzinfo=datetime.timezone.utc))
        items.append(
            f"<item><title>{html.escape(p['title'])}</title><link>{url}</link>"
            f"<guid>{url}</guid><pubDate>{pub}</pubDate></item>")

    entries = "\n".join(
        f'    <div class="entry"><a class="title" href="/writing/{p["slug"]}.html">{html.escape(p["title"])}</a>'
        f'<div class="meta">{p["date"].strftime("%B %Y")}</div></div>'
        for p in posts)
    index = POST_TEMPLATE.format(title="Writing", date_pretty="", body=entries)
    index = index.replace('<div class="date"></div>', "")
    (ROOT / "writing.html").write_text(index)

    rss = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
           f"<title>Jérémy Scheurer</title><link>{SITE}</link>"
           "<description>Writing by Jérémy Scheurer</description>\n"
           + "\n".join(items) + "\n</channel></rss>\n")
    (ROOT / "feed.xml").write_text(rss)
    print(f"built {len(posts)} post(s), writing.html, feed.xml")
    print("reminder: ensure the Writing nav link exists on index.html and about.html")


if __name__ == "__main__":
    main()
