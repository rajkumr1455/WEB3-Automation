'use client'

import { useQuery } from '@tanstack/react-query'
import { agentAPI } from '@/lib/api'
import { getStatusColor } from '@/lib/utils'
import { Activity, Cpu, Zap, RefreshCcw } from 'lucide-react'
import { motion } from 'framer-motion'

export default function AgentsPage() {
    const { data: agentsHealth, isLoading, refetch } = useQuery({
        queryKey: ['agents-health'],
        queryFn: () => agentAPI.getAgentsHealth(),
        refetchInterval: 5000,
    })

    const { data: llmHealth } = useQuery({
        queryKey: ['llm-health'],
        queryFn: () => agentAPI.getLLMRouterHealth(),
        refetchInterval: 10000,
    })

    const { data: models } = useQuery({
        queryKey: ['llm-models'],
        queryFn: () => agentAPI.getModels(),
    })

    const agents = [
        { name: 'orchestrator', port: 8001, description: 'Central pipeline controller' },
        { name: 'llm-router', port: 8000, description: 'Hybrid LLM request routing' },
        { name: 'recon-agent', port: 8002, description: 'Repository mapping & ABI extraction' },
        { name: 'static-agent', port: 8003, description: 'Slither, Mythril, Semgrep analysis' },
        { name: 'fuzzing-agent', port: 8004, description: 'Foundry fuzz, Echidna, Manticore' },
        { name: 'monitoring-agent', port: 8005, description: 'Mempool, oracle, RPC monitoring' },
        { name: 'triage-agent', port: 8006, description: 'Multi-tier AI classification' },
        { name: 'reporting-agent', port: 8007, description: 'Report generation & notifications' },
    ]

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Agent Status</h1>
                    <p className="text-gray-400">Monitor health and performance of all microservices</p>
                </div>
                <button
                    onClick={() => refetch()}
                    className="btn-secondary flex items-center space-x-2"
                >
                    <RefreshCcw className="w-4 h-4" />
                    <span>Refresh</span>
                </button>
            </div>

            {/* LLM Router Status */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card-hover"
            >
                <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center">
                        <Cpu className="w-5 h-5 text-primary-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-white">LLM Router Status</h2>
                </div>

                {llmHealth && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                            <p className="text-gray-400 text-sm mb-1">Ollama Connection</p>
                            <div className="flex items-center space-x-2">
                                <div className={`w-2 h-2 rounded-full ${llmHealth.ollama === 'connected' ? 'bg-success-400 animate-pulse' : 'bg-danger-400'
                                    }`} />
                                <p className="text-white font-medium capitalize">{llmHealth.ollama}</p>
                            </div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                            <p className="text-gray-400 text-sm mb-1">Claude API</p>
                            <div className="flex items-center space-x-2">
                                <div className={`w-2 h-2 rounded-full ${llmHealth.claude === 'configured' ? 'bg-success-400 animate-pulse' : 'bg-warning-400'
                                    }`} />
                                <p className="text-white font-medium capitalize">{llmHealth.claude}</p>
                            </div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                            <p className="text-gray-400 text-sm mb-1">Router Status</p>
                            <div className="flex items-center space-x-2">
                                <div className={`w-2 h-2 rounded-full ${llmHealth.status === 'healthy' ? 'bg-success-400 animate-pulse' : 'bg-danger-400'
                                    }`} />
                                <p className="text-white font-medium capitalize">{llmHealth.status}</p>
                            </div>
                        </div>
                    </div>
                )}
            </motion.div>

            {/* Agent Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {agents.map((agent, index) => {
                    const health = agentsHealth?.[agent.name]
                    return (
                        <motion.div
                            key={agent.name}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="card-hover"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center space-x-3">
                                    <div className={`w-10 h-10 ${health?.status === 'healthy' || health?.status === 'connected'
                                            ? 'bg-success-500/20'
                                            : 'bg-danger-500/20'
                                        } rounded-lg flex items-center justify-center`}>
                                        <Activity className={`w-5 h-5 ${health?.status === 'healthy' || health?.status === 'connected'
                                                ? 'text-success-400'
                                                : 'text-danger-400'
                                            }`} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold text-white capitalize">
                                            {agent.name.replace('-', ' ')}
                                        </h3>
                                        <p className="text-xs text-gray-500">Port {agent.port}</p>
                                    </div>
                                </div>
                                <div className={`px-2 py-1 rounded text-xs font-medium ${health ? getStatusColor(health.status) : 'text-gray-400 bg-gray-500/20'
                                    }`}>
                                    {isLoading ? 'Loading...' : health?.status || 'Unknown'}
                                </div>
                            </div>

                            <p className="text-gray-400 text-sm mb-4">{agent.description}</p>

                            <div className="flex items-center justify-between text-xs text-gray-500">
                                <span>http://localhost:{agent.port}</span>
                                <a
                                    href={`http://localhost:${agent.port}/health`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-primary-400 hover:text-primary-300 transition-colors"
                                >
                                    Test Health
                                </a>
                            </div>
                        </motion.div>
                    )
                })}
            </div>

            {/* Available Models */}
            {models && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="card-hover"
                >
                    <div className="flex items-center space-x-3 mb-6">
                        <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                            <Zap className="w-5 h-5 text-purple-400" />
                        </div>
                        <h2 className="text-2xl font-semibold text-white">Available Models</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <h3 className="text-sm font-semibold text-gray-300 mb-3">Local Models (Ollama)</h3>
                            <div className="space-y-2">
                                {models.local_models && Object.entries(models.local_models).map(([key, model]: [string, any]) => (
                                    <div key={key} className="bg-white/5 border border-white/10 rounded p-3">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-white font-medium capitalize">{key.replace('_', ' ')}</span>
                                            <span className="text-xs badge badge-info">{model.endpoint}</span>
                                        </div>
                                        <p className="text-xs text-gray-400 font-mono">{model.model}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h3 className="text-sm font-semibold text-gray-300 mb-3">Cloud Models</h3>
                            <div className="space-y-2">
                                {models.cloud_models && Object.entries(models.cloud_models).map(([key, model]: [string, any]) => (
                                    <div key={key} className="bg-white/5 border border-white/10 rounded p-3">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-white font-medium capitalize">{key.replace('_', ' ')}</span>
                                            <span className="text-xs badge badge-info">{model.endpoint}</span>
                                        </div>
                                        <p className="text-xs text-gray-400 font-mono">{model.model}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}
        </div>
    )
}
