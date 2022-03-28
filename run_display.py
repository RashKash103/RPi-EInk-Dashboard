import os
import pause
import pytz
from PIL import Image
from datetime import datetime, timedelta
from dotenv import load_dotenv
from display import get_screen, DisplayState
from typing import List, Tuple
from waveshare_epd import epd7in5_V2

load_dotenv()
timezone = pytz.timezone(os.getenv("TIMEZONE"))
off_hours = [int(hour_str) for hour_str in os.env("DOWN_HOURS").split(",")]

def start_updating(epd: epd7in5_V2.EPD):
    state = None

    while True:
        state, update_times = update_once(epd, state)
        update_times.sort()
        update_times = list(filter(lambda time: time > timezone.localize(datetime.now()), update_times))

        current_hour = datetime.now().hour
        if current_hour in off_hours:
            epd.init()
            epd.Clear()
            epd.sleep()
            sleep_until = current_hour
            while (sleep_until % 24) not in off_hours:
                sleep_until = sleep_until + 1
            update_times = [timezone.localize(datetime.now()) + timedelta(hours=sleep_until - current_hour),]

        if (len(update_times) > 1) and ((update_times[1] - update_times[0]) < timedelta(minutes=2)):
            update_times.pop(0)

        pause.until(update_times[0])


def update_once(epd: epd7in5_V2.EPD, prev_state: DisplayState) -> Tuple[DisplayState, List[datetime]]:
    update_times = [timezone.localize(datetime.now()) + timedelta(minutes=int(os.getenv("UPDATE_INTERVAL"))),]
    state, img = get_screen()

    if state and state.events_graphed:
        for event in state.events_graphed:
            update_times.append(event.start + timedelta(seconds=15))
            update_times.append(event.end + timedelta(seconds=15))
    
    if not prev_state or state != prev_state:
        update_display(epd, img)
    return (state, update_times)
    

def update_display(epd: epd7in5_V2.EPD, img: Image.Image):
    img.save("output.png", "PNG")
    if epd:
        epd.init()
        epd.display(epd.getbuffer(img))
        epd.sleep()

def init_display() -> epd7in5_V2.EPD:
    try:
        epd = epd7in5_V2.EPD()
        epd.init()
        epd.Clear()
    except IOError as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    start_updating()