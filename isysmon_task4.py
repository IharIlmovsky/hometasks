import schedule,time

is_debug = False                                # debug global variable for temp dump
logfile = file
v_config = {'interval': 10, 'output': 'json',  # config default parameters
            'out_filename': 'isysmon.out.json',  # default filename
            'is_json_out': True}  # default format


class Base_Metric(object):
    'base class for metric - parent'
    snapshot_counter = 0
    def __init__(self, interval=None, percpu=False):
        import psutil, datetime, time
        self.values = ['', '', '', '', '', '']
        self.fmt_head = ["\nCPU USAGE:\n",
                         "\nDISK USAGE:\n",
                         "\nVIRTUAL MEMORY:\n",
                         "\nMEMORY I/O COUNTERS:\n",
                         "\nNETWORK I/O COUNTERS:\n",
                         "\nNETWORK IFACES ADDRESSES:\n"]
        self.tstamp_str = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        if is_debug: print "Base_Metric.__init__"                 # init message
        self.values[0] = psutil.cpu_percent(interval, percpu)     # get metrics
        self.values[1] = psutil.disk_usage('/')
        self.values[2] = psutil.virtual_memory()
        self.values[3] = psutil.disk_io_counters(perdisk=False)
        self.values[4] = psutil.net_io_counters()
        self.values[5] = psutil.net_if_addrs()
        Base_Metric.snapshot_counter += 1
        if range(len(self.values)) != range(len(self.fmt_head)):
            print "Init error: header size differ from values size\n"
        if is_debug:
            print "Base_Metrics.values:\n  SNAPSHOT {0}  {1}\n".format(Base_Metric.snapshot_counter, self.tstamp_str)
            for k in range(len(self.values)):
                print " {0} ".format(self.values[k - 1])
            print " \n"

    def __repr__(self):
        return "Base_Metric repr called"

    def get_fmt_str(self, out_file):
        out_file.write("SNAPSHOT {0}  {1}\n".format(Base_Metric.snapshot_counter, self.tstamp_str))
        if is_debug: print "Base_Metric.format_str"          # parent class method, abstract?
        return


class Text_Metric(Base_Metric):
    " Text_Metric class - child from Base_Metric"
    def __init__(self):
        Base_Metric.__init__(self)

    def get_fmt_str(self, out_file):
        Base_Metric.get_fmt_str(self, out_file)
        for k in range(len(self.values)):
            out_file.write("  {0} {1}\n".format(self.fmt_head[k -1], self.values[k -1]))

    def __repr__(self):
        return "Text_Metric repr called"

##  JSon_Metric - another child from Base_Metric
class Json_Metric(Base_Metric):
    def __init__(self):
        Base_Metric.__init__(self)

    def get_fmt_str(self,out_file):
        import json
        Base_Metric.get_fmt_str(self, out_file)
        for k in range(len(self.values)):
            out_file.write("{0} ".format(self.fmt_head[k -1]))
            json.dump(self.values[k -1], out_file, indent=4)

    def __repr__(self):
        return "Json_Metric repr called"


def fn_open_config():
    ' read configuration'
    import ConfigParser, os
    global v_config, logfile

    config = ConfigParser.ConfigParser()
    config.read(['isysmon.cfg', os.path.expanduser('~/.isysmon.cfg')])

    interval = config.get('common', 'interval')
    outfmt = config.get('common', 'output')
    if is_debug: print "values from common: interval: {0} output: {1} ".format(interval,outfmt)

    if (int(interval) >= 5): v_config['interval'] = interval
    if (outfmt != None): outfmt = outfmt.lower()

    if outfmt != 'json':
        v_config['out_filename'] = 'isysmon.out.txt' # text is default if is not json
        v_config['is_json_out'] = False
        if is_debug: print "making text output"
    else:
        if is_debug: print "making json output"      # otherwise json is default

    if is_debug: print "out_filename: {0} out_format: {1}".format(v_config['out_filename'], v_config['is_json_out'])
    logfile = open(v_config['out_filename'], 'a+')
    return logfile


## main: getting metrics and than print results
def isysmon_main():
    global logfile
    if (logfile != None):
        if v_config['is_json_out'] == True:
            metric = Json_Metric()
        else:
            metric = Text_Metric()
        metric.get_fmt_str(logfile)
        del metric # delete instance, obviously
    return

## beginning
logfile = fn_open_config() # define output format
schedule.every(int(v_config['interval'])).seconds.do(isysmon_main)
while True:
    schedule.run_pending()
    time.sleep(1000)

if (logfile != None):
    logfile.close()
