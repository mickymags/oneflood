import os 
from pathlib import Path
import boto3 
import earthaccess 
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo 
from timezonefinder import timezone_at

"""
Considering implementation of a bounding box class

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
"""
def get_bbox_timezone(
        xmin: float, 
        ymin: float, 
        xmax: float, 
        ymax: float
) -> ZoneInfo: 
    """
    Get the time zone at the center of a geographic bounding box. 
    """

    if not (-180 <= xmin <= 180 and -180 <= xmax <= 180):
        raise ValueError("Longitudes must be between -180 and 180")

    if not (-90 <= ymin <= 90 and -90 <= ymax <= 90):
        raise ValueError("Latitudes must be between -90 and 90.")

    if xmin >= xmax or ymin >= ymax: 
        raise ValueError("Minimum bounds must not exceed maximum bounds.")

    # Find the center of the bounding box 
    x_center = (xmin + xmax) / 2
    y_center = (ymin + ymax) / 2

    # Identify the IANA timezone at the center of the bounding box
    tz_name = timezone_at(lng=x_center, lat=y_center)

    # Error Handling for Timezone Name
    if tz_name is None: 
        raise ValueError(
            f"Could not determine a time zone at longitude={x_center}, latitude = {y_center}")

    # Check to see if any part of the bounding box lies in a different time zone. 
    # If it does, notify the user. 
    tz_ll = timezone_at(lng = xmin, lat = ymin)
    tz_ul = timezone_at(lng = xmin, lat=ymax)
    tz_lr = timezone_at(lng = xmax, lat=ymin)
    tz_ur = timezone_at(lng=xmax, lat=ymax)

    bool1 = tz_ll == tz_ul == tz_lr == tz_ur  # Boolean to check if all corners of bounding box occupy same time zone.

    # If corners of bounding box occupy different time zones, notify the user and output the time zone name in the center
    if bool1 == False: 
        print("WARNING Bounding Box occupies more than one time zone!")
        print(f"Time Zone for center of bounding box: {tz_name}")

    # If bounding box falls all within one time zone, output the time zone. 
    else: 
        print("Bounding box occupies only one time zone.")
        print(f"Time zone for all of bounding box: {tz_name}")

    return ZoneInfo(tz_name)

def utc_2_local(
        datetime_string : str, 
        xmin: float, 
        ymin: float, 
        xmax: float, 
        ymax: float
) -> str: 
    """
    Convert an ISO 8601 UTC datetime string to local civil time.
    """

    dt = datetime.fromisoformat(
        datetime_string.replace("Z", "+00:00")
    )
    # Assume input is UTC 
    if dt.tzinfo is None: 
        dt = dt.replace(tzinfo = timezone.utc)
    else: 
        dt = dt.astimezone(timezone.utc)

    local_tz = get_bbox_timezone(xmin, ymin, xmax, ymax)

    return dt.astimezone(local_tz).isoformat()

def local_2_utc(
        datetime_string : str,
        xmin : float, 
        ymin : float, 
        xmax : float, 
        ymax : float, 
        fold: int= 0,
) -> str: 
    """
    Convert local civil time to UTC 

    For ambiguous times during the fall daylight savings time transition, 
    fold = 0  selects the earlier occurrence, whereas fold = 1 selects the later occurrence. 

    Input is interpreted as local civil time in ISO 8601 datetime format. 
    """
    if fold not in (0, 1): 
        raise ValueError("fold must be 0 or 1.")

    dt = datetime.fromisoformat(
        datetime_string.replace("Z", "+00:00")
    )

    local_tz = get_bbox_timezone(xmin, ymin, xmax, ymax)

    if dt.tzinfo is None: 
        dt = dt.replace(tzinfo=local_tz, fold=fold)

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def time_bufferer(
        datetime_of_int : str, 
        buffer: int = 12, 
) -> list: 
    """
    Takes as input a datetime string and a buffer for number of hours and 
    returns a list. The first element of the list will be start_time x hours before the 
    datetime_of_int and the second element of the list will be end_time x hours after the 
    datetime_of_int, where x is the buffer

    Parameters 
    ---
    datetime_of_int: str 
        - String representing a date and time in ISO 8601 format. 
    buffer: 
        - Integer representing the number of hours to buffer in either direction.
    """

    # Convert ISO 8601 string to datetime object
    dt = datetime.fromisoformat(datetime_of_int)

    start_time = dt - timedelta(hours = buffer)
    end_time = dt + timedelta(hours = buffer)

    return [start_time.isoformat(), end_time.isoformat()]

bounds = {
    "xmin": -90.9, #-85.72,  
    "ymin": 37.2,  #34.35, 
    "xmax": -90.7, #-85.30,
    "ymax": 37.5   #34.68 
}

utc_time = local_2_utc(
    "2026-07-12T07:00:00",
    **bounds
)

buffer_test = time_bufferer(utc_time)

print(f"buffer_test: {buffer_test}")

"""
local_time = utc_2_local(
    "2026-07-11T12:00:00Z",
    **bounds
)

print(local_time)
"""

print(utc_time)

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
                         xmin: float, 
                         xmax: float): 
    """
    This function will take as input a UTC time in the format. It is intended for use 
    with Flood maps that record the acquisition time in UTC and will let the user 
    know what the local time is when the flood map was acquired. 

    Parameters 
    -----------------
    utc_time: str
        - we expect this to be formatted as follows: YYYYMMDDThhmmss. 
        So October 13, 2026 at 3:25:00 p.m. would be 20261013T152500
    xmin: float 
        - Minimum Longitude of the study area in decimal degrees. 
    xmax: float 
        - Maximum longitude of the study area in decimal degrees

    Notes 
    -------------------
    Please note that this function uses a simple approximation for time zone and may be different than 
    the timezone 
    
    This function should check if the bounding box occupies more than one time zone. 

    If the bounding box occupies only one time zone, the function will output the 
    local date and time corresponding to the utc_time entered. 

    If the bounding box occupies more than one time zone, the function will notify the user that 
    the bounding box occupies multiple time zones, and will output the local time that the majority 
    of the bounding box occupies. 
    """

    # Error handling for longitude bounds outside their range
    if (xmin <= -180 or xmin >= 180) or (xmax <= -180 or xmax >= 180):
        raise ValueError("Longitude bounds must be between -180 and 180 degrees")

    if xmax <= xmin:
        raise ValueError("Minimum longitude must be less than the maximum longitude")

    # Timezones are offset by 15 degrees of longitude 
    offset = timedelta

    date = utc_time[0:8]
    print(date)

    return date


