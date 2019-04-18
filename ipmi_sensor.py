import subprocess
import argparse
from copy import copy
import time
import re
import pymongo


VAL_REGEXP = re.compile('([0-9]*) ?\\n$')

class IpmiToolError(Exception):
    def __init__(self, error_code, stderr):
        self.error_code = error_code
        self.stderr = str(stderr)


class UnknowSensorNameException(Exception):
    def __init__(self, sensor_name):
        self.sensor_name = sensor_name

class BadMongoConfig(Exception):
    def __init__(self, param_name, val):
        self.param_name = param_name
        self.val = val


def process_cmd(cmd_str):
    p =  subprocess.Popen(cmd_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    if p.returncode == 0:
        return out, err
    raise IpmiToolError(p.returncode, err)

class MongoConfig:
    def __init__(self, uri, db, collection):
        self.uri = uri
        self.collection = collection
        self.db = db

    def check(self):
        pass


class MonitoredSensorsConfig:
    def __init__(self, sensor_list):
        #: :attr sensor_list [(str, str)]: list of (sensor_name, sensor_id)
        self.sensor_list = sensor_list
        self.sensor_regexp = list(map(lambda x: re.compile('^'+x[0]+'\s*\|\s*'+x[1]+'\s*\|.*\|\s*(\d*)\D\\|*'), sensor_list))

    def check(self):
        out, err = process_cmd(['ipmitool', 'sdr', 'elist'])
        out = out.decode("utf-8")
        unverified_sensors = list(map(lambda x: (x[0], re.compile('^'+x[0]+'\s*|\s*'+x[1]+'\s*|')), self.sensor_list))

        for line in out.split('\n'):
            if unverified_sensors is []:
                return
            
            for i in range(len(unverified_sensors)):

                name, regexp = unverified_sensors[i]

                if not regexp.search(line) is None:
                    unverified_sensors.pop(i)
                    break

        for bad_name in unverified_sensors:
            raise UnknowSensorNameException(bad_name)

        return 
    
class Config:

    def __init__(self, frequency, verbose, sensor_name, mongo_config, monitored_sensors_config):
        self.frequency = frequency
        self.verbose = verbose
        self.sensor_name = sensor_name
        self.mongo_config = mongo_config
        self.monitored_sensors_config = monitored_sensors_config
    
    def check(self):
        #:TODO self.monitored_sensors_config.check(), self.mongo_config.check()
        self.monitored_sensors_config.check()
        self.mongo_config.check()
def arg_parser_init():
    """ initialize argument parser"""
    parser = argparse.ArgumentParser(
        description="ipmi-sensor")
    
    # MongoDB output
    parser.add_argument("--output_uri",type=str,  help="MongoDB output uri", required=True)
    parser.add_argument("--output_db", type=str, help="MongoDB output database", required=True)
    parser.add_argument("--output_collection", type=str, help="MongoDB output collection", required=True)

    # monitored sensor names and id
    parser.add_argument("-i", help="add a sensor to monitor with its id", action='append')
    parser.add_argument("-s", help="add a sensor to monitor", action='append')
    
    # Misc
    parser.add_argument("-v", "--verbose", help="Enable verbosity",
                        action="store_true", default=False)
    parser.add_argument("-f", "--frequency", help="measure frequency in s", type=int, 
                        default=1)
    parser.add_argument("-n", "--name", help="sensor name",
                        default='ipmi_sensor')
    
    return parser

def create_config(args):
    mongo = MongoConfig(args.output_uri, args.output_db, args.output_collection)
    sensors = MonitoredSensorsConfig(list(zip(args.s, args.i)))
    config = Config(args.frequency, args.verbose, args.name, mongo, sensors)
    return config


def measure(sensor_name):
    p =  subprocess.Popen(['ipmitool', 'sensor', 'reading', sensor_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ts = time.time()
    p.wait()
    out, err = p.communicate()
    out = out.decode("utf-8")
    m = VAL_REGEXP.search(out)
    return {
            'sensor' : 'ipmi_' + sensor_name,
            'timestamp' : ts,
            'value': int(m.group(1))
            }


def extract_measure(sensors, sensor_regexps):
    """
    :param sensors [(str, str)]: list of (sensor_name, sensor_id
    """
    sensors = copy(sensors)
    sensor_regexps = copy(sensor_regexps)
    p =  subprocess.Popen(['ipmitool', 'sdr', 'elist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ts = time.time()
    p.wait()
    out, err = p.communicate()
    out = out.decode("utf-8")

    result = []
    
    for line in out.split('\n'):
        if sensor_regexps == []:
            return result
        for i in range(len(sensor_regexps)):
            m = sensor_regexps[i].search(line)
            if m is not None:
                val = {
                    'sensor' : 'ipmi_' + sensors[i][0] + '_' + sensors[i][1],
                    'timestamp' : ts,
                    'value': int(m.group(1))
                }
                result.append(val)
                sensors.pop(i)
                sensor_regexps.pop(i)
                break
            
    return result
                
    

class DB:
    def __init__(self, mongo_config):
        self.client = pymongo.MongoClient(mongo_config.uri, serverSelectionTimeoutMS=5000)
        self.client.db_name.command('ping')

        self.db = self.client[mongo_config.db]
        self.collection = self.db[mongo_config.collection]

    def store(self, data):
        self.collection.insert(data)
        

args = arg_parser_init().parse_args()
config = create_config(args)
config.check()

db = DB(config.mongo_config)

t = time.time()

while True:
    if time.time() - t > config.frequency:
        for val in extract_measure(config.monitored_sensors_config.sensor_list, config.monitored_sensors_config.sensor_regexp):
            db.store(val)
            if config.verbose:
                print(val)
        t = time.time()
          
