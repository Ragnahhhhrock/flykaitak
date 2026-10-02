"""Download source tiles for Fly Kai Tak (cached under tools/cache, not committed).
Imagery & basemap: Hong Kong Lands Department open data (CSDI). Elevation: AWS Terrain Tiles (SRTM)."""
import os,sys
sys.path.insert(0,os.path.dirname(__file__));os.chdir(os.path.dirname(os.path.abspath(__file__)))
from tiles import mosaic
from geo import bbox_ll,OUTER,INNER,BLD
jobs=[('img',14,OUTER),('img',16,INNER),('base',14,OUTER),('base',16,BLD),('dem',13,OUTER)]
for kind,z,R in jobs:
    lat0,lon0,lat1,lon1=bbox_ll(R)
    im,o=mosaic(kind,z,lat0,lon0,lat1,lon1)
    im.save(f'cache/{kind}_z{z}.png');open(f'cache/{kind}_z{z}.txt','w').write(' '.join(map(str,o)));print(kind,z,im.size,o,flush=True)
