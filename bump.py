#! /usr/bin/python3

import re
import csv
# import sys
import requests
# import json
import urllib.parse

'''
#read all files(4) --> list
# get employee from employee job list-file
# get employee from employee driver list-file
# make list, intersection of employees
# make list, employee-address dict
# get jobs worked from employee job list
#
emp_job_file = sys.argv[1]          #emloyee job file
emp_dr_file = sys.argv2]           #employee driver file
emp_add_file = sys.argv[3]            #emloyee address file
cust_job_file = sys.argv[4]           #customer job file
outname = sys.argv[5]           #employee miles output file








'''
emp_job_file = 'test04.csv'       # emloyee job file
emp_dr_file = 'tested.csv'     # employee driver file
emp_add_file = 'emp.csv'          # emloyee address file
cust_job_file = 'ccl.csv'         # customer job file

outname = 'emp_miles.csv'
outputFile = open(outname, 'w')
outputWriter = csv.writer(outputFile)

api_key = 'AIzaSyC5KTP5tuu4I-g5amjmO3eLpTOZKeur8KQ'

dist_keyRegex = re.compile(r'\s*\"text\" : \"(\d{1,4}.\d) mi\"')
job_keyRegex = re.compile(r':([\d]{2}[-][\d]{3})')
empRegex = re.compile(r'(Total )(\w+\s*\w*,\s\w+\s*\w*)')
job_dayRegex = re.compile(r'([1-9]\d*.\d{2})')

def listFile(infile):
    with open(infile) as in_file:
        file_read = csv.reader(in_file)
        array = list(file_read)
    return array

def makeList(array, regex, gid):
    mylist = []
    for liste in array:
        gggmz = regex.search(liste[0])
        if gggmz:
            listx = gggmz.group(gid)
            if listx not in mylist:
                mylist.append(gggmz.group(gid))
    return mylist

def getDays(emp_add_list, emp_job, empRegex, job_keyRegex, job_dayRegex):
    big_list = []
    mydict = {}
    for e_val in emp_add_list:
        empvar = e_val[0]
        isJob = False
        for job_var in emp_job:
            if isJob:
                ggllz = job_keyRegex.search(job_var[0])
                job_key = ggllz.group(1)
                daycount = 0
                for xday in job_var:
                    if job_dayRegex.search(xday):
                        daycount += 1
                mydict[job_key] = daycount-1
            if empvar in job_var:
                isJob = True
            if ("Total " + empvar) in job_var:
                isJob = False   # or maybe "Break"
        big_list.append({'emp': empvar, 'addr': e_val[1], 'job': mydict})

def makeJoblist(jobvar, jbarray):
    job = {}
    for jb in jbarray:
        if jobvar in jb[0]:
            job = {'job': jobvar, 'addr': jb[1]+", "+jb[2]}
            break
    return job

emp_job = listFile(emp_job_file)
emp_dr = listFile(emp_dr_file)
emp_add = listFile(emp_add_file)
cust_job = listFile(cust_job_file)

emp_a = makeList(emp_job, empRegex, 2)
emp_ab = [set(emp_job).difference(set(emp_dr))]
emp_abc = [abc for ab, abc in zip(emp_ab, emp_add) if ab == abc[0]]
job_list = makeList(emp_job, job_keyRegex, 1)
print(job_list)
job_add_d = [makeJoblist(jobvar, cust_job) for jobvar in job_list]

# generate data structure per employee
biglist = getDays(emp_abc, emp_job, empRegex, job_keyRegex, job_dayRegex)
# print(biglist)

hurl = "https://maps.googleapis.com/maps/api/directions/json?"

for glist in biglist:
    dict_mile = {}

    originx = glist.get('addr')
    for addkey in glist['job'].keys():
        dest = next(x for x in job_add_d if x["job"] == addkey)['addr']
        origin = urllib.parse.quote(originx)
        destination = urllib.parse.quote(dest)
        url = hurl + 'origin=' + origin + '&destination=' + destination + '&key=' + api_key

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        lines = [response.text]
        for line in lines:
            if (dist_keyRegex.search(line)):
                ggllz = dist_keyRegex.search(line)
                dist_key = float(ggllz.group(1))
#                print(dist_key)
                break
        dict_mile.update({addkey: dist_key})
#        print(dict_mile)
    glist.update({'miles': dict_mile})
    outputWriter.writerow([glist['emp']])
#    print(index(glist['emp']))
    outputWriter.writerow(['Job Num', 'Miles', 'Days', 'total'])
#    print('Job Num','Miles','Days','total')
    v1 = glist['job']
    Xtotal = 0
    for k2 in v1:
        days = (glist['job'][k2])
        oneway = (glist['miles'][k2])
        jobNum = str(k2)
        total = int(oneway)*int(days)*2
        Xtotal += total
        outputWriter.writerow([jobNum, oneway, days, total])
#        print(jobNum,oneway,days,total)
    outputWriter.writerow([glist['emp']+' Total miles=', '', '', '', str(Xtotal)])
    print(glist['emp']+', Total miles='+str(Xtotal))

outputFile.close()
