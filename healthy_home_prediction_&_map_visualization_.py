# Healthy Home Prediction & Map Visalization

# 1.Set Environment & Libraries

# # Set an environment for geopandas & other geo-related libraries
# # 
# %%time
# # 
# # Important library for many geopython libraries
# !apt install gdal-bin python-gdal python3-gdal
# # Install rtree - Geopandas requirment
# !apt install python3-rtree
# # Install Geopandas
# !pip install git+git://github.com/geopandas/geopandas.git
# # Install descartes - Geopandas requirment
# !pip install descartes


# # Geo-related libraries
# !pip install geopandas
# !pip install osmnx
# !pip install contextily
# !pip install folium
# !pip install plotly_express
# !pip install geofeather


# # Others
# !pip install matplotlib==3.1.3


# Data manipulation libraries
import os
import pandas as pd
import numpy as np


# Geo-related libraries
import geopandas as gpd
import osmnx as ox
import folium
from folium.plugins import HeatMap
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import contextily as ctx
import geofeather
from geopandas import GeoDataFrame
from shapely.geometry import Point
from shapely import wkt
from shapely.geometry import Point, MultiPoint
from shapely.ops import nearest_points
from shapely import wkt


# Visualization
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


# Timer
from tqdm import tqdm, tqdm_notebook


# Regression
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor


# Model support functions
from sklearn import model_selection
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV
from scipy.stats import uniform
from sklearn.preprocessing import StandardScaler
from pprint import pprint
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 2.Load Data
# Read air pollutant & health info
df_1 = pd.read_csv("Home_n_Map.csv")
df_1.head(5)

# Check a null counts and data types
df_1.info()

# Mapping the data points
# convert pandas df to geopandas df (based on latitude & longitude)

gpd_1_degree = gpd.GeoDataFrame(df_1, geometry=gpd.points_from_xy(df_1.Longitude, df_1.Latitude), crs={'init' :'epsg:4326'})
gpd_1_degree.info()

# Mapping the data points
# draw a figure
fig, ax = plt.subplots(figsize=(12, 10))
gpd_1_degree.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="black",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
# fig.savefig('output/file_name', dpi = 400, transparent = True)

# 3.Data Cleaning
# Check dataframe
df_1.head(2)

# Rename
df_1 = df_1.rename(columns={'NO value': 'NO'})
df_1 = df_1.rename(columns={'NO2 value': 'NO2'})
df_1 = df_1.rename(columns={'PM2p5 value': 'PM2p5'})
# EDF_points = EDF_points.rename(index=str, columns={"NO Value": "NO", "NO2 Value": "NO2", "PM2p5 Value": "PM2p5"})

# Drop Irrelevant Feature
# count unique values for each feature - do this step bf missing data， preveting unnecessary filters
df_1.nunique()

# Drop columns (features)
df_1_drop = df_1.drop(['state', 'county', 'tract_name', 'GEOID'], axis=1)
df_1_drop.head(2)

# Deal with Missing Data 

# Size of data
df_1_drop.shape # row x col

# Check missing data
print('Sum of N/A values', df_1_drop.isnull().sum())

# handling the missing data - drop all N/A, (avg/front fill/back fill)
df_1_miss = df_1_drop.dropna(axis=0, subset=['zone', 'wind', 'temp'])
df_1_miss.tail(2)

# Reset index
df_1_miss = df_1_miss.reset_index()
# Check info
df_1_miss.info()
# Remove index
df_1_miss = df_1_miss.drop(['index'], axis=1)

# Duplicated values

# Size of data
df_1_miss.shape # row x col

# Extract duplicated row
df_1_miss[df_1_miss.duplicated()]

# Remove duplicated row
# Keep first, last or remove all
df_1_dup = df_1_miss.drop_duplicates()
df_1_dup.tail(2)

# Reset index and check
df_1_dup.reset_index(inplace=True)
df_1_dup[df_1_dup.duplicated()]

# Outliers
df_1_out = df_1_dup.copy()

