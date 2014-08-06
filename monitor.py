#! /usr/bin/env python
#coding=utf-8
import os.path  
import urllib2
import urllib
import httplib
import time
import threading
from threading import Thread
import Queue
import socket
import os
import sys
import struct
import select
import random
import asyncore
import xml.dom.minidom

site_info=[]
protocol=""
global ISOTIMEFORMAT
ISOTIMEFORMAT='%Y-%m-%d-%X'

server_target = ('localhost',1234)

ICMP_ECHO_REQUEST = 8 

ICMP_CODE = socket.getprotobyname('icmp')
ERROR_DESCR = {
	1: ' - Note that ICMP messages can only be '
	   'sent from processes running as root.',
	10013: ' - Note that ICMP messages can only be sent by'
		   ' users or processes with administrator rights.'
	}

queue = Queue.Queue()

def udp_sender(ip,port):
	try:
		ADDR = (ip,port)
		sock_udp = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		sock_udp.sendto("abcd...",ADDR)
		sock_udp.close()
	except:
		pass

def icmp_receiver(ip,port):
	icmp = socket.getprotobyname("icmp")
	try:
		sock_icmp = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
	except socket.error, (errno, msg):
		if errno == 1:
			# Operation not permitted
			msg = msg + (
				" - Note that ICMP messages can only be sent from processes"
				" running as root."
			)
			raise socket.error(msg)
		raise # raise the original error
	sock_icmp.settimeout(3)
	try:
		recPacket,addr = sock_icmp.recvfrom(64)
	except:
		queue.put(True)
		return
	icmpHeader = recPacket[20:28]
	icmpPort = int(recPacket.encode('hex')[100:104],16)
	head_type, code, checksum, packetID, sequence = struct.unpack(
			"bbHHh", icmpHeader
	)
	sock_icmp.close()
	if code == 3 and icmpPort == port and addr[0] == ip:
		queue.put(False)
	return

def checker_udp(ip,port):

	thread_udp = threading.Thread(target=udp_sender,args=(ip,port))
	thread_icmp = threading.Thread(target=icmp_receiver,args=(ip,port))

	thread_udp.daemon= True
	thread_icmp.daemon = True

	thread_icmp.start()
	time.sleep(0.1)
	thread_udp.start()

	thread_icmp.join()
	thread_udp.join()
	return queue.get(False)

########################ICMP detect#####################

def checksum(source_string):
	sum = 0
	count_to = (len(source_string) / 2) * 2
	count = 0
	while count < count_to:
		this_val = ord(source_string[count + 1])*256+ord(source_string[count])
		sum = sum + this_val
		sum = sum & 0xffffffff 
		count = count + 2
	if count_to < len(source_string):
		sum = sum + ord(source_string[len(source_string) - 1])
		sum = sum & 0xffffffff 
	sum = (sum >> 16) + (sum & 0xffff)
	sum = sum + (sum >> 16)
	answer = ~sum
	answer = answer & 0xffff
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer


def create_packet(id):
	header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, id, 1)
	data = 192 * 'Q'
	my_checksum = checksum(header + data)
	header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0,
						 socket.htons(my_checksum), id, 1)
	return header + data


def do_one(dest_addr, timeout=1):
	
	try:
		my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, ICMP_CODE)
	except socket.error , e:
		if e.errno in ERROR_DESCR:
			raise socket.error(''.join((e.args[1], ERROR_DESCR[e.errno])))
	try:
		host = socket.gethostbyname(dest_addr)
	except socket.gaierror:
		return
	packet_id = int((id(timeout) * random.random()) % 65535)
	packet = create_packet(packet_id)
	while packet:
		sent = my_socket.sendto(packet, (dest_addr, 1))
		packet = packet[sent:]
	delay = receive_ping(my_socket, packet_id, time.time(), timeout)
	my_socket.close()
	return delay


def receive_ping(my_socket, packet_id, time_sent, timeout):
	time_left = timeout
	while True:
		started_select = time.time()
		ready = select.select([my_socket], [], [], time_left)
		how_long_in_select = time.time() - started_select
		if ready[0] == []: 
			return
		time_received = time.time()
		rec_packet, addr = my_socket.recvfrom(1024)
		icmp_header = rec_packet[20:28]
		type, code, checksum, p_id, sequence = struct.unpack(
			'bbHHh', icmp_header)
		if p_id == packet_id:
			return time_received - time_sent
		time_left -= time_received - time_sent
		if time_left <= 0:
			return


