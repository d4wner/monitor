#! /usr/bin/env python
#coding=utf-8
import urllib
import time
from threading import Thread
from Queue import Queue
import socket

site_info=[]
protocol=""

########################################################
class Worker(Thread):
	def __init__(self,taskQueue):
		Thread.__init__(self)
		self.setDaemon(True)
		self.taskQueue=taskQueue
		self.start()

	def run(self):
		while True:
			try:
				callable,args,kwds=self.taskQueue.get(block=False)
				callable(*args,**kwds)
			except:
				break

#######################################################
class ThreadPool:
	def __init__(self,site_info):
		self.threads=[]
		self.taskQueue=Queue()
		self.threadNum=3
		self.__create_taskqueue(site_info)
		self.__create_threadpool(self.threadNum)

	def __create_taskqueue(self,site_info):
		for items in site_info:
			host=items.split(":")[0]
			last=items.split(":")[1]
			times=items.split(":")[2]
			protocol=items.split(":")[3]
			self.add_task(detect_all,host,last,times,protocol)

	def __create_threadpool(self,threadNum):
		for i in range(threadNum):
			thread=Worker(self.taskQueue)
			self.threads.append(thread)

	def add_task(self,callable,*args,**kwds):
		self.taskQueue.put((callable,args,kwds))

	def waitfor_complete(self):
		while len(self.threads):
			thread=self.threads.pop()
			thread.join()
			if thread.isAlive() and not self.taskQueue.empty():
				self.threads.append(thread)
		print 'Monitoring has completed!'

#######################################################

def http_detect(host,last):
	#print host
	resp=urllib.urlopen("http://"+host)
	#print str(resp.getcode())+":"+host
	if resp.getcode() != 200:
		print "Can't contact the server "+host
	time.sleep(int(last))
	

def tcp_detect(host,last,port):
	sk=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sk=sk.settimeout(2000)
	try:
		sk.connect((host,port))
	except:
		print('Server port is not connected!')
	sk.close()
	time.sleep(int(last))



def detect_all(host,last,times,protocol):
	if protocol == "http":
		#print host+"==detect"
		print 'Starting http_monitor on host',host
		for i in range(int(times)):
			http_detect(host,last)
	elif protocol == "tcp":
		print 'Starting tcp_monitor on host',host
		for i in range(int(times)):
			host=host.split(":")[0]
			port=host.split(":")[1]
			tcp_detect(host,last,port)
			

if __name__ == "__main__":
	t=time.time()
	f=open('config','r')
	for line in f:
		line=line.strip()
		#print line
		if "{" in line:
			continue
		elif "host" in line:
			host=line.split("=")[1]
		elif "last" in line:
			last=line.split("=")[1]
		elif "times" in line:
			times=line.split("=")[1]
		elif "protocol" in line:
			protocol=line.split("=")[1]
		if  protocol != "":
			site_info.append(host+":"+last+":"+times+":"+protocol)
			host = ""
			last = ""
			times = ""
			protocol = ""
	tp=ThreadPool(site_info)
	tp.waitfor_complete()		
	print 'used time:%f' % (time.time()-t) 

