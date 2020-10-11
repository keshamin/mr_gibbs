Python pre-requisites:
```shell script
sudo apt-get insatll python3
sudo apt-get install python3-pip
sudo pip3 install pyTelegramBotAPI
sudo pip3 install humanize
rm db.shelve (if there is + /start in bot to create it again)
```

Tranmission pre-requisites:
```shell script
sudo add-apt-repository ppa:transmissionbt/ppa
sudo apt-get update
sudo apt-get install transmission-cli transmission-common transmission-daemon
sudo nano /etc/transmission-daemon/settings.json (with transmission-daemon stopped)
```
"download-dir": "/home/kesha/Downloads",
"incomplete-dir": "/home/kesha/Downloads",
"rpc-authentication-required": false,
"rpc-whitelist": "127.0.0.1,192.168.*.*",
```shell script
sudo addgroup myuser debian-transmission
sudo addgroup debian-transmission myuser
```

Plex pre-requisites:
- https://www.plex.tv/media-server-downloads/
- login to your accaunt
- set libraries in web-client
- enable auto-scan in server settings
- set running as user who holds content directories:
- `sudo systemctl stop plexmediaserver`
- PLEX_MEDIA_SERVER_USER=myuser
- `sudo addgroup plex myuser`
- `sudo addgroup myuser plex`
- start plex

