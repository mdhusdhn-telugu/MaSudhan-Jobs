import { useState, useEffect } from 'react'
import './App.css'

interface JobAnalysis {
  match_score: number;
  share_message: string;
}

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  found_at?: string;
  job_url: string;
  site: string;
  analysis: JobAnalysis;
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([])

  useEffect(() => {
    fetch(`/data/jobs.json?t=${Date.now()}`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setJobs(data);
      })
      .catch(err => console.error("Error loading jobs:", err));
  }, [])

  const shareJob = (job: Job) => {
    const text = `Hey, check out this job: ${job.title} at ${job.company}. Link: ${job.job_url}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(whatsappUrl, '_blank');
  };

  // CALCULATE "X MINS AGO"
  const getTimeAgo = (isoDate?: string) => {
    if (!isoDate) return 'Recently';
    
    // Convert UTC string to Date Object
    const past = new Date(isoDate);
    const now = new Date();
    
    const diffMs = now.getTime() - past.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} mins ago`;
    
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs} hours ago`;
    
    return 'Yesterday';
  };

  // BEAUTIFY SOURCE NAME
  const getSourceLabel = (site: string) => {
    const s = site.toLowerCase();
    if (s.includes('linkedin')) return 'LinkedIn';
    if (s.includes('indeed')) return 'Indeed';
    if (s.includes('zip')) return 'ZipRecruiter';
    return site; // Fallback
  };

  return (
    <div className="container">
      <header>
        <div className="logo">
          <span className="icon">M</span>
          <div>
            <h1>MaSudhan's</h1>
            <p>LIVE FEED (Last 24 Hours)</p>
          </div>
        </div>
        <div className="stats">
          <span className="live-badge">● Live</span>
          <span className="count">{jobs.length} Active Jobs</span>
        </div>
      </header>

      <main className="job-grid">
        {jobs.length === 0 ? (
          <div className="empty-state"><p>Waiting for hourly update...</p></div>
        ) : (
          jobs.map(job => (
            <div key={job.id} className="job-card">
              <div className="card-header">
                <h3>{job.title}</h3>
                <span className={`score ${job.analysis.match_score >= 80 ? 'high' : 'med'}`}>
                  {job.analysis.match_score}%
                </span>
              </div>
              
              <div className="company-info">
                <p className="company">{job.company}</p>
                <div className="meta">
                  {/* SOURCE BADGE */}
                  <span className="source-tag">{getSourceLabel(job.site)}</span>
                  
                  {/* TIME AGO BADGE */}
                  <span className="time-tag">
                    🕒 {getTimeAgo(job.found_at)}
                  </span>
                </div>
                <p className="location-text">📍 {job.location}</p>
              </div>

              <div className="actions">
                <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="apply-btn">
                  Apply Now
                </a>
                <button onClick={() => shareJob(job)} className="share-btn">
                  Share ↗
                </button>
              </div>
            </div>
          ))
        )}
      </main>
    </div>
  )
}

export default App
