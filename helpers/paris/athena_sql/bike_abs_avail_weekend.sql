SELECT station_id, 
num_bikes_available, 
EXTRACT(hour from time) as hour
FROM paris.historical_data
WHERE EXTRACT(day_of_week from time) IN (6,7)