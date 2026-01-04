import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime
import re

# --- CLOUD CONFIG (Loads from GitHub Secrets) ---
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
            "Junior Full Stack Developer",
            "Web Developer Fresher"
        ],
        "skills_owned": ["Python", "MySQL", "HTML", "CSS", "JavaScript", "React", "TypeScript", "Git", "GitHub"], 
        "skills_desired": ["Django", "Flask", "Redux", "AWS", "Docker", "Tailwind"],     
        "experience_level": "Entry",
        "blacklisted_companies": ["Dice", "Sporty", "rossover", "Braintrust", "Toptal", "CyberCoders", "Hirist"], 
        "blacklisted_titles": ["Senior", "Lead", "Principal", "Architect", "Sr.", "Manager"]
    }

def send_email_alert(job_count, top_jobs):
    if job_count == 0 or not GMAIL_USER or not GMAIL_PASS: return

    subject = f"🚀 {job_count} New Jobs Ready - MaSudhan's Feed"
    
    # Netlify URL (We will update this dynamically or use a generic link)
    dashboard_url = "https://masudhans-jobs.netlify.app" 
    
    body = f"""
    <html>
      <body>
        <h2>Hi MaSudhan,</h2>
        <p>The cloud scraper finished. <b>{job_count} fresh jobs</b> are waiting.</p>
        <p><b>Top Picks:</b></p>
        <ul>
    """
    
    for job in top_jobs[:5]:
        body += f"<li><b>{job['title']}</b> at {job['company']} ({job['analysis']['match_score']}%)</li>"
        
    body += f"""
        </ul>
        <p><a href="{dashboard_url}">Open Dashboard</a></p>
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

def normalize_salary(description):
    desc_lower = description.lower()
    lpa_match = re.search(r'(\d+)\s?-?\s?(\d+)?\s?lpa', desc_lower)
    if lpa_match:
        min_sal = float(lpa_match.group(1))
        max_sal = float(lpa_match.group(2)) if lpa_match.group(2) else min_sal
        return f"₹{min_sal}L - ₹{max_sal}L PA"
    mo_match = re.search(r'(\d+)k\s?/mo', desc_lower)
    if mo_match:
        val = float(mo_match.group(1)) * 12 / 100 
        return f"~₹{val:.1f}L PA"
    return "Not Disclosed"

def analyze_job(job_description, job_title, company, date_posted):
    description_lower = job_description.lower()
    title_lower = job_title.lower()
    
    for blocked in CONFIG['blacklisted_companies']:
        if blocked.lower() in company.lower(): return {"is_suitable": False}
    for title_block in CONFIG['blacklisted_titles']:
        if title_block.lower() in title_lower: return {"is_suitable": False}
            
    skills_found = [s for s in CONFIG['skills_owned'] if s.lower() in description_lower]
    missing_skills = [s for s in CONFIG['skills_desired'] if s.lower() in description_lower]
    
    total_relevant = len(skills_found) + len(missing_skills)
    match_score = (len(skills_found) / max(total_relevant, 1)) * 100
    if "python" in title_lower or "react" in title_lower: match_score += 15
    match_score = min(int(match_score), 100)

    hook = f"Hey, check out this {job_title} role at {company}. It matches my stack!"

    return {
        "is_suitable": True,
        "match_score": match_score,
        "salary_estimate": normalize_salary(description_lower),
        "skill_gap": missing_skills,
        "share_message": hook
    }

def clean_val(value):
    if pd.isna(value) or str(value).lower() == "nan": return "Unknown"
    return str(value)

def main():
    print("🚀 Starting Cloud Scraper...")
    all_jobs = []
    
    for query in CONFIG['search_queries']:
        try:
            # Using Indeed/Glassdoor can be tricky in cloud due to bot protection.
            # We prioritize LinkedIn/Glassdoor for reliability in CI/CD.
            jobs = scrape_jobs(
                site_name=["linkedin", "glassdoor"], 
                search_term=query,
                location="India",
                results_wanted=8, 
                hours_old=24,
                country_indeed='india'
            )
            all_jobs.append(jobs)
        except Exception as e:
            print(f"   Error: {e}")

    if not all_jobs: return

    jobs_df = pd.concat(all_jobs, ignore_index=True)
    jobs_df.drop_duplicates(subset=['job_url'], inplace=True)
    
    processed_jobs = []
    for index, row in jobs_df.iterrows():
        title = clean_val(row.get('title'))
        company = clean_val(row.get('company'))
        desc = clean_val(row.get('description'))
        url = clean_val(row.get('job_url'))
        date_posted = row.get('date_posted', datetime.now().date())

        analysis = analyze_job(desc, title, company, date_posted)
        if not analysis['is_suitable']: continue

        processed_jobs.append({
            "id": str(hash(url)),
            "title": title,
            "company": company,
            "location": clean_val(row.get('location')),
            "date_posted": str(date_posted),
            "job_url": url,
            "site": clean_val(row.get('site', 'unknown')),
            "analysis": analysis
        })
        print(f"✅ Saved: {title}")

    # Ensure directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('frontend/public/data', exist_ok=True)

    # Save to both locations so Netlify picks it up
    with open('data/jobs.json', 'w') as f:
        json.dump(processed_jobs, f, indent=4)
    with open('frontend/public/data/jobs.json', 'w') as f:
        json.dump(processed_jobs, f, indent=4)
        
    print(f"🎉 Saved {len(processed_jobs)} jobs.")
    send_email_alert(len(processed_jobs), processed_jobs)

if __name__ == "__main__":
    main()