# Checking outliers
_,axss = plt.subplots(2,3, figsize=[20,10])  # create a 2x3 matrix = 6 figures
sns.boxplot(y ='NO', data=df_1_out, ax=axss[0, 0])
sns.boxplot(y ='NO2', data=df_1_out, ax=axss[0, 1])
sns.boxplot(y ='PM2p5', data=df_1_out, ax=axss[0, 2])
sns.boxplot(y ='pop_den', data=df_1_out, ax=axss[1][0])
sns.boxplot(y ='wind', data=df_1_out, ax=axss[1][1])
sns.boxplot(y ='temp', data=df_1_out, ax=axss[1][2])

# knowledge for NO: similar effect for high levels
df_1_out.loc[df_1_out['NO'] > 200, 'NO'] = 200

# 4. Feature Engineering: use geography data of Oakland City
Oakland_poly = ox.geocode_to_gdf('Oakland, California')
Oakland_poly
Oakland_poly.plot()

# Convert to geo df
df_1_out['geometry'] = df_1_out['geometry'].apply(lambda x: Point(map(float, x.lstrip('POINT (').rstrip(')').split())))
gpd_1_degree = gpd.GeoDataFrame(df_1_out, geometry = df_1_out['geometry'], crs={'init' :'epsg:4326'})
Oakland_poly.crs, gpd_1_degree.crs

# join the dataset health with the Oakland polygon grid
gpd_1_city = gpd.sjoin(gpd_1_degree, Oakland_poly, how="inner", op="intersects")
gpd_1_city.head(2)

# drop unnecessary cols
print(gpd_1_city.nunique())
gpd_1_city = gpd_1_city.drop(['index_right', 'bbox_east', 'bbox_north', 'bbox_south', 'bbox_west'], axis=1)

# Identify City structure
# Streets

# street data (roads and intersections) for entire city
oak_streets = ox.graph_from_place('Oakland, California', network_type = 'drive')
nodes, edges = ox.graph_to_gdfs(oak_streets)

# nodes.head(1)
# edges.head(1)
# edges.plot()

# Identify roads
oakland_rds = edges.copy()
print(oakland_rds['highway'].value_counts())
print (oakland_rds.shape)

# Clean up road names
# remove '_link' in xxx_link & add it to xxx
# (e.g., motorway_link is added on motorway )
oakland_rds['highway'] = oakland_rds['highway'].str.replace('_link', '')

# 'trunk'  -->  'secondary'
oakland_rds['highway'] = np.where(oakland_rds['highway'] == 'trunk', 'secondary', oakland_rds['highway'])

# 'living_street' --> 'residential'
oakland_rds['highway'] = np.where(oakland_rds['highway'] == 'living_street', 'residential', oakland_rds['highway'])

print(oakland_rds['highway'].value_counts())

sns.countplot(oakland_rds['highway'])

# Map them out
# separate as subsets of roadtypes
oakland_highways = oakland_rds[oakland_rds.highway == 'motorway']
oakland_primary = oakland_rds[oakland_rds.highway == 'primary']
oakland_secondary = oakland_rds[oakland_rds.highway == 'secondary']
oakland_tertiary = oakland_rds[oakland_rds.highway == 'tertiary']
oakland_resid = oakland_rds[oakland_rds.highway == 'residential']

oakland_highways.crs

# Highway
fig, ax = plt.subplots(figsize=(12, 10))
oakland_highways.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="red",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# Primary road
fig, ax = plt.subplots(figsize=(12, 10))
oakland_primary.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="blue",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# Secondary road
fig, ax = plt.subplots(figsize=(12, 10))
oakland_secondary.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="green",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# Primary & Secondary
fig, ax = plt.subplots(figsize=(12, 10))
oakland_primary.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="blue",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
oakland_secondary.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="green",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );

ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# Tertiary road
fig, ax = plt.subplots(figsize=(12, 10))
oakland_tertiary.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="purple",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

gpd_1_city.crs

