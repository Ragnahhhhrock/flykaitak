# Fly Kai Tak · helicopter tour promo: titles, descriptions, tags

One vertical cut, **52 seconds, 1080×1920 at 24 fps**: `flykaitak-helicopter-tour-1080x1920.mp4`. Cover still: `helicopter-tour-cover.jpg` (the S-76 over Victoria Harbour, with Central behind).

Everything was recorded from the sim's Harbour helicopter tour (`tools/tour_promo.py`). It has nine takes: the Peninsula rooftop, the window seat, the harbour, Central, the Peak, Wan Chai, Kai Tak, the harbour at night, and the landing back on the roof. Each take carries an on-screen line, and the video ends on a "Take the tour" card with flykaitak.com. The audio is the project's own synthesised music (`tools/reel_music.py`) with a synthesised rotor underneath. There is nothing to license, so you should not get a copyright claim, but you can swap in a trending track inside each app.

On-screen text stays out of the top 140 px and the bottom 330 px, which are the zones the apps cover with their own buttons. The same file works on all six platforms (each takes 9:16 up to 60 s).

| Platform | Upload as | Limits worth knowing |
|---|---|---|
| YouTube Shorts | the MP4 | title 100 chars; vertical under 60 s posts as a Short |
| Instagram Reels | the MP4, cover `helicopter-tour-cover.jpg` | caption 2,200 chars, up to 30 hashtags (5 or so works best); links only in bio |
| Facebook Reels | the MP4 | |
| TikTok | the MP4 | caption 2,200 chars; links only in bio |
| X (Twitter) | the MP4 | 280 chars |
| Threads | the MP4 | 500 chars, one topic tag |

Every link carries `utm_source` / `utm_medium=social` / `utm_campaign=heli_tour` so the visits show up in Analytics.

---

## YouTube Shorts

**Title** (63 characters)
```
Fly over 1998 Hong Kong in a helicopter 🚁 Free in your browser
```

**Description**
```
Take the Harbour helicopter tour in Fly Kai Tak: you ride in a Sikorsky S-76 from the roof of the Peninsula Hotel, across Victoria Harbour to Central, past the Shun Tak ferry terminal, under Victoria Peak, along Wan Chai and Causeway Bay with Kai Tak in view, and back to the roof.

It takes about four minutes, with a spoken guide and captions in English and Cantonese. You can fly it by day or night, in any weather.

Free, in your browser, no download and no sign-up:
https://flykaitak.com/?utm_source=youtube&utm_medium=social&utm_campaign=heli_tour

維港直升機觀光 · 啟德機場
#Shorts #FlyKaiTak #HongKong #KaiTak #Helicopter
```

**Tags**
```
Fly Kai Tak, Hong Kong helicopter tour, Victoria Harbour, 1998 Hong Kong, Kai Tak, 啟德機場, 維港, Peninsula Hotel helipad, Sikorsky S-76, helicopter simulator, flight simulator, browser game, free game, Hong Kong history, nostalgia
```

**Category:** Gaming · **Pinned comment:**
```
Ride along free here 👉 https://flykaitak.com/?utm_source=youtube&utm_medium=social&utm_campaign=heli_tour  Night or day?
```

---

## Instagram Reels

**Caption** (the first line shows before "more")
```
Your helicopter is waiting on the Peninsula roof. 🚁

Ride along over 1998 Hong Kong: Victoria Harbour, Central, the Peak, Wan Chai, with jets landing at Kai Tak across the bay. It takes four minutes, with a spoken guide in English and Cantonese.

Free in your browser, with no download. Link in bio.

維港直升機觀光
#FlyKaiTak #HongKong #VictoriaHarbour #KaiTak #啟德機場 #Helicopter #HongKong1998 #FlightSim #RetroHongKong #Aviation
```

**Cover:** `helicopter-tour-cover.jpg`. For the grid crop, keep the centre 3:4. **Alt text:** `A green helicopter flies over Victoria Harbour toward the Central skyline in a 1998 Hong Kong flight simulator.`
**Bio link:** `https://flykaitak.com/?utm_source=instagram&utm_medium=social&utm_campaign=heli_tour`

---

## Facebook Reels

**Title**
```
Take the Hong Kong harbour helicopter tour, 1998
```

**Post text**
```
Your helicopter is waiting on the roof of the Peninsula. 🚁

In Fly Kai Tak you can now ride a four-minute scenic flight over 1998 Hong Kong: across Victoria Harbour to Central, under the Peak, along Wan Chai and Causeway Bay with Kai Tak in view, and back to the rooftop pad. A guide talks you through it in English or Cantonese, by day or night.

Free in your browser, no download, no sign-up 👉 https://flykaitak.com/?utm_source=facebook&utm_medium=social&utm_campaign=heli_tour

維港直升機觀光 #FlyKaiTak #HongKong #KaiTak
```

---

## TikTok

**Caption**
```
POV: it's 1998 and your helicopter leaves from the Peninsula roof 🚁 Victoria Harbour, Central, the Peak, and Kai Tak jets across the bay. Free in your browser, link in bio. 維港直升機觀光
#hongkong #hongkong1998 #kaitak #helicopter #flightsim #fyp #nostalgia #retrohongkong #香港 #啟德
```

**On-cover text** (pick a frame from take 3 or 4)
```
Hong Kong, 1998 🚁
```

**Bio link:** `https://flykaitak.com/?utm_source=tiktok&utm_medium=social&utm_campaign=heli_tour`
**Settings:** add the tags as a "Gaming" post, allow Duet/Stitch (people like to react to retro Hong Kong).

---

## X (Twitter)

**Post** (239 characters with the link counted as 23)
```
Fly over 1998 Hong Kong in a helicopter 🚁

From the Peninsula roof, across Victoria Harbour to Central, under the Peak, with jets landing at Kai Tak across the bay.

Free in your browser:
https://flykaitak.com/?utm_source=twitter&utm_medium=social&utm_campaign=heli_tour

#FlyKaiTak #HongKong
```

**Reply to self** (keeps the link conversation going)
```
About 4 minutes, with a spoken guide in English or Cantonese 🇭🇰 Works day or night, in any weather, and on your phone too.
```

---

## Threads

**Post** (about 330 characters)
```
It's 1998, and your helicopter is waiting on the roof of the Peninsula. 🚁

Fly Kai Tak's harbour tour takes you over Victoria Harbour to Central, under the Peak, along Wan Chai, and past Kai Tak with jets landing across the bay. It takes four minutes, with a guide in English or Cantonese.

Free in your browser 👉 flykaitak.com
```

**Topic tag:** `Hong Kong`
**Link attachment:** `https://flykaitak.com/?utm_source=threads&utm_medium=social&utm_campaign=heli_tour`

---

## Rebuild

```
python3 tools/tour_promo.py scout              # 3 stills per take, to check framing
python3 tools/tour_promo.py render             # frames (resumable; about 40 min in software WebGL)
python3 tools/tour_promo.py build              # overlays, end card, music + rotor -> this folder
```
