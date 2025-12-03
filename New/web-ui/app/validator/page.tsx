'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import {
    CheckCircle, XCircle, Clock, AlertTriangle, Play,
    Eye, TrendingUp, Activity, Code, FileCheck
} from 'lucide-react';

interface Finding {
    id: string;
    type: string;
    severity: string;
    title: string;
    description: string;
    proof_of_concept?: string;
}

interface ValidationJob {
    job_id: string;
    finding_id: string;
    status: string;
    is_valid?: boolean;
    confidence?: number;
    execution_trace?: string;
    error_message?: string;
    started_at: string;
    completed_at?: string;
}

export default function ValidatorPage() {
    const [findingId, setFindingId] = useState('');
    const [findingType, setFindingType] = useState('reentrancy');
    const [severity, setSeverity] = useState('high');
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [pocCode, setPocCode] = useState('');
    const queryClient = useQueryClient();

    // Get all validations
    const { data: validations } = useQuery({
        queryKey: ['validations'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8010/validations');
            if (!response.ok) throw new Error('Failed to fetch validations');
            return response.json();
        },
        refetchInterval: 5000,
    });

    // Submit validation
    const { mutate: submitValidation, isPending } = useMutation({
        mutationFn: async (finding: Finding) => {
            const response = await fetch('http://localhost:8010/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    finding,
                    chain: 'ethereum',
                    timeout: 300,
                    sandbox_type: 'foundry'
                }),
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Validation failed');
            }
            return response.json();
        },
        onSuccess: () => {
            toast.success('Validation queued successfully!');
            queryClient.invalidateQueries({ queryKey: ['validations'] });
            // Clear form
            setFindingId('');
            setTitle('');
            setDescription('');
            setPocCode('');
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    // Mark finding manually
    const { mutate: markFinding } = useMutation({
        mutationFn: async ({ jobId, isValid }: { jobId: string; isValid: boolean }) => {
            const response = await fetch(
                `http://localhost:8010/validate/${jobId}/mark?is_valid=${isValid}&confidence=${isValid ? 0.9 : 0.1}`,
                { method: 'POST' }
            );
            if (!response.ok) throw new Error('Failed to mark finding');
            return response.json();
        },
        onSuccess: () => {
            toast.success('Finding marked successfully!');
            queryClient.invalidateQueries({ queryKey: ['validations'] });
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    const handleSubmit = () => {
        if (!findingId || !title || !description) {
            toast.error('Please fill in all required fields');
            return;
        }

        const finding: Finding = {
            id: findingId,
            type: findingType,
            severity,
            title,
            description,
            proof_of_concept: pocCode || undefined,
        };

        submitValidation(finding);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-500';
            case 'running': return 'text-blue-500';
            case 'queued': return 'text-yellow-500';
            case 'failed': return 'text-red-500';
            default: return 'text-gray-500';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return CheckCircle;
            case 'running': return Activity;
            case 'queued': return Clock;
            case 'failed': return XCircle;
            default: return AlertTriangle;
        }
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold gradient-text mb-2 flex items-center gap-3">
                    <FileCheck className="w-10 h-10" />
                    Validator Worker
                </h1>
                <p className="text-gray-400">
                    Reproduce and validate security findings in sandboxed environments
                </p>
            </motion.div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { label: 'Total Jobs', value: validations?.total || 0, icon: Activity },
                    { label: 'Queued', value: validations?.queued || 0, icon: Clock },
                    { label: 'Running', value: validations?.running || 0, icon: Play },
                    { label: 'Completed', value: validations?.completed || 0, icon: CheckCircle },
                ].map((stat, index) => (
                    <motion.div
                        key={stat.label}
                        className="glass-card p-6"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                    >
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-400">{stat.label}</span>
                            <stat.icon className="w-5 h-5 text-primary-500" />
                        </div>
                        <p className="text-3xl font-bold">{stat.value}</p>
                    </motion.div>
                ))}
            </div>

            {/* Submit Form */}
            <motion.div
                className="glass-card p-6 space-y-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <h2 className="text-2xl font-bold mb-4">Submit Finding for Validation</h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Finding ID *
                        </label>
                        <input
                            type="text"
                            value={findingId}
                            onChange={(e) => setFindingId(e.target.value)}
                            placeholder="finding-001"
                            className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                            disabled={isPending}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Finding Type
                        </label>
                        <select
                            value={findingType}
                            onChange={(e) => setFindingType(e.target.value)}
                            className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                            disabled={isPending}
                        >
                            <option value="reentrancy">Reentrancy</option>
                            <option value="integer_overflow">Integer Overflow</option>
                            <option value="access_control">Access Control</option>
                            <option value="unchecked_call">Unchecked Call</option>
                            <option value="flash_loan">Flash Loan</option>
                            <option value="price_manipulation">Price Manipulation</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Severity
                        </label>
                        <select
                            value={severity}
                            onChange={(e) => setSeverity(e.target.value)}
                            className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                            disabled={isPending}
                        >
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                            <option value="info">Info</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Title *
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Reentrancy in withdraw()"
                            className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                            disabled={isPending}
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">
                        Description *
                    </label>
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Detailed description of the vulnerability..."
                        rows={3}
                        className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
                        disabled={isPending}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">
                        Proof of Concept (Optional)
                    </label>
                    <textarea
                        value={pocCode}
                        onChange={(e) => setPocCode(e.target.value)}
                        placeholder="// Solidity PoC code (leave empty to use auto-generated template)"
                        rows={8}
                        className="w-full px-4 py-3 bg-gray-800 rounded-lg border border-gray-700 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all font-mono text-sm"
                        disabled={isPending}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                        If not provided, a template will be auto-generated based on the finding type
                    </p>
                </div>

                <button
                    onClick={handleSubmit}
                    disabled={isPending || !findingId || !title || !description}
                    className="btn-primary w-full py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    <Play className="w-5 h-5" />
                    {isPending ? 'Submitting...' : 'Submit for Validation'}
                </button>
            </motion.div>

            {/* Validation Jobs */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <Eye className="w-6 h-6 text-primary-500" />
                    Validation Jobs ({validations?.total || 0})
                </h2>

                {validations?.jobs?.length > 0 ? (
                    <div className="space-y-3">
                        {validations.jobs.slice(0, 10).reverse().map((job: ValidationJob) => {
                            const StatusIcon = getStatusIcon(job.status);
                            return (
                                <div
                                    key={job.job_id}
                                    className="bg-gray-800/50 rounded-lg p-4 space-y-3"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <StatusIcon className={`w-5 h-5 ${getStatusColor(job.status)}`} />
                                                <span className={`font-semibold capitalize ${getStatusColor(job.status)}`}>
                                                    {job.status}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-400">Finding: {job.finding_id}</p>
                                            <p className="text-xs text-gray-500">
                                                Started: {new Date(job.started_at).toLocaleString()}
                                            </p>
                                        </div>

                                        {job.status === 'completed' && job.is_valid !== undefined && (
                                            <div className={`px-4 py-2 rounded-lg ${job.is_valid
                                                    ? 'bg-red-500/20 text-red-400'
                                                    : 'bg-green-500/20 text-green-400'
                                                }`}>
                                                <div className="text-center">
                                                    <p className="font-semibold">
                                                        {job.is_valid ? 'VALID' : 'FALSE POSITIVE'}
                                                    </p>
                                                    <p className="text-xs">
                                                        {(job.confidence! * 100).toFixed(0)}% confidence
                                                    </p>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {job.error_message && (
                                        <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-3 text-sm text-red-300">
                                            <strong>Error:</strong> {job.error_message}
                                        </div>
                                    )}

                                    {job.execution_trace && (
                                        <details className="bg-gray-900 rounded-lg">
                                            <summary className="cursor-pointer p-3 hover:bg-gray-800 transition-colors">
                                                <span className="font-semibold">View Execution Trace</span>
                                            </summary>
                                            <pre className="p-3 text-xs overflow-auto max-h-64">
                                                {job.execution_trace}
                                            </pre>
                                        </details>
                                    )}

                                    {job.status === 'completed' && job.is_valid === null && (
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => markFinding({ jobId: job.job_id, isValid: true })}
                                                className="flex-1 px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-colors"
                                            >
                                                Mark as Valid
                                            </button>
                                            <button
                                                onClick={() => markFinding({ jobId: job.job_id, isValid: false })}
                                                className="flex-1 px-4 py-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg transition-colors"
                                            >
                                                Mark as False Positive
                                            </button>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-400">
                        <FileCheck className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No validation jobs yet</p>
                        <p className="text-sm">Submit a finding to start validation</p>
                    </div>
                )}
            </motion.div>

            {/* Info */}
            <motion.div
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
            >
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Code className="w-5 h-5 text-primary-500" />
                        Sandboxed Execution
                    </h3>
                    <p className="text-sm text-gray-400">
                        Findings are reproduced in isolated Foundry environments with full trace capture
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-primary-500" />
                        Confidence Scoring
                    </h3>
                    <p className="text-sm text-gray-400">
                        ML-based confidence assessment helps prioritize real vulnerabilities
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-primary-500" />
                        False Positive Detection
                    </h3>
                    <p className="text-sm text-gray-400">
                        Automatically identifies and filters out false positives to reduce noise
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
