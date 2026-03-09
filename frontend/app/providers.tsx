/**
 * app/providers.tsx
 *
 * AppKit (Web3Modal) provider configuration.
 * This file is only loaded client-side (via dynamic import with ssr:false),
 * so module-level code safely accesses browser APIs.
 *
 * Per Reown docs, createAppKit MUST be called at module level — not inside
 * useEffect — so the modal is ready before any useAppKit() hook fires.
 */

"use client";

import { ReactNode, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WagmiProvider, type Config } from "wagmi";
import { createAppKit } from "@reown/appkit/react";
import { WagmiAdapter } from "@reown/appkit-adapter-wagmi";
import {
    mainnet,
    polygon,
    arbitrum,
    optimism,
    bsc,
    avalanche,
    base,
    type AppKitNetwork,
} from "@reown/appkit/networks";

// ── Config ────────────────────────────────────────────────────────
const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "";
const PROJECT_ID_REGEX = /^[a-zA-Z0-9]{32}$/;
export const walletConnectConfigured = PROJECT_ID_REGEX.test(projectId);

const metadata = {
    name: "Portfolio Pulse",
    description: "AI-Powered Crypto Portfolio Advisor",
    url: typeof window !== "undefined" ? window.location.origin : "http://localhost:3000",
    icons: ["/icon.svg"],
};

const networks: [AppKitNetwork, ...AppKitNetwork[]] = [mainnet, polygon, arbitrum, optimism, bsc, avalanche, base];

// ── Module-level initialization (client only) ─────────────────────
let wagmiAdapter: WagmiAdapter | null = null;

if (walletConnectConfigured) {
    wagmiAdapter = new WagmiAdapter({ projectId, networks });
    createAppKit({
        adapters: [wagmiAdapter],
        networks,
        projectId,
        metadata,
        features: { analytics: false },
    });
}

export function WalletProviderBoundary({
    children,
    fallback = null,
}: {
    children: ReactNode;
    fallback?: ReactNode;
}) {
    const [queryClient] = useState(() => new QueryClient());

    if (!walletConnectConfigured || !wagmiAdapter) {
        return <>{children}</>;
    }

    return (
        <WagmiProvider config={wagmiAdapter.wagmiConfig as Config}>
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        </WagmiProvider>
    );
}
