/**
 * ConnectWalletButton.tsx
 *
 * A button that triggers the AppKit (Web3Modal) wallet connection modal.
 * Displays connected address when active, along with a disconnect option.
 */

"use client";

import { useAppKit, useAppKitAccount } from "@reown/appkit/react";

interface Props {
    onConnected?: (address: string) => void;
    onDisconnected?: () => void;
}

export function ConnectWalletButton({ onConnected, onDisconnected }: Props) {
    const { open } = useAppKit();
    const { address, isConnected } = useAppKitAccount();

    // Notify parent when address changes
    if (isConnected && address && onConnected) {
        onConnected(address);
    }

    if (isConnected && address) {
        const short = `${address.slice(0, 6)}…${address.slice(-4)}`;
        return (
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span
                    style={{
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: 13,
                        color: "var(--accent)",
                    }}
                >
                    <span className="wallet-label">
                        <span className="inline-icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                                <path d="M4 7h16v10H4zM7 7V5h10v2M8 12h8" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </span>
                        {short}
                    </span>
                </span>
                <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: "4px 12px" }}
                    onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onDisconnected?.();
                        open();
                    }}
                >
                    Disconnect
                </button>
            </div>
        );
    }

    return (
        <button
            type="button"
            className="btn btn-primary"
            style={{ fontSize: 13 }}
            onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                open();
            }}
        >
            <span className="wallet-label">
                <span className="inline-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24">
                        <path d="M4 7h16v10H4zM7 7V5h10v2M8 12h8" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </span>
                Connect Wallet
            </span>
        </button>
    );
}
