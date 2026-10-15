import argparse 

from oneflood.oneflood_utils import setup_earthdata_netrc, convert_utc_to_local

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

    # Execute the selected function using keyword arguments
    function(**function_args)

if __name__ == "__main__":
    main()


