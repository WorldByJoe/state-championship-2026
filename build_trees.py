# build_trees.py · v1.2 · 2026-10-12
# Trees from the lidar point cloud: canopy height = highest return per 1 m cell minus the
# bare-earth DEM; each tree is a local maximum of the canopy at least 2 m tall; NAIP NDVI confirms
# it is vegetation (not a roof or a rock); its colour comes from the aerial. Writes chm_1m.tif
# (canopy height), ndvi_1m.tif, trees_data.js (10 bytes per tree, base64) and a summary.
# CHANGED: v1.2 points in any projection and unit (e.g. State Plane feet) are moved into the DEM's
#   UTM metres; NAIP read from naip4/naip4_1m.tif when present; trees kept 2.5 m off the GPS line and
#   crowns trimmed 1.2 m short of it so none straddles the drawn trail. v1.1 crown colour = darkest 3x3 pixel.
import sys, os, glob, json, base64, struct
import numpy as np, rasterio, laspy
from pyproj import Transformer, CRS as PCRS
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
LAZ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'laz')
NAIP4 = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'naip4')
info = json.load(open('course_info.json')); E0, N1, W, H = info['origin_e'], info['origin_n'], info['width'], info['height']
with rasterio.open('course_dem_1m.tif') as d: dtm = d.read(1); prof = d.profile
T = json.loads(open('course_data.js').read().split('window.COURSE_TRACK = ')[1].split(';\n')[0])

# ---- highest return per cell -------------------------------------------
dsm = np.full(H * W, -9999.0, np.float32); npts = 0
for f in sorted(glob.glob(os.path.join(LAZ, '*.laz'))):
    with laspy.open(f) as fh:
        hdr = fh.header; lcrs = PCRS.from_user_input(hdr.parse_crs())
        hcrs = lcrs.sub_crs_list[0] if lcrs.is_compound else lcrs; vcrs = lcrs.sub_crs_list[1] if lcrs.is_compound else hcrs
        to_dem = Transformer.from_crs(hcrs, 'EPSG:%d' % info['epsg'], always_xy=True)
        zf = vcrs.axis_info[0].unit_conversion_factor or 1.0       # feet -> metres when the survey is in feet
        counts = {}
        for ch in fh.chunk_iterator(4_000_000):
            x, y = to_dem.transform(np.asarray(ch.x), np.asarray(ch.y)); z = np.asarray(ch.z) * zf; cls = np.asarray(ch.classification)
            for k, n in zip(*np.unique(cls, return_counts=True)): counts[int(k)] = counts.get(int(k), 0) + int(n)
            keep = (cls != 7) & (cls != 18) & (cls != 6)           # noise and buildings out
            c = np.floor(x - E0).astype(np.int64); r = np.floor(N1 - y).astype(np.int64)
            m = keep & (c >= 0) & (c < W) & (r >= 0) & (r < H)
            idx = r[m] * W + c[m]; zz = z[m].astype(np.float32)
            order = np.argsort(zz, kind='stable')                   # later (higher) assignments win
            sub = np.full(H * W, -9999.0, np.float32); sub[idx[order]] = zz[order]; dsm = np.maximum(dsm, sub)
            npts += m.sum()
    print(os.path.basename(f)[-12:-4], 'points %.1fM' % (hdr.point_count / 1e6), 'classes', counts, 'z x %.4f' % zf, 'z %.0f..%.0f' % (z.min(), z.max()))
dsm = dsm.reshape(H, W); valid = dsm > -9000
print('cells with returns %.3f  points used %.1fM' % (valid.mean(), npts / 1e6))
diff = dsm - dtm
print('DSM minus DTM: median %.2f  p10 %.2f  p90 %.2f  p99 %.2f' % tuple(np.percentile(diff[valid], [50, 10, 90, 99])))
chm = np.where(valid, np.clip(diff, 0, 45), 0).astype(np.float32)
prof.update(dtype='float32', nodata=None)
with rasterio.open('chm_1m.tif', 'w', **prof) as d: d.write(chm[None])

