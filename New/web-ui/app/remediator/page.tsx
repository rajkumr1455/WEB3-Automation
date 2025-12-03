'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import { Wrench, GitPullRequest, CheckCircle, Clock, AlertCircle, ExternalLink } from 'lucide-react';

export default function RemediatorPage() {
    const queryClient = useQueryClient();

    // Get remediation jobs
    const { data: jobs } = useQuery({
        queryKey: ['remediation-jobs'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8013/jobs');
            if (!response.ok) throw new Error('Failed to fetch jobs');
            return response.json();
        },
        refetchInterval: 5000,
    });

    // Get PR history
    const { data: prs } = useQuery({
        queryKey: ['pr-history'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8013/prs');
            if (!response.ok) throw new Error('Failed to fetch PRs');
            return response.json();
        },
        refetchInterval: 10000,
    });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return CheckCircle;
            case 'failed': return AlertCircle;
            default: return Clock;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-500';
            case 'failed': return 'text-red-500';
            default: return 'text-yellow-500';
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
                    <Wrench className="w-10 h-10" />
                    Remediator
                </h1>
                <p className="text-gray-400">
                    Automated vulnerability remediation with GitHub PR creation
                </p>
            </motion.div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { label: 'Total Jobs', value: jobs?.total || 0, icon: Wrench, color: 'text-blue-500' },
                    { label: 'PRs Created', value: prs?.total || 0, icon: GitPullRequest, color: 'text-green-500' },
                    {
                        label: 'Success Rate',
                        value: jobs?.total > 0
                            ? `${((jobs.jobs.filter((j: any) => j.status === 'completed').length / jobs.total) * 100).toFixed(0)}%`
                            : '0%',
                        icon: CheckCircle,
                        color: 'text-primary-500'
                    },
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

            {/* Remediation Jobs */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <Wrench className="w-6 h-6 text-primary-500" />
                    Remediation Jobs ({jobs?.total || 0})
                </h2>

                {jobs?.jobs && jobs.jobs.length > 0 ? (
                    <div className="space-y-3">
                        {jobs.jobs.slice(0, 20).reverse().map((job: any) => {
                            const StatusIcon = getStatusIcon(job.status);
                            return (
                                <div
                                    key={job.job_id}
                                    className="bg-gray-800/50 rounded-lg p-4"
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <StatusIcon className={`w-5 h-5 ${getStatusColor(job.status)}`} />
                                                <span className={`font-semibold capitalize ${getStatusColor(job.status)}`}>
                                                    {job.status.replace('_', ' ')}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-400">Finding: {job.finding_id}</p>
                                            <p className="text-xs text-gray-500">
                                                Started: {new Date(job.created_at).toLocaleString()}
                                            </p>
                                        </div>

                                        {job.pr_url && (
                                            <a
                                                href={job.pr_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-4 py-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg transition-colors flex items-center gap-2"
                                            >
                                                <GitPullRequest className="w-4 h-4" />
                                                View PR
                                                <ExternalLink className="w-3 h-3" />
                                            </a>
                                        )}
                                    </div>

                                    {job.fix && (
                                        <div className="mt-3 bg-gray-900/50 rounded-lg p-3">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-semibold">Fix Applied</span>
                                                <span className="text-xs px-2 py-1 bg-primary-500/20 text-primary-400 rounded">
                                                    {(job.fix.confidence * 100).toFixed(0)}% confidence
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-300 whitespace-pre-wrap">
                                                {job.fix.explanation.substring(0, 200)}
                                                {job.fix.explanation.length > 200 && '...'}
                                            </p>
                                        </div>
                                    )}

                                    {job.error && (
                                        <div className="mt-3 bg-red-900/20 border border-red-500/50 rounded-lg p-3">
                                            <p className="text-sm text-red-300">
                                                <strong>Error:</strong> {job.error}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-400">
                        <Wrench className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p className="text-lg mb-2">No remediation jobs yet</p>
                        <p className="text-sm">
                            Jobs will appear here when vulnerabilities are remediated
                        </p>
                    </div>
                )}
            </motion.div>

            {/* PR History */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <GitPullRequest className="w-6 h-6 text-green-500" />
                    Pull Requests ({prs?.total || 0})
                </h2>

                {prs?.prs && prs.prs.length > 0 ? (
                    <div className="space-y-2">
                        {prs.prs.slice(0, 15).reverse().map((pr: any, index: number) => (
                            <div
                                key={index}
                                className="bg-gray-800/30 rounded-lg p-3 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    <GitPullRequest className="w-5 h-5 text-green-500" />
                                    <div>
                                        <p className="text-sm">Finding: {pr.finding_id}</p>
                                        <p className="text-xs text-gray-500">
                                            {new Date(pr.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <a
                                    href={pr.pr_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors flex items-center gap-1 text-sm"
                                >
                                    View
                                    <ExternalLink className="w-3 h-3" />
                                </a>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-400">
                        <GitPullRequest className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No pull requests created yet</p>
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
                        <Wrench className="w-5 h-5 text-primary-500" />
                        Automated Fixes
                    </h3>
                    <p className="text-sm text-gray-400">
                        Generates secure code fixes for common vulnerability patterns
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <GitPullRequest className="w-5 h-5 text-primary-500" />
                        GitHub Integration
                    </h3>
                    <p className="text-sm text-gray-400">
                        Automatically creates pull requests with detailed explanations
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-primary-500" />
                        Confidence Scoring
                    </h3>
                    <p className="text-sm text-gray-400">
                        Each fix includes a confidence score for manual review guidance
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
