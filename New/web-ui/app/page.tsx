'use client'

import { useQuery } from '@tanstack/react-query'
import { scanAPI, agentAPI } from '@/lib/api'
import MetricsCards from '@/components/MetricsCards'
import ScanForm from '@/components/ScanForm'
import { RecentScans } from '@/components/RecentScans'
import { Activity, TrendingUp, Shield, Zap } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Dashboard() {
    const { data: scans, isLoading: scansLoading } = useQuery({
        queryKey: ['scans'],
        queryFn: () => scanAPI.listScans(),
        refetchInterval: 5000,
    })

    const { data: agentsHealth } = useQuery({
        queryKey: ['agents-health'],
        queryFn: () => agentAPI.getAgentsHealth(),
        refetchInterval: 10000,
    })

    const containerVariants = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    }

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        show: { y: 0, opacity: 1 }
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <h1 className="text-4xl font-bold gradient-text mb-2">Security Command Center</h1>
                <p className="text-gray-400">
                    Monitor your Web3 bug bounty automation pipeline in real-time
                </p>
            </motion.div>

            {/* Metrics Overview */}
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="show"
            >
                <MetricsCards scans={scans} agentsHealth={agentsHealth} />
            </motion.div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* New Scan Form */}
                <motion.div
                    variants={itemVariants}
                    initial="hidden"
                    animate="show"
                    transition={{ delay: 0.3 }}
                    className="xl:col-span-1"
                >
                    <div className="card-hover">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center">
                                <Zap className="w-5 h-5 text-primary-400" />
                            </div>
                            <h2 className="text-2xl font-semibold text-white">New Scan</h2>
                        </div>
                        <ScanForm />
                    </div>
                </motion.div>

                {/* Recent Scans */}
                <motion.div
                    variants={itemVariants}
                    initial="hidden"
                    animate="show"
                    transition={{ delay: 0.4 }}
                    className="xl:col-span-2"
                >
                    <div className="card-hover h-full">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                    <Activity className="w-5 h-5 text-purple-400" />
                                </div>
                                <h2 className="text-2xl font-semibold text-white">Recent Scans</h2>
                            </div>
                            <div className="text-sm text-gray-400">
                                {scans?.length || 0} total scans
                            </div>
                        </div>
                        {scansLoading ? (
                            <div className="space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="h-20 bg-white/5 rounded-lg loading-shimmer" />
                                ))}
                            </div>
                        ) : (
                            <RecentScans scans={scans || []} />
                        )}
                    </div>
                </motion.div>
            </div>

            {/* System Status */}
            <motion.div
                variants={itemVariants}
                initial="hidden"
                animate="show"
                transition={{ delay: 0.5 }}
                className="card-hover"
            >
                <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-success-500/20 rounded-lg flex items-center justify-center">
                        <Shield className="w-5 h-5 text-success-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-white">System Status</h2>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {agentsHealth && Object.entries(agentsHealth).map(([name, health]) => (
                        <div
                            key={name}
                            className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all"
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-300 capitalize">
                                    {name.replace('-', ' ')}
                                </span>
                                <div
                                    className={`w-2 h-2 rounded-full ${health.status === 'healthy' || health.status === 'connected'
                                        ? 'bg-success-400 animate-pulse'
                                        : health.status === 'degraded'
                                            ? 'bg-warning-400'
                                            : 'bg-danger-400'
                                        }`}
                                />
                            </div>
                            <div className="text-xs text-gray-500">
                                {health.status}
                            </div>
                        </div>
                    ))}
                </div>
            </motion.div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <motion.div
                    variants={itemVariants}
                    className="card-hover"
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-sm mb-1">Active Scans</p>
                            <p className="text-3xl font-bold text-white">
                                {scans?.filter(s => s.status === 'running').length || 0}
                            </p>
                        </div>
                        <div className="w-12 h-12 bg-primary-500/20 rounded-lg flex items-center justify-center">
                            <Activity className="w-6 h-6 text-primary-400" />
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    variants={itemVariants}
                    className="card-hover"
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-sm mb-1">Completed Today</p>
                            <p className="text-3xl font-bold text-white">
                                {scans?.filter(s => s.status === 'completed').length || 0}
                            </p>
                        </div>
                        <div className="w-12 h-12 bg-success-500/20 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-success-400" />
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    variants={itemVariants}
                    className="card-hover"
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-sm mb-1">Total Vulnerabilities</p>
                            <p className="text-3xl font-bold text-white">
                                {scans?.reduce((acc, scan) => {
                                    if (!scan.findings) return acc
                                    return acc + Object.values(scan.findings).reduce((sum, count) => sum + count, 0)
                                }, 0) || 0}
                            </p>
                        </div>
                        <div className="w-12 h-12 bg-danger-500/20 rounded-lg flex items-center justify-center">
                            <Shield className="w-6 h-6 text-danger-400" />
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
