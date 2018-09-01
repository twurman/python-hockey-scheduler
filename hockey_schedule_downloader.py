# TO RUN THIS SCRIPT
# for the record, I'm using python 3.6. some mods would have to be made to backport this to 2.7
# in the directory that the script is in, you will need to first run
# pip install BeautifulSoup4
# pip install Requests
# pip install --upgrade google-api-python-client
# pip install dateparser
# pip install oauth2client 
# 
# then follow the steps on https://developers.google.com/google-apps/calendar/quickstart/python
# to create an oath key; save it to client_secret.json
# 
# the first time you run this, it will attempt to authenticate in your browser window

from bs4 import BeautifulSoup
import requests
import httplib2
import os
import sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
from datetime import timedelta
import pytz
import dateparser

try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Python Hockey Scheduler'

# copied from google documentation
def get_credentials():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir,
								   'stashed_credentials.json')

	store = Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

def parse_text(text):
	lines = text.split('\n')
	if len(lines) != 4:
		return {}
	#TODO: fix daylight savings time
	game = {
		'home': lines[0],
		'away': lines[1],
		# parse the date and time from line 3, which is mashed together, but should always be 11 characters ex. Sun, May 07 or Sun, Apr 30
		'startTime': dateparser.parse(lines[2][0:11] + ' ' + lines[2][11:] + ' CDT'), # watch out for that daylight savings time
		'endTime': dateparser.parse(lines[2][0:11] + ' ' + lines[2][11:] + ' CDT') + timedelta(hours=1), # watch out for that daylight savings time
		'rink': lines[3].replace('JIH West', 'Johnny\'s IceHouse - West').replace('JIH East', 'Johnny\'s Ice House - East')
	}
	return game

def get_games(link):
	page = requests.get(link)
	soup = BeautifulSoup(page.content, 'html.parser')
	rows = soup.find_all('tr')
	games = []
	for row in rows[1:]:
		text = row.get_text().rstrip()
		if text.endswith('final') or text.endswith('forfeit'):
			pass
		else:
			game = parse_text(text)
			# added error handling for empty games
			if game:
				games.append(game)
	return games

def add_games_to_calendar(service, games, calendarId):
	for game in games:
		# check if game already exists
		startCheck = game['startTime'].replace(hour=0, minute=0, second=0, microsecond=0)
		endCheck = startCheck + timedelta(days=1)
		eventsResult = service.events().list(
			calendarId=calendarId, timeMin=startCheck.isoformat(), timeMax=endCheck.isoformat(), maxResults=5, singleEvents=True, orderBy='startTime').execute()
		events = eventsResult.get('items', [])
		
		found = False
		updated = False
		for event in events:
			if event['summary'] == game['home'] + ' vs ' + game['away'] or event['summary'] == game['away'] + ' vs ' + game['home']:
				print(event['summary'])
				if event['location'] != game['rink'] or event['start']['dateTime'] != game['startTime'].isoformat():
					print('Updating game time and location')
					oldId = event['id']
					event = {
						'summary': game['home'] + ' vs ' + game['away'],
						'location': game['rink'],
						'start': {
							'dateTime': game['startTime'].isoformat(),
							'timeZone': 'America/Chicago'
						},
						'end': {
							'dateTime': (game['endTime']).isoformat(),
							'timeZone': 'America/Chicago'
						}
					}
					event = service.events().update(calendarId=calendarId, eventId=oldId, body=event).execute()
					print(event.get('htmlLink'))
					updated = True
				
				found = True
				break
		if not events or not found:
			print('Creating new game event ' + game['home'] + ' vs ' + game['away'])
			event = {
				'summary': game['home'] + ' vs ' + game['away'],
				'location': game['rink'],
				'start': {
					'dateTime': game['startTime'].isoformat(),
					'timeZone': 'America/Chicago'
				},
				'end': {
					'dateTime': (game['endTime']).isoformat(),
					'timeZone': 'America/Chicago'
				}
			}
			event = service.events().insert(calendarId=calendarId, body=event).execute()
			print(event.get('htmlLink'))
		elif not updated:
			print('Game found, skipping creation')



def main():
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	# Wet Seals A Team - calendarId n7gqu1nsla6i8r9aiegh650pl8@group.calendar.google.com
	games = get_games('http://stats.pointstreak.com/players/players-team-schedule.html?teamid=624336&seasonid=18553')
	add_games_to_calendar(service, games, 'n7gqu1nsla6i8r9aiegh650pl8@group.calendar.google.com')

	# Pepper Grinders - calendarId qfrau8vql8ukt0cfdjnl11qq0s@group.calendar.google.com
	games = get_games('http://stats.pointstreak.com/players/players-team-schedule.html?teamid=624322&seasonid=18553')
	add_games_to_calendar(service, games, 'qfrau8vql8ukt0cfdjnl11qq0s@group.calendar.google.com') 
	
	# Wet Seals B2 Team - calendarId 9njrsmfevqjk31qnujhumd7j3s@group.calendar.google.com
	games = get_games('http://stats.pointstreak.com/players/players-team-schedule.html?teamid=624356&seasonid=18553')
	add_games_to_calendar(service, games, '9njrsmfevqjk31qnujhumd7j3s@group.calendar.google.com') 
	
	


if __name__ == '__main__':
	main()














