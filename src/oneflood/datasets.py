import earthaccess 
from datetime import datetime
import boto3 
from botocore.client import Config 
from botocore import UNSIGNED

from oneflood.oneflood_utils import (
    get_bbox_timezone, utc_2_local, 
    local_2_utc, time_bufferer,
    check_4_netrc, vfm_tiler,
    find_earliest_date, 
    find_latest_date, 
    military_to_civil
)

dataset_info_dict = {
    "DSWx-NI": {
        "start_date": "",
        "end_date": None,
        "minimum_latitude": 0,
        "maximum_latitude": 0,
        "latency": 0
    },
    "DSWx-S1": {
        "start_date": "2023-12-01",
        "end_date": None,
        "minimum_latitude": -84,
        "maximum_latitude": 84,
        "latency": 0
    },
    "DSWx-HLS": {
        "start_date": "2016-01-01",
        "end_date": None,
        "minimum_latitude": -84,
        "maximum_latitude": 84,
        "latency": 0
    },
    "MCDWD": {
        "start_date": "",
        "end_date": None,
        "minimum_latitude": 0,
        "maximum_latitude": 0,
        "latency": 0
    },
    "VFM": {
        "start_date": "",
        "end_date": None,
        "minimum_latitude": 0,
        "maximum_latitude": 0,
        "latency": 0
    },
}

dswx_s1_start_date = dataset_info_dict["DSWx-S1"]["start_date"]

#print(f' dswxs1 sd: {dswx_s1_start_date}')


