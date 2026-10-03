/**************************************************************************
 * Uganda regional rainfall export — CHIRPS daily → monthly, 1990–2025
 * Paste into the Earth Engine Code Editor (code.earthengine.google.com)
 * and press Run. Then start the export from the Tasks tab.
 *
 * Output: uganda_rainfall_by_region_1990_2025.csv, one row per region per month:
 *   region, group, date, month, year, rainfall_mm
 * Same CHIRPS source, period and monthly-sum logic as the national script
 * (uganda_national_rainfall_gee.js). Feeds scripts/regional_pipeline.py and
 * notebooks/02_regional_analysis.ipynb.
 *
 * Regions: Uganda (national, reference), Karamoja, Lake Victoria basin (Uganda
 * part), and Central / Eastern / Northern / Western as an agro-ecological zone
 * stand-in. Permanent open water is masked in every series.
 **************************************************************************/

// ---------------------------------------------------------------- settings
var START_YEAR = 1990;
var END_YEAR   = 2025;
var SCALE      = 5566;          // CHIRPS native resolution (~0.05°)
// CHIRPS is weak over open water (few gauges). Masking permanent water keeps
// the Lake Victoria basin series about rain on land. Applied to every region,
// including the national reference row, so all series stay comparable.
var MASK_WATER = true;

// Optional: your own agro-ecological zones shapefile uploaded as an asset
// (Assets → New → Shape files). Leave '' to use the admin-region fallback.
var AEZ_ASSET  = '';            // e.g. 'users/yourname/uganda_aez'
var AEZ_FIELD  = 'AEZ_NAME';    // attribute that holds the zone name

// ---------------------------------------------------------------- boundaries
var gaul0 = ee.FeatureCollection('FAO/GAUL/2015/level0');
var gaul1 = ee.FeatureCollection('FAO/GAUL/2015/level1');

var uganda = gaul0.filter(ee.Filter.eq('ADM0_NAME', 'Uganda'));
var ugGeom = uganda.geometry();

// 1) Karamoja sub-region. In FAO GAUL 2015, Uganda's level 1 = districts and
//    level 2 = counties. Match at level 1: level 2 has a "Moroto County" in
//    Alebtong District near Lira, which is not in Karamoja.
var KARAMOJA_DISTRICTS = ['Abim', 'Amudat', 'Kaabong', 'Karenga', 'Kotido',
                          'Moroto', 'Nabilatuk', 'Nakapiripirit', 'Napak'];
var ugDistricts = gaul1.filter(ee.Filter.eq('ADM0_NAME', 'Uganda'));
var karamojaDistricts = ugDistricts.filter(ee.Filter.inList('ADM1_NAME', KARAMOJA_DISTRICTS));
print('Uganda districts in GAUL level 1:', ugDistricts.size());
print('Karamoja districts matched (expect 5-7):', karamojaDistricts.size(),
      karamojaDistricts.aggregate_array('ADM1_NAME'));

// Safety net: if fewer than 5 districts match, use a box over north-eastern
// Uganda clipped to the border instead (close enough for rainfall averages).
var karamojaBox = ee.Geometry.Rectangle([33.35, 1.40, 35.05, 4.25]).intersection(ugGeom, 1000);
var karamojaGeom = ee.Geometry(ee.Algorithms.If(
  karamojaDistricts.size().gte(5), karamojaDistricts.geometry().dissolve(1000), karamojaBox));
var karamoja = ee.Feature(karamojaGeom)
  .set({region: 'Karamoja', group: 'Focus region'});

// 2) Lake Victoria basin, Uganda portion. Start at the lake's outlet at
//    Jinja (source of the Nile) and walk upstream through HydroBASINS
//    NEXT_DOWN links: everything upstream of the outlet is the basin.
var HYBAS_LEVEL = 6;
var outlet = ee.Geometry.Point([33.19, 0.42]);
var basins = ee.FeatureCollection('WWF/HydroSHEDS/v1/Basins/hybas_' + HYBAS_LEVEL)
  .filterBounds(ee.Geometry.Rectangle([28, -5, 37, 3]));
