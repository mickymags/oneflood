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
def find_earliest_date(iso_dates):
  """
  This function will navigate through a list of dates in ISO 8601 format (YYYY-MM-ddThh:mm:ss.sss format)
  and return the earliest date (also in ISO format).
  """

  earliest = min(
    iso_dates, 
    key = lambda d: datetime.strptime(d, "%Y-%m-%dT%H:%M.%f")
  )

  dt = datetime.strptime(earliest, "%Y-%m-%dT%H:%M.%f")

  return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

def find_latest_date(iso_dates): 
  """
  This function will navigate through a list of datetimes in ISO 8601 format (YYYY-MM-ddThh:mm:ss.sss)
  and return the latest date (also in ISO format).
  """

  latest = max(
    iso_dates, 
    key = lambda d: datetime.strptime(d, "%Y-%m-%dT%H:%M.%f")
  )

  dt = datetime.strptime(latest, "%Y-%m-%dT%H:%M.%f")

  return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

def military_to_civil(mil_date):
  """
  This function will take as input a string containing a datetime in ISO 8601 format (YYYY-MM-ddThh:mm:ss.sss)
  and will return a list containing two strings. The first string will contain the date in YYYY-MM-dd format 
  and the second string will contain the time (in hh:mm am/pm format).
  """

  dt = datetime.fromisoformat(mil_date)

  mydate = dt.strftime("%Y-%m-%d")
  std_time = dt.strftime("%I:%M %p").lstrip("0")

  return [mydate, std_time]

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
        #print("Bounding box occupies only one time zone.")
        #print(f"Time zone for all of bounding box: {tz_name}")
        pass

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

def check_4_netrc() -> None: 
    """
    This function will check if the user has a .netrc file in their root directory. 
    A .netrc file is how NASA Earthdata authenticates data downloads from command line. 
    Note that this function will not check if the .netrc contains a valid username or password, 
    but only whether or not the file exists.
    """

    if os.name != "nt": 
        netrc_path = Path.home() / ".netrc"
    else: 
        netrc_path = Path.home() / "_netrc"

    if netrc_path.exists(): 
        pass
        #print(f"Found existing netrc file: {netrc_path}")
    else:
        raise FileNotFoundError("No .netrc file exists! Please setup earthdata netrc as shown in instructions")
    

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


