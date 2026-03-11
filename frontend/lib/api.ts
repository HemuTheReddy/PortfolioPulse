const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

const REQUEST_TIMEOUT_MS = 15000;

interface ApiErrorDetails {
    kind: "network" | "http" | "parse";
    message: string;
    path: string;
    url: string;
    status?: number;
    statusText?: string;
    responseBody?: string;
}

export class ApiError extends Error {
    kind: ApiErrorDetails["kind"];
    path: string;
    url: string;
    status?: number;
    statusText?: string;
    responseBody?: string;

    constructor(details: ApiErrorDetails) {
        super(details.message);
        this.name = "ApiError";
        this.kind = details.kind;
        this.path = details.path;
        this.url = details.url;
        this.status = details.status;
        this.statusText = details.statusText;
        this.responseBody = details.responseBody;
    }
}

export function getApiErrorMessage(err: unknown): string {
    if (err instanceof ApiError) {
        if (err.kind === "network") {
            return "Unable to reach the API. Check NEXT_PUBLIC_API_URL, CORS allowlist, and network.";
        }
        if (err.kind === "http") {
            const bodyNote = err.responseBody ? ` Details: ${err.responseBody.slice(0, 160)}` : "";
            return `API error ${err.status}: ${err.statusText || "request failed"}.${bodyNote}`;
        }
        return "The API returned an invalid response format.";
    }
    if (err instanceof Error) return err.message;
    return "Unexpected error.";
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
    const url = `${API_BASE}${path}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    let res: Response;
    try {
        res = await fetch(url, { ...init, signal: controller.signal });
    } catch (err) {
        const msg = err instanceof Error ? err.message : "unknown network error";
        throw new ApiError({
            kind: "network",
            message: `Network request failed for ${path} (${url}): ${msg}`,
            path,
            url,
        });
    } finally {
        clearTimeout(timeout);
    }

    if (!res.ok) {
        let body = "";
        try {
            body = await res.text();
        } catch {
            body = "";
        }
        throw new ApiError({
            kind: "http",
            message: `API request failed for ${path}: ${res.status} ${res.statusText}`,
            path,
            url,
            status: res.status,
            statusText: res.statusText,
            responseBody: body,
        });
    }

    try {
        return (await res.json()) as T;
    } catch {
        throw new ApiError({
            kind: "parse",
            message: `API request for ${path} returned invalid JSON.`,
            path,
            url,
        });
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

