
import dlt
import gbfs
import gbfs.services
import pandas as pd
import datetime as dt
import time
import argparse
from typing import Iterator, Dict, Any
import datetime as dt


def create_gbfs_client(city: str):
    """
    Creates a GBFS client for the specified city.

    Args:
        city: The name of the city to create the client for.

    Returns:
        A GBFS client for the specified city.

    Raises:
        ValueError: If the specified city is not available in the GBFS discovery service.
    """
    ds = gbfs.services.SystemDiscoveryService()
    try:
        client = ds.instantiate_client(city)
        assert client is not None
        return client
    except ValueError as e:
        raise ValueError(f"City '{city}' not found in GBFS discovery service. Available cities: {ds.available_systems}") from e


@dlt.source(name="gbfs_feed")
def gbfs_source(city: str):
    """
    A dlt source that pulls data from a GBFS feed.

    Args:
        city: The name of the city to pull data for.
              This must be a city supported by the GBFS System Discovery Service.

    Returns:
        A dlt source that yields data from the GBFS feed.
    """
    client = create_gbfs_client(city)

    @dlt.resource(name="station_info", write_disposition="merge", primary_key = "station_id")
    def get_stations():
        """
        A dlt resource that pulls station information from the GBFS feed.
        """
        feed = client.request_feed('station_information')
        if feed and feed.get('data') and feed.get('data').get('stations'):
            for station in feed.get('data').get('stations'):
                station['updated_at'] = dt.datetime.now()
                yield station

    @dlt.resource(name="station_data", write_disposition="append")
    def get_station_data() -> Iterator[Dict[str, Any]]:
        """
        A dlt resource that pulls station status data from the GBFS feed, incrementally.

        Args:
            last_updated: An incremental object that keeps track of the last updated timestamp.

        Yields:
            A dictionary of station status data.
        """
        feed = client.request_feed('station_status')
        if feed and feed.get('data') and feed.get('data').get('stations'):
            stations = feed.get('data').get('stations')
            
            df = pd.DataFrame.from_records(stations)
            # print(df)
            df['time'] = dt.datetime.now()
            no_bikes = pd.DataFrame.from_records(df.num_bikes_available_types).map(lambda x:x[list(x.keys())[0]])
            no_bikes.columns = ['no_mechanical', 'no_ebike']

            df = pd.merge(df.drop('num_bikes_available_types', axis = 1),
                  no_bikes, right_index = True, left_index = True)
            # if not df.empty:
            #     # Ensure 'last_reported' column exists in the DataFrame
            #     if 'last_reported' not in df.columns:
            #         print("Warning: 'last_reported' column not found in station data.  Skipping incremental filtering.")
            #         filtered_df = df
            #     else:
            #       # apply a filter based on last_updated to fetch just the new records
            #         filtered_df = df[df['last_reported'] > last_updated.last_value]

            #     # yield only if the dataframe has new records
            #     if not filtered_df.empty:
            #       yield filtered_df.to_dict("records")
            #     else:
            #        print("no new records")

            yield df.to_dict("records")

    return get_stations, get_station_data

def main(city: str, dataset_name: str, destination: str = "athena"):
    """
    Runs the data ingestion pipeline.

    Args:
        city: The name of the city to pull data for.
        dataset_name: The name of the dlt dataset.
        destination: The dlt destination to use.  Defaults to "athena".
    """
    pipeline = dlt.pipeline(
        pipeline_name="gbfs_pipeline",
        destination=destination,
        dataset_name=dataset_name.lower(),
    )
    data = gbfs_source(city=city)

    info = pipeline.run(data, write_disposition="append")

    print(info)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GBFS Data Ingestion Pipeline")
    parser.add_argument("city", help="The city to pull GBFS data for")
    parser.add_argument("dataset_name", help="The name of the dlt dataset")
    parser.add_argument(
        "--destination",
        default="athena",
        help="The dlt destination to use (e.g., athena, duckdb)",
    )

    args = parser.parse_args()

    main(city=args.city, dataset_name=args.dataset_name, destination=args.destination)
