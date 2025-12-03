'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import {
    TrendingUp, Activity, Zap, Brain, BarChart3,
    RefreshCw, CheckCircle, AlertTriangle
} from 'lucide-react';

export default function MLOpsPage() {
    const queryClient = useQueryClient();

    // Get metrics
    const { data: metrics } = useQuery({
        queryKey: ['mlops-metrics'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8011/metrics');
            if (!response.ok) throw new Error('Failed to fetch metrics');
            return response.json();
        },
        refetchInterval: 10000,
    });

    // Get detection rules
    const { data: rules } = useQuery({
        queryKey: ['detection-rules'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8011/rules');
            if (!response.ok) throw new Error('Failed to fetch rules');
            return response.json();
        },
        refetchInterval: 10000,
    });

    // Train models
    const { mutate: trainModels, isPending: isTraining } = useMutation({
        mutationFn: async () => {
            const response = await fetch('http://localhost:8011/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ min_samples: 5, retrain: false }),
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Training failed');
            }
            return response.json();
        },
        onSuccess: () => {
            toast.success('Models trained successfully!');
            queryClient.invalidateQueries({ queryKey: ['mlops-metrics'] });
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    // Generate rules
    const { mutate: generateRules, isPending: isGenerating } = useMutation({
        mutationFn: async () => {
            const response = await fetch('http://localhost:8011/generate-rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ min_confidence: 0.7, min_samples: 3 }),
            });
            if (!response.ok) throw new Error('Rule generation failed');
            return response.json();
        },
        onSuccess: (data) => {
            toast.success(`Generated ${data.count} new detection rules!`);
            queryClient.invalidateQueries({ queryKey: ['detection-rules'] });
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
                    <Brain className="w-10 h-10" />
                    ML-Ops Engine
                </h1>
                <p className="text-gray-400">
                    Continuous learning and automated rule generation from validated findings
                </p>
            </motion.div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    {
                        label: 'Total Findings',
                        value: metrics?.total_findings || 0,
                        icon: Activity,
                        color: 'text-blue-500'
                    },
                    {
                        label: 'Validated',
                        value: metrics?.validated_findings || 0,
                        icon: CheckCircle,
                        color: 'text-green-500'
                    },
                    {
                        label: 'False Positives',
                        value: metrics?.false_positives || 0,
                        icon: AlertTriangle,
                        color: 'text-yellow-500'
                    },
                    {
                        label: 'Accuracy',
                        value: `${((metrics?.accuracy || 0) * 100).toFixed(1)}%`,
                        icon: TrendingUp,
                        color: 'text-primary-500'
                    },
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
                            <stat.icon className={`w-5 h-5 ${stat.color}`} />
                        </div>
                        <p className="text-3xl font-bold">{stat.value}</p>
                    </motion.div>
                ))}
            </div>

            {/* Training Data Stats */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <BarChart3 className="w-6 h-6 text-primary-500" />
                    Training Statistics
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-gray-800/50 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">Training Samples</p>
                        <p className="text-2xl font-bold">{metrics?.training_samples || 0}</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">Precision</p>
                        <p className="text-2xl font-bold">{((metrics?.precision || 0) * 100).toFixed(1)}%</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">Recall</p>
                        <p className="text-2xl font-bold">{((metrics?.recall || 0) * 100).toFixed(1)}%</p>
                    </div>
                </div>

                {/* Accuracy by Type */}
                {metrics?.accuracy_by_type && Object.keys(metrics.accuracy_by_type).length > 0 && (
                    <div className="mt-6">
                        <h3 className="text-lg font-semibold mb-3">Accuracy by Finding Type</h3>
                        <div className="space-y-2">
                            {Object.entries(metrics.accuracy_by_type).map(([type, accuracy]: [string, any]) => (
                                <div key={type} className="bg-gray-800/30 rounded-lg p-3">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                                        <span className="text-sm font-semibold">{(accuracy * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full bg-gray-700 rounded-full h-2">
                                        <div
                                            className="bg-primary-500 h-2 rounded-full transition-all"
                                            style={{ width: `${accuracy * 100}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </motion.div>

            {/* Actions */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
            >
                <h2 className="text-2xl font-bold mb-4">Actions</h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button
                        onClick={() => trainModels()}
                        disabled={isTraining}
                        className="btn-primary py-4 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        <RefreshCw className={`w-5 h-5 ${isTraining ? 'animate-spin' : ''}`} />
                        {isTraining ? 'Training Models...' : 'Train Models'}
                    </button>

                    <button
                        onClick={() => generateRules()}
                        disabled={isGenerating}
                        className="btn-primary py-4 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        <Zap className="w-5 h-5" />
                        {isGenerating ? 'Generating...' : 'Generate Detection Rules'}
                    </button>
                </div>

                <p className="text-sm text-gray-400 mt-4">
                    Train models on validated findings and automatically generate new detection rules
                </p>
            </motion.div>

            {/* Detection Rules */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
            >
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <Zap className="w-6 h-6 text-yellow-500" />
                    Generated Detection Rules ({rules?.total || 0})
                </h2>

                {rules?.rules && rules.rules.length > 0 ? (
                    <div className="space-y-3">
                        {rules.rules.map((rule: any, index: number) => (
                            <div
                                key={rule.rule_id}
                                className="bg-gray-800/50 rounded-lg p-4 border-l-4 border-primary-500"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div>
                                        <h3 className="font-semibold text-lg">{rule.name}</h3>
                                        <p className="text-sm text-gray-400 mt-1">{rule.description}</p>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${rule.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                            rule.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                'bg-yellow-500/20 text-yellow-400'
                                        }`}>
                                        {rule.severity.toUpperCase()}
                                    </span>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-sm">
                                    <div className="bg-gray-900/50 rounded p-2">
                                        <p className="text-gray-500 text-xs">Confidence</p>
                                        <p className="font-semibold">{(rule.confidence_threshold * 100).toFixed(0)}%</p>
                                    </div>
                                    <div className="bg-gray-900/50 rounded p-2">
                                        <p className="text-gray-500 text-xs">False Positive Rate</p>
                                        <p className="font-semibold">{(rule.false_positive_rate * 100).toFixed(1)}%</p>
                                    </div>
                                    <div className="bg-gray-900/50 rounded p-2">
                                        <p className="text-gray-500 text-xs">Validated Count</p>
                                        <p className="font-semibold">{rule.validated_count}</p>
                                    </div>
                                </div>

                                <details className="mt-3">
                                    <summary className="cursor-pointer text-sm text-primary-400 hover:text-primary-300">
                                        View Pattern
                                    </summary>
                                    <pre className="mt-2 bg-gray-900 rounded p-3 text-xs overflow-auto">
                                        {rule.pattern}
                                    </pre>
                                </details>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-400">
                        <Zap className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No detection rules generated yet</p>
                        <p className="text-sm">Train models and generate rules to see them here</p>
                    </div>
                )}
            </motion.div>

            {/* Info Cards */}
            <motion.div
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
            >
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Brain className="w-5 h-5 text-primary-500" />
                        Continuous Learning
                    </h3>
                    <p className="text-sm text-gray-400">
                        Automatically learns from every validated finding to improve detection accuracy
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-primary-500" />
                        Pattern Recognition
                    </h3>
                    <p className="text-sm text-gray-400">
                        Extracts vulnerability patterns from code and execution traces automatically
                    </p>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                        <Zap className="w-5 h-5 text-primary-500" />
                        Auto-Generation
                    </h3>
                    <p className="text-sm text-gray-400">
                        Generates new detection rules with confidence scores and false positive rates
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
