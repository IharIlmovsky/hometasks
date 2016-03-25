import psutil
import schedule
import json
import time

is_debug = True
v_config = {'interval':10, 'output':'json', 'outfname':'isysmon.out.json'}
var_fmt  = ["\n\nCPU USAGE:\n",
            "\n\nDISK USAGE:\n", "\n\nVIRTUAL MEMORY:\n",
            "\n\nMEMORY I/O COUNTERS:\n",
            "\n\nNETWORK I/O COUNTERS:\n",
            "\n\nNETWORK IFACES ADDRESSES:\n"]
var_value = ['','','','','','']
cnt_snapshot = 0
is_json_out  = 1
outfname = ""

def fn_get_metric(interval=None, percpu=False):
    '''Get metrics into globals'''
    global var_value
    var_value[0] = psutil.cpu_percent(interval, percpu)
    var_value[1] = psutil.disk_usage('/')
    var_value[2] = psutil.virtual_memory()
    var_value[3] = psutil.disk_io_counters(perdisk=False)
    var_value[4] = psutil.net_io_counters()
    var_value[5] = psutil.net_if_addrs()

    if is_debug:
       for k in range(len(var_value)):
           print var_value[k-1]
    return

def timestamp():
    '''produce timestamp string for logging'''
    import datetime
    import time
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

def fn_open_config():
    import ConfigParser, os
    global v_config
    global is_json_out
    config = ConfigParser.ConfigParser()
    config.read(['isysmon.cfg', os.path.expanduser('~/.isysmon.cfg')])

    interval = config.get('common', 'interval')
    outfmt = config.get('common', 'output')

    if (interval >= 5) and (interval != v_config['interval']):
        v_config['interval'] = interval
    if is_debug: print v_config['interval']

    if (outfmt != None): outfmt = outfmt.lower()
    if is_debug: print outfmt

    if outfmt != 'json':
        v_config['outfname'] = 'isysmon.out.txt'
        is_json_out = 0
        if is_debug: print "making text output"
    else:
        if is_debug: print "making json output"

    if is_debug: print v_config['outfname']
    return v_config['outfname']


def fn_format_data(log_fname, snap_str):
    '''formatting metrics'''
    global cnt_snapshot
    global var_fmt
    global v_config
    global is_json_out

    outfile = open(log_fname, 'a+')
    outfile.write(snap_str)
    for i in range(len(var_fmt)):
        outfile.write("{0} ".format(var_fmt[i - 1]))
        if is_json_out == 1:
            json.dump( var_value[i-1], outfile, indent=4)
        else:
            outfile.write("    {0}".format(var_value[i-1]))
    outfile.close()
    return

## main
def isysmon_main():
    global cpu_times
    global cnt_snapshot
    global outfname
    outfname = fn_open_config()
    snap_str = "\n SNAPSHOT {0}  {1} \n".format(cnt_snapshot, timestamp())
    fn_get_metric();
    fn_format_data(outfname, snap_str)
    cnt_snapshot += 1;
    return cnt_snapshot

#isysmon_main()
schedule.every(int(v_config['interval'])).seconds.do(isysmon_main)
while True:
    schedule.run_pending()
    time.sleep(1000)

