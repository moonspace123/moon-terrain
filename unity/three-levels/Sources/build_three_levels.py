from pathlib import Path
import concurrent.futures
import hashlib
import json
import shutil
import sys
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import build_all_revision as previous
import build_revision as base_tools
import terrain_tools as tools

ROOT = Path(__file__).resolve().parents[1]
PORTABLE = (ROOT / 'UnityProject/Assets').is_dir()
DELIVERY = ROOT if PORTABLE else ROOT / 'outputs/Lunar_Terrain_Three_Levels'
PROJECT = DELIVERY / 'UnityProject'
ASSETS = PROJECT / 'Assets/TerrainLevels'
WORK = ROOT / ('Sources/GeneratedChecks' if PORTABLE else 'work/three_level_checks')
REFERENCE = ROOT / 'outputs/Lunar_Terrain_Revision'
NAMES = ['一级 · 基础', '二级 · 增强', '三级 · 复合']
RULES = ['基础形态', '主形态增强至1.5倍', '增强主形态，叠加次级起伏']
FAMILIES = previous.DESIGNS


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    if not PORTABLE:
        pairs = []
        for name in ('Assets', 'Packages', 'ProjectSettings'):
            source = REFERENCE / 'UnityProject' / name
            for p in source.rglob('*'):
                if p.is_file():
                    target = PROJECT / name / p.relative_to(source)
                    if not target.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        pairs.append((p, target))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda pair: shutil.copy2(*pair), pairs))
        print('STAGED', len(pairs), 'FILES', flush=True)
    for folder in ('Meshes', 'Data', 'Materials', 'Scripts', 'Editor'):
        (ASSETS / folder).mkdir(parents=True, exist_ok=True)
    base_tools.PROJECT = PROJECT
    for name in ('TerrainLevels.cs', 'TerrainLevelsPlayerSmoke.cs', 'TerrainLevelsBuilder.cs', 'TerrainLevelsAudit.cs', 'TerrainLevelsSuite.cs'):
        src = Path(__file__).parent / name
        if src.exists():
            shutil.copy2(src, ASSETS / ('Editor' if name in ('TerrainLevelsBuilder.cs', 'TerrainLevelsAudit.cs', 'TerrainLevelsSuite.cs') else 'Scripts') / name)


def secondary(x, z):
    # Natural correlated relief, rather than the regular sinusoid in V4.
    # Unit-normalised bounded field, same field and support for every level.
    field = .68 * tools.noise2(x * .105 + 1.4, z * .105 - .6, 23) + .32 * tools.noise2(x * .055 - 2, z * .055 + 3, 67)
    support = 1 - tools.smooth(56., 88., np.hypot(x, z))
    return .48 * field * support


def classify(cameras, target, sample, rocks):
    camera = np.asarray(cameras)
    f = target - camera
    f /= np.linalg.norm(f, axis=1, keepdims=True)
    right = np.cross(f, [0, 1, 0]); right /= np.linalg.norm(right, axis=1, keepdims=True)
    up = np.cross(right, f)
    t = np.linspace(.008, .995, 210)[None, :, None]
    margins = []
    for iz in (-1, 0, 1):
        for ix in (-1, 0, 1):
            end = target + right * (ix * .26) + up * (iz * .26)
            line = camera[:, None, :] + (end - camera)[:, None, :] * t
            margin = (line[:, :, 1] - sample(line[:, :, [2, 0]])).min(axis=1)
            for center, axes in rocks:
                hit = (np.sum(((line - center) / axes) ** 2, axis=-1).min(axis=1) < .90)
                margin = np.where(hit, np.minimum(margin, -.25), margin)
            margins.append(margin)
    m = np.array(margins)
    return np.where(m.max(axis=0) < -.06, 'H', np.where(m.min(axis=0) > .012, 'V', 'P'))


def camera_route(points, sample):
    return np.column_stack([points[:, 0], sample(points[:, [1, 0]]) + .65, points[:, 1]])


def grade(route):
    return np.degrees(np.arctan2(abs(np.diff(route[:, 1])), np.linalg.norm(np.diff(route[:, [0, 2]], axis=0), axis=1)))


