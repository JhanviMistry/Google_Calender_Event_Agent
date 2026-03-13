AI Google Calendar Agent (Built with Google ADK)

An AI-powered scheduling assistant that manages Google Calendar using natural language.
Built with Google Agent Development Kit (ADK), the agent can create, update, delete, search events, and suggest available meeting times while handling recurring meetings, attendees, and time zones automatically.

Features

Create calendar events using natural language

Update existing events

Delete events

Search and list calendar events

Suggest available meeting times based on calendar availability

Support recurring meetings (RRULE)

Add and manage event attendees

Parse natural language date/time

Handle user time zones automatically

Example Commands

The agent can understand requests like:

Schedule a meeting tomorrow at 3pm for 1 hour
Create a weekly standup every Monday at 10am
Move my meeting with Alex to Friday at 4pm
Delete my meeting tomorrow
Find free time for a 30-minute meeting this afternoon
Add john@gmail.com to the team meeting
Tech Stack

Python

Google Agent Development Kit (ADK)

Google Calendar API

OAuth 2.0 Authentication

dateparser

python-dateutil

pytz / tzlocal

Agent Architecture

The agent uses a tool-based architecture provided by Google ADK.

User Request
      │
      ▼
Google ADK Agent
      │
      ▼
Tool Selection
      │
      ▼
Calendar Tools
      │
      ▼
Google Calendar API

The LLM decides which tool to call based on the user’s request.

Available Agent Tools
Tool	Purpose
create_event	Create a new calendar event
update_event	Update event details
delete_event	Delete a calendar event
get_event	Retrieve event information
search_events	Search events in the calendar
list_events	List upcoming events
parse_natural_language_datetime	Convert human text to datetime
parse_recurrence	Convert recurrence text to RRULE
suggest_meeting_times	Suggest free time slots
Project Structure
google-calendar-agent/
│
├── agent.py
├── calendar_tools.py
├── datetime_parser.py
├── recurrence_parser.py
├── main.py
├── requirements.txt
└── README.md
Setup
1 Install Dependencies
pip install -r requirements.txt

Example requirements.txt:

google-api-python-client
google-auth
google-auth-oauthlib
python-dateutil
dateparser
pytz
tzlocal
2 Create Google API Credentials

Open Google Cloud Console

Create a new project

Enable Google Calendar API

Create OAuth Client Credentials

Download credentials.json

Place it in the project root

3 Run the Agent

Run the ADK agent locally:

adk run

or run your script:

python main.py

On first run, Google will ask you to authorize access to your calendar.

A token.json file will be generated to store authentication tokens.

Example Agent Workflow

User request:

Schedule a meeting tomorrow at 4pm for 1 hour with alex@gmail.com

Agent reasoning flow:

1. Parse natural language datetime
2. Parse attendees
3. Call create_event tool
4. Create event via Google Calendar API
Future Improvements

Multi-calendar support

Slack / Teams integration

Voice assistant integration

Multi-agent scheduling

Smart conflict resolution

Author

Jhanvi Mistry
