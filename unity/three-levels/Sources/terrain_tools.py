import struct
import numpy as np


def loadmesh(path):
    b=path.read_bytes();n,ni=struct.unpack('<ii',b[:8]);offset=8
    v=np.frombuffer(b,'<f4',n*3,offset).reshape(-1,3).copy();offset+=n*12
    normals=np.frombuffer(b,'<f4',n*3,offset).reshape(-1,3).copy();offset+=n*12
    uv=np.frombuffer(b,'<f4',n*2,offset).reshape(-1,2).copy();offset+=n*8
    tri=np.frombuffer(b,'<i4',ni,offset).reshape(-1,3).copy()
    return v,normals,uv,tri


def savemesh(path,v,normals,uv,tri):
    with path.open('wb') as f:
        f.write(struct.pack('<ii',len(v),tri.size))
        for a,dtype in [(v,'<f4'),(normals,'<f4'),(uv,'<f4'),(tri,'<i4')]:f.write(np.asarray(a,dtype=dtype).tobytes())


def noise2(x,z,seed=1):
    ix=np.floor(x).astype(np.int64);iz=np.floor(z).astype(np.int64);fx=x-ix;fz=z-iz
    def grad(i,j,dx,dz):
        h=(i*374761393+j*668265263+seed*1442695041)&0xffffffff
        h=((h^(h>>13))*1274126177)&0xffffffff
        a=(h&65535)*(2*np.pi/65536)
        return np.cos(a)*dx+np.sin(a)*dz
    u=fx**3*(fx*(fx*6-15)+10);w=fz**3*(fz*(fz*6-15)+10)
    a=grad(ix,iz,fx,fz)*(1-u)+grad(ix+1,iz,fx-1,fz)*u
    b=grad(ix,iz+1,fx,fz-1)*(1-u)+grad(ix+1,iz+1,fx-1,fz-1)*u
    return (a*(1-w)+b*w)*1.7


def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)


def densify(points,spacing=.24):
    out=[]
    for a,b in zip(points[:-1],points[1:]):
        a=np.array(a);b=np.array(b);n=max(2,int(np.linalg.norm(b-a)/spacing)+1)
        out.extend((a+(b-a)*t).tolist() for t in np.linspace(0,1,n,endpoint=False))
    out.append(points[-1]);return np.array(out)


def runs(states):
    result=[]
    for i,state in enumerate(states):
        if not result or result[-1]['state']!=state:result.append(dict(state=state,start=i,end=i))
        else:result[-1]['end']=i
    return result
