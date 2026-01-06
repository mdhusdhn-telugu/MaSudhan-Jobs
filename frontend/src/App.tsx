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
    // Add a random number to URL to prevent browser caching
    fetch(`/data/jobs.json?t=${new Date().getTime()}`)
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

  return (
    <div className="container">
      <header>
        <div className="logo">
          <span className="icon">M</span>
          <div>
            <h1>MaSudhan's</h1>
            <p>LIVE FEED (Updates Hourly)</p>
          </div>
        </div>
        <div className="stats">
          <span className="live-badge">● Live</span>
          <span className="count">{jobs.length} Jobs in Feed</span>
        </div>
      </header>

      <main className="job-grid">
        {jobs.length === 0 ? (
          <div className="empty-state"><p>Waiting for next update...</p></div>
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
                  {/* Show specific time */}
                  <span className="time-tag">
                    🕒 {job.found_at ? `Found today at ${job.found_at}` : 'Recent'}
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
