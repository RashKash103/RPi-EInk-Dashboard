import os
import pytz
from datetime import datetime, timedelta, tzinfo
from PIL import Image, ImageDraw, ImageOps
from fonts import Style, get_font
from weather import get_json
from calendars import get_calendar, get_events, SavedEvent
from weather_icons import get_moon_phase_name, get_weather_icon_for_code, get_weather_icon_for_name, get_weather_icon_for_moon
from dotenv import load_dotenv
from typing import Tuple
from pytz import timezone

class State:
    def __str__(self):
        return (', '.join(f"{name}: {value}" for name, value in vars(self).items()))
    def __repr__(self) -> str:
        return self.__str__()
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, self.__class__):
            return self.__dict__ == __o.__dict__
        else:
            return False
    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

class DisplayState(State):
    pass

class EventState(State):
    pass


load_dotenv()

def draw_day(image: Image.Image, state: DisplayState):
    date_str = datetime.now().strftime("%A, %b %-d")

    draw = ImageDraw.Draw(image)
    draw.text((10, 0), date_str, fill=0, align="left", font=get_font(Style.BOLD, 36))
    state.date_str = date_str


def draw_weather(image: Image.Image, state: DisplayState):
    weather_data = get_json()
    draw = ImageDraw.Draw(image)

    timezone = pytz.timezone(os.getenv("TIMEZONE"))
    sunrise = datetime.fromtimestamp(weather_data["current"]["sunrise"], tz=pytz.utc).astimezone(timezone)
    sunset = datetime.fromtimestamp(weather_data["current"]["sunset"], tz=pytz.utc).astimezone(timezone)
    is_day = sunrise < datetime.utcnow().astimezone(timezone) < sunset

    # Current weather icon
    with Image.open(get_weather_icon_for_code(weather_data["current"]["weather"][0]["id"], is_day)) as weather_icon:
        weather_icon.thumbnail((150, 150), Image.NEAREST)
        image.paste(weather_icon, (10, 45), weather_icon)
    state.weather_icon_name = weather_data["current"]["weather"][0]["id"]


    # Current feels like temp
    feels_like = f"{str(round(weather_data['current']['feels_like']))}°"
    draw.text((170, 70), feels_like, fill=0, font=get_font(Style.BOLD, 58))
    state.feels_like_temp = round(weather_data['current']['feels_like'])


    # High/low temperatures
    dir_up_icon = Image.open(get_weather_icon_for_name("direction-up"))
    dir_up_icon.thumbnail((60, 60))
    dir_dn_icon = ImageOps.flip(dir_up_icon)
    image.paste(dir_up_icon, (260, 55), dir_up_icon)
    image.paste(dir_dn_icon, (260, 110), dir_dn_icon)

    max_temp = f"{str(round(weather_data['daily'][0]['temp']['max']))}°"
    min_temp = f"{str(round(weather_data['daily'][0]['temp']['min']))}°"
    draw.text((315, 60), max_temp, fill=0, font=get_font(Style.BOLD, 30))
    draw.text((315, 120), min_temp, fill=0, font=get_font(Style.BOLD, 30))
    state.high_temp = round(weather_data['daily'][0]['temp']['max'])
    state.low_temp = round(weather_data['daily'][0]['temp']['min'])


    # Sunrise/sunset times
    sunset_icon = Image.open(get_weather_icon_for_name("sunset"))
    sunrise_icon = Image.open(get_weather_icon_for_name("sunrise"))
    sunset_icon.thumbnail((60, 60), Image.NEAREST)
    sunrise_icon.thumbnail((60, 60), Image.NEAREST)
    image.paste(sunrise_icon, (380, 55), sunrise_icon)
    image.paste(sunset_icon, (380, 110), sunset_icon)

    sunrise_time = sunrise.strftime("%-I:%M%p").lower()
    sunset_time = sunset.strftime("%-I:%M%p").lower()
    draw.text((445, 60), sunrise_time, fill=0, font=get_font(Style.BOLD, 30))
    draw.text((445, 120), sunset_time, fill=0, font=get_font(Style.BOLD, 30))
    state.sunrise_time = sunrise_time
    state.sunset_time = sunset_time


    # Moon phase
    moon_phase_icon = Image.open(get_weather_icon_for_moon(weather_data["daily"][0]["moon_phase"]))
    moon_phase_icon.thumbnail((100, 100), Image.NEAREST)
    image.paste(moon_phase_icon, (700, 0), moon_phase_icon)
    state.moon_phase_name = get_moon_phase_name(weather_data["daily"][0]["moon_phase"])


    # Percentage of precipitation
    raindrops_icon = Image.open(get_weather_icon_for_name("raindrops"))
    raindrops_icon.thumbnail((90, 90), Image.NEAREST)
    image.paste(raindrops_icon, (170, 165), raindrops_icon)

    precip_percent = f"{round(weather_data['daily'][0]['pop'] * 100)}"
    (precip_length, precip_height) = draw.textsize(precip_percent, font=get_font(Style.BOLD, 30))
    draw.text((240, 185), precip_percent, fill=0, font=get_font(Style.BOLD, 30))
    draw.text((242 + precip_length, 186 + precip_height), "%", fill=0, font=get_font(Style.BOLD, 20), anchor="lb")
    state.precip_percent = precip_percent


    # Humidity
    humidity_icon = Image.open(get_weather_icon_for_name("raindrop"))
    humidity_icon.thumbnail((60, 60), Image.NEAREST)
    image.paste(humidity_icon, (320, 178), humidity_icon)

    humidity_percent = f"{round(weather_data['current']['humidity'])}"
    (humidity_length, humidity_height) = draw.textsize(humidity_percent, font=get_font(Style.BOLD, 30))
    draw.text((370, 185), humidity_percent, fill=0, font=get_font(Style.BOLD, 30))
    draw.text((372 + humidity_length, 186 + humidity_height), "%", fill=0, font=get_font(Style.BOLD, 20), anchor="lb")
    state.humidity_percent = humidity_percent


    # Wind speed/direction
    wind_dir_icon = Image.open(get_weather_icon_for_name("wind-deg"))
    wind_dir_icon.thumbnail((60, 60), Image.NEAREST)
    wind_dir_icon = wind_dir_icon.rotate(-1 * weather_data["current"]["wind_deg"], Image.NEAREST)
    image.paste(wind_dir_icon, (580, 55), wind_dir_icon)
    state.wind_dir = round(weather_data["current"]["wind_deg"] / 4) * 4

    wind_speed = weather_data["current"]["wind_speed"]
    if wind_speed < 1: beaufort_speed = 0
    elif wind_speed < 4: beaufort_speed = 1
    elif wind_speed < 8: beaufort_speed = 2
    elif wind_speed < 13: beaufort_speed = 3
    elif wind_speed < 19: beaufort_speed = 4
    elif wind_speed < 25: beaufort_speed = 5
    elif wind_speed < 32: beaufort_speed = 6
    elif wind_speed < 39: beaufort_speed = 7
    elif wind_speed < 47: beaufort_speed = 8
    elif wind_speed < 55: beaufort_speed = 9
    elif wind_speed < 64: beaufort_speed = 10
    elif wind_speed < 73: beaufort_speed = 11
    else: beaufort_speed = 12
    wind_speed_icon = Image.open(get_weather_icon_for_name(f"wind-beaufort-{beaufort_speed}"))
    wind_speed_icon.thumbnail((90, 90), Image.NEAREST)
    image.paste(wind_speed_icon, (580, 90), wind_speed_icon)
    state.beaufort_speed = beaufort_speed
    
