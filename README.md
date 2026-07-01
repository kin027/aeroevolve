# AeroEvolve Visualizer

## Overview

A Python tool that analyzes 1990-2025 Bureau of Transportation Statistics (BTS) data to visualize the evolution of airline route networks over time.

### Why I Built This

I'm an avgeek (aviation enthusiast) and data nerd. If [my 300,000+ miles of air travel](https://my.flightradar24.com/kin_on_a_plane) has taught me anything, it's that the airline industry is truly one where the only constant is change. That especially goes for airline route networks. So, when I found _decades_ of BTS T-100 tables (linked below) showing raw information on their routes, I knew I had to do something with them, and this... wasn't originally the plan. I initially planned to build something that would map out all airports from a given airport that have lost nonstop service, then I thought, "Wouldn't it be cooler to use a slider to see how airlines have changed their networks over 36 years?" I did have to limit the routes to one origin airport that the user enters, or else the resulting map would look more like a plate of spaghetti.

### Key Insights

Just by dragging the slider forward (or hitting the right arrow key on my keyboard), I could easily see an airline's network strategy for the airports I frequent unfold over time, instead of combing through over 13 million rows of government data. 

Also, an airline's route network is living and breathing. The difference between a profitable airline and one facing bankruptcy could simply be in network planning, so airlines must be quick to adapt to changes in market conditions. From 1990 to now, we've experienced financial crises, pandemics, and geopolitical conflicts, all of which keep network planners on their toes.

With that in mind, an interesting takeaway I got from running this was with American Airlines' long haul presence from LAX (Los Angeles). The map shows that in July 2019, the last summer before COVID, American flew from LAX to nine long haul destinations, but in July 2025, years after the effects of the pandemic had settled, American flew to just three: London/Heathrow, Sydney, and Tokyo/Haneda. 

Let's be honest, something like this was bound to happen to an airline that (shortsightedly) [decided to retire (not park) nearly half of its widebody fleet during COVID](https://viewfromthewing.com/american-retired-40-of-its-long-haul-planes-during-covid-many-are-now-headed-to-a-new-airline/). But American's oneworld alliance partners continue to operate some of those routes, and given how phenomenal they are, I ain't complaining. ✈️

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
3. Install the dependencies (you don't need to download the datasets themselves as I've already included the final ones in the repo):
```bash
pip install -r requirements.txt
```
4. Run the program!
```bash
python main.py
```

## Data Source

I got data from the Bureau of Transportation Statistics (BTS), a part of the U.S. Department of Transportation. Airlines report their traffic data to the BTS each month.

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
  - But I can get 2026 data when it's available and immediately visualize the important stuff that happened this year, like Alaska going intercontiental and Spirit going belly-up (RIP Spirit).
    
- Routes that do not touch the U.S. are excluded because the T-100 tables only include routes that start or end somewhere in the U.S.

## Future Improvement Plans

- When All Carriers is selected, color-coding the lines based on the number of carriers operating that route.

- Formatting the slider better (e.g. with the tooltip).

- Preserving the map view when changing the month/year.