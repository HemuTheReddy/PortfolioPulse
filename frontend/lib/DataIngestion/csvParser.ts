/**
 * DataIngestion/csvParser.ts
 *
 * Client-side CSV parser for exchange portfolio exports.
 * Uses PapaParse — file NEVER leaves the browser.
 *
 * Auto-detects common exchange CSV formats by scanning headers for
 * known column names (Currency, Asset, Ticker, Balance, Amount, etc).
 */

import Papa from "papaparse";
import type { UnifiedAsset } from "./types";

// ── Header aliases recognized by the auto-mapper ────────────────────
const SYMBOL_HEADERS = [
    "currency", "asset", "ticker", "symbol", "coin", "token", "name",
    // Coinbase-specific
    "asset name",
];
const AMOUNT_HEADERS = [
    "balance", "amount", "quantity", "size", "total", "holdings",
    // Coinbase-specific
    "quantity (total)",
];
const VALUE_HEADERS = [
    "value", "usd value", "value (usd)", "total value", "native value",
    // Coinbase-specific
    "subtotal",
];

/** Normalise a header string for matching */
function norm(h: string): string {
    return h.toLowerCase().trim().replace(/[_\-]/g, " ");
}

/** Find a matching column index from a set of known aliases */
function findColumn(headers: string[], aliases: string[]): number {
    return headers.findIndex((h) => aliases.includes(norm(h)));
}

/**
 * Parse an exchange CSV file into UnifiedAsset[].
 * Entirely client-side — the File is read in the browser via FileReader.
 *
 * @param file    The File object from an <input> or drop zone
 * @param source  Human-readable name to attach as `location`, e.g. filename
 * @returns       Promise resolving to parsed assets
 */
export function parseExchangeCSV(
    file: File,
    source?: string
): Promise<UnifiedAsset[]> {
    const location = source || file.name;

    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete(results) {
                const headers = results.meta.fields ?? [];
                const symbolIdx = findColumn(headers, SYMBOL_HEADERS);
                const amountIdx = findColumn(headers, AMOUNT_HEADERS);
                const valueIdx = findColumn(headers, VALUE_HEADERS);

                if (symbolIdx < 0 || amountIdx < 0) {
                    reject(
                        new Error(
                            `Could not detect columns. Expected headers like "Currency" and "Balance". Found: ${headers.join(", ")}`
                        )
                    );
                    return;
                }

                const symbolKey = headers[symbolIdx];
                const amountKey = headers[amountIdx];
                const valueKey = valueIdx >= 0 ? headers[valueIdx] : null;

                const assets: UnifiedAsset[] = [];
                for (const row of results.data as Record<string, string>[]) {
                    const rawSymbol = row[symbolKey]?.trim();
                    const rawAmount = parseFloat(row[amountKey]);

                    if (!rawSymbol || isNaN(rawAmount) || rawAmount <= 0) continue;

                    // Extract just the ticker if the cell is something like "Bitcoin (BTC)"
                    const symbol = extractTicker(rawSymbol);
                    const valueUsd = valueKey ? parseFloat(row[valueKey]) || 0 : 0;

                    assets.push({
                        symbol: symbol.toUpperCase(),
                        amount: rawAmount,
                        valueUsd,
                        source: "csv",
                        location,
                    });
                }

                resolve(assets);
            },
            error(err) {
                reject(new Error(`CSV parse error: ${err.message}`));
            },
        });
    });
}

/**
 * Extract a clean ticker from strings like:
 *   "Bitcoin (BTC)" → "BTC"
 *   "ETH"           → "ETH"
 *   "Ethereum"      → "Ethereum"  (kept as-is if no parenthetical)
 */
function extractTicker(raw: string): string {
    const match = raw.match(/\(([A-Z0-9]+)\)/);
    if (match) return match[1];
    // If it looks like a plain ticker already, return it
    if (/^[A-Z0-9]{2,10}$/.test(raw.trim())) return raw.trim();
    return raw.trim();
}
