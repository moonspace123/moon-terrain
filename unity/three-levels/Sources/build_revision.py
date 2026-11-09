from pathlib import Path
import concurrent.futures
import hashlib
import json
import shutil
import struct
import sys

import numpy as np
from scipy.interpolate import RectBivariateSpline, RegularGridInterpolator
import terrain_tools as old

ROOT = Path(__file__).resolve().parents[1]
OLD_ROOT=Path(r'C:\Users\lyz\Documents\Codex\2026-11-03\hai\outputs')
OLD=next((p for p in OLD_ROOT.iterdir() if p.is_dir()),None) if OLD_ROOT.exists() else None
PORTABLE=(ROOT/'UnityProject/Assets').is_dir()
DELIVERY = ROOT if PORTABLE else ROOT / 'outputs' / 'Lunar_Terrain_Revision'
PROJECT = DELIVERY / 'UnityProject'
ASSETS = PROJECT / 'Assets' / 'TerrainRevision'
WORK=ROOT/'Sources/GeneratedChecks' if PORTABLE else ROOT/'work'
WORK.mkdir(parents=True,exist_ok=True)


def stage():
    if PORTABLE:
        return
    if OLD is None:
        raise FileNotFoundError('A complete UnityProject/Assets directory is required beside Sources.')
    pairs = []
    for name in ('Assets', 'Packages', 'ProjectSettings'):
        src = OLD / 'UnityProject' / name
        for p in src.rglob('*'):
            if p.is_file():
                target = PROJECT / name / p.relative_to(src)
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    pairs.append((p, target))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda pair: shutil.copy2(*pair), pairs))
    for name in ('Data', 'Meshes', 'Materials', 'Scripts', 'Editor'):
        (ASSETS / name).mkdir(parents=True, exist_ok=True)
    print(f'STAGED {len(pairs)} files', flush=True)


def source_surface(source, origin=(0., 0.)):
    path = PROJECT / 'Assets/LunarPilot/Meshes' / f'{source}_native.bytes'
    v, _, _, _ = old.loadmesh(path)
    xs, zs = np.unique(v[:, 0]), np.unique(v[:, 2])
    y = v[np.lexsort((v[:, 0], v[:, 2])), 1].reshape(len(zs), len(xs))
    # Cubic resampling of the existing coarse source, never additional measured detail.
    spline = RectBivariateSpline(zs, xs, y, kx=3, ky=3, s=0)
    offset = float(spline.ev(origin[1], origin[0]))
    def evaluate(x, z):
        return spline.ev(z + origin[1], x + origin[0]) - offset
    return evaluate, path, float(np.median(np.diff(xs)))


def channel_center(z):
    return 2.4 * np.sin(z * .027 + .6) + 1.0 * np.sin(z * .073 - .4)


def trench_shape(x, z):
    lateral = x - channel_center(z)
    floor = 2.0 + .30 * np.sin(z * .048 + .4)
    # Unequal banks and two broad saddles, not a uniform narrow Gaussian ditch.
    west = 8.5 + .9 * np.sin(z * .036 - .5) + 5.5 * np.exp(-((z + 20) / 11) ** 2)
    east = 6.2 + .7 * np.sin(z * .043 + .8) + 7.5 * np.exp(-((z - 15) / 12) ** 2)
    width = np.where(lateral < 0, west, east)
    cross = 1 - old.smooth(floor, floor + width, np.abs(lateral))
    depth = 2.25 + .25 * np.sin(z * .032 + .5)
    ends = 1 - old.smooth(68, 94, np.abs(z))
    return -depth * cross * ends


def terrain(x, z, base):
    return base(x, z) + trench_shape(x, z) + .018 * old.noise2(x * .29, z * .29, 19)


def nominal_visibility(camera, target, radius, sample):
    right = np.cross(target - camera, np.array([0., 1., 0.]))
    right /= np.linalg.norm(right)
    forward = (target - camera) / np.linalg.norm(target - camera)
    up = np.cross(right, forward)
    offsets = [right * i * radius + up * j * radius for i in (-1, 0, 1) for j in (-1, 0, 1)]
    margins = []
    t = np.linspace(.008, .995, 320)
    for offset in offsets:
        end = target + offset
        line = camera + (end - camera) * t[:, None]
        margins.append(float(np.min(line[:, 1] - sample(line[:, [2, 0]]))))
    return 'H' if max(margins) < -.06 else 'V' if min(margins) > .012 else 'P'


