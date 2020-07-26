import pandas as pd
import requests
import numpy as np
from io import StringIO
import time
import html5lib
from datetime import datetime, timedelta, date
import calendar
import datetime as dt
from functools import reduce
import json
import os
from collections import Counter

# functions for processing convenience
def revr(data, nmbr):
    cols = data.columns.tolist()
    cols = cols[nmbr:] + cols[:nmbr]
    data = data[cols]
    return data

def add_months(sourcedate, months):
    sourcedate = datetime.strptime(sourcedate, "%Y%m%d").date() if type(sourcedate)==str else sourcedate
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return dt.date(year, month, day)

def fullpathname(outdir, outname):
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    return os.path.join(outdir, outname)

def clean(d):
    d = d.fillna(1e-4)
    def flt(x):
        try:
            return float(x)
        except ValueError:
            # return 0
            return 1e-4
    not_nmbr = ['日','月','季','年','代號','名稱']
    numeric_cols = list(filter(lambda x:not any(i in x for i in not_nmbr), list(d.columns)))
    for i in numeric_cols:
        d[i] = d[i].apply(flt)                           
    return d

    