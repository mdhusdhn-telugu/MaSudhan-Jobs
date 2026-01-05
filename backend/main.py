import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime
import time

# --- CLOUD CONFIG ---
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
TO_EMAIL   = os.environ.get("TO_EMAIL")

# --- JOB CONFIG ---
try:
    with open('backend/skills_config.json', 'r') as f:
        CONFIG = json.load(f)
except Exception:
    CONFIG = {
        "search_queries": [
            "Python Developer Entry Level",
            "Junior Frontend Developer", 
            "React Developer Intern",
            "Junior Full Stack Developer"
        ],
        "skills_owned": ["Python", "MySQL", "HTML", "CSS", "JavaScript", "React", "TypeScript"], 
        "skills_desired": ["Django", "Flask", "AWS"],     
        
        # FILTERS
        "blacklisted_companies": ["Dice", "Braintrust", "Toptal", "CyberCoders"], 
        "blacklisted_titles": ["Senior", "Lead", "Principal", "Manager", "Architect"],
        "blacklisted_keywords": ["flutter", "dart", "android", "ios", "native"] 
    }

def send_email_alert(job_count, top_jobs):
    if job_count == 0 or not GMAIL_USER or not GMAIL_PASS: return

    subject = f"🚀 {job_count} Jobs Found (Top Match: {top_jobs[0]['analysis']['match_score']}%)"
    dashboard_url = "https://masudhans-jobs.netlify.app"
    
    body = f"""
    <html>
      <body>
        <h2>Hi MaSudhan,</h2>
        <p>I found <b>{job_count} jobs</b>. Here are the best matches:</p>
        <ul>
    """
    # Show top 5 sorted jobs
    for job in top_jobs[:5]:
        body += f"<li><b>{job['analysis']['match_score']}% Match</b>: {job['title']} at {job['company']}</li>"
        
    body += f"""
        </ul>
        <p><a href="{dashboard_url}">Open Your Dashboard</a></p>
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

def analyze_job(job_description, job_title, company):
    description_lower = job_description.lower()
    title_lower = job_title.lower()
    
    # 1. Company & Title Filter
    for blocked in CONFIG['blacklisted_companies']:
        if blocked.lower() in company.lower(): return {"is_suitable": False}
    for title_block in CONFIG['blacklisted_titles']:
        if title_block.lower() in title_lower: return {"is_suitable": False}

    # 2. Tech Stack Filter
    for bad_keyword in CONFIG['blacklisted_keywords']:
        if bad_keyword in title_lower or bad_keyword in description_lower:
             return {"is_suitable": False, "reason": f"Contains {bad_keyword}"}
            
    # 3. Match Score Calculation
    skills_found = [s for s in CONFIG['skills_owned'] if s.lower() in description_lower]
    # Simple logic: 80% weight on skills, 20% bonus for title match
    match_score = (len(skills_found) / max(len(CONFIG['skills_owned']), 1)) * 80
    
    if "python" in title_lower or "react" in title_lower or "developer" in title_lower:
        match_score += 20
        
    match_score = min(int(match_score), 100)

    if match_score < 10: # Keep low threshold to ensure data flow
        return {"is_suitable": False, "reason": "Low Match"}

    return {
        "is_suitable": True,
        "match_score": match_score,
        "share_message": f"Check out this {job_title} at {company}"
    }

def clean_val(value):
    if pd.isna(value) or str(value).lower() == "nan": return "Unknown"
    return str(value)

def perform_scraping(hours):
    print(f"🔎 Scraping jobs from last {hours} hours...")
    all_jobs = []
    for query in CONFIG['search_queries']:
        try:
            # Added Indeed and ZipRecruiter
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "zip_recruiter"], 
                search_term=query,
                location="India",
                results_wanted=15, 
                hours_old=hours,
                country_indeed='india'
            )
            all_jobs.append(jobs)
        except Exception as e:
            print(f"   Error scraping {query}: {e}")
            
    if not all_jobs: return pd.DataFrame()
    return pd.concat(all_jobs, ignore_index=True)

def main():
    print("🚀 Starting Smart Scraper...")
    
    # --- PHASE 1: Try 24 Hours ---
    jobs_df = perform_scraping(24)

    # --- PHASE 2: Fallback to 35 Hours ---
    if jobs_df.empty:
        print("⚠️ No jobs found in last 24h. Expanding search to 35h...")
        jobs_df = perform_scraping(35)
        
    if jobs_df.empty:
        print("❌ Still no jobs found. Exiting.")
        return

    # Deduplicate
    jobs_df['title_clean'] = jobs_df['title'].astype(str).str.lower().str.strip()
    jobs_df['company_clean'] = jobs_df['company'].astype(str).str.lower().str.strip()
    jobs_df.drop_duplicates(subset=['title_clean', 'company_clean'], inplace=True)
    
    processed_jobs = []
    for index, row in jobs_df.iterrows():
        title = clean_val(row.get('title'))
        company = clean_val(row.get('company'))
        desc = clean_val(row.get('description'))
        url = clean_val(row.get('job_url'))
        date_posted = str(datetime.now().date())

        analysis = analyze_job(desc, title, company)
        if not analysis['is_suitable']: continue

        processed_jobs.append({
            "id": str(hash(url)),
            "title": title,
            "company": company,
            "location": clean_val(row.get('location')),
            "date_posted": date_posted,
            "job_url": url,
            "site": clean_val(row.get('site', 'unknown')),
            "analysis": analysis
        })
        print(f"✅ Saved: {title} ({analysis['match_score']}%)")

    # --- SORTING: Highest Match First ---
    processed_jobs.sort(key=lambda x: x['analysis']['match_score'], reverse=True)

    # Save
    os.makedirs('data', exist_ok=True)
    os.makedirs('frontend/public/data', exist_ok=True)
    
    with open('data/jobs.json', 'w') as f:
        json.dump(processed_jobs, f, indent=4)
    with open('frontend/public/data/jobs.json', 'w') as f:
        json.dump(processed_jobs, f, indent=4)
        
    print(f"🎉 Saved {len(processed_jobs)} jobs (Sorted by Match).")
    send_email_alert(len(processed_jobs), processed_jobs)

if __name__ == "__main__":
    main()
