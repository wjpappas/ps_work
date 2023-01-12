#! /usr/bin/python3

import re
import csv
import logging
from datetime import datetime
from configparser import ConfigParser
import argparse
import textwrap
import requests
import urllib.parse

logging.basicConfig(filename='log_filename.txt', level=logging.DEBUG, format='%(lineno)d - %(funcName)s - %(levelname)s - %(message)s')
hurl = "https://maps.googleapis.com/maps/api/directions/json?"

job_keyRegex = re.compile(r'([\d]{2}[-][\d]{3})')
emp_Regex = re.compile(r'(Total )(\w+\s*\w*,\s\w+\s*\w*)')

outname = 'emp_miles.csv'

'''
#read all files(4) --> list
# get employee from employee job list-file
# get employee from employee driver list-file
# make list, intersection of employees
# make list, employee-address dict
# get jobs worked from employee job list
#
'''
def _get_values():
    """ Fetch the Paintsmith config values your configuration file.

    Expects a configuration file named "secrets.ini" with structure:

        [paintsmith]
        overhead=22-000 OH
    """
    config = ConfigParser()
    config.read("secrets.ini")
    return config["paintsmith"]["overhead"]

def _get_api_key():
    """ Fetch the API key from your configuration file.

    Expects a configuration file named "secrets.ini" with structure:

        [google]
        api_key=<YOUR-GOOGLE-API-KEY>
    """
    config = ConfigParser()
    config.read("secrets.ini")
    return config["google"]["api_key"]

def check_ext(a):
    if not a[-4:len(a)] == ".csv":
        raise argparse.ArgumentTypeError(
            "file extension must be *.csv")
    return a