def draw_calendar(image: Image.Image, state: DisplayState):
    global tz
    tz = timezone(os.getenv('TIMEZONE'))

    current_time = tz.localize(datetime.now())

    calendar = get_calendar()
    events_today = get_events(calendar, current_time.date())
    events_tomorrow = get_events(calendar, current_time.date() + timedelta(1))

    events_left_today = list(filter(lambda x: x.dt_end > current_time, events_today))

    showing_today = True
    events_to_plot = events_left_today
    num_total_events = len(events_today)
    if len(events_left_today) == 0:
        events_to_plot = events_tomorrow if len(events_tomorrow) != 0 else None
        num_total_events = len(events_tomorrow) if len(events_tomorrow) != 0 else None
        showing_today = False

    y_coord = 235
    y_offset = 0

    draw = ImageDraw.Draw(image)

    num_drawn = 0
    state.events_graphed = []
    if events_to_plot:
        while num_drawn < 3 and len(events_to_plot) > 0:
            _, y_offset, in_progress = draw_event(image, current_time, events_to_plot[0], (20, y_coord))

            y_coord = y_coord + y_offset
            if y_offset != 0:
                num_drawn = num_drawn + 1
                event_state = EventState()
                event_state.name = events_to_plot[0].event_name
                event_state.start = events_to_plot[0].dt_start
                event_state.end = events_to_plot[0].dt_end
                event_state.in_progress = in_progress
                state.events_graphed.append(event_state)
            events_to_plot.pop(0)
        
        if len(events_to_plot) > 0:
            draw.rounded_rectangle((200, y_coord, 440, y_coord + 46), radius=0, fill=None, outline=0, width=4)
            draw.text((320, y_coord + 23), f"{len(events_to_plot)} more...", anchor="mm", fill=0, font=get_font(Style.BOLD, 26))
            state.overflow_events = len(events_to_plot)

        state.total_events = num_total_events
        if showing_today:
            draw.text((785, 470), f"Today: {num_total_events} total, {len(events_left_today) + num_drawn} left", anchor="rb", fill=0, font=get_font(Style.BOLD, 26))
        else:
            draw.text((785, 470), f"Tomorrow: {num_total_events} events", anchor="rb", fill=0, font=get_font(Style.BOLD, 26))
    else:
        state.total_events = 0
        draw.text((400, 330), "No upcoming events today or tomorrow", anchor="mm", fill=0, font=get_font(Style.BOLD, 26))

