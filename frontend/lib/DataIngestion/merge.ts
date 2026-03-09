/**
 * DataIngestion/merge.ts
 *
 * Merges multiple UnifiedAsset arrays (from different pillars) into
 * a single deduplicated UnifiedPortfolio.
 *
 * Deduplication logic: same symbol from multiple sources → amounts are summed,
 * valueUsd is summed, sources array reflects all contributors.
 */

import type { UnifiedAsset, UnifiedPortfolio, AssetSource } from "./types";

export function mergePortfolios(...sources: UnifiedAsset[][]): UnifiedPortfolio {
    // Flatten everything
    const all: UnifiedAsset[] = sources.flat();

    // Deduplicate by symbol — sum amounts and valueUsd
    const map = new Map<string, UnifiedAsset>();

    for (const asset of all) {
        const sym = asset.symbol.toUpperCase();
        if (map.has(sym)) {
            const existing = map.get(sym)!;
            map.set(sym, {
                ...existing,
                amount: existing.amount + asset.amount,
                valueUsd: existing.valueUsd + asset.valueUsd,
                // Keep the location of the first source, note multi-source
                location:
                    existing.location === asset.location
                        ? existing.location
                        : `${existing.location}, ${asset.location}`,
            });
        } else {
            map.set(sym, { ...asset, symbol: sym });
        }
    }

    const assets = Array.from(map.values()).sort((a, b) => b.valueUsd - a.valueUsd);
    const totalValueUsd = assets.reduce((sum, a) => sum + a.valueUsd, 0);

    // Collect unique sources
    const sourceSet = new Set<AssetSource>(all.map((a) => a.source));

    return {
        assets,
        totalValueUsd,
        lastUpdated: new Date().toISOString(),
        sources: Array.from(sourceSet),
    };
}
