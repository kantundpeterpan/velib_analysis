######################
# IMPORTS + CONFIG   #
######################
import geopandas as gpd
import os
import pyproj
pyproj.datadir.set_data_dir("/home/kantundpeterpan/miniconda3/envs/velib/share/proj")
import sqlite3
import pandas as pd
import rasterio
from pathlib import Path
from rasterstats import point_query
from pyathena import connect 
import json
# from gbfs

__here__ = Path(__file__).parent

import os 

aws_access_key_id = os.getenv("aws_access_key_id".upper())
aws_secret_access_key = os.getenv("aws_secret_access_key".upper())

if aws_access_key_id is None or aws_secret_access_key is None:

    with open("./.creds/key.json", "r") as f:
        creds = json.loads(f.read())
        
    db = connect(
        s3_staging_dir='s3://gbfsbikesbucket', 
        region_name = 'eu-central-1',
        **creds
    )
    
else:
    db = connect(
        s3_staging_dir='s3://gbfsbikesbucket', 
        region_name = 'eu-central-1',
        aws_access_key_id = aws_access_key_id,
        aws_secret_access_key =aws_secret_access_key
    )

dataset_name = "Paris"

# Pull town info for Ile-de-France
## Population data

def load_towns():
    #load from IDF data repo, keep only most recent data
    town_pop_idf = pd.read_csv('https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/populations-legales-communes-et-arrondissements-municipaux-millesime-ile-de-fran/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B', sep = ';').query("`Année de recensement` == 2018")
    
    col_map = {col:'_' + str(i) for col, i in zip(town_pop_idf, range(town_pop_idf.shape[-1]))}
    town_pop_idf.columns = town_pop_idf.columns.map(col_map)
    
    ## Town and district data
    towns = gpd.read_file('https://www.data.gouv.fr/fr/datasets/r/5cd27d86-4859-40dc-b029-a215219eedf9',
                encoding = 'utf-1').to_crs('EPSG:2154')
    
    towns['insee'] = towns['insee'].astype(int)
    towns = towns.merge(town_pop_idf[['_2', '_6']], left_on = 'insee', right_on = '_2', how = 'inner').rename({'_2':'insee_town_pop', '_6':'pop_tot'}, axis = 1)

    return towns

def load_bike_stations():
    global towns

    ###

    
    
    ###
    s = pd.read_sql(f'SELECT * from {dataset_name.lower()}.station_info', db)\
            .set_index('station_id', drop = True).sort_index()
    
    velo_stations = gpd.GeoDataFrame(
        s, 
        geometry = gpd.points_from_xy(
            s.lon, s.lat,
        crs = 'EPSG:4326'
        )
    ).to_crs('EPSG:2154')

    # find town_id for given station
    velo_stations['town_id'] = velo_stations.geometry\
            .apply(lambda s: towns.geometry.contains(s).idxmax())

    # get town name for each town id
    velo_stations['town'] = velo_stations.town_id\
            .apply(lambda s:towns.loc[s].nomcom.replace(' Arrondissement', ''))

    # dem_data = rasterio.open(__here__ / '../../data/elevation_data/paris/idf.tif')
    # dem_array = dem_data.read(1)

    # velo_stations_geocoord = velo_stations[['geometry']].to_crs('EPSG:4326')
    
    # velo_stations['elevation'] = dem_array[
    # dem_data.index(
    #     velo_stations_geocoord.geometry.x.values,
    #     velo_stations_geocoord.geometry.y.values
    # )
    # ]


    velo_stations_geocoord = velo_stations[['geometry']].to_crs('EPSG:4326')

    # Use point_query from rasterstats to get elevation values
    velo_stations['elevation'] = point_query(
        velo_stations_geocoord.geometry,
        __here__ / '../../data/elevation_data/paris/idf.tif'
    )

    velo_stations['zero_cap'] = velo_stations.capacity.eq(0)
    
    return velo_stations
    
def load_train_stations():
    train_stations = gpd.read_file('https://www.data.gouv.fr/fr/datasets/r/e2679f65-0321-403a-8fe6-e51dbcbce309')\
        .drop(["picto", "geo_point_2d", "x", "y"], axis = 1)\
        .query("idf == 1").to_crs('EPSG:2154')

    return train_stations

def compute_nearest_train_station():
    global train_stations, velo_stations #BAD BAD BAD

    distmat = velo_stations.geometry.apply(lambda g:train_stations.geometry.distance(g))
    
    #get index of nearest train station, references train_stations table
    velo_stations['nearest_train'] = distmat.apply(lambda r: r.idxmin(), axis = 1)


    #get distance to nearest train station
    velo_stations['min_dist_train'] = distmat.apply(lambda r: r.loc[r.idxmin()], axis = 1)
    
    #remove train stations that are further away than the maxmial minimum distance
    train_stations = train_stations.loc[velo_stations.nearest_train.values]

towns = load_towns()
velo_stations = load_bike_stations()
train_stations = load_train_stations()
compute_nearest_train_station()

