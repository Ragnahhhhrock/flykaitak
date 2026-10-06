#!/usr/bin/env python3
"""Assemble the social reel from the frames tools/reel.py rendered.

Usage:  python3 tools/reel_assemble.py FRAMES_DIR OUT_DIR [yt|ig|all] [--card-dir DIR]

FRAMES_DIR holds yt/<shot>/f*.jpg and ig/<shot>/f*.jpg (12 fps frames); the end cards come from
tools/reel_card.py (default FRAMES_DIR/card). Each shot is motion-interpolated to 24 fps on its own, so the
interpolation never blends across a cut, then the shots are joined, the end card fades in and the file is
encoded with an original synthesised music track (tools/reel_music.py), cut to the picture.
Outputs in OUT_DIR:
  flykaitak-reel-youtube-1080p.mp4        1920x1080, 24 fps
  flykaitak-reel-facebook-1080p.mp4       the same cut, a lighter encode
  flykaitak-reel-instagram-1080x1920.mp4  1080x1920, 24 fps (also fits YouTube Shorts)
  instagram-cover.jpg                     a still from the overhead pass, for the Reels cover
Needs: ffmpeg.
"""
import argparse
import importlib.util
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reel", HERE / "reel.py")
reel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reel)

CARD_SECONDS = 5.0
FADE = 0.6          # the last shot dissolves into the end card
X264 = ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "24"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + " ".join(map(str, cmd)) + "\n" + r.stderr[-1500:])
    return r.stdout


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).strip())


def shot_clip(frames, tmp, fmt, name):
    out = tmp / f"{fmt}-{name}.mp4"
    if out.exists():
        return out
    night = any(s["name"] == name and s["start"].get("night") for s in reel.SHOTS)
    lift = ",eq=gamma=1.15:saturation=1.05" if night else ""   # night takes are dark on a phone: lift them a little
    run(["ffmpeg", "-v", "error", "-y", "-framerate", "12", "-i", str(frames / fmt / name / "f%05d.jpg"),
         "-vf", "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" + lift + ",format=yuv420p",
         "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-r", "24", str(out)])
    return out


def build(fmt, frames, card_dir, out_dir, only):
    tmp = out_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    names = [s["name"] for s in reel.SHOTS if (not only or s["name"][:2] in only)]
    missing = [n for n in names if not (frames / fmt / n / "DONE").exists()]
    if missing:
        sys.exit(f"{fmt}: shots not rendered yet: {', '.join(missing)}")
    clips = [shot_clip(frames, tmp, fmt, n) for n in names]
    w, h = reel.FORMATS[fmt]
    body = sum(duration(c) for c in clips)
    ins, chain = [], []
    for c in clips:
        ins += ["-i", str(c)]
    n = len(clips)
    # the music: a hit on every cut, the big one when the end card arrives
    total_len = body + CARD_SECONDS - FADE
    cuts, acc = [], 0.0
    for c in clips[:-1]:
        acc += duration(c)
        cuts.append(round(acc, 3))
    cuts.append(round(body - FADE, 3))
    wav = tmp / f"music-{fmt}.wav"
    run([sys.executable, str(HERE / "reel_music.py"), str(wav), f"{total_len:.3f}", ",".join(map(str, cuts))])
    ins += ["-loop", "1", "-framerate", "24", "-t", str(CARD_SECONDS), "-i", str(card_dir / f"card-{fmt}.png"),
            "-i", str(wav)]
    chain.append("".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0,fps=24,settb=AVTB[body]")
    chain.append(f"[{n}:v]format=yuv420p,setsar=1,fps=24,settb=AVTB[card]")
    chain.append(f"[body][card]xfade=transition=fade:duration={FADE}:offset={body - FADE:.3f}[x]")
    total = body + CARD_SECONDS - FADE
    chain.append(f"[x]fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.5:.3f}:d=0.5[v]")
    master = out_dir / f"master-{fmt}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(chain), "-map", "[v]", "-map", f"{n + 1}:a",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         *X264, "-crf", "16", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(master)])
    print(fmt, f"{w}x{h}", round(duration(master), 1), "s", master.stat().st_size // 1024 // 1024, "MB", flush=True)
    return master


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames")
    ap.add_argument("out")
    ap.add_argument("fmt", nargs="?", default="all", choices=["yt", "ig", "all"])
    ap.add_argument("--card-dir")
    ap.add_argument("--only", default="", help="comma list of shot numbers, to test with a few shots")
    a = ap.parse_args()
    frames, out = pathlib.Path(a.frames), pathlib.Path(a.out)
    card_dir = pathlib.Path(a.card_dir) if a.card_dir else frames / "card"
    only = {s for s in a.only.split(",") if s}
    out.mkdir(parents=True, exist_ok=True)
    if a.fmt in ("yt", "all"):
        m = build("yt", frames, card_dir, out, only)
        (out / "flykaitak-reel-youtube-1080p.mp4").write_bytes(m.read_bytes())
        run(["ffmpeg", "-v", "error", "-y", "-i", str(m), *X264, "-crf", "21", "-c:a", "copy", "-movflags", "+faststart",
             str(out / "flykaitak-reel-facebook-1080p.mp4")])
    if a.fmt in ("ig", "all"):
        m = build("ig", frames, card_dir, out, only)
        (out / "flykaitak-reel-instagram-1080x1920.mp4").write_bytes(m.read_bytes())
        cover = frames / "ig" / "06-overhead-pass" / "f00040.jpg"
        if cover.exists():
            (out / "instagram-cover.jpg").write_bytes(cover.read_bytes())


if __name__ == "__main__":
    main()
