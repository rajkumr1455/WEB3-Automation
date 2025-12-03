'use client'

import { Shield, AlertTriangle, Bug, CheckCircle } from 'lucide-react'

export default function StaticAnalysisPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold gradient-text mb-2">Static Analysis</h1>
                <p className="text-gray-400">Slither, Mythril, and Semgrep vulnerability detection</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { icon: AlertTriangle, label: 'Critical', count: '0', color: 'danger' },
                    { icon: Bug, label: 'High', count: '0', color: 'warning' },
                    { icon: Shield, label: 'Medium', count: '0', color: 'primary' },
                    { icon: CheckCircle, label: 'Low', count: '0', color: 'success' },
                ].map((metric) => (
                    <div key={metric.label} className="card-hover">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className={`text-${metric.color}-400 text-sm font-semibold mb-1`}>{metric.label}</p>
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
                    Static analysis results will appear here after a scan completes
                </p>
            </div>
        </div>
    )
}
