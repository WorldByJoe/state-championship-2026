# build_solar.py · v1.0 · 2026-10-13
# Find solar arrays in the 0.3 m NAIP aerial and write crude panel rows for the viewer (solar_data.js).
#   1. panel pixels: bright and bluish (fixed rows) or darker bluish and not vegetation (tracker rows);
#   2. arrays: panel pixels smoothed and closed into solid regions of at least 1,500 m2;
#   3. per array: the row direction from the long thin panel strips inside it, the spacing from the 2D
#      Fourier transform near that direction (no stripe = a roof, rejected), then one row per peak, clipped
#      to where panels are seen.
# Rows within 30 degrees of east-west are fixed, tilted 25 degrees to the south; others lie flat.
# CHANGED: first version (fixed rows from the strict colour rule, tracker rows from the loose one).
import json, math, numpy as np, rasterio
from scipy import ndimage
HERE = __import__('os').path.dirname(__import__('os').path.abspath(__file__)); __import__('os').chdir(HERE)
with rasterio.open('naip_0p3.tif') as d: A = d.read().astype(np.float32); RES = d.res[0]
with rasterio.open('ndvi_1m.tif') as d: nd1 = d.read(1)
R, G, B = A; br = (R + G + B) / 3; bl = B / np.maximum(R, 1)
nd = nd1[np.minimum((np.arange(A.shape[1]) * RES).astype(int), nd1.shape[0] - 1)][:, np.minimum((np.arange(A.shape[2]) * RES).astype(int), nd1.shape[1] - 1)]
def run(panel, keep_tilt):
    """All panel rows found with this pixel rule; keep only rows with tilt == keep_tilt."""
    global rows, frac, h3, w3, lab, n, plab, pn, ids, cnt, cy_, cx_, ori, wt, good, STRIPE_MIN, celly, cellx
    # 0.9 m cells (3 x 3 pixels) for the region work
    h3, w3 = panel.shape[0] // 3, panel.shape[1] // 3; C = 0.9
    frac = panel[:h3 * 3, :w3 * 3].reshape(h3, 3, w3, 3).mean((1, 3))
    sm = ndimage.gaussian_filter(frac, 3)
    reg = ndimage.binary_fill_holes(ndimage.binary_closing(sm > 0.2, iterations=4))
    lab, n = ndimage.label(reg)
    # every connected panel strip at 0.3 m: centroid, orientation and length from its second moments
    plab, pn = ndimage.label(panel); ids = np.arange(1, pn + 1)
    cnt = ndimage.sum(np.ones_like(plab), plab, ids)
    yy_, xx_ = np.indices(panel.shape)
    cy_ = ndimage.mean(yy_, plab, ids); cx_ = ndimage.mean(xx_, plab, ids)
    syy = ndimage.mean(yy_ * yy_, plab, ids) - cy_ ** 2; sxx = ndimage.mean(xx_ * xx_, plab, ids) - cx_ ** 2; sxy = ndimage.mean(xx_ * yy_, plab, ids) - cx_ * cy_
    del yy_, xx_
    ori = 0.5 * np.arctan2(2 * sxy, sxx - syy)
    l1 = (sxx + syy) / 2 + np.sqrt(((sxx - syy) / 2) ** 2 + sxy ** 2); l2 = np.maximum((sxx + syy) / 2 - np.sqrt(((sxx - syy) / 2) ** 2 + sxy ** 2), 0.25)
    good = (cnt > 20) & (np.sqrt(l1 / l2) > 3); wt = np.sqrt(l1)          # long thin strips, weighted by length
    print('panel strips: %d, of which long and thin: %d' % (pn, good.sum()))
    STRIPE_MIN = float(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else 1000.0   # roofs score 54-165, real arrays 5,500-46,000 (2026-10-13)
    rows = []
    def lay_rows(m, ra, name):
        """Panel rows in sub-block m (0.9 m cells) whose rows run at angle ra (x east, y south)."""
        area = m.sum() * C * C
        if area < 800: return
        sl = ndimage.find_objects(m.astype(int))[0]; inner = ndimage.binary_erosion(m[sl], iterations=2)
        if inner.sum() < 200: return
        f0 = np.where(inner, frac[sl] - frac[sl][inner].mean(), 0.0); ny_, nx_ = f0.shape
        Fs = np.abs(np.fft.fft2(f0, s=(2 ** int(math.ceil(math.log2(ny_ * 2))), 2 ** int(math.ceil(math.log2(nx_ * 2)))))) ** 2
        fy = np.fft.fftfreq(Fs.shape[0], C)[:, None]; fx = np.fft.fftfreq(Fs.shape[1], C)[None, :]; fr = np.hypot(fx, fy)
        band = (fr > 1 / 15) & (fr < 1 / 3.5); th = np.arctan2(fy + 0 * fx, fx + 0 * fy); tg0 = ra + math.pi / 2
        near = band & (np.abs(((th - tg0 + np.pi / 2) % np.pi) - np.pi / 2) < math.radians(15))
        jy, jx = np.unravel_index(np.argmax(np.where(near, Fs, 0)), Fs.shape)
        strength = Fs[jy, jx] / np.median(Fs[band])                # a stripe's peak against the typical band power
        if strength < STRIPE_MIN: print('%s: %.0f m2 rejected, no stripes (peak/median %.0f)' % (name, area, strength)); return
        period = 1 / math.hypot(fx[0, jx], fy[jy, 0])
        ux, uy = math.cos(tg0), math.sin(tg0); vx, vy = -uy, ux        # u across rows, v along rows
        yy, xx = np.nonzero(m); X = (xx + 0.5) * C; Y = (yy + 0.5) * C
        u = X * ux + Y * uy; v = X * vx + Y * vy
        bins = np.arange(u.min(), u.max() + 0.3, 0.3); dg = np.digitize(u, bins)
        prof = np.bincount(dg, weights=frac[m], minlength=len(bins) + 1)[1:len(bins)] / np.maximum(np.bincount(dg, minlength=len(bins) + 1)[1:len(bins)], 1)
        ps = ndimage.gaussian_filter1d(prof, period / 0.3 / 6)
        peaks = [i for i in range(1, len(ps) - 1) if ps[i] >= ps[i - 1] and ps[i] > ps[i + 1] and ps[i] > ps.mean()]
        fill = (ps > (ps.max() + ps.min()) / 2).mean(); W = float(np.clip(fill * period, 1.5, 4.0))
        ang = (math.atan2(vy, vx) + math.pi / 2) % math.pi - math.pi / 2   # row direction with an eastward component
        fixed = abs(math.degrees(ang)) < 30; fsm = ndimage.uniform_filter(frac, 3)
        for i in peaks:
            uc = bins[i] + 0.15; tt = np.arange(v.min() - 2, v.max() + 2, 0.9)
            px = uc * ux + tt * vx; py = uc * uy + tt * vy
            ci = np.clip((px / C).astype(int), 0, w3 - 1); ri = np.clip((py / C).astype(int), 0, h3 - 1)
            seg, ns = ndimage.label(ndimage.binary_closing(m[ri, ci] & (fsm[ri, ci] > 0.15), iterations=3))
            for q in range(1, ns + 1):
                idx = np.flatnonzero(seg == q)
                if len(idx) * 0.9 < 4: continue
                t0, t1 = tt[idx[0]], tt[idx[-1]]
                rows.append(dict(x=round(uc * ux + (t0 + t1) / 2 * vx, 2), z=round(uc * uy + (t0 + t1) / 2 * vy, 2), a=round(ang, 4), L=round(t1 - t0 + 0.9, 1), W=round(W, 2), tilt=25 if fixed else 0))
        print('%s: %.0f m2, stripe peak/median %.0f, rows run %.0f deg from east, spacing %.1f m, panel width %.1f m, %s, %d rows' % (name, area, strength, math.degrees(ang), period, W, 'fixed tilt' if fixed else 'flat (tracker)', len(peaks)))

    celly = np.clip((cy_ / 3).astype(int), 0, h3 - 1); cellx = np.clip((cx_ / 3).astype(int), 0, w3 - 1)
    for k in range(1, n + 1):
        m = lab == k; area = m.sum() * C * C
        if area < 1500 or frac[m].mean() < 0.25: continue
        inb = m[celly, cellx] & good
        if inb.sum() < 5: continue
        # split the block by strip direction: east-west strips and north-south strips each make a sub-block
        d = np.degrees(ori)
        for cname, sel in (('E-W', inb & (np.abs(d) < 45)), ('N-S', inb & (np.abs(d) >= 45))):
            if wt[sel].sum() < 0.2 * wt[inb].sum() or sel.sum() < 4: continue
            look = np.zeros(pn + 1, bool); look[ids[sel]] = True
            sm_ = look[plab][:h3 * 3, :w3 * 3].reshape(h3, 3, w3, 3).any((1, 3))
            sub = m & ndimage.binary_dilation(sm_, iterations=5)
            ra = 0.5 * math.atan2((wt[sel] * np.sin(2 * ori[sel])).sum(), (wt[sel] * np.cos(2 * ori[sel])).sum())
            lay_rows(sub, ra, 'block %d %s' % (k, cname))
    return [r for r in rows if r['tilt'] == keep_tilt]

# the strict rule (bright blue) reads the fixed rows cleanly; the loose rule (grey-blue, not vegetation)
# also catches the lighter tracker panels but blurs the fixed rows, so each kind comes from its own rule
strict = (bl > 1.0) & (br > 90)
loose = strict | ((bl > 0.86) & (br < 175) & (br > 60) & (nd < 0.05))
print('-- fixed rows (strict rule)'); fixed_rows = run(strict | ((bl > 0.86) & (br < 140) & (br > 60) & (nd < 0.05)), 25)
print('-- tracker rows (loose rule)'); tracker_rows = run(loose, 0)
rows = fixed_rows + tracker_rows
with open('solar_data.js', 'w') as f:
    f.write('// solar_data.js · generated by build_solar.py v1.0 · panel rows found in the 2023 NAIP aerial\n')
    f.write('// x east, z south: metres from the NW corner of the DEM clip; a = row direction (radians from east, z south); L, W metres; tilt degrees\n')
    f.write('window.SOLAR = ' + json.dumps(rows) + ';\n')
print('%d panel rows written, %.0f m of row in all' % (len(rows), sum(r['L'] for r in rows)))
