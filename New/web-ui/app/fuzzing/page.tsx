'use client'

import { Zap, Target, Flame, Search } from 'lucide-react'

export default function FuzzingPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold gradient-text mb-2">Fuzzing</h1>
                <p className="text-gray-400">Foundry, Echidna, and Manticore fuzz testing results</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { icon: Target, label: 'Test Cases', count: '0', color: 'primary' },
                    { icon: Flame, label: 'Crashes Found', count: '0', color: 'danger' },
                    { icon: Search, label: 'Coverage', count: '0%', color: 'success' },
                    { icon: Zap, label: 'Mutations', count: '0', color: 'warning' },
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
                    Fuzzing results will be displayed here after scan execution
                </p>
            </div>
        </div>
    )
}