def build():
    stage()
    extent, n = 96., 769
    axis = np.linspace(-extent, extent, n)
    x, z = np.meshgrid(axis, axis)
    base, source, native_spacing = source_surface('rille', (1000., 0.))
    h = terrain(x, z, base)
    dz, dx = np.gradient(h, axis, axis)
    # A single nonuniform grid extends to distant context. Adjacent cells share
    # their vertices; there is no second overlapping background surface.
    positive = np.concatenate([np.arange(0,48,.25), np.arange(48,96,.5), np.arange(96,256,2), np.arange(256,769,8)])
    mesh_axis = np.concatenate([-positive[:0:-1], positive])
    mx, mz = np.meshgrid(mesh_axis, mesh_axis)
    mh = terrain(mx, mz, base)
    mdz, mdx = np.gradient(mh, mesh_axis, mesh_axis)
    normals = np.stack([-mdx, np.ones_like(mh), -mdz], -1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    mesh_n = len(mesh_axis)
    jj, ii = np.indices((mesh_n-1, mesh_n-1)); a = jj * mesh_n + ii
    tri = np.stack([a, a+mesh_n, a+1, a+1, a+mesh_n, a+mesh_n+1], -1).reshape(-1, 3)
    mesh = ASSETS / 'Meshes/trench_continuous.bytes'
    old.savemesh(mesh, np.stack([mx, mh, mz], -1).reshape(-1, 3), normals.reshape(-1, 3), np.stack([mx / 3.1, mz / 3.1], -1).reshape(-1, 2), tri)
    height = ASSETS / 'Data/trench_height.bytes'
    height.write_bytes(h.astype('<f4').tobytes())
    sample = RegularGridInterpolator((axis, axis), h)
    center = lambda zz: float(channel_center(zz))
    path = [[-17, -31], [-11, -25], [center(-19), -19], [center(-5), -5], [center(7), 7], [center(15) + 9, 19], [17, 25], [16, 13]]
    route_xz = old.densify(path, spacing=.25)
    camera = np.column_stack([route_xz[:, 0], sample(route_xz[:, [1, 0]]) + .65, route_xz[:, 1]])
    target_xz = np.array([17., 8.])
    target = np.array([target_xz[0], float(sample([target_xz[[1, 0]]])[0]) + .29, target_xz[1]])
    states = [nominal_visibility(eye, target, .26, sample) for eye in camera]
    groups = old.runs(states)
    stable = [g for g in groups if g['state'] != 'P' and g['end'] - g['start'] >= 4]
    sequence = ''.join(g['state'] for g in stable)
    if 'VHV' not in sequence:
        raise RuntimeError(f'Trench nominal VHV missing: {sequence}')
    witnesses = []
    for i in range(len(stable)-2):
        if ''.join(g['state'] for g in stable[i:i+3]) == 'VHV':
            witnesses = [(g['start']+g['end'])//2 for g in stable[i:i+3]]
            break
    rng = np.random.default_rng(20261108)
    rocks = []
    for _ in range(560):
        rx, rz = rng.uniform(-70, 70, 2)
        if np.min(np.linalg.norm(route_xz - [rx, rz], axis=1)) < 1.15:
            continue
        if np.linalg.norm(target_xz - [rx, rz]) < 1.1:
            continue
        if rng.random() < .55 and abs(rx-center(rz)) > 18:
            continue
        scale = float(rng.uniform(.11, .53))
        if rng.random() < .07:
            scale *= 2.0
        rocks.append(dict(type=int(rng.integers(0, 9)), x=float(rx), z=float(rz), ground=float(sample([[rz, rx]])[0]), scale=scale, yaw=float(rng.uniform(0, 360)), burial=float(rng.uniform(.20, .38)), stretch=rng.uniform(.8, 1.25, 3).tolist(), primary=False))
    scene = dict(id='trench', name='沟槽 · 连续地形修正样例', source='rille', description='沿缓坡进入沟底，再从另一侧缓坡走出；固定红球经历可见、遮挡和重现。', sourceNative=str(source.relative_to(PROJECT)).replace('\\', '/'), sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(), sourceOrigin=[1000., 0.], nativeGridSpacingM=native_spacing, mesh='Meshes/trench_continuous.bytes', heightData='Data/trench_height.bytes', extent=extent, gridSize=n, eyeHeight=.65, targetRadius=.26, targetPosition=target.tolist(), route=[dict(position=q.tolist()) for q in camera], rocks=rocks, witnessIndices=witnesses, provenance='Existing DEM-derived rille asset, crop centered at source-local (1000,0)m. Original elevations retained; additive synthetic shallow trough and 1.8cm amplitude procedural detail. 0.25m render mesh is resampling, not measured DEM resolution.')
    (ASSETS / 'revision_config.json').write_text(json.dumps(dict(version='trench-pilot-1', scenes=[scene]), ensure_ascii=False), encoding='utf-8')
    slopes = np.degrees(np.arctan(np.hypot(dx, dz)))
    grade = np.degrees(np.arctan2(np.abs(np.diff(camera[:, 1])), np.linalg.norm(np.diff(camera[:, [0, 2]], axis=0), axis=1)))
    area = (np.abs(x) < 30) & (np.abs(z) < 40)
    report = dict(status='GEOMETRY_AND_NOMINAL_VISIBILITY_PASS', sceneCount=1, terrainSurfaceCount=1, terrainVertices=mesh_n*mesh_n, terrainTriangles=len(tri), duplicateTerrainTriangles=0, separateBackgroundSurface=False, nearRenderGridSpacingM=.25, farRenderGridSpacingM=8., terrainContextWidthM=float(np.ptp(mesh_axis)), nativeSourceGridSpacingM=native_spacing, originalSourceHash=scene['sourceSha256'], originalSourceElevationsScaled=False, syntheticModifications=scene['provenance'], nominalSequence=sequence, nominalWitnessIndices=witnesses, routePoints=len(camera), routeLengthM=float(np.linalg.norm(np.diff(camera, axis=0), axis=1).sum()), routeGradeP95AndMaxDeg=np.percentile(grade, [95, 100]).tolist(), activeAreaSlopeP50P95MaxDeg=np.percentile(slopes[area], [50, 95, 100]).tolist(), robotWalkingTested=False, MuJoCoTested=False, unityRenderVerified=False)
    DELIVERY.mkdir(parents=True, exist_ok=True)
    (DELIVERY / 'geometry_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    np.savez_compressed(ROOT/'work/trench_design.npz', axis=axis, height=h, slope=slopes, route=camera, target=target, states=np.array(states), witnesses=witnesses)
    for name in ('TerrainRevision.cs', 'TerrainRevisionBuilder.cs', 'TerrainRevisionAudit.cs'):
        folder = 'Editor' if name != 'TerrainRevision.cs' else 'Scripts'
        src = ROOT / 'work' / name
        if src.exists():
            shutil.copy2(src, ASSETS / folder / name)
    print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    build()
