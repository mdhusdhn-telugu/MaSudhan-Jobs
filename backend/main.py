import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime, timezone, timedelta

# --- CLOUD CONFIG ---
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
TO_EMAIL   = os.environ.get("TO_EMAIL")

# --- MASTER CONFIG ---
CONFIG = {
    "search_queries": [
        "Python Developer Entry Level",
        "Junior React Developer",
        "Frontend Developer Fresher",
        "Amazon University Hiring Software",
        "TCS NQT Fresher",
        "Accenture Associate Software Engineer",
        "Off Campus Drive Batch 2024 2025",
        "Software Engineer Intern India",
        "Junior Full Stack Developer",
        "Wipro Fresher Hiring"
    ],
    "skills_owned": ["Python", "MySQL", "HTML", "CSS", "JavaScript", "React", "TypeScript"], 
    "blacklisted_companies": ["Dice", "Braintrust", "Toptal", "CyberCoders", "Hirist", "Patterned Learning"], 
    "blacklisted_titles": ["Senior", "Lead", "Principal", "Manager", "Sr.", "Head"],
    "blacklisted_keywords": ["flutter", "dart", "android", "ios", "sales", "bpo"] 
}

def is_8pm_ist():
    current_utc = datetime.now(timezone.utc)
    # 8 PM IST is roughly 2:30 PM UTC. We check the hour 14.
    return current_utc.hour == 14

def send_email_alert(new_jobs_count, top_new_job):
    if not is_8pm_ist(): return 
    if new_jobs_count == 0 or not GMAIL_USER or not GMAIL_PASS: return

    subject = f"🚀 Daily Summary: {new_jobs_count} New Jobs"
    dashboard_url = "https://masudhans-jobs.netlify.app"
    
    body = f"""
    <html>
      <body>
        <h2>Hi MaSudhan,</h2>
        <p>Your bot has been running all day. We found <b>{new_jobs_count} new jobs</b>.</p>
        <p><b>Latest Top Pick:</b><br/>
        {top_new_job['title']} at {top_new_job['company']} ({top_new_job['analysis']['match_score']}% Match)</p>
        <p><a href="{dashboard_url}">Open Live Dashboard</a></p>
      </body>
    </html>
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = TO_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("📧 Email Alert Sent!")
    except Exception as e:
        print(f"⚠️ Email Failed: {e}")

def analyze_job(desc, title, company):
    desc_lower = desc.lower()
    title_lower = title.lower()
    
    # 1. Filters
    for blocked in CONFIG['blacklisted_companies']:
        if blocked.lower() in company.lower(): return {"is_suitable": False}
    for title_block in CONFIG['blacklisted_titles']:
        if title_block.lower() in title_lower: return {"is_suitable": False}
    for bad_kw in CONFIG['blacklisted_keywords']:
        if bad_kw in title_lower: return {"is_suitable": False}

    # 2. Score
    skills_found = [s for s in CONFIG['skills_owned'] if s.lower() in desc_lower]
    match_score = (len(skills_found) / max(len(CONFIG['skills_owned']), 1)) * 100
    if "python" in title_lower or "react" in title_lower or "fresh" in title_lower:
        match_score += 20
    match_score = min(int(match_score), 100)

    if match_score < 10: return {"is_suitable": False}

    return {
        "is_suitable": True,
        "match_score": match_score,
        "share_message": f"Hey! Found this job: {title} at {company}. Check it out!"
    }

def clean_val(value):
    if pd.isna(value) or str(value).lower() == "nan": return "Unknown"
    return str(value)

def load_existing_jobs():
    # Load the previous JSON to keep history
    if os.path.exists('data/jobs.json'):
        try:
            with open('data/jobs.json', 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def main():
    print("🚀 Starting Feed Scraper...")
    
    # 1. Load History (So we don't lose previous hours)
    existing_jobs = load_existing_jobs()
    existing_ids = {job['id'] for job in existing_jobs}
    
    # 2. Scrape ONLY fresh data (Last 3 hours is enough for hourly runs)
    all_scraped_jobs = []
    for query in CONFIG['search_queries']:
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "zip_recruiter"], 
                search_term=query,
                location="India",
                results_wanted=5,  # Fetch fewer per query to run faster
                hours_old=3,       # Only look for NEW stuff
                country_indeed='india'
            )
            all_scraped_jobs.append(jobs)
        except Exception as e:
            print(f"   Error scraping {query}: {e}")

    if not all_scraped_jobs: 
        print("No new jobs found this hour.")
        return

    jobs_df = pd.concat(all_scraped_jobs, ignore_index=True)
    
    # 3. Process New Jobs
    new_jobs = []
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for index, row in jobs_df.iterrows():
        url = clean_val(row.get('job_url'))
        job_id = str(hash(url))
        
        # If we already have this job, SKIP IT
        if job_id in existing_ids:
            continue
            
        title = clean_val(row.get('title'))
        company = clean_val(row.get('company'))
        desc = clean_val(row.get('description'))
        
        analysis = analyze_job(desc, title, company)
        if not analysis['is_suitable']: continue

        new_job_entry = {
            "id": job_id,
            "title": title,
            "company": company,
            "location": clean_val(row.get('location')),
            "date_posted": clean_val(row.get('date_posted')), # Original post date
            "found_at": current_time_str,                     # WHEN WE FOUND IT (For sorting)
            "job_url": url,
            "site": clean_val(row.get('site', 'unknown')),
            "analysis": analysis
        }
        new_jobs.append(new_job_entry)
        existing_ids.add(job_id) # Prevent dupes within same run

    print(f"✅ Found {len(new_jobs)} BRAND NEW jobs.")

    # 4. Merge: Put NEW jobs at the TOP
    # Combine [New Jobs] + [Old Jobs]
    updated_feed = new_jobs + existing_jobs

    # 5. Cleanup: Keep list size manageable (e.g., last 100 jobs)
    updated_feed = updated_feed[:100]

    # Save
    os.makedirs('data', exist_ok=True)
    os.makedirs('frontend/public/data', exist_ok=True)
    with open('data/jobs.json', 'w') as f: json.dump(updated_feed, f, indent=4)
    with open('frontend/public/data/jobs.json', 'w') as f: json.dump(updated_feed, f, indent=4)
        
    if len(new_jobs) > 0:
        send_email_alert(len(new_jobs), new_jobs[0])

if __name__ == "__main__":
    main()