def verbose_ping(dest_addr, timeout=2, count=4):
	print('ping {}...'.format(dest_addr))
	delay = do_one(dest_addr, timeout)
	if delay == None:
		return False
	else:
		delay = round(delay * 1000.0, 4)
	return True
	print('')


class PingQuery(asyncore.dispatcher):
	def __init__(self, host, p_id, timeout=0.5, ignore_errors=False):
	
		asyncore.dispatcher.__init__(self)
		try:
			self.create_socket(socket.AF_INET, socket.SOCK_RAW, ICMP_CODE)
		except socket.error , e:
			if e.errno in ERROR_DESCR:
				raise socket.error(''.join((e.args[1], ERROR_DESCR[e.errno])))
			raise 
		self.time_received = 0
		self.time_sent = 0
		self.timeout = timeout
		self.packet_id = int((id(timeout) / p_id) % 65535)
		self.host = host
		self.packet = create_packet(self.packet_id)
		if ignore_errors:
			self.handle_error = self.do_not_handle_errors
			self.handle_expt = self.do_not_handle_errors

	def writable(self):
		return self.time_sent == 0

	def handle_write(self):
		self.time_sent = time.time()
		while self.packet:
			sent = self.sendto(self.packet, (self.host, 1))
			self.packet = self.packet[sent:]

	def readable(self):
		if (not self.writable()
			and self.timeout < (time.time() - self.time_sent)):
			self.close()
			return False
		return not self.writable()

	def handle_read(self):
		read_time = time.time()
		packet, addr = self.recvfrom(1024)
		header = packet[20:28]
		type, code, checksum, p_id, sequence = struct.unpack("bbHHh", header)
		if p_id == self.packet_id:
			self.time_received = read_time
			self.close()

	def get_result(self):
		if self.time_received > 0:
			return self.time_received - self.time_sent

	def get_host(self):
		return self.host

	def do_not_handle_errors(self):
		pass

	def create_socket(self, family, type, proto):
		sock = socket.socket(family, type, proto)
		sock.setblocking(0)
		self.set_socket(sock)
		self.family_and_type = family, type

	def handle_connect(self):
		pass

	def handle_accept(self):
		pass

	def handle_close(self):
		self.close()


def multi_ping_query(hosts, timeout=1, step=512, ignore_errors=False):
  
	results, host_list, id = {}, [], 0
	for host in hosts:
		try:
			host_list.append(socket.gethostbyname(host))
		except socket.gaierror:
			results[host] = None
	while host_list:
		sock_list = []
		for ip in host_list[:step]: 
			id += 1
			sock_list.append(PingQuery(ip, id, timeout, ignore_errors))
			host_list.remove(ip)
		asyncore.loop(timeout)
		for sock in sock_list:
			results[sock.get_host()] = sock.get_result()
	return results


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
		self.taskQueue=Queue.Queue()
		self.threadNum=3
		self.__create_taskqueue(site_info)
		self.__create_threadpool(self.threadNum)

	def __create_taskqueue(self,site_info):
		for items in site_info:
			host=items.split(":")[0]
			protocol=items.split(":")[1]
			sid=items.split(":")[2]
			self.add_task(detect_all,host,protocol,sid)

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

def http_detect(host,port,sid,flag):
	url="http://"+host+":"+str(port)
	try:
		resp=urllib2.urlopen(url,timeout=5)
		#result_post(sid,"1")
		flag=0
		return flag
	except:
		#print "Can't contact the server " +host+":"+str(port)
		#result_post(sid,"0")
		if flag !=2:
			flag=flag+1
			return flag
	time.sleep(int(last))
	

def tcp_detect(host,port,sid,flag):
	sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sk.settimeout(2)
	print "tcp"
	try:
		sk.connect((host,port))
		#if flag != 0:
		flag=0
		return flag
	except Exception,e:
		#print 'Server '+host+': port is not connected!'
		#result_post(sid,"0")
		if flag !=2:
			flag=flag+1
			return flag
	sk.close()
	time.sleep(int(last))

def udp_detect(host,port,sid,flag):
	if not checker_udp(host,port):
		#print 'Server'+host+': port is not connected!'
		#result_post(sid,"0")
		if flag !=2:
			flag=flag+1
			return flag
	else:
		#result_post(sid,"1")
		flag=0
		return flag
	time.sleep(int(last))


def icmp_detect(host,sid,flag):
	if not verbose_ping(host):
		#print "Can't contact the server "+host
		#result_post(sid,"0")
		if flag !=2:
			flag=flag+1
			return flag
	else:
		flag=0
		return flag
		#result_post(sid,"1")
	time.sleep(int(last))
