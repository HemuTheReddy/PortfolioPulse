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
        <div className="hero-buttons">
          <Link href="/quiz" className="btn btn-primary">
            Take the Quiz →
          </Link>
          <Link href="/import" prefetch={false} className="btn btn-secondary">
            Import My Portfolio
          </Link>
        </div>
      </section>

      <section className="features">
        <div className="card feature-card">
          <div className="feature-icon">🧠</div>
          <h3>Neural Collaborative Filtering</h3>
          <p>
            NeuMF model trained on 200k+ wallet interactions identifies tokens
            that match your investment profile.
          </p>
        </div>
        <div className="card feature-card">
          <div className="feature-icon">📊</div>
          <h3>Dynamic Market Regimes</h3>
          <p>
            Real-time DynamoDB pipeline adjusts allocations based on Fear &
            Greed Index, BTC RSI and volatility.
          </p>
        </div>
        <div className="card feature-card">
          <div className="feature-icon">🛡️</div>
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
