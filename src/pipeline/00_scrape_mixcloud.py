
# ==============================================================================
# SCRAPE MIXCLOUD ----
# This script scrapes Mixcloud for DJ sets and mixes.
# ==============================================================================

# ------------------------------------------------------------------------------
# SETUP ----
# ------------------------------------------------------------------------------

# Import Libraries ----
from utilities.mixcloud_scraper import scrape_mixcloud_main

# ?scrape_mixcloud_main

# Run the Script ----
result = scrape_mixcloud_main(
    dj_url = 'https://www.mixcloud.com/djsprenk',
    test_size = 1,
    scroll_number = 5,
    headless = False,
    verbose = True,
)

result[0]
result[1]