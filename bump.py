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
from pprint import pprint

logging.basicConfig(filename='get_miles.log', level=logging.DEBUG, format='%(lineno)d - %(funcName)s - %(levelname)s - %(message)s')

job_keyRegex = re.compile(r'([\d]{2}[-][\d]{3})')
emp_Regex = re.compile(r'(Total )(\w+\s*\w*,\s\w+\s*\w*)')

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
    return [config["paintsmith"]["overhead"]]
#    return [config["paintsmith"]["overhead"], config["paintsmith"]["outfile"]]

def _get_api_key():
    """ Fetch the API key from your configuration file.

    Expects a configuration file named "secrets.ini" with structure:

        [google]
        api_key=<YOUR-GOOGLE-API-KEY>
    """
    config = ConfigParser()
    config.read("secrets.ini")
    return [config["google"]["api_key"], config["google"]["url"]]

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
        emp_job_file  =  empjob.csv    # emloyee job file
        emp_dr_file   =  empdr.csv     # employee driver file
        emp_gas_file  =  empgas.csv    # employee gas card file
        emp_add_file  =  empadd.csv    # emloyee address file
        cust_job_file =  ccl.csv       # customer job file'''))

    parser.add_argument('-f', '--file', nargs=5, type=check_ext, help='enter 4 ".csv" files: emp_job, emp_dr, emp_gas, emp_add, cust_job')
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

def get_week_num(zlist, *args):
    """ Generate a weeknum tuple for day/job entry plus

        From employee job/hour header
        week_num    [w/n, w/n+1, ...]
        idx0, idxN  iso day of week (first and last)
        lastday     days in the month
    """
    wk_num = []
#    with open(infile) as in_file:
#        line_read = next(csv.reader(in_file))
    zlist.pop()
    idx0 = (datetime.strptime(zlist[1], "%b %d, %y")).isocalendar().weekday
    lastday = (datetime.strptime(zlist[-1], "%b %d, %y")).day
    for dstring in zlist:
        if dstring != '':
            wkx = (datetime.strptime(dstring, "%b %d, %y")).isocalendar().week
            if wkx not in wk_num:
                wk_num.append(wkx)
    idxN = (datetime.strptime(dstring, "%b %d, %y")).isocalendar().weekday
    logging.debug("%s %s %s %s", wk_num, idx0, idxN, lastday)
    return wk_num + [idx0, idxN, lastday]

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
    start = inc - first + 2
    stop = dayN + inc
    logging.debug('day-count %s %s ', start, stop)
    st = 1
    wk_list = []
    for i in range(start, stop, inc):
        sp = i
        if i > dayN:
            sp = sp + last - inc
        wk_count = len([x for x in hours[st:sp] if float(x) > 0])
        logging.debug('day-count %s %s %s ', st, sp, wk_count)
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
    input_list = read_user_cli_args()
    oh_code = _get_values()
#    oh_code, outname = _get_values()


# try input list True
emp_jobx, emp_dr, emp_gas, emp_add, cust_job = [listFile(x) for x in input_list.file]

emp_job = [x for x in emp_jobx if x[0] != oh_code[0]]     # strip overhead code
logging.debug("emp_job: %s", emp_job[0])

outname = input_list.file[1][:input_list.file[1].index('.')] + '_miles.csv'

week_number = get_week_num(emp_job[0])
logging.debug("x %s %s %s", week_number, oh_code, outname)

emp_a = makeList(emp_job, emp_Regex, 2)                 # select employees
emp_abx = [ab for ab in emp_dr if ab not in emp_gas]     # driver not gas card
emp_ab = [ab[0] for ab in emp_abx if ab[0] in emp_a]     # driver from employees
emp_abc = [abc for abc in emp_add if abc[0] in emp_ab]  # driver + address
job_list = makeList(emp_job, job_keyRegex, 1)           # select active jobs
job_add_d = [makeJoblist(jobvar, cust_job) for jobvar in job_list] # job address
logging.debug("Driver AAAA set: %s", emp_a)
logging.debug("Driver gas set: %s", emp_abx)
#logging.debug("Driver address set: %s", emp_add)
logging.debug("Driver set: %s", emp_ab)
logging.debug("Driver and address: %s", emp_abc)
logging.debug("Employee jobs: %s", job_list)
logging.debug("Employee jobs with address: %s", job_add_d)

# generate data structure, employee, address, jobs{Job#:days,...}
biglist = getDays(emp_abc, emp_job, week_number, emp_Regex, job_keyRegex)
pprint(biglist)
print(week_number)

""" For one employee record,                                  
    step though emp-jobs finding the distance to the cust-job."""

# def gen_miles(outname, biglist, api_key, hurl, ...)
outputFile = open(outname, 'w', newline='', encoding='utf-8')
outputWriter = csv.writer(outputFile)
api_key, hurl = _get_api_key()
logging.debug("api key= %s url= %s", api_key, hurl)

for glist in biglist:
    dict_mile = {}
    originx = glist.get('addr')
    for addkey in glist['job'].keys():
        origin = urllib.parse.quote(originx)
        dest = next(x for x in job_add_d if x['job'] == addkey)['addr']
        dist_key = get_distkey(hurl, origin, dest, api_key)
        logging.debug("%s FROM: %s  TO: %s FOR %s miles", glist.get('emp'), originx, dest, dist_key)
        dict_mile.update({addkey: dist_key})
    glist.update({'miles': dict_mile})
    outputWriter.writerow([''])
    outputWriter.writerow([glist['emp'], glist['addr']])
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
    outputWriter.writerow([glist['emp'], ' Total miles=', str(Xtotal)])
    print(glist['emp']+', Total miles='+str(Xtotal))

outputFile.close()


