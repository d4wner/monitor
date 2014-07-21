#! /usr/bin/env python
#coding=utf-8



def detect_all(host,last,time,protocol):
	if protocol == "http":
		http_detect

if __name__ == "__main__":
	f=open('config','r')
	for line in f:
		#print line
		if "{" in line:
			continue
		elif "host" in line:
			host=line.split("=")[1]
			#print host
		elif "last" in line:
			last=line.split("=")[1]
		elif "time" in line:
			time=line.split("=")[1]
		elif "protocol" in line:
			protocol=line.split("=")[1]
		

