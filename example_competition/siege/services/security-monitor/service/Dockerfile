FROM ubuntu:22.04
WORKDIR /
COPY security-monitor.c .
COPY ssl.pem .
COPY sm-users.csv .
COPY notes.txt .
RUN dpkg --add-architecture i386
RUN apt update
RUN apt install -y socat
RUN apt install -y libc6:i386
RUN apt install -y gcc gcc-multilib
RUN gcc -O0 -m32 security-monitor.c -o security-monitor
EXPOSE 10002
CMD ["socat", "openssl-listen:10002,reuseaddr,cert=ssl.pem,verify=0,fork", "SYSTEM:\"./security-monitor ; sleep 3\",pty,stderr"]
