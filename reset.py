#! /usr/bin/env python
import time
import socket
import os
import threading

def reset():
	try:
		os.system('kill -9 '+pid)
		os.system('python reset.py')
	except Exception,e:
		print e
		exit(0)

if __name__ == '__main__':
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('localhost', 8888))
	try:
		sock.send(' Pid_getting...')
		pid= sock.recv(1024)
	except Exception,e:
		print e
		exit(0)
	while(1):
		time.sleep(2)
		try:
			sock.send(' Monitor_testing...')
			sock.settimeout(5)
			data=sock.recv(1024)
			if data == "shutdown":
				break
				exit(0)
			#print data
		except:
			print "Recived no data!"
			thread_watch = threading.Thread(target=reset)
			thread_watch.daemon= True
			thread_watch.start()
			time.sleep(2)
	sock.close()
