import { useEffect, useRef, useState } from 'react';
import { ArrowDownToLine, ArrowUpRight, BarChart3, Check, FileText, Plus, Search, Terminal, X } from 'lucide-react';
import './JobDesk.css';

type Job = { title?: string; company?: string; description: string; url?: string; source?: string; published_at?: string | null; location?: string; remote?: boolean | null };
type Quote = { line: number; text: string };
type Evidence = { skill: string; status: string; evidence: Quote[] };
type ReviewedJob = Job & { id: string; source_text: string; source_sha256: string; skill_evidence: Evidence[]; signals: Record<string, Quote[]>; questions: string[] };
type Report = { jobs: ReviewedJob[]; duplicates: { title: string; content_changed: boolean; alternate: ReviewedJob }[]; reviewed_at: string; method: string };
type Board = { jobs: Job[]; matching_count: number; scanned_count: number; fetched_at: string; coverage: string };
type SkillSummary = { skill: string; listing_count: number; evidence: { title: string; company: string; url?: string; quotes: Quote[] }[] };
type BoardSummary = { skills: SkillSummary[]; listing_count: number; matching_count: number; scanned_count: number; fetched_at: string; coverage: string; method: string };
const BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
// SOURCE: backend JobInput/ReviewInput and JobPrivacyMiddleware limits.
const MAX_JOBS = 20;
const MAX_TEXT = 60_000;
const MAX_FILE = 2_000_000;
const STORAGE = 'relay-job-desk-v1';
const SCHEMA = 'relay-job-workspace-v1';
const date = (value?: string | null) => value && Number.isFinite(Date.parse(value)) ? new Date(value).toLocaleString() : 'Date not supplied';

async function request(path: string, payload?: unknown): Promise<Response> {
  // GUESS: UNCALIBRATED GUESS deadline accommodates a cold backend without an endless spinner.
  const signal = AbortSignal.timeout(45_000);
  const response = await fetch(`${BASE}/jobs/${path}`, payload === undefined ? { cache: 'no-store', signal } : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), cache: 'no-store', signal,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail)
      ? data.detail.map((item: { msg: string }) => item.msg).join('; ') : 'Service unavailable. Please try again.';
    throw new Error(detail);
  }
  return response;
}

function download(value: string, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([value], { type }));
  const link = document.createElement('a');
  link.href = url; link.download = filename; link.click();
  URL.revokeObjectURL(url);
}

function parseWorkspace(raw: string): { jobs: Job[]; skills: string } {
  if (new Blob([raw]).size > MAX_FILE) throw new Error('Workspace exceeds the 2 MB limit.');
  const data = JSON.parse(raw);
  if (data.schema !== SCHEMA || !Array.isArray(data.jobs) || data.jobs.length > MAX_JOBS || typeof data.skills !== 'string')
    throw new Error('Choose a Relay workspace JSON export.');
  const allowed = new Set(['title', 'company', 'description', 'url', 'source', 'published_at', 'location', 'remote']);
  for (const job of data.jobs) {
    if (!job || typeof job.description !== 'string' || !job.description.trim() || job.description.length > MAX_TEXT ||
      Object.keys(job).some(key => !allowed.has(key))) throw new Error('Invalid listing in workspace.');
    for (const key of ['title', 'company', 'url', 'source', 'published_at', 'location'])
      if (job[key] != null && typeof job[key] !== 'string') throw new Error(`Invalid ${key} in workspace.`);
    if (job.remote != null && typeof job.remote !== 'boolean') throw new Error('Invalid remote field.');
    if (job.url) { const url = new URL(job.url); if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password) throw new Error('Unsafe listing URL.'); }
  }
  return { jobs: data.jobs, skills: data.skills };
}

