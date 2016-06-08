class BoundingBox:
    def __init__(self, min_lon, min_lat, max_lon, max_lat):
        self.min_longitude = float(min_lon)
        self.min_latitude = float(min_lat)
        self.max_longitude = float(max_lon)
        self.max_latitude = float(max_lat)

    def ToURL(self):
        return "bbox=%f,%f,%f,%f" % (self.min_longitude, self.min_latitude, self.max_longitude, self.max_latitude)

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