# Now calculate the distance from the road
# Convert geometry from degree to meter
gpd_1_city_utm = gpd_1_city.to_crs({'init': 'epsg:32610'}).copy()
highway_utm = oakland_highways.to_crs({'init': 'epsg:32610'}).copy()
primary_utm = oakland_primary.to_crs({'init': 'epsg:32610'}).copy()
secondary_utm = oakland_secondary.to_crs({'init': 'epsg:32610'}).copy()
tertiary_utm = oakland_tertiary.to_crs({'init': 'epsg:32610'}).copy()

# UDF
def distance_to_roadway(gps, roadway):
    '''Calculate distance from GPS point to nearest road line polygon'''
    dists = []
    for i in roadway.geometry:
        dists.append(i.distance(gps))
    return(np.min(dists))

# Calculate distance to nearest major roadway
gpd_1_city['closest_highway'] = gpd_1_city_utm['geometry'].apply(distance_to_roadway, roadway = highway_utm)
gpd_1_city['closest_primary'] = gpd_1_city_utm['geometry'].apply(distance_to_roadway, roadway = primary_utm)
gpd_1_city['closest_secondary'] = gpd_1_city_utm['geometry'].apply(distance_to_roadway, roadway = secondary_utm)
gpd_1_city['closest_tertiary'] = gpd_1_city_utm['geometry'].apply(distance_to_roadway, roadway = tertiary_utm)

gpd_1_city.head(2)

# traffic signal & stop sign
# Identify traffic signals & stop signs
nodes['highway'].value_counts()
nodes.head(2)
nodes.crs

# Map them out
trafic_signals = nodes[nodes['highway'] == 'traffic_signals']
stop_cross = nodes[nodes['highway'] == 'stop']

# Traffic signal: blue
# Stop sign: red
fig, ax = plt.subplots(figsize=(12, 10))
trafic_signals.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="blue",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
stop_cross.to_crs(epsg=3857).plot(ax = ax,
                figsize=(12,12),
                markersize=40,
               color="orangered",
               edgecolor="white",
               alpha=0.8,
               marker="o"
            );
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# Convert geometry from degree to meter
traffic_sig_utm = trafic_signals.to_crs({'init': 'epsg:32610'}).copy()
stop_sign_utm = stop_cross.to_crs({'init': 'epsg:32610'}).copy()

# set UDF
def nearest_intersection(gps, intersections):
    ''' Calculates distance from GPS point to nearest intersection'''
    closest_point = nearest_points(gps, MultiPoint(intersections.values))[1]
    return(gps.distance(closest_point))

# tqdm.pandas() # show progress bar
# gpd_1_city['trafic_signal_dist'] = gpd_1_city_utm['geometry'].progress_apply(nearest_intersection, intersections = traffic_sig_utm['geometry'])
gpd_1_city['trafic_signal_dist'] = gpd_1_city_utm['geometry'].apply(nearest_intersection, intersections = traffic_sig_utm['geometry'])

# Calculate distance to nearest traffic signal
gpd_1_city['stop_sign_dist'] = gpd_1_city_utm['geometry'].apply(nearest_intersection, intersections = stop_sign_utm['geometry'])

## Category Encoding

gpd_1_city.head(2)

zone = gpd_1_city['zone']
road_type = gpd_1_city['road_type']

# One-hot encoding: convert category features to numerical features（0 & 1） - spliting into diff columns
gpd_1_city = pd.get_dummies(gpd_1_city, columns=['road_type'], drop_first=False)      # drop_first=False: do not remove a lable to reduce multicollision
gpd_1_city = pd.get_dummies(gpd_1_city, columns=['zone'], drop_first=False)

gpd_1_city.head(2)

# Merge them back - for visualization
# axis = 1: rows invariant，but features increased
gpd_1_city = pd.concat([gpd_1_city, zone], axis = 1)
gpd_1_city = pd.concat([gpd_1_city, road_type], axis = 1)

gpd_1_city.head(2)

# Data Preparation

gpd_1_city.info()

