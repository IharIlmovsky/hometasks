import schedule, time, logging, logging

# list for config parameters, updating from config file "isysmon.cfg"
# config parameter "debug" defines only printing to console only
v_config = {'interval': 10, 'output': 'json',       # config default parameters
            'out_filename': 'isysmon.out.json',     # default filename
            'is_json_out': True,                    # default format
            'debug': True}                          # debug for tmp dump
outfile = None                                      # metric's output file
log_level = logging.INFO                            # logging default level, overrides from config file "logging"

# names for metrics dict
prm_names = ('\nCPU USAGE','\nDISK USAGE','\nVIRTUAL MEMORY',
             '\nMEMORY I/O COUNTERS','\nNETWORK I/O COUNTERS','\nNETWORK IFACES ADDRESSES')

def wrap(pre, post): # wrap decorator
    def decorate(func):
        def call(*args, **kwargs):
            pre(func, *args, **kwargs)
            result = func(*args, **kwargs)
            post(func, *args, **kwargs)
            return result
        return call
    return decorate

def write_log(vs):   # write log depends on global "log_level"
    import datetime, time
    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S: ')
    if not(logging is None):
        if log_level == logging.DEBUG:
            logging.debug(ts)
            logging.debug(vs)
        elif log_level == logging.INFO:
            logging.debug(ts)
            logging.info(vs)
        elif log_level == logging.ERROR:
            logging.error(ts)
            logging.error(vs)
        elif log_level == logging.CRITICAL:
            logging.critical(ts)
            logging.critical(vs)
        else:
            logging.warning(ts)
            logging.warning(vs)

# input wrapper
def trace_in(func, *args, **kwargs):
    vs = "Entering function ", func.__name__
    write_log(vs)
    print vs

# output wrapper
def trace_out(func, *args, **kwargs):
    vs = "Leaving function ", func.__name__
    write_log(vs)
    print vs

## functional class
class Base_Metric(object):
    'base class for metric - parent'
    snapshot_counter = 0
    def __init__(self, interval=None, percpu=False,default_disk='/',perdisk=False):
        if v_config['debug']:
            print "Base_Metric.__init__"  # init message
        self.timestamp = None
        self.interval = interval
        self.per_cpu  = percpu
        self.ddisk    = default_disk
        self.per_disk = perdisk
        self.values = { prm_names[0]: '', prm_names[1]: '', prm_names[2]: '',
                        prm_names[3]: '', prm_names[4]: '', prm_names[5]: '' }

    @wrap(trace_in, trace_out)
    def get_metrics(self):
        import psutil, datetime, time
        self.timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        if v_config['debug']:
            print "Base_Metric.get_metrics"  # init message
        self.values[prm_names[0]] = psutil.cpu_percent(self.interval, self.per_cpu)  # get metrics
        self.values[prm_names[1]] = psutil.disk_usage(self.ddisk)
        self.values[prm_names[2]] = psutil.virtual_memory()
        self.values[prm_names[3]] = psutil.disk_io_counters(self.per_disk)
        self.values[prm_names[4]] = psutil.net_io_counters()
        self.values[prm_names[5]] = psutil.net_if_addrs()
        Base_Metric.snapshot_counter += 1
        if v_config['debug']:
            print "Base_Metrics.values:\n  SNAPSHOT {0}  {1}\n".format(Base_Metric.snapshot_counter, self.timestamp)
            for key, value in self.values.items():
                print " {0} {1}".format(key, value), "\n", type(value)
            print "\n"
        return Base_Metric.snapshot_counter

    def __repr__(self):
        return "Base_Metric repr called"

    @wrap(trace_in, trace_out)
    def get_fmt_str(self, out_file):
        if v_config['debug']:
            print "Base_Metric.format_str"  # parent class method
        out_file.write("SNAPSHOT {0}  {1}\n".format(Base_Metric.snapshot_counter, self.timestamp))
        return


