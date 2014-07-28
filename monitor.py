#! /usr/bin/env python
#coding=utf-8
import urllib
import time
from threading import Thread
from Queue import Queue
import socket
from  icmp_ping import verbose_ping
from udp_detect import checker_udp

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
	sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sk.settimeout(2)
	#print "host:",host
	#print "port:",port
	try:
		sk.connect((host,port))
	except Exception,e:
		print e
		print 'Server '+host+': port is not connected!'
	sk.close()
	time.sleep(int(last))

def udp_detect(host,last,port):
	if not checker_udp(host,port):
		print 'Server'+host+': port is not connected!'
	time.sleep(int(last))


def icmp_detect(host,last):
	#x=verbose_ping(host)
	#print x
	if not verbose_ping(host):
		print "Can't contact the server "+host
	time.sleep(int(last))

def detect_all(host,last,times,protocol):
	#print('host:'+host)
	#print('last:'+last)
	#print('times:'+times)
	#print('protocol:'+protocol)
	if protocol == "http":
		#print host+"==detect"
		print 'Starting http_monitor on host',host
		http_t=time.time()
		for i in range(int(times)):
			http_detect(host,last)
		print 'used time:%f' % (time.time()-http_t) ,host
	elif protocol == "tcp":
		print 'Starting tcp_monitor on host',host
		tcp_t=time.time()
		for i in range(int(times)):
			r_host=host.split("#")[0]
			port=int(host.split("#")[1])
			tcp_detect(r_host,last,port)
		print 'used time:%f' % (time.time()-tcp_t) ,host
	elif protocol == "udp":
		print 'Starting udp_monitor on host',host
		udp_t=time.time()
		for i in range(int(times)):
			r_host=host.split("#")[0]
			port=int(host.split("#")[1])
			udp_detect(r_host,last,port)
		print 'used time:%f' % (time.time()-udp_t) ,host
	elif protocol == "icmp":
		print 'Starting icmp_monitor on host',host
		icmp_t=time.time()
		for i in range(int(times)):
			icmp_detect(host,last)
		print 'used time:%f' % (time.time()-icmp_t),host 

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
	print 'Used time:%f' % (time.time()-t)

