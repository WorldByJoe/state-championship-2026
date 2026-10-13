# State Championship 2026 · course notes

Compiled 2026-10-12 from the league site, Colorado Mountain College news, OpenStreetMap, USGS lidar and USDA aerial imagery.

## The race

| | |
|---|---|
| Event | Colorado High School Cycling League State Championship 2026 |
| Dates | Saturday Oct 24 (Freshman and JV) and Sunday Oct 25, 2026 (Sophomore, Varsity, Coach race) |
| Venue | CMC Spring Valley Campus, 3000 CO Rd 114, Glenwood Springs CO 81601 |
| Lap | 5.6 mi, 653 ft climbing per lap (league figures) |
| Entry | Qualification required; registration closes Oct 19; not included in the Series Pass |
| Rules | E-bikes not permitted; no dogs on the CMC campus |

The league lists the starting elevation as 5,760 ft, which is the elevation of Glenwood Springs itself. The lidar puts the start on the campus field at 6,880 ft.

CMC Spring Valley first hosted the championship in 2022. For that race the college and the league built about three miles of new, professionally built trail connecting to the existing campus network.

### Schedule

| Time | Saturday | Sunday |
|---|---|---|
| 7:00-8:00 | Pre-ride | Pre-ride |
| 7:45 | Coach meeting | Coach meeting |
| 8:15 | Freshman Boys staging | Sophomore Boys staging |
| 9:40 | Freshman Girls staging | Sophomore Girls staging |
| 11:00 | JV Boys staging | Varsity Boys staging |
| 12:25 / 12:45 | JV Girls staging (12:25) | Varsity Girls staging (12:45) |
| Afternoon | Pre-ride about 2:30-4:00; JV and Freshman awards 4:00; season awards 4:30 (picnic at the CMC Field House) | Coach race staging 3:00; Varsity, Sophomore and team awards 4:15 |

Friday pre-ride runs 2:00-5:30 PM. Pre-ride is for registered riders and coaches with a number plate on the bike.

## The course from the lidar

The GPX is the league's "Racecourse GPX" download. The file itself is named "2025 State Championship Racecourse" and was recorded on 2025-09-10. The league also posts a separate warm-up GPX, which is not used here.

| | |
|---|---|
| Length | 5.65 mi / 9.09 km |
| Total ascent | 761 ft / 232 m (the league's 653 ft counts only the larger rises) |
| Start and finish | about 6,880 ft, on the campus field |
| High point | 7,140 ft at mile 1.03 |
| Low point | 6,655 ft at mile 4.07 |
| Steepest | about +17% climbing, -18% descending |

The lap climbs 185 ft in its first 0.6 mile and another 87 ft to the high point at mile 1.0. It then descends Dreamer, dropping 295 ft by mile 2.0, and keeps losing height to the low point at mile 4.1. The last 1.6 miles climb back about 320 ft, with pitches near 17%.

## Trail surface and passing

The surface was read from a 24 m strip of the USDA NAIP aerial centred on the race GPX. The image was taken on 7 Sep 2023 at 0.3 m, after the 2022 trail building. Trail names come from OpenStreetMap, which maps 72% of the lap.

| Miles | Surface | Passing |
|---|---|---|
| 0.00-0.07 | Campus grass field (start) | Anywhere |
| 0.07-0.50 | Paved path crossing, then a wide dirt path, about 2-3 m | Yes |
| 0.50-0.61 | Gravel road | Yes |
| 0.61-0.97 | Singletrack, Spring Valley Summit Trail | Single file |
| 0.97-1.06 | Gravel road | Yes |
| 1.06-1.98 | Singletrack, Dreamer (the long descent) | Single file |
| 1.98-2.71 | Singletrack through piñon-juniper, then Swoop's Loop | Single file |
| 2.71-2.97 | Dirt track beside the solar array, about 2.5 m | Yes |
| 2.97-3.56 | Singletrack, Swoop's Loop then East Ridge Loop | Single file |
| 3.56-3.70 | East Ridge Loop, wider singletrack about 1.5 m | Tight |
| 3.70-5.16 | Singletrack, Swoop's Loop, crossing a road at 4.38 | Single file |
| 5.16-5.26 | Short double-track | Yes |
| 5.26-5.40 | Singletrack, Spring Valley Summit Trail | Single file |
| 5.40-5.65 | Wide dirt down to the campus field (finish) | Yes |

That comes to about 4.3 miles of singletrack and 1.3 miles of grass, road or double-track per lap. The opening climb is on the wide first 0.6 mile, the only long stretch with room to pass before 1.6 miles of singletrack over the top and down Dreamer. After that, the wide windows are short: miles 0.97-1.06, 2.71-2.97 and 5.16-5.26, then the run into the finish.

Limits: the imagery is from September 2023, so any trail work since then does not show. Widths are estimates from 0.3 m pixels. The lidar cannot resolve singletrack width; it has about 5 points per square metre and gives a singletrack only 1-2 points across.

## Data sources

- Terrain: USGS 3DEP lidar, project CO_Central_and_WesternCO_2016_A16 (flown 2016), original-resolution tiles LD2508-LD2514 x 1596-1602. The tiles are in Colorado State Plane Central coordinates, in US survey feet, at 3 ft pixels. The build warps them to NAD83(2011) UTM 13N metres at 1 m and converts elevations to metres: `course_dem_1m.tif`, 1,882 x 1,879 m, with a 220 m margin around the track.
- Trees: the 2016 lidar point cloud for the same nine tiles, 15 million returns. Canopy height is the highest return per 1 m cell minus the bare-earth DEM (`chm_1m.tif`; the two agree within 13 cm on open ground). A tree is a canopy peak at least 2 m tall that the 2023 aerial's near-infrared confirms as vegetation. That gives 30,294 trees: half under 6.5 m, one in ten over 9 m, the tallest 22 m. Trees are kept at least 2.5 m off the GPS line, and crowns stop 1.2 m short of it, so none sits on the drawn trail. The split into conifers and broadleaf trees is rough here: the Gambel oak draws as conifers too.
- Aerial: USDA NAIP, 7 Sep 2023, 0.3 m, read from Microsoft Planetary Computer because the USGS image service was down (`aerial_course.jpg` at 0.5 m; `naip_0p3.tif` at 0.3 m for the surface reading).
- Surroundings: 3DEP 1/3 arc-second DEM resampled to 30 m, and NAIP 2023 at 12 m, over 36 x 24 km.
- Trail names: OpenStreetMap, © OpenStreetMap contributors, ODbL.

## Files

- `course_viewer.html`: the viewer. `race_info.js` holds everything specific to this race (titles, link, surface table). Data: `course_data.js`, `aerial_data.js`, `background_data.js`, `trees_data.js`, and `lib/` for three.js.
- Build order: `build_course.py`, then `fetch_naip.py`, then `build_background.py`, then `build_trees.py <laz folder>`. Settings are in `race_config.json`.

## Sources

- Race page and schedule: https://coloradomtb.org/race/ (State Championship, Event Details)
- CMC news, 2022 championship and the new trails: https://coloradomtn.edu/news/cmc-news/cmc-spring-valley-to-host-2022-high-school-mountain-bike-championships-in-october/
- USGS National Map: https://apps.nationalmap.gov/downloader/
- NAIP on Microsoft Planetary Computer: https://planetarycomputer.microsoft.com/dataset/naip
- OpenStreetMap: https://www.openstreetmap.org
