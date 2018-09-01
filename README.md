# python-hockey-scheduler
Small python script that scrapes pointstreak for schedules and uploads them to google calendar

TO RUN THIS SCRIPT:

in the directory that the script is in, you will need to first run
* pip install BeautifulSoup4
* pip install Requests
* pip install --upgrade google-api-python-client
* pip install dateparser
* pip install oauth2client 

then follow the steps on https://developers.google.com/google-apps/calendar/quickstart/python
to create an oath key; save it to client_secret.json

the first time you run this, it will attempt to authenticate in your browser window

for the record, I'm using python 3.6. some mods would have to be made to backport this to 2.7
