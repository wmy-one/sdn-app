#/usr/bin/env/python
import socket
host=''
port=51432
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((host,port))
for time in range (0,22):
	s.listen(1)
	print "listening port 51432"
	conn,addr=s.accept()
	print 'connected by ',addr
	data=conn.recv(1024)
	print data
s.close()
