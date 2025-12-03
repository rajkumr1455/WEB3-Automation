'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import { Shield, Download, Code, FileText, Zap } from 'lucide-react';

export default function SignaturesPage() {
    const [selectedFormat, setSelectedFormat] = useState('yara');
    const queryClient = useQueryClient();

    // Get all signatures
    const { data: signatures } = useQuery({
        queryKey: ['signatures'],
        queryFn: async () => {
            const response = await fetch('http://localhost:8012/signatures');
            if (!response.ok) throw new Error('Failed to fetch signatures');
            return response.json();
        },
        refetchInterval: 10000,
    });

    // Export signatures
    const { mutate: exportSignatures, isPending: isExporting } = useMutation({
        mutationFn: async (format: string) => {
            const response = await fetch(`http://localhost:8012/export?format=${format}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            if (!response.ok) throw new Error('Export failed');
            return response.json();
        },
        onSuccess: (data) => {
            // Download the exported content
            const blob = new Blob([data.content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `signatures_${data.format}_${Date.now()}.txt`;
            a.click();
            URL.revokeObjectURL(url);

            toast.success(`Exported ${data.count} ${data.format.toUpperCase()} signatures!`);
        },
        onError: (error: Error) => {
            toast.error(error.message);
        },
    });

    const formatInfo = {
        yara: {
            name: 'YARA',
            description: 'Bytecode pattern matching rules',
            icon: Code,
            color: 'text-blue-500',
        },
        sigma: {
            name: 'Sigma',
            description: 'Transaction monitoring rules',
            icon: Shield,
            color: 'text-green-500',
        },
        suricata: {
            name: 'Suricata',
            description: 'Network-level detection rules',
            icon: Zap,
            color: 'text-yellow-500',
        },
        custom: {
            name: 'Custom',
            description: 'Platform-agnostic JSON rules',
            icon: FileText,
            color: 'text-purple-500',
        },
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
                    Signature Generator
                </h1>
                <p className="text-gray-400">
                    Convert security findings into monitoring signatures and detection rules
                </p>
            </motion.div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {Object.entries(formatInfo).map(([format, info], index) => {
                    const Icon = info.icon;
                    const count = signatures?.by_format?.[format] || 0;

                    return (
                        <motion.div
                            key={format}
                            className="glass-card p-6 cursor-pointer hover:border-primary-500 transition-all"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            onClick={() => setSelectedFormat(format)}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-gray-400">{info.name}</span>
                                <Icon className={`w-5 h-5 ${info.color}`} />
                            </div>
                            <p className="text-3xl font-bold mb-1">{count}</p>
                            <p className="text-xs text-gray-500">{info.description}</p>
                        </motion.div>
                    );
                })}
            </div>

            {/* Format Tabs */}
            <motion.div
                className="glass-card p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold">Signatures</h2>
                    <button
                        onClick={() => exportSignatures(selectedFormat)}
                        disabled={isExporting || !signatures?.signatures?.length}
                        className="btn-primary px-6 py-2 flex items-center gap-2 disabled:opacity-50"
                    >
                        <Download className="w-4 h-4" />
                        Export {formatInfo[selectedFormat as keyof typeof formatInfo].name}
                    </button>
                </div>

                {/* Format Selector */}
                <div className="flex gap-2 mb-6 overflow-x-auto">
                    {Object.entries(formatInfo).map(([format, info]) => (
                        <button
                            key={format}
                            onClick={() => setSelectedFormat(format)}
                            className={`px-4 py-2 rounded-lg transition-all whitespace-nowrap ${selectedFormat === format
                                    ? 'bg-primary-500 text-white'
                                    : 'bg-gray-800 hover:bg-gray-700'
                                }`}
                        >
                            {info.name}
                        </button>
                    ))}
                </div>

                {/* Signatures List */}
                {signatures?.signatures && signatures.signatures.length > 0 ? (
                    <div className="space-y-3">
                        {signatures.signatures
                            .filter((sig: any) => sig.format === selectedFormat)
                            .map((sig: any, index: number) => (
                                <div
                                    key={sig.signature_id}
                                    className="bg-gray-800/50 rounded-lg p-4"
                                >
                                    <div className="flex items-start justify-between mb-2">
                                        <div>
                                            <h3 className="font-semibold capitalize">
                                                {sig.finding_type.replace('_', ' ')}
                                            </h3>
                                            <p className="text-sm text-gray-400">
                                                ID: {sig.finding_id}
                                            </p>
                                        </div>
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${sig.metadata.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                                sig.metadata.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                    'bg-yellow-500/20 text-yellow-400'
                                            }`}>
                                            {sig.metadata.severity?.toUpperCase() || 'MEDIUM'}
                                        </span>
                                    </div>

                                    <details className="mt-3">
                                        <summary className="cursor-pointer text-sm text-primary-400 hover:text-primary-300">
                                            View {formatInfo[selectedFormat as keyof typeof formatInfo].name} Rule
                                        </summary>
                                        <pre className="mt-2 bg-gray-900 rounded p-3 text-xs overflow-auto max-h-96">
                                            {sig.content}
                                        </pre>
                                    </details>

                                    {sig.metadata.contract && (
                                        <p className="text-xs text-gray-500 mt-2">
                                            Contract: {sig.metadata.contract}
                                        </p>
                                    )}
                                </div>
                            ))}
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-400">
                        <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p className="text-lg mb-2">No {formatInfo[selectedFormat as keyof typeof formatInfo].name} signatures yet</p>
                        <p className="text-sm">
                            Signatures will appear here when findings are converted to detection rules
                        </p>
                    </div>
                )}
            </motion.div>

            {/* Info Cards */}
            <motion.div
                className="grid grid-cols-1 md:grid-cols-4 gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
            >
                {Object.entries(formatInfo).map(([format, info]) => {
                    const Icon = info.icon;
                    return (
                        <div key={format} className="glass-card p-6">
                            <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                                <Icon className={`w-5 h-5 ${info.color}`} />
                                {info.name}
                            </h3>
                            <p className="text-sm text-gray-400">{info.description}</p>
                        </div>
                    );
                })}
            </motion.div>
        </div>
    );
}
