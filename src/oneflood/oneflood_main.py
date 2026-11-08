import argparse 

from .oneflood_utils import setup_earthdata_netrc, region_to_bounds
from .datasets import dataset_info

def main(): 
    parser = argparse.ArgumentParser(
        prog = "oneflood",
        description = "Facilitated access to Level 3 Surface Water Products"
    )

    # Creae the subcommands 
    subparsers = parser.add_subparsers(
        dest = "command",
        required = True
    )

    #####################################################
    #               Command 1: setup_netrc              #
    #####################################################

    netrc_parser = subparsers.add_parser(
        "setup-netrc",
        help = "Set up Netrc authentication"
    )

    netrc_parser.add_argument(
        "--username",
        dest = "earthdata_username",
        required = True,
        help = "Earthdata username"
    )

    netrc_parser.add_argument(
        "--password",
        dest = "earthdata_password",
        required = True,
        help = "Earthdata Password"
    )

    # Associate this command with its function 
    netrc_parser.set_defaults(func = setup_earthdata_netrc)

    ##########################################################
    #           Command 2: Dataset_info                      #
    ##########################################################
    info_parser = subparsers.add_parser(
        "dataset_info", 
        help = "Determine availability and info of surface water products"
    )

    region = info_parser.add_mutually_exclusive_group(required = True)

    region.add_argument(
        "--bbox", 
        nargs = 4, 
        type = float,
        metavar = ("XMIN", "YMIN", "XMAX", "YMAX"),
        help = "Bounding Box in latitude and longitude. Format: mininimum_longitude, minimum_latitude, \
                maximum_longitude, maximum_latitude. Mutually exclusive with shapefile and geojson arguments. "
    )

    region.add_argument(
        "--shapefile", 
        help = "Absolute path to a shapefile, must end in .shp defining the region of interest in latitude/longitude \
            (ESPG:4326). Mutually exclusive with bbox and geojson arguments."
    )

    region.add_argument(
        "--geojson",
        help = "Absolute path to a geojson file defining the region of interest in latitude/longitude (EPSG:4326). \
            Mutually exclusive with shapefile and bbox arguments."
    )

    info_parser.add_argument(
        "--date", 
        dest = "date_of_int",
        required = True,
        help = "Date in 'YYYY-MM-DD' format", 
    )

    info_parser.add_argument(
        "--time", 
        dest = "time_of_int",
        default = "12:00:00",
        help = "Optional Argument. Time in HH:MM:SS format. If your time is in local time, set the utc_flag to False", 
    )

    info_parser.add_argument(
        "--buffer", 
        type = int, 
        default = 12, 
        help = "Optional argument. Number of hours before and after time of interest to search" 
    )

    info_parser.add_argument(
        "--utc_flag", 
        dest = "utc",
        action = argparse.BooleanOptionalAction,
        default = True,
        help = "Optional argument. Flag to indicate whether time is in utc or not. True indicates that the time given\
            in the time argument is in UTC. False indicates that the time given is in local time\
                Will be set to True by default."    
    )

    # Associate this command with its function
    info_parser.set_defaults(func = dataset_info)

    """
    ########################################################
    #         Command 2: convert UTC 2 Local               # 
    ########################################################
    
    utc2local_parser = subparsers.add_parser(
        "utc2local",
        help = "Convert UTC to Local"
    )

    utc2local_parser.add_argument(
        "--xmin",
        dest = "xmin"
        help = "Minimum Longitude"
    )

    utc2local_parser.add_argument(
        "--ymin",
        help = "Minimum Latitude"
    )

    utc2local_parser.add_argument(
        "--xmax",
        help = "Maximum Longitude"
    )

    utc2local_parser.add_argument(
        "--ymax",
        help = "Maximum Latitude"
    )

    utc2local_parser.add_argument(
        "--utc_time",
        help = "time in UTC, in YYYYMMddThhmmss format"
    )

    # Associate this command with its function 
    utc2local_parser.set_defaults(func = convert_utc_to_local)
    """

    # Parse the command-line arguments 
    args = parser.parse_args()

    # Extract the function and its keyword arguments 
    function = args.func
    function_args = vars(args).copy()

    # Remove CLI-specific entries
    function_args.pop("command")
    function_args.pop("func")

    if any(k in function_args for k in ("bbox", "shapefile", "geojson")):
        bounds = region_to_bounds(
            function_args.pop("bbox", None),
            function_args.pop("shapefile", None), 
            function_args.pop("geojson", None),
        ) 

        function_args.update(zip(("xmin", "ymin", "xmax", "ymax"), bounds))
    # Execute the selected function using keyword arguments
    function(**function_args)

if __name__ == "__main__":
    main()


