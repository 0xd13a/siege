FROM ubuntu:22.04
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive TZ="America/New_York" apt-get -y install tzdata
RUN apt install -y php
WORKDIR /
COPY styles.css .
COPY index.php .
COPY login.php .
COPY portal.php .
COPY lib.php .
COPY reactor.jpg .
COPY sw-users.csv .
COPY station.png .
CMD ["php", "-S", "0.0.0.0:10003", "-t", "."]
