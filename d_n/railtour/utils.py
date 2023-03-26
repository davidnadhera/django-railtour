from datetime import datetime,timedelta,date

def handle_timedelta(s):
    s = s.strip(' "')
    word_list = s.split(" ")
    s = word_list[-1]
    t = datetime.strptime(s, "%H:%M:%S")
    return timedelta(hours=t.hour, minutes=t.minute)

def add_time(cas, doba):
    den = datetime.combine(date(2021, 6, 1), cas)
    posun_den = den + doba
    return posun_den.time()

def time_diff(cas2, cas1):
    den1 = datetime.combine(date(2021, 6, 1), cas1)
    den2 = datetime.combine(date(2021, 6, 1), cas2)
    if cas2 < cas1:
        den2 = den2 + timedelta(days=1)
    return den2 - den1
