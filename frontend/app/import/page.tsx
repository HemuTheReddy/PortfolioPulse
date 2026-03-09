"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { Suspense } from "react";
import { importPortfolio } from "@/lib/api";
import type { UnifiedAsset } from "@/lib/DataIngestion/types";
import { mergePortfolios } from "@/lib/DataIngestion/merge";
import { parseExchangeCSV } from "@/lib/DataIngestion/csvParser";
import { fetchMobulaPortfolio } from "@/lib/DataIngestion/mobula";

const ImportWalletConnect = dynamic(
    () =>
        import("@/components/ImportWalletConnect").then((mod) => mod.ImportWalletConnect),
    {
        ssr: false,
        loading: () => (
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div className="spinner" style={{ width: 20, height: 20 }} />
                <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                    Loading wallet connection…
                </span>
            </div>
        ),
    }
);

/* ── Coin list for manual entry ─────────────────────────────────── */
const COIN_OPTIONS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE",
    "DOT", "MATIC", "LINK", "UNI", "ATOM", "LTC", "FIL", "NEAR",
    "APT", "ARB", "OP", "AAVE", "MKR", "GRT", "INJ", "RENDER",
    "FTM", "ALGO", "VET", "SAND", "MANA", "AXS", "SUI", "CRV",
    "SNX", "COMP", "SUSHI", "1INCH", "LDO", "RPL", "ENS",
];

const inputStyle: React.CSSProperties = {
    padding: "12px 16px",
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    color: "var(--text-primary)",
    fontSize: 14,
    width: "100%",
};

/* ── Portfolio Preview Component ──────────────────────────────── */
function PortfolioPreview({
    assets,
    totalUsd,
}: {
    assets: UnifiedAsset[];
    totalUsd: number;
}) {
    if (assets.length === 0) return null;

    return (
        <div className="card" style={{ padding: 20, marginTop: 24 }}>
            <h3 style={{ color: "var(--text-primary)", margin: "0 0 16px 0", fontSize: 16 }}>
                📊 Portfolio Preview — {assets.length} asset{assets.length !== 1 ? "s" : ""}
            </h3>

            <div style={{ maxHeight: 260, overflowY: "auto" }}>
                {assets.map((a) => (
                    <div
                        key={`${a.symbol}-${a.source}`}
                        style={{
                            display: "grid",
                            gridTemplateColumns: "60px 1fr 90px 80px",
                            alignItems: "center",
                            padding: "8px 0",
                            borderBottom: "1px solid var(--border)",
                            fontSize: 14,
                        }}
                    >
                        <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>
                            {a.symbol}
                        </span>
                        <span style={{ color: "var(--text-secondary)" }}>
                            {a.amount.toLocaleString(undefined, { maximumFractionDigits: 6 })}
                        </span>
                        <span
                            style={{
                                fontFamily: "JetBrains Mono, monospace",
                                color: "var(--accent)",
                                fontSize: 13,
                            }}
                        >
                            {a.valueUsd > 0
                                ? `$${a.valueUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                : "—"}
                        </span>
                        <span
                            style={{
                                fontSize: 11,
                                color: "var(--text-secondary)",
                                background: "rgba(255,255,255,0.05)",
                                padding: "2px 6px",
                                borderRadius: 4,
                                textAlign: "center",
                            }}
                        >
                            {a.location}
                        </span>
                    </div>
                ))}
            </div>

            {totalUsd > 0 && (
                <div style={{ marginTop: 12, textAlign: "right", fontSize: 15, fontWeight: 700, color: "var(--accent)" }}>
                    Total: ${totalUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
            )}
        </div>
    );
}

/* ── Source Status Badge ────────────────────────────────────────── */
function SourceBadge({ count, label }: { count: number; label: string }) {
    if (count === 0) return <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>Not connected</span>;
    return (
        <span style={{ color: "var(--accent)", fontSize: 13, fontWeight: 600 }}>
            ✅ Found {count} {label}
        </span>
    );
}

/* ── Main Import Page Content ─────────────────────────────────── */
function ImportContent() {
    const router = useRouter();

    // ── Per-source asset lists ──────────────────────────────────────
    const [manualAssets, setManualAssets] = useState<UnifiedAsset[]>([]);
    const [walletAssets, setWalletAssets] = useState<UnifiedAsset[]>([]);
    const [csvAssets, setCsvAssets] = useState<UnifiedAsset[]>([]);

    // ── UI state ────────────────────────────────────────────────────
    const [expandedSection, setExpandedSection] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingMsg, setLoadingMsg] = useState("");
    const [walletScanning, setWalletScanning] = useState(false);
    const [csvError, setCsvError] = useState("");
    const [walletError, setWalletError] = useState("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    // ── Manual entry state ──────────────────────────────────────────
    const [manualCoins, setManualCoins] = useState([{ symbol: "", amount: "" }]);

    // ── Merge all sources ───────────────────────────────────────────
    const merged = mergePortfolios(manualAssets, walletAssets, csvAssets);
    const hasAnyAsset = merged.assets.length > 0;

    // ── Manual entry handlers ───────────────────────────────────────
    const updateManualCoin = (i: number, field: "symbol" | "amount", value: string) => {
        const copy = [...manualCoins];
        copy[i] = { ...copy[i], [field]: value };
        setManualCoins(copy);
    };

    const applyManualEntry = useCallback(() => {
        const valid = manualCoins.filter((c) => c.symbol && parseFloat(c.amount) > 0);
        setManualAssets(
            valid.map((c) => ({
                symbol: c.symbol.toUpperCase(),
                amount: parseFloat(c.amount),
                valueUsd: 0,
                source: "manual" as const,
                location: "Manual",
            }))
        );
    }, [manualCoins]);

    // Auto-apply manual entries when they change
    useEffect(() => {
        applyManualEntry();
    }, [applyManualEntry]);

    // ── WalletConnect handler ───────────────────────────────────────
    const handleWalletConnected = async (address: string) => {
        if (walletAssets.length > 0) return; // already scanned
        setWalletScanning(true);
        setWalletError("");
        try {
            const assets = await fetchMobulaPortfolio(address);
            setWalletAssets(assets);
        } catch (err: unknown) {
            const errorText = err instanceof Error ? err.message : "";
            const msg = errorText.includes("Failed to fetch") || errorText.includes("Network request failed")
                ? "Mobula API unreachable. Check NEXT_PUBLIC_MOBULA_KEY and network."
                : err instanceof Error ? err.message : "Wallet scan failed.";
            setWalletError(msg);
        } finally {
            setWalletScanning(false);
        }
    };

    // ── CSV handler ─────────────────────────────────────────────────
    const handleCSV = async (file: File) => {
        setCsvError("");
        try {
            const assets = await parseExchangeCSV(file);
            if (assets.length === 0) {
                setCsvError("No valid holdings found in CSV.");
                return;
            }
            setCsvAssets(assets);
        } catch (err: unknown) {
            setCsvError(err instanceof Error ? err.message : "CSV parse error.");
        }
    };

    // ── Submit to AI pipeline ───────────────────────────────────────
    const submit = async () => {
        if (!hasAnyAsset) return;
        setLoading(true);
        setLoadingMsg("Analyzing your portfolio & generating recommendations…");

        try {
            const result = await importPortfolio(
                merged.assets.map((a) => ({ symbol: a.symbol, amount: a.amount }))
            );

            sessionStorage.setItem(
                "portfoliopulse_results",
                JSON.stringify({
                    quiz: {
                        risk_score: result.risk_score,
                        risk_label: result.risk_label,
                        proxy_user: result.proxy_user,
                    },
                    market: result.market,
                    recommendations: {
                        recommendations: result.recommendations,
                        regime_explanation: result.regime_explanation,
                        market_state: result.market.market_state,
                        risk_score: result.risk_score,
                    },
                })
            );
            router.push("/results");
        } catch (err: unknown) {
            const errorText = err instanceof Error ? err.message : "";
            const msg = errorText.includes("Failed to fetch") || errorText.includes("Network request failed")
                ? "Backend unavailable. Make sure the API server is running (e.g. uvicorn on port 8000)."
                : "Something went wrong. Please try again.";
            alert(msg);
            setLoading(false);
        }
    };

    // ── Loading overlay ─────────────────────────────────────────────
    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
                <p>{loadingMsg}</p>
            </div>
        );
    }

    const toggle = (section: string) =>
        setExpandedSection(expandedSection === section ? null : section);

    return (
        <div className="quiz-container" style={{ maxWidth: 780 }}>
            <h2 className="quiz-question" style={{ textAlign: "center" }}>
                Build Your Portfolio
            </h2>
            <p className="quiz-subtitle" style={{ textAlign: "center" }}>
                Connect your accounts, wallets, or upload data. We merge everything
                into one unified view for AI analysis.
            </p>

            {/* ── WalletConnect ─────────────────────────────────────────── */}
            <div className="card" style={{ padding: 20, marginBottom: 12, cursor: "pointer" }}>
                <div
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    onClick={() => toggle("wallet")}
                >
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ fontSize: 24 }}>🦊</span>
                        <div>
                            <h4 style={{ color: "var(--text-primary)", margin: 0 }}>Connect Wallet</h4>
                            <SourceBadge count={walletAssets.length} label="tokens" />
                        </div>
                    </div>
                    <span style={{ color: "var(--text-secondary)" }}>
                        {expandedSection === "wallet" ? "▲" : "▼"}
                    </span>
                </div>

                {expandedSection === "wallet" && (
                    <div style={{ marginTop: 16 }} onClick={(e) => e.stopPropagation()}>
                        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginBottom: 12 }}>
                            Connect MetaMask, Coinbase Wallet, or any WalletConnect-compatible wallet.
                            We scan all chains automatically via Mobula.
                        </p>

                        <ImportWalletConnect
                            walletScanning={walletScanning}
                            walletAssetsCount={walletAssets.length}
                            onConnected={handleWalletConnected}
                            onDisconnected={() => setWalletAssets([])}
                        />

                        {walletError && (
                            <div style={{
                                marginTop: 8, padding: "8px 12px",
                                background: "rgba(255,68,68,0.08)", border: "1px solid rgba(255,68,68,0.3)",
                                borderRadius: 8, fontSize: 13, color: "#FF6B6B",
                            }}>
                                ⚠️ {walletError}
                            </div>
                        )}

                        <div style={{
                            marginTop: 12, padding: "8px 12px",
                            background: "rgba(0,255,148,0.05)", border: "1px solid rgba(0,255,148,0.15)",
                            borderRadius: 8, fontSize: 12, color: "var(--text-secondary)",
                        }}>
                            🔒 We only read your public address — no private key or seed phrase is ever requested.
                        </div>
                    </div>
                )}
            </div>

            {/* ── CSV Upload ────────────────────────────────────────────── */}
            <div className="card" style={{ padding: 20, marginBottom: 12, cursor: "pointer" }}>
                <div
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    onClick={() => toggle("csv")}
                >
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ fontSize: 24 }}>📄</span>
                        <div>
                            <h4 style={{ color: "var(--text-primary)", margin: 0 }}>Upload CSV</h4>
                            <SourceBadge count={csvAssets.length} label="assets" />
                        </div>
                    </div>
                    <span style={{ color: "var(--text-secondary)" }}>
                        {expandedSection === "csv" ? "▲" : "▼"}
                    </span>
                </div>

                {expandedSection === "csv" && (
                    <div style={{ marginTop: 16 }}>
                        <p style={{ color: "var(--text-secondary)", fontSize: 13, marginBottom: 12 }}>
                            Export your portfolio CSV from any exchange (Coinbase, Binance, Kraken, etc.)
                            and drop it here. <strong>The file is parsed entirely in your browser</strong> — it never
                            leaves your device.
                        </p>

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".csv"
                            style={{ display: "none" }}
                            onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) handleCSV(file);
                            }}
                        />

                        {/* Drop zone */}
                        <div
                            onClick={() => fileInputRef.current?.click()}
                            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                            onDrop={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                const file = e.dataTransfer.files?.[0];
                                if (file) handleCSV(file);
                            }}
                            style={{
                                border: "2px dashed var(--border)",
                                borderRadius: 12,
                                padding: "28px 20px",
                                textAlign: "center",
                                cursor: "pointer",
                                transition: "border-color 0.2s",
                            }}
                        >
                            <div style={{ fontSize: 28, marginBottom: 8 }}>📁</div>
                            <p style={{ color: "var(--text-secondary)", fontSize: 13, margin: 0 }}>
                                {csvAssets.length > 0
                                    ? `✅ ${csvAssets.length} assets loaded. Drop another file to replace.`
                                    : "Drag & drop a CSV here, or click to browse"}
                            </p>
                        </div>

                        {csvError && (
                            <div style={{
                                marginTop: 8, padding: "8px 12px",
                                background: "rgba(255,68,68,0.08)", border: "1px solid rgba(255,68,68,0.3)",
                                borderRadius: 8, fontSize: 13, color: "#FF6B6B",
                            }}>
                                ⚠️ {csvError}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* ── Manual Entry ──────────────────────────────────────────── */}
            <div className="card" style={{ padding: 20, marginBottom: 12, cursor: "pointer" }}>
                <div
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    onClick={() => toggle("manual")}
                >
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ fontSize: 24 }}>✏️</span>
                        <div>
                            <h4 style={{ color: "var(--text-primary)", margin: 0 }}>Manual Entry</h4>
                            <SourceBadge count={manualAssets.length} label="coins" />
                        </div>
                    </div>
                    <span style={{ color: "var(--text-secondary)" }}>
                        {expandedSection === "manual" ? "▲" : "▼"}
                    </span>
                </div>

                {expandedSection === "manual" && (
                    <div style={{ marginTop: 16 }}>
                        {manualCoins.map((coin, i) => (
                            <div
                                key={i}
                                style={{
                                    display: "grid",
                                    gridTemplateColumns: "1fr 120px 40px",
                                    gap: 12,
                                    marginBottom: 12,
                                    alignItems: "center",
                                }}
                            >
                                <select
                                    value={coin.symbol}
                                    onChange={(e) => updateManualCoin(i, "symbol", e.target.value)}
                                    style={inputStyle}
                                >
                                    <option value="">Select token…</option>
                                    {COIN_OPTIONS.map((s) => (
                                        <option key={s} value={s}>{s}</option>
                                    ))}
                                </select>

                                <input
                                    type="number"
                                    placeholder="Amount"
                                    value={coin.amount}
                                    onChange={(e) => updateManualCoin(i, "amount", e.target.value)}
                                    style={inputStyle}
                                />

                                {i > 0 && (
                                    <button
                                        onClick={() => setManualCoins(manualCoins.filter((_, idx) => idx !== i))}
                                        style={{
                                            width: 36, height: 36, borderRadius: 8,
                                            background: "transparent", border: "1px solid var(--border)",
                                            color: "#FF4444", cursor: "pointer", fontSize: 16,
                                        }}
                                    >
                                        ✕
                                    </button>
                                )}
                            </div>
                        ))}

                        <button
                            className="btn btn-secondary"
                            style={{ fontSize: 13 }}
                            onClick={() => setManualCoins([...manualCoins, { symbol: "", amount: "" }])}
                        >
                            + Add Another Coin
                        </button>
                    </div>
                )}
            </div>

            {/* ── Portfolio Preview ─────────────────────────────────────── */}
            <PortfolioPreview assets={merged.assets} totalUsd={merged.totalValueUsd} />

            {/* ── Action Buttons ────────────────────────────────────────── */}
            <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
                <button
                    className="btn btn-primary"
                    onClick={submit}
                    disabled={!hasAnyAsset}
                    style={{
                        opacity: hasAnyAsset ? 1 : 0.4,
                        flex: 1,
                        fontSize: 15,
                    }}
                >
                    🧠 Analyze Total Portfolio →
                </button>
            </div>

            <div style={{ marginTop: 16 }}>
                <button className="btn btn-secondary" onClick={() => router.push("/")}>
                    ← Back
                </button>
            </div>
        </div>
    );
}

/* ── Page Wrapper ──────────────────────────────────────────────── */
export default function ImportPage() {
    return (
        <Suspense
            fallback={
                <div className="loading">
                    <div className="spinner" />
                    <p>Loading import page…</p>
                </div>
            }
        >
            <ImportContent />
        </Suspense>
    );
}
