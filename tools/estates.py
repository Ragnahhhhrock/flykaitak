#!/usr/bin/env python3
"""Build assets/estates.json: Hong Kong Housing Authority public housing estates that stood in 1998.

Source: "Public Housing Estates in Hong Kong" (Housing Authority via DATA.GOV.HK, hosted by Esri China (Hong Kong) Ltd.,
https://opendata.esrichina.hk/maps/fcb36abecd2347a59f6fff75400784ca/explore). An estate is kept when its earliest year of intake is 1998 or earlier.
Each row: [x, z, blocks, year, [block types], name_en, name_zh] with x, z in the sim's metres (see geo.py).
"""
import json, pathlib, re, urllib.request, urllib.parse
from geo import to_xz

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://services3.arcgis.com/6j1KwZfY2fZrfNMR/arcgis/rest/services/Public_Housing_Estates_in_Hong_Kong/FeatureServer/0/query"


def kinds(s):
    s = (s or "").lower()
    out = []
    for key, k in (("trident", "Y"), ("harmony", "cross"), ("cruciform", "cross"), ("twin tower", "twin"), ("double h", "H"), ("triple h", "H"),
                   ("single h", "H"), ("small household", "small"), ("old slab", "oldslab"), ("new slab", "slab"), ("linear", "slab"),
                   ("non-standard", "free"), ("non standard", "free")):
        if key in s and k not in out:
            out.append(k)
    return out or ["free"]


def main():
    q = urllib.parse.urlencode({"where": "1=1", "outFields": "*", "returnGeometry": "false", "outSR": "4326", "f": "json"})
    feats = json.load(urllib.request.urlopen(URL + "?" + q))["features"]
    rows = []
    for f in feats:
        a = f["attributes"]
        yrs = [int(y) for y in re.findall(r"(?:19|20)\d\d", a.get("Year_of_Intake_en") or "")]
        if not yrs or min(yrs) > 1998 or a.get("Latitude") is None:
            continue
        x, z = to_xz(a["Latitude"], a["Longitude"])
        rows.append([round(x), round(z), int(a.get("No__of_Blocks") or 4), min(yrs), kinds(a.get("Type_s__of_Block_s__en")),
                     a["Estate_Name_en"], a.get("Estate_Name_zh_Hant") or ""])
    (ROOT / "assets/estates.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    print(len(feats), "estates,", len(rows), "in service by 1998")


if __name__ == "__main__":
    main()