def vfm_tiler(lon, lat):
  """
  This function will report the VFM tile associated with a certain latitude/longitude pair. 

  Parameters 
  --- 
  lon = longitude in decimal degrees 
  lat = latitude in decmial_degrees
  """
  if lat > 75:
    if lon > 90 and lon < 105:
      vfm_tile = 50
    if lon > 105 and lon < 120:
      vfm_tile = 51
  if lat > 60 and lat < 75:
    if lon < -165:
      vfm_tile = 1
    if lon > -165 and lon < -150:
      vfm_tile = 2
    if lon > -150 and lon < -135:
      vfm_tile = 3
    if lon > -135 and lon < -120:
      vfm_tile = 4
    if lon > -120 and lon < -105:
      vfm_tile = 5
    if lon > -105 and lon < -90:
      vfm_tile = 6
    if lon > -90 and lon < -75:
      vfm_tile = 7
    if lon > -75 and lon < -60:
      vfm_tile = 8
    if lon > -60 and lon < -45:
      vfm_tile = 130
    if lon > -45 and lon < -30:
      vfm_tile = 131
    if lon > -30 and lon < -15:
      vfm_tile = 132
    if lon > -15 and lon < 0:
      vfm_tile = 42
    if lon > 0 and lon < 15:
      vfm_tile = 43
    if lon > 15 and lon < 30:
      vfm_tile = 44
    if lon > 30 and lon < 45:
      vfm_tile = 45
    if lon > 45 and lon < 60:
      vfm_tile = 46
    if lon > 60 and lon < 75:
      vfm_tile = 47
    if lon > 75 and lon < 90:
      vfm_tile = 48
    if lon > 90 and lon < 105:
      vfm_tile = 49
    if lon > 105 and lon < 120:
      vfm_tile = 52
    if lon > 120 and lon < 135:
      vfm_tile = 53
    if lon > 135 and lon < 150:
      vfm_tile = 54
    if lon > 150 and lon < 165:
      vfm_tile = 55
    if lon > 165 and lon < 180:
      vfm_tile = 56
  if lat > 45 and lat < 60:
    if lon < -165:
      vfm_tile = 9
    if lon > -165 and lon < -150:
      vfm_tile = 10
    if lon > -150 and lon < -135:
      vfm_tile = 129
    if lon > -135 and lon < -120:
      vfm_tile = 11
    if lon > -120 and lon < -105:
      vfm_tile = 12
    if lon > -105 and lon < -90:
      vfm_tile = 13
    if lon > -90 and lon < -75:
      vfm_tile = 14
    if lon > -75 and lon < -60:
      vfm_tile = 15
    if lon > -60 and lon < -45:
      vfm_tile = 16
    if lon > -15 and lon < 0:
      vfm_tile = 57
    if lon > 0 and lon < 15:
      vfm_tile = 58
    if lon > 15 and lon < 30:
      vfm_tile = 59
    if lon > 30 and lon < 45:
      vfm_tile = 60
    if lon > 45 and lon < 60:
      vfm_tile = 61
    if lon > 60 and lon < 75:
      vfm_tile = 62
    if lon > 75 and lon < 90:
      vfm_tile = 63
    if lon > 90 and lon < 105:
      vfm_tile = 64
    if lon > 105 and lon < 120:
      vfm_tile = 65
    if lon > 120 and lon < 135:
      vfm_tile = 66
    if lon > 135 and lon < 150:
      vfm_tile = 67
    if lon > 150 and lon < 165:
      vfm_tile = 68
    if lon > 165 and lon < 180:
      vfm_tile = 69
  if lat > 30 and lat < 45:
    if lon > -135 and lon < -120:
      vfm_tile = 17
    if lon > -120 and lon < -105:
      vfm_tile = 18
    if lon > -105 and lon < -90:
      vfm_tile = 19
    if lon > -90 and lon < -75:
      vfm_tile = 20
    if lon > -75 and lon < -60:
      vfm_tile = 21
    if lon > -15 and lon < 0:
      vfm_tile = 70
    if lon > 0 and lon < 15:
      vfm_tile = 71
    if lon > 15 and lon < 30:
      vfm_tile = 72
    if lon > 30 and lon < 45:
      vfm_tile = 73
    if lon > 45 and lon < 60:
      vfm_tile = 74
    if lon > 60 and lon < 75:
      vfm_tile = 75
    if lon > 75 and lon < 90:
      vfm_tile = 76
    if lon > 90 and lon < 105:
      vfm_tile = 77
    if lon > 105 and lon < 120:
      vfm_tile = 78
    if lon > 120 and lon < 135:
      vfm_tile = 79
    if lon > 135 and lon < 150:
      vfm_tile = 80
    if lon > 150 and lon < 165:
      vfm_tile = 81
  if lat > 15 and lat < 30:
    if lon > -165 and lon < -150:
      vfm_tile = 133
    if lon > -120 and lon < -105:
      vfm_tile = 22
    if lon > -105 and lon < -90:
      vfm_tile = 23
    if lon > -90 and lon < -75:
      vfm_tile = 24
    if lon > -75 and lon < -60:
      vfm_tile = 25
    if lon > -30 and lon < -15:
      vfm_tile = 82
    if lon > -15 and lon < 0:
      vfm_tile = 83
    if lon > 0 and lon < 15:
      vfm_tile = 84
    if lon > 15 and lon < 30:
      vfm_tile = 85
    if lon > 30 and lon < 45:
      vfm_tile = 86
    if lon > 45 and lon < 60:
      vfm_tile = 87
    if lon > 60 and lon < 75:
      vfm_tile = 88
    if lon > 75 and lon < 90:
      vfm_tile = 89
    if lon > 90 and lon < 105:
      vfm_tile = 90
    if lon > 105 and lon < 120:
      vfm_tile = 91
    if lon > 120 and lon < 135:
      vfm_tile = 92
  if lat > 0 and lat < 15:
    if lon > -105 and lon < -90:
      vfm_tile = 26
    if lon > -90 and lon < -75:
      vfm_tile = 27
    if lon > -75 and lon < -60:
      vfm_tile = 28
    if lon > -60 and lon < -45:
      vfm_tile = 29
    if lon > -30 and lon < -15:
      vfm_tile = 93
    if lon > -15 and lon < 0:
      vfm_tile = 94
    if lon > 0 and lon < 15:
      vfm_tile = 95
    if lon > 15 and lon < 30:
      vfm_tile = 96
    if lon > 30 and lon < 45:
      vfm_tile = 97
    if lon > 45 and lon < 60:
      vfm_tile = 98
    if lon > 60 and lon < 75:
      vfm_tile = 99
    if lon > 75 and lon < 90:
      vfm_tile = 100
    if lon > 90 and lon < 105:
      vfm_tile = 101
    if lon > 105 and lon < 120:
      vfm_tile = 102
    if lon > 120 and lon < 135:
      vfm_tile = 103
  if lat > -15 and lat < 0:
    if lon < -165:
      vfm_tile = 136
    if lon > -90 and lon < -75:
      vfm_tile = 30
    if lon > -75 and lon < -60:
      vfm_tile = 31
    if lon > -60 and lon < -45:
      vfm_tile = 32
    if lon > -45 and lon < -30:
      vfm_tile = 33
    if lon > 0 and lon < 15:
      vfm_tile = 104
    if lon > 15 and lon < 30:
      vfm_tile = 105
    if lon > 30 and lon < 45:
      vfm_tile = 106
    if lon > 45 and lon < 60:
      vfm_tile = 107
    if lon > 75 and lon < 90:
      vfm_tile = 108
    if lon > 90 and lon < 105:
      vfm_tile = 109
    if lon > 105 and lon < 120:
      vfm_tile = 110
    if lon > 120 and lon < 135:
      vfm_tile = 111
    if lon > 135 and lon < 150:
      vfm_tile = 112
    if lon > 150 and lon < 165:
      vfm_tile = 134
  if lat > -30 and lat < -15:
    if lon > -75 and lon < -60:
      vfm_tile = 34
    if lon > -60 and lon < -45:
      vfm_tile = 35
    if lon > -45 and lon < -30:
      vfm_tile = 36
    if lon > 0 and lon < 15:
      vfm_tile = 113
    if lon > 15 and lon < 30:
      vfm_tile = 114
    if lon > 30 and lon < 45:
      vfm_tile = 115
    if lon > 45 and lon < 60:
      vfm_tile = 116
    if lon > 105 and lon < 120:
      vfm_tile = 117
    if lon > 120 and lon < 135:
      vfm_tile = 118
    if lon > 135 and lon < 150:
      vfm_tile = 119
    if lon > 150 and lon < 165:
      vfm_tile = 120
    if lon > 165 and lon < 180:
      vfm_tile = 135
  if lat > -45 and lat < -30:
    if lon > -75 and lon < -60:
      vfm_tile = 37
    if lon > -60 and lon < -45:
      vfm_tile = 38
    if lon > 15 and lon < 30:
      vfm_tile = 121
    if lon > 30 and lon < 45:
      vfm_tile = 122
    if lon > 105 and lon < 120:
      vfm_tile = 123
    if lon > 120 and lon < 135:
      vfm_tile = 124
    if lon > 135 and lon < 150:
      vfm_tile = 125
    if lon > 150 and lon < 165:
      vfm_tile = 126
    if lon > 165 and lon < 180:
      vfm_tile = 127
  if lat > -60 and lat < -45:
    if lon > -90 and lon < -75:
      vfm_tile = 39
    if lon < -75 and lon < -60:
      vfm_tile = 40
    if lon < -60 and lon < -45:
      vfm_tile = 41
    if lon > 165:
      vfm_tile = 128

  return vfm_tile