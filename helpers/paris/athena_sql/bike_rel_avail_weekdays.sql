SELECT station_id, 
    num_bikes_available / (num_bikes_available + num_docks_available) as rel_avail, 
    EXTRACT(hour from time) as hour
FROM paris.historical_data
WHERE EXTRACT(day_of_week from time) IN (1,2,3,4,5)