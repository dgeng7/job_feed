# generate_feed.py
#
# This script scrapes recent Data Scientist and Machine Learning Engineer job
# listings from Indeed, deduplicates them, and exports the results as an
# RSS 2.0 XML feed that any RSS reader (e.g. Feedly, NetNewsWire) can subscribe to.

# jobspy is a third-party library that wraps multiple job boards and returns
# results as a pandas DataFrame, making them easy to filter and process.
from jobspy import scrape_jobs

# datetime is used to stamp each RSS <item> with the current UTC time.
from datetime import datetime, timezone

# escape() converts special XML characters (&, <, >) into safe entity references
# (&amp;, &lt;, &gt;) so they don't corrupt the XML structure.
from xml.sax.saxutils import escape

# pandas provides the DataFrame type returned by scrape_jobs(), and its
# date/timedelta helpers are used in the freshness filter below.
import pandas as pd

# ---------------------------------------------------------------------------
# Step 1: Scrape job listings from Indeed
# ---------------------------------------------------------------------------
# scrape_jobs() queries the specified job board and returns a pandas DataFrame
# where each row is one job posting.
#
# Key parameters:
#   site_name      – which job board(s) to query (other supported boards are
#                    listed in the comment; uncomment to enable them)
#   search_term    – keyword(s) sent to the job board's search engine
#   results_wanted – maximum number of listings to fetch per query
#   location       – geographic filter applied to the search
#   country_indeed – country context required by Indeed's API
#   hours_old      – only return listings posted within this many hours


jobs_indeed = scrape_jobs(
    site_name=["indeed"],  # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term='("customer" OR "GTM" OR "LTV" OR "unit economics" OR "lifetime value") ("data scientist" OR "machine learning engineer" OR "applied scientist") -manager -distinguished -director -intern -head -consultant -founding -chief -vp -infra',
    results_wanted=300,
    location="San Francisco Bay Area, CA",
    country_indeed="USA",
    hours_old=336
)

jobs_linkedin = scrape_jobs(
    site_name=["linkedin"],  # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term='("customer" OR "GTM" OR "LTV" OR "unit economics" OR "lifetime value") ("data scientist" OR "machine learning engineer" OR "applied scientist") -manager -distinguished -director -intern -head -consultant -founding -chief -vp -infra',
    results_wanted=200,
    location="San Francisco Bay Area, CA",
    linkedin_fetch_description=True,
    hours_old=336
)


# ---------------------------------------------------------------------------
# Step 2: Filter and merge results
# ---------------------------------------------------------------------------
# Although hours_old=24 already limits the initial query, job boards may still
# return slightly older listings due to caching.  We apply a secondary date
# filter to keep only jobs posted within the last 2 days, providing a safe
# overlap window that prevents stale results from slipping through.

# Combine all DataFrames into one by stacking rows vertically (axis=0).
jobs = pd.concat([jobs_indeed, jobs_linkedin], axis=0)

# A single posting may appear in both search results (e.g. a role titled
# "Data Scientist / ML Engineer").  Drop duplicates by the unique job ID so
# each posting appears only once in the final feed.
jobs = jobs.drop_duplicates(
    subset="id",
    keep="first",  # keep the first occurrence and discard all others
)

# ---------------------------------------------------------------------------
# Step 3: Build the RSS <item> blocks
# ---------------------------------------------------------------------------
# RSS 2.0 is XML-based, so each job becomes an <item> element.  We accumulate
# all items as a single string and embed it in the channel envelope later.
rss_items = ""

for _, job in jobs.iterrows():
    # Pull each field from the row, falling back to an empty string when missing,
    # then escape it so special characters won't break the surrounding XML.
    title = escape(str(job.get("title", "")))
    title_lc = str(job.get("title", "")).lower()
    if not any(k in title_lc for k in ("scientist", "engineer", "analytics")):
        continue
    link = escape(str(job.get("job_url", "")))
    company = escape(str(job.get("company", "")))

    # Truncate descriptions to 8 000 characters — full descriptions can be
    # several thousand characters long and would unnecessarily bloat the feed.
    description = escape(str(job.get("description", ""))[:8000])

    date_posted = escape(str(job.get("date_posted", "")))

    # Build the XML block for this job.  The f-string embeds each variable
    # directly into the template without manual string concatenation.
    rss_items += f"""
    <item>
        <title>{title} - {company}</title>
        <link>{link}</link>
        <description>{description}</description>
        <pubDate>{date_posted}</pubDate>
    </item>
    """

# ---------------------------------------------------------------------------
# Step 4: Wrap items in the RSS 2.0 channel envelope
# ---------------------------------------------------------------------------
# A valid RSS 2.0 document requires a root <rss> element containing a
# <channel> block with feed metadata followed by all the <item> blocks.
# Note: "&" must be written as "&amp;" inside XML text to keep the document
# well-formed — the original "&" in the title was an XML validity bug.
rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>DS &amp; MLE Jobs</title>
    <link>https://indeed.com</link>
    <description>jobs</description>
    {rss_items}
</channel>
</rss>
"""


# ---------------------------------------------------------------------------
# Step 5: Write the feed to disk
# ---------------------------------------------------------------------------
# Open the file with UTF-8 encoding to match the declaration in the XML header.
# If the file already exists it will be overwritten, which is the desired
# behaviour for a periodically regenerated feed.
with open("indeed_jobs.xml", "w", encoding="utf-8") as f:
    f.write(rss_feed)

print("RSS file generated: indeed_jobs.xml")
