// race_info.js · v1.0 · 2026-10-12
// Everything in course_viewer.html that belongs to this one race: titles, the public link, and the
// surface table (miles from the start; class grass / road / two / single, optional note shown on click).
// Surface read 2026-10-12 from a 24 m strip of the USDA NAIP aerial (7 Sep 2023, 0.3 m, public domain)
// centred on the race GPX; trail names from OpenStreetMap (© OpenStreetMap contributors, ODbL).
// CHANGED: v1.0 surface table filled from the 2023 aerial (v0.1 was a placeholder).
window.RACE = {
  pageTitle: 'State Championship course',
  title: 'State Championship · CMC Spring Valley',
  subtitle: 'Glenwood Springs CO · Oct 24-25, 2026 · 5.6 mi lap · USGS 1 m lidar (2016) + NAIP aerial (2023)',
  url: 'worldbyjoe.github.io/state-championship-2026',
  kinds: { road: { label: 'Gravel road', width: '~4 m' }, two: { label: 'Double-track', width: '~2-3 m wide dirt' } },
  surface: [
    [0.00, 0.065, 'grass', 'start on the campus field'],
    [0.065, 0.08, 'road', 'paved path crossing'],
    [0.08, 0.50, 'two', 'wide dirt path up from the field'],
    [0.50, 0.61, 'road', 'gravel road'],
    [0.61, 0.97, 'single', 'Spring Valley Summit Trail'],
    [0.97, 1.06, 'road', 'gravel road'],
    [1.06, 1.98, 'single', 'Dreamer'],
    [1.98, 2.26, 'single', 'through the piñon-juniper'],
    [2.26, 2.71, 'single', "Swoop's Loop"],
    [2.71, 2.97, 'two', 'dirt track beside the solar array'],
    [2.97, 3.28, 'single', "Swoop's Loop"],
    [3.28, 3.56, 'single', 'East Ridge Loop'],
    [3.56, 3.70, 'single', 'East Ridge Loop, wider, about 1.5 m: passing is tight'],
    [3.70, 4.38, 'single', "Swoop's Loop"],
    [4.38, 4.40, 'road', 'road crossing'],
    [4.40, 5.16, 'single', "Swoop's Loop through the piñon-juniper"],
    [5.16, 5.26, 'two', 'short double-track'],
    [5.26, 5.40, 'single', 'Spring Valley Summit Trail'],
    [5.40, 5.47, 'two', 'wide dirt down to the field'],
    [5.47, 5.70, 'grass', 'finish on the campus field'],
  ],
  surfaceNote: 'Surface read from the 2023 NAIP aerial (USDA, 0.3 m); trail names from OpenStreetMap.',
};