def shared_route(design, samples, occluders, old_scene):
    tx, tz = old_scene['targetPosition'][0], old_scene['targetPosition'][2]
    targets = [(tx, tz), tuple(design['target']), (tx - 4, tz), (tx + 4, tz), (tx, tz - 5), (tx, tz + 5), (tx - 8, tz - 4), (tx + 6, tz - 5)]
    previous_points = np.array([p['position'][::2] for p in old_scene['route']])
    if design['id'] == 'barrier':
        approach = tools.densify([[-18., -10.], previous_points[0].tolist()], .25)
        previous_points = np.vstack([approach[:-1], previous_points])
    paths = [previous_points, tools.densify(design['path'], .25)]
    for target_xz in targets:
        target = [np.array([target_xz[0], float(s([[target_xz[1], target_xz[0]]])[0]) + .29, target_xz[1]]) for s in samples]
        for points in paths:
            routes = [camera_route(points, s) for s in samples]
            states = [classify(c, t, s, r) for c, t, s, r in zip(routes, target, samples, occluders)]
            sequences = [previous.sequence(s) for s in states]
            if all(q[1] for q in sequences) and max(grade(c).max() for c in routes) < 33:
                return points, routes, target, states, sequences, 'jointly_accepted_existing_route'
        gx, gz = np.meshgrid(np.arange(-28, 29, 4), np.arange(-28, 29, 4))
        grid = np.column_stack([gx.ravel(), gz.ravel()])
        candidates = [camera_route(grid, s) for s in samples]
        states = np.array([classify(c, t, s, r) for c, t, s, r in zip(candidates, target, samples, occluders)])
        distance = np.linalg.norm(grid - target_xz, axis=1)
        visible = np.flatnonzero((states == 'V').all(axis=0) & (distance > 9) & (distance < 37))
        hidden = np.flatnonzero((states == 'H').all(axis=0) & (distance > 5) & (distance < 32))
        if len(visible) < 2 or not len(hidden):
            continue
        hidden = sorted(hidden, key=lambda i: np.linalg.norm(grid[i]))[:10]
        for h in hidden:
            starts = sorted(visible, key=lambda i: np.linalg.norm(grid[i] - np.array(design['path'][0])))[:6]
            finishes = sorted(visible, key=lambda i: distance[i])[:8]
            for start in starts:
                for finish in finishes:
                    if np.linalg.norm(grid[start] - grid[finish]) < 7:
                        continue
                    points = tools.densify(grid[[start, h, finish]], .25)
                    routes = [camera_route(points, s) for s in samples]
                    if max(grade(c).max() for c in routes) > 33:
                        continue
                    st = [classify(c, t, s, r) for c, t, s, r in zip(routes, target, samples, occluders)]
                    seq = [previous.sequence(a) for a in st]
                    if all(q[1] for q in seq):
                        return points, routes, target, st, seq, 'one_route_jointly_selected_for_all_three_levels'
    raise RuntimeError('No single shared route accepted across all three levels for ' + design['id'])


def primary_rocks(kind, level, sample):
    if kind != 'barrier':
        return [], []
    vertices = tools.loadmesh(PROJECT / 'Assets/LunarPilot/Meshes/rock_1.bytes')[0]
    specs = [(0., 0., 4.5 * (1. if level == 0 else 1.5))]
    if level == 2:
        specs.append((3.6, 2.4, 4.5))
    records, ellipsoids = [], []
    for x, z, scale in specs:
        stretch = np.array([1.15, .95, 1.]); size = np.ptp(vertices, axis=0) * scale * stretch
        ground = float(sample([[z, x]])[0]); burial = .22
        center = np.array([x, ground + size[1] * (.5 - burial), z])
        ellipsoids.append((center, size * .46))
        records.append(dict(type=1, x=x, z=z, ground=ground, scale=scale, stretch=stretch.tolist(), yaw=29., burial=burial, primary=True))
    return records, ellipsoids


