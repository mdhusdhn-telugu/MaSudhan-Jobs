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
    // Add random param to force fresh data load
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

  const getTimingLabel = (foundAt?: string) => {
    if (!foundAt) return "Recently";
    
    // foundAt format: "YYYY-MM-DD HH:MM"
    const [datePart, timePart] = foundAt.split(' ');
    
    // Get today's date in YYYY-MM-DD
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];

    // Get yesterday's date
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];

    if (datePart === todayStr) {
      return `Found Today at ${timePart}`;
    } else if (datePart === yesterdayStr) {
      return `Found Yesterday at ${timePart}`;
    } else {
      return `Found on ${datePart}`;
    }
  };

  return (
    <div className="container">
      <header>
        <div className="logo">
          <span className="icon">M</span>
          <div>
            <h1>MaSudhan's</h1>
            <p>LIVE FEED (Last 24 Hours Only)</p>
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
                  <span>📍 {job.location}</span>
                  <span className="time-tag">
                    🕒 {getTimingLabel(job.found_at)}
                  </span>
                </div>
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
