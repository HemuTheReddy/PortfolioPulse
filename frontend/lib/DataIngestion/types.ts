/**
 * DataIngestion/types.ts
 *
 * Shared interfaces for the 3-pillar portfolio ingestion system.
 * All data sources (WalletConnect, CSV, Manual) normalize
 * their output into UnifiedAsset before merging.
 */

export type AssetSource = "wallet" | "csv" | "manual";

export interface UnifiedAsset {
    /** Token ticker, always uppercase. e.g. "ETH", "BTC" */
    symbol: string;
    /** Raw token balance */
    amount: number;
    /** Current USD value (amount × price). 0 if price unknown. */
    valueUsd: number;
    /** Which pillar contributed this asset */
    source: AssetSource;
    /** Human-readable origin: "MetaMask", "kraken_export.csv", "Manual" */
    location: string;
}

export interface UnifiedPortfolio {
    assets: UnifiedAsset[];
    totalValueUsd: number;
    lastUpdated: string;   // ISO 8601
    sources: AssetSource[]; // which pillars contributed
}
