#lat="12.9754", lon="77.6783"
import streamlit as st
import ephem
import calendar
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Pancha Pakshi Decision Calendar", layout="wide")

BIRDS = ["Vulture", "Owl", "Crow", "Cock", "Peacock"]
MONTHS = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]

ACTIVITIES = ["Ruling", "Eating", "Walking", "Sleeping", "Dying"]

# Classical Friendship Matrix
BIRD_RELATIONS = {
    "Vulture": {"Friends": ["Crow"], "Enemies": ["Peacock", "Cock"], "Neutral": ["Owl"]},
    "Owl": {"Friends": ["Cock", "Peacock"], "Enemies": ["Crow", "Vulture"], "Neutral": []},
    "Crow": {"Friends": ["Vulture", "Owl"], "Enemies": ["Peacock", "Cock"], "Neutral": []},
    "Cock": {"Friends": ["Peacock", "Owl"], "Enemies": ["Vulture", "Crow"], "Neutral": []},
    "Peacock": {"Friends": ["Cock", "Vulture"], "Enemies": ["Owl", "Crow"], "Neutral": []}
}

SHUKLA_DAY_ORDER = {
    0: ["Cock", "Vulture", "Owl", "Peacock", "Crow"],     # Sun
    1: ["Owl", "Cock", "Peacock", "Crow", "Vulture"],     # Mon
    2: ["Crow", "Peacock", "Vulture", "Owl", "Cock"],     # Tue
    3: ["Peacock", "Crow", "Cock", "Vulture", "Owl"],     # Wed
    4: ["Vulture", "Owl", "Crow", "Cock", "Peacock"],     # Thu
    5: ["Cock", "Vulture", "Owl", "Peacock", "Crow"],     # Fri
    6: ["Crow", "Peacock", "Vulture", "Owl", "Cock"]      # Sat
}

KRISHNA_DAY_ORDER = {
    0: ["Vulture", "Crow", "Peacock", "Owl", "Cock"],
    1: ["Cock", "Owl", "Vulture", "Peacock", "Crow"],
    2: ["Owl", "Peacock", "Crow", "Cock", "Vulture"],
    3: ["Crow", "Cock", "Owl", "Vulture", "Peacock"],
    4: ["Peacock", "Vulture", "Cock", "Crow", "Owl"],
    5: ["Vulture", "Crow", "Peacock", "Owl", "Cock"],
    6: ["Owl", "Peacock", "Crow", "Cock", "Vulture"]
}

# Panchang Dictionaries
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", 
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", 
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"
]

YOGA_NAMES = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", 
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", 
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", 
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

MOVING_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]

# --- ASTRONOMICAL / PANCHANG ENGINE ---
def get_panchang_and_yamas(date_obj, selected_bird, lat="12.9716", lon="77.5946"):
    obs = ephem.Observer()
    obs.lat = lat
    obs.lon = lon
    obs.elevation = 920

    dt_midnight_ist = datetime.datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0)
    dt_start_utc = dt_midnight_ist - datetime.timedelta(hours=5, minutes=30)
    obs.date = ephem.Date(dt_start_utc)

    sun = ephem.Sun()
    moon = ephem.Moon()

    sunrise_utc = obs.next_rising(sun).datetime()
    sunset_utc = obs.next_setting(sun).datetime()
    sunrise = sunrise_utc + datetime.timedelta(hours=5, minutes=30)
    sunset = sunset_utc + datetime.timedelta(hours=5, minutes=30)

    # Compute at local noon
    obs.date = ephem.Date(dt_start_utc + datetime.timedelta(hours=6))
    sun.compute(obs)
    moon.compute(obs)

    m_ecl = ephem.Ecliptic(moon)
    s_ecl = ephem.Ecliptic(sun)
    moon_lon_trop = float(m_ecl.lon) * 180.0 / 3.141592653589793
    sun_lon_trop = float(s_ecl.lon) * 180.0 / 3.141592653589793

    # Apply rough Lahiri Ayanamsa for accurate Sidereal Yoga calculations
    ayanamsa = 23.85 + (date_obj.year - 2000) * (50.29 / 3600)
    moon_lon = (moon_lon_trop - ayanamsa) % 360.0
    sun_lon = (sun_lon_trop - ayanamsa) % 360.0

    # 1. Tithi Calculation (Relative Angle)
    diff = (moon_lon - sun_lon) % 360.0
    tithi_no = int(diff / 12) + 1
    paksha = "Shukla" if diff < 180.0 else "Krishna"
    
    if tithi_no == 15:
        tithi_name = "Purnima"
    elif tithi_no == 30:
        tithi_name = "Amavasya"
    else:
        tithi_name = TITHI_NAMES[(tithi_no - 1) % 15]

    # 2. Yoga Calculation (Sum of Sidereal Longitudes)
    yoga_idx = int(((sun_lon + moon_lon) % 360.0) / (40.0 / 3.0))
    yoga_name = YOGA_NAMES[yoga_idx]

    # 3. Karana Calculation (Half Tithis)
    karana_idx = int(diff / 6)
    if karana_idx == 0: karana_name = "Kinstughna"
    elif karana_idx == 57: karana_name = "Shakuni"
    elif karana_idx == 58: karana_name = "Chatushpada"
    elif karana_idx == 59: karana_name = "Naga"
    else: karana_name = MOVING_KARANAS[(karana_idx - 1) % 7]

    # Weekday & Bird Logic
    cal_weekday = (date_obj.weekday() + 1) % 7 
    master_order = SHUKLA_DAY_ORDER[cal_weekday] if paksha == "Shukla" else KRISHNA_DAY_ORDER[cal_weekday]
    day_bird = master_order[0]

    day_duration = sunset - sunrise
    yama_len = day_duration / 5
    bird_idx_in_day = master_order.index(selected_bird)
    
    yamas = []
    for i in range(5):
        y_start = sunrise + (yama_len * i)
        y_end = sunrise + (yama_len * (i + 1))
        activity = ACTIVITIES[(i - bird_idx_in_day) % 5]
        yamas.append({
            "start": y_start.strftime("%H:%M"),
            "end": y_end.strftime("%H:%M"),
            "activity": activity
        })

    return {
        "sunrise": sunrise.strftime("%H:%M"),
        "sunset": sunset.strftime("%H:%M"),
        "paksha": paksha,
        "tithi_name": tithi_name,
        "yoga_name": yoga_name,
        "karana_name": karana_name,
        "day_bird": day_bird,
        "yamas": yamas
    }

