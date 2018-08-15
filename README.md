# skippy
Telegram bot to interface with Restya.

Step 1) Create a Telegram bot to get a bot token https://core.telegram.org/bots

Step 2) Install requirements (tested on Ubuntu server 16.04)
```bash
apt install python-pip screen
pip install python-telegram-bot --upgrade
pip install psycopg2-binary
```
Step 3) Become root if not already and change to /root
```bash
sudo -i
cd /root
```
Step 4) Download Bot Files
```bash
git clone https://github.com/kno3it/skippy
```
Step 5) Make script executable
```bash
chmod 755 skippy/skippy.py
```
Step 6) Make the script run in a screen session on server startup
```bash
# open file for editing
nano /etc/rc.local

# add following line to run skippy on startup.
# be sure to write this line above the exit 0
screen -dmS restyaBot /root/skippy/skippy.py
```
Step 7) Configure script to use your database and Telegram bot
```bash
# open file for editing
nano skippy/skippy.py

# Make sure to add the bot to your team group chat
host = "localhost"
database = "restyaboard"
user = "restya"
password = ""
telegramToken = ""
```
Note:
If the bot is running on a different server than the restya database then make sure
the database allows remote connections. Otherwise you will get database unreachable
error messages. More info can be found here: 
https://blog.bigbinary.com/2016/01/23/configure-postgresql-to-allow-remote-connection.html
