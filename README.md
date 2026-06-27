# myYFinance

`myYFinance` is a specialized Python module built on top of the `yfinance` library. It fetches financial market data, filters for specific quote types (such as equities), and processes metrics into organized, structured watchlists. It features custom analytical computations, including a time-weighted analyst revision momentum index.

## Project Structure

This module is designed to work as part of a multi-file package architecture:

```text
your_package/
├── __init__.py
├── myYFinance.py                          # This module (Data retrieval & processing)
├── mytuple.py                             # Defines myTuple/MyTuple data structures
└── mysharesdefinition.py                  # Defines various WatchListDefinitions structures
```

## Features

* **Strict Asset Filtering**: Restricts operations to allowed quote types (e.g., `['EQUITY']`).
* **Weighted Analyst Revisions**: Calculates custom momentum metrics by double-weighting recent 7-day analyst earnings-per-share (EPS) revisions against 30-day trends.
* **Structured Output Categories**: Automatically populates separate dataclass attributes for targeted analysis:
  * Static Watchlist Data (ISIN, Name, Sector, Industry, Currency)
  * Performance Data (Spans, Volumes, Momentum, Moving Averages)
  * Analyst Data
  * Fundamentals Data
  * Derivatives & Calendar Data
* **Safe Data Parsing**: Handles empty DataFrames, missing timestamps, and rounds float lists safely.

## Key Mathematical Functions

### Weighted Revisions Index
The function `calc_weighted_revisions_index(pd_revision_data)` extracts up/down revisions for the last 7 and 30 days to compute a normalized score:

\[\text{Index}_{7d} = \frac{\text{Up}_{7d} - \text{Down}_{7d}}{\text{Up}_{7d} + \text{Down}_{7d}}\]

\[\text{Index}_{30d} = \frac{\text{Up}_{30d} - \text{Down}_{30d}}{\text{Up}_{30d} + \text{Down}_{30d}}\]

\[\text{Weighted Revision} = \frac{2 \cdot \text{Index}_{7d} + \text{Index}_{30d}}{3}\]

## Dependencies

Make sure you have the following external dependencies installed:

```bash
pip install yfinance pandas
```

## Quick Start

Here is how you import and initialize the `MyYFinance` dataclass within your package:

```python
from myYFinance import MyYFinance

# Initialize the dataclass object
ticker_data = MyYFinance()

# The class sets up empty dictionaries and defaults ready to fetch 
# and hold data mapped to your custom WatchListDefinitions.
print(ticker_data._dict_static_watch_list_data)
```

## Architecture Details

### Classes
* `MyYFinance`: A Dataclass that maps raw `yfinance` ticker endpoints (`.info`, `.eps_revisions`, `.history`, `.calendar`) directly into structured internal dictionaries.

### Helper Functions
* `calc_delta_days(int_date_1, int_date_2)`: Calculates the exact days elapsed between two Unix timestamps (defaults to today if the second date is omitted).
* `process_float_list(input_list)`: Verifies if a collection contains only floats and returns them clean and rounded to 2 decimal places.

## License & Copyright

© 2026, Brain Center Höfen. All rights reserved.  
**Author:** Oliver Rudow (<oliver.rudow@googlemail.com>)  
**Version:** 0.1.2
