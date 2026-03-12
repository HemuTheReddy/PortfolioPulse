import Link from "next/link";

export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>
          AI-Powered<br />
          <span className="gradient-text">Crypto Portfolio</span><br />
          Advisor
        </h1>
        <p>
          Personalized token recommendations backed by neural collaborative
          filtering and real-time market regime analysis.
        </p>
        <div className="hero-prompts">
          <div className="hero-prompt-card hero-prompt-quiz">
            <p className="hero-prompt-title">No portfolio but still want recommendations?</p>
            <p className="hero-prompt-subtitle">
              Start with a quick risk quiz and we will generate a personalized allocation.
            </p>
            <Link href="/quiz" className="btn btn-primary">
              Take the Risk Quiz →
            </Link>
          </div>
          <div className="hero-prompt-card hero-prompt-import" style={{ alignItems: 'flex-start', textAlign: 'left' }}>
            <p className="hero-prompt-title" style={{ textAlign: 'left' }}>Have existing coins?</p>
            <p className="hero-prompt-subtitle" style={{ textAlign: 'left' }}>
              Import your holdings to tailor recommendations around your current portfolio.
            </p>
            <Link href="/import" prefetch={false} className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}>
              Import My Portfolio →
            </Link>
          </div>
        </div>
      </section>

      <section className="features">
        <div className="card feature-card">
          <div className="feature-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M7 10a2 2 0 1 0-1.73-3h-.02A2 2 0 0 0 7 10Zm10 0a2 2 0 1 0 1.73-3h.02A2 2 0 0 0 17 10ZM12 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm-5 8a2 2 0 1 0-1.73-3h-.02A2 2 0 0 0 7 15Zm10 0a2 2 0 1 0 1.73-3h.02A2 2 0 0 0 17 15Zm-5 6a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm-3.6-9.1 2-1.4m3.2 0 2 1.4m-3.6 2.2v2.8m-4.6-5.7v2.8m9.2-2.8v2.8" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h3>Neural Collaborative Filtering</h3>
          <p>
            NeuMF model trained on 200k+ wallet interactions identifies tokens
            that match your investment profile.
          </p>
        </div>
        <div className="card feature-card">
          <div className="feature-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M4 20h16M7 17v-5m5 5V8m5 9v-7" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
            </svg>
          </div>
          <h3>Dynamic Market Regimes</h3>
          <p>
            Real-time DynamoDB pipeline adjusts allocations based on Fear &
            Greed Index, BTC RSI and volatility.
          </p>
        </div>
        <div className="card feature-card">
          <div className="feature-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M12 3 5 6v5c0 5 3.3 8.7 7 10 3.7-1.3 7-5 7-10V6l-7-3Zm0 5v8m-3-5h6" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h3>Risk-Aware Optimization</h3>
          <p>
            Mean-variance efficient frontier plus stablecoin floors ensure your
            portfolio matches your risk appetite.
          </p>
        </div>
      </section>
    </>
  );
}
