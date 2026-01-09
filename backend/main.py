import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime, timezone, timedelta
import re

# --- CLOUD CONFIG ---
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
TO_EMAIL   = os.environ.get("TO_EMAIL")

# --- MASTER CONFIG ---
CONFIG = {
    "search_queries": [
        "Python Developer Fresher",
        "Java Developer Entry Level",
        "React Developer Intern",
        "Frontend Developer 0-1 Years",
        "Software Engineer Batch 2024 2025",
        "TCS NQT Off Campus",
        "Amazon University Hiring",
        "Graduate Engineer Trainee",
        "Junior Full Stack Developer",
        "Associate Software Engineer"
    ],
    "skills_owned": ["Python", "MySQL", "HTML", "CSS", "JavaScript", "React", "TypeScript", "Java", "C++"], 
    
    # STRICT BLOCKLIST
    "blacklisted_companies": ["Dice", "Braintrust", "Toptal", "CyberCoders", "Hirist", "Patterned Learning", "Crossover"], 
    "blacklisted_titles": ["Senior", "Lead", "Principal", "Manager", "Sr.", "Head", "Architect", "Staff", "II", "III"],
    "blacklisted_keywords": ["flutter", "dart", "android", "ios", "sales", "bpo", "telecaller", "customer support"] 
}

def is_8pm_ist():
    return datetime.now(timezone.utc).hour == 14

