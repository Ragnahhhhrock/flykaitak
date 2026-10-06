"""Road network for 1998 from the Transport Department's Intelligent Road Network -> ../assets/roads.json, ../assets/streets.json

Source: "Road Network Data of Hong Kong" (Transport Department, packaged as a File Geodatabase by Esri China (HK)),
https://hub.arcgis.com/datasets/188a2dfc78bd44d19fa99edfe87b20e7 . Downloaded to tools/cache (not committed).
Needs: pip install pyogrio pyproj shapely

The dataset is today's network, so roads that did not exist in 1998 are taken out:
  - roads opened after 1998, by name (Route 8 Tsing Sha Highway, Hung Hom Bypass, Central-Wan Chai Bypass, Cyberport, ...)
  - everything on the Kai Tak airport site, the Central Reclamation Phase III waterfront and the West Kowloon Cultural District
  - streets the dataset first recorded after 2009 (new estates and developments), except old roads that were only renamed
Tunnels are left out (traffic would drive over the hills). Segments are chained through junctions into long roads.
"""
import os,sys,math,json,zipfile,urllib.request,collections
import numpy as np
sys.path.insert(0,os.path.dirname(__file__));os.chdir(os.path.dirname(os.path.abspath(__file__)))
from geo import to_xz,BLD
URL='https://www.arcgis.com/sharing/rest/content/items/188a2dfc78bd44d19fa99edfe87b20e7/data'
GDB='cache/RoadNetwork_HK80.gdb'
STREET_BOX=(-2600,-2000,900,600)   # Kowloon City / San Po Kong / Kowloon Tsai streets under the approach (x0,z0,x1,z1)

