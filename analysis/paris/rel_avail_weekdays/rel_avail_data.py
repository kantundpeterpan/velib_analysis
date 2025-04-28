import sys
import os
sys.path.append(
    os.path.abspath("../../../")
)
from helpers.cloud.aws import get_athena_conn
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

conn = get_athena_conn()

df = pd.read_sql(
    """SELECT
    station_id, hour, AVG(rel_avail) as avg_rel_avail
    FROM paris.bike_rel_avail_weekdays
    GROUP BY station_id,hour""",
    conn)

station_id_vs_hour = pd.crosstab(
    df.station_id, df.hour, df.avg_rel_avail, aggfunc=lambda x: x
).dropna()
station_id_vs_hour.columns = [f"hour_{col}" for col in station_id_vs_hour.columns]

# Determine optimal number of clusters using the Elbow Method (no plotting):
wcss = []
for i in range(1, 11):
    kmeans = KMeans(n_clusters=i, init='k-means++', max_iter=300, n_init=10, random_state=0)
    kmeans.fit(station_id_vs_hour)
    wcss.append(kmeans.inertia_)

# save wcss to csv
wcss_df = pd.DataFrame({'n_clusters': range(1, 11), 'wcss': wcss})
wcss_df.to_csv('wcss_results.csv', index = False)

# Based on the elbow method, choose an optimal number of clusters (e.g., 3 or 4)
n_clusters = 5  # Example: Adjust based on visual elbow plot inspection

# Apply K-means clustering
kmeans = KMeans(n_clusters=n_clusters, init='k-means++', max_iter=300, n_init=10, random_state=0)
clusters = kmeans.fit_predict(station_id_vs_hour)+1

# Add cluster labels to the station_id_vs_hour dataframe
station_id_vs_hour['cluster'] = clusters

# change cluster labels to be coherent with textual analysis
cluster_map = {
    1:5,
    2:4,
    3:2,
    4:3,
    5:1
}
station_id_vs_hour['cluster'] = station_id_vs_hour.cluster.map(cluster_map)
# Save station_id_vs_hour with cluster assignments to a CSV file
# station_id_vs_hour.to_csv('station_clusters.csv', index=True)

# Calculate cluster profiles (average availability per hour for each cluster)
cluster_profiles = station_id_vs_hour.groupby('cluster').mean()

# Save cluster profiles to CSV
cluster_profiles.to_csv('cluster_profiles.csv', index=True)

# Print cluster sizes
cluster_sizes = station_id_vs_hour['cluster'].value_counts()
print("Cluster Sizes:")
print(cluster_sizes)

#Save cluster sizes to csv.
cluster_sizes_df = pd.DataFrame({'cluster': cluster_sizes.index, 'size': cluster_sizes.values})
cluster_sizes_df.to_csv('cluster_sizes.csv', index = False)

# Apply t-SNE
tsne = TSNE(n_components=2, random_state=0)
tsne_result = tsne.fit_transform(station_id_vs_hour.drop('cluster', axis=1))

# Create a DataFrame for the t-SNE results
tsne_df = pd.DataFrame({'tsne_1': tsne_result[:, 0], 'tsne_2': tsne_result[:, 1]}, index = station_id_vs_hour.index)

# Concatenate station_id_vs_hour and tsne_df along the index
station_id_vs_hour = pd.concat([station_id_vs_hour, tsne_df], axis=1)
station_info = pd.read_sql(
    "SELECT * FROM paris.historical_stations", conn
)
# Merge station_id_vs_hour and station_info on station_id
station_id_vs_hour = station_id_vs_hour.merge(
    station_info, left_index=True, right_on='station_id', how='left'
).dropna(subset = ['lat', 'lon'])

print(station_id_vs_hour.head().columns)

# Save merged data to CSV
station_id_vs_hour.to_csv('station_clusters_with_info.csv', index=False)

