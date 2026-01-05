import { useState, useEffect } from 'react'
import './App.css'

// 1. Define the NEW Shape of Data (Matches your Python Script)
interface JobAnalysis {
  match_score: number;
  share_message: string;
}

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  date_posted: string;
  job_url: string;
  site: string;
  analysis: JobAnalysis; // <--- The new nested part!
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([])

  // 2. Load the data
  useEffect(() => {
    fetch('/data/jobs.json')
      .then(res => res.json())
      .then(data => {
        // Ensure data is an array before setting it
        if (Array.isArray(data)) {
          setJobs(data);
        } else {
          console.error("Data is not an array:", data);
        }
      })
      .catch(err => console.error("Error loading jobs:", err));
  }, [])

  return (
    <div className="container">
      <header>
        <div className="logo">
          <span className="icon">M</span>
          <div>
            <h1>MaSudhan's</h1>
            <p>PERSONAL JOB CENTER</p>
          </div>
        </div>
        <div className="stats">
          <span className="live-badge">Live Feed</span>
          <span className="count">Found {jobs.length} Jobs</span>
        </div>
      </header>

      <main className="job-grid">
        {jobs.length === 0 ? (
          <div className="empty-state">
             <p>Loading your jobs...</p>
          </div>
        ) : (
          jobs.map(job => (
            <div key={job.id} className="job-card">
              <div className="card-header">
                <h3>{job.title}</h3>
                {/* 3. Read the Score from the NEW location */}
                <span className={`score ${job.analysis.match_score >= 80 ? 'high' : 'med'}`}>
                  {job.analysis.match_score}%
                </span>
              </div>
              
              <div className="company-info">
                <p className="company">{job.company}</p>
                <div className="meta">
                  <span>📍 {job.location}</span>
                  <span className="site-tag">{job.site}</span>
                </div>
              </div>

              <div className="actions">
                <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="apply-btn">
                  Apply Now
                </a>
              </div>
            </div>
          ))
        )}
      </main>
    </div>
  )
}

export default App
