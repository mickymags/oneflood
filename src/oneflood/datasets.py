import earthaccess 

from oneflood.oneflood_utils import get_bbox_timezone, utc_2_local, local_2_utc

def obtain_dswxs1(
        date_of_int : str,
        xmin : float, 
        ymin : float, 
        xmax : float, 
        ymax : float,
        time_of_int : str = "12:00:00",
        buffer : int = 12,
        utc: bool = True
) -> str:

    """
    This function will obtain the DSWx-S1 surface water map product for a date and time of interest 
    and a region of interest. It will return the path of the directory to which all of the DSWx-S1 images 
    were downloaded

    Parameters 
    ---
    date_of_int
        - str in YYYY-MM-dd format
    time_of_int 
        - str in HH:mm:ss format
    xmin 
        - float of minimum longitude 
    ymin 
        - float of minimum latitude 
    xmax 
        - float of maximum longitude 
    ymax
        - float of maximum latitude
    buffer
        - integer. This will be how many hours before and after the date
    utc 
        - boolean. Default = True. If this is set to False, the datetime_of_int must be given 
            in the local civil time of the region of interest rather than UTC. 

    Notes: 

    Because the default time zone is UTC, the default time_of_int is 12:00 noon, and 
    the default buffer is 12 hours, the default start and end date

    """

    ### Construct a datetime string in ISO format 
    iso_datetime = date_of_int + 'T' + time_of_int

    # If utc boolean is set to False, convert to local time 
    