#!/usr/bin/env python

import os
import yaml
import rasterio
from shapely.geometry import Polygon
from shapely.ops import cascaded_union

# from .mapchete import *
import mapchete

def get_clean_configuration(
    mapchete_file,
    zoom=None,
    bounds=None,
    output_path=None,
    output_format=None
    ):
    """
    Reads mapchete configuration file as well as the additional parameters (if
    available) and merges them into a unambiguous and complete set of
    configuration parameters.
    - Additional parameters (e.g. from CLI) always overwrite parameters coming
      from the mapchete configuration file.
    - If any parameter is invalid or not available, an exception is thrown.
    - Configuration parameters are returned as a dictionary.
    """

    additional_parameters = {
       "zoom": zoom,
       "bounds": bounds,
       "output_path": output_path,
       "output_format": output_format
       }

    out_config = {}

    # Analyze input parameters #
    ############################

    ## Check mapchete config file
    try:
        assert os.path.isfile(mapchete_file)
    except:
        raise IOError("%s is not available" % mapchete_file)
    ## Read raw configuration.
    with open(mapchete_file, "r") as config_file:
        raw_config = yaml.load(config_file.read())

    ## Check mapchete process file
    try:
        mapchete_process_file = raw_config["process_file"]
    except:
        raise Exception("'process_file' parameter is missing")
    rel_path = mapchete_process_file
    config_dir = os.path.dirname(os.path.realpath(mapchete_file))
    abs_path = os.path.join(config_dir, rel_path)
    mapchete_process_file = abs_path
    try:
        assert os.path.isfile(mapchete_process_file)
    except:
        raise IOError("%s is not available" % mapchete_process_file)
    ### zoom level(s)
    try:
        config_zoom = raw_config["process_zoom"]
        zoom = [config_zoom]
    except:
        zoom = None
        try:
            minzoom = raw_config["process_minzoom"]
            maxzoom = raw_config["process_maxzoom"]
            zoom = [minzoom, maxzoom]
        except:
            zoom = None
    #### overwrite zoom if provided in additional_parameters
    if additional_parameters["zoom"]:
        zoom = additional_parameters["zoom"]
    #### if zoom still empty, throw exception
    if not zoom:
        raise Exception("No zoom level(s) provided.")
    if len(zoom) == 1:
        zoom_levels = zoom
    elif len(zoom) == 2:
        for i in zoom:
            try:
                assert i>=0
            except:
                raise ValueError("Zoom levels must be greater 0.")
        if zoom[0] < zoom[1]:
            minzoom = zoom[0]
            maxzoom = zoom[1]
        else:
            minzoom = zoom[1]
            maxzoom = zoom[0]
        zoom_levels = range(minzoom, maxzoom+1)
    else:
        raise ValueError(
            "Zoom level parameter requires one or two value(s)."
            )
    out_config["zoom_levels"] = zoom_levels

    ### check overall validity of mapchete configuration object at zoom levels
    config = mapchete.MapcheteConfig(mapchete_file)
    # TODO in MapcheteConfig
    for zoom in zoom_levels:
        try:
            # checks if input files are valid etc.
            assert config.is_valid_at_zoom(zoom)
        except:
            raise Exception(config.explain_validity_at_zoom(zoom))

    ### process_bounds
    try:
        config_bounds = raw_config["process_bounds"]
        bounds = config_bounds
    except:
        bounds = None
    #### overwrite if bounds are provided explicitly
    if additional_parameters["bounds"]:
        # validate bounds
        try:
            assert len(additional_parameters["bounds"]) == 4
        except:
            raise ValueError("Invalid number of process bounds.")
        bounds = additional_parameters["bounds"]
    #### write bounds for every zoom level
    bounds_per_zoom = {}

    for zoom_level in zoom_levels:
        input_files = config.at_zoom(zoom)["input_files"]
        bboxes = []
        for input_file, rel_path in input_files.iteritems():
            if rel_path:
                config_dir = os.path.dirname(os.path.realpath(mapchete_file))
                abs_path = os.path.join(config_dir, rel_path)
                with rasterio.open(abs_path, 'r') as raster:
                    left, bottom, right, top = raster.bounds
                    ul = left, top
                    ur = right, top
                    lr = right, bottom
                    ll = left, bottom
                    bboxes.append(Polygon([ul, ur, lr, ll]))
        files_area = cascaded_union(bboxes)
        out_area = files_area
        if bounds:
            left, bottom, right, top = bounds
            ul = left, top
            ur = right, top
            lr = right, bottom
            ll = left, bottom
            user_bbox = Polygon([ul, ur, lr, ll])
            out_area = files_area.intersection(user_bbox)
            try:
                assert out_area.geom_type in [
                    "Polygon",
                    "MultiPolygon",
                    "GeometryCollection"
                    ]
            except:
                # TODO if process area is empty, remove zoom level from zoom
                # level list
                out_area = Polygon()
        bounds_per_zoom[zoom_level] = out_area
    out_config["process_area"] = bounds_per_zoom

    ### output_path

    ### output_format

    return out_config