export function JobDesk() {
  const [tab, setTab] = useState<'board' | 'paste'>('board');
  const [board, setBoard] = useState<Board | null>(null);
  const [summary, setSummary] = useState<BoardSummary | null>(null);
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [remote, setRemote] = useState(false);
  const [searching, setSearching] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [skills, setSkills] = useState('Python, TypeScript, PostgreSQL, SQL, AI, MCP');
  const [report, setReport] = useState<Report | null>(null);
  const [selected, setSelected] = useState(0); // SOURCE: initial array selection, not a ranking.
  const [paste, setPaste] = useState({ title: '', company: '', url: '', description: '' });
  const fileRef = useRef<HTMLInputElement>(null);
  const searchVersion = useRef(0); // SOURCE: request sequence prevents stale search responses replacing newer results.
  const summaryVersion = useRef(0); // SOURCE: request sequence prevents stale aggregate responses replacing newer results.
  const current = report?.jobs[selected];

  async function search() {
    const version = ++searchVersion.current;
    setSearching(true); setError(''); setBoard(null);
    try {
      const params = new URLSearchParams({ query, location, remote_only: String(remote) });
      const data = await (await request(`search?${params}`)).json();
      if (version === searchVersion.current) setBoard(data);
    } catch (e) { if (version === searchVersion.current) setError(e instanceof Error ? e.message : 'Could not read the board.'); }
    finally { if (version === searchVersion.current) setSearching(false); }
  }
  const selectedSkills = () => skills.split(',').map(s => s.trim()).filter(Boolean)
    .filter((skill, index, values) => values.findIndex(other => other.toLowerCase() === skill.toLowerCase()) === index);
  async function summarize() {
    const chosen = selectedSkills();
    if (!chosen.length) { setSummary(null); return; }
    const version = ++summaryVersion.current;
    setSummarizing(true); setError('');
    try {
      const data = await (await request('summary', { query, location, remote_only: remote, skills: chosen })).json();
      if (version === summaryVersion.current) setSummary(data);
    } catch (e) { if (version === summaryVersion.current) setError(e instanceof Error ? e.message : 'Could not count board evidence.'); }
    finally { if (version === summaryVersion.current) setSummarizing(false); }
  }
  function runBoardQuery() { void search(); void summarize(); }
  // SOURCE: initial read of a public board; never submits or changes external records.
  useEffect(() => { runBoardQuery(); return () => { searchVersion.current++; summaryVersion.current++; }; }, []);

  function changed() { setReport(null); setNotice(''); setError(''); }
  function add(job: Job) {
    if (jobs.length >= MAX_JOBS) { setError('Review up to 20 listings at a time. Export this batch before starting another.'); return; }
    changed(); setJobs([...jobs, job]); setNotice('Added to your review queue.');
  }
  const payload = () => ({ jobs, skills: selectedSkills() });
  async function review() {
    setWorking(true); setError(''); setNotice('');
    try { const result = await (await request('review', payload())).json(); setReport(result); setSelected(0); }
    catch (e) { setError(e instanceof Error ? e.message : 'Review failed.'); }
    finally { setWorking(false); }
  }
  // Export original inputs, including every duplicate, without duplicating the entire derived report.
  function workspace() { return JSON.stringify({ schema: SCHEMA, jobs, skills }, null, 2); } // SOURCE: JSON indentation for readability.
  function restore(raw: string) {
    const value = parseWorkspace(raw); changed(); setJobs(value.jobs); setSkills(value.skills);
    setNotice('Workspace restored. Run a fresh review to verify its evidence.');
  }
  async function exportMarkdown() {
    setWorking(true); setError('');
    try { download(await (await request('export', payload())).text(), 'relay-review.md', 'text/markdown'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Export failed.'); }
    finally { setWorking(false); }
  }
  const endpoint = new URL(BASE, window.location.origin).origin + '/tools/mcp';

  return <div className="job-desk">
    <header className="desk-header"><a className="desk-brand" href="#"><span aria-hidden="true">↳</span> Relay</a></header>
    <main className="desk-main">
      <div className="desk-heading"><div><p className="eyebrow">MCP · PYTHON · TYPESCRIPT</p><h1>Check a job’s requirements</h1><p>Add a listing, enter the skills you want to find, then select Review evidence. The review shows the original wording so you can check it yourself.</p></div>
        <div className="desk-contract"><Check size={18} /><div><strong>Public job descriptions only</strong><p>Do not paste your CV or private messages. This tool does not submit applications or save reviews to its database.</p></div></div></div>
      {error && <div className="desk-error" role="alert">{error} <button onClick={() => setError('')} aria-label="Dismiss error"><X size={16} /></button></div>}
      {notice && <p className="desk-notice" role="status">{notice}</p>}
      <details className="desk-panel summary-panel">
        <summary>Skill mentions on the public board</summary>
        <div className="panel-heading"><div><h2>Latest page only</h2><p>Open a skill count to read the listings it came from.</p></div><button className="desk-button" disabled={summarizing || !selectedSkills().length} onClick={() => void summarize()}><BarChart3 size={15} />{summarizing ? 'Counting…' : 'Refresh counts'}</button></div>
        <div className="summary-body" aria-busy={summarizing}>{!summary && <p className="desk-empty">Reading the current board evidence…</p>}{summary && <><div className="summary-bars">{summary.skills.map(item => { const max = Math.max(1, ...summary.skills.map(row => row.listing_count)); const width = `${(item.listing_count / max) * 100}%`; return <details className="summary-skill" key={item.skill}><summary><span>{item.skill}</span><i><b style={{ width }}></b></i><strong>{item.listing_count} / {summary.listing_count}</strong></summary><div className="summary-sources">{item.evidence.length ? item.evidence.map((source, index) => <article key={`${source.url}-${index}`}><div><strong>{source.title}</strong><span>{source.company}</span></div>{source.quotes.map(quote => <blockquote key={quote.line}><small>LINE {quote.line}</small>{quote.text}</blockquote>)}{source.url && <a href={source.url} target="_blank" rel="noreferrer">Original listing ↗</a>}</article>) : <p>No literal mention in this result.</p>}</div></details> })}</div><div className="summary-boundary"><p>{summary.method}</p><p>{summary.listing_count} filtered listings · {summary.scanned_count} valid listings scanned on the latest API page · fetched {date(summary.fetched_at)}.</p><p>{summary.coverage}</p></div></>}</div>
      </details>
      <div className="desk-columns">
        <section className="desk-panel desk-sources" aria-label="Find listings"><div className="panel-heading"><h2>Find listings</h2><div className="source-tabs"><button aria-pressed={tab === 'board'} onClick={() => setTab('board')}>Public board</button><button aria-pressed={tab === 'paste'} onClick={() => setTab('paste')}>Paste a listing</button></div></div>
          {tab === 'board' ? <><form className="board-search" onSubmit={e => { e.preventDefault(); runBoardQuery(); }}>
            <label>Keyword<input value={query} onChange={e => setQuery(e.target.value)} maxLength={100} placeholder="Python, backend, data…" /></label>
            <label>Location<input value={location} onChange={e => setLocation(e.target.value)} maxLength={100} placeholder="City or country" /></label>
            <div className="search-bottom"><label className="check-label"><input type="checkbox" checked={remote} onChange={e => setRemote(e.target.checked)} />Remote tag only</label><button className="desk-button primary" disabled={searching} type="submit"><Search size={15} />{searching ? 'Reading board…' : 'Search'}</button></div>
          </form><div className="board-provenance"><a href="https://www.arbeitnow.com/api/job-board-api" target="_blank" rel="noreferrer">Source: Arbeitnow public API ↗</a><p>{board ? `${board.jobs.length} shown · ${board.matching_count} matches · ${board.scanned_count} valid listings on latest page` : 'Latest public page only — not a search of every opening.'}</p>{board && <p>Fetched {date(board.fetched_at)}. Cached briefly; employer status not verified.</p>}</div>
          <div className="board-results" aria-busy={searching}>{searching && <p className="desk-empty">Reading the public source…</p>}{!searching && board?.jobs.length === 0 && <p className="desk-empty">No matches on this page. Broaden the filters or paste a listing from another source.</p>}{board?.jobs.map((job, index) => <article className="board-job" key={`${job.url}-${index}`}><div><p className="job-company">{job.company}</p><h3>{job.title}</h3><p>{job.location} · {job.remote === true ? 'Remote tag' : job.remote === false ? 'No remote tag' : 'Remote unknown'}</p><small>Published {date(job.published_at)}</small><details><summary>Read listing</summary><p className="listing-text">{job.description}</p>{job.url && <a href={job.url} target="_blank" rel="noreferrer">Original listing ↗</a>}</details></div><button className="add-job" aria-label={`Add ${job.title}`} disabled={working || jobs.length >= MAX_JOBS} onClick={() => add(job)}><Plus size={17} /></button></article>)}</div></> :
          <form className="paste-form" onSubmit={e => { e.preventDefault(); add({ ...paste, title: paste.title || 'Untitled opportunity', company: paste.company || 'Not supplied' }); }}>
            <p>Paste public listing text, not your CV or private correspondence. Text is sent to this service only when you run a review.</p>
            <label>Job title<input value={paste.title} maxLength={200} onChange={e => setPaste({ ...paste, title: e.target.value })} /></label>
            <label>Company<input value={paste.company} maxLength={200} onChange={e => setPaste({ ...paste, company: e.target.value })} /></label>
            <label>Original URL <span>(optional; never fetched)</span><input type="url" value={paste.url} onChange={e => setPaste({ ...paste, url: e.target.value })} placeholder="https://…" /></label>
            <label>Listing text<textarea required rows={11} maxLength={MAX_TEXT} value={paste.description} onChange={e => setPaste({ ...paste, description: e.target.value })} placeholder="Paste the full job description, including requirements and location restrictions." /></label>
            <button className="desk-button primary" disabled={working || !paste.description.trim() || jobs.length >= MAX_JOBS}><Plus size={15} />Add to review</button></form>}
        </section>
        <section className="desk-panel review-queue" aria-label="Review queue"><div className="panel-heading"><h2>Listings to review</h2><span className="queue-count">{jobs.length} / {MAX_JOBS}</span></div>
          <div className="queue-body"><label>Skills to look for <span>(comma-separated)</span><input disabled={working} value={skills} onChange={e => { changed(); setSkills(e.target.value); }} placeholder="Python, TypeScript, PostgreSQL" /></label><p className="field-note">Your own list. Mentions are not necessarily requirements; missing text does not mean you lack a skill.</p>
          {jobs.length === 0 ? <div className="queue-empty"><FileText size={28} /><h3>Add a listing to begin</h3><p>Use the + button beside a public listing,<br />or choose Paste a listing to add your own.</p></div> : <ol className="queue-list">{jobs.map((job, index) => <li key={index}><div><strong>{job.title}</strong><span>{job.company}</span></div><button disabled={working} aria-label={`Remove ${job.title}`} onClick={() => { changed(); setJobs(jobs.filter((_, i) => i !== index)); }}><X size={16} /></button></li>)}</ol>}
          <button className="desk-button primary review-button" disabled={!jobs.length || working} onClick={() => void review()}>{working ? 'Processing…' : 'Review evidence'}<ArrowUpRight size={17} /></button>
          <p className="field-note">Canonical-URL duplicates are grouped. Changed duplicate text is kept, not silently discarded.</p>
          <div className="workspace-actions"><button disabled={working} onClick={() => { try { localStorage.setItem(STORAGE, workspace()); setNotice('Saved only in this browser on this device. Shared devices are not private.'); } catch { setError('This browser could not save the workspace. Export JSON instead.'); } }}>Save on this device</button><button disabled={working} onClick={() => { try { const raw = localStorage.getItem(STORAGE); if (!raw) throw new Error('No saved workspace on this device.'); restore(raw); } catch (e) { setError(e instanceof Error ? e.message : 'Restore failed.'); } }}>Restore saved</button><button onClick={() => { localStorage.removeItem(STORAGE); setNotice('Saved device copy removed. Current queue is unchanged.'); }}>Forget saved copy</button></div>
          <div className="workspace-actions"><button disabled={!jobs.length || working} onClick={() => download(workspace(), 'relay-workspace.json', 'application/json')}>Export workspace JSON</button><button disabled={working} onClick={() => fileRef.current?.click()}>Import workspace JSON</button><input ref={fileRef} type="file" accept=".json,application/json" hidden onChange={async e => { const file = e.target.files?.[0]; e.target.value = ''; if (!file) return; try { if (file.size > MAX_FILE) throw new Error('Workspace exceeds the 2 MB limit.'); restore(await file.text()); } catch (err) { setError(err instanceof Error ? err.message : 'Import failed.'); } }} /></div></div>
        </section>
      </div>
      {report && <section className="desk-panel evidence-panel" aria-label="Evidence results"><div className="panel-heading"><div><h2><span>04</span> Evidence, with the receipts</h2><p>Reviewed {date(report.reviewed_at)} · No eligibility decision or application submitted.</p></div><button className="desk-button" disabled={working} onClick={() => void exportMarkdown()}><ArrowDownToLine size={16} />Export Markdown</button></div>
        {report.duplicates.length > 0 && <details className="duplicate-notice"><summary>{report.duplicates.length} duplicate record(s) grouped — inspect alternate text</summary>{report.duplicates.map((dupe, i) => <div key={i}><strong>{dupe.title}: {dupe.content_changed ? 'text changed' : 'same text'}</strong><pre>{dupe.alternate.source_text}</pre></div>)}</details>}
        <div className="comparison-scroll"><table className="comparison"><thead><tr><th>Listing</th>{payload().skills.map((skill, i) => <th key={`${skill}-${i}`}>{skill}</th>)}<th>Inspect</th></tr></thead><tbody>{report.jobs.map((job, index) => <tr key={job.id} className={index === selected ? 'selected' : ''}><td><strong>{job.title}</strong><small>{job.company}</small></td>{job.skill_evidence.map(item => <td key={item.skill}><span className={item.status === 'mentioned' ? 'mention' : 'not-found'}>{item.status === 'mentioned' ? 'Mentioned' : 'Not found'}</span></td>)}<td><button className="desk-button" onClick={() => setSelected(index)} aria-pressed={selected === index}>Read evidence</button></td></tr>)}</tbody></table></div>
        {current && <div className="evidence-detail"><div><p className="eyebrow">SELECTED LISTING</p><h3>{current.title}</h3><p>{current.company} · {current.location}</p><p className="field-note">{current.source}</p>{current.url && <a href={current.url} target="_blank" rel="noreferrer">Open original listing <ArrowUpRight size={14} /></a>}
          {current.skill_evidence.map(item => <div className="skill-evidence" key={item.skill}><h4>{item.skill} <span className={item.status === 'mentioned' ? 'mention' : 'not-found'}>{item.status === 'mentioned' ? 'Mentioned' : 'Not found'}</span></h4>{item.evidence.map(q => <blockquote key={q.line}><small>LINE {q.line}</small>{q.text}</blockquote>)}{!item.evidence.length && <p>No literal mention found in the supplied text.</p>}</div>)}
          <h4 className="signal-title">Other wording to check</h4>{Object.entries(current.signals).map(([name, quotes]) => <details className="signal" key={name}><summary>{name.replace(/_/g, ' ')} · {quotes.length ? 'quoted wording' : 'not found'}</summary>{quotes.map(q => <blockquote key={q.line}><small>LINE {q.line}</small>{q.text}</blockquote>)}{!quotes.length && <p>Confirm this with the employer; absence is not an answer.</p>}</details>)}
          <div className="verification"><h4>Before you apply</h4><ul>{current.questions.map(q => <li key={q}>{q}</li>)}</ul></div></div>
          <div className="source-document"><h4>Source text</h4><p>HTML removed; whitespace normalized. Line numbers below match every quote.</p><ol>{current.source_text.split('\n').map((line, index) => <li key={index}>{line}</li>)}</ol><details><summary>Content fingerprint (SHA-256)</summary><code>{current.source_sha256}</code><p>Identifies this text snapshot. Does not certify the employer or the listing.</p></details></div>
        </div>}
      </section>}
      <details className="mcp-guide"><summary><Terminal size={17} /> Use the same workflow through MCP <span>Developer notes</span></summary><div><p>The official MCP SDK exposes four read-only tools: <code>search_job_board</code>, <code>summarize_job_board</code>, <code>review_job_evidence</code>, <code>export_job_review</code>. The browser uses the same services through HTTP; it is not an AI agent.</p><p>Streamable HTTP endpoint: <code>{endpoint}</code></p><p>Local stdio, from the backend directory after installing requirements:</p><pre>python -m app.mcp.jobs_server</pre><p>No API key or paid model is needed. Public board descriptions are untrusted data, not instructions.</p></div></details>
      <footer className="desk-footer"><p><strong>Relay</strong> connects a React interface to a FastAPI service and four read-only MCP tools.</p></footer>
    </main>
  </div>;
}