var seedIds = basins.filterBounds(outlet).aggregate_array('HYBAS_ID');
var lvIds = ee.List(ee.List.sequence(1, 60).iterate(function (_, acc) {
  acc = ee.List(acc);
  var up = basins.filter(ee.Filter.inList('NEXT_DOWN', acc)).aggregate_array('HYBAS_ID');
  return acc.cat(up).distinct();
}, seedIds));
// Drop the outlet sub-basin itself: it is the Nile reach below Jinja and runs
// north towards Lake Kyoga, which is downstream of Lake Victoria.
lvIds = lvIds.removeAll(seedIds);
var lvAll = basins.filter(ee.Filter.inList('HYBAS_ID', lvIds));
var lvBasin = lvAll.geometry().dissolve(1000);
var lakeVictoria = ee.Feature(lvBasin.intersection(ugGeom, 1000))
  .set({region: 'Lake Victoria basin', group: 'Focus region'});
print('Lake Victoria sub-basins found (expect dozens):', lvIds.size());

// Size checks (km²): Karamoja is about 27,000-28,000. The full Lake Victoria
// basin incl. the lake is roughly 250,000; the Uganda part is a fraction of that.
print('Karamoja area km²:', karamoja.geometry().area(1000).divide(1e6).round());
print('Lake Victoria basin, full, km²:', lvBasin.area(1000).divide(1e6).round());
print('Lake Victoria basin, Uganda part, km²:', lakeVictoria.geometry().area(1000).divide(1e6).round());

// 3) Agro-ecological zones: your asset if provided. Otherwise a stand-in:
//    geoBoundaries level 1 for Uganda, used only if it is the coarse
//    4-region level (Central/Eastern/Northern/Western); else zones are skipped.
var zones;
if (AEZ_ASSET !== '') {
  zones = ee.FeatureCollection(AEZ_ASSET).map(function (f) {
    return ee.Feature(f.geometry().intersection(ugGeom, 1000))
      .set({region: f.get(AEZ_FIELD), group: 'Agro-ecological zone'});
  });
} else {
  var gb1 = ee.FeatureCollection('WM/geoLab/geoBoundaries/600/ADM1')
    .filter(ee.Filter.eq('shapeGroup', 'UGA'));
  print('geoBoundaries UGA level 1 units (stand-in used only if <= 10):', gb1.size(),
        gb1.aggregate_array('shapeName').slice(0, 12));
  var gbRegions = gb1.map(function (f) {
    return ee.Feature(f.geometry())
      .set({region: ee.String(f.get('shapeName')).cat(' region'),
            group: 'Admin region (AEZ stand-in)'});
  });
  zones = ee.FeatureCollection(ee.Algorithms.If(gb1.size().lte(10), gbRegions,
                                                ee.FeatureCollection([])));
}

// National reference, built with the same masking as everything else.
var national = ee.Feature(ugGeom).set({region: 'Uganda (national)', group: 'Reference'});

var regions = ee.FeatureCollection([national, karamoja, lakeVictoria]).merge(zones);
print('Regions to export:', regions.aggregate_array('region'));

// ---------------------------------------------------------------- map check
Map.centerObject(uganda, 6);
Map.addLayer(zones, {color: '999999'}, 'Zones', true, 0.4);
Map.addLayer(ee.FeatureCollection([lakeVictoria]), {color: '1f6fb2'}, 'Lake Victoria basin (UG)');
Map.addLayer(lvAll, {color: '8cc0ec'}, 'Lake Victoria basin (full, check only)', false);
Map.addLayer(ee.FeatureCollection([karamoja]), {color: 'c4572e'}, 'Karamoja');

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

  var stats = img.reduceRegions({
    collection: regions,
    reducer: ee.Reducer.mean(),
    scale: SCALE,
    tileScale: 4
  });

  return stats.map(function (f) {
    return ee.Feature(null, {
      region: f.get('region'),
      group: f.get('group'),
      date: start.format('YYYY-MM'),
      month: start.get('month'),
      year: start.get('year'),
      rainfall_mm: f.get('mean')
    });
  });
})).flatten();

print('Sample rows:', monthly.limit(10));

// ---------------------------------------------------------------- export
Export.table.toDrive({
  collection: monthly,
  description: 'uganda_rainfall_by_region_1990_2025',
  fileNamePrefix: 'uganda_rainfall_by_region_1990_2025',
  fileFormat: 'CSV',
  selectors: ['region', 'group', 'date', 'month', 'year', 'rainfall_mm']
});
