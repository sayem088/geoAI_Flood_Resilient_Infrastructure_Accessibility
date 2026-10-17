var dhaka_bbox = ee.Geometry.BBox(90.15, 23.55, 90.65, 24.05);
Map.centerObject(dhaka_bbox, 11);
Map.addLayer(dhaka_bbox, {color: 'red'}, 'Dhaka BBox', false);

var dem = ee.ImageCollection('COPERNICUS/DEM/GLO30_COG')
  .select('DEM')
  .mosaic()
  .clip(dhaka_bbox)
  .rename('elevation');

var slope = ee.Terrain.slope(dem).rename('slope');

var slopeRad = slope.multiply(Math.PI / 180.0);
var tanSlope = slopeRad.max(0.001).tan();
var twi = tanSlope.pow(-1).log().rename('twi');

var dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD_V1')
  .filterBounds(dhaka_bbox)
  .filterDate('2024-01-01', '2024-12-31')
  .select('built')
  .mean()
  .clip(dhaka_bbox)
  .rename('impervious_fraction');

var s1_dry = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(dhaka_bbox)
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filterDate('2024-01-01', '2024-03-31')
  .select(['VV', 'VH'])
  .median()
  .clip(dhaka_bbox);

var s1_flood = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(dhaka_bbox)
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filterDate('2024-07-01', '2024-09-30')
  .select(['VV', 'VH'])
  .median()
  .clip(dhaka_bbox);

var s1_dry_clean = s1_dry.focal_median(50, 'circle', 'meters');
var s1_flood_clean = s1_flood.focal_median(50, 'circle', 'meters');

var vh_diff = s1_flood_clean.select('VH').subtract(s1_dry_clean.select('VH')).rename('vh_diff');

var flood_mask = s1_flood_clean.select('VH').lt(-20.0)
  .or(vh_diff.lt(-2.5))
  .rename('flood_ground_truth');

var stack = ee.Image.cat([
  flood_mask,
  dem,
  slope,
  twi,
  dw,
  vh_diff
]);

Map.addLayer(dem, {min: 0, max: 25, palette: ['blue', 'yellow', 'brown']}, 'Copernicus Elevation');
Map.addLayer(flood_mask, {min: 0, max: 1, palette: ['white', 'blue']}, 'Sentinel-1 Flood Ground Truth');

Export.image.toDrive({
  image: stack,
  description: 'dhaka_gee_flood_covariates_30m',
  folder: 'Research_SCA_Data',
  fileNamePrefix: 'dhaka_gee_flood_covariates_30m',
  region: dhaka_bbox,
  scale: 30,
  crs: 'EPSG:32646',
  maxPixels: 1e9
});

print('Script loaded successfully. Click "Run", then go to the Tasks tab on the right to click "Run" for the export!');
