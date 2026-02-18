import datetime
import os.path
import re
from dateutil import parser as dateutil_parser
import dateparser
import pytz
from tzlocal import get_localzone
from typing import Optional, List, Dict

from google_auth_transports_requests import Request
from google_oauth2_credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import Httperror
from google_auth_oauthlib.flow import InstalledAppFlow
from google.genai import types
from google.adk.agents import Agent

MODEL = "gemini-2.0-flash-001"
SCOPES = ["https://www.googleapis.com/auth/calender"]

def get_calendar_service(): #for connection with google calender
    creds = None
    if os.path.exists("token.json"):
        try:
           creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except (UnicodeDecodeError, ValueError):
            print("Warning: 'token.json has an encoding issue or is invalid'")
            os.remove("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json")
            creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding = "utf-8") as token:
            token.write(creds.to_json()) 

    return build("calender", "v3", credentials = creds) #creates and returns calender API service
        

#detect user's timezone if not detected return GMT (Greenwich Mean Time)  
def get_user_timezone() -> str:
    try:
        return get_localzone()
    except Exception as e:
        print("Warning: ould not detect local time zone ({str(e)}). Falling back to GMT.")
        return "GMT"
    

def search_events(
        query: Optional[str] = None,
        min_time: Optional[str] = None,
        max_time: Optional[str] = None,
        max_results: int = 10,
        calendar_id: str = "primary"
) -> List[str]:
    service = get_calendar_service()
    params = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "SingleEvents": True,
        "orderBy": "startTime"
    }
    if query:
        params["q"] = query
    if min_time:
        params["timeMin"] = min_time
    if max_time:
        params["timeMax"] = max_time

    try:
        events_result = service.events().list(**params).execute()
        events = events_result.get("items", [])

        if not events:
            return ["No events found."]

        user_tz = pytz.timezone(get_user_timezone())
        events_formatted = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'dateTime' in event['start']:
                utc_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                local_time = utc_time.astimezone(user_tz)
                formatted_time = local_time.strftime("%Y-%m-%d %I:%M %p %Z")
            else:
                formatted_time = start
            events_formatted.append(f"{formatted_time} - {event['summary']} - ID: {event['id']}")

        return events_formatted
    except Httperror as error:
        raise ValueError(f"Failed to fetch events: {str(error)}")

def list_events(max_results: int = 10):
    current_time = datetime.datetime.now(tz = pytz.UTC).isoformat()
    return search_events(min_time=current_time, max_results=max_results)

