"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
    getMarketState,
    getRecommendations,
    type Recommendation,
    type MarketData,
    type QuizResult,
    type RecommendResult,
} from "@/lib/api";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

/* ─── Color Palette for chart ─────────────────────────────────── */
const CHART_COLORS = [
    "#00FF94", "#00C46A", "#009C55", "#007A40", "#005C2E",
    "#FFCA28", "#FF9500", "#FF4444", "#AB47BC", "#42A5F5",
];

function tierColor(tier: string) {
    if (tier === "High Signal") return "#00FF94";
    if (tier === "Moderate") return "#FFB800";
    return "#A0A0A0";
}

function ResultsContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const isDemo = searchParams.get("demo") === "true";

    const [loading, setLoading] = useState(true);
    const [market, setMarket] = useState<MarketData | null>(null);
    const [quiz, setQuiz] = useState<QuizResult | null>(null);
    const [recs, setRecs] = useState<RecommendResult | null>(null);

    useEffect(() => {
        async function load() {
            try {
                // Try sessionStorage first (quiz flow)
                const stored = sessionStorage.getItem("portfoliopulse_results");
                if (stored && !isDemo) {
                    const data = JSON.parse(stored);
                    setMarket(data.market);
                    setQuiz(data.quiz);
                    setRecs(data.recommendations);
                    setLoading(false);
                    return;
                }

                // Demo or direct visit — generate with defaults
                const marketData = await getMarketState();
                setMarket(marketData);

                const demoRecs = await getRecommendations(
                    42,  // demo user
                    3,   // moderate risk
                    marketData.market_state
                );
                setQuiz({
                    risk_score: 3,
                    risk_label: "Moderate",
                    proxy_user: { user_idx: 42, avg_hold_days: 30, token_diversity: 10, risk_tier: "moderate", pool_size: 100 },
                });
                setRecs(demoRecs);
            } catch (err) {
                console.error("Failed to load results:", err);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [isDemo]);

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
                <p>Loading your personalized portfolio…</p>
            </div>
        );
    }

    if (!recs || !market || !quiz) {
        return (
            <div className="loading">
                <p>No results found.</p>
                <button className="btn btn-primary" onClick={() => router.push("/quiz")}>
                    Take the Quiz →
                </button>
            </div>
        );
    }

    const recommendations = recs.recommendations;

    /* ─── CSV Export ─────────────────────────────────────────── */
    const exportCSV = () => {
        const header = "Rank,Symbol,Name,Weight %,Tier,Confidence,Price USD,24h Change %\n";
        const rows = recommendations
            .map(
                (r) =>
                    `${r.rank},${r.symbol},${r.name},${r.weight},${r.tier},${r.confidence}%,${r.price_usd ?? "N/A"},${r.price_change_24h?.toFixed(2) ?? "N/A"}`
            )
            .join("\n");
        const blob = new Blob([header + rows], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `portfoliopulse_portfolio_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    /* ─── Regime banner color ───────────────────────────────── */
    const bannerBg = {
        bull: "rgba(0,255,148,0.1)",
        bear: "rgba(255,68,68,0.1)",
        neutral: "rgba(255,184,0,0.1)",
        extreme_fear: "rgba(255,68,68,0.15)",
    }[market.market_state] || "rgba(255,184,0,0.1)";

    const bannerBorder = {
        bull: "#00FF94",
        bear: "#FF4444",
        neutral: "#FFB800",
        extreme_fear: "#FF4444",
    }[market.market_state] || "#FFB800";

    return (
        <div className="results-container">
            {/* ─── Stats Row ───────────────────────────────────── */}
            <div className="stats-row">
                <div className="card stat-card">
                    <div className="stat-label">Market State</div>
                    <div className="stat-value" style={{ fontSize: 22 }}>
                        {market.market_state.toUpperCase()}
                    </div>
                    <div className="stat-sub">Source: {market.source}</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Risk Score</div>
                    <div className="stat-value">{quiz.risk_score}/5</div>
                    <div className="stat-sub">{quiz.risk_label}</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Avg Affinity</div>
                    <div className="stat-value">
                        {Math.round(
                            recommendations.reduce((a, r) => a + r.confidence, 0) /
                            recommendations.length
                        )}
                        %
                    </div>
                    <div className="stat-sub">AI profile match</div>
                </div>
            </div>

            {/* ─── Regime Banner ───────────────────────────────── */}
            <div
                className="regime-banner"
                style={{ background: bannerBg, borderLeft: `4px solid ${bannerBorder}` }}
            >
                {market.regime_message}
            </div>

            {/* ─── Main Grid ───────────────────────────────────── */}
            <div className="results-grid">
                {/* Left: Recommendation Cards */}
                <div>
                    <h2 className="results-section-title">Your Allocations</h2>
                    {recommendations.map((r) => (
                        <div className="card rec-card" key={r.item_idx}>
                            <div className="rec-top">
                                <div className="rec-rank">#{r.rank}</div>

                                {r.logo_url ? (
                                    <img
                                        className="rec-logo"
                                        src={r.logo_url}
                                        alt={r.symbol}
                                        onError={(e) => {
                                            (e.target as HTMLImageElement).style.display = "none";
                                        }}
                                    />
                                ) : (
                                    <div className="rec-logo-fallback">
                                        {r.symbol.slice(0, 2)}
                                    </div>
                                )}

                                <div className="rec-info">
                                    <h4>
                                        <a
                                            href={r.coingecko_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            style={{ color: "var(--text-primary)", textDecoration: "none" }}
                                            title="View on CoinGecko"
                                        >
                                            {r.name} ({r.symbol}) ↗
                                        </a>
                                    </h4>
                                    <p>{r.explanation}</p>
                                </div>
                            </div>

                            <div className="rec-bottom">
                                <div style={{ display: "flex", flexWrap: "wrap", gap: "12px 20px", alignItems: "center", flex: 1, minWidth: 0 }}>
                                    <span
                                        className="tier-badge"
                                        style={{ color: tierColor(r.tier), borderColor: tierColor(r.tier) }}
                                    >
                                        {r.tier}
                                    </span>
                                    {r.category && (
                                        <span style={{
                                            fontSize: 11,
                                            color: "var(--text-secondary)",
                                            background: "rgba(255,255,255,0.05)",
                                            padding: "2px 8px",
                                            borderRadius: 4,
                                        }}>
                                            {r.category}
                                        </span>
                                    )}
                                    <span className="confidence-bar" style={{ color: "var(--text-secondary)" }} title="AI affinity: how strongly the model matches this token to your profile (0–100%)">
                                        {r.confidence}% affinity
                                    </span>
                                    {r.price_usd && (
                                        <span style={{ fontSize: 13, fontFamily: "JetBrains Mono", color: "var(--text-secondary)" }}>
                                            ${r.price_usd.toLocaleString()}{" "}
                                            {r.price_change_24h != null && (
                                                <span style={{ color: r.price_change_24h >= 0 ? "#00FF94" : "#FF4444" }}>
                                                    {r.price_change_24h >= 0 ? "+" : ""}
                                                    {r.price_change_24h.toFixed(1)}%
                                                </span>
                                            )}
                                        </span>
                                    )}
                                </div>
                                <span className="rec-weight">{r.weight}%</span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Right: Donut Chart */}
                <div>
                    <h2 className="results-section-title">Portfolio Breakdown</h2>
                    <div className="card chart-container">
                        {typeof window !== "undefined" && Plot && (
                            <Plot
                                data={[
                                    {
                                        values: recommendations.map((r) => r.weight),
                                        labels: recommendations.map((r) => r.symbol),
                                        type: "pie",
                                        hole: 0.6,
                                        marker: {
                                            colors: recommendations.map(
                                                (_, i) => CHART_COLORS[i % CHART_COLORS.length]
                                            ),
                                            line: { color: "#0A0A0A", width: 2 },
                                        },
                                        textinfo: "percent",
                                        textposition: "inside",
                                        textfont: { color: "#FFFFFF", size: 12, family: "Inter", weight: 600 },
                                        hovertemplate: "<b>%{label}</b><br>Weight: %{value}%<extra></extra>",
                                    },
                                ]}
                                layout={{
                                    autosize: true,
                                    height: 400,
                                    showlegend: false,
                                    paper_bgcolor: "transparent",
                                    plot_bgcolor: "transparent",
                                    margin: { l: 20, r: 20, t: 20, b: 20 },
                                }}
                                config={{ displayModeBar: false, responsive: true }}
                                style={{ width: "100%", maxWidth: 440 }}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* ─── Explainability ────────────────────────────────── */}
            <div className="explain-section">
                <h2 className="results-section-title">How This Works</h2>
                <div className="explain-grid">
                    <div className="card explain-card">
                        <div className="icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                                <path d="M7 10a2 2 0 1 0-1.73-3h-.02A2 2 0 0 0 7 10Zm10 0a2 2 0 1 0 1.73-3h.02A2 2 0 0 0 17 10ZM12 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm-5 8a2 2 0 1 0-1.73-3h-.02A2 2 0 0 0 7 15Zm10 0a2 2 0 1 0 1.73-3h.02A2 2 0 0 0 17 15Zm-5 6a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm-3.6-9.1 2-1.4m3.2 0 2 1.4m-3.6 2.2v2.8m-4.6-5.7v2.8m9.2-2.8v2.8" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h4>NeuMF Inference</h4>
                        <p>
                            Neural Collaborative Filtering scores every token against your wallet
                            profile. Top {recommendations.length} are selected by affinity score.
                        </p>
                    </div>
                    <div className="card explain-card">
                        <div className="icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                                <path d="M4 20h16M7 17v-5m5 5V8m5 9v-7" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
                            </svg>
                        </div>
                        <h4>Regime Adjustment</h4>
                        <p>{recs.regime_explanation}</p>
                    </div>
                    <div className="card explain-card">
                        <div className="icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                                <path d="M12 4v3m-7 4h14M8 11l-3 6h6l-3-6Zm8 0-3 6h6l-3-6ZM12 7v11m-3 2h6" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h4>Risk Constraints</h4>
                        <p>
                            Risk score {quiz.risk_score}/5 ({quiz.risk_label}) applies max
                            single-asset caps and stablecoin floors via mean-variance optimization.
                        </p>
                    </div>
                </div>
            </div>

            {/* ─── Signal Legend + Actions ───────────────────────── */}
            <div className="signal-legend">
                <div className="signal-item">
                    <div className="signal-dot" style={{ background: "#00FF94" }} />
                    High Signal (affinity &gt; 60%)
                </div>
                <div className="signal-item">
                    <div className="signal-dot" style={{ background: "#FFB800" }} />
                    Moderate (40–60%)
                </div>
                <div className="signal-item">
                    <div className="signal-dot" style={{ background: "#A0A0A0" }} />
                    Lower Signal (affinity &lt; 40%)
                </div>
            </div>

            <div className="actions" style={{ justifyContent: "center" }}>
                <button className="btn btn-primary" onClick={exportCSV}>
                    Export CSV
                </button>
                <button className="btn btn-secondary" onClick={() => router.push("/quiz")}>
                    Retake Quiz
                </button>
                <button className="btn btn-secondary" onClick={() => router.push("/")}>
                    Home
                </button>
            </div>

        </div>
    );
}

export default function ResultsPage() {
    return (
        <Suspense
            fallback={
                <div className="loading">
                    <div className="spinner" />
                    <p>Loading results…</p>
                </div>
            }
        >
            <ResultsContent />
        </Suspense>
    );
}
