'use client'

import { FileText, Download, Send, CheckCircle } from 'lucide-react'

export default function ReportsPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold gradient-text mb-2">Security Reports</h1>
                <p className="text-gray-400">Generate and export reports for Immunefi and HackenProof</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { icon: FileText, label: 'Total Reports', count: '0', color: 'primary' },
                    { icon: Send, label: 'Submitted', count: '0', color: 'success' },
                    { icon: Download, label: 'Downloaded', count: '0', color: 'warning' },
                    { icon: CheckCircle, label: 'Accepted', count: '0', color: 'purple' },
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
                    Generated reports will be listed here
                </p>
            </div>
        </div>
    )
}
