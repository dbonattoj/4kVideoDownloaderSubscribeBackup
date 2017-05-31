import sys
import os
from datetime import datetime
import calendar

def getTimestamp(year, month, day):
    d = datetime(year=int(year), month=int(month), day=int(day))
    return calendar.timegm(d.timetuple())

def getDate(timestamp):
    return str(datetime.fromtimestamp(timestamp))

walk = os.walk('.')

if len(sys.argv) < 4:
    today = datetime.now()
    min_date = getTimestamp(today.year, today.month, today.day-5)
else:
    min_date = getTimestamp(sys.argv[1], sys.argv[2], sys.argv[3])
print("Videos from date: " + getDate(min_date))
print()

files = {}

for w in walk:
    if w[2]:
        for file in w[2]:
            file_path = str(w[0]) + "/" + file
            date = os.path.getmtime(file_path)
            if date > min_date:
                files[getDate(date)] = file_path

    with open("list_" + getDate(min_date)[0:10] + ".txt", 'w', encoding='utf-8') as f:
        for key in sorted(files.keys()):
            txt = key[0:19] + " " + files[key]
            print(txt)
            f.write(txt)
            f.write('\n')



