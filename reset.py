#! /usr/bin/env python
import time
import os
import socket
import threading

def reset(pid):	
	try:
		if os.popen('ps -ef|grep '+pid).read(): 
			os.system('kill -9 '+pid)
		print "Process has been killed."
	except:
		pass
	try:
		os.system('python monitor.py')
	except Exception,e:
		print e
		exit(0)

class thread_watch(threading.Thread):
	def __init__(self,connection):
		self.isRunning = True
		threading.Thread.__init__(self)
		self.connection=connection

	def stop(self):
		print "Server stopping ..."
		self.isRunning = False

	def run(self):
		print "Server starting.."
		self.connection.settimeout(6)
		pid=str(self.connection.recv(1024))
		while(self.isRunning):
			time.sleep(2)
			try:
				self.connection.send(' Monitor_testing...')
				self.connection.settimeout(5)
				data=self.connection.recv(1024)
				print "data: ",data
				if data == "shutdown":
					break
					exit(0)
				#print data
			except socket.timeout:
				#print e
				print "Recived no data!"
				thread_watch = threading.Thread(target=reset,args=(pid,))
				thread_watch.daemon= True
				thread_watch.start()
		self.connection.close()
		#self.stop()


if __name__ == '__main__':
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
	sock.bind(('localhost', 8888))
	while True:
		sock.listen(5)
		connection,address = sock.accept()
		if connection:
			try:
				thread_watcher = thread_watch(connection)
				thread_watcher.start()
			except KeyboardInterrupt:
				thread_watcher.stop()
				break
				exit(0)















