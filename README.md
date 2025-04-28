# Analysis of Velib bike sharing


# Project Overview: Analyzing Velib Utilization Patterns in Paris

This project analyses the dynamics of the Parisian Velib bike sharing
system. I use clustering, spatial and temporal visulization to uncover
patterns in the flow of bikes in the network separately of weekdays and
weekends. Both timeperiods exhibit quite different dynamics.

# The Dataset

The dataset consists of two tables, one containing general information
(id, name, location etc.) for all station and another containing the
number of bikes available at a given station at a given timepoint.

The data were acquired from 01/07/2024 to 11/02/2025 using the
`General Bikeshare Feed` of the Velib system (available at:
<https://www.velib-metropole.fr/donnees-open-data-gbfs-du-service-velib-metropole>).
The feed was accessed using the
[`gbfs-client`](https://github.com/jakehadar/bikeshare-client-python)
package for python. The feed was queried at a time interval of 5
minutes.

After unnesting, the newly acquired data was pushed to a local `sqlite`
database.

The original script is available at
[./archive/server.py](./archive/server.py).

Data acquisition stopped due to a schema change in the feed. A new
implementation using `dlt` is pending.

The timeseries data set contains 87 047 062 rows.

# Tools

- data load tool `dlt`: data ingestion (local `sqlite` database to AWS
  `Athena`, recurrent querying of the GBFS feed for future data
  acquisition)
- data build tool `dbt`: data transformation
- AWS `Quicksight`: dashboarding
- python libraries for data processing: `pandas`, `scikit-learn`

# Data pipeline schema

![](./img/mermaid-diagram-2025-04-27-214223.png)

# Data transformation and processing

Data were filtered to exclude the period from 2024-07-15 to 2024-08-31
during which the Olympic Summer games took place in Paris and which
probably caused significant alterations in daily bike usage patterns
both due to differences in trip profiles as reallocation strategy as
well as setup of temporary rental stations.

For each time point and station the relative occupation of the station
was calculated by dividing the number of available bikes
(`num_bikes_available`) by the sum of available bikes and available
docks (`num_docks_availabe`) ([see also the dbt
models](./dbt/athena_/models/)).

The relative occupation was then averaged for each station by the hour
of the day ([see for
example](./analysis/paris/rel_avail_weekdays/rel_avail_data.py)).
Separate datasets were created for weekdays and the weekend.

# Results

## Network dynamics during weekdays

### Code

![](readme_files/figure-commonmark/cell-4-output-1.png)

### Interpretation

The number of clusters was identified using the elbow method, there is
no clearcut results, but a choice of $k=5$ seems justified as it
provided a meaningful distinction of temporal patterns and geographic
concentrations that align with expected urban mobility behaviors,
offering a coherent basis for analysis.

Given the five clusters, temporal analysis of the hourly mean relative
occupancy over the course of a typical working day shows interesting
dynamics.

Cluster no. 1 is the biggest cluster with about 500 stations
(corresponding to about 30% of all stations in the network). Its mean
occupancy goes never beyond 30% and is very low (\<20%) during working
hours (8am to 20pm). The stations belonging to cluster 1, are mainly
situated in the outer ring of the Parisian arrondissements on the Rive
droite of the river Seine (Arr. 17, 18, 19, 20) and in the 13th and 14th
arrondissement on the Rive Gauche.

The mean occupancy in cluster 2 is quite stable between 60-70%
throughout the day. Stations assigned to cluster 2 are concentrated in
two regions of Paris: 1) In the eastern part of the inner circle of
arrondissements (3rd, 4th, 5th) and 2) In the outer south-western part,
around and south of the Eiffel tower which might indicate

The remaining clusters 3, 4, and 5 exhibit anti-correlated periodic
patterns with pronounced changes in occupancy during communting hours
(6-9am and 4-6pm). Stations in the 6th, 7th, and 8th arrondissement
(cluster 4) are lowly occupied in the morning and experience a large
increase in occupancy, consistent with commuter influx from clusters 3
and 5.

One has to keep in mind, that only net fluxes can be observed in this
dataset, *i.e.* the flux path cannot be inferred from these data meaning
outflows from clusters 3 and 5 in the morning might directly go into
cluster 4 while a flux equilibrium between clusters 3,5,2 and 4 an
equally good explanation for the observed *net* pattern.

Keeping this in mind, the observed net flow patterns are still
informative as to whether specific stations or clusters of stations
exhibit certain characteristics and guide network operations:

Stations or clusters that show a significant decrease in available bikes
during morning peak hours, suggest a high volume of net rentals typical
of commuter activity while stations or clusters that exhibit a strong
increase in available bikes during evening hours, indicate a net inflow
of bikes (more returns than rentals), potentially from users returning
bikes after work or leisure.

Stations with consistent net decrease during peak usage times are
candidates for having bikes sent during proactive rebalancing while
bikes might need to be removed from stations that saturate.

## Network dynamics during weekends

### Code

![](readme_files/figure-commonmark/cell-6-output-1.png)

### Interpretation

The elbow plot for the weekend data indicates that an analysis using
only two clusters might be warranted. However, in order to facilitate
direct comparison to the weekday analysis, 5 clusters were retained.

Additionnally, clusters found in the weekend analysis were manually
relabeled to highlight differences in usage patterns similarities of
spatial station distributions while usage patterns differ from weekdays.

Results for clusters 1 and 2 are very similar in terms of temporal
occupancy pattern and cluster size in comparison to weekdays. Overall,
clusters 1, 2, 3, and 5 show intercorrelated occupancy patterns with a
much smaller amplitude compared to weekdays, particularly noticable in
clusters 3 and 5, indicating less extreme fluctuations in bike
availability.

As during weekdays, the pattern in found in cluster 4 is anti-correlated
to the occupancy in the remaining clusters. Compared to weekdays, bike
availability is higher and the change in availibility is more pronounced
during the hours after midnight, while peak net influx is shifted to
mid-afternoon. This could be due to users returning home after having
spent the evening night out which is consistent with cluster 4 stations
being located in busy downtown districts. The flatter patterns observed
in the remaining clusters could either indicate lower user activity in
general or a more homogenous distribution of trips over the city.

# Conclusions and outlook

This analysis explored temporal patterns of bike availability in the
Parisian Velib bike sharing network. I have shown that a large part of
the network is chronically underserved (cluster 1 in both weekday and
weekend analyses) while another part provides stable access to bikes on
any given day (cluster 2).

These finding provide guidance for potential rebalancing efforts (more
bikes shifted to cluster 1) and potential infrastructure improvements
(more docks for cluster 4 alternative returning solutions).

Comparing occupancy patterns stratified by weekday/weekend, revealed
differences in the occupancy time course but less so in the spatial
clustering of bike stations. This suggests that there might be two
distinct states of the bike sharing system thus warranting further
finegrained investigation, *e.g.* by day of the week and especially of
the supposed change points - friday evening and monday morning.

<!-- # Outlook
&#10;## Occupancy analysis
- per district/city
- correlation with sociodemographic indicators (salary, age, level of education, total population)
- correlation with station elevation
- stratified analysis mechanical/ebikes
- correlation and (lagged) crosscorrelation
- clustering comparison metrics ari, nmi
- banlieue vs. intramuros
- analysis per weekday with emphasis on change points
&#10;## Network structure analysis (solely based on stations)
&#10;- theoretical capacity -->
