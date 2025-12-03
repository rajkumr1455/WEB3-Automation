'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import { Radio, Activity, Play, Square, BarChart3, Zap } from 'lucide-react';

export default function IndexerPage() {
    const queryClient = useQueryClient();
    const [contractAddress, setContractAddress] = useState('');
    const [chain, setChain] = useState('ethereum');
    const [backfill, setBackfill] = useState(false);

    // Get indexing status
    const { data: status } = useQuery({
        queryKey: ['indexer-status'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8014/index/status');
            if (!response.ok) throw new Error('Failed to fetch status');
            return response.json();
        },
        refetchInterval: 3000,
    });

    // Get stats
    const { data: stats } = useQuery({
        queryKey: ['indexer-stats'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8014/stats');
            if (!response.ok) throw new Error('Failed to fetch stats');
            return response.json();
        },
        refetchInterval: 5000,
    });

    // Start indexing
    const { mutate: startIndexing, isPending: isStarting } = useMutation({
        mutationFn: async () => {
            const response = await fetch('http://localhost:8014/index/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contract_address: contractAddress,
                    chain,
                    backfill
                }),
            });
            if (!response.ok) throw new Error('Failed to start indexing');
            return response.json();
        },
        onSuccess: () => {
            toast.success('Indexing started!');
            queryClient.invalidateQueries({ queryKey: ['indexer-status'] });
            setContractAddress('');
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    return (
        <div className="space-y-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold gradient-text mb-2 flex items-center gap-3">
                    <Radio className="w-10 h-10" />
                    Streaming Indexer
                </h1>
                <p className="text-gray-400">
                    Real-time blockchain event indexing with WebSocket streaming
                </p>
            </motion.div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { label: 'Total Events', value: stats?.total_events || 0, icon: Activity, color: 'text-blue-500' },
                    { label: 'Active Contracts', value: stats?.indexed_contracts || 0, icon: BarChart3, color: 'text-green-500' },
                    { label: 'WebSocket Clients', value: stats?.active_websockets || 0, icon: Zap, color: 'text-yellow-500' },
                    { label: 'Chains', value: stats?.events_by_chain ? Object.keys(stats.events_by_chain).length : 0, icon: Radio, color: 'text-primary-500' },
                ].map((stat, index) => {
                    const Icon = stat.icon;
                    return (
                        <motion.div
                            key={stat.label}
                            className="glass-card p-6"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-gray-400">{stat.label}</span>
                                <Icon className={`w-5 h-5 ${stat.color}`} />
                            </div>
                            <p className="text-3xl font-bold">{stat.value}</p>
                        </motion.div>
                    );
                })}
            </div>

            {/* Start Indexing Form */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <Play className="w-6 h-6 text-primary-500" />
                    Start Indexing
                </h2>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">Contract Address</label>
                        <input
                            type="text"
                            value={contractAddress}
                            onChange={(e) => setContractAddress(e.target.value)}
                            placeholder="0x..."
                            className="input-field"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">Blockchain</label>
                        <select
                            value={chain}
                            onChange={(e) => setChain(e.target.value)}
                            className="input-field"
                        >
                            <option value="ethereum">Ethereum</option>
                            <option value="bsc">BSC</option>
                            <option value="polygon">Polygon</option>
                            <option value="arbitrum">Arbitrum</option>
                            <option value="optimism">Optimism</option>
                        </select>
                    </div>

                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="backfill"
                            checked={backfill}
                            onChange={(e) => setBackfill(e.target.checked)}
                            className="w-4 h-4"
                        />
                        <label htmlFor="backfill" className="text-sm">
                            Backfill Historical Events
                        </label>
                    </div>

                    <button
                        onClick={() => startIndexing()}
                        disabled={isStarting || !contractAddress}
                        className="btn-primary w-full py-3 disabled:opacity-50"
                    >
                        {isStarting ? 'Starting...' : 'Start Indexing'}
                    </button>
                </div>
            </motion.div>

            {/* Indexed Contracts */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <BarChart3 className="w-6 h-6 text-primary-500" />
                    Indexed Contracts ({status?.total || 0})
                </h2>

                {status?.indexed_contracts && status.indexed_contracts.length > 0 ? (
                    <div className="space-y-3">
                        {status.indexed_contracts.map((contract: any, index: number) => (
                            <div
                                key={index}
                                className="bg-gray-800/50 rounded-lg p-4"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex-1">
                                        <p className="font-mono text-sm">{contract.contract_address}</p>
                                        <p className="text-xs text-gray-400 mt-1 capitalize">{contract.chain}</p>
                                    </div>
                                    <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">
                                        Active
                                    </span>
                                </div>

                                <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                                    <div className="bg-gray-900/50 rounded p-2">
                                        <p className="text-gray-500 text-xs">Events</p>
                                        <p className="font-semibold">{contract.indexed_count}</p>
                                    </div>
                                    <div className="bg-gray-900/50 rounded p-2">
                                        <p className="text-gray-500 text-xs">Last Block</p>
                                        <p className="font-semibold">{contract.last_block?.toLocaleString()}</p>
                                    </div>
                                    <div className="bg-gray-900/50 rounded p-2">
                                        <p className="text-gray-500 text-xs">Started</p>
                                        <p className="font-semibold text-xs">
                                            {new Date(contract.started_at).toLocaleTimeString()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-400">
                        <Radio className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p className="text-lg mb-2">No contracts indexed yet</p>
                        <p className="text-sm">Start indexing a contract to see real-time events</p>
                    </div>
                )}
            </motion.div>

            {/* Info Cards */}
            <motion.div
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
            >
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Radio className="w-5 h-5 text-primary-500" />
                        Real-Time Streaming
                    </h3>
                    <p className="text-sm text-gray-400">
                        WebSocket-based event streaming for instant updates
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-primary-500" />
                        Multi-Chain Support
                    </h3>
                    <p className="text-sm text-gray-400">
                        Index events from Ethereum, BSC, Polygon, and more
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-primary-500" />
                        Historical Backfill
                    </h3>
                    <p className="text-sm text-gray-400">
                        Optional backfilling of past events for complete history
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
