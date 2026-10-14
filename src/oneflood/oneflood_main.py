import argparse 
import sys 

from oneflood_utils import setup_earthdata_netrc, area_of_interest


#COMMAND_MODULES = [setup_earthdata_netrc]

def main(): 
    parser = argparse.ArgumentParser(
        description="Download a file from NASA Earthdata."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    ###
    parser.add_argument(
        "--earthdata_username",
        help = "NASA Earthdata Login Username. If you do not have an Earthdata account, you can create one at https://urs.earthdata.nasa.gov/users/new",
        required = True
    )

    parser.add_argument(
        "--earthdata_password"
        help = "NASA Earthdata Login Username. If you do not have an Earthdata account, you can create one at https://urs.earthdata.nasa.gov/users/new",
        required = True
    )

    parser.add_argument(
        "--bbox",
        nargs = 4,
        type = float,
        metavar = ("Xmin", "Ymin", "Xmax", "Ymax"),
        help = "Bounding Box to be fed as floats in units of longitidue in the order (xmin, ymin, xmax, ymax)."
    )

    parser.add_argument(
        "--date_of_interest",
        help = "Date of interest in YYYYMMdd format. e.g. June 26, 2026 would be 20260626",
        required = False
    )

    parser.add_argument(
        "--time of interest",
        help = "Time of interest in the time zone the majority of your region of interest is in. Format: "
    )

    args = parser.parse_args()

    setup_earthdata_netrc(
        args.earthdata_username,
        args.earthdata_password
    )

    area_of_interest(
        args.bbox[0],
        args.bbox[1],
        args.bbox[2],
        args.bbox[3]
    )
    
if __name__ ==  "__main__":
    main()

