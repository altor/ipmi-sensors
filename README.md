## Ipmi-sensor

Script that use the Intelligent Platform Management Interface(IPMI) to monitor multiple sensors of a machine like Temperature, Fan speed, ...

## Requirements

- python >= 3.5
- pymongo

## Usage

- `python3 ipmi_sensor.py -s SENSOR_NAME -i SENSOR_ID -f FREQUENCY --output_uri MONGODB_URI --output_db DB --output_collection COLLECTION`

with FREQUENCY : time in seconds between each measure (default 1)

### How to retrieve SENSOR_NAME and SENSOR_ID

Use the following command : `sudo ipmitool sdr elist` if will print
you a table with the following format :

`SENSOR_NAME| SENSOR_ID| ... | ... | current sensor value`

### example

How to monitor the CPUs temperature on a machine from the chiclet
cluster (two cpus). the two sensors are named Temp and their id are 01h
and 02h. 3 seconds between each measure :
  
`sudo python3 ipmi_sensor.py -s 'Temp' -i 01h -s Temp -i 02h --output_uri "mongodb://localhost" --output_db testdb --output_collection testcol -f 3`

### Docker usage

if you use this script in a docker container, you have to make the ipmi device accessible to your container.
Run your container with the option `--device=PATH_TO_IPMI_DEVICE`

Path to ipmi device are usually : `/dev/ipmi0` or `/dev/ipmi/0`