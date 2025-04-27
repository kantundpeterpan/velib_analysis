SELECT station_id, 
        CAST(num_bikes_available AS DECIMAL(10,3)) / (CAST(num_bikes_available AS DECIMAL(10,3)) + CAST(num_docks_available AS DECIMAL(10,3))) as rel_avail,  
    EXTRACT(hour from time) as hour
FROM {{ source('paris', 'historical_data') }}
WHERE EXTRACT(day_of_week from time) IN (1,2,3,4,5)  AND
num_bikes_available+num_bikes_available != 0