def check_4_dswxs1(
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
    the default buffer is 12 hours, the default start datetime will be 12:01 a.m. 
    on the date of interest and the default end datetime will be 11:59 p.m. on the date of interest
    in UTC. 

    """

    ##############################################################
    #    Step 1: Obtain start times and end times                #
    ##############################################################

    ### Construct a datetime string in ISO format 
    input_iso_datetime = date_of_int + 'T' + time_of_int

    #print(f'Datetime of interest: {input_iso_datetime}')

    # If utc boolean is set to False, convert from local time to UTC 
    if utc == False:
        utc_datetime = local_2_utc(input_iso_datetime)

    # If utc boolean is set to true, set utc_datetime equal to the input datetime
    else: 
        utc_datetime = input_iso_datetime

    #print(f'UTC Datetime of interest: {utc_datetime}')

    start_and_end_times = time_bufferer(utc_datetime, buffer)

    start_time_utc = start_and_end_times[0]
    end_time_utc = start_and_end_times[1]

    #print(f'Start Time: {start_time_utc}')
    #print(f'End Time: {end_time_utc}')


    ######################################################
    #     Step 2: Check for DSWx-S1 files                # 
    ######################################################

    # Check for netrc file 
    check_4_netrc() 

    # Download files with earthaccess 
    dswxs1_results = earthaccess.search_data(
        short_name = "OPERA_L3_DSWX-S1_V1",
        cloud_hosted = True, 
        temporal = (start_time_utc, end_time_utc),
        bounding_box = (xmin, ymin, xmax, ymax)
    )

    num_results = len(dswxs1_results)

    if num_results == 0:
        dswxs1_return_string = "DSWx-S1 is not available for your region and time period of interest"
    else: 
        """
        first_result = dswxs1_results[0]

        temporal = first_result['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']

        local_time = utc_2_local(temporal, xmin, ymin, xmax, ymax)

        date = local_time[:10]
        time = local_time[11:-6]

        time_obj = datetime.strptime(time, "%H:%M:%S")
        standard_time = time_obj.strftime("%I:%M %p")

        return_string = f"DSWx-S1 overpass occurred on {standard_time} local time on {date}"
        """
        dswxs1_start_times = []
        dswxs1_end_times = [] 

        # For each DSWx-S1 product found, do the following: 
        for j in dswxs1_results: 

            #### Find Start Time ####
            temp_s1_start = j['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']
            temp_s1_start = temp_s1_start[:-8] + '.000000'
            dswxs1_start_times.append(temp_s1_start)

            ##### Find End Time #####
            temp_s1_end = j['umm']['TemporalExtent']['RangeDateTime']['EndingDateTime']
            temp_s1_end = temp_s1_end[:-8] + '.000000'
            dswxs1_end_times.append(temp_s1_end)

        # Find earliest start time and convert to local time 
        dswxs1_early_time = find_earliest_date(dswxs1_start_times)
        dswxs1_early_local = utc_2_local(dswxs1_early_time, xmin, ymin, xmax, ymax)
        dswxs1_early_civil = military_to_civil(dswxs1_early_local)

        # Find latest end time and convert to local time
        dswxs1_late_time = find_latest_date(dswxs1_end_times)
        dswxs1_late_local = utc_2_local(dswxs1_late_time, xmin, ymin, xmax, ymax)
        dswxs1_late_civil = military_to_civil(dswxs1_late_local)

        # If early and late products were acquired on the same date and same time 
        if dswxs1_early_civil == dswxs1_late_civil:
            dswxs1_return_string = f'DSWx-S1 was acquired at {dswxs1_early_civil[1]} (local time) on {dswxs1_late_civil[0]}'

        # If early and late products were acquired on the same date but at different times: 
        if dswxs1_early_civil[0] == dswxs1_late_civil[0] and dswxs1_early_civil[1] != dswxs1_late_civil[1]:
            dswxs1_return_string = f'DSWx-S1 was acquired between {dswxs1_early_civil[1]} and {dswxs1_late_civil[1]} (local time) on {dswxs1_late_civil[0]}'

        # If early and late products were acquired on different dates and different times: 
        if dswxs1_early_civil[0] != dswxs1_late_civil[0] and dswxs1_early_civil[1] != dswxs1_late_civil[1]:
            dswxs1_return_string = f'DSWx-S1 was acquired between {dswxs1_early_civil[1]} (local time) on {dswxs1_early_civil[0]} and {dswxs1_late_civil[1]} (local time) on {dswxs1_late_civil[0]}'

    return dswxs1_return_string

def check_4_dswxhls(
        date_of_int : str,
        xmin : float, 
        ymin : float, 
        xmax : float, 
        ymax : float,
        time_of_int : str = "12:00:00",
        buffer : int = 12,
        utc: bool = True
) -> str:
    ##############################################################
    #    Step 1: Obtain start times and end times                #
    ##############################################################

    ### Construct a datetime string in ISO format 
    input_iso_datetime = date_of_int + 'T' + time_of_int

    #print(f'Datetime of interest: {input_iso_datetime}')

    # If utc boolean is set to False, convert from local time to UTC 
    if utc == False:
        utc_datetime = local_2_utc(input_iso_datetime)

    # If utc boolean is set to true, set utc_datetime equal to the input datetime
    else: 
        utc_datetime = input_iso_datetime

    #print(f'UTC Datetime of interest: {utc_datetime}')

    start_and_end_times = time_bufferer(utc_datetime, buffer)

    start_time_utc = start_and_end_times[0]
    end_time_utc = start_and_end_times[1]

    ######################################################
    #     Step 2: Check for DSWx-S1 files                # 
    ######################################################
    
    # Check for netrc file 
    check_4_netrc() 
    
    # Download files with earthaccess 
    dswxhls_results = earthaccess.search_data(
        short_name = "OPERA_L3_DSWX-HLS_V1",
        cloud_hosted = True, 
        temporal = (start_time_utc, end_time_utc),
        bounding_box = (xmin, ymin, xmax, ymax)
    )

    num_dswxhls_results = len(dswxhls_results)
    #print(num_dswxhls_results)

    if num_dswxhls_results == 0:
        dswxhls_return_string = 'DSWx-HLS is not available for your time period and region of interest'
    else: 
        """
        first_hls = dswxhls_results[0]

        temp_hls = first_hls['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']

        print(f'temp_hls: {temp_hls}')
        hls_local_time = utc_2_local(temp_hls, xmin, ymin, xmax, ymax).split(".")[0]

        hls_date = hls_local_time[:10]
        hls_time = hls_local_time[11:]

        hls_time_obj = datetime.strptime(hls_time, "%H:%M:%S")
        hls_std_time = hls_time_obj.strftime("%I:%M %p")

        dswxhls_return_string = f"DSWx-HLS overpass occurred on {hls_std_time} local time on {hls_date}"

        return dswxhls_return_string
        """
        dswxhls_start_times = []
        dswxhls_end_times = []

        for i in dswxhls_results: 

            ####### Find Start Time ######
            temp_hls_start = i['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']

            temp_hls_start = temp_hls_start[:-8] + '.000000'
            print(temp_hls_start)

            dswxhls_start_times.append(temp_hls_start)

            ####### Find End Time ##########
            temp_hls_end = i['umm']['TemporalExtent']['RangeDateTime']['EndingDateTime']

            temp_hls_end = temp_hls_end[:-8] + '.000000'
            dswxhls_end_times.append(temp_hls_end)

        #print(dswxhls_start_times)
        #print(dswxhls_end_times)

        # Find Earliest time, convert to local time
        dswxhls_early_time = find_earliest_date(dswxhls_start_times)
        dswxhls_early_local = utc_2_local(dswxhls_early_time, xmin, ymin, xmax, ymax)
        dswxhls_early_civil = military_to_civil(dswxhls_early_local)

        # Find latest time, convert to local time 
        dswxhls_late_time = find_latest_date(dswxhls_end_times)
        dswxhls_late_local = utc_2_local(dswxhls_late_time, xmin, ymin, xmax, ymax)
        dswxhls_late_civil = military_to_civil(dswxhls_late_local)

        print(dswxhls_early_civil)
        print(dswxhls_late_civil)

        # If early and late products were acquired on the same date and same time
        if dswxhls_early_civil == dswxhls_late_civil:
            dswxhls_return_string = f'DSWx-HLS was acquired at {dswxhls_early_civil[1]} (local time) on {dswxhls_late_civil[0]}'

        # If early and late products were acquired on the same date but at different times
        if dswxhls_early_civil[0] == dswxhls_late_civil[0] and dswxhls_early_civil[1] != dswxhls_late_civil[1]:
            dswxhls_return_string = f'DSWx-HLS was acquired between {dswxhls_early_civil[1]} and {dswxhls_late_civil[1]} (local time) on {dswxhls_early_civil[0]}'

        # If early and late products were acquired on different dates and different times:
        if dswxhls_early_civil[0] != dswxhls_late_civil[0] and dswxhls_early_civil[1] != dswxhls_late_civil[1]:
            dswxhls_return_string = f'DSWx-HLS was acquired between {dswxhls_early_civil[1]} (local time) on {dswxhls_early_civil[0]} and {dswxhls_late_civil[1]} (local time) on {dswxhls_late_civil[0]}'

    return dswxhls_return_string

def check_4_vfm1day(
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
    This function will check for the VFM 1day GLB product. consider adding the VFM NRT product later.
    """

    tile1 = vfm_tiler(xmin, ymin)
    tile2 = vfm_tiler(xmin, ymax)
    tile3 = vfm_tiler(xmax, ymin)
    tile4 = vfm_tiler(xmax, ymax)

    tiles = [tile1, tile2, tile3, tile4]

    unique_tiles = []

    # Convert tiles to strings and add a leading zero if it is only double digits
    for i in tiles: 
        if i < 100:
            i = '0' + str(i)
        else: 
            i = str(i)

        if i not in unique_tiles:
            unique_tiles.append(i)

    # Convert VFM 
    formatted_date = date_of_int.replace('-', '/')

    # Initialize AWS
    cred = {
        "aws_access_key_id": "", 
        "aws_secret_access_key": "", 
        "config": Config(signature_version = UNSIGNED)
    }

    session = boto3.Session() 
    client = session.client('s3', **cred)

    vfm_start_times = []
    vfm_end_times = []

    for j in unique_tiles:
        paginator = client.get_paginator('list_objects_v2')

        vfm_params = {'Bucket': 'noaa-jpss',
                      'Prefix': 'JPSS_Blended_Products/VFM_1day_GLB/TIF/' + formatted_date \
                        + '/VIIRS-Flood-1day-GLB' + j}

        page_iterator = paginator.paginate(**vfm_params)

        for page in page_iterator:
            my_key = page['Contents'][0]['Key']
            redux_date = formatted_date.replace('/', '')
            my_key_split = my_key.split(redux_date)#[1][:7]
            vfm_start = my_key_split[1][:7]
            vfm_end = my_key_split[2][:7]
            #print(my_key)
            #print(my_key_split)

            vfm_start_iso = date_of_int + 'T' + vfm_start[:2] + ':' + vfm_start[2:4] + '.' + vfm_start[4:7]
            vfm_end_iso = date_of_int + 'T' + vfm_end[:2] + ':' + vfm_end[2:4] + '.' + vfm_end[4:7]

            vfm_start_times.append(vfm_start_iso)
            vfm_end_times.append(vfm_end_iso)


    vfm_early_time = find_earliest_date(vfm_start_times)
    vfm_late_time = find_latest_date(vfm_end_times)

    #print(f'vfm_early_time: {vfm_early_time}')
    vfm_local_early = utc_2_local(vfm_early_time, xmin, ymin, xmax, ymax)
    vfm_local_late = utc_2_local(vfm_late_time, xmin, ymin, xmax, ymax)

    vfm_readable_early = military_to_civil(vfm_local_early)
    vfm_readable_late = military_to_civil(vfm_local_late)

    #print(vfm_readable_early)
    #print(vfm_readable_late)

    # If early and late acqusition were on two different dates ...
    if vfm_readable_early[0] != vfm_readable_late[0]:
        vfm_string = f'VFM was acquired between {vfm_readable_early[1]} (local time) on {vfm_readable_early[0]} and {vfm_readable_late[1]} (local time) on {vfm_readable_late[0]}'
    else: 
        vfm_string = f'VFM was acquired between {vfm_readable_early[1]} and {vfm_readable_late[1]} (local time) on {vfm_readable_early[0]}'

    #print(vfm_string)

    return vfm_string


def dataset_info(
        date_of_int : str, 
        xmin : float, 
        ymin : float, 
        xmax : float, 
        ymax : float, 
        time_of_int : str = "12:00:00",
        buffer : int = 12, 
        utc: bool = True
) -> dict: 
    """
    This function will take as input a user-defined region and time period of interest, and will 
    output the availability and acquisition times of various flood products. 

    This function should check the user input and do several things based on the dataset_info_dict 
    dictionary located at the top of this code. 

        1. if the date requested is less than a week in the past, it should notify the user 
        of the latency of several products 

        2. if the date requested is outside of the range of availability of any of the products 
    """
    print("="*60)
    print("Requesting Availability of Surface Water Products")

    ############################################################################################################
    #                         Step 1: DSWx-S1
    ############################################################################################################

    ######### Step 1a: Check to see if requested date is within spatiotemporal bounds for DSWx-S1 ######### 

    print('='*60)
    print('DSWx-S1')        
    dswxs1_date = datetime.fromisoformat(dataset_info_dict["DSWx-S1"]["start_date"])
    user_date = datetime.fromisoformat(date_of_int)

    if user_date < dswxs1_date:
        print(f"DSWx-S1 is not available for this date. DSWx-S1 is only available after {dswxs1_date}")

    dswxs1_xmin = dataset_info_dict["DSWx-S1"]["minimum_latitude"]
    dswxs1_xmax = dataset_info_dict["DSWx-S1"]["maximum_latitude"]

    if xmax > dswxs1_xmax: #xmin < dswxs1_xmin: #or xmax > dswxs1_xmax:
        print(f"DSWx-S1 is not available for this region. DSWx-S1 is only available between {dswxs1_xmin} and {dswxs1_xmax} degrees latitude ")

    print('Checking for DSWx-S1 Products')
    dswxs1_check = check_4_dswxs1(
        date_of_int,
        xmin,
        ymin, 
        xmax, 
        ymax,
        time_of_int, 
        buffer, 
        utc
    )

    print('Checking for DSWx-HLS Products')
    dswxhls_check = check_4_dswxhls(
        date_of_int, 
        xmin, 
        ymin, 
        xmax, 
        ymax, 
        time_of_int, 
        buffer, 
        utc
    )

    print('Checking for VFM Products')
    vfm_check = check_4_vfm1day(
        date_of_int, 
        xmin,
        ymin, 
        xmax,
        ymax, 
        time_of_int, 
        buffer,
        utc
    )
    

    info_dict = [dswxs1_check, dswxhls_check, vfm_check] 

    print("="*60)
    print("Product Availability:")
    print("="*60)

    for i in info_dict:
        print(i)

    return info_dict

bounds = {
    "xmin": -90.9, #-85.72,  
    "ymin": 37.2,  #34.35, 
    "xmax": -90.7, #-85.30,
    "ymax": 37.5   #34.68 
}

check = dataset_info(
    "2026-10-03",
    **bounds,
)


#print(check)
#print(start_end_times)