# drop
# Drop features
gpd_1_city = gpd_1_city.drop(['index', 'Pt_CANCR'], axis=1)

# health conversion

# if df['Respiratory_HI'] contains 'high', replace "high" to "3" and save into df['Respiratory_HI']
gpd_1_city['Respiratory_HI'] = np.where(gpd_1_city['Respiratory_HI'].str.contains('high'), '3', gpd_1_city['Respiratory_HI'])

# if df['Respiratory_HI'] contains 'moderate', replace "high" to "2" and save into df['Respiratory_HI']
gpd_1_city['Respiratory_HI'] = np.where(gpd_1_city['Respiratory_HI'].str.contains('moderate'), '2', gpd_1_city['Respiratory_HI'])

# if df['Respiratory_HI'] contains 'low', replace "high" to "1" and save into df['Respiratory_HI']
gpd_1_city['Respiratory_HI'] = np.where(gpd_1_city['Respiratory_HI'].str.contains('low'), '1', gpd_1_city['Respiratory_HI'])

# convert object to float
gpd_1_city["Respiratory_HI"] = gpd_1_city.Respiratory_HI.astype(float)

gpd_1_city.head(3)
# gpd_1_city.Respiratory_HI.value_counts()

gpd_1_city.zone.value_counts()

gpd_1_city.info()

# Numerical & Categorical
# Numerical Features
numerical = ['NO', 'NO2', 'PM2p5', 'pop_den', 'wind', 'temp', 'closest_highway', 'closest_primary', 'closest_secondary', 'closest_tertiary',
             'trafic_signal_dist', 'stop_sign_dist', 'road_type_motorway', 'road_type_primary', 'road_type_residential', 'road_type_secondary', 'road_type_tertiary',
             'road_type_unclassified', 'zone_commercial', 'zone_industrial', 'zone_mixed', 'zone_open_space', 'zone_residential', 'Longitude', 'Latitude', 'Respiratory_HI']

# Categorical Features
categorical = ['geometry', 'zone', 'road_type']

# 5.Data Visualization

df_vis = gpd_1_city.copy()

## Correlation Matrix

f, ax = plt.subplots(figsize= [20,15])
sns.heatmap(df_vis[numerical].corr(), annot=True, fmt=".2f", ax=ax, cmap = "magma" )
ax.set_title("Correlation Matrix", fontsize=20)
plt.show()

Corr = pd.DataFrame(df_vis[numerical].corr()['Respiratory_HI'].sort_values(ascending=False))
Corr = Corr.iloc[1:,:]
Corr.columns=['Target Correlation']
Corr

g0 = sns.barplot(x="Target Correlation", y=Corr.index, data=Corr)
g0.figure.set_size_inches(12, 9)

gpd_1_vis = gpd_1_city.copy()

# Plot the overall heatmap
plt.figure(figsize = (11, 10))
plt.scatter(gpd_1_vis.Longitude, gpd_1_vis.Latitude, s=5, c = gpd_1_vis.NO2)
plt.colorbar(); plt.xlabel('Longitude', fontsize=18); plt.ylabel('Latitude', fontsize=18)

plt.figure(figsize = (11, 10))
plt.scatter(gpd_1_vis.Longitude, gpd_1_vis.Latitude, s=5, c = gpd_1_vis.PM2p5, cmap='inferno')
plt.colorbar(); plt.xlabel('Longitude', fontsize=18); plt.ylabel('Latitude', fontsize=18)

# boxplot - roads
plt.figure(figsize=(20,4))
sns.countplot(x = 'road_type', data = df_vis);

# Road type & health
plt.figure(figsize=(20,4))
sns.countplot(x = 'road_type', hue = df_vis['Respiratory_HI'], data = df_vis);

# NO on different road types
plt.figure(figsize=(20,4))
sns.boxplot(x = df_vis['road_type'], y = df_vis['NO']);

# NO2 on different road types
plt.figure(figsize=(20,4))
sns.boxplot(x = df_vis['road_type'], y = df_vis['NO2']);