def send_email_alert(new_jobs_count, top_new_job):
    if not is_8pm_ist(): return 
    if new_jobs_count == 0 or not GMAIL_USER or not GMAIL_PASS: return

    subject = f"🚀 Daily Summary: {new_jobs_count} Fresh Jobs"
    dashboard_url = "https://masudhans-jobs.netlify.app"
    body = f"""
    <html><body>
        <h2>Hi MaSudhan,</h2>
        <p><b>{new_jobs_count} jobs</b> passed the Fresher Filter today.</p>
        <p><b>Top Pick:</b> {top_new_job['title']} at {top_new_job['company']}</p>
        <p><a href="{dashboard_url}">Open Live Feed</a></p>
    </body></html>
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
    except Exception: pass

# --- THE NEW "EXPERIENCE GUARD" ---
def is_fresher_friendly(description):
    desc_lower = description.lower()
    
    # 1. Look for "Years Experience" patterns
    # Matches: "3+ years", "3-5 years", "minimum 4 years", "5 yrs"
    # We explicitly allow "0-1", "0-2", "0 to 1"
    
    # Regex to find years logic
    # Look for a number followed by "year" or "yr"
    patterns = re.findall(r'(\d+)\s*(?:\+|plus)?\s*(?:-|\s*to\s*)?\s*(\d+)?\s*(?:years?|yrs?)', desc_lower)
    
    for match in patterns:
        min_exp = int(match[0])
        # If minimum experience required is > 1 year, REJECT IT
        if min_exp > 1:
            return False, f"Requires {min_exp}+ years"
            
    # 2. Look for "Senior" keywords in description that usually imply experience
    bad_phrases = ["5+ years", "3+ years", "4+ years", "senior level", "expert level"]
    for phrase in bad_phrases:
        if phrase in desc_lower:
            return False, f"Contains '{phrase}'"

    return True, "Fresher Friendly"

def analyze_job(desc, title, company):
    desc_lower = desc.lower()
    title_lower = title.lower()
    
    # 1. Metadata Filters
    for blocked in CONFIG['blacklisted_companies']:
        if blocked.lower() in company.lower(): return {"is_suitable": False}
    for title_block in CONFIG['blacklisted_titles']:
        if title_block.lower() in title_lower: return {"is_suitable": False}
    for bad_kw in CONFIG['blacklisted_keywords']:
        if bad_kw in title_lower: return {"is_suitable": False}

    # 2. STRICT EXPERIENCE CHECK (New!)
    is_fresh, reason = is_fresher_friendly(desc)
    if not is_fresh:
        return {"is_suitable": False, "reason": reason}

    # 3. Score
    skills_found = [s for s in CONFIG['skills_owned'] if s.lower() in desc_lower]
    match_score = (len(skills_found) / max(len(CONFIG['skills_owned']), 1)) * 100
    
    # Boost for explicitly fresher titles
    if "fresher" in title_lower or "trainee" in title_lower or "intern" in title_lower or "entry" in title_lower:
        match_score += 25
    elif "python" in title_lower or "react" in title_lower:
        match_score += 15
        
    match_score = min(int(match_score), 100)

    if match_score < 10: return {"is_suitable": False}

    return {"is_suitable": True, "match_score": match_score}

def clean_val(value):
    if pd.isna(value) or str(value).lower() == "nan": return "Unknown"
    return str(value)

def load_existing_jobs():
    if os.path.exists('data/jobs.json'):
        try:
            with open('data/jobs.json', 'r') as f: return json.load(f)
        except: return []
    return []

def main():
    print("🚀 Starting MULTI-SOURCE Scraper (Google + LinkedIn + Indeed)...")
    
    existing_jobs = load_existing_jobs()
    fresh_jobs = []
    seen_signatures = set()
    
    # Purge old jobs (>24h)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    
    for job in existing_jobs:
        try:
            t_str = job.get('found_at', '')
            if 'T' in t_str: job_time = datetime.fromisoformat(t_str)
            else: job_time = datetime.strptime(t_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            
            if job_time > cutoff_time:
                sig = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
                if sig not in seen_signatures:
                    fresh_jobs.append(job)
                    seen_signatures.add(sig)
        except: pass
    
    print(f"🧹 Database cleaned. Kept {len(fresh_jobs)} recent jobs.")

    # --- SCRAPING (Added 'google' source) ---
    all_scraped_jobs = []
    for query in CONFIG['search_queries']:
        try:
            # ADDED "google" to the list!
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "zip_recruiter", "google"], 
                search_term=query,
                location="India",
                results_wanted=15, 
                hours_old=24, 
                country_indeed='india'
            )
            all_scraped_jobs.append(jobs)
        except Exception as e:
            print(f"   Error scraping {query}: {e}")

    new_jobs = []
    current_time_iso = datetime.now(timezone.utc).isoformat()

    if all_scraped_jobs:
        jobs_df = pd.concat(all_scraped_jobs, ignore_index=True)
        
        for index, row in jobs_df.iterrows():
            title = clean_val(row.get('title'))
            company = clean_val(row.get('company'))
            
            # Spam Block
            sig = f"{title.lower().strip()}|{company.lower().strip()}"
            if sig in seen_signatures: continue
            
            url = clean_val(row.get('job_url'))
            desc = clean_val(row.get('description'))
            
            # Filter
            analysis = analyze_job(desc, title, company)
            if not analysis['is_suitable']: continue

            new_job_entry = {
                "id": str(hash(url)),
                "title": title,
                "company": company,
                "location": clean_val(row.get('location')),
                "date_posted": clean_val(row.get('date_posted')),
                "found_at": current_time_iso,
                "job_url": url,
                "site": clean_val(row.get('site', 'unknown')),
                "analysis": analysis
            }
            new_jobs.append(new_job_entry)
            seen_signatures.add(sig)

    print(f"✅ Found {len(new_jobs)} UNIQUE Fresh jobs.")

    updated_feed = new_jobs + fresh_jobs
    
    os.makedirs('data', exist_ok=True)
    os.makedirs('frontend/public/data', exist_ok=True)
    with open('data/jobs.json', 'w') as f: json.dump(updated_feed, f, indent=4)
    with open('frontend/public/data/jobs.json', 'w') as f: json.dump(updated_feed, f, indent=4)
        
    if len(new_jobs) > 0:
        send_email_alert(len(new_jobs), new_jobs[0])

if __name__ == "__main__":
    main()
