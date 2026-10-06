#!/usr/bin/env python3
"""Compose the reel's music: an original, synthesised track (no samples, nothing to license).

Usage:  python3 tools/reel_music.py OUT.wav TOTAL_SECONDS CUT1,CUT2,...

144 BPM, E minor, built to feel like a low final over Kowloon: a drone and a heartbeat kick at the start, a driving
8th-note bass and an arpeggio as the approach builds, the full kit through the turn, the storms and the touchdowns,
then the drums drop out for the runway lights, a riser, and one big hit when the end card arrives.
CUTS are the times (seconds) where the picture cuts; each gets a reversed-crash swell into it and a hit on it.
The last cut is the end card. Needs: numpy, scipy.
"""
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
BPM = 144
BEAT = 60 / BPM
rng = np.random.default_rng(1998)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a, d, s=0.0, r=0.0, sustain_len=0):
    """Simple attack / exponential decay envelope over n samples."""
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-t / max(d, 1e-4))
    return e


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp(x, lo, hi):
    b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    ph = (freq * (1 + detune) * t) % 1.0
    return 2 * ph - 1


def add(buf, start, x, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i] * gain


def kick(n=int(0.45 * SR)):
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.16)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.004) * 0.25
    return np.tanh(1.6 * (body + click))


def snare(n=int(0.3 * SR)):
    t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 1500, 9000) * np.exp(-t / 0.09)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05)
    return np.tanh(1.4 * (0.9 * noise + 0.5 * tone))


