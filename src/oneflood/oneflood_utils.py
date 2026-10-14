import os 
from pathlib import Path
import boto3 
import earthaccess 
import datetime

class bounding_box: 
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin = xmin 
        self.ymin = ymin 
        self.xmax = xmax 
        self.ymax = ymax

    def as_list(self): 
        print("xmin:", self.xmin)
        return [self.xmin, self.ymin, self.xmax, self.ymax]

def area_of_interest(xmin, ymin, xmax, ymax):

    my_bbox = bounding_box(xmin, ymin, xmax, ymax)

    return my_bbox.as_list()

def setup_earthdata_netrc(earthdata_username, earthdata_password):
    """
    setup_earthdata_netrc will create a .netrc file in the user's home directory such that 
    it will be able to access data stored on NASA Earthdata. 
    earthdata_username = string, 
    earthdata_password = string
    An account can be made for free at https://urs.earthdata.nasa.gov/users/new
    """
    if os.name != "nt":
        netrc_path = Path.home() / ".netrc"
    else: 
        netrc_path = Path.home() / "_netrc"

    machine = "urs.earthdata.nasa.gov"

    # Check whether netrc already exists 
    if netrc_path.exists(): 
        print(f"Found existing netrc file: {netrc_path}")

        contents = netrc_path.read_text() 

        if machine in contents: 
            print("Earthdata entry already exists in netrc.")
            return 
    
    username = earthdata_username
    password = earthdata_password 
    
    entry = (
        f"machine {machine}\n"
        f"  login {earthdata_username}\n"
        f"  password {earthdata_password}\n"
    )

    with netrc_path.open("a") as f: 
        f.write(entry)
    
    # Restrict permissions on Unix (Mac/Linux)
    if os.name != "nt":
        netrc_path.chmod(0o600)
    
    print(f"Earthdata credentials stored in {netrc_path}")

    print("u:", username)
    print("pass:", password)


def convert_utc_to_local(utc_time : str, 
                         bbox: bounding_box): 
    """
    This function will take as input a UTC time in the format. It is intended for use 
    with Flood maps that record the acquisition time in UTC and will let the user 
    know what the local time is when the flood map was acquired. 

    Parameters 
    -----------------
    utc_time: str
        - we expect this to be formatted as follows: YYYYMMDDThhmmss. 
        So October 13, 2026 at 3:25:00 p.m. would be 20261013T152500
    bbox: of type bounding_box (defined by bounding_box class above)

    Notes 
    -------------------
    This function should check if the bounding box occupies more than one time zone. 

    If the bounding box occupies only one time zone, the function will output the 
    local date and time corresponding to the utc_time entered. 

    If the bounding box occupies more than one time zone, the function will notify the user that 
    the bounding box occupies multiple time zones, and will output the local time that the majority 
    of the bounding box occupies. 
    """

    date = utc_time[0:8]
    print(date)

    return date


