#!/usr/bin/env python3
"""Publish queued blog posts (blog/queue/<date>-<slug>/) whose publish time has come.

Each queue folder holds post.json (the posts.json entry plus publish_at, an ISO time with offset),
en.html and zh.html. Publishing copies the bodies to blog/src/, puts the entry at the top of
blog/posts.json with date = the publish day, renders the social card (tools/blog_images.py), rebuilds the
blog (tools/blog.py), and deletes the queue folder.

Usage:
  python3 tools/publish_queue.py              publish everything due now
  python3 tools/publish_queue.py --list       show the queue and what is due
  python3 tools/publish_queue.py --push       also commit and push to main (what a scheduled run uses)
  python3 tools/publish_queue.py --slug SLUG  publish one queued post now, whatever its time
"""
import datetime as dt
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE = ROOT / "blog" / "queue"
HK = dt.timezone(dt.timedelta(hours=8))


def load():
    items = []
    for d in sorted(QUEUE.iterdir()) if QUEUE.exists() else []:
        if (d / "post.json").exists():
            meta = json.loads((d / "post.json").read_text(encoding="utf-8"))
            items.append((dt.datetime.fromisoformat(meta["publish_at"]), d, meta))
    return items


def run(*cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def publish(d, meta):
    slug = meta["slug"]
    entry = {k: v for k, v in meta.items() if k != "publish_at"}
    entry["date"] = dt.datetime.fromisoformat(meta["publish_at"]).astimezone(HK).date().isoformat()
    # keep the key order of existing entries: slug first
    ordered = {"slug": slug, **{k: v for k, v in entry.items() if k != "slug"}}
    posts_path = ROOT / "blog" / "posts.json"
    posts = json.loads(posts_path.read_text(encoding="utf-8"))
    assert all(p["slug"] != slug for p in posts), f"{slug} is already published"
    posts.insert(0, ordered)
    posts_path.write_text(json.dumps(posts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    shutil.copy(d / "en.html", ROOT / "blog" / "src" / f"{slug}.html")
    shutil.copy(d / "zh.html", ROOT / "blog" / "src" / f"{slug}.zh.html")
    shutil.rmtree(d)
    run(sys.executable, "tools/blog_images.py", slug)
    run(sys.executable, "tools/blog.py")


def main():
    args = sys.argv[1:]
    now = dt.datetime.now(HK)
    items = load()
    if "--list" in args:
        for t, d, m in items:
            print(("DUE   " if t <= now else "later ") + t.astimezone(HK).strftime("%a %d %b %H:%M HKT"), m["slug"])
        return
    if "--slug" in args:
        slug = args[args.index("--slug") + 1]
        due = [(t, d, m) for t, d, m in items if m["slug"] == slug]
    else:
        due = [(t, d, m) for t, d, m in items if t <= now]
    if not due:
        print("nothing due")
        return
    for t, d, m in sorted(due, key=lambda x: x[0]):
        print("publishing", m["slug"])
        publish(d, m)
    if "--push" in args:
        run("git", "add", "-A")
        names = ", ".join(m["slug"] for _, _, m in due)
        run("git", "commit", "-m", f"Blog: {names}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
        run("git", "pull", "--rebase", "origin", "main")
        run("git", "push", "origin", "HEAD:main")


if __name__ == "__main__":
    main()