# main roads (the Lands Department basemap's major roads)
MAIN={"ABERDEEN TUNNEL","ALBANY ROAD","ARGYLE STREET","AUSTIN ROAD WEST","BELCHER'S STREET","BONHAM ROAD","BOUNDARY STREET","BUTTERFLY VALLEY ROAD",
 "CAINE ROAD","CANAL ROAD FLYOVER","CANAL ROAD WEST","CANTON ROAD","CASTLE PEAK ROAD","CASTLE PEAK ROAD - KWAI CHUNG","CASTLE PEAK ROAD - TSUEN WAN",
 "CAUSEWAY ROAD","CHAI WAN ROAD","CHATER ROAD","CHATHAM ROAD NORTH","CHATHAM ROAD SOUTH","CHE KUNG MIU ROAD","CHEUNG PEI SHAN ROAD","CHEUNG SHA WAN ROAD",
 "CHEUNG TSING HIGHWAY","CHEUNG WING ROAD","CHING CHEUNG ROAD","CHING HONG ROAD","CHOI HUNG ROAD","CLEAR WATER BAY ROAD","CONNAUGHT ROAD CENTRAL",
 "CONNAUGHT ROAD WEST","CONTAINER PORT ROAD","CONTAINER PORT ROAD SOUTH","CORNWALL STREET","DES VOEUX ROAD CENTRAL","DES VOEUX ROAD WEST","ELECTRIC ROAD",
 "FAT KWONG STREET","FERRY STREET","FUNG SHUE WO ROAD","GASCOIGNE ROAD","GILLIES AVENUE SOUTH","GLOUCESTER ROAD","HARCOURT ROAD","HENNESSY ROAD","HILL ROAD",
 "HIRAM'S HIGHWAY","HOI BUN ROAD","HOI WANG ROAD","HOI YUEN ROAD","HONG CHONG ROAD","HUNG MUI KUK ROAD","ISLAND EASTERN CORRIDOR","JAVA ROAD","JOHNSTON ROAD",
 "JORDAN ROAD","JUNCTION ROAD","KAI CHEUNG ROAD","KAI FUK ROAD","KAI FUK ROAD FLYOVER","KING'S ROAD","KORNHILL ROAD","KOWLOON CITY ROAD","KOWLOON PARK DRIVE",
 "KWAI CHUNG ROAD","KWAI TSING ROAD","KWUN TONG BY-PASS","KWUN TONG ROAD","LAI CHI KOK ROAD","LANTAU LINK","LEI YUE MUN ROAD","LEIGHTON ROAD","LIN CHEUNG ROAD",
 "LION ROCK TUNNEL ROAD","LUNG CHEUNG ROAD","MA TAU CHUNG ROAD","MA TAU WAI ROAD","MA WAN ROAD","MAGAZINE GAP ROAD","NAM CHEONG STREET","NATHAN ROAD",
 "NEW CLEAR WATER BAY ROAD","NEW HIRAM'S HIGHWAY","NORTH LANTAU HIGHWAY","NORTH WEST TSING YI INTERCHANGE","PARK ROAD","PEAK ROAD","PERCIVAL STREET","PO HONG ROAD",
 "POK FU LAM ROAD","PRINCE EDWARD ROAD EAST","PRINCE EDWARD ROAD WEST","PRINCESS MARGARET ROAD","PUI CHING ROAD","QUEEN'S ROAD CENTRAL","QUEEN'S ROAD EAST",
 "QUEEN'S ROAD WEST","QUEENSWAY","REPULSE BAY ROAD","ROBINSON ROAD","SAI YEE STREET","SALISBURY ROAD","SHA LEK HIGHWAY","SHA TIN ROAD","SHA TIN WAI ROAD",
 "SHANGHAI STREET","SHAU KEI WAN ROAD","SHEK PAI WAN ROAD","SHING MUN TUNNEL ROAD","SHING SAI ROAD","SING WOO ROAD","SIU SAI WAN ROAD","STUBBS ROAD",
 "SUNG WONG TOI ROAD","TAI CHUNG KIU ROAD","TAI CHUNG ROAD","TAI HANG ROAD","TAI KOK TSUI ROAD","TAI PO ROAD","TAI PO ROAD - PIPER'S HILL",
 "TAI PO ROAD - SHA TIN HEIGHTS","TAI TAM ROAD","TATE'S CAIRN HIGHWAY","TEXACO ROAD","TEXACO ROAD NORTH","TO KWA WAN ROAD","TONG MI ROAD","TRADEMART DRIVE",
 "TSEUNG KWAN O ROAD","TSEUNG KWAN O TUNNEL ROAD","TSING KING ROAD","TSING KWAI HIGHWAY","TSING LONG HIGHWAY","TSING TSUEN ROAD","TSING YI HEUNG SZE WUI ROAD",
 "TSING YI ROAD","TSING YI ROAD WEST","TSUEN WAN ROAD","TUEN MUN ROAD","TUNG CHAU STREET","TUNG HEI ROAD","UPPER ALBERT ROAD","VICTORIA PARK ROAD","WAI FAT ROAD",
 "WAI YIP STREET","WAN CHAI INTERCHANGE","WANG CHIN STREET","WATERLOO ROAD","WEST KOWLOON CORRIDOR","WEST KOWLOON CORRIDOR WEST","WEST KOWLOON HIGHWAY",
 "WESTERN HARBOUR CROSSING","WING TAI ROAD","WING TAK ROAD","WO YI HOP ROAD","WONG CHUK HANG ROAD","WONG NAI CHUNG GAP FLYOVER","WONG NAI CHUNG GAP ROAD",
 "WONG NAI CHUNG ROAD","YAU MA TEI INTERCHANGE","YEE WO STREET","YEN CHOW STREET"}