def hat(open_=False):
    n = int((0.22 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t / (0.09 if open_ else 0.015))


def reverb_ir(sec=2.2):
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((2, n)) * np.exp(-t / 0.55)
    ir = np.stack([lp(ch, 5000) for ch in ir])
    ir[:, : int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    return ir * 0.05


def impact(n=int(2.4 * SR)):
    t = np.arange(n) / SR
    f = 34 + 70 * np.exp(-t / 0.12)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    boom = lp(rng.standard_normal(n), 900) * np.exp(-t / 0.35) * 0.9
    crash = hp(rng.standard_normal(n), 3500) * np.exp(-t / 0.7) * 0.35
    return np.tanh(1.5 * (sub + boom + crash))


def swell(n):
    """Reversed crash: noise that grows into the cut."""
    t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 2500) * np.exp(-(t[::-1]) / (n / SR / 3.0))
    return x * np.linspace(0, 1, n) ** 1.5


def riser(n):
    t = np.arange(n) / SR
    f = 180 * (24 ** (t / (n / SR)))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    noise = hp(rng.standard_normal(n), 1500) * 0.5
    return (tone + noise) * (np.linspace(0, 1, n) ** 2.2)


# chords per bar (4 bars loop): Em | Em | C | D, as MIDI note sets
CHORDS = [(40, [64, 67, 71]), (40, [64, 67, 71]), (36, [60, 64, 67]), (38, [62, 66, 69])]


def compose(total, cuts):
    n = int(total * SR)
    mix = np.zeros((2, n))
    drums = np.zeros(n)
    kick_only = np.zeros(n)   # for sidechain ducking
    bass = np.zeros(n)
    arp = np.zeros(n)
    pad = np.zeros(n)
    fx = np.zeros(n)
    verb_send = np.zeros(n)

    end_card = cuts[-1] if cuts else total - 5
    drop = end_card - 4.2          # the drums leave for the runway-lights shot

    def sec_in(t, a, b):
        return a <= t < b

    k, sn, h1, h2 = kick(), snare(), hat(), hat(True)
    n_beats = int(total / BEAT) + 1

    # --- drone: a low E with a slow rise, the whole way
    t = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 41.2 * t) + 0.5 * lp(saw(82.4, n), 300)) * 0.35
    drone *= np.clip(0.35 + t / total * 0.8, 0, 1)
    bass_gain = np.interp(t, [0, 5, 10, 14, drop, drop + 0.5, total], [0, 0.15, 0.7, 1, 1, 0.25, 0.25])

    for b in range(n_beats):
        tb = b * BEAT
        bar = int(tb / (BEAT * 4))
        bar_beat = b % 4
        root, chord = CHORDS[bar % 4]
        # kick: heartbeat (beats 1 and 3, quiet) at first, four on the floor from 5 s
        if tb < drop:
            if tb < 5:
                if bar_beat in (0, 2) or (bar_beat == 3 and tb > 2.5):
                    add(kick_only, tb, k, 0.55 + 0.04 * tb)
            else:
                add(kick_only, tb, k, 0.9)
        # snare on 2 and 4 from 14 s, rolls in the last beats before the drop and before each storm cut
        if 14 <= tb < drop and bar_beat in (1, 3):
            add(drums, tb, sn, 0.7)
        if tb >= 10 and tb < drop:
            for s in range(4):
                add(drums, tb + s * BEAT / 4, h1, 0.22 + 0.12 * (s % 2 == 0) * (tb >= 14))
            add(drums, tb + BEAT / 2 - BEAT / 8, h2, 0.18) if bar_beat in (1, 3) else None
        # snare roll on the last bar before the drop
        if drop - BEAT * 4 <= tb < drop:
            for s in range(8):
                add(drums, tb + s * BEAT / 8, sn, 0.25 + 0.5 * ((tb - (drop - BEAT * 4)) / (BEAT * 4)))
        # bass: driving 8ths, octave jump on the off-beat
        for half in range(2):
            tt = tb + half * BEAT / 2
            f = mtof(root + (12 if half else 0))
            m = int(BEAT / 2 * SR)
            note = lp(saw(f, m), 700 + 900 * (tb / total)) * env(m, 0.004, 0.22)
            add(bass, tt, note, 0.8)
        # arpeggio: 16ths over the chord, two octaves, from 5 s
        if tb >= 5:
            for s in range(4):
                tt = tb + s * BEAT / 4
                idx = (b * 4 + s) % 6
                m_ = chord + [chord[0] + 12, chord[1] + 12, chord[2] + 12]
                f = mtof(m_[idx] + 12 * (tb > 24))
                m = int(BEAT / 4 * SR * 1.6)
                note = (saw(f, m) + saw(f, m, 0.006)) * 0.5
                note = lp(note, 1200 + 5000 * min(1, tb / 30)) * env(m, 0.002, 0.11)
                add(arp, tt, note, 0.5 if tb < drop else 0.0)
        # chord stabs (distorted) on the off-beats from 34 s
        if 34 <= tb < drop and bar_beat in (0, 2):
            for nn in chord:
                m = int(BEAT * 0.9 * SR)
                st = np.tanh(3 * lp(saw(mtof(nn - 12), m) + saw(mtof(nn - 12), m, 0.008), 2400)) * env(m, 0.003, 0.16)
                add(pad, tb + BEAT / 2, st, 0.2)

    # pad: slow chords, filtered up as the piece builds
    for bar in range(int(total / (BEAT * 4)) + 1):
        tb = bar * BEAT * 4
        root, chord = CHORDS[bar % 4]
        m = int(BEAT * 4 * SR * 1.05)
        for nn in chord:
            v = (saw(mtof(nn), m) + saw(mtof(nn), m, 0.007) + saw(mtof(nn), m, -0.007)) / 3
            v = lp(v, 500 + 2500 * min(1, tb / 30))
            v *= np.minimum(np.arange(m) / (0.4 * SR), 1) * np.minimum((m - np.arange(m)) / (0.4 * SR), 1)
            add(pad, tb, v, 0.11)

    # riser into the end card and a reversed crash into every cut, a hit on every cut
    rn = int(4.2 * SR)
    add(fx, end_card - 4.2, riser(rn), 0.55)
    for c in cuts:
        sw = int(min(0.9, c) * SR)
        add(fx, c - sw / SR, swell(sw), 0.45)
        big = c == end_card
        add(fx, c, impact(), 0.85 if big else 0.5)
    # a short silent beat just before the end-card hit so it lands
    gap0, gap1 = int((end_card - 0.18) * SR), int(end_card * SR)
    bass[gap0:gap1] *= 0.0
    arp[gap0:gap1] *= 0.0
    fx_keep = fx.copy()

    # sidechain: everything but the drums ducks on each kick
    duck = np.ones(n)
    kicks = np.where(np.abs(kick_only) > 0)[0]
    pulse = np.zeros(n)
    beat_idx = (np.arange(n_beats) * BEAT * SR).astype(int)
    for bi in beat_idx:
        if bi < n and np.abs(kick_only[bi: bi + 50]).max() > 0:
            ln = int(0.22 * SR)
            seg = 1 - 0.6 * np.exp(-np.arange(min(ln, n - bi)) / (0.07 * SR))
            duck[bi: bi + len(seg)] = np.minimum(duck[bi: bi + len(seg)], seg)
    musical = (drone * 0.8 + bass * bass_gain * 0.9 + arp * 0.7 + pad) * duck
    verb_send = arp * 0.5 + pad * 0.6 + drums * 0.15 + fx * 0.25
    dry = musical + kick_only * 1.0 + drums * 0.8 + fx

    ir = reverb_ir()
    wet = np.stack([signal.fftconvolve(verb_send, ir[0])[:n], signal.fftconvolve(verb_send, ir[1])[:n]])
    # stereo: arp and hats a little wide, the rest centred
    left = dry + wet[0] + np.roll(arp, int(0.011 * SR)) * 0.12
    right = dry + wet[1] + np.roll(arp, -int(0.011 * SR)) * 0.12
    mix = np.stack([left, right])

    # master: fade in 0.3 s, long tail out, soft clip, normalise
    fade_in = np.minimum(np.arange(n) / (0.3 * SR), 1)
    fade_out = np.minimum((n - np.arange(n)) / (1.4 * SR), 1)
    mix = mix * fade_in * fade_out
    mix = np.tanh(1.3 * mix / np.abs(mix).max())
    mix = mix / np.abs(mix).max() * 0.89
    return mix


def main():
    out = sys.argv[1]
    total = float(sys.argv[2])
    cuts = [float(c) for c in sys.argv[3].split(",") if c]
    m = compose(total, cuts)
    wavfile.write(out, SR, (m.T * 32767).astype(np.int16))
    print("wrote", out, round(total, 1), "s", "cuts:", cuts)


if __name__ == "__main__":
    main()
