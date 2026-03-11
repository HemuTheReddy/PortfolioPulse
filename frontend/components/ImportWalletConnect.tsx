"use client";

import { ConnectWalletButton } from "@/components/ConnectWalletButton";
import { WalletProviderBoundary, walletConnectConfigured } from "@/app/providers";

interface ImportWalletConnectProps {
    walletScanning: boolean;
    walletAssetsCount: number;
    onConnected: (address: string) => void;
    onDisconnected: () => void;
}

export function ImportWalletConnect({
    walletScanning,
    walletAssetsCount,
    onConnected,
    onDisconnected,
}: ImportWalletConnectProps) {
    if (!walletConnectConfigured) {
        return (
            <div
                style={{
                    marginTop: 8,
                    padding: "8px 12px",
                    background: "rgba(255,68,68,0.08)",
                    border: "1px solid rgba(255,68,68,0.3)",
                    borderRadius: 8,
                    fontSize: 13,
                    color: "#FF6B6B",
                }}
            >
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                    <span className="inline-icon" aria-hidden="true">
                        <svg viewBox="0 0 24 24">
                            <path d="M12 3 2 21h20L12 3Zm0 6v6m0 3h.01" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </span>
                    WalletConnect unavailable. Add a valid `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`
                    to `frontend/.env.local` and restart the frontend server.
                </span>
            </div>
        );
    }

    if (walletScanning) {
        return (
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div className="spinner" style={{ width: 20, height: 20 }} />
                <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                    Loading wallet data across all chains…
                </span>
            </div>
        );
    }

    return (
        <WalletProviderBoundary
            fallback={
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div className="spinner" style={{ width: 20, height: 20 }} />
                    <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                        Initializing wallet connection…
                    </span>
                </div>
            }
        >
            <ConnectWalletButton
                key={walletAssetsCount > 0 ? "connected" : "disconnected"}
                onConnected={onConnected}
                onDisconnected={onDisconnected}
            />
        </WalletProviderBoundary>
    );
}