# PM2.5 on different road types
plt.figure(figsize=(20,4))
sns.boxplot(x = df_vis['road_type'], y = df_vis['PM2p5']);

# boxplot-zones
plt.figure(figsize=(20,4))
sns.countplot(x = 'zone', data = df_vis);

# NO in different zones
plt.figure(figsize=(20,4))
sns.boxplot(x = df_vis['zone'], y = df_vis['NO']);

# NO2 in different zones
plt.figure(figsize=(20,4))
sns.boxplot(x = df_vis['zone'], y = df_vis['NO2']);

# PM2.5 in different zones
plt.figure(figsize=(20,4))
sns.boxplot(x = df_vis['zone'], y = df_vis['PM2p5']);

# NO2 in different zone & health
plt.figure(figsize=(20,4))
sns.boxplot(x = df_vis['zone'], y = df_vis['NO2'], hue = df_vis['Respiratory_HI']);

# distance
# PM2p5
plt.figure(figsize=(12, 5.5))
plt.scatter(df_vis['closest_highway'], df_vis['PM2p5'], s=3)
plt.ylim(10, 45)
plt.tick_params(labelsize=16)
plt.xlabel('Distance to Major Highway (m)', fontsize=18); plt.ylabel('PM2.5 (ug/m3)', fontsize=20)
# plt.savefig('highway_distance.png', format='png', dpi=300)

# save engineered dataset
df_vis.to_file('/content/drive/MyDrive/Colab Notebooks/model_data', driver='GeoJSON')

# 6.Model
# We build a model for No2, NO and PM2.5 here, since they are common factors that cause lung diseases, as well as other various diseases that harm the public.

df_model = gpd.read_file('/content/drive/MyDrive/Colab Notebooks/model_data')

def abline(slope, intercept):
    """Plot a line from slope and intercept"""
    axes = plt.gca()
    x_vals = np.array(axes.get_xlim())
    y_vals = intercept + slope * x_vals
    plt.plot(x_vals, y_vals, '-', color='black')


def pred_summary(pred, ytest, limit = 200):
    """Plotting for test set predictions"""
    df = pd.DataFrame({"Predicted": pred, "Actual": ytest})
    sns.scatterplot(x="Predicted", y="Actual", data=df)
    abline(1, 0) #1-1 line
    plt.ylim(0, limit); plt.xlim(0, limit)
    plt.tick_params(labelsize=18)

    print('RMSE', np.sqrt(mean_squared_error(ytest, pred)))
    print('R2', r2_score(ytest, pred))



def plot_corr(df, size=10, MI = False):
    '''Function plots a graphical correlation matrix for each pair of columns in the dataframe.

    Input:
        df: pandas DataFrame
        size: vertical and horizontal size of the plot'''
    if MI == False:
        corr = df.corr()
    else:
        K = df.shape[1]
        corr = np.empty((K, K), dtype=float)

        for i, ac in enumerate(X.columns):
            for j, bc in enumerate(X.columns):
                MI = mutual_information(X.loc[:, ac], X.loc[:, bc], bins=10, normalize=True)
                corr[i, j] = MI

    fig, ax = plt.subplots(figsize=(size, size))
    ax.matshow(corr)
    plt.xticks(range(len(corr.columns)), corr.columns);
    plt.yticks(range(len(corr.columns)), corr.columns);


# Feature selection

df_model[numerical].columns

X = df_model[numerical].drop(['Respiratory_HI', 'Longitude','Latitude', 'road_type_unclassified','NO', 'NO2', 'PM2p5'], axis=1)
X.columns

# Model Selection
# Train-Test Split & Feature Scaling

# NO
y_NO = df_model['NO']
X_train_NO, X_test_NO, y_train_NO, y_test_NO = model_selection.train_test_split(X, y_NO, test_size=0.25, random_state= 1)
print('training data has ' + str(X_train_NO.shape[0]) + ' observation with ' + str(X_train_NO.shape[1]) + ' features')
print('test data has ' + str(X_test_NO.shape[0]) + ' observation with ' + str(X_test_NO.shape[1]) + ' features')
index = X_train_NO.index