# opened after 1998
AFTER_1998={"TSING SHA HIGHWAY",            # Route 8, 2008-09 (with Stonecutters Bridge, Eagle's Nest and Sha Tin Heights tunnels)
 "TSING YI NORTH COASTAL ROAD",              # 1999
 "HUNG HOM BYPASS",                          # 1999
 "PENNY'S BAY HIGHWAY",                      # 2005
 "CYBERPORT ROAD",                           # 2002-04
 "CENTRAL-WAN CHAI BYPASS TUNNEL","ISLAND EASTERN CORRIDOR LINK",  # 2019
 "TIM MEI AVENUE","LEGISLATIVE COUNCIL ROAD","LUNG HOP STREET","YIU SING STREET","LUNG WO ROAD",  # Tamar / Central Reclamation III
 "MUSEUM DRIVE","NGA CHEUNG ROAD","HOI PO ROAD","WUI MAN ROAD",   # West Kowloon Cultural District
 "SHING KAI ROAD","SHING FUNG ROAD","SHING CHEONG ROAD","CONCORDE ROAD","KAI SAN ROAD","TSAT PO STREET","MUK TAI STREET","MUK ON STREET","MUK CHUI STREET",
 "MUK HUNG STREET","MUK YUEN STREET","MUK NING STREET","MUK LONG STREET","MUK CHUN STREET","CHOI WING ROAD","CHOI WING LANE","CHOI HING ROAD",  # Kai Tak Development
 "ON SAU ROAD","ON YAN STREET","ON CHUI STREET","ON TAI ROAD",   # Anderson Road quarry development
}
# first recorded after 2009 but much older (renamed or re-surveyed)
OLD_NAMES={"PRINCESS MARGARET HOSPITAL ROAD","TREGUNTER PATH","SCENIC VILLA DRIVE","CLAYMORE AVENUE","TAK CHEONG STREET","WILMER STREET","AMOY STREET",
 "PING TIN STREET","MISEREOR ROAD","HANG CHEUNG STREET","TSOI TAK STREET"}
WEST_KOWLOON_KEEP={"WEST KOWLOON HIGHWAY","WESTERN HARBOUR CROSSING","LIN CHEUNG ROAD","JORDAN ROAD","CANTON ROAD","YAU MA TEI INTERCHANGE"}

D2R=math.pi/180;U=(math.sin(134*D2R),-math.cos(134*D2R));R=(math.cos(134*D2R),math.sin(134*D2R))
def gone(x,z):
    """Places whose roads were built after 1998 (mirrors skipFootprint / WATER1998 in index.html)."""
    s=x*U[0]+z*U[1];l=x*R[0]+z*R[1]
    if -170<s<3390+200 and -420<l<200:return True               # Kai Tak runway and its taxiway strip
    if -170<s<1150 and -1300<l<=-420:return True                # Kai Tak terminal, aprons and hangars (up to Kai Fuk Road)
    if -3460<x<-2330 and 4240<z<4650:return True                # Central Reclamation Phase III: still harbour
    if -7300<x<-6450 and 200<z<650:return True                  # Stonecutters Bridge landing (2009)
    return False
def in_wkcd(x,z):return -4400<x<-2750 and 500<z<3150             # West Kowloon reclamation: empty in 1998

def load():
    if not os.path.exists(GDB):
        os.makedirs('cache',exist_ok=True);z='cache/RoadNetwork_HK80.gdb.zip'
        if not os.path.exists(z):print('downloading road network ...',flush=True);urllib.request.urlretrieve(URL,z)
        zipfile.ZipFile(z).extractall('cache')
    import pyogrio,shapely,warnings
    from pyproj import Transformer
    warnings.filterwarnings('ignore')
    meta,_,geom,f=pyogrio.raw.read(GDB,layer='CENTERLINE_JOIN',columns=['STREET_ENAME','ELEVATION','ROUTE_NUM','CRE_DATE'])
    T=Transformer.from_crs(2326,4326,always_xy=True);out=[]
    for i,G in enumerate(shapely.from_wkb(geom)):
        for ln in (G.geoms if G.geom_type=='MultiLineString' else [G]):
            c=np.asarray(ln.coords)[:,:2];lon,lat=T.transform(c[:,0],c[:,1]);x,z=to_xz(lat,lon)
            n=f[0][i];n='' if n in(None,'-99') else n.strip()
            out.append(dict(p=np.stack([x,z],1),name=n,elev=int(f[1][i]),route=f[2][i] if f[2][i]==f[2][i] else None,year=int(str(f[3][i])[:4])))
    return out

