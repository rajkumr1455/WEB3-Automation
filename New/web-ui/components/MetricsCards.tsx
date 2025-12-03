'use client'

import { type ScanStatus, type AgentHealth } from '@/lib/api'
import { Target, AlertTriangle, CheckCircle, Activity } from 'lucide-react'
import { motion } from 'framer-motion'

interface MetricsCardsProps {
    scans?: ScanStatus[]
    agentsHealth?: Record<string, AgentHealth>
}

export default function MetricsCards({ scans, agentsHealth }: MetricsCardsProps) {
    // Defensive: ensure scans is always an array
    const scansList = Array.isArray(scans) ? scans : []

    // Defensive: ensure agentsHealth is always an object
    const agentsHealthObj = agentsHealth && typeof agentsHealth === 'object' ? agentsHealth : {}

    const totalScans = scansList.length
    const activeScans = scansList.filter(s => s.status === 'running').length
    const completedScans = scansList.filter(s => s.status === 'completed').length
    const failedScans = scansList.filter(s => s.status === 'failed').length

    const totalVulns = scansList.reduce((acc, scan) => {
        if (!scan.findings) return acc
        return acc + Object.values(scan.findings).reduce((sum, count) => sum + count, 0)
    }, 0)

    const criticalVulns = scansList.reduce((acc, scan) => {
        return acc + (scan.findings?.critical || 0)
    }, 0)

    const healthyAgents = Object.values(agentsHealthObj).filter(
        a => a.status === 'healthy' || a.status === 'connected'
    ).length

    const totalAgents = Object.keys(agentsHealthObj).length || 8

    const metrics = [
        {
            label: 'Total Scans',
            value: totalScans,
            subtext: `${activeScans} active`,
            icon: Target,
            color: 'primary',
            bgColor: 'bg-primary-500/20',
            textColor: 'text-primary-400',
        },
        {
            label: 'Vulnerabilities Found',
            value: totalVulns,
            subtext: `${criticalVulns} critical`,
            icon: AlertTriangle,
            color: 'danger',
            bgColor: 'bg-danger-500/20',
            textColor: 'text-danger-400',
        },
        {
            label: 'Success Rate',
            value: `${totalScans > 0 ? Math.round((completedScans / totalScans) * 100) : 0}%`,
            subtext: `${completedScans} completed`,
            icon: CheckCircle,
            color: 'success',
            bgColor: 'bg-success-500/20',
            textColor: 'text-success-400',
        },
        {
            label: 'Agents Online',
            value: `${healthyAgents}/${totalAgents}`,
            subtext: 'System health',
            icon: Activity,
            color: healthyAgents === totalAgents ? 'success' : 'warning',
            bgColor: healthyAgents === totalAgents ? 'bg-success-500/20' : 'bg-warning-500/20',
            textColor: healthyAgents === totalAgents ? 'text-success-400' : 'text-warning-400',
        },
    ]

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {metrics.map((metric, index) => {
                const Icon = metric.icon
                return (
                    <motion.div
                        key={metric.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="card-hover"
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <p className="text-gray-400 text-sm mb-1">{metric.label}</p>
                                <p className={`text-4xl font-bold ${metric.textColor}`}>
                                    {metric.value}
                                </p>
                                <p className="text-gray-500 text-xs mt-1">{metric.subtext}</p>
                            </div>
                            <div className={`w-14 h-14 ${metric.bgColor} rounded-xl flex items-center justify-center`}>
                                <Icon className={`w-7 h-7 ${metric.textColor}`} />
                            </div>
                        </div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: '100%' }}
                                transition={{ delay: index * 0.1 + 0.2, duration: 0.5 }}
                                className={`h-full bg-gradient-to-r from-${metric.color}-500 to-${metric.color}-600`}
                            />
                        </div>
                    </motion.div>
                )
            })}
        </div>
    )
}
