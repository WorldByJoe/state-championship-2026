# build_course.py · v1.1 · 2026-10-12
# Mosaic the USGS 1 m lidar DEM tiles, clip them around the race course,
# sample the GPX track against the DEM, and write the data files the HTML
# viewer loads (heights PNG, track JSON, stats).
# CHANGED: v1.1 tiles in any projection and unit (e.g. State Plane feet) are warped to
#   NAD83(2011) UTM metres at 1 m and elevations converted to metres; source text from
#   race_config.json. v1.0 first version (Chalk Creek, tiles already UTM metres).
import re, math, json, glob, sys, os, struct, zlib
import numpy as np, rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, transform_bounds, Resampling
from rasterio.transform import from_origin
from rasterio.transform import rowcol
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
TILES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'dem_tiles')
MARGIN = 220.0           # metres of terrain kept around the track bbox

# ---- the track ---------------------------------------------------------
txt = open(os.path.join(HERE, 'course.gpx')).read()
pts = re.findall(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)">\s*<ele>([-\d.]+)</ele>', txt)
lat = np.array([float(p[0]) for p in pts]); lon = np.array([float(p[1]) for p in pts])
gpx_ele = np.array([float(p[2]) for p in pts])
srcs = [rasterio.open(f) for f in sorted(glob.glob(os.path.join(TILES, '*.tif')))]
SCRS = srcs[0].crs; assert all(s.crs == SCRS for s in srcs), 'tiles in mixed projections'
units = (SCRS.linear_units or '').lower()
ZFAC = 1200 / 3937 if 'us survey' in units else 0.3048 if ('foot' in units or 'feet' in units) else 1.0   # USGS keeps z in the horizontal unit
zone = int((float(np.mean(lon)) + 180) // 6) + 1; EPSG = 6329 + zone                                    # NAD83(2011) / UTM zone N, metres (13N = 6342)
CRS = rasterio.crs.CRS.from_epsg(EPSG)
print('tiles', len(srcs), SCRS, 'res', srcs[0].res, 'units', units, '-> EPSG:%d, z x %.6f' % (EPSG, ZFAC))
CFG = json.load(open(os.path.join(HERE, 'race_config.json')))
to_utm = Transformer.from_crs('EPSG:4326', CRS, always_xy=True)
E, N = to_utm.transform(lon, lat)

# ---- mosaic + clip -----------------------------------------------------
bounds = (E.min() - MARGIN, N.min() - MARGIN, E.max() + MARGIN, N.max() + MARGIN)
W_ = int(np.ceil(bounds[2] - bounds[0])); H_ = int(np.ceil(bounds[3] - bounds[1])); tr = from_origin(bounds[0], bounds[3], 1.0, 1.0)
sb = transform_bounds(CRS, SCRS, *bounds, densify_pts=21); pad = 20 * srcs[0].res[0]
mos, mtr = merge(srcs, bounds=(sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad), nodata=-999999.0)   # in the tiles' own projection
z = np.full((H_, W_), -999999.0, np.float32)
reproject(mos[0].astype(np.float32), z, src_transform=mtr, src_crs=SCRS, src_nodata=-999999.0, dst_transform=tr, dst_crs=CRS, dst_nodata=-999999.0, resampling=Resampling.bilinear)
print('clip', z.shape, 'origin E %.0f N %.0f' % (tr.c, tr.f), 'valid %.4f' % (z > -1000).mean())
assert (z > -1000).all(), 'nodata inside the clip'
z *= ZFAC
meta = dict(driver='GTiff', dtype='float32', count=1, width=W_, height=H_, crs=CRS, transform=tr, compress='deflate', predictor=3)
with rasterio.open(os.path.join(HERE, 'course_dem_1m.tif'), 'w', **meta) as d: d.write(z[None])

# ---- sample the track against the DEM ----------------------------------
# bilinear sample
def sample(e, n):
    c = (e - tr.c) / tr.a; r = (n - tr.f) / tr.e
    c0 = np.clip(np.floor(c).astype(int), 0, z.shape[1] - 2); r0 = np.clip(np.floor(r).astype(int), 0, z.shape[0] - 2)
    fc = c - c0; fr = r - r0
    return (z[r0, c0] * (1 - fc) * (1 - fr) + z[r0, c0 + 1] * fc * (1 - fr) + z[r0 + 1, c0] * (1 - fc) * fr + z[r0 + 1, c0 + 1] * fc * fr)
dem_ele = sample(E, N)
# drop exact-duplicate points, keep order
keep = np.r_[True, (np.diff(E) != 0) | (np.diff(N) != 0)]
E, N, dem_ele, gpx_ele = E[keep], N[keep], dem_ele[keep], gpx_ele[keep]
step = np.hypot(np.diff(E), np.diff(N)); dist = np.r_[0, np.cumsum(step)]
# resample every 2 m along the track, then smooth the DEM elevation over 10 m
s = np.arange(0, dist[-1], 2.0)
Es = np.interp(s, dist, E); Ns = np.interp(s, dist, N)
zs = sample(Es, Ns)
k = 5; zsm = np.convolve(np.pad(zs, k, mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), mode='valid')
grade = np.gradient(zsm, s) * 100
gain = np.sum(np.clip(np.diff(zsm), 0, None)); loss = -np.sum(np.clip(np.diff(zsm), None, 0))
print('track %.2f km  DEM gain %.0f m (%.0f ft)  loss %.0f m  ele %.1f..%.1f  grade max +%.1f%% / %.1f%%' % (
    dist[-1] / 1000, gain, gain * 3.281, loss, zsm.min(), zsm.max(), grade.max(), grade.min()))
print('GPX ele minus DEM ele: median %.1f m  p5 %.1f  p95 %.1f (first point excluded)' % tuple(np.percentile((gpx_ele - dem_ele)[1:], [50, 5, 95])))

# ---- write the viewer data ---------------------------------------------
# heights as a 16-bit PNG (value = (z - z0) * 100, hi byte in R, lo byte in G)
z0 = math.floor(z.min()); q = np.round((z - z0) * 100).astype(np.uint16)
assert q.max() < 65535
H, W = q.shape
rgb = np.zeros((H, W, 3), np.uint8); rgb[..., 0] = q >> 8; rgb[..., 1] = q & 255
def png(a):
    raw = b''.join(b'\x00' + a[i].tobytes() for i in range(a.shape[0]))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', a.shape[1], a.shape[0], 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
import base64
p = png(rgb)
open(os.path.join(HERE, 'heights.png'), 'wb').write(p)
# 4-corner lat/lon for reference
to_ll = Transformer.from_crs(CRS, 'EPSG:4326', always_xy=True)
info = dict(origin_e=tr.c, origin_n=tr.f, width=W, height=H, res=1.0, z0=z0, crs='EPSG:%d' % EPSG, epsg=EPSG,
            source=CFG['dem_source'],
            bbox_ll=[to_ll.transform(tr.c, tr.f + tr.e * H), to_ll.transform(tr.c + tr.a * W, tr.f)])
track = dict(s=np.round(s, 1).tolist(), x=np.round(Es - tr.c, 2).tolist(), y=np.round(Ns - tr.f, 2).tolist(),
             z=np.round(zsm, 2).tolist(), zraw=np.round(zs, 2).tolist(), grade=np.round(grade, 2).tolist(),
             length_m=float(dist[-1]), gain_m=float(gain), loss_m=float(loss),
             lat=np.round(np.interp(s, dist, lat[keep]), 6).tolist(), lon=np.round(np.interp(s, dist, lon[keep]), 6).tolist())
with open(os.path.join(HERE, 'course_data.js'), 'w') as f:
    f.write('// course_data.js · generated by build_course.py v1.1\n')
    f.write('window.COURSE_INFO = ' + json.dumps(info) + ';\n')
    f.write('window.COURSE_TRACK = ' + json.dumps(track) + ';\n')
    f.write('window.COURSE_HEIGHTS_PNG = "data:image/png;base64,' + base64.b64encode(p).decode() + '";\n')
print('wrote course_dem_1m.tif, heights.png (%.1f MB), course_data.js (%.1f MB)' % (len(p) / 1e6, os.path.getsize(os.path.join(HERE, 'course_data.js')) / 1e6))
json.dump(info, open(os.path.join(HERE, 'course_info.json'), 'w'), indent=1)
