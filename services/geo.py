import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from core.config import ALLOWED_MCCS

def filter_towers_by_region(csv_path: str, output_path: str = None) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype={'mcc': 'Int64', 'mnc': 'Int64'})
    filtered_df = df[df['mcc'].isin(ALLOWED_MCCS)].copy()
    if output_path:
        filtered_df.to_csv(output_path, index=False)
    return filtered_df

def towers_to_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry)
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf
