import { RupeeFlow } from "../components/rupee-flow";

function Arrow() {
  return <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M3 10h13m-5-5 5 5-5 5" /></svg>;
}

function Symbol({ path }: { path: string }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={path} /></svg>;
}

export default function Home() {
  return (
    <>
      <div className="entry-print-field" aria-hidden="true" />
      <section className="entry-hero" aria-labelledby="entry-title">
        <div className="hero-copy">
          <p className="eyebrow"><span aria-hidden="true" />Trusted reconciliation<br />for a stronger India</p>
          <p className="hero-wordmark">Reconra</p>
          <h1 id="entry-title">Every rupee should have a trail.</h1>
          <p className="hero-description">AI-assisted Razorpay settlement reconciliation<br className="desktop-break" /> with deterministic verification.</p>
          <p className="hero-sequence">Reconcile <span>|</span> Verify <span>|</span> Investigate <span>|</span> Evidence <span>|</span> Stay in control</p>
        </div>
        <RupeeFlow />
      </section>

      <section className="entry-actions" aria-label="Start with a source">
        <div className="action-grid">
          <button type="button" className="action-card action-card-primary" disabled aria-label="Run Demo Reconciliation" aria-describedby="entry-availability">
            <svg className="card-engraving" viewBox="0 0 300 140" aria-hidden="true">{Array.from({ length: 20 }, (_, i) => <path key={i} d={`M90 ${155 + i * 3}C130 ${25 + i * 3} 225 ${70 + i * 3} 320 ${-30 + i * 3}`} />)}</svg><span className="action-icon"><Symbol path="m9 6 10 6-10 6V6Z" /></span>
            <span className="action-title">Run Demo Reconciliation</span>
            <span className="action-detail">See how Reconra works</span>
            <span className="action-arrow"><Arrow /></span>
          </button>
          <button type="button" className="action-card" disabled aria-label="Import Data" aria-describedby="entry-availability">
            <svg className="card-engraving" viewBox="0 0 300 140" aria-hidden="true">{Array.from({ length: 20 }, (_, i) => <path key={i} d={`M90 ${155 + i * 3}C130 ${25 + i * 3} 225 ${70 + i * 3} 320 ${-30 + i * 3}`} />)}</svg><span className="action-icon"><Symbol path="M4 14v6h16v-6M12 3v12M7 8l5-5 5 5" /></span>
            <span className="action-title">Import Data</span>
            <span className="action-detail">Upload your settlement files</span>
            <span className="action-arrow"><Arrow /></span>
          </button>
          <button type="button" className="action-card" disabled aria-label="Sync Razorpay Test Mode" aria-describedby="entry-availability">
            <svg className="card-engraving" viewBox="0 0 300 140" aria-hidden="true">{Array.from({ length: 20 }, (_, i) => <path key={i} d={`M90 ${155 + i * 3}C130 ${25 + i * 3} 225 ${70 + i * 3} 320 ${-30 + i * 3}`} />)}</svg><span className="action-icon"><Symbol path="m10 14 4-4M8 16l-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0M16 8l1-1a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" /></span>
            <span className="action-title">Sync Razorpay Test Mode</span>
            <span className="action-detail">Connect and fetch Test Mode data</span>
            <span className="action-arrow"><Arrow /></span>
          </button>
          <blockquote className="statement-panel"><span aria-hidden="true">“</span><p>Greater financial clarity begins with an explainable trail.</p><hr /></blockquote>
        </div>
        <p className="availability-note" id="entry-availability"><strong>Entry preview</strong><span>Workflows are not available yet. No data has been processed.</span></p>
      </section>

      <section className="capability-strip" aria-label="Reconciliation principles">
        <div className="capability"><span className="capability-icon"><Symbol path="M5 4h14v16H5zM8 8h8M8 12h8M8 16h4" /></span><div><h2>Deterministic first</h2><p>Rules explain what <br />can be proven</p></div></div>
        <div className="capability"><span className="capability-icon"><Symbol path="M16 16l5 5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0ZM7 10h6M10 7v6" /></span><div><h2>Residual AI</h2><p>AI investigates only <br />ambiguous exceptions</p></div></div>
        <div className="capability"><span className="capability-icon"><Symbol path="m12 2 8 3v6c0 5-8 10-8 10S4 16 4 11V5l8-3ZM8 11l3 3 5-6" /></span><div><h2>Independent verification</h2><p>Proposals are checked <br />before financial impact</p></div></div>
        <div className="capability"><span className="capability-icon"><Symbol path="M3 12a9 9 0 1 0 18 0 9 9 0 1 0-18 0ZM8 10h8M8 14h8" /></span><div><h2>Exact tie-out</h2><p>Bank credit = <br />explained + residual</p></div></div>
      </section>

      <section className="preview-grid" aria-label="Product capability previews">
        <article className="preview-panel trail-preview">
          <header><h2>A traceable money trail</h2><span>Capability preview</span></header>
          <p className="preview-description">Connected references, from source to settlement.</p>
          <div className="source-trail"><div><Symbol path="M5 3h14v18H5zM8 7h8M8 11h8M8 15h4" /><strong>Payments</strong><span>Orders & refunds</span></div><Arrow /><div><Symbol path="M3 7h18v13H3zM2 7l10-5 10 5M7 10v7M12 10v7M17 10v7" /><strong>Settlement</strong><span>Fees & tax</span></div><Arrow /><div><Symbol path="M3 6h18v14H3zM3 10h18M15 15h3" /><strong>Bank credit</strong><span>Source evidence</span></div></div><p className="trail-footnote">SOURCE REFERENCES <span>EXACT TIE-OUT</span></p>
        </article>
        <article className="preview-panel verification-preview">
          <header><h2>Verification before impact</h2></header>
          <p className="preview-description">Every proposal passes independent checks.</p>
          <ol><li><span aria-hidden="true">01</span> Evidence</li><li><span aria-hidden="true">02</span> Agent proposal</li><li><span aria-hidden="true">03</span> Deterministic verifier</li><li><span aria-hidden="true">04</span> Risk gate</li><li><span aria-hidden="true">05</span> Human review <small>when required</small></li></ol>
        </article>
        <article className="preview-panel evidence-preview">
          <header><h2>Built for investigation</h2><span>Capability preview</span></header>
          <dl><div><dt>Source references</dt><dd>Follow the original records</dd></div><div><dt>Settlement evidence</dt><dd>Trace fees and bank credit</dd></div><div><dt>Residual evidence</dt><dd>Keep uncertainty visible</dd></div><div><dt>Verifier status</dt><dd>Checks before action</dd></div></dl>
          <p>No live reconciliation results to display.</p>
        </article>
      </section>
      <footer className="entry-footer"><span><strong>Reconra</strong> Built for clarity. Grounded in evidence.</span><span>India · Fintech · Trust · Transparency</span></footer>
    </>
  );
}
