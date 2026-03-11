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
        <nav className="navbar">
            <Link href="/" className="navbar-logo">
                <span>
                    Portfolio <span className="accent">Pulse</span>
                </span>
            </Link>

            {market && (
                <div className="market-badge">
                    <span className="dot" style={{ background: stateColor }} />
                    {market.emoji} {market.market_state.toUpperCase()} ·
                    F&G: {market.market_metrics.fear_greed}
                </div>
            )}
            {!market && marketError && (
                <div className="market-badge" title={marketError}>
                    <span className="dot" style={{ background: "#FF6B6B" }} />
                    Market unavailable
                </div>
            )}
        </nav>
    );
}