# Feature Scaling
scaler = StandardScaler()
scaler.fit(X_train_NO)
X_train_NO = scaler.transform(X_train_NO)
X_test_NO = scaler.transform(X_test_NO)

# NO2
y_NO2 = df_model['NO2']
X_train_NO2, X_test_NO2, y_train_NO2, y_test_NO2 = model_selection.train_test_split(X, y_NO2, test_size=0.25, random_state= 1)
index = X_train_NO2.index

# Feature Scaling
scaler = StandardScaler()
scaler.fit(X_train_NO2)
X_train_NO2 = scaler.transform(X_train_NO2)
X_test_NO2 = scaler.transform(X_test_NO2)

# PM2.5
y_PM = df_model['PM2p5']
X_train_PM, X_test_PM, y_train_PM, y_test_PM = model_selection.train_test_split(X, y_PM, test_size=0.25, random_state= 1)
index = X_train_PM.index

# Feature Scaling
scaler = StandardScaler()
scaler.fit(X_train_PM)
X_train_PM = scaler.transform(X_train_PM)
X_test_PM = scaler.transform(X_test_PM)

# NO2
# ensemble learning - Bagging

# Use the same random forest gridsearch as above
from sklearn.ensemble import RandomForestRegressor
forest = RandomForestRegressor(n_jobs=2)

params = {'max_features': [6, 8, 10],
          'n_estimators': [100, 150, 200]}

forest_grid_no2 = GridSearchCV(forest, params, cv=5, scoring = 'neg_mean_squared_error')
forest_grid_no2.fit(X_train_NO2, y_train_NO2)

# Best estimator
forest_grid_no2.best_estimator_

fig = plt.figure(figsize=(9,6))
forest_out_no2 = forest_grid_no2.predict(X_test_NO2)
pred_summary(forest_out_no2, y_test_NO2, limit=50)
plt.xlabel('Predicted NO$_2$', fontsize = 18); plt.ylabel('Observed NO$_2$', fontsize=18)

FI_rf = pd.DataFrame(forest_grid_no2.best_estimator_.feature_importances_, index=X.columns, columns=['Feature Importance (RF)'])
FI_rf = FI_rf.sort_values(by='Feature Importance (RF)',ascending=False)
FI_rf # major factor identification

# ensemble learning - Boosting
gb_forest = GradientBoostingRegressor()

params = {'max_features': [6, 8, 10],
          'learning_rate': [0.05, 0.1, 0.5],
          'n_estimators': [100, 150, 200]}

gb_forest_grid_no2 = GridSearchCV(gb_forest, params, cv=5, scoring = 'neg_mean_squared_error')
gb_forest_grid_no2.fit(X_train_NO2, y_train_NO2)

# Best estimator
gb_forest_grid_no2.best_estimator_

fig = plt.figure(figsize=(9,6))
gb_forest_out_no2 = gb_forest_grid_no2.predict(X_test_NO2)
pred_summary(gb_forest_out_no2, y_test_NO2, limit=50)
plt.xlabel('Predicted NO$_2$', fontsize = 18); plt.ylabel('Observed NO$_2$', fontsize=18)

FI_gb = pd.DataFrame(gb_forest_grid_no2.best_estimator_.feature_importances_, index=X.columns, columns=['Feature Importance (GB)'])
FI_gb = FI_gb.sort_values(by='Feature Importance (GB)',ascending=False)
FI_gb

g2 = sns.barplot(x="Feature Importance (GB)", y=FI_gb.index, data=FI_gb)
g2.figure.set_size_inches(12, 9)

# permutation Importance

# Current paramters
grid_search_best_no2 = forest_grid_no2.best_estimator_
pprint(grid_search_best_no2.get_params())

# Permutation Importance
PI_no2 = permutation_importance(grid_search_best_no2, X_test_NO2, y_test_NO2, n_repeats=5, random_state=1)

