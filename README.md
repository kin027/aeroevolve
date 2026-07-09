# AeroEvolve Visualizer

## Overview

A Python tool that analyzes 1990-2026 Bureau of Transportation Statistics (BTS) data to visualize the evolution of airline route networks over time.

### Why I Built This

I'm an avgeek (aviation enthusiast) and data nerd. If [my 300,000+ miles of air travel](https://my.flightradar24.com/kin_on_a_plane) has taught me anything, it's that the airline industry is truly one where the only constant is change. That especially goes for airlines' route networks, which network planners always monitor and tweak in response to economic conditions, financial crises, pandemics, and geopolitical conflicts.

So, when I found _decades_ of BTS T-100 tables (linked below) showing raw information on airline routes, I knew I had to do something with them, and this... wasn't originally the plan. I initially wanted to build something that would map out all airports from a given airport that were once connected nonstop, but now aren't, then I thought, "Wouldn't it be cooler to use a slider to visualize 36 years of airline route networks on a map?"

(I did have to limit the routes to one origin airport that the user enters, though, or else the resulting map would look more like a plate of spaghetti.)

### Key Insights

Running this saves me from needing to comb through over 13 million rows of raw government data, and instead watch an airline's network strategy unfold just by dragging the slider forward. Since the data goes back to 1990, some interesting aviation history I never knew about is hidden among those rows. Without this, I never would've learned that my home airport, PDX (Portland, OR) once had a nonstop flight to... TPE (Taipei)??? And the airline that operated it was... Delta??? I was shooketh to learn this one, especially knowing that Portland doesn't see a single nonstop to Asia these days (well except for that time [SEA (Seattle-Tacoma) had a fuel shortage that forced STARLUX's SEA-TPE flights to make a fuel stop at PDX](https://www.paddleyourownkanoo.com/2025/11/22/seattle-tacoma-could-run-out-of-jet-fuel-heres-how-airlines-will-manage-this-mess/)).

But a bit of digging revealed that [Delta operated a transpacific gateway hub at PDX in the 90s](https://www.travelcodex.com/de-portland/), which would explain why they also ran flights to various airports in Japan at that time. Unfortunately, those days are long gone, and [Delta's 2024 handover of their PDX-AMS (Amsterdam) route to their partner KLM](https://simpleflying.com/klm-replaces-delta-air-lines-from-amsterdam-portland/) officially marked the end of their long-haul operation out of PDX, meaning that Portland-based Delta loyalists must now take the short flight up to SEA and connect onto one of Delta's many long-haul services to get anywhere meaningful. Oh well, more MQSs (Medallion Qualifying Segments) for them. ✈️

**Try the AeroEvolve Visualizer out with your home airport to discover where you used to be able to go, and where you could go today, with just one flight!**

## Getting Started

Make sure you have Python 3.13 or higher installed.

Note for Linux users: You may need to install Tkinter manually if it isn't included in your distro's default Python package:

```bash
sudo apt-get install python3-tk
```

1. Clone this repository:

```bash
git clone https://github.com/kin027/aeroevolve.git
cd aeroevolve
```

2. Create a virtual environment:

```bash
# Create the environment
python -m venv venv

# Activate it:
# On macOS and Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

3. Install the dependencies (you don't need to download the data tables themselves as I've already included the final ones in the repo):

```bash
pip install -r requirements.txt
```

4. Run the program!

```bash
python main.py
```

## Data Source

I downloaded data from the Bureau of Transportation Statistics (BTS), a part of the U.S. Department of Transportation. Airlines report their traffic data to the BTS each month.

- [BTS T-100 Segment (All Carriers) table from 1990 to 2025](https://www.transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EEE) with DEPARTURES_PERFORMED, PASSENGERS, UNIQUE_CARRIER, UNIQUE_CARRIER_NAME, ORIGIN, ORIGIN_CITY_NAME, ORIGIN_COUNTRY_NAME, DEST, DEST_CITY_NAME, DEST_COUNTRY_NAME, YEAR, MONTH, CLASS fields (to identify nonstop flights, the airlines that operated them, and the months and years of operation)

## Libraries Used

- pandas (to analyze the T-100 tables)

- plotly (to design the map)

- dash (to make the map interactive with the slider)

- pywebview (to open a new window to open the map)

- Tkinter (to create the GUI)

- pathlib (to get all file names in the folder holding all the T-100 CSVs)

- calendar (to convert the month number in each T-100 CSV to its month name)

- threading (to allow concurrent execution)

## Limitations

- The data is not real-time; it comes from BTS data tables that the government releases only once a quarter (with a three-month delay).
  - But I can easily download the most recent T-100s when they're available and immediately visualize the important stuff that happened in 2026, like Alaska going intercontinental and Spirit going belly-up (RIP Spirit).
- Routes that do not touch the U.S. are excluded because the T-100 tables only include routes that start or end somewhere in the U.S.

## Future Improvement Plans

- ~~Adjusting line width based on seats available~~ (Implemented!)

- When All Carriers is selected, color-coding the lines based on the number of carriers operating that route.

- Formatting the slider better (e.g. with the tooltip).

- Preserving the map view when changing the month/year.