# --- UI CONTROLS ---
st.title("🦅 Pancha Pakshi Stock Market & Decision Calendar")

c1, c2, c3 = st.columns(3)
with c1:
    selected_bird = st.selectbox("Select Your Birth Bird", BIRDS, index=3) 
with c2:
    selected_year = st.selectbox("Select Year", range(2015, 2051), index=datetime.datetime.now().year - 2015)
with c3:
    current_month_idx = datetime.datetime.now().month - 1
    selected_month_name = st.selectbox("Select Month", MONTHS, index=current_month_idx)

selected_month = MONTHS.index(selected_month_name) + 1

# --- HTML/CSS CALENDAR GENERATOR ---
cal = calendar.Calendar(firstweekday=0)
weeks = cal.monthdatescalendar(selected_year, selected_month)

def generate_cell_html(day_obj, row_idx, col_idx):
    if day_obj.month != selected_month:
        return "<div class='cal-cell outside-month'></div>"

    data = get_panchang_and_yamas(day_obj, selected_bird)
    is_shukla = data["paksha"] == "Shukla"
    bg_class = "shukla-cell" if is_shukla else "krishna-cell"
    badge_color = "#3b82f6" if is_shukla else "#eab308"

    day_bird = data["day_bird"]
    friends = BIRD_RELATIONS[selected_bird]["Friends"]
    enemies = BIRD_RELATIONS[selected_bird]["Enemies"]
    
    if day_bird in friends:
        compat_badge = "<span class='badge favorable'>Friendly Day</span>"
        decision_tip = "High cosmic harmony. Excellent day for decisive trade entries and launches."
    elif day_bird in enemies:
        compat_badge = "<span class='badge enemy'>Enemy Day</span>"
        decision_tip = "Hostile day energy. Strictly defend capital, tighten stops, and avoid large risks."
    else:
        compat_badge = "<span class='badge neutral'>Neutral Day</span>"
        decision_tip = "Balanced conditions. Trade strictly based on established technicals."

    yama_lines = ""
    for y in data["yamas"]:
        act = y["activity"]
        act_class = act.lower()
        icon = "👑" if act == "Ruling" else "🍽️" if act == "Eating" else "🚶" if act == "Walking" else "💤" if act == "Sleeping" else "⚠️"
        yama_lines += f"""
        <div class='yama-row {act_class}'>
            <span class='yama-time'>{y['start']}-{y['end']}</span>
            <span class='yama-act'>{icon} {act}</span>
        </div>
        """

    pos_x = "right: 0;" if col_idx >= 5 else "left: 0;" if col_idx <= 1 else "left: 50%; transform: translateX(-50%);"
    pos_y = "top: 105%;" if row_idx <= 1 else "bottom: 105%;"

    tooltip_html = f"""
    <div class='tooltip-content' style='{pos_x} {pos_y}'>
        <div class='tip-header'>
            <strong>{day_obj.strftime('%A, %d %b %Y')}</strong>
            {compat_badge}
        </div>
        <div class='tip-body'>
            <div class='tip-row'><span>Tithi:</span> <strong>{data['tithi_name']} ({data['paksha']})</strong></div>
            <div class='tip-row'><span>Yoga / Karana:</span> <strong>{data['yoga_name']} / {data['karana_name']}</strong></div>
            <div class='tip-row'><span>Sun / Moon:</span> <strong>{data['sunrise']} | {data['sunset']}</strong></div>
            <div class='tip-row'><span>Day's Ruling Bird:</span> <strong>{day_bird}</strong></div>
            <div class='tip-divider'></div>
            <div class='tip-strategy'>
                <strong>Execution Strategy:</strong><br>
                {decision_tip}
            </div>
        </div>
    </div>
    """

    return f"""
    <div class='cal-cell {bg_class}'>
        <div class='cell-top'>
            <span class='date-num'>{day_obj.day}</span>
            <span class='paksha-pill' style='background-color:{badge_color}22; color:{badge_color}; border: 1px solid {badge_color}55;'>
                {data['paksha'][:2]}. {data['tithi_name']}
            </span>
        </div>
        <div class='yamas-container'>
            {yama_lines}
        </div>
        {tooltip_html}
    </div>
    """

headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
header_html = "".join([f"<div class='cal-header'>{h}</div>" for h in headers])

rows_html = ""
for r_idx, week in enumerate(weeks):
    for c_idx, day in enumerate(week):
        rows_html += generate_cell_html(day, r_idx, c_idx)

full_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    body {{ background: transparent; padding: 10px; }}
    
    .calendar-wrapper {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; width: 100%; }}
    .cal-header {{ background: #1e293b; color: #f8fafc; text-align: center; padding: 10px; font-weight: 700; font-size: 13px; border-radius: 6px; letter-spacing: 0.5px; }}
    
    .cal-cell {{ position: relative; min-height: 180px; border-radius: 8px; border: 1px solid #cbd5e1; padding: 8px; display: flex; flex-direction: column; justify-content: flex-start; transition: transform 0.15s ease, box-shadow 0.15s ease; cursor: default; }}
    .cal-cell:hover {{ z-index: 50; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25); border-color: #64748b; }}

    .shukla-cell {{ background-color: #f1f5f9; }} 
    .krishna-cell {{ background-color: #fef9c3; }} 
    .outside-month {{ background-color: #f8fafc; border: 1px dashed #e2e8f0; opacity: 0.35; }}

    .cell-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
    .date-num {{ font-size: 16px; font-weight: 800; color: #0f172a; }}
    .paksha-pill {{ font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 9999px; white-space: nowrap; }}

    .yamas-container {{ display: flex; flex-direction: column; gap: 3px; }}
    .yama-row {{ display: flex; justify-content: space-between; align-items: center; padding: 2px 5px; border-radius: 4px; font-size: 10.5px; font-weight: 600; line-height: 1.2; }}

    .ruling {{ background: #dcfce7; color: #166534; border-left: 3px solid #16a34a; }}
    .eating {{ background: #ecfdf5; color: #047857; border-left: 3px solid #10b981; }}
    .walking {{ background: #f1f5f9; color: #475569; border-left: 3px solid #94a3b8; }}
    .sleeping {{ background: #fee2e2; color: #991b1b; border-left: 3px solid #f87171; }}
    .dying {{ background: #fef2f2; color: #b91c1c; border-left: 3px solid #dc2626; }}

    .yama-time {{ font-family: monospace; font-size: 10px; }}
    .yama-act {{ font-weight: 700; }}

    .tooltip-content {{ display: none; position: absolute; width: 310px; background: #0f172a; color: #ffffff; padding: 12px; border-radius: 8px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); font-size: 12px; z-index: 100; pointer-events: none; }}
    .cal-cell:hover .tooltip-content {{ display: block; }}
    .tip-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 8px; }}
    .tip-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; color: #cbd5e1; }}
    .tip-row strong {{ color: #f8fafc; }}
    .tip-divider {{ height: 1px; background: #334155; margin: 8px 0; }}
    .tip-strategy {{ background: #1e293b; padding: 8px; border-radius: 6px; color: #e2e8f0; line-height: 1.35; }}

    .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; }}
    .favorable {{ background: #22c55e; color: #fff; }}
    .enemy {{ background: #ef4444; color: #fff; }}
    .neutral {{ background: #64748b; color: #fff; }}
</style>
</head>
<body>
    <div class="calendar-wrapper">
        {header_html}
        {rows_html}
    </div>
</body>
</html>
"""

st.components.v1.html(full_html, height=1350, scrolling=True)
