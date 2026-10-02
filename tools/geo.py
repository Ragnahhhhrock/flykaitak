import math
LAT0,LON0=22.32558,114.19262   # Kai Tak runway 13 threshold (fitted to the Lands Department basemap)
KLAT,KLON=110735.0,103022.0     # metres per degree at 22.33N
OUTER=(-28000,-17000,14000,14000)  # x0,z0,x1,z1 metres (x east, z south)
INNER=(-8000,-3800,4800,9000)
BLD=(-17000,-6000,6400,8400)
def to_ll(x,z): return LAT0-z/KLAT, LON0+x/KLON
def to_xz(lat,lon): return (lon-LON0)*KLON, -(lat-LAT0)*KLAT
def bbox_ll(R):
    x0,z0,x1,z1=R;la0,lo0=to_ll(x0,z1);la1,lo1=to_ll(x1,z0);return la0-.002,lo0-.002,la1+.002,lo1+.002
def merc(lat,lon,z):
    import numpy as np
    n=2**z;x=(lon+180)/360*n;y=(1-np.log(np.tan(np.radians(lat))+1/np.cos(np.radians(lat)))/np.pi)/2*n;return x,y
