from jobspy import scrape_jobs
from datetime import datetime
from xml.sax.saxutils import escape
import pandas as pd

# Step 1: Scrape jobs
jobs_DS = scrape_jobs(
    site_name=["indeed"], # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term="Data Scientist",
    results_wanted=200,
    location="San Francisco Bay Area, CA",
    country_indeed='USA',
    hours_old=24,
)

jobs_MLE = scrape_jobs(
    site_name=["indeed"], # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term="Machine Learning Engineer",
    results_wanted=200,
    location="San Francisco Bay Area, CA",
    country_indeed='USA',
    hours_old=24,
)

jobs_MLE_filtered = jobs_MLE[jobs_MLE.date_posted >= (pd.Timestamp.now() - pd.Timedelta(days=2)).date()]
jobs_DS_filtered = jobs_DS[jobs_DS.date_posted >= (pd.Timestamp.now() - pd.Timedelta(days=2)).date()]

jobs = pd.concat([jobs_MLE_filtered, jobs_DS_filtered],axis=0)

# Step 2: Build RSS items
rss_items = ""

for _, job in jobs.iterrows():
    title = escape(str(job.get("title", "")))
    link = escape(str(job.get("job_url", "")))
    company = escape(str(job.get("company", "")))
    description = escape(str(job.get("description", ""))[:1000])

    pub_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    rss_items += f"""
    <item>
        <title>{title} - {company}</title>
        <link>{link}</link>
        <description>{description}</description>
        <pubDate>{pub_date}</pubDate>
    </item>
    """

rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>DS&MLE Jobs</title>
    <link>https://indeed.com</link>
    <description>Scraped jobs</description>
    {rss_items}
</channel>
</rss>
"""

with open("indeed_jobs.xml", "w", encoding="utf-8") as f:
    f.write(rss_feed)

print("RSS file generated: indeed_jobs.xml")