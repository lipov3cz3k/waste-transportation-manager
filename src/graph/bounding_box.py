class BoundingBox:
    def __init__(self, min_lon, min_lat, max_lon, max_lat):
        self.min_longitude = float(min_lon)
        self.min_latitude = float(min_lat)
        self.max_longitude = float(max_lon)
        self.max_latitude = float(max_lat)

    def ToURL(self):
        return "bbox=%f,%f,%f,%f" % (self.min_longitude, self.min_latitude, self.max_longitude, self.max_latitude)

    def ToXAPIBBox(self):
        return "%f,%f,%f,%f" % (self.min_latitude, self.min_longitude, self.max_latitude, self.max_longitude)

    def ToName(self):
        return "data_%f_%f_%f_%f"% (self.min_longitude, self.min_latitude, self.max_longitude, self.max_latitude)
    def ToList(self):
        return [self.max_latitude, self.min_longitude], [self.min_latitude, self.max_longitude]

    def Center(self):
        lat = self.min_latitude + ((self.max_latitude - self.min_latitude) / 2)
        lon = self.min_longitude + ((self.max_longitude - self.min_longitude) / 2)
        return lat, lon

    def Validate(self):
        if not self.min_longitude or not self.min_latitude or not self.max_longitude or not self.max_latitude:
            raise Exception("Bounding box is not valid: missing some coord")

        if self.min_longitude >= self.max_longitude or self.min_latitude >= self.max_latitude:
            raise Exception("Bounding box is not valid: invalid coords")

    def InBoundingBox(self, lon, lat):
        if self.min_longitude > float(lon) or self.max_longitude < float(lon):
            return False
        if self.min_latitude > float(lat) or self.max_latitude < float(lat):
            return False
        return True

def get_bounding_box(latitude_in_degrees, longitude_in_degrees, half_side_in_km):
    import math
    assert half_side_in_km > 0
    assert latitude_in_degrees >= -90.0 and latitude_in_degrees  <= 90.0
    assert longitude_in_degrees >= -180.0 and longitude_in_degrees <= 180.0

    lat = math.radians(latitude_in_degrees)
    lon = math.radians(longitude_in_degrees)

    radius  = 6371
    # Radius of the parallel at given latitude
    parallel_radius = radius*math.cos(lat)

    lat_min = lat - half_side_in_km/radius
    lat_max = lat + half_side_in_km/radius
    lon_min = lon - half_side_in_km/parallel_radius
    lon_max = lon + half_side_in_km/parallel_radius
    rad2deg = math.degrees

    box = BoundingBox(rad2deg(lon_min), rad2deg(lat_min), rad2deg(lon_max), rad2deg(lat_max))

    return (box)