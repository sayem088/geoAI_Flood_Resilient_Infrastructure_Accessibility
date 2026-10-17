import requests
import json
import geopandas as gpd
from shapely.geometry import Point
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS03_INFRASTRUCTURE, ensure_dirs
ensure_dirs()
BBOX = '23.66,90.32,23.91,90.52'
QUERY = f'\n[out:json][timeout:90];\n(\n  node["amenity"="water_point"]({BBOX});\n  node["man_made"="water_well"]({BBOX});\n  node["man_made"="water_tap"]({BBOX});\n  node["man_made"="water_works"]({BBOX});\n  node["social_facility"="shelter"]({BBOX});\n  node["amenity"="community_centre"]({BBOX});\n  node["landuse"="landfill"]({BBOX});\n  node["amenity"="waste_disposal"]({BBOX});\n  node["amenity"="waste_transfer_station"]({BBOX});\n  node["amenity"="recycling"]({BBOX});\n);\nout center tags;\n'
ENDPOINTS = ['https://overpass-api.de/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']
HEADERS = {'User-Agent': 'DhakaUrbanResilienceResearch/1.0', 'Accept': 'application/json'}
print('=' * 65)
print('  STEP 1: OSM INFRASTRUCTURE EXTRACTION (OVERPASS API)')
print('=' * 65)
elements = []
for endpoint in ENDPOINTS:
    try:
        res = requests.post(endpoint, data={'data': QUERY}, headers=HEADERS, timeout=60)
        if res.status_code == 200:
            elements = res.json().get('elements', [])
            print(f'[OK] Retrieved {len(elements)} nodes from {endpoint}')
            break
        else:
            print(f'[WARN] {endpoint} → HTTP {res.status_code}, trying next…')
    except Exception as exc:
        print(f'[WARN] {endpoint} → {exc}, trying next…')
if not elements:
    raise RuntimeError('All Overpass endpoints failed. Check your internet connection or try again later.')

def classify_node(tags: dict) -> str:
    amenity = tags.get('amenity', '')
    man_made = tags.get('man_made', '')
    landuse = tags.get('landuse', '')
    soc_fac = tags.get('social_facility', '')
    if amenity in ('water_point',) or man_made in ('water_well', 'water_tap', 'water_works'):
        return 'WASH_DRINKING_WATER'
    if soc_fac == 'shelter' or amenity == 'community_centre':
        return 'EMERGENCY_SHELTER'
    if landuse == 'landfill' or amenity in ('waste_disposal', 'waste_transfer_station', 'recycling'):
        return 'WASTE_CONTAMINATION_SITE'
    return 'WASH_DRINKING_WATER'
records = []
for elem in elements:
    lat = elem.get('lat') or elem.get('center', {}).get('lat')
    lon = elem.get('lon') or elem.get('center', {}).get('lon')
    if lat is None or lon is None:
        continue
    tags = elem.get('tags', {})
    records.append({'geometry': Point(lon, lat), 'category': classify_node(tags), 'osm_id': elem.get('id'), 'name': tags.get('name', '')})
gdf = gpd.GeoDataFrame(records, crs='EPSG:4326').to_crs(epsg=32646)
unknown_mask = gdf['category'] == 'UNKNOWN'
if unknown_mask.any():
    print(f'  Reclassifying {unknown_mask.sum()} UNKNOWN → WASH_DRINKING_WATER')
    gdf.loc[unknown_mask, 'category'] = 'WASH_DRINKING_WATER'
print('\n  Category breakdown:')
print(gdf['category'].value_counts().to_string())
gdf.to_file(str(DS03_INFRASTRUCTURE), driver='GeoJSON')
print(f'\n[SUCCESS] Saved {len(gdf)} infrastructure nodes → {DS03_INFRASTRUCTURE}')
