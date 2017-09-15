from os.path import basename, isfile, join, exists
from os import listdir, stat, remove, makedirs, unlink
from bz2 import BZ2File
from shutil import copyfileobj
from tqdm import tqdm
from datetime import date, time, datetime
from time import gmtime, strftime, strptime
from .config import local_config
from multiprocessing import Lock

_print = print
mutex = Lock()

class LogType :
    info = 1
    warning = 2
    debug = 3
    trace = 4
    error = 5

    LogTypeToString = {
        info : "[I]",
        warning : "[W]",
        debug : "[D]",
        trace : "[T]",
        error : "[E]"
    }


def removeFile(path):
    try:
        if isfile(path):
            unlink(path)
    except Exception as e:
        print(e, LogType.error)

def get_last_log_archive_counter():
    counter = 1
    for filename in listdir(local_config.folder_log_files):
        filename = basename(filename)
        if not filename.endswith('.bz2'): continue
        filename_array = filename.split(".")
        file_counter = int(filename_array[2])
        if counter < file_counter:
            counter = file_counter

    return counter

# function to archive large log file
def archive_logfile(file_path):
    file_path = join(local_config.folder_log_files, local_config.log_filename)
    log_counter = get_last_log_archive_counter() + 1
    if isfile(file_path):
        statinfo = stat(file_path)
        if statinfo.st_size > local_config.log_file_maxsize:
            with open(file_path, 'rb') as input:
                bz_file_name = "%s.%d.bz2" % (file_path, log_counter)
                with BZ2File(bz_file_name, 'wb', compresslevel=9) as output:
                    copyfileobj(input, output)

            remove(file_path)

# use print function to save message into file with timestamp
def print(what, log_type=LogType.info, has_EOL=True, only_Message=False) :
    from inspect import stack

    file_path = join(local_config.folder_log_files, local_config.log_filename)

    with mutex:
        archive_logfile(file_path)

    indent_level = len(stack()) - 3
    call_in_stack = sum([stck[3].count("__call__") for stck in stack()])
    indent_level -= int(call_in_stack - 1)

    indentation = '  ' * indent_level
    end = "\n"
    if not has_EOL:
        end = ""

    with open(file_path, "a", encoding="utf-8") as myfile:
        time_stamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        message = "%s" % what
        if not only_Message:
            message = "%s: %s: %s%s" % (time_stamp, LogType.LogTypeToString[log_type], indentation, what)
        _print(message, file=myfile, end=end)
        myfile.flush()

# parse filename to list
# 2015-11-14_-1.xml => {'date':'2015-11-14', 'index':'-1', 'suffix':'xml'}
def parse_filename(filename):
    filename_array = filename.split(".")
    suffix = filename_array[1]
    name = filename_array[0]
    name_array = name.split("_")
    date = name_array[0]
    index = name_array[1]

    return {
        'date' : date,
        'index' : index,
        'suffix' : suffix
    }


def join_filename(parsed_filename):
    filename = "%s_%s.%s" % (parsed_filename['date'], parsed_filename['index'], parsed_filename['suffix'])
    return filename


def CheckFolders():
    if not exists(local_config.folder_database):
        makedirs(local_config.folder_database)
    if not exists(local_config.folder_data_root):
        makedirs(local_config.folder_data_root)
    if not exists(local_config.folder_log_files):
        makedirs(local_config.folder_log_files)
    if not exists(local_config.folder_osm_data_root):
        makedirs(local_config.folder_osm_data_root)
    if not exists(local_config.folder_graphs_root):
        makedirs(local_config.folder_graphs_root)
    if not exists(local_config.folder_export_root):
        makedirs(local_config.folder_export_root)
    if not exists(local_config.folder_paths_root):
        makedirs(local_config.folder_paths_root)

def get_float_coord(coord):
    try:
        return float(coord)
    except ValueError:
        return None


