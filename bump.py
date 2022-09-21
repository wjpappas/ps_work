#! /usr/bin/python3

import re, csv, sys
import requests, json
import urllib.parse

'''
mempfile = sys.argv[1]          #emloyee job file
sempfile = sys.argv2]           #employee driver file
empadd = sys.argv[3]            #emloyee address file
custjob = sys.argv[4]           #customer job file
outname = sys.argv[5]           #employee miles output file
'''
mempfile = 'test04.csv'       #emloyee job file
sempfile = 'tested.csv'     #employee driver file
empadd = 'emp.csv'          #emloyee address file
custjob = 'ccl.csv'         #customer job file

outname = 'emp_miles.csv'
outputFile = open(outname, 'w')
outputWriter = csv.writer(outputFile)

api_key = 'AIzaSyC5KTP5tuu4I-g5amjmO3eLpTOZKeur8KQ'

dist_keyRegex = re.compile(r'\s*\"text\" : \"(\d{1,4}.\d) mi\"')
job_keyRegex = re.compile(r':([\d]{2}[-][\d]{3})')
employeeRegex = re.compile(r'(Total )(\w+\s*\w*,\s\w+\s*\w*)')
job_dayRegex = re.compile(r'([1-9]\d*.\d{2})')

def listFile(infile):
    with open(infile) as in_file:
        file_read = csv.reader(in_file)
        array = list(file_read)
    return array

def makeList(array,regex,gid):
    mylist = []
    for liste in array:
        if(regex.search(liste[0])):
            gggmz = regex.search(liste[0])
            listx = gggmz.group(gid)
            if listx not in mylist:
                mylist.append(gggmz.group(gid))
    return mylist

def getDays(mempvar,sparray,employeeRegex,job_keyRegex,job_dayRegex):
    x = 0
    minidict = {}
    while x < len(sparray):
        if mempvar in sparray[x]:
            isJob = True
            while isJob:
                x = x+1
                if (employeeRegex.search(sparray[x][0])):
                    isJob = False
                if (job_keyRegex.search(sparray[x][0])):
                    ggllz = job_keyRegex.search(sparray[x][0])
                    job_key = ggllz.group(1)
                    z=1
                    daycount = 0
                    while z < len(sparray[x])-1:
                        if (job_dayRegex.search(sparray[x][z])):
                            daycount +=1
                        z = z+1
                    minidict[job_key]=daycount
        x = x+1
    return minidict

def makeBiglist(bvar,array,mydict):
    dictlst = {}
    for bg in array:
        if bvar in bg:
            dictlst = {'emp':bvar,'addr':bg[1],'job':mydict}
            break
    return dictlst

def makeJoblist(jobvar,jbarray):
    job = {}
    for jb in jbarray:
        if jobvar in jb[0]:
            job = {'job':jobvar,'addr':jb[1]+", "+jb[2]}
            break
    return job

biglist = []
joblistx = []

sparray = listFile(mempfile)

memp1 = makeList(sparray,employeeRegex,2)
joblist = makeList(sparray,job_keyRegex,1)

array = listFile(empadd)
jbarray = listFile(custjob)

print(joblist)
jaddlist = [makeJoblist(jobvar,jbarray) for jobvar in joblist]

f = open('tested.csv')
lines = list(f)
f.close

new_lst = [x[1:-2] for x in lines]
memp2 = []
for x in new_lst:
    for list in memp1:
        if x in list:
            memp2.append(x)

#generate data structure per employee
for mempvar in memp2:
    mydict = getDays(mempvar,sparray,employeeRegex,job_keyRegex,job_dayRegex)
    biglist.append(makeBiglist(mempvar,array,mydict))
#print(biglist)

hurl = "https://maps.googleapis.com/maps/api/directions/json?"

for glist in biglist:
    dict_mile = {}

    originx = glist.get('addr')
    for addkey in glist['job'].keys():
        dest = next(x for x in jaddlist if x["job"] == addkey)['addr']
        origin = urllib.parse.quote(originx)
        destination = urllib.parse.quote(dest)
        url = hurl + 'origin=' + origin + '&destination=' + destination + '&key=' + api_key

        payload={}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        lines = [response.text]
        for line in lines:
            if(dist_keyRegex.search(line)):
                ggllz = dist_keyRegex.search(line)
                dist_key = float(ggllz.group(1))
#                print(dist_key)
                break
        dict_mile.update({addkey:dist_key})
#        print(dict_mile)
    glist.update({'miles':dict_mile})
    outputWriter.writerow([glist['emp']])
#    print(index(glist['emp']))
    outputWriter.writerow(['Job Num','Miles','Days','total'])
#    print('Job Num','Miles','Days','total')
    v1 = glist['job']
    Xtotal = 0
    for k2 in v1:
        days = (glist['job'][k2])
        oneway = (glist['miles'][k2])
        jobNum = str(k2)
        total = int(oneway)*int(days)*2
        Xtotal += total
        outputWriter.writerow([jobNum,oneway,days,total])
#        print(jobNum,oneway,days,total)
    outputWriter.writerow([glist['emp']+' Total miles=','','','',str(Xtotal)])
    print(glist['emp']+', Total miles='+str(Xtotal))

outputFile.close()
