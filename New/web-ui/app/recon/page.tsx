'use client'

import { Search, Database, FileText, Globe } from 'lucide-react'

export default function ReconPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold gradient-text mb-2">Reconnaissance</h1>
                <p className="text-gray-400">Repository mapping, ABI extraction, and attack surface discovery</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { icon: Search, label: 'Contract Discovery', count: '0', color: 'primary' },
                    { icon: Database, label: 'ABIs Extracted', count: '0', color: 'success' },
                    { icon: FileText, label: 'Dependencies', count: '0', color: 'warning' },
                    { icon: Globe, label: 'RPC Endpoints', count: '0', color: 'purple' },
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
                    Start a scan to see reconnaissance results here
                </p>
            </div>
        </div>
    )
}
