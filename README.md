# ipmi-sensor

script that use the Intelligent Platform Management Interface(IPMI) to monitor multiple sensors of a machine like Temperature, Fan speed, ...

# Requirements

- python >= 3.5
- pymongo

# usage

- `python3 ipmi_sensor.py -s SENSOR_NAME -i SENSOR_ID -f FREQUENCY --output_uri MONGODB_URI --output_db DB --output_collection COLLECTION`

with FREQUENCY : time in seconds between each measure (default 1)

## How to retrieve SENSOR_NAME and SENSOR_ID

use the following command : `sudo ipmitool sdr elist` if will print
you a table with the following format :

`SENSOR_NAME| SENSOR_ID| ... | ... | current sensor value`

## example

- how to monitor the CPUs temperature on a machine from the chiclet
  cluster (two cpus). the two sensors are named Temp and their id are 01h
  and 02h. 3 seconds between each measure :
  
  `python3 ipmi_sensor.py -s 'Temp' -i 01h -s Temp -i 02h --output_uri "mongodb://localhost" --output_db testdb --output_collection testcol -f 3`