PI_res = pd.DataFrame(data=np.transpose([PI_no2['importances_mean'],PI_no2['importances_std']]),
             index = X.columns,columns=['PI_mean','PI_std'])
PI_res = PI_res.sort_values(by='PI_mean',ascending=False)
PI_res

g1 = sns.barplot(x="PI_mean", y=PI_res.index, data=PI_res)
g1.figure.set_size_inches(12, 9)

# result summary

summary_0 = pd.DataFrame({'Random Forest':list(FI_rf.index),
              'Gradient Boost':list(FI_gb.index),
               'Permutation Importance':list(PI_res.index)})
summary_0

# NO

# Ensemble learning - Bagging
forest = RandomForestRegressor(n_jobs=2)

params = {'max_features': [6, 8, 10],
          'n_estimators': [150, 200]}

forest_grid = GridSearchCV(forest, params, cv=5, scoring = 'neg_mean_squared_error')
forest_grid.fit(X_train_NO, y_train_NO)

# Best estimator
forest_grid.best_estimator_

forest_NO = forest_grid.predict(X_test_NO)
pred_summary(forest_NO, y_test_NO, limit=110)
plt.xlabel('Predicted NO', fontsize = 18); plt.ylabel('Observed NO', fontsize=18)

FI_rf = pd.DataFrame(forest_grid_no.best_estimator_.feature_importances_, index=X.columns, columns=['Feature Importance (RF)'])
FI_rf = FI_rf.sort_values(by='Feature Importance (RF)',ascending=False)
FI_rf # major factor identification

features = X.columns
importance = forest_grid.best_estimator_.feature_importances_
indices = np.argsort(importance)
plt.figure(figsize=(5, 7))
plt.title("Feature importances (Random Forest)", fontsize = 18)
plt.barh(features[indices], importance[indices],
       color="r",  align="center")
plt.tick_params(labelsize=14);

# Ensemble learning - Boosting
gb_forest = GradientBoostingRegressor()

params = {'max_features': [6, 8, 10],
          'learning_rate': [0.05, 0.1, 0.5],
          'n_estimators': [100, 150, 200]}

gb_forest_grid_no = GridSearchCV(gb_forest, params, cv=5, scoring = 'neg_mean_squared_error')
gb_forest_grid_no.fit(X_train_NO, y_train_NO2)

# Best estimator
gb_forest_grid_no.best_estimator_

fig = plt.figure(figsize=(9,6))
gb_forest_out_no = gb_forest_grid_no.predict(X_test_NO)
pred_summary(gb_forest_out_no, y_test_NO, limit=50)
plt.xlabel('Predicted NO', fontsize = 18); plt.ylabel('Observed NO', fontsize=18)

FI_gb = pd.DataFrame(gb_forest_grid_no.best_estimator_.feature_importances_, index=X.columns, columns=['Feature Importance (GB)'])
FI_gb = FI_gb.sort_values(by='Feature Importance (GB)',ascending=False)
FI_gb

g2 = sns.barplot(x="Feature Importance (GB)", y=FI_gb.index, data=FI_gb)
g2.figure.set_size_inches(12, 9)

# permutation importance
# Current paramters
grid_search_best_no = forest_grid_no.best_estimator_
pprint(grid_search_best_no.get_params())

# Permutation Importance
PI_no = permutation_importance(grid_search_best_no, X_test_NO, y_test_NO, n_repeats=5, random_state=1)

PI_res = pd.DataFrame(data=np.transpose([PI_no['importances_mean'],PI_no['importances_std']]),
             index = X.columns,columns=['PI_mean','PI_std'])
PI_res = PI_res.sort_values(by='PI_mean',ascending=False)
PI_res

# result summary
summary_1 = pd.DataFrame({'Random Forest':list(FI_rf.index),
              'Gradient Boost':list(FI_gb.index),
               'Permutation Importance':list(PI_res.index)})
summary_1

# PM2.5

# Ensemble learning - Bagging
forest = RandomForestRegressor(n_jobs=2)

