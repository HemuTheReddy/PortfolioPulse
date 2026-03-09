const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
    const url = `${API_BASE}${path}`;
    let res: Response;
    try {
        res = await fetch(url, init);
    } catch (err) {
        const msg = err instanceof Error ? err.message : "unknown network error";
        throw new Error(`Network request failed for ${path} (${url}): ${msg}`);
    }

    if (!res.ok) {
        let body = "";
        try {
            body = await res.text();
        } catch {
            body = "";
        }
        const detail = body ? ` — ${body.slice(0, 180)}` : "";
        throw new Error(`API request failed for ${path}: ${res.status} ${res.statusText}${detail}`);
    }

    try {
        return (await res.json()) as T;
    } catch {
        throw new Error(`API request for ${path} returned invalid JSON.`);
    }
}

export interface MarketData {
    market_state: string;
    market_metrics: {
        fear_greed: number;
        rsi: number;
        volatility: string;
        btc_24h: number;
    };
    source: string;
    regime_message: string;
    emoji: string;
}

export interface QuizResult {
    risk_score: number;
    risk_label: string;
    proxy_user: {
        user_idx: number;
        avg_hold_days: number;
        token_diversity: number;
        risk_tier: string;
        pool_size: number;
    };
}

export interface Recommendation {
    rank: number;
    item_idx: number;
    symbol: string;
    name: string;
    logo_url: string | null;
    weight: number;
    confidence: number;
    tier: string;
    explanation: string;
    category: string;
    price_usd: number | null;
    price_change_24h: number | null;
    coingecko_url: string;
    token_popularity: number;
}

export interface RecommendResult {
    recommendations: Recommendation[];
    regime_explanation: string;
    market_state: string;
    risk_score: number;
}

export interface ImportResult {
    risk_score: number;
    risk_label: string;
    proxy_user: {
        user_idx: number;
        avg_hold_days: number;
        token_diversity: number;
        risk_tier: string;
        pool_size: number;
        detected_tokens: number;
        risk_score: number;
    };
    market: MarketData;
    recommendations: Recommendation[];
    regime_explanation: string;
}

export async function getMarketState(): Promise<MarketData> {
    return requestJson<MarketData>("/api/market");
}

export async function submitQuiz(
    answers: Record<string, string>
): Promise<QuizResult> {
    return requestJson<QuizResult>("/api/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
    });
}

export async function getRecommendations(
    user_idx: number,
    risk_score: number,
    market_state: string
): Promise<RecommendResult> {
    return requestJson<RecommendResult>("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_idx, risk_score, market_state }),
    });
}

export async function importPortfolio(
    holdings: { symbol: string; amount: number }[]
): Promise<ImportResult> {
    return requestJson<ImportResult>("/api/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ holdings }),
    });
}

