# Geospatial Feature — MongoDB

## 1. Overview

The IoT Sensor Monitor database includes a MongoDB `2dsphere` index on location coordinates. Geospatial indexes support queries involving geographic positions stored in GeoJSON format.

## 2. Purpose

A geospatial feature can help locate sensors or monitoring locations within a specified distance or geographic area.

Possible use cases include:
- Finding monitoring locations near a selected point.
- Identifying sensors within a geographic radius.
- Supporting location-based environmental monitoring.

## 3. Required Data Format

MongoDB geospatial queries expect coordinates in a supported format, such as GeoJSON:

```javascript
{
  type: "Point",
  coordinates: [longitude, latitude]
}
```

Coordinates must be in longitude, latitude order.

## 4. Example Geospatial Index

If the `locations` collection stores GeoJSON coordinates in a field named `coordinates`, the index can be created with:

```javascript
db.locations.createIndex({ coordinates: "2dsphere" })
```

The project already includes a geospatial index, but the actual stored field and coordinate format should be checked before running a query.

## 5. Example Nearby-Location Query

After verifying that valid GeoJSON points exist in `locations.coordinates`, a nearby search can be tested with:

```javascript
db.locations.find({
  coordinates: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [68.3578, 25.3960]
      },
      $maxDistance: 10000
    }
  }
})
```

The example point represents an approximate location in Hyderabad, Pakistan. The maximum distance is 10,000 metres.

This query is an example to test, not a claim that the current database has already returned matching results. It will work only if the field contains valid GeoJSON coordinates and the index is configured correctly.

## 6. Conclusion

MongoDB's `2dsphere` index provides a foundation for location-based sensor searches. Valid coordinate data and a successfully executed geospatial query are needed to demonstrate the feature fully.