def read_user_cli_args():   # this doesn't act correctly when no args are given
    """Handle the CLI user interactions.

    Returns:
        argparse.Namspace: Populated namespace object
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
        gets the mileage for travel between jobs
        --------------------------------------------------
        emp_job_file  =     *.csv     # emloyee job file
        emp_dr_file   =    **.csv     # employee driver file
        emp_add_file  =   ***.csv     # emloyee address file
        cust_job_file =  ****.csv     # customer job file'''))

    parser.add_argument('-f', '--file', nargs=4, type=check_ext, help='enter 4 ".csv" files: emp_job, emp_dr, emp_add, cust_job')
    return parser.parse_args()

def get_distkey(hurl, origin, dest, api_key):
    """ Get employee-to-job distance"""
    dist_keyRegex = re.compile(r'\s*\"text\" : \"(\d{1,4}.\d) mi\"')
    destin = urllib.parse.quote(dest)
    url = hurl + 'origin=' + origin + '&destination=' + destin + '&key=' + api_key
    payload, headers = {}, {}
    response = requests.request("GET", url, headers=headers, data=payload)
    lines = [response.text]
    for line in lines:                      # fetch miles from reponse
        ggllz = dist_keyRegex.search(line)  # Is there a better way scan
        if ggllz:                           # the json file for the miles?
            dist_key = float(ggllz.group(1))
            logging.debug(dist_key)
            break
    return dist_key

def get_week_num(infile, *args):
    """ Generate a weeknum tuple for day/job entry"""
    wk_num = []
    with open(infile) as in_file:
        line_read = next(csv.reader(in_file))
    line_read.pop()
    idx0 = (datetime.strptime(line_read[1], "%b %d, %y")).isocalendar().weekday
    lastday = (datetime.strptime(line_read[-1], "%b %d, %y")).day
    for dstring in line_read:
        if dstring != '':
            wkx = (datetime.strptime(dstring, "%b %d, %y")).isocalendar().week
            if wkx not in wk_num:
                wk_num.append(wkx)
    idxN = (datetime.strptime(dstring, "%b %d, %y")).isocalendar().weekday
    logging.debug("%s %s %s %s", wk_num, idx0, idxN, lastday)
    return wk_num + [idx0-7, idxN, lastday]

def listFile(infile):
    """Read file into list."""
    with open(infile) as in_file:
        file_read = csv.reader(in_file)
        array = list(file_read)
    return array

def makeList(array, regex, gid):
    """Extract unique data set from list."""
    mylist = []
    for liste in array:
        gggmz = regex.search(liste[0])
        if gggmz:
            listx = gggmz.group(gid)
            if listx not in mylist:
                mylist.append(gggmz.group(gid))
    return mylist

def getDays(emp_add, emp_job, wk_num, empRegex, jobRegex):
    """Build the employee, address, job no. dictionary."""

    big_list = []
    for e_val in emp_add:                       # select emp/address element
        mydict = {}
        empvar = e_val[0]
        isJob = False
        for job_var in emp_job:                 # step thru job/employee
            if ("Total " + empvar) in job_var:  # end of employee block
                isJob = False
            if isJob:
                ggllz = jobRegex.search(job_var[0])
                job_key = ggllz.group(1)
                daycount = get_daycount(job_var, wk_num)
                mydict[job_key] = daycount
            if empvar in job_var:
                isJob = True
        big_list.append({'emp': empvar, 'addr': e_val[1], 'job': mydict})
        logging.debug(big_list[-1])
    return big_list

def get_daycount(hours, weeks):
    """Break out hours for each week"""
    hours.pop()
    first, last, dayN = weeks[-3], weeks[-2], weeks[-1]
    inc = 7
    start = first + inc
    stop = dayN+inc
    st = 1
    wk_list = []
    for i in range(start, stop, inc):
        sp = i
        if i > dayN:
            sp = sp + last - inc
        wk_count = len([x for x in hours[st:sp] if float(x) > 0])
        wk_list.append(wk_count)
        st = sp
    return wk_list

def makeJoblist(jobvar, jbarray):
    """Attach an address to the active job."""
    job = {}
    for jb in jbarray:
        if jobvar in jb[0]:
            job = {'job': jobvar, 'addr': jb[1]+", "+jb[2]}
            break
    return job

if __name__ == "__main__":
    oh_code = _get_values()
    input_list = read_user_cli_args()
    empjobfile = (input_list.file[0])
    week_number = get_week_num(empjobfile)
    logging.debug("x %s %s %s", input_list.file[0], week_number, oh_code)

# try input list True
emp_jobx, emp_dr, emp_add, cust_job = [listFile(x) for x in input_list.file]
emp_job = [x for x in emp_jobx if x[0] != oh_code]

emp_a = makeList(emp_job, emp_Regex, 2)                 # select employees
emp_ab = [ab[0] for ab in emp_dr if ab[0] in emp_a]     # driver from employees
emp_abc = [abc for abc in emp_add if abc[0] in emp_ab]  # driver + address
job_list = makeList(emp_job, job_keyRegex, 1)           # select active jobs
logging.debug(emp_ab)
logging.debug(emp_abc)
logging.debug(job_list)
job_add_d = [makeJoblist(jobvar, cust_job) for jobvar in job_list]

# generate data structure, employee, address, jobs{Job#:days,...}
biglist = getDays(emp_abc, emp_job, week_number, emp_Regex, job_keyRegex)
print(biglist)
print(week_number)

""" For one employee record,                                  
    step though emp-jobs finding the distance to the cust-job."""

outputFile = open(outname, 'w', newline='', encoding='utf-8')
outputWriter = csv.writer(outputFile)
api_key = _get_api_key()
logging.debug(api_key)

for glist in biglist:
    dict_mile = {}
    originx = glist.get('addr')
    logging.debug(glist.get('emp'))
    logging.debug(originx)
    for addkey in glist['job'].keys():
        dest = next(x for x in job_add_d if x["job"] == addkey)['addr']
        logging.debug(dest)
        origin = urllib.parse.quote(originx)
        dist_key = get_distkey(hurl, origin, dest, api_key)

        dict_mile.update({addkey: dist_key})
    glist.update({'miles': dict_mile})
    outputWriter.writerow(['\n'+glist['emp']])
#    print(index(glist['emp']))
    outputWriter.writerow(['Job Num', 'Miles', 'Days', 'total'])
    v1 = glist['job']
    Xtotal = 0
    for k2 in v1:
        jobNum = str(k2)
        oneway = (glist['miles'][k2])
        days = (glist['job'][k2])
        total = int(oneway)*int(sum(days))*2
        Xtotal += total
        outputWriter.writerow([jobNum, oneway, days, total])
    outputWriter.writerow([glist['emp']+' Total miles='+str(Xtotal)])
    print(glist['emp']+', Total miles='+str(Xtotal))

outputFile.close()