# ---- NDVI and colour from the 4-band NAIP --------------------------------
if os.path.exists(os.path.join(NAIP4, 'naip4_1m.tif')):
    with rasterio.open(os.path.join(NAIP4, 'naip4_1m.tif')) as d: naip = d.read().astype(np.float32)
else:
    naip = np.concatenate([rasterio.open(os.path.join(NAIP4, n)).read().astype(np.float32) for n in ('naip4_L.tif', 'naip4_R.tif')], axis=2)
assert naip.shape[1:] == (H, W), naip.shape
R, G, B, NIR = naip
ndvi = (NIR - R) / (NIR + R + 1e-3)
with rasterio.open('ndvi_1m.tif', 'w', **prof) as d: d.write(ndvi.astype(np.float32)[None])

# ---- individual trees ----------------------------------------------------
cs = ndimage.gaussian_filter(chm, 0.6)
def peaks(size, lo, hi): return (cs == ndimage.maximum_filter(cs, size=size)) & (cs >= lo) & (cs < hi)
cand = peaks(3, 2.0, 3.0) | peaks(5, 3.0, 8.0) | peaks(7, 8.0, 14.0) | peaks(9, 14.0, 99)
rr, cc = np.nonzero(cand); h = cs[rr, cc]
nd = ndimage.uniform_filter(ndvi, 3)[rr, cc]
print('candidates', len(rr), 'NDVI percentiles at candidates', np.percentile(nd, [5, 25, 50, 75, 95]).round(2))
hist, edges = np.histogram(nd, bins=np.arange(-0.2, 0.9, 0.05)); print('NDVI histogram', list(zip(edges[:-1].round(2).tolist(), hist.tolist())))
NDVI_MIN = 0.10
veg = nd > NDVI_MIN
# not on the trail itself: drop anything within 1.5 m of the track centreline
tx = np.array(T['x']); ty = -np.array(T['y'])
from scipy.spatial import cKDTree
dist, _ = cKDTree(np.c_[tx, ty]).query(np.c_[cc + 0.5, rr + 0.5])
keep = veg & (dist > 2.5)   # GPS lines wander a few metres: keep a clear corridor for the ride view
rr, cc, h, nd, dist = rr[keep], cc[keep], h[keep], nd[keep], dist[keep]
broad = (nd > 0.42) | ((h > 9) & (nd > 0.3))
r = np.where(broad, np.clip(0.35 * h, 1.5, 8), np.clip(0.9 + 0.28 * h, 1.0, 4.5))
r = np.minimum(r, np.maximum(0.4, dist - 1.2))   # crowns stop 1.2 m short of the GPS line
col = np.stack([ndimage.minimum_filter(b, 3)[rr, cc] for b in (R, G, B)], 1)   # the darkest pixel under the crown is the crown, not the ground
col = np.clip(col, 0, 255)
print('trees kept %d (conifer %d, broadleaf %d); height p50 %.1f p90 %.1f max %.1f m' % (len(rr), (~broad).sum(), broad.sum(), *np.percentile(h, [50, 90, 100])))
near = dist < 60; print('within 60 m of the track: %d' % near.sum())

# ---- pack: int16 x, int16 z(south), u8 h*4, u8 r*10, u8 R,G,B, u8 type ----
buf = bytearray()
for i in range(len(rr)):
    buf += struct.pack('<hhBBBBBB', int(cc[i]), int(rr[i]), int(min(round(h[i] * 4), 255)), int(min(round(r[i] * 10), 255)), int(col[i, 0]), int(col[i, 1]), int(col[i, 2]), int(broad[i]))
with open('trees_data.js', 'w') as f:
    f.write('// trees_data.js · generated by build_trees.py v1.0 · 2026-10-06 · 2020 lidar canopy + NAIP NDVI\n')
    f.write('window.TREES = ' + json.dumps(dict(n=len(rr), rec=10, b64=base64.b64encode(bytes(buf)).decode(),
            note='x east and z south in metres from the NW corner of the DEM clip; h in 0.25 m; r in 0.1 m; type 1 = broadleaf')) + ';\n')
print('trees_data.js %.2f MB' % (os.path.getsize('trees_data.js') / 1e6))
