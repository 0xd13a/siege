# Station Website Challenge

## Description

This is a vulnerable station intranet application written in PHP. The functionality is limited - you can sign in and read and post news items on the front page.

There are 2 types of users - Readers and Writers. Writers can post news to the newsfeed.

## Vulnerabilities

There are 3 vulnerabilities in this application:

- Password checking is done by comparing hashes in a vulnerable way, which can be exploited by "magic hashes" (hashes that start with "0e" and are all numbers). This is possible due to the type juggling PHP does: essentially in PHP "0" == "0e23874928734918273984729837474" 
- User role is serialized by PHP into an unguarded cookie that can then be manipulated by attacker for privilege escalation
- News posting allows posting of HTML, and scripts can be smuggled in.

## Setup

### On the build machine

* Pack up the files for the container 

```
tar zcf station-website.tar.gz Dockerfile compose.yaml styles.css index.php login.php portal.php lib.php reactor.jpg sw-users.csv station.png
```

* Copy the package to the host machine:

```
scp ./station-website.tar.gz website:~
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
tar xzf station-website.tar.gz
```

* Run the container

```
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run