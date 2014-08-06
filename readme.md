===========================
Usage:
Run by root user.

python reset.py
python monitor.py

reset.py==> reset file for monitor.py 

===========================
config文件配置

{site1}===>
这一类的为配置名称，随意填写在{}里即可

host格式===>
icmp，http:   （IP或者域名）
udp,tcp:  （IP或者域名#端口） 

last====>
持续时间：定为整数

times===>
循环次数：定为整数


protocol====>
协议：现有tcp,udp,http,icmp
===============================

使用方法：
root权限, not just "sudo" to change，python2.7环境
直接运行monitor.py即可

===============================
Update time: 07/29
在运行monitor.py后，需要运行reset.py,使用心跳包交互，以便在monitor.py挂掉后短时间内自动重启
主程序在运行结束会自动断掉单线程的心跳轮询，并向客户端发送退出命令。

PS:reset.py实现的不是断点续航，而是重新开始任务

===============================
Update time: 07/30

Modify the structure of the script,solve some bugs.

monitor.py==>socket client
reset.py==>socket server

Add extra threadline to listen on the port. 
Solve the problem of "port in use".
===============================
update time: 08/05

monitor.py==>monitor-heart.py

取消心跳包（reset.py）检测脚本存活
增加服务器端接收扫描结果文件：server.py,附加口令认证
使用监控前对原扫描结果进行预获取




 

















