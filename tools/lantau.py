"""West Lantau terrain patch for Fly Kai Tak (Ngong Ping, Lantau Peak and the Big Buddha).
The main terrain (build.py) stops at x = -28000; this patch carries the island on to the west.
Downloads its own tiles (cached under tools/cache) and writes:
  ../assets/lantau.json      {"b64": <int32 nx, nz, then int16 heights x10>}  grid over LANTAU at 50 m
  ../assets/aerial_lantau.jpg
"""
import os,sys,json,struct,base64
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0,os.path.dirname(__file__));os.chdir(os.path.dirname(os.path.abspath(__file__)))
from geo import to_ll,merc,bbox_ll
from tiles import mosaic
Image.MAX_IMAGE_PIXELS=None
LANTAU=(-36800,3800,-28000,14000)   # x0,z0,x1,z1 metres; the east edge meets the outer grid
D=50;NX=int((LANTAU[2]-LANTAU[0])/D)+1;NZ=int((LANTAU[3]-LANTAU[1])/D)+1
OUT='../assets';os.makedirs('cache',exist_ok=True)

def get(kind,z):
    p=f'cache/lantau_{kind}_z{z}.png'
    if not os.path.exists(p):
        im,o=mosaic(kind,z,*bbox_ll(LANTAU));im.save(p);open(p[:-4]+'.txt','w').write(' '.join(map(str,o)))
    return np.asarray(Image.open(p).convert('RGB')),list(map(int,open(p[:-4]+'.txt').read().split()))
def sample(im,o,X,Z):
    lat,lon=to_ll(X,Z);mx,my=merc(lat,lon,o[2]);px=(mx-o[0])*256-.5;py=(my-o[1])*256-.5
    if im.ndim==2:return ndimage.map_coordinates(im.astype(np.float32),[py,px],order=1,mode='nearest')
    return np.stack([ndimage.map_coordinates(im[:,:,c].astype(np.float32),[py,px],order=1,mode='nearest') for c in range(3)],-1)
def watermask(im):
    r,g,b=im[:,:,0].astype(int),im[:,:,1].astype(int),im[:,:,2].astype(int)
    return ((abs(r-204)<10)&(abs(g-236)<10)&(b>245))|((abs(r-160)<12)&(g>220)&(b>245))

x0,z0,x1,z1=LANTAU
X,Z=np.meshgrid(np.linspace(x0,x1,NX),np.linspace(z0,z1,NZ))
dem,od=get('dem',13);H=(dem[:,:,0].astype(np.float32)*256+dem[:,:,1]+dem[:,:,2]/256.)-32768
base,ob=get('base',14);W=watermask(base).astype(np.float32)
h=sample(H,od,X,Z);water=sample(W,ob,X,Z)>.5
hl=ndimage.gaussian_filter(np.where(water,0,h),1.0)   # SRTM is already smooth on these hills; just take the speckle off
h=np.where(water,-8.0,np.maximum(hl,3.5))
# fade the north, west and south edges into the sea so the island does not end in a cliff
e=np.minimum.reduce([(X-x0)/600,(Z-z0)/600,(z1-Z)/600]);h=np.where(e<1,np.minimum(h,-8+(h+8)*np.clip(e,0,1)),h)
open(f'{OUT}/lantau.json','w').write(json.dumps({'b64':base64.b64encode(struct.pack('<2i',NX,NZ)+np.round(h*10).astype('<i2').tobytes()).decode()}))
print('lantau.json',NX,NZ,'h',h.min(),h.max())
img,oi=get('img',15)
TW,TH=1760,2040
TX,TZ=np.meshgrid(np.linspace(x0,x1,TW),np.linspace(z0,z1,TH))
a=np.clip(sample(img,oi,TX,TZ),0,255).astype(np.uint8)
Image.fromarray(a).save(f'{OUT}/aerial_lantau.jpg',quality=80,optimize=True,progressive=True)
print('aerial_lantau.jpg',os.path.getsize(f'{OUT}/aerial_lantau.jpg')//1024,'KB')
