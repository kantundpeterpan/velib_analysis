import sys
import os

import panel as pn
pn.extension('plotly')
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from sklearn.manifold import TSNE
import folium
import holoviews as hv
hv.extension('plotly')

# Data Retrieval from CSV files
cluster_profiles = pd.read_csv("cluster_profiles.csv", index_col=0)
cluster_sizes = pd.read_csv("cluster_sizes.csv", index_col=0)
station_clusters_with_info = pd.read_csv("station_clusters_with_info.csv")
station_clusters = pd.read_csv("station_clusters_with_info.csv", index_col=0)
wcss_results = pd.read_csv("wcss_results.csv")

# Remove "hour_" from column names in cluster_profiles
cluster_profiles.columns = [col.replace('hour_', '') for col in cluster_profiles.columns]

# Remove "hour_" from column names in station_clusters_with_info
station_clusters_with_info.columns = [col.replace('hour_', '') for col in station_clusters_with_info.columns]

# Remove "hour_" from column names in station_clusters
station_clusters.columns = [col.replace('hour_', '') for col in station_clusters.columns]


# Elbow Method Plot from loaded data
elbow_fig = px.line(x=wcss_results['n_clusters'], y=wcss_results['wcss'], title='Elbow Method', labels={'x': 'Number of clusters', 'y': 'WCSS'})
elbow_plot = pn.pane.Plotly(elbow_fig)

# Consistent color palette
palette = px.colors.qualitative.Plotly

# Cluster Profiles Visualization
time_course_fig = go.Figure()
n_clusters = len(cluster_profiles)

cluster_profiles.columns = [str(col) for col in cluster_profiles.columns]

for i in range(n_clusters):
    time_course_fig.add_trace(
        go.Scatter(x=cluster_profiles.columns, y=cluster_profiles.iloc[i], mode='lines', name=f'Cluster {i}',
                   marker_color=palette[i % len(palette)], showlegend=False))

time_course_fig.update_layout(title='Cluster Profiles (Average Availability per Hour)', xaxis_title='Hour', yaxis_title='Average Relative Availability')
time_course_plot = pn.pane.Plotly(time_course_fig)

# Heatmap Visualization
heatmap_fig = px.imshow(cluster_profiles, labels=dict(x="Hour", y="Cluster", color="Average Availability"), color_continuous_scale="YlGnBu", title="Heatmap of Average Availability by Cluster")
heatmap_plot = pn.pane.Plotly(heatmap_fig)

# Cluster Size Display
cluster_sizes_pane = pn.pane.Markdown(f"Cluster Sizes:\n{cluster_sizes.to_markdown()}")

# t-SNE Visualization
tsne_fig = go.Figure()

for cluster_id in range(n_clusters): #enumerate(station_clusters['cluster'].unique().sort()):
    cluster_data = station_clusters[station_clusters['cluster'] == cluster_id]
    tsne_fig.add_trace(go.Scatter(
        x=cluster_data['tsne_1'],
        y=cluster_data['tsne_2'],
        mode='markers',
        marker_color=palette[cluster_id % len(palette)], #dict(color=palette[cluster_id % len(palette)]),
        name=f'Cluster {cluster_id}',
        showlegend=False
    ))

tsne_fig.update_layout(
    title='t-SNE Visualization of Clusters',
    xaxis_title='t-SNE Dimension 1',
    yaxis_title='t-SNE Dimension 2'
)

tsne_plot = pn.pane.Plotly(tsne_fig)


# Station Map with data from station_clusters_with_info.csv

center_lat = station_clusters_with_info['lat'].mean()
center_lon = station_clusters_with_info['lon'].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

for index, row in station_clusters_with_info.iterrows():
    station_lat = row['lat']
    station_lon = row['lon']
    cluster_id = row['cluster']
    color = palette[int(cluster_id % len(palette))]
    folium.CircleMarker(
        location=[station_lat, station_lon],
        radius=5,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=f"Station ID: {row['station_id']}, Cluster: {cluster_id}"
    ).add_to(m)


# 5. Display the map

map_pane = pn.pane.HTML(m._repr_html_())

# %%
# Dashboard Layout using Gridspec
template = pn.GridSpec(width = 1200)

template[0, :8] = pn.pane.Markdown("# Bike Station Clustering Dashboard", align="center")
template[1:3, :3] = elbow_plot
template[1:3, 3:4] = cluster_sizes_pane
template[3:5, :2] = time_course_plot
template[3:5, 2:4] = heatmap_plot
template[5:7, :4] = tsne_plot
template[1:8, 4:8] = map_pane

dashboard = template
dashboard.servable()
# dashboard.show(port=38951, websocket_origin='localhost:8080')