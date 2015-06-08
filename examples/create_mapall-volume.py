from scaleiopy import scaleio
from pprint import pprint
import sys

# How to run:
# python create_mapall-volume.py ip-to-mdm user pass volume_name protection_domain_name

# Whats this code doing:
# Create a volume of 8GB inside specified protectiondomain and map it to all registered SDCs

sio = scaleio.ScaleIO("https://" + sys.argv[1] + "/api",sys.argv[2],sys.argv[3],False,"ERROR") # HTTPS must be used as there seem to be an issue with 302 responses in Requests when using POST
    
sio.create_volume(sys.argv[4], 8192, sio.get_storage_pool_by_name(sys.argv[5]), mapAll=True)

pprint(sio.volumes)
