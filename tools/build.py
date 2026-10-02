"""Build Fly Kai Tak geo assets from cached tiles (run fetch.py first).
Outputs in ../assets:
  aerial_outer.jpg  aerial_inner.jpg  terrain.json  buildings.json  roads.json (binary grids as base64)
"""
import os,sys,json,math,struct
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure,morphology
sys.path.insert(0,os.path.dirname(__file__));os.chdir(os.path.dirname(os.path.abspath(__file__)))
from geo import *
Image.MAX_IMAGE_PIXELS=None
OUT='../assets';os.makedirs(OUT,exist_ok=True)

def load(name):
    im=np.asarray(Image.open(f'cache/{name}.png').convert('RGB'));o=list(map(int,open(f'cache/{name}.txt').read().split()));return im,o
def grid(R,nx,nz):
    x0,z0,x1,z1=R;xs=np.linspace(x0,x1,nx);zs=np.linspace(z0,z1,nz);X,Z=np.meshgrid(xs,zs);return X,Z
def sample(im,o,X,Z,order=1):
    lat,lon=to_ll(X,Z);mx,my=merc(lat,lon,o[2]);px=(mx-o[0])*256-.5;py=(my-o[1])*256-.5
    if im.ndim==2: return ndimage.map_coordinates(im.astype(np.float32),[py,px],order=order,mode='nearest')
    return np.stack([ndimage.map_coordinates(im[:,:,c].astype(np.float32),[py,px],order=order,mode='nearest') for c in range(im.shape[2])],-1)

# ---------- aerial textures ----------
def aerial(src,R,W,H,out,q):
    im,o=load(src);X,Z=grid(R,W,H);a=sample(im,o,X,Z)
    a=np.clip(a,0,255).astype(np.uint8)
    Image.fromarray(a).save(f'{OUT}/{out}',quality=q,optimize=True,progressive=True);print(out,W,H,os.path.getsize(f'{OUT}/{out}')//1024,'KB')
if not os.path.exists(f'{OUT}/aerial_outer.jpg'): aerial('img_z14',OUTER,4096,3024,'aerial_outer.jpg',82)
if not os.path.exists(f'{OUT}/aerial_inner.jpg'): aerial('img_z16',INNER,4096,4096,'aerial_inner.jpg',80)

# ---------- water mask & heights ----------
def watermask(im):
    r,g,b=im[:,:,0].astype(int),im[:,:,1].astype(int),im[:,:,2].astype(int)
    return ((abs(r-204)<10)&(abs(g-236)<10)&(b>245))|((abs(r-160)<12)&(g>220)&(b>245))
b14,o14=load('base_z14');b16,o16=load('base_z16');dem,od=load('dem_z13')
w14=watermask(b14).astype(np.float32);w16=watermask(b16).astype(np.float32)
D=(dem[:,:,0].astype(np.float32)*256+dem[:,:,1]+dem[:,:,2]/256.)-32768
def heights(R,nx,nz,use16):
    X,Z=grid(R,nx,nz);h=sample(D,od,X,Z);w=sample(w14,o14,X,Z)
    if use16:
        w2=sample(w16,o16,X,Z);x0,z0,x1,z1=BLD;inb=(X>x0+50)&(X<x1-50)&(Z>z0+50)&(Z<z1-50);w=np.where(inb,w2,w)
    water=w>.5
    # strip building bumps from the surface model: grey opening wider than a city block, then smooth
    cell=(R[2]-R[0])/(nx-1);k=max(3,int(round(220/cell))|1)
    hl=np.where(water,0,h);ho_=ndimage.grey_opening(hl,size=(k,k))
    # vegetated ground (from the aerial) is natural terrain: keep its full height
    img,oi=load('img_z16' if use16 else 'img_z14');c=sample(img,oi,X,Z).astype(np.float32)
    veg=((c[:,:,1]>c[:,:,0]*1.04)&(c[:,:,1]>c[:,:,2]*1.0)).astype(np.float32)
    veg=ndimage.gaussian_filter(veg,max(1,40/cell));veg=np.clip((veg-.35)*3,0,1)
    hl=ho_*(1-veg)+ndimage.gaussian_filter(hl,max(.5,25/cell))*veg
    hl=ndimage.gaussian_filter(hl,max(.6,40/cell))
    h=np.where(water,-8.0,np.maximum(hl,3.5))
    # coastal smoothing: land within ~2 cells of water stays low
    return h.astype(np.float32),water
ho,_=heights(OUTER,421,311,False)
hi,wi=heights(INNER,513,513,True)
import base64
def b64json(name,data): json.dump({'b64':base64.b64encode(data).decode()},open(f'{OUT}/{name}.json','w'))
b64json('terrain',struct.pack('<4i',421,311,513,513)+np.round(ho*10).astype('<i2').tobytes()+np.round(hi*10).astype('<i2').tobytes())
print('terrain.json','outer h range',ho.min(),ho.max())

# ---------- building footprints ----------
r,g,b=b16[:,:,0].astype(int),b16[:,:,1].astype(int),b16[:,:,2].astype(int)
bm=(abs(r-200)<6)&(abs(g-205)<6)&(abs(b-225)<6)
lab=measure.label(bm,connectivity=1)
props=measure.regionprops(lab)
mpp=156543.03392*math.cos(math.radians(LAT0))/2**16
rows=[]
for p in props:
    if p.area<7: continue
    cy,cx=p.centroid;mx=o16[0]+(cx+.5)/256;my=o16[1]+(cy+.5)/256
    n=2**16;lon=mx/n*360-180;lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*my/n))))
    x,z=to_xz(lat,lon)
    th=p.orientation;phi=math.atan2(math.cos(th),math.sin(th))
    a=max(p.major_axis_length,1)/1.155*mpp;bb=max(p.minor_axis_length,1)/1.155*mpp
    area=p.area*mpp*mpp;k=math.sqrt(area/max(a*bb,1));a*=k;bb*=k
    a=min(a,160);bb=min(bb,160)
    rows.append((round(x),round(z),round(a*10),round(bb*10),round(phi*1000),min(int(area),32767)))
