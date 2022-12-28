#! /usr/bin/python3

import re
import csv
from configparser import ConfigParser
import argparse
import textwrap
# import sys
#import requests
# import json
import urllib.parse

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

def _get_api_key():
    """ Fetch the API key form your configuration file.

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

def read_user_cli_args():
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

def get_distkey(origin, dest, api_key):
    """ Get employee-to-job distance"""
    dist_keyRegex = re.compile(r'\s*\"text\" : \"(\d{1,4}.\d) mi\"')
    destin = urllib.parse.quote(dest)
    url = hurl + 'origin=' + origin + '&destination=' + destin + '&key=' + api_key
    payload, headers = {}, {}
    response = requests.request("GET", url, headers=headers, data=payload)
    lines = [response.text]
    for line in lines:
        ggllz = dist_keyRegex.search(line)
        if ggllz:
            dist_key = float(ggllz.group(1))
            break
    return dist_key

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

def getDays(emp_add, emp_job, empRegex, jobRegex):
    """Build the employee, address, job no. dictionary."""
    job_dayRegex = re.compile(r'([1-9]\d*.\d{2})')
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
                daycount = 0
                for xday in job_var:            # count days on job/employee
                    if job_dayRegex.search(xday):
                        daycount += 1
                mydict[job_key] = daycount-1
            if empvar in job_var:
                isJob = True
        big_list.append({'emp': empvar, 'addr': e_val[1], 'job': mydict})
        print(big_list[-1])
    return big_list

def makeJoblist(jobvar, jbarray):
    """Attach an address to the active job."""
    job = {}
    for jb in jbarray:
        if jobvar in jb[0]:
            job = {'job': jobvar, 'addr': jb[1]+", "+jb[2]}
            break
    return job

'''
emp_job_file = 'test04.csv'       # emloyee job file
emp_dr_file = 'tested.csv'     # employee driver file
emp_add_file = 'emp.csv'          # emloyee address file
cust_job_file = 'ccl.csv'         # customer job file
'''
if __name__ == "__main__":
    bob = read_user_cli_args()
    print(bob.file[0], bob.file[1], bob.file[2], bob.file[3])
    input_list = read_user_cli_args()
print(input_list.file)

emp_job, emp_dr, emp_add, cust_job = [listFile(x) for x in input_list.file]

emp_a = makeList(emp_job, emp_Regex, 2)
emp_ab = [ab[0] for ab in emp_dr if ab[0] in emp_a]
emp_abc = [abc for abc in emp_add if abc[0] in emp_ab]
job_list = makeList(emp_job, job_keyRegex, 1)
print(emp_ab, "\n\n")
print(emp_abc, "\n\n")
print(job_list)
job_add_d = [makeJoblist(jobvar, cust_job) for jobvar in job_list]

# generate data structure per employee
biglist = getDays(emp_abc, emp_job, emp_Regex, job_keyRegex)
# print(biglist)

""" For one employee record,                                  
    step though emp-jobs finding the distance to the cust-job."""
'''
outputFile = open(outname, 'w')
outputWriter = csv.writer(outputFile)
api_key = _get_api_key()

for glist in biglist:
    dict_mile = {}
    originx = glist.get('addr')
    for addkey in glist['job'].keys():
        dest = next(x for x in job_add_d if x["job"] == addkey)['addr']
        origin = urllib.parse.quote(originx)
        dist_key = get_distkey(hurl, origin, dest, api_key)

        dict_mile.update({addkey: dist_key})
    glist.update({'miles': dict_mile})
    outputWriter.writerow([glist['emp']])
#    print(index(glist['emp']))
    outputWriter.writerow(['Job Num', 'Miles', 'Days', 'total'])
    v1 = glist['job']
    Xtotal = 0
    for k2 in v1:
        days = (glist['job'][k2])
        oneway = (glist['miles'][k2])
        jobNum = str(k2)
        total = int(oneway)*int(days)*2
        Xtotal += total
        outputWriter.writerow([jobNum, oneway, days, total])
    outputWriter.writerow([glist['emp']+' Total miles=', '', '', '', str(Xtotal)])
    print(glist['emp']+', Total miles='+str(Xtotal))

outputFile.close()

'''
