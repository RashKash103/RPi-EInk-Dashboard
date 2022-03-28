import os
import pause
import pytz
import logging
from PIL import Image
from datetime import datetime, timedelta
from dotenv import load_dotenv
from display import get_screen, DisplayState
from typing import List, Tuple

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

try:
    from waveshare_epd import epd7in5_V2
except OSError as e:
    class epd7in5_V2:
        def EPD():
            raise IOError("Device not found")
    logger.error(e)


load_dotenv()
timezone = pytz.timezone(os.getenv("TIMEZONE"))
off_hours = [int(hour_str) for hour_str in os.getenv("DOWN_HOURS").split(",")]

def start_updating(epd: epd7in5_V2.EPD):
    state = None

    while True:
        state, update_times = update_once(epd, state)
        update_times.sort()
        update_times = list(filter(lambda time: time > timezone.localize(datetime.now()), update_times))

        current_hour = datetime.now().hour
        if current_hour in off_hours:
            logger.info("Detected off hours, clearing and waiting.")
            try:
                epd.init()
                epd.Clear()
                epd.sleep()
            except IOError as e:
                logger.error(e)
            sleep_until = current_hour
            while (sleep_until % 24) not in off_hours:
                sleep_until = sleep_until + 1
            update_times = [timezone.localize(datetime.now()) + timedelta(hours=sleep_until - current_hour),]

        logger.info(f"Waiting until {update_times[0]}")
        pause.until(update_times[0])


def update_once(epd: epd7in5_V2.EPD, prev_state: DisplayState) -> Tuple[DisplayState, List[datetime]]:
    logger.info("Attempting to update state.")
    update_times = [timezone.localize(datetime.now()) + timedelta(minutes=int(os.getenv("UPDATE_INTERVAL"))),]
    state, img = get_screen()

    if state and state.events_graphed:
        for event in state.events_graphed:
            update_times.append(event.start + timedelta(seconds=15))
            update_times.append(event.end + timedelta(seconds=15))
    
    if not prev_state or state != prev_state:
        logger.info("New state differs from previous, updating display.")
        update_display(epd, img)
    return (state, update_times)
    

def update_display(epd: epd7in5_V2.EPD, img: Image.Image):
    logger.info("Updating display now.")
    if epd:
        epd.init()
        epd.display(epd.getbuffer(img))
        epd.sleep()
    else:
        img.save("output.png", "PNG")

def init_display() -> epd7in5_V2.EPD:
    try:
        logger.info("Initializing EPD")
        epd = epd7in5_V2.EPD()
        epd.init()
        epd.Clear()
        logger.info("Successfully initialized EPD")
    except IOError as e:
        logger.error(e)
        return None

if __name__ == "__main__":
    logger.info("Starting updater...")

    epd = init_display()
    try:
        start_updating(epd)
    except KeyboardInterrupt:
        logger.info("Ctrl+C detected, terminating.")
        if epd:
            epd7in5_V2.epdconfig.module_exit()
