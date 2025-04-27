import dlt
import sqlite3
import argparse


def load_sqlite_to_destination(sqlite_file_path, table_name, destination, destination_table_name="default_table", destination_dataset="default", chunk_size=1000):
    """
    Loads a SQLite table to a specified destination (Athena, BigQuery, etc.) using dlt.
    Data is fetched from SQLite in chunks/iteratively using `fetchmany` to ensure memory efficiency.
    Args:
        sqlite_file_path (str): Path to the SQLite database file.
        table_name (str): Name of the table in the SQLite database to load.
        destination (str):  Name of the destination (e.g., 'athena', 'bigquery').
        destination_table_name (str): Name of the destination table to create (defaults to "default_table").
        destination_dataset (str): Name of the destination dataset/database (defaults to "default").
        chunk_size (int): Size of the chunks to load from SQLite in each iteration (defaults to 1000).
    """

    # Create a dlt pipeline to load data to the specified destination
    pipeline = dlt.pipeline(
        pipeline_name='sqlite_to_destination',
        destination=destination,
        dataset_name=destination_dataset  # Name of the destination dataset/database
    )

    # Function to read data from SQLite in chunks
    def load_data_from_sqlite():
        
        conn = sqlite3.connect(sqlite_file_path)
        cursor = conn.cursor()
        
        # Fetch column names
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        column_names = [description[0] for description in cursor.description]
        
        
        for row in cursor.execute(f"SELECT * FROM {table_name}"):
            yield dict(zip(column_names, row))
            
        # while True:
        #     rows = cursor.fetchmany(chunk_size)
        #     if not rows:
        #         break  # No more data

        #     # Yield data as dictionaries
        #     for row in rows:
        #         yield dict(zip(column_names, row))

        conn.close()

    # Run the pipeline
    info = pipeline.run(
        load_data_from_sqlite(),
        table_name=destination_table_name,
        write_disposition="replace"  # Or "append", "merge", etc.
    )

    print(info) # Print information about the load


def main():
    parser = argparse.ArgumentParser(description='Load a SQLite table to a specified destination.')
    parser.add_argument('sqlite_file_path', help='Path to the SQLite database file.')
    parser.add_argument('table_name', help='Name of the table in the SQLite database.')
    parser.add_argument('destination', help='Name of the destination (e.g., "athena", "bigquery").')
    parser.add_argument('--destination_table_name', default='default_table', help='Name of the destination table to create (default: default_table)')
    parser.add_argument('--destination_dataset', default='default', help='Name of the destination dataset/database where to load (default: default)')
    parser.add_argument('--chunk_size', type=int, default=1000, help='Size of the chunks to load from SQLite (default: 1000)')


    args = parser.parse_args()

    load_sqlite_to_destination(args.sqlite_file_path, args.table_name, args.destination, args.destination_table_name, args.destination_dataset, args.chunk_size)

if __name__ == '__main__':
    main()
   