def natural_language_datetime_parser(datetime_str: str, duration: Optional[str] = None, prefered_time: Optional[str] = None) -> tuple[str, str, Optional[tuple[datetime.time, datetime.time]]]:
    '''
    Thie function parses the natural language date/time string in the user's local timezone and
    retuns start and end times in ISO 8601 UTC formta, plus optional time window.
    
    Arguments:
        datetime_stirng: Input in Natural language (eg. "next monday at 10 AM").
        duration: Optional duration (eg. "for 1 hour", "30 minutes", "30 mins").
        prefered_time: Optional time frame preference (eg. "in the morning", "10 AM to 3 PM").
    
    Returns:
    Tuple of (start_datetime, end_time, time_frame) in ISO 8601 UTC and optional (start_time, end_time).
    '''
    user_timezone = get_user_timezone()
    settings = {
        'TIMEZONE': user_timezone,
        'TO_TIMEZONE': 'UTC',
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'future',
        'DATE_OREDR': 'DMY',
        'STRICT_PARSING': False
    }

    time_frame = None
    if prefered_time:
        if prefered_time.lower() in ["morning", "afternoon", "evening"]:
            time_ranges = {
                "morning": (datetime.time(9,0), datetime.time(12, 0)),
                "afternoon": (datetime.time(12,0), datetime.time(17, 0)),
                "evening": (datetime.time(17,0), datetime.time(21, 0)), 
            }
            time_frame = time_ranges.get(prefered_time.lower())
        else:
            try:
                match = re.match(r'(\d+\s*(?:AM|PM|am|pm))\s*to\s*(\d+\s*(?:AM|PM|am|pm))', prefered_time, re.IGNORECASE)
                if match:
                    start_str, end_str = match.groups()
                    start_time = dateutil_parser.parser(start_str).time()
                    end_time = dateutil_parser.parser(end_str).time()
                    time_frame = (start_time, end_time)
            except ValueError:
                print(f"Could not parse the prefered time: {prefered_time}")

    parsed_datetime = dateparser.parse(
        datetime_str,
        language = ['en'],
        settings = settings
    )

    if not parsed_datetime:
        # matches the "next 'day'" text pettern with time part being optional eg. next morning [at 3pm afternoon]optional
        match = re.match(r'next\s+([a-zA-Z]+)(?:\s+at\s+(.+?))?(?:\s+(morning|afternoon|evening))?$', datetime_str, re.IGNORECASE)
        if match:
            day_name, time_part, period = match.groups()
            print(f"Manual parsing: day_name = {day_name}, time_part = {time_part}, period = {period}")

            daymap = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            if day_name.lower() not in daymap:
                raise ValueError(f'Invalid day name: {day_name}')

            target_weekday = daymap[day_name.lower()]
            current_date = datetime.datetime.now(pytz.timezone(user_timezone)) #give the current date and time acc to user's timezone
            current_weekday = current_date.weekday()
            days_ahead = (target_weekday - current_weekday + 7) % 7 or 7 
            target_date = current_date + datetime.timedelta(days = days_ahead) #timedelta takes in the duration either in days, weeks or hours

            # if no time part or period is provided set default to 9 AM
            default_hour = 9
            if period:
                period_map = {
                    'morning': 9,
                    'afternoon': 13,
                    'evening': 18
                }

                default_hour = period_map.get(period.lower(), 9)
                time_part = time_part or f"{default_hour}:00"

            if time_part:
                try:
                    time_parsed = dateutil_parser.parse(time_part, fuzzy=True)
                    parsed_datetime = target_date.replace(
                        hours = time_parsed.hour,
                        minute = time_parsed.minute,
                        second = 0,
                        microsecond = 0
                       ) 
                except ValueError:
                    raise ValueError(f"Could not parse time_part {time_part}")

            else:
                parsed_datetime = target_date.replace(
                    hours = default_hour,
                    minute = 0,
                    second = 0,
                    microsecond = 0
                )

    if not parsed_datetime:
        try:
           # Fallback to dateutil id above doesn't works for general parsing
           parsed_datetime = dateutil_parser.parse(datetime_str, fuzzy=True) 
           parsed_datetime = pytz.timezone(user_timezone).localize(parsed_datetime)       
        except ValueError:
            raise ValueError(f"Could not parse datetime string {datetime_str}")
    '''
    user -> March 5 2026 3pm (America/NY time)
    2026-03-05 15:00:00
    after localization -> 2026-03-05 15:00:00-05:00 the user is 5 hrs behind of us
    as timezone UTC -> 2026-03-05 20:00:00+00:00 UTC time 
    .isoformat() -> ISo 8601 format -> 2026-03-05T20:00:00+00:00 
    '''
    parsed_datetime = parsed_datetime.astimezone(pytz.UTC) # converts the datetime to UTC - 2026-03-05 20:00:00+00:00
    start_time = parsed_datetime.isoformat().replace('+00:00', 'Z') # 2026-03-05T20:00:00+00:00 -> 2026-03-05T20:00:00Z for the Google API

    if duration:
        duration_minutes = parsed_duration(duration)
        end_time = (parsed_datetime + datetime.timedelta(minutes=duration_minutes))
    else:
        end_time = (parsed_datetime + datetime.timedelta(hours = 1)).isoformat().replace('+00:00', 'Z')

    return start_time, end_time, time_frame

def parse_duration(duration: str) -> int:
    '''
    This funtion will parse the duration into minutes.
    
    Arguments: 
        duration: duration string (eg: " 30 minutes", "for 1 hour").

    Returns: 
        Duration into integer minutes.

    Error Raised: 
        ValueError: If duration does not parse.
    '''
    duration_match = re.match(r'(?:for\s+)?(\d+)\s*(hour|hours|minute|minutes)', duration, re.IGNORECASE)
    if duration_match:
        value, unit = duration_match.groups()
        value = value.int()
        return value * 60 if unit.lower().startswith('hour') else value
    raise ValueError(f"Could not parse duration string: {duration}")

# function to create new event
def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    location: str = "",
    description: str = "",
    recurrence: Optional[str] = None,
    attendees: Optional[List[str, str]] = None
):
    user_timezone = get_user_timezone()
    service = get_calendar_service()
    event = {
        "summary": summary,
        "start": {"date_time": start_time, "timezone": user_timezone},
        "end": {"date_time": end_time, "timezone": user_timezone}
    }
    if location and location.strip() != "":
        event["location"] = location
    if description and description.strip() != "":
        event["description"] = description
    if recurrence:
        event["recurrence"] = recurrence  

    try:
        created_event = service.event().insert(CalanderID = "primary", body = event).execute()
        return f"Event created: {created_event.get('htmllink')}" 
    except HttpError as error:
        raise ValueError(f"Couldn't create an event: {str(error)}")