params = {'max_features': [6, 8, 10],
          'n_estimators': [150, 200, 250]}

forest_grid_pm = GridSearchCV(forest, params, cv=5, scoring = 'neg_mean_squared_error')
forest_grid_pm.fit(X_train_PM, y_train_PM)

# Best estimator
forest_grid_pm.best_estimator_

fig = plt.figure(figsize=(9,6))
forest_out_pm = forest_grid_pm.predict(X_test_PM)
pred_summary(forest_out_pm, y_test_PM, limit=50)
plt.xlabel('Predicted PM', fontsize = 18); plt.ylabel('Observed PM', fontsize=18)

FI_rf = pd.DataFrame(forest_grid_pm.best_estimator_.feature_importances_, index=X.columns, columns=['Feature Importance (RF)'])
FI_rf = FI_rf.sort_values(by='Feature Importance (RF)',ascending=False)
FI_rf # major factor identification

features = X.columns
importance = forest_grid_pm.best_estimator_.feature_importances_
indices = np.argsort(importance)
plt.figure(figsize=(5, 7))
plt.title("PM Feature importances (Random Forest)")
plt.barh(features[indices], importance[indices],
       color="b",  align="center");

# Ensemble learning - Boosting
gb_forest = GradientBoostingRegressor()

params = {'max_features': [6, 8, 10],
          'learning_rate': [0.05, 0.1, 0.5],
          'n_estimators': [100, 150, 200]}

gb_forest_grid_pm = GridSearchCV(gb_forest, params, cv=5, scoring = 'neg_mean_squared_error')
gb_forest_grid_pm.fit(X_train_PM, y_train_PM)

# Best estimator
gb_forest_grid_pm.best_estimator_

fig = plt.figure(figsize=(9,6))
gb_forest_out_pm = gb_forest_grid_pm.predict(X_test_PM)
pred_summary(gb_forest_out_pm, y_test_PM, limit=50)
plt.xlabel('Predicted PM 2.5', fontsize = 18); plt.ylabel('Observed PM 2.5', fontsize=18)

FI_gb = pd.DataFrame(gb_forest_grid_pm.best_estimator_.feature_importances_, index=X.columns, columns=['Feature Importance (GB)'])
FI_gb = FI_gb.sort_values(by='Feature Importance (GB)',ascending=False)
FI_gb

g2 = sns.barplot(x="Feature Importance (GB)", y=FI_gb.index, data=FI_gb)
g2.figure.set_size_inches(12, 9)

# permutation importance
# Current paramters
grid_search_best_pm = forest_grid_pm.best_estimator_
pprint(grid_search_best_pm.get_params())

# Permutation Importance
PI_pm = permutation_importance(grid_search_best_pm, X_test_PM, y_test_PM, n_repeats=5, random_state=1)

PI_res = pd.DataFrame(data=np.transpose([PI_pm['importances_mean'],PI_pm['importances_std']]),
             index = X.columns,columns=['PI_mean','PI_std'])
PI_res = PI_res.sort_values(by='PI_mean',ascending=False)
PI_res

# result summary
summary_2 = pd.DataFrame({'Random Forest':list(FI_rf.index),
              'Gradient Boost':list(FI_gb.index),
               'Permutation Importance':list(PI_res.index)})
summary_2

# All model results
result = pd.concat([summary_0, summary_1, summary_2], axis=1)
result.columns = ['Random Forest NO2', 'Gradient Boost NO2', 'Permutation Importance NO2',
       'Random Forest NO', 'Gradient Boost NO', 'Permutation Importance NO',
       'Random Forest PM2.5', 'Gradient Boost PM2.5', 'Permutation Importance PM2.5']
result

# We can see that for all three harmful substances, the most importnat common factor using all three models is how close the houses are to the highway, which makes sense as they often cause pollutions in the nearby area. Overall, how far residences are from any type of roads contribute significantly to their levels of these substances, which implies that choosing an area relatively further from the roads may contribute positively to the overall health level of the household.








