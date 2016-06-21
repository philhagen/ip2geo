#!/usr/bin/python
# ip2geo.py
# version 1.0
# by Phil Hagen <phil@lewestech.com>
#
# This script reads IP addresses from STDIN and performs GeoIP database lookups
# on each to add typical geo fields as well as ASNs.  The results are output
# in a customizable format, which defaults to CSV containing the lat/long,
# Autonomous System (AS) Number name.


import sys
from argparse import ArgumentParser, RawTextHelpFormatter
import urllib2
import os
import gzip
import shutil
import re
import fileinput

try:
    import pygeoip
except ImportError:
    sys.stderr.write('ERROR: No pygeoip library available - exiting.\n')
    sys.stderr.write('       Try installing with "pip install pygeoip" or similar (may require admin privileges).\n')
    exit(2)

format_map = {
    '%ip': ['ipaddress', 'IP Address'],

    '%ci': ['city', 'City'],
    '%rc': ['region_code', 'Region Code (State)'],
    '%cn': ['country_name', 'Country Name'],
    '%pc': ['postal_code', 'Postal (ZIP) Code'],
    '%cc2': ['country_code', 'Country Code (2 char)'],
    '%cc3': ['country_code3', 'Country Code (3 char)'],
    '%co': ['continent', 'Continent'],
    '%mc': ['metro_code', 'Metro Code'],

    '%ac': ['area_code', 'Telephone Area Code'],
    '%tz': ['time_zone', 'Time Zone Name'],
    '%dc': ['dma_code', 'DMA Code'],
    '%lat': ['latitude', 'Latitude'],
    '%lon': ['longitude', 'Longitude'],

    '%asnum': ['asnum', 'AS Number'],
    '%asname': ['asname', 'AS Name'],
}
format_map_help_string = ''
for tag in format_map.keys():
    format_map_help_string += '%10s : %s\n' % (tag.replace('%','%%'), format_map[tag][1])

null_record = {
    'city': None,
    'region_code': None,
    'country_name': None,
    'postal_code': None,
    'country_code': None,
    'country_code3': None,
    'continent': None,
    'metro_code': None,
    'area_code': None,
    'time_zone': None,
    'dma_code': None,
    'latitude': None,
    'longitude': None,
}

as_re = re.compile('AS(?P<num>\d+)(?: (?P<name>.+))?')
output_re = re.compile('|'.join(format_map.keys()))

default_geoip_dir = './'
default_format_string = '"%ip","%lat","%lon","%asnum","%asname"'

# handle command line options
p = ArgumentParser(description='Perform GeoIP lookups on IP addresses, displaying output in normalized format.', formatter_class=RawTextHelpFormatter)
p.add_argument('-g', '--geoipdir', dest='geoipdir', help='Directory containing MaxMind GeoIP databases; Default: %s' % (default_geoip_dir), default=default_geoip_dir)
p.add_argument('-d', '--download', dest='download', help='Download latest GeoIP databases to GEOIPDIR directory and exit.', action='store_true', default=False)
p.add_argument('-f', '--format', dest='format', help='Output format string; Default: \'%s\'.\nPossible values:\n%s' % (default_format_string.replace('%','%%'), format_map_help_string), default=default_format_string)

args = p.parse_args()

def geoip_download(storagedir):
    city_url = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'
    asn_url = 'http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz'

    for url in (city_url, asn_url):
        download_file = url.split('/')[-1]
        final_file = os.path.splitext(download_file)[0]

        u = urllib2.urlopen(url)
        f = open(os.path.join(storagedir, download_file), 'wb')

        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print 'Downloading: %s Bytes: %s' % (download_file, file_size)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            status = r'%10d  [%3.2f%%]' % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8) * (len(status) + 1)
            print status,

        f.close()

        print 'Decompressing %s' % (download_file)
        with gzip.open(os.path.join(storagedir, download_file), 'rb') as f_in:
            with open(os.path.join(storagedir, final_file), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        f_in.close()
        f_out.close()
        os.remove(download_file)

def check_geoip_files(storagedir):
    try:
        gi1 = pygeoip.GeoIP(os.path.join(storagedir, 'GeoLiteCity.dat'))
        gi2 = pygeoip.GeoIP(os.path.join(storagedir, 'GeoIPASNum.dat'))
    except IOError:
        sys.stderr.write('ERROR: Required GeoIP files not present. Use "-d" flag to put them into %s.' % (storagedir))
        exit(2)

    return (gi1, gi2)

# if we're here to download, get after it
if args.download:
    # TODO: check perms on destination directory
    geoip_download(args.geoipdir)
    exit(0)

(geocity, geoasn) = check_geoip_files(args.geoipdir)

# loop over input data
for line in fileinput.input():
    line = line.strip()

    # make sure line only has an IP address via regexp
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', line):
        # do geo lookups on IP
        ipdata = geocity.record_by_addr(line)
        if ipdata == None:
            ipdata = null_record

        asn = geoasn.asn_by_addr(line)
        if asn != None:
            (asnum, asname) = as_re.match(asn).groups()
        else:
            (asnum, asname) = (0, 'None')
        ipdata['ipaddress'] = line
        ipdata['asnum'] = int(asnum)
        ipdata['asname'] = asname

        # print out fields in CSV format
        output_string = output_re.sub(lambda x: str(ipdata[format_map[x.group()][0]]), args.format)
        print output_string