def build():
    stage()
    old_file = (PROJECT / 'Assets/TerrainRevision/revision_config.json')
    old_config = json.loads(old_file.read_text(encoding='utf-8'))
    old_by_id = {c['id']: c for c in old_config['scenes']}
    axis = np.linspace(-96, 96, 769); x, z = np.meshgrid(axis, axis)
    all_scenes, reports, paired = [], [], []
    for family_index, d in enumerate(FAMILIES):
        kind, origin = d['id'], d['origin']
        native, source, spacing = base_tools.source_surface(d['source'], origin)
        primary = previous.addition(kind, x, z)
        extra = np.zeros_like(x) if kind == 'barrier' else secondary(x, z)
        common = native(x, z) + .018 * tools.noise2(x * .29, z * .29, 19)
        heights = [common + primary * (1. if kind == 'barrier' else f) + (extra if level == 2 else 0) for level, f in enumerate([1., 1.5, 1.5])]
        samples = [RegularGridInterpolator((axis, axis), h) for h in heights]
        rocks_and_shapes = [primary_rocks(kind, level, s) for level, s in enumerate(samples)]
        points, routes, targets, states, sequences, route_method = shared_route(d, samples, [q[1] for q in rocks_and_shapes], old_by_id[kind])
        print('SHARED_ROUTE', kind, len(points), route_method, flush=True)
        # Cosmetic rock x/z/type/size/yaw/burial are identical across all three.
        # Exclude the shared route and all grounded targets for every level.
        cosmetic = []
        rng = np.random.default_rng(20261108 + family_index)
        for _ in range(620 if kind == 'perlin_rough' else 420):
            rx, rz = rng.uniform(-75, 75, 2)
            if np.min(np.linalg.norm(points - [rx, rz], axis=1)) < 1.3 or np.linalg.norm(targets[0][[0, 2]] - [rx, rz]) < 1.3:
                continue
            density = .28 + .52 * tools.smooth(-.3, .4, tools.noise2(np.array(rx * .035), np.array(rz * .035), 63))
            if rng.random() > density:
                continue
            scale = float(rng.uniform(.10, .48))
            if kind == 'perlin_rough':
                scale *= float(rng.uniform(1.3, 2.6))
            elif rng.random() < .06:
                scale *= 2
            cosmetic.append(dict(type=int(rng.integers(0, 9)), x=float(rx), z=float(rz), scale=scale, stretch=rng.uniform(.8, 1.25, 3).tolist(), yaw=float(rng.uniform(0, 360)), burial=float(rng.uniform(.2, .38)), primary=False))
        vv = tools.loadmesh(source)[0]
        ax = previous.axis_for(max(-768., float(vv[:, 0].min()) - origin[0] + 8), min(768., float(vv[:, 0].max()) - origin[0] - 8))
        az = previous.axis_for(max(-768., float(vv[:, 2].min()) - origin[1] + 8), min(768., float(vv[:, 2].max()) - origin[1] - 8))
        mx, mz = np.meshgrid(ax, az)
        j, i = np.indices((len(az) - 1, len(ax) - 1)); a = j * len(ax) + i
        tri = np.stack([a, a + len(ax), a + 1, a + 1, a + len(ax), a + len(ax) + 1], -1).reshape(-1, 3)
        source_sha = digest(source)
        common_route_sha = hashlib.sha256(points.astype('<f8').tobytes()).hexdigest()
        focus_y = float(samples[0]([[0., 0.]])[0])
        for level, strength in enumerate([1., 1.5, 1.5]):
            scene_id = kind + '_a' + str(level)
            s = samples[level]; h = heights[level]
            mh = native(mx, mz) + .018 * tools.noise2(mx * .29, mz * .29, 19) + (1. if kind == 'barrier' else strength) * previous.addition(kind, mx, mz)
            if level == 2 and kind != 'barrier':
                mh += secondary(mx, mz)
            dz, dx = np.gradient(mh, az, ax); normal = np.stack([-dx, np.ones_like(mh), -dz], -1); normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
            mesh = ASSETS / 'Meshes' / (scene_id + '_continuous.bytes')
            tools.savemesh(mesh, np.stack([mx, mh, mz], -1).reshape(-1, 3), normal.reshape(-1, 3), np.stack([mx / 3.1, mz / 3.1], -1).reshape(-1, 2), tri)
            height_path = ASSETS / 'Data' / (scene_id + '_height.bytes'); height_path.write_bytes(h.astype('<f4').tobytes())
            rocks = rocks_and_shapes[level][0] + [dict(rec, ground=float(s([[rec['z'], rec['x']]])[0])) for rec in cosmetic]
            rule = RULES[level] if kind != 'barrier' or level != 2 else '增强主屏障，增加第二块主要遮挡岩石'
            c = dict(id=scene_id, family=kind, familyName=d['name'], level=level, levelName=NAMES[level], name=d['name'], source=d['source'], description=d['description'], levelDescription=rule, primaryStrength=strength, secondaryFieldCoefficientM=.48 if level == 2 and kind != 'barrier' else 0., designSeed=23, cosmeticSeed=20261108 + family_index, secondarySeeds=[23,67], sourceNative=str(source.relative_to(PROJECT)).replace('\\', '/'), sourceSha256=source_sha, sourceOrigin=origin, nativeGridSpacingM=spacing, mesh='Meshes/' + mesh.name, heightData='Data/' + height_path.name, extent=96., gridSize=769, eyeHeight=.65, targetRadius=.26, targetPosition=targets[level].tolist(), route=[dict(position=p.tolist()) for p in routes[level]], routeXZSha256=common_route_sha, rocks=rocks, witnessIndices=sequences[level][1], comparisonFocus=[0., focus_y, 0.], comparisonBankPosition=[22., float(samples[0]([[-29.,22.]])[0])+8., -29.], comparisonBankFocus=[0., float(samples[0]([[4.,0.]])[0]), 4.], provenance='Preserved DEM-relative macro elevations. Synthetic primary relief strength ' + str(strength) + '. Same source crop, fixed shared horizontal route, target x/z and grounding rule, camera, light, decorative rock layout and seed across all three. Unity scale adaptation of LunarBench V4; no empirical difficulty claim.')
            all_scenes.append(c)
            dz, dx = np.gradient(h, axis, axis)
            slope = np.degrees(np.arctan(np.hypot(dx, dz)))
            rec = dict(id=scene_id, family=kind, level=level, status='NOMINAL_GEOMETRY_PASS', primaryStrength=strength, nominalSequence=sequences[level][0], routeChoice=route_method, sharedRouteXZSha256=common_route_sha, sourceSha256=source_sha, sourceElevationsScaled=False, terrainSurfaceCount=1, vertices=len(ax) * len(az), triangles=len(tri), routeGradeP95MaxDeg=np.percentile(grade(routes[level]), [95, 100]).tolist(), robotWalkingTested=False, empiricalDifficulty='unmeasured')
            reports.append(rec)
            np.savez_compressed(WORK / (scene_id + '.npz'), axis=axis, height=h, route=routes[level], target=targets[level], primary=primary * (1. if kind == 'barrier' else strength), secondary=extra if level == 2 else np.zeros_like(extra))
            print(json.dumps(rec), flush=True)
        checks = dict(nativeSourceAndOriginFixed=True, a2SecondaryMaxAbsM=float(abs(extra).max()), horizontalRouteIdentical=all(np.array_equal(routes[0][:, [0, 2]], c[:, [0, 2]]) for c in routes[1:]), targetXZIdentical=all(np.array_equal(targets[0][[0, 2]], t[[0, 2]]) for t in targets[1:]), primaryOccluderCounts=[len(q[0]) for q in rocks_and_shapes], allThreeNominalVHV=all(bool(q[1]) for q in sequences))
        paired.append(dict(family=kind, checks=checks, routeXZSha256=common_route_sha))
    config = dict(version='eight-families-three-levels-1', repositoryCommit='a63a83e8a976663565408467955a0fb3f924c77d', designLabels=['基础', '增强', '复合'], empiricalDifficultyValidated=False, scenes=all_scenes)
    (ASSETS / 'levels_config.json').write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
    (DELIVERY / 'geometry_verification.json').write_text(json.dumps(dict(status='TWENTY_FOUR_NOMINAL_GEOMETRY_PASS', scenes=reports), ensure_ascii=False, indent=2), encoding='utf-8')
    (DELIVERY / 'paired_design_verification.json').write_text(json.dumps(dict(status='EIGHT_PAIRED_GROUPS_PASS', scope='Controlled design pairs; not empirical difficulty calibration', families=paired), ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    build()
