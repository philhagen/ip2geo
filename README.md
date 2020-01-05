# ip2geo

This script reads IP addresses from STDIN and uses the MaxMind GeoIP databases to output various data points for each source IP.  The script uses the GeoCityLite and ASN databases for enrichment.  The user can specify various fields for output in a format string.  You can use this script to download the GeoIP database files if needed as well.

## Usage

Look up a single IP address and display results with default output format string:

    echo 192.30.252.122 | ./ip2geo.py
    "192.30.252.122","37.7697","-122.3933","36459","GitHub, Inc."

Generate custom output format for all IPs in a file (one per line):

    cat file_of_ips.txt | ./ip2geo.py -f '%ip %asnum %cn'
    157.166.226.26 5662 United States
    192.30.252.122 36459 United States
    66.35.59.202 22625 United States
    58.162.89.137 1221 Australia

Look up a single IP address and display results in JSON:

    echo 192.30.252.122 | ./ip2geo.py -j | jq '.'
    {
    "ipaddress": "192.30.252.122",
    "city": null,
    "region_code": null,
    "country_name": "United States",
    "postal_code": null,
    "country_code": "US",
    "continent": "North America",
    "metro_code": null,
    "time_zone": "America/Chicago",
    "latitude": 37.751,
    "longitude": -97.822,
    "asnum": 36459,
    "asname": "GitHub, Inc."
    }

Download (or update) GeoIP database files:

    ./ip2geo.py -d
    Downloading GeoIP database files.

Display usage (including list of all format string tags):

    ./ip2geo.py -h
    usage: ip2geo.py [-h] [-g GEOIPCONF] [-j] [-d] [-f FORMAT]

    Perform GeoIP lookups on IP addresses, displaying output in normalized format.

    optional arguments:
      -h, --help            show this help message and exit
      -g GEOIPCONF, --geoipconf GEOIPCONF
                            Path to GeoIP.conf file used by geoipupdate utility; Default: ./GeoIPData/GeoIP.conf
      -j, --json            Provide each output record in JSON format.  Ignores -f; Default: False
      -d, --download        Download latest GeoIP databases to DatabaseDirectory specified in GeoIP.conf and exit.
      -f FORMAT, --format FORMAT
                            Output format string; Default: '"%ip","%lat","%lon","%asnum","%asname"'.
                            Possible values:
                                  %ip : IP Address
                                  %ci : City
                                  %rc : Region Code (State)
                                  %cn : Country Name
                                  %pc : Postal (ZIP) Code
                                  %cc : ISO Country Code
                                  %co : Continent
                                  %mc : Metro Code
                                  %tz : Time Zone Name
                                 %lat : Latitude
                                 %lon : Longitude
                               %asnum : AS Number
                              %asname : AS Name
