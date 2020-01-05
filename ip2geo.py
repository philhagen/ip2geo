#!env python3
# ip2geo.py
# version 2.0
# by Phil Hagen <phil@lewestech.com>
#
# This script reads IP addresses from STDIN and performs GeoIP database lookups
# on each to add typical geo fields as well as ASNs.  The results are output
# in a customizable format, which defaults to CSV containing the IP,  lat/long,
# Autonomous System (AS) Number, and AS name.

import sys
from argparse import ArgumentParser, RawTextHelpFormatter
import os
import shutil
import re
import platform
from subprocess import Popen, PIPE
import json

try:
    import geoip2.database
except ImportError:
    sys.stderr.write('ERROR: No geoip2 library available - exiting.\n')
    sys.stderr.write('       Try installing with "pip install geoip2" or similar (may require admin privileges).\n')
    exit(2)

format_map = {
    '%ip': ['ipaddress', 'IP Address'],
    '%ci': ['city', 'City'],
    '%rc': ['region_code', 'Region Code (State)'],
    '%cn': ['country_name', 'Country Name'],
    '%pc': ['postal_code', 'Postal (ZIP) Code'],
    '%cc': ['country_code', 'ISO Country Code'],
    '%co': ['continent', 'Continent'],
    '%mc': ['metro_code', 'Metro Code'],
    '%tz': ['time_zone', 'Time Zone Name'],
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
    'continent': None,
    'metro_code': None,
    'time_zone': None,
    'latitude': None,
    'longitude': None,
}

output_re = re.compile('|'.join(format_map.keys()))

default_geoipconf = './GeoIPData/GeoIP.conf'
default_format_string = '"%ip","%lat","%lon","%asnum","%asname"'

# handle command line options
p = ArgumentParser(description='Perform GeoIP lookups on IP addresses, displaying output in normalized format.', formatter_class=RawTextHelpFormatter)
p.add_argument('-g', '--geoipconf', dest='geoipconf', help='Path to GeoIP.conf file used by geoipupdate utility; Default: %s' % (default_geoipconf), default=default_geoipconf)
p.add_argument('-j', '--json', dest='json', help='Provide each output record in JSON format.  Ignores -f; Default: False', action='store_true', default=False)
p.add_argument('-d', '--download', dest='download', help='Download latest GeoIP databases to DatabaseDirectory specified in GeoIP.conf and exit.', action='store_true', default=False)
p.add_argument('-f', '--format', dest='format', help='Output format string; Default: \'%s\'.\nPossible values:\n%s' % (default_format_string.replace('%','%%'), format_map_help_string), default=default_format_string)

args = p.parse_args()

def geoip_download(storagedir):
    conffile = os.path.abspath(args.geoipconf)
    db_download = Popen(['geoipupdate', '-f', conffile], cwd=storagedir, stdout=PIPE, stderr=PIPE)

    print('Downloading GeoIP database files.')

    db_download.communicate()
    if db_download.returncode != 0:
        sys.stderr.write('ERROR: Error downloading/updating GeoIP databases - exiting.')
        exit(5)

def check_geoip_files(storagedir):
    try:
        gi1 = geoip2.database.Reader(os.path.join(storagedir, 'GeoLite2-City.mmdb'))
        gi2 = geoip2.database.Reader(os.path.join(storagedir, 'GeoLite2-ASN.mmdb'))
    except IOError:
        sys.stderr.write('ERROR: Required GeoIP files not present. Use "-d" flag to put them into %s.\n' % (storagedir))
        sys.exit(2)

    return (gi1, gi2)

#############################
if not shutil.which('geoipupdate'):
    sys.stderr.write('ERROR: Could not locate the geoipupdate utility in the path - exiting.\n')
    sys.stderr.write('       Try installing with apt, yum, brew, or similar.\n')
    exit(3)

if not os.path.isfile(args.geoipconf):
    sys.stderr.write('ERROR: GeoIP configuration file %s does not exist - exiting.\n' % args.geoipconf)
    sys.stderr.write('       Refer to the included GeoIPData/GeoIP.conf.sample file.\n')
    sys.stderr.write('       Note that this requires a MaxMind account to update the database.\n')
    exit(4)

# set up the storage directory, ending with an absolute path
geoconf_fh = open(args.geoipconf)
try:
    databasedir = re.search(r'^DatabaseDirectory\s+(\S+)', geoconf_fh.read(), re.MULTILINE).group(1)
    storagedir = os.path.abspath(os.path.join(os.path.dirname(args.geoipconf), databasedir))
except AttributeError:
    # this is the default, from the geoipupdate package
    if platform.system == 'Windows':
        storagedir = os.environ['SYSTEMDRIVE'] + '\\ProgramData\\MaxMind\\GeoIPUpdate\\GeoIP'
    else:
        storagedir = '/usr/local/share/GeoIP'
geoconf_fh.close()

# if we're here to download, get after it
if args.download:
    geoip_download(storagedir)
    exit(0)

(geocity, geoasn) = check_geoip_files(storagedir)

# loop over input data
for line in sys.stdin:
    line = line.strip()

    # make sure line only has an IP address via regexp
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', line):

        output_record = null_record

        # do geo lookups on IP
        try:
            ipdata = geocity.city(line)

            output_record = {
                'ipaddress': line,
                'city': ipdata.city.name,
                'region_code': ipdata.subdivisions.most_specific.iso_code,
                'country_name': ipdata.country.name,
                'postal_code': ipdata.postal.code,
                'country_code': ipdata.country.iso_code,
                'continent': ipdata.continent.name,
                'metro_code': ipdata.location.metro_code,
                'time_zone': ipdata.location.time_zone,
                'latitude': ipdata.location.latitude,
                'longitude': ipdata.location.longitude,
            }

        except geoip2.errors.AddressNotFoundError:
            output_record = null_record

        try:
            asn = geoasn.asn(line)
            output_record['asnum'] = asn.autonomous_system_number
            output_record['asname'] = asn.autonomous_system_organization

        except geoip2.errors.AddressNotFoundError:
            output_record['asnum'] = 0
            output_record['asname'] = 'None'

        if args.json:
            print(json.dumps(output_record))

        else:
            # print out fields in CSV format
            output_record = {k: str(v) for k,v in output_record.items()}

            output_string = output_re.sub(lambda x: output_record[format_map[x.group()][0]], args.format)
            print(output_string)