class Text_Metric(Base_Metric):
    " Text_Metric class - child from Base_Metric"
    def __init__(self):
        Base_Metric.__init__(self)
        Base_Metric.get_metrics(self)

    @wrap(trace_in, trace_out)
    def get_fmt_str(self, out_file):
        Base_Metric.get_fmt_str(self, out_file)  # inherite making SNAPSHOT string
        for key, value in self.values.items():
            out_file.write("  {0} {1}\n".format(key, value))

    def __repr__(self):
        return "Text_Metric repr called"


##  JSon_Metric - another child from Base_Metric
class Json_Metric(Base_Metric):
    def __init__(self):
        Base_Metric.__init__(self)
        Base_Metric.get_metrics(self)

    @wrap(trace_in, trace_out)
    def get_fmt_str(self,out_file):
        import json
        Base_Metric.get_fmt_str(self, out_file)
        for key, value in self.values.items():
            out_file.write(" {0}:".format(key))
            if type(value) in (int, float, str):
                out_file.write(" {0}\n".format(value))
            elif isinstance(value, dict):
                json.dump(value, out_file, indent=4)
            else:
                json.dump(zip(value._fields, list(value)), out_file, indent=4)

    def __repr__(self):
        return "Json_Metric repr called"

def open_config():
    ' read configuration from file'
    import ConfigParser, os
    global v_config, outfile, log_level

    config = ConfigParser.ConfigParser()
    try:
        config.read(['isysmon.cfg', os.path.expanduser('~/.isysmon.cfg')])
        interval = config.get('common', 'interval')
        outfmt   = config.get('common', 'output')
        try:
            is_debug = bool(config.get('common', 'debug'))
            config_log_level = config.get('common', 'logging')
        except:
            is_debug = True  # optional parameters
            config_log_level = logging.WARNING
    except:
        print "Error during reading config:"
        interval = 5      # default mandatory params
        outfmt   = 'json'

    if config_log_level in (logging.DEBUG, logging.INFO, logging.CRITICAL, logging.ERROR, logging.WARNING):
        log_level =  config_log_level
    logging.basicConfig(filename='isysmon.log', level=log_level)  # default warinig logging level
    write_log('process started...')

    if is_debug != None: v_config['debug'] = is_debug
    print "values from common: interval: {0} output: {1} ".format(interval, outfmt)

    if v_config['debug']:
        print "values from common: interval: {0} output: {1} ".format(interval,outfmt)

    logging.info("interval value from config file: {0}".format(interval))
    if (int(interval) >= 5):
        v_config['interval'] = interval # up from 5 sec
        logging.warning("interval value accepted: {0}".format(v_config['interval']))

    if (outfmt != None): outfmt = outfmt.lower()             # param in lowercase

    if outfmt != 'json':
        v_config['out_filename'] = 'isysmon.out.txt'         # text is default if is not json
        v_config['is_json_out'] = False
        if v_config['debug']: print "making text output"
    else:
        if v_config['debug']: print "making json output"      # otherwise json is default

    if v_config['debug']: print "out_filename: {0} out_format: {1}".format(v_config['out_filename'], v_config['is_json_out'])
    try:
        outfile = open(v_config['out_filename'], 'a+')
        return True
    except:
        return False


## main: getting metrics and than print results
@wrap(trace_in, trace_out)
def isysmon_main():
    global outfile
    if (not outfile is None):
        if v_config['is_json_out'] == True:
           metric = Json_Metric()
        else:
           metric = Text_Metric()
        metric.get_fmt_str(outfile)  # save data in proper format
        del metric # delete instance, obviously
    return

## beginning
if open_config(): # read config file and define logging level
    isysmon_main();
    schedule.every(int(v_config['interval'])).seconds.do(isysmon_main)
    while True:
        schedule.run_pending()
        time.sleep(10)
if (not outfile is None):
    outfile.close()
logging.info('process finished')