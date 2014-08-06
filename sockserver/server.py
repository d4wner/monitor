#!/usr/bin/python  
import SocketServer  
import os.path 
import socket
# Format: name_len      --- one byte  
#         name          --- name_len bytes  
#         data          --- variable length  
# Save data to name into current directory  
addr = ('localhost', 1234)  
client_target = ('localhost', 1234)  
def get_header (name):  
	leng = len(name)  
	assert leng < 250  
	return chr(leng) + name  
  
def send_file (name):
	basename = os.path.basename(name)  
	header = get_header(basename)  
	cont = open(name).read()  
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
	s.connect(client_target)  
	s.sendall (header)  
	s.sendall (cont)  
	s.close()  

class MyTCPHandler (SocketServer.StreamRequestHandler):  
	def handle (self):
		self.request.send('Server')
		send_file('config')
		send_file('warn_result.log')  
		data=self.rfile.read(6)
		if data == "Client":
			name_len = ord(self.rfile.read(1))  
			name = self.rfile.read(name_len)  
			print "Get request:%s"%name  
			fd = open(name, 'w')  
			cont = self.rfile.read(4096)      
			while cont:  
					fd.write(cont)  
					cont = self.rfile.read(4096)  
			fd.close()  
			print "Out :%s"%name  
		else:
			pass
server = SocketServer.TCPServer(addr, MyTCPHandler)  
server.serve_forever()  
