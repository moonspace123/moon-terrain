from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import build_revision as b

ROOT, PROJECT, ASSETS, DELIVERY = b.ROOT, b.PROJECT, b.ASSETS, b.DELIVERY
S = b.old.smooth
NOISE = b.old.noise2
DESIGNS = [
 dict(id='barrier',name='巨石屏障',source='plain',origin=[0,-80],description='沿巨石一侧看见目标，靠近正面后被遮挡，再绕到另一侧恢复视线。',target=[0,8],path=[[-8,-9],[0,-8],[8,-7],[8,2],[5,6]]),
 dict(id='trench',name='连续沟槽',source='rille',origin=[1000,0],description='沿缓坡进入沟底，再从另一侧缓坡走出；固定红球经历可见、遮挡和重现。',target=[17,8],path=[[-17,-31],[-11,-25],[float(b.channel_center(-19)),-19],[float(b.channel_center(-5)),-5],[float(b.channel_center(7)),7],[float(b.channel_center(15))+9,19],[17,25],[16,13]]),
 dict(id='stairs_up',name='上行阶地',source='plain',origin=[80,-160],description='多级不等高平台沿坡面展开；经缓坡连接上行，平台边缘改变目标视线。',target=[18,18],path=[[21,-25],[3,-18],[15,-9],[1,0],[15,9],[3,18],[17,24]]),
 dict(id='pit',name='局部凹坑',source='depression',origin=[0,0],description='进入小范围凹陷后，坑缘挡住目标；从较缓的一侧离开后重新看见。',target=[11,3],path=[[15,-8],[5,-8],[0,-3],[1,3],[6,8],[12,9]]),
 dict(id='basin',name='宽阔凹地',source='rim',origin=[-600,-300],description='宽阔低地与长缓坡连接；在盆底目标被盆缘遮住，回到坡面后恢复视线。',target=[25,10],path=[[27,-16],[15,-12],[4,-3],[0,7],[12,13],[23,20]]),
 dict(id='waves',name='连续丘脊',source='ejecta',origin=[96,-96],description='宽缓丘脊的高度、间距和走向各有变化；沿途观察固定目标的消失与重现。',target=[3,32],path=[[-3,-22],[-2,-10],[2,1],[-2,14],[2,25]]),
 dict(id='perlin',name='平滑随机起伏',source='plain',origin=[160,0],description='宽缓丘包、洼地与鞍部连成一片；沿平缓地带移动，观察地势造成的遮挡。',target=[7,22],path=[[-9,-22],[-3,-12],[0,-2],[7,8],[10,17]]),
 dict(id='perlin_rough',name='岩块与强起伏',source='ejecta',origin=[-96,-96],description='大地势保持连贯，较强起伏与岩块分区分布；经过坡折后重新观察目标。',target=[9,23],path=[[-10,-23],[-6,-12],[0,0],[8,10],[13,18]]),
]


def addition(kind,x,z):
    if kind=='barrier':
        return .13*NOISE(x*.035,z*.035,2)
    if kind=='trench':return b.trench_shape(x,z)
    if kind=='stairs_up':
        out=np.zeros_like(x)
        for i,(q,rise,width) in enumerate([(-18,1.30,3.0),(-1,1.65,3.5),(18,1.45,3.25)]):
            contour=q+2.8*np.sin(x*.035+i*.9)+.07*x
            side=1-S(30+4*np.sin(z*.025),76,np.abs(x))
            out+=rise*S(contour-width,contour+width,z)*side
        return out
    if kind in ('pit','basin'):
        theta=np.arctan2(z,x)
        r=np.hypot(x,z)/(1+.10*np.sin(3*theta+.4)+.05*np.cos(2*theta-1))
        floor,outer,depth=(2.4,9.0,2.05) if kind=='pit' else (10.0,25.0,3.2)
        width=outer-floor
        # Broader east-side saddle joins the floor to surrounding ground.
        saddle=np.exp(-((theta-.8)/.5)**2)
        cross=1-S(floor,outer+width*.45*saddle,r)
        rim=.10*np.exp(-((r-outer)/2.7)**2)*(1-.6*saddle)
        return -depth*cross+rim
    if kind=='waves':
        out=np.zeros_like(x)
        for i,(q,height,width) in enumerate([(-24,2.2,7.5),(2,2.6,10.0),(32,1.9,12.0)]):
            contour=q+3.4*np.sin(x*.026+i*.8)+.035*x
            amplitude=height*(.85+.15*np.cos(x*.022+i))
            out+=amplitude*np.exp(-((z-contour)/width)**2)*(1-S(65,155,np.abs(x)))
        return out
    if kind=='perlin':
        return 1.7*NOISE(x*.045+2,z*.045-1,21)+.18*NOISE(x*.09,z*.09,26)
    broad=2.0*NOISE(x*.043+2,z*.043-1,21)
    zone=.3+.7*S(-.35,.45,NOISE(x*.018,z*.018,80))
    return broad+.55*NOISE(x*.105,z*.105,25)*zone


