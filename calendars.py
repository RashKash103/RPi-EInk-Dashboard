import os
from pytz import timezone, UTC
import requests
from dotenv import load_dotenv
from icalendar import Calendar, Event
import datetime
import dateutil.rrule as rrule
from typing import List

load_dotenv()

class SavedEvent:
    is_all_day = False
    event_name = None
    dt_start = None
    dt_end = None
    
    def __init__(self, is_all_day: bool, event_name: Event, dt_start: datetime.datetime, dt_end: datetime.datetime):
        self.is_all_day = is_all_day
        self.event_name = event_name
        self.dt_start = dt_start
        self.dt_end = dt_end
    
    def __eq__(self, other):
        return self.event_name == other.event_name

def get_events(cal: Calendar, date: datetime.date) -> List[SavedEvent]:
    global tz
    tz = timezone(os.getenv('TIMEZONE'))

    all_events = cal.walk('VEVENT')
    return _extract_events(all_events, date)

def get_calendar() -> str:
    req = requests.get(os.getenv("ICS_CALENDARS"))
    if req.status_code != 200:
        print("Error")
        exit(0)
    return Calendar.from_ical(req.text)
    # with open('calendar.ics', mode='r') as calendar:
    #     return Calendar.from_ical(calendar.read())

def _extract_events(events: List[Event], date: datetime.date) -> List[SavedEvent]:
    days_events = []

    for event in events:
        event_start = None
        event_end = None
        is_all_day = False

        if event.has_key('rrule'):
            recurrence = rrule.rrulestr(event['rrule'].to_ical().decode(), dtstart=event['dtstart'].dt.astimezone(tz))
            recurring_event_today = recurrence.after(UTC.localize(datetime.datetime.combine(date, datetime.datetime.min.time())))

            if recurring_event_today and recurring_event_today.date() == date:
                event_start = tz.localize(recurring_event_today.replace(tzinfo=None))
                event_end = tz.localize((event_start + (event['dtend'].dt - event['dtstart'].dt)).replace(tzinfo=None))
        elif event.has_key('dtstart'):
            start = event['dtstart'].dt
            end = None
            if event.has_key('dtend'):
                end = event['dtend'].dt
            
            if not isinstance(start, datetime.datetime):
                is_all_day = True

            start_date = start if is_all_day else start.date()
            if start_date == date:
                event_start = start if is_all_day else start.astimezone(tz)
                event_end = end if is_all_day or end == None else end.astimezone(tz)

        if event_start:
            if not isinstance(event_start, datetime.datetime):
                event_start = tz.localize(datetime.datetime.combine(event_start, datetime.datetime.min.time()))
            if not isinstance(event_end, datetime.datetime):
                event_end = tz.localize(datetime.datetime.combine(event_end, datetime.time(23, 59, 59)))

            event_to_save = SavedEvent(is_all_day, event['summary'], event_start, event_end)
            if event_to_save not in days_events:
                days_events.append(event_to_save)
    
    days_events.sort(key=lambda x: x.dt_start)
    return days_events

if __name__ == "__main__":
    todays_events = get_events(get_calendar(), datetime.date(2022, 3, 28))

    for event in todays_events:
        # print(f"{event.dt_start.strftime('%b %-d %-I:%M %p')} - {event.dt_end.strftime('%b %-d %-I:%M %p')}: {event.event_name}")
        print(f"{event.dt_start} - {event.dt_end}: {event.event_name}")
