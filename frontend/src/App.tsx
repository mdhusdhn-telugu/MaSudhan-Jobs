import React, { useState, useEffect } from 'react';

export interface JobAnalysis {
  match_score: number;
  salary_estimate: string;
  share_message: string;
  skill_gap: string[];
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  date_posted: string;
  job_url: string;
  site: string;
  analysis: JobAnalysis;
}

const App: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<string>('');
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [view, setView] = useState<'feed' | 'saved'>('feed');

  useEffect(() => {
    const saved = localStorage.getItem('zero_battery_saved_jobs');
    if (saved) setSavedJobIds(new Set(JSON.parse(saved)));

    const fetchJobs = async () => {
      try {
        const response = await fetch('/data/jobs.json');
        if (!response.ok) throw new Error('Data not found');
        const data = await response.json();
        setJobs(data.sort((a: Job, b: Job) => b.analysis.match_score - a.analysis.match_score));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  const toggleSave = (id: string) => {
    const newSaved = new Set(savedJobIds);
    newSaved.has(id) ? newSaved.delete(id) : newSaved.add(id);
    setSavedJobIds(newSaved);
    localStorage.setItem('zero_battery_saved_jobs', JSON.stringify(Array.from(newSaved)));
  };

  const shareJob = (job: Job) => {
    const text = `${job.analysis.share_message}\nLink: ${job.job_url}`;
    navigator.clipboard.writeText(text);
    alert("Job link & message copied! Send it to your friend.");
  }

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.title.toLowerCase().includes(filter.toLowerCase()) || 
                          job.company.toLowerCase().includes(filter.toLowerCase());
    const matchesView = view === 'saved' ? savedJobIds.has(job.id) : true;
    return matchesSearch && matchesView;
  });

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-emerald-50 text-emerald-800">Loading MaSudhan's Dashboard...</div>;

  return (
    <div className="min-h-screen bg-[#f0fdf4] font-sans text-slate-800">
      
      {/* Top Navigation Bar */}
      <nav className="sticky top-0 z-20 backdrop-blur-md bg-white/70 border-b border-emerald-100 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-white font-bold shadow-lg shadow-emerald-200">
                    M
                </div>
                <div>
                    <h1 className="text-xl font-bold text-slate-900 tracking-tight">MaSudhan's</h1>
                    <p className="text-[10px] text-emerald-600 font-medium uppercase tracking-wider">Personal Job Center</p>
                </div>
            </div>
            
            <div className="flex bg-slate-100/50 p-1 rounded-xl">
                <button 
                    onClick={() => setView('feed')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${view === 'feed' ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-500 hover:text-emerald-600'}`}
                >
                    Live Feed
                </button>
                <button 
                    onClick={() => setView('saved')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${view === 'saved' ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-500 hover:text-emerald-600'}`}
                >
                    Saved ({savedJobIds.size})
                </button>
            </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto p-6 md:p-8">
        
        {/* Job Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredJobs.map(job => (
                <div key={job.id} className="group bg-white rounded-2xl border border-emerald-50 p-6 hover:border-emerald-200 hover:shadow-xl hover:shadow-emerald-900/5 transition-all duration-300 flex flex-col">
                    
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="font-bold text-lg text-slate-900 group-hover:text-emerald-700 transition-colors line-clamp-1">{job.title}</h3>
                            <p className="text-sm font-medium text-slate-500">{job.company}</p>
                        </div>
                        <div className={`flex flex-col items-center justify-center w-12 h-12 rounded-xl font-bold text-sm ${job.analysis.match_score >= 80 ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                            <span>{job.analysis.match_score}</span>
                            <span className="text-[8px] uppercase opacity-70">%</span>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2 mb-6">
                        <span className="px-2.5 py-1 rounded-md bg-slate-50 text-slate-600 text-xs font-medium border border-slate-100">{job.location}</span>
                        <span className="px-2.5 py-1 rounded-md bg-slate-50 text-slate-600 text-xs font-medium border border-slate-100 uppercase">{job.site}</span>
                        {job.analysis.salary_estimate !== "Not Disclosed" && (
                            <span className="px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-100">
                                {job.analysis.salary_estimate}
                            </span>
                        )}
                    </div>

                    {job.analysis.skill_gap.length > 0 && (
                        <div className="mb-4 bg-red-50/50 rounded-lg p-3 border border-red-100">
                            <p className="text-[10px] font-bold text-red-400 uppercase tracking-wide mb-2">Skill Gaps Detected</p>
                            <div className="flex flex-wrap gap-1.5">
                                {job.analysis.skill_gap.map(skill => (
                                    <span key={skill} className="px-1.5 py-0.5 bg-white text-red-600 text-[10px] font-medium rounded border border-red-100 shadow-sm">
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="mt-auto pt-4 border-t border-slate-50 grid grid-cols-2 gap-3">
                        <button 
                            onClick={() => shareJob(job)}
                            className="px-4 py-2 bg-white border border-slate-200 text-slate-600 text-xs font-bold rounded-lg hover:bg-slate-50 hover:text-emerald-600 transition-colors flex items-center justify-center gap-2"
                        >
                            Share ↗
                        </button>
                        <div className="flex gap-2">
                             <button 
                                onClick={() => toggleSave(job.id)}
                                className={`flex-1 rounded-lg border flex items-center justify-center transition-colors ${savedJobIds.has(job.id) ? 'bg-emerald-50 border-emerald-200 text-emerald-600' : 'border-slate-200 text-slate-400 hover:border-emerald-200'}`}
                             >
                                <svg className="w-4 h-4" fill={savedJobIds.has(job.id) ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                             </button>
                             <a 
                                href={job.job_url} 
                                target="_blank"
                                className="flex-[2] flex items-center justify-center bg-slate-900 text-white text-xs font-bold rounded-lg hover:bg-emerald-600 transition-colors"
                             >
                                Apply
                             </a>
                        </div>
                    </div>
                </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default App;