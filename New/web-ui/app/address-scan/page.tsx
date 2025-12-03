'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import {
    Search, Loader2, CheckCircle, XCircle, AlertTriangle,
    ExternalLink, Code, Shield, Globe
} from 'lucide-react';

interface Chain {
    id: string;
    name: string;
    type: string;
}

interface ScanResult {
    scan_id: string;
    address: string;
    chain: string;
    source_found: boolean;
    decompiled: boolean;
    findings: Array<{
        severity: string;
        title: string;
        description: string;
    }>;
    status: string;
}

export default function AddressScanPage() {
    const [address, setAddress] = useState('');
    const [selectedChain, setSelectedChain] = useState('');
    const [forceDecompile, setForceDecompile] = useState(false);
    const [lastError, setLastError] = useState<string | null>(null);
    const queryClient = useQueryClient();

    // Fetch supported chains
    const { data: chainsData } = useQuery({
        queryKey: ['supported-chains'],
        queryFn: async () => {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
            const response = await fetch(`${API_URL}/address-scanner/supported-chains`);
            if (!response.ok) throw new Error('Failed to fetch chains');
            return response.json();
        },
    });

    // Scan mutation
    const { mutate: scanAddress, isPending, data: scanResult } = useMutation({
        mutationFn: async (data: { address: string; chain?: string; force_decompile?: boolean }) => {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
            const response = await fetch(`${API_URL}/address-scanner/scan-address`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Scan failed');
            }

            return response.json();
        },
        onSuccess: (data: ScanResult) => {
            toast.success(`Scan complete! Found ${data.findings.length} issues`);
            setLastError(null);
            queryClient.invalidateQueries({ queryKey: ['address-scans'] });
        },
        onError: (error: Error) => {
            setLastError(error.message);
            toast.error(error.message || 'Failed to scan address');
        },
    });

    const handleScan = () => {
        if (!address) {
            toast.error('Please enter a contract address');
            return;
        }

        scanAddress({
            address,
            chain: selectedChain || undefined,
            force_decompile: forceDecompile,
        });
    };

    const handleRetryWithDecompile = () => {
        setForceDecompile(true);
        setTimeout(() => {
            scanAddress({
                address,
                chain: selectedChain || undefined,
                force_decompile: true,
            });
        }, 100);
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold gradient-text mb-2 flex items-center gap-3">
                    <Globe className="w-10 h-10" />
                    Address-Only Scanner
                </h1>
                <p className="text-gray-400">
                    Scan smart contracts across multiple blockchains using just the contract address
                </p>
            </motion.div>

            {/* Scan Form */}
            <motion.div
                className="glass-card p-6 space-y-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
            >
                <div>
                    <label className="block text-sm font-medium mb-2">
                        Contract Address *
                    </label>
                    <div className="relative">
                        <input
                            type="text"
                            value={address}
                            onChange={(e) => setAddress(e.target.value)}
                            placeholder="0x... or Solana address"
                            className="w-full px-4 py-3 pl-12 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                            disabled={isPending}
                        />
                        <Code className="absolute left-4 top-3.5 w-5 h-5 text-gray-500" />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                        Supports: Ethereum, BSC, Polygon, Arbitrum, Optimism, Solana, Aptos, Sui, Starknet
                    </p>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">
                        Blockchain (Optional - Will Auto-Detect)
                    </label>
                    <select
                        value={selectedChain}
                        onChange={(e) => setSelectedChain(e.target.value)}
                        className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                        disabled={isPending}
                    >
                        <option value="">Auto-detect from address</option>
                        {chainsData?.chains?.map((chain: string) => (
                            <option key={chain} value={chain}>
                                {chain.charAt(0).toUpperCase() + chain.slice(1)}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Force Decompile Option */}
                <div className="flex items-start space-x-3 p-4 bg-gray-800/30 rounded-lg border border-gray-700">
                    <input
                        type="checkbox"
                        id="forceDecompile"
                        checked={forceDecompile}
                        onChange={(e) => setForceDecompile(e.target.checked)}
                        className="mt-1 w-4 h-4 text-primary-600 bg-gray-700 border-gray-600 rounded focus:ring-primary-500 focus:ring-2"
                        disabled={isPending}
                    />
                    <div className="flex-1">
                        <label htmlFor="forceDecompile" className="block text-sm font-medium cursor-pointer">
                            Force Bytecode Decompilation
                        </label>
                        <p className="text-xs text-gray-500 mt-1">
                            Enable for unverified contracts. Generates pseudo-code from bytecode for analysis.
                            ⚠️ May take longer and produce less accurate results than verified source.
                        </p>
                    </div>
                </div>

                {/* Error Display with Retry Option */}
                {lastError && lastError.includes('force_decompile') && !forceDecompile && (
                    <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5" />
                            <div className="flex-1">
                                <p className="text-sm font-medium text-yellow-200">Contract Source Not Verified</p>
                                <p className="text-xs text-gray-400 mt-1">{lastError}</p>
                                <button
                                    onClick={handleRetryWithDecompile}
                                    disabled={isPending}
                                    className="mt-3 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
                                >
                                    🔧 Scan with Bytecode Decompilation
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                <button
                    onClick={handleScan}
                    disabled={isPending || !address}
                    className="btn-primary w-full py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {isPending ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Scanning...
                        </>
                    ) : (
                        <>
                            <Search className="w-5 h-5" />
                            Scan Contract
                        </>
                    )}
                </button>
            </motion.div>

            {/* Results */}
            {scanResult && (
                <motion.div
                    className="glass-card p-6 space-y-6"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold flex items-center gap-2">
                            <Shield className="w-6 h-6 text-primary-500" />
                            Scan Results
                        </h2>
                        <div className={`flex items-center gap-2 ${scanResult.status === 'completed' ? 'text-green-500' : 'text-yellow-500'
                            }`}>
                            {scanResult.status === 'completed' ? (
                                <CheckCircle className="w-5 h-5" />
                            ) : (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            )}
                            <span className="font-semibold capitalize">{scanResult.status}</span>
                        </div>
                    </div>

                    {/* Scan Info */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-gray-800/50 rounded-lg p-4">
                            <p className="text-sm text-gray-400 mb-1">Address</p>
                            <p className="font-mono text-sm break-all">{scanResult.address}</p>
                        </div>
                        <div className="bg-gray-800/50 rounded-lg p-4">
                            <p className="text-sm text-gray-400 mb-1">Blockchain</p>
                            <p className="font-semibold capitalize">{scanResult.chain}</p>
                        </div>
                        <div className="bg-gray-800/50 rounded-lg p-4">
                            <p className="text-sm text-gray-400 mb-1">Source Code</p>
                            <p className={`font-semibold ${scanResult.source_found ? 'text-green-500' : 'text-red-500'}`}>
                                {scanResult.source_found ? 'Verified ✓' : 'Not Found'}
                            </p>
                        </div>
                    </div>

                    {/* Findings */}
                    <div>
                        <h3 className="text-xl font-bold mb-4">
                            Vulnerabilities Found: {scanResult.findings.length}
                        </h3>

                        {scanResult.findings.length === 0 ? (
                            <div className="bg-green-900/20 border border-green-500 rounded-lg p-6 text-center">
                                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                                <p className="text-lg font-semibold text-green-500">No vulnerabilities detected!</p>
                                <p className="text-sm text-gray-400 mt-1">
                                    This contract appears to be secure based on static analysis
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {scanResult.findings.map((finding, index) => (
                                    <div
                                        key={index}
                                        className="bg-gray-800/50 border-l-4 border-red-500 rounded-lg p-4"
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <h4 className="font-semibold text-lg">{finding.title}</h4>
                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${finding.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                                finding.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                    finding.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                        'bg-blue-500/20 text-blue-400'
                                                }`}>
                                                {finding.severity.toUpperCase()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400">{finding.description}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </motion.div>
            )}

            {/* Feature Info */}
            <motion.div
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
            >
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Globe className="w-5 h-5 text-primary-500" />
                        Multi-Chain
                    </h3>
                    <p className="text-sm text-gray-400">
                        Support for 9+ blockchains including Ethereum, BSC, Polygon, Solana, and more
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Search className="w-5 h-5 text-primary-500" />
                        Auto-Detection
                    </h3>
                    <p className="text-sm text-gray-400">
                        Automatically detects the blockchain from address format for seamless scanning
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-primary-500" />
                        Deep Analysis
                    </h3>
                    <p className="text-sm text-gray-400">
                        Comprehensive static analysis using Slither, Mythril, and custom detection rules
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
