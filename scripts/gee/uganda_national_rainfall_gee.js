/**************************************************************************
 * Uganda national rainfall export — CHIRPS daily → monthly, 1990–2025
 * Paste into the Earth Engine Code Editor (code.earthengine.google.com)
 * and press Run. Then start the export from the Tasks tab.
 *
 * Output: uganda_monthly_rainfall.csv, one row per month:
 *   date, month, year, rainfall_mm   (432 rows)
 * rainfall_mm = monthly total of daily CHIRPS rainfall, averaged over Uganda.
 *
 * This produces the input for the national report (Part 1) and
 * notebooks/01_national_analysis.ipynb.
 *
 * MASK_WATER = false matches Part 1 (lakes included, 1,241 mm average).
 * Set it to true to match the national row in the regional run (1,203 mm).
 **************************************************************************/

// ---------------------------------------------------------------- settings
var START_YEAR = 1990;
var END_YEAR   = 2025;
var SCALE      = 5566;          // CHIRPS native resolution (~0.05°)
var MASK_WATER = false;         // true = exclude permanent open water (lakes)

// ---------------------------------------------------------------- boundary
var uganda = ee.FeatureCollection('FAO/GAUL/2015/level0')
  .filter(ee.Filter.eq('ADM0_NAME', 'Uganda'));
var ugGeom = uganda.geometry();

Map.centerObject(uganda, 6);
Map.addLayer(uganda, {color: '16825a'}, 'Uganda');
print('Uganda area km²:', ugGeom.area(1000).divide(1e6).round());

// ---------------------------------------------------------------- rainfall
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').select('precipitation');
var landMask = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('occurrence').unmask(0).lt(50);       // water <50% of the time = land

var months = ee.List.sequence(0, (END_YEAR - START_YEAR + 1) * 12 - 1);

var monthly = ee.FeatureCollection(months.map(function (i) {
  var start = ee.Date.fromYMD(START_YEAR, 1, 1).advance(ee.Number(i), 'month');
  var end   = start.advance(1, 'month');
  var img   = chirps.filterDate(start, end).sum().rename('rainfall_mm');
  img = MASK_WATER ? img.updateMask(landMask) : img;

  var mean = img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: ugGeom,
    scale: SCALE,
    maxPixels: 1e10,
    tileScale: 4
  }).get('rainfall_mm');

  return ee.Feature(null, {
    date: start.format('YYYY-MM'),
    month: start.get('month'),
    year: start.get('year'),
    rainfall_mm: mean
  });
}));

print('Rows (expect 432):', monthly.size());
print('Sample rows:', monthly.limit(12));

// Quick chart to eyeball the series before exporting
print(ui.Chart.feature.byFeature(monthly, 'date', 'rainfall_mm')
  .setOptions({title: 'Uganda monthly rainfall (mm)', legend: {position: 'none'}}));

// ---------------------------------------------------------------- export
Export.table.toDrive({
  collection: monthly,
  description: 'uganda_monthly_rainfall',
  fileNamePrefix: 'uganda_monthly_rainfall',
  fileFormat: 'CSV',
  selectors: ['date', 'month', 'year', 'rainfall_mm']
});
