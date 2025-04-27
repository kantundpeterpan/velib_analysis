# %%
import sys
import os
sys.path.append(
    os.path.abspath("../../")
)
# %%
from helpers.cloud.aws import get_athena_conn
# %%
conn = get_athena_conn()

# %%
import pandas as pd

# %%
df = pd.read_sql(
    """SELECT 
    station_id, hour, AVG(rel_avail) as avg_rel_avail 
    FROM paris.bike_rel_avail_weekdays
    GROUP BY station_id,hour""",
    conn)
# %%
station_id_vs_hour = pd.crosstab(
    df.station_id, df.hour, df.avg_rel_avail, aggfunc=lambda x: x #single value per combination
).dropna()
station_id_vs_hour.columns = [f"hour_{col}" for col in station_id_vs_hour.columns]
# %%
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Determine optimal number of clusters using the Elbow Method:
wcss = []
for i in range(1, 11):
    kmeans = KMeans(n_clusters=i, init='k-means++', max_iter=300, n_init=10, random_state=0)
    kmeans.fit(station_id_vs_hour)
    wcss.append(kmeans.inertia_)

plt.plot(range(1, 11), wcss)
plt.title('Elbow Method')
plt.xlabel('Number of clusters')
plt.ylabel('WCSS')
plt.show()

# %%

# Based on the elbow method, choose an optimal number of clusters (e.g., 3 or 4)
n_clusters = 5 # Example: Adjust based on the elbow plot

# Apply K-means clustering
kmeans = KMeans(n_clusters=n_clusters, init='k-means++', max_iter=300, n_init=10, random_state=0)
clusters = kmeans.fit_predict(station_id_vs_hour)

# Add cluster labels to the station_id_vs_hour dataframe
station_id_vs_hour['cluster'] = clusters
# %%
# Visualize cluster profiles (example: average availability per hour for each cluster)
cluster_profiles = station_id_vs_hour.groupby('cluster').mean()

# Plot cluster profiles
plt.figure(figsize=(12, 6))
palette = sns.color_palette("hls", n_clusters)
for i in range(n_clusters):
    plt.plot(cluster_profiles.iloc[i], label=f'Cluster {i}', color=palette[i])

plt.title('Cluster Profiles (Average Availability per Hour)')
plt.xlabel('Hour')
plt.ylabel('Average Relative Availability')
plt.xticks(range(24))
plt.legend()
plt.grid(True)
plt.show()

# Optionally, visualize using a heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(cluster_profiles, cmap="YlGnBu")
plt.title("Heatmap of Average Availability by Cluster")
plt.ylabel("Cluster")
plt.show()

# Print cluster sizes
print("Cluster Sizes:")
print(station_id_vs_hour['cluster'].value_counts())

# %%
from sklearn.manifold import TSNE

# Apply t-SNE
# tsne = TSNE(n_components=2, random_state=0)
# tsne_result = tsne.fit_transform(station_id_vs_hour.drop('cluster', axis=1))

# Create a DataFrame for the t-SNE results
tsne_df = pd.DataFrame({'tsne_1': tsne_result[:, 0], 'tsne_2': tsne_result[:, 1], 'cluster': station_id_vs_hour['cluster']})
# %%
# Visualize t-SNE with clusters
plt.figure(figsize=(10, 8))
sns.scatterplot(x='tsne_1', y='tsne_2', hue='cluster', palette=sns.color_palette("hls", n_clusters), data=tsne_df)
plt.title('t-SNE Visualization of Clusters')
plt.xlabel('t-SNE Dimension 1')
plt.ylabel('t-SNE Dimension 2')
plt.show()
# %%
station_info = pd.read_sql(
    "SELECT * FROM paris.historical_stations", conn
)
# %%
# Merge station_id_vs_hour and station_info on station_id
station_id_vs_hour = station_id_vs_hour.merge(
    station_info, left_index=True, right_on='station_id', how='left'
).dropna(subset = ['lat', 'lon'])

print(station_id_vs_hour.head())
# %%
import folium

# 1. Calculate the center of the stations for the map's initial view
center_lat = station_id_vs_hour['lat'].mean()
center_lon = station_id_vs_hour['lon'].mean()

# 2. Create a Folium map centered around the calculated coordinates
m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

# 3. Define a color palette for the clusters
colors = sns.color_palette("hls", n_clusters).as_hex() # Get hex colors
cluster_colors = {i: colors[i] for i in range(n_clusters)}

# 4. Iterate through the DataFrame and add markers for each station
for index, row in station_id_vs_hour.dropna(subset=['lat','lon']).iterrows():
    station_lat = row['lat']
    station_lon = row['lon']
    cluster_id = row['cluster']
    color = cluster_colors[cluster_id] # Get color for the cluster

    # Add a circle marker (more visually suitable for clusters)
    folium.CircleMarker(
        location=[station_lat, station_lon],
        radius=5,  # Adjust the radius as needed
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=f"Station ID: {row['station_id']}, Cluster: {cluster_id}"
    ).add_to(m)

# 5. Display the map
m
# %%