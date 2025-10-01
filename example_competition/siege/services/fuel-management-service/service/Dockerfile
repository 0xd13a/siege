FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip
RUN pip3 install flask pycryptodome PyJWT pyopenssl
WORKDIR /
COPY fuel_management_service.py .
COPY fms-users.txt .
COPY build-db.py .
COPY static ./static
COPY login_template.html .
COPY status_template.html .
RUN python3 ./build-db.py
CMD ["python3", "./fuel_management_service.py"]
