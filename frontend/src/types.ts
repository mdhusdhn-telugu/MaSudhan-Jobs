export interface JobAnalysis {
  match_score: number;
  is_suitable_for_fresher: boolean;
  salary_estimate: string;
  cover_letter_hook: string;
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