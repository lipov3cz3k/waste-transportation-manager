.headers on
.mode csv
.output test.csv

select x.path_id, Path.track_id, sum(x.length) as osm_length, Track.distance as original_length, 
		sum(x.motorway) as motorway, sum(x.trunk) as trunk, sum(x.prim) as prim, sum(x.secondary) as secondary, sum(x.tertiary) as tertiary,
		sum(x.road) as road, sum(x.residential) as residential,sum(x.service) as service,sum(x.motorway_link) as motorway_link,sum(x.trunk_link) as trunk_link,
		sum(x.primary_link) as primary_link, sum(x.secondary_link) as secondary_link,sum(x.teriary_link) as teriary_link,sum(x.living_street) as living_street,sum(x.unclassified) as unclassified
from
    (
    SELECT 
        Routes.path_id,
        sum(CASE WHEN highway = 'motorway' THEN length END) as motorway,
        sum(CASE WHEN highway = 'trunk' THEN length END) as trunk,
        sum(CASE WHEN highway = 'primary' THEN length END) as prim,
        sum(CASE WHEN highway = 'secondary' THEN length END) as secondary,
        sum(CASE WHEN highway = 'tertiary' THEN length END) as tertiary,
        sum(CASE WHEN highway = 'road' THEN length END) as road,
        sum(CASE WHEN highway = 'residential' THEN length END) as residential,
        sum(CASE WHEN highway = 'service' THEN length END) as service,
        sum(CASE WHEN highway = 'motorway_link' THEN length END) as motorway_link,
        sum(CASE WHEN highway = 'trunk_link' THEN length END) as trunk_link,
        sum(CASE WHEN highway = 'primary_link' THEN length END) as primary_link,
        sum(CASE WHEN highway = 'secondary_link' THEN length END) as secondary_link,
        sum(CASE WHEN highway = 'teriary_link' THEN length END) as teriary_link,
        sum(CASE WHEN highway = 'living_street' THEN length END) as living_street,
        sum(CASE WHEN highway = 'unclassified' THEN length END) as unclassified,
		sum(length) as length
    FROM Routes
    GROUP BY Routes.path_id, Routes.highway
    ) x
INNER JOIN Path
	ON Path.id = x.path_id
INNER JOIN Track
	ON Track.id = Path.track_id
GROUP BY x.path_id
