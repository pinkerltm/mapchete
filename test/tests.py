#!/usr/bin/env python
"""Test all mapchete modules."""

import os
from shapely.geometry import Polygon
from shapely.wkt import loads

from tilematrix import TilePyramid
from mapchete import Mapchete
from mapchete.config import MapcheteConfig

ROUND = 10


def main():
    """Start tests."""
    scriptdir = os.path.dirname(os.path.realpath(__file__))

    """drivers"""
    from mapchete.formats import (
        available_input_formats, available_output_formats, _file_ext_to_driver
        )

    assert set(['mapchete', 'raster_file']).issubset(
        set(available_input_formats()))
    assert set(['GTiff', 'PNG', 'PNG_hillshade']).issubset(
        set(available_output_formats()))
    ext_to_driver = _file_ext_to_driver()
    assert isinstance(ext_to_driver, dict)
    assert set(['mapchete', 'tif', 'jp2', 'png', 'vrt']).issubset(
        set(ext_to_driver))
    for extension, driver in ext_to_driver.iteritems():
        assert len(driver) == 1

    """config and base module"""
    # Load source process from python file and initialize.
    mapchete_file = os.path.join(scriptdir, "example.mapchete")
    config = MapcheteConfig(mapchete_file)
    mapchete = Mapchete(config)

    dummy1_abspath = os.path.join(scriptdir, "testdata/dummy1.tif")
    dummy2_abspath = os.path.join(scriptdir, "testdata/dummy2.tif")

    # Validate configuration constructor
    ## basic run through
    try:
        config = mapchete.config
        print "OK: basic configuraiton constructor run through"
    except:
        print "FAILED: basic configuraiton constructor run through"
        raise

    try:
        # Check configuration at zoom level 5
        zoom5 = config.at_zoom(5)
        input_files = zoom5["input_files"]
        assert input_files["file1"] is None
        assert input_files["file2"].path == dummy2_abspath
        assert zoom5["some_integer_parameter"] == 12
        assert zoom5["some_float_parameter"] == 5.3
        assert zoom5["some_string_parameter"] == "string1"
        assert zoom5["some_bool_parameter"] is True

        # Check configuration at zoom level 11
        zoom11 = config.at_zoom(11)
        input_files = zoom11["input_files"]
        assert input_files["file1"].path == dummy1_abspath
        assert input_files["file2"].path == dummy2_abspath
        assert zoom11["some_integer_parameter"] == 12
        assert zoom11["some_float_parameter"] == 5.3
        assert zoom11["some_string_parameter"] == "string2"
        assert zoom11["some_bool_parameter"] is True
    except:
        raise
        print "FAILED: basic configuration parsing"
        print input_files
    else:
        print "OK: basic configuration parsing"

    ## read zoom level from config file
    mapchete_file = os.path.join(scriptdir, "testdata/zoom.mapchete")
    config = Mapchete(MapcheteConfig(mapchete_file)).config
    try:
        assert 5 in config.zoom_levels
        print "OK: read zoom level from config file"
    except:
        print "FAILED: read zoom level from config file"
        print mapchete_file
        raise
    ## read min/max zoom levels from config file
    mapchete_file = os.path.join(scriptdir, "testdata/minmax_zoom.mapchete")
    config = Mapchete(MapcheteConfig(mapchete_file)).config
    try:
        for zoom in [7, 8, 9, 10]:
            assert zoom in config.zoom_levels
        print "OK: read  min/max zoom levels from config file"
    except:
        print "FAILED: read  min/max zoom levels from config file"
        raise
    ## zoom levels override
    mapchete_file = os.path.join(scriptdir, "testdata/minmax_zoom.mapchete")
    config = Mapchete(MapcheteConfig(mapchete_file, zoom=[1, 4])).config
    try:
        for zoom in [1, 2, 3, 4]:
            assert zoom in config.zoom_levels
        print "OK: zoom levels override"
    except:
        print "FAILED: zoom levels override"
        raise
    ## read bounds from config file
    mapchete_file = os.path.join(scriptdir, "testdata/zoom.mapchete")
    config = Mapchete(MapcheteConfig(mapchete_file)).config
    try:
        test_polygon = Polygon([
            [3, 1.5], [3, 2], [3.5, 2], [3.5, 1.5], [3, 1.5]
            ])
        assert config.process_area(5).equals(test_polygon)
        print "OK: read bounds from config file"
    except:
        print "FAILED: read bounds from config file"
        print config.process_area(5), test_polygon
        raise
    ## override bounds
    mapchete_file = os.path.join(scriptdir, "testdata/zoom.mapchete")
    config = Mapchete(MapcheteConfig(
        mapchete_file,
        bounds=[3, 2, 3.5, 1.5]
        )).config
    try:
        test_polygon = Polygon([
            [3, 1.5], [3, 2], [3.5, 2], [3.5, 1.5], [3, 1.5]
            ])
        assert config.process_area(5).equals(test_polygon)
        print "OK: override bounds"
    except:
        print "FAILED: override bounds"
        print config.process_area(5)
        raise
    ## read bounds from input files
    mapchete_file = os.path.join(scriptdir, "testdata/files_bounds.mapchete")
    config = Mapchete(MapcheteConfig(mapchete_file)).config
    try:
        test_polygon = Polygon(
        [[3, 2], [4, 2], [4, 1], [3, 1], [2, 1], [2, 4], [3, 4], [3, 2]]
        )
        assert config.process_area(10).equals(test_polygon)
        print "OK: read bounds from input files"
    except:
        print "FAILED: read bounds from input files"
        print config.process_area(10), test_polygon
        raise
    ## read .mapchete files as input files
    mapchete_file = os.path.join(scriptdir, "testdata/mapchete_input.mapchete")
    config = Mapchete(MapcheteConfig(mapchete_file)).config
    area = config.process_area(5)
    testpolygon = "POLYGON ((3 2, 3.5 2, 3.5 1.5, 3 1.5, 3 1, 2 1, 2 4, 3 4, 3 2))"
    try:
        assert area.equals(loads(testpolygon))
        print "OK: read bounding box from .mapchete subfile"
    except:
        print "FAILED: read bounding box from .mapchete subfile"
        raise

    """io module"""
    testdata_directory = os.path.join(scriptdir, "testdata")

    dummy1 = os.path.join(testdata_directory, "dummy1.tif")
    zoom = 8
    tile_pyramid = TilePyramid("geodetic")

    mapchete_file = os.path.join(scriptdir, "testdata/minmax_zoom.mapchete")
    mapchete = Mapchete(MapcheteConfig(mapchete_file))
    raster = mapchete.config.at_zoom(7)["input_files"]["file1"]
    dummy1_bbox = raster.bbox()

    tiles = tile_pyramid.tiles_from_geom(dummy1_bbox, zoom)
    resampling = "average"
    pixelbuffer = 5
    from mapchete.io.raster import read_raster_window
    for tile in tiles:
        for band in read_raster_window(
            dummy1,
            tile,
            resampling=resampling,
            pixelbuffer=pixelbuffer
        ):
            try:
                assert band.shape == (
                    tile_pyramid.tile_size + 2 * pixelbuffer,
                    tile_pyramid.tile_size + 2 * pixelbuffer
                )
                print "OK: read data size"
            except:
                print "FAILED: read data size"

    """processing"""
    tilenum = 0
    for cleantopo_process in [
        "testdata/cleantopo_tl.mapchete", "testdata/cleantopo_br.mapchete"
    ]:
        mapchete_file = os.path.join(scriptdir, cleantopo_process)
        mapchete = Mapchete(MapcheteConfig(mapchete_file))
        from mapchete import BufferedTile
        import numpy.ma as ma
        for tile in mapchete.get_process_tiles():
            output = mapchete.execute(tile)
            assert isinstance(output, BufferedTile)
            assert isinstance(output.data, ma.MaskedArray)
            assert output.data.shape == output.shape()
            assert not ma.all(output.data.mask)
            mapchete.write(output)
            tilenum += 1
    print "OK: tile properties from %s tiles" % tilenum

if __name__ == "__main__":
    main()
