SELECT station_id, 
    CAST(num_bikes_available AS DECIMAL(10,3)) / (CAST(num_bikes_available AS DECIMAL(10,3)) + num_docks_available) as rel_avail, 
    EXTRACT(hour from time) as hour
FROM {{ source('paris', 'historical_data') }}
WHERE EXTRACT(day_of_week from time) IN (6,7) 
AND num_bikes_available+num_docks_available != 0
--exclude (para/o)lympic games
AND (
    CAST(time as date)  < DATE('2024-07-15') OR
    CAST(time as date)  > DATE('2024-08-31')
)