def decorated_tqdm(sequence, SetState, desc="", total=None):
    n = 0
    description = desc
    if hasattr(sequence, 'desc'):
        description = sequence.desc
    if not total:
        total = len(sequence)
    if total == 0:
        SetState(action=description, percentage=100)
    else:
        SetState(action=description, percentage=int((0/total)*100))

    for elem in sequence:
        yield elem

        if total == 0:
            SetState(action=description, percentage=100)
        else:
            SetState(action=description, percentage=int((n/total)*100))
        n += 1

def get_tqdm(files, SetState, desc, total=None, position=None):
    return decorated_tqdm(
        tqdm(files,
            desc=desc,
            total=total,
            leave=True,
            disable=local_config.tqdm_console_disabled,
            position=position),
        SetState,
        desc,
        total)

def convertBytesToString(size_in_bytes):
    if size_in_bytes < 1024:
        return "%dB" % size_in_bytes
    elif size_in_bytes  < 1024*1024:
        return "%dKB" % (size_in_bytes/1024)
    else:
        return "%dMB" % (size_in_bytes/(1024*1024))

def progress_hook(state):
    def inner(b=1, bsize=1, tsize=None):
        state['percentage'] = 50
        state['action'] = "Get OSM Data (Downloaded: %s)" % (convertBytesToString(b * bsize))

    return inner


class TRACE_FN_CALL (object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        self.cls = owner
        self.obj = instance

        return self.__call__

    def __call__(self, *args, **kwargs):
        function_name_prepend = ""
        if self.func.__name__ == "__init__":
            function_name_prepend = "%s." % self.cls.__name__

        print("Entering %s%s" % (function_name_prepend, self.func.__name__), LogType.trace)
        result = self.func(self.obj, *args, **kwargs)
        print("Leaving %s%s" % (function_name_prepend, self.func.__name__), LogType.trace)
        return result

prohibited_methods = ['SetState', 'TestIsRun', '_inCity', '_searchNearby']

def DECORATE_ALL(decorator):
    def decorate(cls):
        for attr in cls.__dict__: # there's propably a better way to do this
            if not attr in prohibited_methods and callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate



dayTimes = [('night',     (time(0),  time(6))),
           ('morning',   (time(7),  time(10))),
           ('forenoon',  (time(11), time(12))),
           ('afternoon', (time(13), time(18))),
           ('evening',   (time(19), time(22))),
           ('night',     (time(23), time(23,59,59,999999)))
            ]
Y = 2000 # dummy leap year to allow input X-02-29 (leap day)
seasons = [('winter', (date(Y,  1,  1),  date(Y,  3, 20))),
           ('spring', (date(Y,  3, 21),  date(Y,  6, 20))),
           ('summer', (date(Y,  6, 21),  date(Y,  9, 22))),
           ('autumn', (date(Y,  9, 23),  date(Y, 12, 20))),
           ('winter', (date(Y, 12, 21),  date(Y, 12, 31)))]

def dayTimeNeighbors(dayTime):
    i = [y[0] for y in dayTimes].index(dayTime)
    p = dayTimes[(i - 1) % 5]
    n = dayTimes[(i + 1) % 5]
    return p, n

def seasonNeighbors(season):
    i = [y[0] for y in seasons].index(season)
    p = seasons[(i - 1) % 4]
    n = seasons[(i + 1) % 4]
    return p, n

def DayTimeCoefficient(dt1, dt2):
    if dt1 == dt2:
        return 1
    elif dt1 in dayTimeNeighbors(dt2):
        return 0.8
    else:
        return 0.7

def SeasonCoefficient(s1, s2):
    if s1 == s2:
        return 1
    elif s1 in seasonNeighbors(s2):
        return 0.8
    else:
        return 0.7

def DayTime(now):
    if isinstance(now, datetime):
        now = now.time()
    now = now.replace(minute=0, second=0, microsecond=0)
    return next(dayTime for dayTime, (start, end) in dayTimes
                if start <= now <= end)
def Season(now):
    if isinstance(now, datetime):
        now = now.date()
    now = now.replace(year=Y)
    return next(season for season, (start, end) in seasons
                if start <= now <= end)