B=np.array(rows,dtype='<i2')
b64json('buildings',struct.pack('<i',len(B))+B.tobytes())
print('buildings',len(B))

# ---------- main roads ----------
rm=((r==255)&(abs(g-225)<6)&(abs(b-169)<8))|((r==255)&(abs(g-211)<6)&(abs(b-127)<8))|((r==255)&(abs(g-176)<6)&(b<40))
rm=rm[::2,::2];rm=morphology.binary_closing(rm,morphology.disk(2));rm=morphology.remove_small_objects(rm,400)
sk=morphology.skeletonize(rm)
nb=ndimage.convolve(sk.astype(int),np.ones((3,3),int),mode='constant')-1
nb=np.where(sk,nb,0)
node=sk&(nb!=2)
H,W=sk.shape;visited=np.zeros_like(sk)
def pt(yx):
    cy,cx=yx;mx=o16[0]+(cx*2+1)/256;my=o16[1]+(cy*2+1)/256;n=2**16
    lon=mx/n*360-180;lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*my/n))));return to_xz(lat,lon)
def neigh(y,x):
    for dy in(-1,0,1):
        for dx in(-1,0,1):
            if (dy or dx) and 0<=y+dy<H and 0<=x+dx<W and sk[y+dy,x+dx]: yield y+dy,x+dx
def rdp(P,eps):
    if len(P)<3: return P
    a=np.array(P[0]);bq=np.array(P[-1]);d=bq-a;L=np.hypot(*d)or 1
    ds=[abs(d[0]*(a[1]-p[1])-d[1]*(a[0]-p[0]))/L for p in P[1:-1]];i=int(np.argmax(ds))+1
    if ds[i-1]>eps: return rdp(P[:i+1],eps)[:-1]+rdp(P[i:],eps)
    return [P[0],P[-1]]
lines=[]
sys.setrecursionlimit(10000)
ys,xs=np.nonzero(node)
for y0,x0 in zip(ys,xs):
    for n1 in neigh(y0,x0):
        if visited[n1] : continue
        path=[(y0,x0),n1];visited[n1]=True;prev=(y0,x0);cur=n1
        while not node[cur]:
            nxt=[q for q in neigh(*cur) if q!=prev and not visited[q]]
            if not nxt:
                nxt=[q for q in neigh(*cur) if q!=prev and node[q]]
                if not nxt: break
            prev,cur=cur,nxt[0];path.append(cur)
            if not node[cur]: visited[cur]=True
        P=[pt(q) for q in path]
        L=sum(math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]) for i in range(1,len(P)))
        if L>250: lines.append([[round(a),round(b)] for a,b in rdp(P,6)])
json.dump(lines,open(f'{OUT}/roads.json','w'),separators=(',',':'))
print('roads',len(lines),os.path.getsize(f'{OUT}/roads.json')//1024,'KB')
