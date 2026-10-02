import math,os,sys,io,concurrent.futures as cf,urllib.request
from PIL import Image
def t2(lat,lon,z):
    n=2**z;x=(lon+180)/360*n;y=(1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2*n;return x,y
def ll(x,y,z):
    n=2**z;lon=x/n*360-180;lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n))));return lat,lon
URL={'img':'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{z}/{x}/{y}.png','base':'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/basemap/WGS84/{z}/{x}/{y}.png','dem':'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'}
def get(kind,z,x,y):
    p=f'cache/{kind}/{z}/{x}_{y}.png';os.makedirs(os.path.dirname(p),exist_ok=True)
    if os.path.exists(p) and os.path.getsize(p)>0:return p
    for a in range(4):
        try:
            d=urllib.request.urlopen(URL[kind].format(z=z,x=x,y=y),timeout=40).read();open(p,'wb').write(d);return p
        except Exception as e:
            err=e
    print('fail',kind,z,x,y,err);return None
def mosaic(kind,z,lat0,lon0,lat1,lon1):
    x0,y0=t2(lat1,lon0,z);x1,y1=t2(lat0,lon1,z)
    X0,Y0,X1,Y1=int(x0),int(y0),int(x1),int(y1)
    jobs=[(X,Y) for X in range(X0,X1+1) for Y in range(Y0,Y1+1)]
    with cf.ThreadPoolExecutor(12) as ex: res=list(ex.map(lambda j:get(kind,z,*j),jobs))
    W=(X1-X0+1)*256;H=(Y1-Y0+1)*256;im=Image.new('RGB',(W,H))
    for (X,Y),p in zip(jobs,res):
        if p:
            try: im.paste(Image.open(p).convert('RGB'),((X-X0)*256,(Y-Y0)*256))
            except Exception as e: print('bad',p)
    return im,(X0,Y0,z)
if __name__=='__main__':
    im,o=mosaic('img',17,22.300,114.170,22.345,114.225);im.save('kaitak_z17.jpg',quality=85);print(im.size,o)
