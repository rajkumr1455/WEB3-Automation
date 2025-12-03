'use client'

import { Eye, Activity, TrendingUp, AlertCircle } from 'lucide-react'

export default function MonitoringPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold gradient-text mb-2">Real-Time Monitoring</h1>
                <p className="text-gray-400">Mempool analysis, oracle monitoring, and anomaly detection</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { icon: Activity, label: 'Active Monitors', count: '0', color: 'primary' },
                    { icon: AlertCircle, label: 'Alerts', count: '0', color: 'danger' },
                    { icon: TrendingUp, label: 'Transactions', count: '0', color: 'success' },
                    { icon: Eye, label: 'Contracts Watched', count: '0', color: 'warning' },
                ].map((metric) => (
                    <div key={metric.label} className="card-hover">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm mb-1">{metric.label}</p>
                                <p className="text-3xl font-bold text-white">{metric.count}</p>
                            </div>
                            <div className={`w-12 h-12 bg-${metric.color}-500/20 rounded-lg flex items-center justify-center`}>
                                <metric.icon className={`w-6 h-6 text-${metric.color}-400`} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="card-hover">
                <p className="text-center text-gray-400 py-12">
                    Real-time monitoring data will stream here
                </p>
            </div>
        </div>
    )
}