##########################xml parse##########################
def xmlparse():
	global times,last
	count=0
	dom = xml.dom.minidom.parse("config.xml")
	root = dom.documentElement
	last = root.getElementsByTagName("minute")[0].childNodes[0].nodeValue 
	times = root.getElementsByTagName('times')[0].childNodes[0].nodeValue 
	nodes=  root.getElementsByTagName('hostlist')[0].childNodes
	for node in nodes:
		count=count+1
	#count=count/2
	count=count-1
	for x in range(1,count,2):
		sid=root.getElementsByTagName('hostlist')[0].childNodes[x].getElementsByTagName("id")[0].childNodes[0].nodeValue
		host=root.getElementsByTagName('hostlist')[0].childNodes[x].getElementsByTagName("host")[0].childNodes[0].nodeValue
		try:
			port=root.getElementsByTagName('hostlist')[0].childNodes[x].getElementsByTagName("port")[0].childNodes[0].nodeValue
		except:
			port="-1"
		host=host+"#"+port
		protocol=root.getElementsByTagName('hostlist')[0].childNodes[x].getElementsByTagName("protocol")[0].childNodes[0].nodeValue
		site_info.append(host+":"+protocol+":"+sid)
#########################result_post#########################
def result_post(sid,state):
	params = urllib.urlencode({'id':sid,'state':state})
	headers = {"Content-Type":"application/x-www-form-urlencoded","Connection":"Keep-Alive"}
	#f = urllib.urlopen("http://192.168.10.170:8080/?getconfig", params)
	try:
		conn = httplib.HTTPConnection("192.168.10.170",8080)
		conn.request(method="POST",url="/?getconfig",body=params,headers=headers)
		response = conn.getresponse()
		print response.read()
	except Exception,e:
		#print e
		pass

#############################################################
def detect_all(host,protocol,sid):
	flag=0
	if protocol == "http":
		print 'Starting http_monitor on host',host,sid
		http_t=time.time()
		r_host=host.split("#")[0]
		port=int(host.split("#")[1])
		for i in range(int(times)):
			flag=http_detect(r_host,port,sid,flag)
			if flag==2:
				print "Can't contact the http_server " +host+":"+str(port)
				#result_post(sid,"0")
				break
			else:
				print "host_running:",host,flag
				#result_post(sid,"1")
		print 'used time:%f' % (time.time()-http_t) ,host
	elif protocol == "tcp":
		print 'Starting tcp_monitor on host',host,sid
		tcp_t=time.time()
		r_host=host.split("#")[0]
		port=int(host.split("#")[1])
		for i in range(int(times)):
			flag=tcp_detect(r_host,port,sid,flag)
			if flag==2:
				print "Can't contact the tcp_server " +host+":"+str(port)
				#result_post(sid,"0")
				break
			else:
				print "host_running:",host,flag
				#result_post(sid,"1")
		print 'used time:%f' % (time.time()-tcp_t) ,host
	elif protocol == "udp":
		print 'Starting udp_monitor on host',host
		udp_t=time.time()
		r_host=host.split("#")[0]
		port=int(host.split("#")[1])
		for i in range(int(times)):
			flag=udp_detect(r_host,port,sid,flag)
			if flag==2:
				print "Can't contact the udp_server " +host+":"+str(port)
				result_post(sid,"0")
				break
			else:
				print "host_running:",host,flag
				result_post(sid,"1")
		print 'used time:%f' % (time.time()-udp_t) ,host
	elif protocol == "icmp":
		print 'Starting icmp_monitor on host',host
		icmp_t=time.time()
		r_host=host.split("#")[0]
		for i in range(times):
			flag=icmp_detect(r_host,sid,flag)
			if flag==2:
				print "Can't contact the icmp_server " +host+":"+str(port)
				result_post(sid,"0")
				break
			else:
				print "host_running:",host,flag
				result_post(sid,"1")
		print 'used time:%f' % (time.time()-icmp_t),host 
#################################################################

if __name__ == "__main__":
	t=time.time()
	#f=open('config.xml','w')
	#response=urllib.urlopen('http://192.168.10.170:8080/?getconfig').read()
	#f.writelines(response)
	#f.close()
	#os.system('wget http://192.168.10.170:8080/?getconfig -O config.xml')
	try:
		f=open('config.xml','r')
	except:
		print "Open config file failed！"
		exit(0)
	xmlparse()
	tp=ThreadPool(site_info)
	tp.waitfor_complete()
	print 'Used time:%f' % (time.time()-t)
	

