'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import {
    Shield, Play, Square, AlertTriangle, CheckCircle,
    Activity, Pause, Clock, Eye, TrendingUp
} from 'lucide-react';

interface MonitorRequest {
    contract_address: string;
    chain: string;
    auto_pause: boolean;
    alert_channels: string[];
}

interface PauseRequest {
    id: number;
    contract_address: string;
    reason: string;
    severity: string;
    status: string;
    created_at: string;
}

export default function GuardrailPage() {
    const [contractAddress, setContractAddress] = useState('');
    const [chain, setChain] = useState('ethereum');
    const [autoPause, setAutoPause] = useState(false);
    const queryClient = useQueryClient();

    // Get monitoring status
    const { data: monitoringStatus } = useQuery({
        queryKey: ['guardrail-status'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8009/monitor/status');
            if (!response.ok) throw new Error('Failed to fetch status');
            return response.json();
        },
        refetchInterval: 5000,
    });

    // Get pause requests
    const { data: pauseRequests } = useQuery({
        queryKey: ['pause-requests'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8009/pause/requests');
            if (!response.ok) throw new Error('Failed to fetch requests');
            return response.json();
        },
        refetchInterval: 5000,
    });

    // Start monitoring
    const { mutate: startMonitoring, isPending: isStarting } = useMutation({
        mutationFn: async (data: MonitorRequest) => {
            const response = await fetch('http://localhost:8009/monitor/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start monitoring');
            }
            return response.json();
        },
        onSuccess: () => {
            toast.success('Monitoring started successfully!');
            queryClient.invalidateQueries({ queryKey: ['guardrail-status'] });
            setContractAddress('');
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    // Stop monitoring
    const { mutate: stopMonitoring } = useMutation({
        mutationFn: async (address: string) => {
            const response = await fetch(`http://localhost:8009/monitor/stop?contract_address=${address}`, {
                method: 'POST',
            });
            if (!response.ok) throw new Error('Failed to stop monitoring');
            return response.json();
        },
        onSuccess: () => {
            toast.success('Monitoring stopped');
            queryClient.invalidateQueries({ queryKey: ['guardrail-status'] });
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    // Approve pause request
    const { mutate: approvePause } = useMutation({
        mutationFn: async (pauseId: number) => {
            const response = await fetch(`http://localhost:8009/pause/approve/${pauseId}`, {
                method: 'POST',
            });
            if (!response.ok) throw new Error('Failed to approve pause');
            return response.json();
        },
        onSuccess: () => {
            toast.success('Pause request approved and executed!');
            queryClient.invalidateQueries({ queryKey: ['pause-requests'] });
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    const handleStartMonitoring = () => {
        if (!contractAddress) {
            toast.error('Please enter a contract address');
            return;
        }

        startMonitoring({
            contract_address: contractAddress,
            chain,
            auto_pause: autoPause,
            alert_channels: ['api'],
        });
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold gradient-text mb-2 flex items-center gap-3">
                    <Shield className="w-10 h-10" />
                    Guardrail Auto-Pause System
                </h1>
                <p className="text-gray-400">
                    Real-time transaction monitoring with automatic contract pausing on exploit detection
                </p>
            </motion.div>

            {/* Monitoring Form */}
            <motion.div
                className="glass-card p-6 space-y-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
            >
                <h2 className="text-2xl font-bold mb-4">Start Monitoring</h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Contract Address *
                        </label>
                        <input
                            type="text"
                            value={contractAddress}
                            onChange={(e) => setContractAddress(e.target.value)}
                            placeholder="0x..."
                            className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                            disabled={isStarting}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Blockchain
                        </label>
                        <select
                            value={chain}
                            onChange={(e) => setChain(e.target.value)}
                            className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                            disabled={isStarting}
                        >
                            <option value="ethereum">Ethereum</option>
                            <option value="bsc">BSC</option>
                            <option value="polygon">Polygon</option>
                        </select>
                    </div>
                </div>

                <div className="flex items-center space-x-3">
                    <input
                        type="checkbox"
                        checked={autoPause}
                        onChange={(e) => setAutoPause(e.target.checked)}
                        className="w-5 h-5 rounded"
                        disabled={isStarting}
                    />
                    <label className="text-sm">
                        Auto-Pause (automatically pause contract on critical threat)
                    </label>
                </div>

                {autoPause && (
                    <div className="bg-yellow-900/20 border border-yellow-500/50 rounded-lg p-4">
                        <div className="flex items-start gap-2">
                            <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5" />
                            <div className="text-sm text-yellow-200">
                                <strong>Warning:</strong> Auto-pause will execute immediately when a critical threat is detected.
                                Ensure you have proper governance and multi-sig controls in production.
                            </div>
                        </div>
                    </div>
                )}

                <button
                    onClick={handleStartMonitoring}
                    disabled={isStarting || !contractAddress}
                    className="btn-primary w-full py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    <Play className="w-5 h-5" />
                    {isStarting ? 'Starting...' : 'Start Monitoring'}
                </button>
            </motion.div>

            {/* Active Monitors */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <Eye className="w-6 h-6 text-primary-500" />
                    Active Monitors ({monitoringStatus?.total || 0})
                </h2>

                {monitoringStatus?.active_monitors?.length > 0 ? (
                    <div className="space-y-3">
                        {monitoringStatus.active_monitors.map((address: string) => (
                            <div
                                key={address}
                                className="bg-gray-800/50 rounded-lg p-4 flex items-center justify-between"
                            >
                                <div className="flex items-center gap-3">
                                    <Activity className="w-5 h-5 text-green-500 animate-pulse" />
                                    <div>
                                        <p className="font-mono text-sm">{address}</p>
                                        <p className="text-xs text-gray-400">Monitoring in real-time</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => stopMonitoring(address)}
                                    className="px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-colors flex items-center gap-2"
                                >
                                    <Square className="w-4 h-4" />
                                    Stop
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-400">
                        <Eye className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No active monitors</p>
                        <p className="text-sm">Start monitoring a contract to see it here</p>
                    </div>
                )}
            </motion.div>

            {/* Pause Requests */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <Pause className="w-6 h-6 text-orange-500" />
                    Pause Requests ({pauseRequests?.total || 0})
                </h2>

                {pauseRequests?.requests?.length > 0 ? (
                    <div className="space-y-3">
                        {pauseRequests.requests.map((request: PauseRequest) => (
                            <div
                                key={request.id}
                                className="bg-gray-800/50 border-l-4 border-orange-500 rounded-lg p-4"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div>
                                        <p className="font-mono text-sm mb-1">{request.contract_address}</p>
                                        <p className="text-sm text-gray-300">{request.reason}</p>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${request.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                            request.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                'bg-yellow-500/20 text-yellow-400'
                                        }`}>
                                        {request.severity.toUpperCase()}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between mt-3">
                                    <div className="flex items-center gap-4 text-xs text-gray-400">
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {new Date(request.created_at).toLocaleString()}
                                        </span>
                                        <span className={`px-2 py-1 rounded ${request.status === 'executed' ? 'bg-green-500/20 text-green-400' :
                                                request.status === 'auto_approved' ? 'bg-blue-500/20 text-blue-400' :
                                                    'bg-yellow-500/20 text-yellow-400'
                                            }`}>
                                            {request.status.replace('_', ' ')}
                                        </span>
                                    </div>

                                    {request.status === 'pending_approval' && (
                                        <button
                                            onClick={() => approvePause(request.id)}
                                            className="px-4 py-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg transition-colors flex items-center gap-2"
                                        >
                                            <CheckCircle className="w-4 h-4" />
                                            Approve & Execute
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-400">
                        <Pause className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No pause requests</p>
                        <p className="text-sm">Requests will appear here when exploits are detected</p>
                    </div>
                )}
            </motion.div>

            {/* Feature Info */}
            <motion.div
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
            >
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-primary-500" />
                        Real-Time Monitoring
                    </h3>
                    <p className="text-sm text-gray-400">
                        Watch mempool transactions in real-time and detect exploits before execution
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-primary-500" />
                        Exploit Detection
                    </h3>
                    <p className="text-sm text-gray-400">
                        Identify reentrancy, flash loans, price manipulation, and access control issues
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Pause className="w-5 h-5 text-primary-500" />
                        Auto-Pause
                    </h3>
                    <p className="text-sm text-gray-400">
                        Automatically pause contracts when critical threats detected, with manual approval option
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
