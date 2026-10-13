// race_info.js · v1.1 · 2026-10-13
// Everything in course_viewer.html that belongs to this one race: titles, the public link, and the
// surface table: [from mile, to mile, class (grass / road / two / single), note shown on click,
// optional course width in metres when it differs from the class default].
// Surface read 2026-10-12 from a 24 m strip of the USDA NAIP aerial (7 Sep 2023, 0.3 m, public domain)
// centred on the race GPX; trail names from OpenStreetMap (© OpenStreetMap contributors, ODbL).
// CHANGED: v1.1 miles remapped onto the cleaned GPS line (stops removed, lap 5.61 mi); dirt-road
//   crossing at 1.84 added; course widths per row. v1.0 first surface table.
window.RACE = {
  pageTitle: 'State Championship course',
  title: 'State Championship · CMC Spring Valley',
  subtitle: 'Glenwood Springs CO · Oct 24-25, 2026 · 5.6 mi lap · USGS 1 m lidar (2016) + NAIP aerial (2023)',
  url: 'worldbyjoe.github.io/state-championship-2026',
  kinds: { road: { label: 'Gravel road', width: '~4 m' }, two: { label: 'Double-track', width: '~2-3 m wide dirt' } },
  surface: [
    [0.00, 0.065, 'grass', 'start on the campus field'],
    [0.065, 0.08, 'road', 'paved path crossing', 2.5],
    [0.08, 0.50, 'two', 'wide dirt path up from the field'],
    [0.50, 0.61, 'road', 'gravel road'],
    [0.61, 0.969, 'single', 'Spring Valley Summit Trail'],
    [0.969, 1.059, 'road', 'gravel road'],
    [1.059, 1.837, 'single', 'Dreamer'],
    [1.837, 1.855, 'road', 'crosses a dirt road', 0.9],
    [1.855, 1.97, 'single', 'Dreamer'],
    [1.97, 2.236, 'single', 'through the piñon-juniper'],
    [2.236, 2.679, 'single', "Swoop's Loop"],
    [2.679, 2.939, 'two', 'dirt track beside the solar array'],
    [2.939, 3.249, 'single', "Swoop's Loop"],
    [3.249, 3.528, 'single', 'East Ridge Loop'],
    [3.528, 3.669, 'single', 'East Ridge Loop, wider, about 1.5 m: passing is tight', 1.5],
    [3.669, 4.347, 'single', "Swoop's Loop"],
    [4.347, 4.367, 'road', 'road crossing', 0.9],
    [4.367, 5.126, 'single', "Swoop's Loop through the piñon-juniper"],
    [5.126, 5.222, 'two', 'short double-track'],
    [5.222, 5.362, 'single', 'Spring Valley Summit Trail'],
    [5.362, 5.432, 'two', 'wide dirt down to the field'],
    [5.432, 5.70, 'grass', 'finish on the campus field'],
  ],
  surfaceNote: 'Surface read from the 2023 NAIP aerial (USDA, 0.3 m); trail names from OpenStreetMap.',
};
