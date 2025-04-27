import sqlite3
import pandas as pd
import datetime as dt
import time

from gbfs.services import SystemDiscoveryService
ds = SystemDiscoveryService()

client = ds.instantiate_client('Paris')

def pull_data():

    now = dt.datetime.now()
    
    df = pd.DataFrame.from_records(client.request_feed('station_status').get('data').get('stations'))

    no_bikes = pd.DataFrame.from_records(df.num_bikes_available_types).map(lambda x:x[list(x.keys())[0]])

    no_bikes.columns = ['no_mechanical', 'no_ebike']

    df = pd.merge(df.drop('num_bikes_available_types', axis = 1),
                  no_bikes, right_index = True, left_index = True)

    df['time'] = now

    return df

def run():

    db = sqlite3.connect('velib.db')

    while True:
        try:
            print('Pulling data ...')
            df = pull_data()
            print('Pushing to SQL DB...')
            df.to_sql(name = 'data', con = db,
                      if_exists='append')
        except KeyboardInterrupt:
            break

        except Exception as e:
            print(e)

        print('... complete')
        time.sleep(60 *5)


if __name__ == '__main__':
    run()
