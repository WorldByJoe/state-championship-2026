# fetch_naip.py · v1.0 · 2026-10-12
# Read the newest NAIP aerial (USDA, public domain) for the course clip from Microsoft Planetary
# Computer's cloud-optimised GeoTIFFs, warp it onto the DEM grid, and write
#   aerial_course.jpg  RGB at 0.5 m for the 3D texture
#   naip4/naip4_1m.tif 4-band RGB+NIR at 1 m for the tree NDVI check
#   naip_0p3.tif       RGB at the native 0.3 m for reading trail surfaces
# With 'background x0 y0 x1 y1 res out' it instead writes a coarse RGB mosaic of a large box (any years).
# Used when the USGS image service is down or older than the trails.
# CHANGED: first version.
import json, os, sys, subprocess, numpy as np, rasterio
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.transform import from_origin
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
info = json.load(open('course_info.json')); E0, N1, W, H = info['origin_e'], info['origin_n'], info['width'], info['height']; CRS = 'EPSG:%d' % info['epsg']
(lo0, la0), (lo1, la1) = info['bbox_ll']
BG = len(sys.argv) > 1 and sys.argv[1] == 'background'
if BG:
    x0, y0, x1, y1, bres = map(float, sys.argv[2:7]); BGOUT = sys.argv[7]
    (lo0, la0, lo1, la1) = transform_bounds(CRS, 'EPSG:4326', x0, y0, x1, y1)
    E0, N1, W, H = x0, y1, x1 - x0, y1 - y0
q = {'collections': ['naip'], 'bbox': [lo0, la0, lo1, la1], 'limit': 200}
items = json.loads(subprocess.run(['curl', '-s', '--max-time', '60', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(q),
                                   'https://planetarycomputer.microsoft.com/api/stac/v1/search'], capture_output=True, text=True).stdout)['features']
year = max(int(f['properties']['naip:year']) for f in items)
if BG:   # newest image of each quarter quad
    best = {}
    for f in items:
        k = f['id'].split('_')[2] + f['id'].split('_')[3]
        if k not in best or f['properties']['naip:year'] > best[k]['properties']['naip:year']: best[k] = f
    items = list(best.values())
else:
    items = [f for f in items if int(f['properties']['naip:year']) == year]
print('NAIP', year, [f['id'] for f in items], 'gsd', items[0]['properties']['gsd'])
tok = json.loads(subprocess.run(['curl', '-s', '--max-time', '60', 'https://planetarycomputer.microsoft.com/api/sas/v1/token/naip'], capture_output=True, text=True).stdout)['token']
def warp(res, bands):
    w, h = round(W / res), round(H / res); tr = from_origin(E0, N1, res, res)
    out = np.zeros((len(bands), h, w), np.float32); have = np.zeros((h, w), bool)
    for f in items:
        with rasterio.open('/vsicurl/' + f['assets']['image']['href'] + '?' + tok) as src:
            b = transform_bounds(CRS, src.crs, E0, N1 - H, E0 + W, N1, densify_pts=21)
            win = rasterio.windows.from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
            win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            if win.width < 1 or win.height < 1: continue
            ow, oh = max(1, round(win.width * src.res[0] / res)), max(1, round(win.height * src.res[1] / res))   # read from overviews when coarse
            a = src.read(bands, window=win, out_shape=(len(bands), oh, ow), resampling=Resampling.average).astype(np.float32)
            wtr = src.window_transform(win) * rasterio.Affine.scale(win.width / ow, win.height / oh)
            tmp = np.zeros((len(bands), h, w), np.float32)
            for k in range(len(bands)):
                reproject(a[k], tmp[k], src_transform=wtr, src_crs=src.crs, dst_transform=tr, dst_crs=CRS, src_nodata=0, dst_nodata=0, resampling=Resampling.bilinear)
            m = (tmp.sum(0) > 0) & ~have; out[:, m] = tmp[:, m]; have |= m
    print('res %.2f m: %d x %d px, covered %.4f' % (res, w, h, have.mean())); return out, tr
if BG:
    rgb, _ = warp(bres, [1, 2, 3]); Image.fromarray(np.moveaxis(rgb, 0, -1).clip(0, 255).astype(np.uint8)).save(BGOUT, quality=80)
    print('wrote', BGOUT, 'from', len(items), 'NAIP images'); sys.exit(0)
rgb, _ = warp(0.5, [1, 2, 3])
Image.fromarray(np.moveaxis(rgb, 0, -1).clip(0, 255).astype(np.uint8)).save('aerial_course.jpg', quality=82)
os.makedirs('naip4', exist_ok=True)
four, tr1 = warp(1.0, [1, 2, 3, 4])
with rasterio.open('naip4/naip4_1m.tif', 'w', driver='GTiff', dtype='uint8', count=4, width=W, height=H, crs=CRS, transform=tr1, compress='deflate') as d: d.write(four.clip(0, 255).astype(np.uint8))
fine, tr3 = warp(0.3, [1, 2, 3])
with rasterio.open('naip_0p3.tif', 'w', driver='GTiff', dtype='uint8', count=3, width=fine.shape[2], height=fine.shape[1], crs=CRS, transform=tr3, compress='jpeg', photometric='ycbcr', tiled=True) as d: d.write(fine.clip(0, 255).astype(np.uint8))
json.dump(dict(year=year, items=[f['id'] for f in items], date=items[0]['properties']['datetime'], gsd=items[0]['properties']['gsd']), open('naip_source.json', 'w'), indent=1)
print('wrote aerial_course.jpg, naip4/naip4_1m.tif, naip_0p3.tif')
