# Monitor Challenge

## Description

Alarm monitor is written in C. It simulates an alarm monitoring panel of a nuclear plant.

3 types of users are defined: operators, administrators, and maintenance technicians. All users should be able to see current alarm state. Administrators should trigger and clear alarms. Maintenance technicians can disarm all alarms.

## Vulnerabilities

There are 3 vulnerabilties defined:

- Password check has a buffer overflow that when password is 21 characters long, and causes user with an incorrect password to log in
- Alarm change is done without enforcing proper user type
- Selecting a negative menu item allows attacker to disarm all alarms

## Setup

### On the build machine

* Pack up the files for the container 

```
tar zcf security-monitor.tar.gz Dockerfile compose.yaml security-monitor.c ssl.pem sm-users.csv notes.txt
```

* Copy the package to the host machine:

```
scp ./security-monitor.tar.gz monitor:~
```

### On the host machine

* Install Docker:

```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose
```

* Unpack the files

```
tar xzf security-monitor.tar.gz
```

* Run the container

```
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run