def classify(cameras,target,sample,primary=None):
    camera=np.asarray(cameras)
    f=target-camera;f/=np.linalg.norm(f,axis=1,keepdims=True)
    right=np.cross(f,np.array([0,1,0]));right/=np.linalg.norm(right,axis=1,keepdims=True)
    up=np.cross(right,f)
    t=np.linspace(.008,.995,210)[None,:,None]
    margins=[]
    for iz in (-1,0,1):
        for ix in (-1,0,1):
            end=target+right*(ix*.26)+up*(iz*.26)
            line=camera[:,None,:]+(end-camera)[:,None,:]*t
            clearance=line[:,:,1]-sample(line[:,:,[2,0]])
            margin=clearance.min(axis=1)
            if primary is not None:
                center,axes=primary
                normalized=(line-center)/axes
                hit=(np.sum(normalized**2,axis=-1).min(axis=1)<.90)
                margin=np.where(hit,np.minimum(margin,-.25),margin)
            margins.append(margin)
    margins=np.array(margins)
    return np.where(margins.max(axis=0)<-.06,'H',np.where(margins.min(axis=0)>.012,'V','P'))


def sequence(states):
    groups=b.old.runs(states)
    stable=[g for g in groups if g['state']!='P' and g['end']-g['start']>=4]
    seq=''.join(g['state'] for g in stable)
    for i in range(len(stable)-2):
        if ''.join(g['state'] for g in stable[i:i+3])=='VHV':
            return seq,[(g['start']+g['end'])//2 for g in stable[i:i+3]]
    return seq,[]


def route_with_visibility(design,sample,primary):
    points=b.old.densify(design['path'],spacing=.25)
    camera=np.column_stack([points[:,0],sample(points[:,[1,0]])+.65,points[:,1]])
    tx,tz=design['target'];targets=[(tx,tz),(tx-4,tz),(tx+4,tz),(tx,tz-5),(tx,tz+5),(tx-8,tz-4),(tx+6,tz-5)]
    for px,pz in targets:
        target=np.array([px,float(sample([[pz,px]])[0])+.29,pz])
        states=classify(camera,target,sample,primary)
        seq,witness=sequence(states)
        if witness:
            distance=np.linalg.norm(camera[witness[0]]-target)
            if distance<56:return camera,target,states,seq,witness,'authored_camera_route'
    # Select a demonstration path after fixing the terrain. Geometry is never
    # changed in response to visibility search. This is not autonomous navigation.
    gx,gz=np.meshgrid(np.arange(-28,29,4),np.arange(-28,29,4))
    candidates=np.column_stack([gx.ravel(),sample(np.column_stack([gz.ravel(),gx.ravel()]))+.65,gz.ravel()])
    for px,pz in targets:
        target=np.array([px,float(sample([[pz,px]])[0])+.29,pz])
        states=classify(candidates,target,sample,primary)
        distance=np.linalg.norm(candidates-target,axis=1)
        v=np.flatnonzero((states=='V')&(distance>10)&(distance<42))
        hh=np.flatnonzero((states=='H')&(distance>5)&(distance<35))
        if len(v)<2 or not len(hh):continue
        hh=sorted(hh,key=lambda i:np.linalg.norm(candidates[i,[0,2]]))
        for hidden in hh[:12]:
            visible=sorted(v,key=lambda i:np.linalg.norm(candidates[i,[0,2]]-np.array(design['path'][0])))[:8]
            recovered=sorted(v,key=lambda i:distance[i])[:12]
            for start in visible:
                for finish in recovered:
                    if np.linalg.norm(candidates[start]-candidates[finish])<7:continue
                    pp=b.old.densify(candidates[[start,hidden,finish]][:,[0,2]],spacing=.25)
                    cc=np.column_stack([pp[:,0],sample(pp[:,[1,0]])+.65,pp[:,1]])
                    grade=np.degrees(np.arctan2(abs(np.diff(cc[:,1])),np.linalg.norm(np.diff(pp,axis=0),axis=1)))
                    if np.max(grade)>27:continue
                    ss=classify(cc,target,sample,primary);seq,w=sequence(ss)
                    if w:return cc,target,ss,seq,w,'terrain_fixed_then_selected_scripted_route'
    raise RuntimeError(f'No suitable nominal demonstration route for {design["id"]}')


def axis_for(a,bound):
    values=np.concatenate([np.arange(0,48,.25),np.arange(48,96,.5),np.arange(96,256,2),np.arange(256,769,8)])
    full=np.concatenate([-values[:0:-1],values]);return full[(full>=a)&(full<=bound)]


def build():
    b.stage();scenes=[];reports=[]
    if (ASSETS/'revision_config.json').exists():
        shutil.copy2(ASSETS/'revision_config.json',b.WORK/'previous_revision_config.json')
    axis=np.linspace(-96,96,769);x,z=np.meshgrid(axis,axis)
    for index,d in enumerate(DESIGNS):
        kind=d['id'];origin=d['origin'];base,source,spacing=b.source_surface(d['source'],origin)
        def evaluate(xx,zz):return base(xx,zz)+addition(kind,xx,zz)+.018*NOISE(xx*.29,zz*.29,19)
        h=evaluate(x,z);sample=RegularGridInterpolator((axis,axis),h)
        vv,_,_,_=b.old.loadmesh(source)
        ax=axis_for(max(-768.,float(vv[:,0].min())-origin[0]+8),min(768.,float(vv[:,0].max())-origin[0]-8))
        az=axis_for(max(-768.,float(vv[:,2].min())-origin[1]+8),min(768.,float(vv[:,2].max())-origin[1]-8))
        mx,mz=np.meshgrid(ax,az);mh=evaluate(mx,mz);dz,dx=np.gradient(mh,az,ax)
        normal=np.stack([-dx,np.ones_like(mh),-dz],-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        j,i=np.indices((len(az)-1,len(ax)-1));a=j*len(ax)+i
        tri=np.stack([a,a+len(ax),a+1,a+1,a+len(ax),a+len(ax)+1],-1).reshape(-1,3)
        mesh=ASSETS/'Meshes'/f'{kind}_continuous.bytes'
        b.old.savemesh(mesh,np.stack([mx,mh,mz],-1).reshape(-1,3),normal.reshape(-1,3),np.stack([mx/3.1,mz/3.1],-1).reshape(-1,2),tri)
        height=ASSETS/'Data'/f'{kind}_height.bytes';height.write_bytes(h.astype('<f4').tobytes())
        primary=None;rocks=[]
        if kind=='barrier':
            rock=b.old.loadmesh(PROJECT/'Assets/LunarPilot/Meshes/rock_1.bytes')[0]
            scale=4.5;stretch=np.array([1.15,.95,1.0]);size=np.ptp(rock,axis=0)*scale*stretch;burial=.22
            ground=float(sample([[0,0]])[0]);center=np.array([0,ground+size[1]*(.5-burial),0]);axes=size*.46
            primary=(center,axes)
            rocks.append(dict(type=1,x=0,z=0,ground=ground,scale=scale,stretch=stretch.tolist(),yaw=29.,burial=burial,primary=True))
        camera,target,states,seq,witness,method=route_with_visibility(d,sample,primary)
        route_xz=camera[:,[0,2]];rng=np.random.default_rng(20261108+index)
        for _ in range(620 if kind=='perlin_rough' else 420):
            rx,rz=rng.uniform(-75,75,2)
            if np.min(np.linalg.norm(route_xz-[rx,rz],axis=1))<1.2:continue
            if np.linalg.norm(target[[0,2]]-[rx,rz])<1.2:continue
            density=.28+.52*S(-.3,.4,NOISE(np.array(rx*.035),np.array(rz*.035),63))
            if rng.random()>density:continue
            scale=float(rng.uniform(.10,.48))
            if kind=='perlin_rough':scale*=float(rng.uniform(1.3,2.6))
            elif rng.random()<.06:scale*=2
            rocks.append(dict(type=int(rng.integers(0,9)),x=float(rx),z=float(rz),ground=float(sample([[rz,rx]])[0]),scale=scale,stretch=rng.uniform(.8,1.25,3).tolist(),yaw=float(rng.uniform(0,360)),burial=float(rng.uniform(.2,.38)),primary=False))
        source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        scene=dict(id=kind,name=d['name'],source=d['source'],description=d['description'],sourceNative=str(source.relative_to(PROJECT)).replace('\\','/'),sourceSha256=source_sha,sourceOrigin=origin,nativeGridSpacingM=spacing,mesh=f'Meshes/{mesh.name}',heightData=f'Data/{height.name}',extent=96.,gridSize=769,eyeHeight=.65,targetRadius=.26,targetPosition=target.tolist(),route=[dict(position=q.tolist()) for q in camera],rocks=rocks,witnessIndices=witness,provenance=f'Existing DEM-derived {d["source"]} asset, source-local crop origin {origin}m. Source macro elevations retained without scaling. Additive synthetic {kind} design and procedural surface detail. Fine render mesh is interpolation, not measured DEM resolution.')
        dz,dx=np.gradient(h,axis,axis);slope=np.degrees(np.arctan(np.hypot(dx,dz)));area=(abs(x)<32)&(abs(z)<38)
        grade=np.degrees(np.arctan2(abs(np.diff(camera[:,1])),np.linalg.norm(np.diff(camera[:,[0,2]],axis=0),axis=1)))
        report=dict(id=kind,status='NOMINAL_GEOMETRY_PASS',terrainSurfaceCount=1,vertices=len(ax)*len(az),triangles=len(tri),renderSpacingNearM=.25,sourceGridSpacingM=spacing,sourceOrigin=origin,sourceSha256=source_sha,sourceElevationsScaled=False,separateBackgroundSurface=False,nominalSequence=seq,witnessIndices=witness,routeChoice=method,routeGradeP95MaxDeg=np.percentile(grade,[95,100]).tolist(),areaSlopeMedianP95MaxDeg=np.percentile(slope[area],[50,95,100]).tolist(),rocks=len(rocks),robotWalkingTested=False,unityRendered=False)
        scenes.append(scene);reports.append(report)
        np.savez_compressed(b.WORK/f'{kind}_design.npz',axis=axis,height=h,slope=slope,route=camera,target=target,witnesses=witness)
        print(json.dumps(report,ensure_ascii=True),flush=True)
    (ASSETS/'revision_config.json').write_text(json.dumps(dict(version='eight-continuous-scenes-2',scenes=scenes),ensure_ascii=False),encoding='utf-8')
    (DELIVERY/'geometry_verification.json').write_text(json.dumps(dict(status='EIGHT_SCENE_GEOMETRY_PASS',scenes=reports),ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ('TerrainRevision.cs','TerrainRevisionBuilder.cs','TerrainRevisionAudit.cs','TerrainRevisionSuite.cs','TerrainRevisionPlayerSmoke.cs'):
        src=Path(__file__).parent/name
        if src.exists():shutil.copy2(src,ASSETS/('Editor' if name in ('TerrainRevisionBuilder.cs','TerrainRevisionAudit.cs','TerrainRevisionSuite.cs') else 'Scripts')/name)


if __name__=='__main__':build()
