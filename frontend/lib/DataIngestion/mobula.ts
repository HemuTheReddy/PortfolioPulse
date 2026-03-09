/**
 * DataIngestion/mobula.ts
 *
 * Mobula API integration for multi-chain wallet portfolio scanning.
 * Fetches all holdings across 80+ EVM + Solana networks from a
 * single wallet address in one API call.
 *
 * Docs: https://docs.mobula.io
 * Endpoint: GET /api/1/wallet/portfolio
 */

import type { UnifiedAsset } from "./types";

const MOBULA_KEY = process.env.NEXT_PUBLIC_MOBULA_KEY || "";
const BASE_URL = "https://api.mobula.io/api/1/wallet/portfolio";

/** Minimum USD value to include (filters dust tokens) */
const MIN_VALUE_USD = 1.0;

/**
 * Represents a single asset in the Mobula API response.
 * Only the fields we use are typed here.
 */
interface MobulaAsset {
    asset: {
        name: string;
        symbol: string;
        contract_address: string;
    };
    token_balance: number;
    price: number;
    estimated_balance: number;  // USD value = price × balance
}

interface MobulaResponse {
    data: {
        total_wallet_balance: number;
        assets: MobulaAsset[];
    };
}

/**
 * Fetch a wallet's complete multi-chain portfolio from Mobula.
 *
 * @param address  EVM (0x…) or Solana wallet address
 * @returns        Normalized UnifiedAsset[] sorted by USD value
 */
export async function fetchMobulaPortfolio(
    address: string
): Promise<UnifiedAsset[]> {
    if (!MOBULA_KEY) {
        throw new Error(
            "NEXT_PUBLIC_MOBULA_KEY not set. Get a free key at https://admin.mobula.fi"
        );
    }

    const url = new URL(BASE_URL);
    url.searchParams.set("wallet", address);
    url.searchParams.set("fetchAllChains", "true");
    url.searchParams.set("filterSpam", "true");
    url.searchParams.set("cache", "true");

    const res = await fetch(url.toString(), {
        headers: {
            Authorization: MOBULA_KEY,
        },
    });

    if (!res.ok) {
        const err = await res.text().catch(() => "Unknown error");
        throw new Error(`Mobula API error (${res.status}): ${err}`);
    }

    const json: MobulaResponse = await res.json();

    if (!json.data?.assets?.length) {
        return [];
    }

    return json.data.assets
        .filter((a) => a.estimated_balance >= MIN_VALUE_USD)
        .map((a) => ({
            symbol: a.asset.symbol.toUpperCase(),
            amount: a.token_balance,
            valueUsd: Math.round(a.estimated_balance * 100) / 100,
            source: "wallet" as const,
            location: "On-Chain",
        }))
        .sort((a, b) => b.valueUsd - a.valueUsd);
}