def draw_event(image: Image.Image, current_time: datetime, event: SavedEvent, coord: Tuple[int, int]) -> Tuple[int, int, bool]:
    if event.is_all_day or event.dt_end < current_time:
        return (0, 0)
    
    width = 760
    height = 62
    thickness = 4
    time_space = 160
    
    x_coord, y_coord = coord
    in_progress = False

    text_color = 0
    bg_color = None

    event_name = event.event_name.strip()
    font = get_font(Style.BOLD, 30)

    if current_time > event.dt_start and current_time < event.dt_end:
        in_progress = True

    if in_progress:
        text_color = 1
        bg_color = 0

    draw = ImageDraw.Draw(image)

    if draw.textlength(event_name, font=font) > (width - time_space - 15):
        while draw.textlength(f"{event_name.strip()}...", font=font) > (width - time_space - 10):
            event_name = event_name[:-1].strip()
        event_name = f"{event_name}..."

    draw.rounded_rectangle((x_coord, y_coord, x_coord + width, y_coord + height), radius=0, fill=bg_color, outline=0, width=4)

    if not in_progress:
        draw.text((x_coord + time_space - 20, y_coord + (height / 2)), event.dt_start.strftime("%-I:%M%p").lower(), anchor='rm', fill=text_color, font=font)
        draw.text((x_coord + time_space, y_coord + (height / 2)), event_name, anchor='lm', fill=text_color, font=font)
    else:
        draw.text((x_coord + 30, y_coord + (height / 2)), event_name, anchor='lm', fill=text_color, font=font)
        draw.text((x_coord + width - 20, y_coord + (height / 2)), event.dt_end.strftime("%-I:%M%p").lower(), anchor='rm', fill=text_color, font=font)

    return (width - round(thickness / 2), height - round(thickness / 2), in_progress)


def init_image(width: int, height: int) -> Image.Image:
    return Image.new(mode="1", size=(width, height), color=255)


def show_image(image: Image.Image):
    image.show()

def get_screen() -> Tuple[DisplayState, Image.Image]:
    state = DisplayState()
    img = init_image(800, 480)

    draw_day(img, state)
    draw_weather(img, state)
    draw_calendar(img, state)

    return (state, img)

if __name__ == "__main__":

    (state, img) = get_screen()

    show_image(img)

    img.save("output.png", "PNG")

    pass