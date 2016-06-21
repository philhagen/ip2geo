# ip2geo

This script reads IP addresses from STDIN and uses the MaxMind GeoIP databases to output various data points for each source IP.  The script uses the GeoCityLite and ASN databases for enrichment.  The user can specify various fields for output in a format string.  You can use this script to download the GeoIP database files if needed as well.

## Usage

Look up a single IP address with default output format string:

    echo 192.30.252.122 | ./ip2geo.py
    "192.30.252.122","37.7697","-122.3933","36459","GitHub, Inc."

Generate custom output format for all IPs in a file (one per line):

    cat file_of_ips.txt | ./ip2geo.py -f '%ip %asnum %cn'
    157.166.226.26 5662 United States
    192.30.252.122 36459 United States
    66.35.59.202 22625 United States
    58.162.89.137 1221 Australia

Download GeoIP database files:

    ./ip2geo.py -d
    Downloading: GeoLiteCity.dat.gz Bytes: 14022119
     Decompressing GeoLiteCity.dat.gz
    Downloading: GeoIPASNum.dat.gz Bytes: 2074034
     Decompressing GeoIPASNum.dat.gz

Display usage (including list of all format string tags):

    ./ip2geo.py -h
    usage: ip2geo.py [-h] [-g GEOIPDIR] [-d] [-f FORMAT]

    Perform GeoIP lookups on IP addresses, displaying output in normalized format.

    optional arguments:
      -h, --help            show this help message and exit
      -g GEOIPDIR, --geoipdir GEOIPDIR
                            Directory containing MaxMind GeoIP databases; Default: ./
      -d, --download        Download latest GeoIP databases to GEOIPDIR directory and exit.
      -f FORMAT, --format FORMAT
                            Output format string; Default: '"%ip","%lat","%lon","%asnum","%asname"'.
                            Possible values:
                                  %ip : IP Address
                                 %cc3 : Country Code (3 char)
                                 %cc2 : Country Code (2 char)
                               %asnum : AS Number
                                  %mc : Metro Code
                                  %dc : DMA Code
                                  %co : Continent
                                  %cn : Country Name
                                  %ac : Telephone Area Code
                              %asname : AS Name
                                  %ci : City
                                  %tz : Time Zone Name
                                 %lat : Latitude
                                  %rc : Region Code (State)
                                 %lon : Longitude
                                  %pc : Postal (ZIP) Code
