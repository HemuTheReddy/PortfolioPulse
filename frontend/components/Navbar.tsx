"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMarketState, type MarketData, getApiErrorMessage } from "@/lib/api";

export function Navbar() {
    const [market, setMarket] = useState<MarketData | null>(null);
    const [marketError, setMarketError] = useState("");

    useEffect(() => {
        getMarketState()
            .then((data) => {
                setMarket(data);
                setMarketError("");
            })
            .catch((err: unknown) => {
                setMarketError(getApiErrorMessage(err));
            });
    }, []);

    const stateColor = market
        ? { bull: "#00FF94", bear: "#FF4444", neutral: "#FFB800", extreme_fear: "#FF4444" }[
        market.market_state
        ] || "#A0A0A0"
        : "#A0A0A0";

    return (
        <nav className="navbar-shell">
            <div className="navbar">
                <Link href="/" className="navbar-logo" aria-label="PortfolioPulse home">
                    <span className="navbar-logo-text">
                        Portfolio<span className="accent">Pulse</span>
                    </span>
                </Link>

                <div className="navbar-right">
                    {market && (
                        <div className="market-badge">
                            <span className="dot" style={{ background: stateColor }} />
                            <span className="market-label">Market State:</span>
                            <span>{market.market_state.toUpperCase()}</span>
                            <span className="market-separator" aria-hidden="true">|</span>
                            <span>F&amp;G: {market.market_metrics.fear_greed}</span>
                        </div>
                    )}
                    {!market && marketError && (
                        <div className="market-badge" title={marketError}>
                            <span className="dot" style={{ background: "#FF6B6B" }} />
                            <span>Market unavailable</span>
                        </div>
                    )}
                    <a
                        className="github-link"
                        href="https://github.com/HemuTheReddy/PortfolioPulse"
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label="PortfolioPulse GitHub repository"
                    >
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path
                                fill="currentColor"
                                d="M12 2C6.48 2 2 6.58 2 12.23c0 4.52 2.87 8.35 6.84 9.7.5.1.68-.22.68-.5 0-.24-.01-1.04-.02-1.88-2.78.62-3.37-1.21-3.37-1.21-.45-1.18-1.1-1.49-1.1-1.49-.9-.63.07-.62.07-.62 1 .07 1.52 1.05 1.52 1.05.88 1.57 2.32 1.11 2.88.85.09-.66.35-1.11.63-1.36-2.22-.26-4.56-1.14-4.56-5.08 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05A9.37 9.37 0 0 1 12 6.83c.85 0 1.71.12 2.51.36 1.9-1.32 2.74-1.05 2.74-1.05.54 1.4.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.95-2.34 4.82-4.57 5.07.36.32.67.95.67 1.92 0 1.39-.01 2.5-.01 2.84 0 .27.18.6.69.5A10.25 10.25 0 0 0 22 12.23C22 6.58 17.52 2 12 2Z"
                            />
                        </svg>
                    </a>
                </div>
            </div>
            <p className="navbar-disclaimer">
                This system identifies what historically profitable traders with your risk profile
                held during similar market conditions -- then adjusts for current market regime.
                Do not take recommendations as strict financial advice.
            </p>
        </nav>
    );
}
