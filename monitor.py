#! /usr/bin/env python
#coding=utf-8
import urllib
import time
import threading
from threading import Thread
from Queue import Queue
import socket
from  icmp_ping import verbose_ping
from udp_detect import checker_udp
import os
import sys

site_info=[]
protocol=""
global r,last,times,ISOTIMEFORMAT
ISOTIMEFORMAT='%Y-%m-%d-%X'
last=3
times=5
###################Single thread_watch#################
class thread_watch(threading.Thread):
	def __init__(self):
		self.isRunning = True
		threading.Thread.__init__(self)
		pass

	def stop(self):
		print "stopping ..."
		self.isRunning = False
		#pid = str(connection.recv(1024))
	def run(self):
		print 'Client starting...'
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(('localhost', 8888))
		pid=str(os.getpid())
		while(self.isRunning):
			try:
				sock.send(pid)
				sock.settimeout(5)
				buf = sock.recv(1024)
			except Exception,e:
				print e
				pass
		sock.sendall("shutdown")
		sock.close()

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

###############Threading Pool#################
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
			protocol=items.split(":")[1]
			self.add_task(detect_all,host,protocol)

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

#########################Detect Models######################

def http_detect(host):
	resp=urllib.urlopen("http://"+host)
	if resp.getcode() != 200:
		print "Can't contact the server "+host
		r.writelines("HTTP_lost "+host+" "+time.strftime(ISOTIMEFORMAT, time.localtime())+"\n")
	time.sleep(int(last))
	

def tcp_detect(host,port):
	sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sk.settimeout(2)
	try:
		sk.connect((host,port))
	except Exception,e:
		#print e
		print 'Server '+host+': port is not connected!'
		r.writelines("TCP_lost "+host+" "+time.strftime(ISOTIMEFORMAT, time.localtime())+"\n")
	sk.close()
	time.sleep(int(last))

def udp_detect(host,port):
	if not checker_udp(host,port):
		print 'Server'+host+': port is not connected!'
		r.writelines("UDP_lost "+host+" "+time.strftime(ISOTIMEFORMAT, time.localtime())+"\n")
	time.sleep(int(last))


def icmp_detect(host):
	if not verbose_ping(host):
		print "Can't contact the server "+host
		r.writelines("ICMP_lost "+host+" "+time.strftime(ISOTIMEFORMAT, time.localtime())+"\n")
	time.sleep(int(last))

#############################################################
def detect_all(host,protocol):
	if protocol == "http":
		print 'Starting http_monitor on host',host
		http_t=time.time()
		for i in range(int(times)):
			http_detect(host)
		print 'used time:%f' % (time.time()-http_t) ,host
	elif protocol == "tcp":
		print 'Starting tcp_monitor on host',host
		tcp_t=time.time()
		for i in range(int(times)):
			r_host=host.split("#")[0]
			port=int(host.split("#")[1])
			tcp_detect(r_host,port)
		print 'used time:%f' % (time.time()-tcp_t) ,host
	elif protocol == "udp":
		print 'Starting udp_monitor on host',host
		udp_t=time.time()
		for i in range(int(times)):
			r_host=host.split("#")[0]
			port=int(host.split("#")[1])
			udp_detect(r_host,port)
		print 'used time:%f' % (time.time()-udp_t) ,host
	elif protocol == "icmp":
		print 'Starting icmp_monitor on host',host
		icmp_t=time.time()
		for i in range(times):
			icmp_detect(host)
		print 'used time:%f' % (time.time()-icmp_t),host 


if __name__ == "__main__":
	r=open('warn_result.log','w+')
	t=time.time()
	if len(sys.argv)<2:
		pass
	else:
		os.system('wget '+sys.argv[1]+'-O config')
	try:
		f=open('config','r')
	except:
		print "Open config file failed！"
	thread_watcher = thread_watch()
	thread_watcher.start()
	for line in f:
		line=line.strip()
		#print line
		if "{" in line:
			continue
		elif "host" in line:
			host=line.split("=")[1]
		elif "protocol" in line:
			protocol=line.split("=")[1]
		if  protocol != "":
			site_info.append(host+":"+protocol)
			host = ""
			protocol = ""
	tp=ThreadPool(site_info)
	tp.waitfor_complete()
	print 'Used time:%f' % (time.time()-t)
	f.close()
	r.close()
	time.sleep(2)
	thread_watcher.stop()

