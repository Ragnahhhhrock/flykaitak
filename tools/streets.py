"""Minor streets under the Kai Tak approach (Kowloon City / San Po Kong / Kowloon Tsai) -> ../assets/streets.json"""
import os,sys,json,math
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import morphology
sys.path.insert(0,os.path.dirname(__file__));os.chdir(os.path.dirname(os.path.abspath(__file__)))
from geo import *
Image.MAX_IMAGE_PIXELS=None
b=np.asarray(Image.open('cache/base_z16.png').convert('RGB'));o=list(map(int,open('cache/base_z16.txt').read().split()))
def px(x,z):
    lat,lon=to_ll(x,z);mx,my=merc(np.array(lat),np.array(lon),16);return int((float(mx)-o[0])*256),int((float(my)-o[1])*256)
x0,y0=px(-2600,-2000);x1,y1=px(900,600)
c=b[y0:y1,x0:x1].astype(int)
white=(c[:,:,0]>250)&(c[:,:,1]>250)&(c[:,:,2]>250)
main=((c[:,:,0]==255)&(abs(c[:,:,1]-225)<6))|((c[:,:,0]==255)&(abs(c[:,:,1]-211)<6))|((c[:,:,0]==255)&(abs(c[:,:,1]-176)<6))
m=morphology.remove_small_objects(white|main,60)
sk=morphology.skeletonize(m)
H,W=sk.shape
nb=ndimage.convolve(sk.astype(int),np.ones((3,3),int),mode='constant')-1;nb=np.where(sk,nb,0);node=sk&(nb!=2)
vis=np.zeros_like(sk)
def pt(y,x):
    mx=o[0]+(x0+x+.5)/256;my=o[1]+(y0+y+.5)/256;n=2**16;lon=mx/n*360-180;lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*my/n))));return to_xz(lat,lon)
def neigh(y,x):
    for dy in(-1,0,1):
        for dx in(-1,0,1):
            if (dy or dx) and 0<=y+dy<H and 0<=x+dx<W and sk[y+dy,x+dx]:yield y+dy,x+dx
def rdp(P,eps):
    if len(P)<3:return P
    a=np.array(P[0]);q=np.array(P[-1]);d=q-a;L=np.hypot(*d)or 1
    ds=[abs(d[0]*(a[1]-p[1])-d[1]*(a[0]-p[0]))/L for p in P[1:-1]];i=int(np.argmax(ds))+1
    if ds[i-1]>eps:return rdp(P[:i+1],eps)[:-1]+rdp(P[i:],eps)
    return [P[0],P[-1]]
sys.setrecursionlimit(20000);out=[]
ys,xs=np.nonzero(node)
for y,x in zip(ys,xs):
    for n1 in neigh(y,x):
        if vis[n1]:continue
        path=[(y,x),n1];vis[n1]=True;prev=(y,x);cur=n1
        while not node[cur]:
            nx=[q for q in neigh(*cur) if q!=prev and not vis[q]]
            if not nx:
                nx=[q for q in neigh(*cur) if q!=prev and node[q]]
                if not nx:break
            prev,cur=cur,nx[0];path.append(cur)
            if not node[cur]:vis[cur]=True
        P=[pt(*q) for q in path];L=sum(math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]) for i in range(1,len(P)))
        if L>60:out.append([[round(a),round(c2)] for a,c2 in rdp(P,3)])
json.dump(out,open('../assets/streets.json','w'),separators=(',',':'));print('streets',len(out),os.path.getsize('../assets/streets.json')//1024,'KB')