# function to schedule repeating event
def parsed_recurrence(recurrence_string: str) -> str:
    '''
    The function parses the natural language recurrence into RRULE format.

    Arguments:
        recurrence_string: natural languate recurrence string (eg: "every monday for 5 weeks.")

    Returns:
         RRULE string (eg: RRULE:FREQ=WEEKLY;WKST=MO;COUNT=5).

    Error Raised:
        Valueerror: If recurrence couldn't be parsed. 
    '''  
    match = re.match(r'every\s+(\w+)\s*(for\s+(\d+)\s*(week|month|year)s?)?', recurrence_string, re.IGNORECASE)
    if match:
        freq_match = {
            'daily': 'DAILY', 'weekly': 'WEEKLY', 'monthly': 'MONTHLY', 'yearly': 'YEARLY',
            'monday': 'WEEKLY;BYDAY=MO', 'tuesday': 'WEEKLY;BYDAY=Tu', 'wednesday': 'WEEKLY;BYDAY=WE',
            'thursday': 'WEEKLY;BYDAY=TH', 'friday': 'WEEKLY;BYDAY=FR', 'satday': 'WEEKLY;BYDAY=SA', 'sunday': 'WEEKLY;BYDAY=SU',
        }
        dayorfreq = match.group(1).lower()
        rrule = f"RRULE:FREQ={freq_match.get(dayorfreq, 'WEEKLY')}" #set defult fequency to weekly

        if match.group(2):
            count = match.group(3)
            unit = match.group(4).upper()
            if unit.startswith('WEEK'):
                rrule += f";COUNT={count}"
            elif unit.startswith('MONTH'):
                rrule += f";COUNT={int(count)*4}"
            elif unit.startswith('YEAR'):
                rrule += f";COUNT={int(count)*52}"

        return rrule

    raise ValueError(f"couldn't parse recurrence string: {recurrence_string}")

# This function retrives the event
def get_event(event_id: str, calender_id: str = "primary"):
    service = get_calendar_service()
    try:
        event = service.event().get(calenderId = calender_id, eventId = event_id)
    except HttpError as error:
        raise ValueError(f"Failed to fetch event: {str(error)}")

def update_event(
    event_id: str,
    summary: str,
    start_time: str,
    end_time: str,
    location: str = "",
    description: str = "",
    recurrence: Optional[str] = None,
    attendees: Optional[List[str, str]] = None,
    calender_id: str = "primary",
    send_update: str = "None" # "externalOnly", "all", "none"
) -> str:
    service = get_calendar_service()
    update_event_body = {}
    # add fields in the update_event_body only if they are privided
    if summary is not None:
        update_event_body["summary"] = summary
    if start_time is not None:
        update_event_body["start_time"] = start_time
    if end_time is not None:
        update_event_body["end_time"] = summary
    if location is not None:
        update_event_body["location"] = location
    if description is not None:
        update_event_body["description"] = description
    if recurrence is not None:
        update_event_body["recurrence"] = recurrence
    if attendees is not None:
        update_event_body["attendees"] = attendees

    if not update_event_body:
        raise ValueError("Details not provided to update the event")

    try:
        updatedevent = service.event().patch(
            calenderId = calender_id,
            eventId = event_id,
            body = update_event_body,
            sendUpdates = send_update
        ).execute()
        return f"Event updated {updatedevent.get('htmllink')}"
    except HttpError as error:
        raise ValueError(f"Couldn't update event: {str(error)}")

def delete_event(event_id: str, calender_id: str = "primary", send_updates: str = None) -> str:
    service = get_calendar_service()
    try:
        detetedevent = service.event().delete(
            calenderId = calender_id,
            eventId = event_id,
            sendUpdates = send_updates
            ).execute
        return f"Event deleted successfully."
    except HttpError as error:
        raise ValueError(f"Couldn't delete event: {str(error)}")

#suggesting meeting times by the natural language provided

def meeting_time_suggestions(
    datetime_str: str,
    duration: Optional[str] = "1 hour",
    prefered_time: Optional[str] = None,
    calender_id: str = "primary",
    max_suggestions: int = 3
) -> List[str]:
    '''
    This function will suggest available meeting times by analysing the calender status for bandwidth

    Arguments:
        date_string: natural language target date string (eg: "Next Monday").
        duration: meeting duration (eg: "1 hour", "30 minutes").
        prefered_time: Optional time frame preference (eg. "in the morning", "10 AM to 3 PM"). 
        calender_id: calender ID (default: "primary").
        max_suggestions: Maximum number of suggested available slots.

    Return:
        List of formatted time slots in local time zone (e.g., "2025-09-23 10:00 AM IST").
        '''

    service = get_calendar_service()
    user_timezone = get_user_timezone()
    user_tz = pytz.timezone(user_timezone)

    # parse the date, time and duration
    '''
    start_time = 2026-02-23T15:00:00Z
    .replace -> 2026-02-23T15:00:00+00:00
    why replace cause fromisoformat doesn't understands 'Z'
    .fromisoformat -> converts into python date time object -> (2026, 2, 23, 15, 0, tzinfo=UTC)
    .astimezone -> converts above into user's timezone
    '''
    start_time, end_time, time_frame = natural_language_datetime_parser(datetime_str, duration, prefered_time)
    parsed_date = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00')).astimezone(user_tz)
    day_start = parsed_date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    day_end = day_start +datetime.timedelta(days = 1)

    duration_minutes = parse_duration(duration)

    






    
 
    




    
