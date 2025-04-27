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

# Data transformation

Data were analysed over the complete acquisition period. For each time
point and station the relative occupation of the station was calculated
by dividing the number of available bikes (`num_bikes_available`) by the
sum of available bikes and available docks (`num_docks_availabe`) ([see
also the dbt models](./dbt/athena_/models/)).

The relative occupation was then averaged for each station by the hour
of the day ([see for
example](./analysis/paris/rel_avail_weekdays/rel_avail_data.py)).
Separate datasets were created for weekdays and the weekend.

# Results

## Network dynamics during weekdays

![](readme_files/figure-commonmark/cell-4-output-1.png)

## Network dynamics during weekends

![](readme_files/figure-commonmark/cell-6-output-1.png)
