import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime, timezone

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
    "blacklisted_companies": ["Dice", "Braintrust", "Toptal", "CyberCoders", "Hirist"], 
    "blacklisted_titles": ["Senior", "Lead", "Principal", "Manager", "Sr.", "Head"],
    "blacklisted_keywords": ["flutter", "dart", "android", "ios", "sales", "bpo"] 
}

def is_8pm_ist():
    # GitHub runs in UTC. 8 PM IST is roughly 2:30 PM UTC (14:30).
    # We check if the current UTC hour is 14 (which covers 7:30 PM - 8:30 PM IST)
    current_utc = datetime.now(timezone.utc)
    return current_utc.hour == 14

def send_email_alert(job_count, top_jobs):
    # ONLY send email if it's 8 PM IST (approx)
    if not is_8pm_ist(): 
        print("🕒 Not 8 PM yet. Skipping email.")
        return

    if job_count == 0 or not GMAIL_USER or not GMAIL_PASS: return

    subject = f"🚀 {job_count} Jobs (Daily Summary)"
    dashboard_url = "https://masudhans-jobs.netlify.app"
    
    body = f"""
    <html>
      <body>
        <h2>Hi MaSudhan,</h2>
        <p>Here is your 8 PM summary. The bot has been updating all day.</p>
        <p><b>Top Fresh Picks:</b></p>
        <ul>
    """
    for job in top_jobs[:5]:
        body += f"<li><b>{job['analysis']['match_score']}% Match</b>: {job['title']} at {job['company']}</li>"
        
    body += f"""
        </ul>
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

def main():
    print("🚀 Starting Hourly Scraper...")
    all_jobs = []
    
    # Scrape last 24h of data (always ensures overlap so list is never empty)
    for query in CONFIG['search_queries']:
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "zip_recruiter"], 
                search_term=query,
                location="India",
                results_wanted=10, 
                hours_old=24, 
                country_indeed='india'
            )
            all_jobs.append(jobs)
        except Exception as e:
            print(f"   Error scraping {query}: {e}")

    if not all_jobs: return

    jobs_df = pd.concat(all_jobs, ignore_index=True)
    
    # Deduplicate
    jobs_df['title_clean'] = jobs_df['title'].astype(str).str.lower().str.strip()
    jobs_df['company_clean'] = jobs_df['company'].astype(str).str.lower().str.strip()
    jobs_df.drop_duplicates(subset=['title_clean', 'company_clean'], inplace=True)
    
    processed_jobs = []
    for index, row in jobs_df.iterrows():
        title = clean_val(row.get('title'))
        company = clean_val(row.get('company'))
        url = clean_val(row.get('job_url'))
        desc = clean_val(row.get('description'))
        
        analysis = analyze_job(desc, title, company)
        if not analysis['is_suitable']: continue

        processed_jobs.append({
            "id": str(hash(url)),
            "title": title,
            "company": company,
            "location": clean_val(row.get('location')),
            "date_posted": str(datetime.now().date()),
            "job_url": url,
            "site": clean_val(row.get('site', 'unknown')),
            "analysis": analysis
        })

    # Sort: Highest Match First
    processed_jobs.sort(key=lambda x: x['analysis']['match_score'], reverse=True)

    # Save
    os.makedirs('data', exist_ok=True)
    os.makedirs('frontend/public/data', exist_ok=True)
    with open('data/jobs.json', 'w') as f: json.dump(processed_jobs, f, indent=4)
    with open('frontend/public/data/jobs.json', 'w') as f: json.dump(processed_jobs, f, indent=4)
        
    print(f"✅ Saved {len(processed_jobs)} active jobs.")
    send_email_alert(len(processed_jobs), processed_jobs)

if __name__ == "__main__":
    main()
