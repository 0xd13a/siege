# Fuel Management Service Challenge

## Description

This is a vulnerable application written in Python that simulates operation of a fuel management application. 

User logs in with valid credentials and is managing insertion and removal of reactor fuel "bundles".

Users can be of 2 types: Monitors and Management Technicians. Monitors are only 
allowed to see the current state of the fuel in the reactor, while Management Technicians can 
also order fuel loading and unloading.

Fuel in Can-doo reactor is stored in the form of 'bundles' that are put into 'channels'. Not all channels need to be filled.
Used bundles are candidates for removal.

Fuel management has to follow these rules:

- You cannot fill more than 70% of the slots, or the reactor will become unstable
- You cannot fill less than 20% of the slots, or the reactor will lack necessary fuel and will have to undergo an emergency shutdown
- You cannot remove more bundles than there are candidates for removal, or good fuel will be wasted

The current state of reactor (how many bundles are inserted and how many are "spent" and ready for removal) is set through a simulated call from the "fuel sensor" (performed by attacker application).

## Vulnerabilities

There are 3 vulnerabilities in this application:

- Password checking is not performed, any user with a non-empty password can log in
- User roles are not enforced - monitors are allowed to manage fuel bundles
- No rule management rules are implemented. Players have to add them to reject requests that specify incorrect bundle counts

## Setup

### On the build machine

* Pack up the files for the container 

```
tar zcf fuel-management-service.tar.gz Dockerfile compose.yaml fuel_management_service.py fms-users.db static login_template.html status_template.html
```

* Copy the package to the host machine:

```
scp ./fuel-management-service.tar.gz fuel:~
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
tar xzf fuel-management-service.tar.gz
```

* Run the container

```
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run