def chain(segs,max_turn=55):
    """Join segments end to end through junctions, carrying on along the straightest (same-named first) way."""
    key=lambda q:(round(q[0]),round(q[1]))
    ends=collections.defaultdict(list)
    for k,s in enumerate(segs):ends[key(s['p'][0])].append((k,0));ends[key(s['p'][-1])].append((k,1))
    used=[False]*len(segs);lines=[]
    def hd(a,b):return math.atan2(b[1]-a[1],b[0]-a[0])
    def walk(pts,name):
        while True:
            e=key(pts[-1]);h=hd(pts[-2],pts[-1]);best=None
            for k,side in ends[e]:
                if used[k]:continue
                q=segs[k]['p'] if side==0 else segs[k]['p'][::-1]
                t=abs((hd(q[0],q[1])-h+math.pi)%(2*math.pi)-math.pi)/D2R
                if t>max_turn:continue
                sc=t-(30 if segs[k]['name']==name and name else 0)
                if best is None or sc<best[0]:best=(sc,k,q)
            if not best:return pts
            used[best[1]]=True;pts=np.vstack([pts,best[2][1:]])
    order=sorted(range(len(segs)),key=lambda k:min(len(ends[key(segs[k]['p'][0])]),len(ends[key(segs[k]['p'][-1])])))   # dead ends first
    for k in order:
        if used[k]:continue
        used[k]=True;s=segs[k]
        fw=walk(s['p'],s['name']);bw=walk(s['p'][::-1],s['name'])
        lines.append(np.vstack([bw[::-1],fw[len(s['p']):]]))
    return lines

def rdp(P,eps):
    if len(P)<3:return P
    a=P[0];b=P[-1];d=b-a;L=math.hypot(*d) or 1
    ds=np.abs(d[0]*(a[1]-P[1:-1,1])-d[1]*(a[0]-P[1:-1,0]))/L;i=int(np.argmax(ds))+1
    if ds[i-1]>eps:return np.vstack([rdp(P[:i+1],eps)[:-1],rdp(P[i:],eps)])
    return np.vstack([a,b])
def length(P):return float(np.hypot(*np.diff(P,axis=0).T).sum())
def inside(P,B):m=P.mean(0);return B[0]<m[0]<B[2] and B[1]<m[1]<B[3]

segs=load()
first=collections.defaultdict(lambda:9999)
for s in segs:
    if s['name']:first[s['name']]=min(first[s['name']],s['year'])
drop=collections.Counter();main=[];street=[]
for s in segs:
    p=s['p'];n=s['name'];m=p.mean(0)
    if s['elev']<0:drop['tunnel']+=1;continue
    if n in AFTER_1998:drop['after 1998']+=1;continue
    if not n and s['route']==8 and m[0]>-10500:drop['after 1998']+=1;continue      # Route 8 ramps east of Tsing Yi (Tsing Sha Highway)
    if gone(*m):drop['Kai Tak / Central III']+=1;continue
    if in_wkcd(*m) and n not in WEST_KOWLOON_KEEP and not s['route']:drop['West Kowloon']+=1;continue
    if n and first[n]>=2010 and n not in OLD_NAMES:drop['new street']+=1;continue
    if n in MAIN or (not n and s['route']):
        if inside(p,BLD):main.append(s)
    elif inside(p,STREET_BOX):street.append(s)
print('dropped',dict(drop))
if os.environ.get('ROADS_DEBUG'):import pickle;pickle.dump((main,street),open(os.environ['ROADS_DEBUG'],'wb'))
def emit(sel,minL,eps,out):
    L=[rdp(P,eps) for P in chain(sel) if length(P)>=minL]
    J=[[[round(float(x)),round(float(z))] for x,z in P] for P in L]
    json.dump(J,open(out,'w'),separators=(',',':'))
    print(os.path.basename(out),len(J),'lines',round(sum(length(P) for P in L)/1000),'km',os.path.getsize(out)//1024,'KB')
emit(main,250,3,'../assets/roads.json')
emit(street,60,1.5,'../assets/streets.json')
