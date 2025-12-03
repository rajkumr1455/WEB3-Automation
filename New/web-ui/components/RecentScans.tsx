'use client'

import { type ScanStatus } from '@/lib/api'
import { formatDate, getSeverityColor, getStatusColor } from '@/lib/utils'
import { Clock, ExternalLink, AlertTriangle } from 'lucide-react'
import Link from 'next/link'

interface RecentScansProps {
    scans: ScanStatus[]
}

export function RecentScans({ scans }: RecentScansProps) {
    if (!scans || scans.length === 0) {
        return (
            <div className="text-center py-12 text-gray-400">
                <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No scans yet. Start your first scan to begin!</p>
            </div>
        )
    }

    return (
        <div className="space-y-3 max-h-96 overflow-y-auto pr-2 scrollbar-hide">
            {scans.slice(0, 10).map((scan) => (
                <div
                    key={scan.scan_id}
                    className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 hover:border-white/20 transition-all group"
                >
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                                <span className="text-sm font-mono text-gray-400">
                                    #{scan.scan_id.slice(0, 8)}
                                </span>
                                <span className={`badge ${getStatusColor(scan.status)}`}>
                                    {scan.status}
                                </span>
                            </div>
                            <p className="text-white font-medium truncate">
                                {scan.target_url ? new URL(scan.target_url).pathname : 'N/A'}
                            </p>
                        </div>
                        <Link
                            href={`/scan/${scan.scan_id}`}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <ExternalLink className="w-4 h-4 text-gray-400 hover:text-white" />
                        </Link>
                    </div>

                    {/* Progress Bar */}
                    {scan.status === 'running' && (
                        <div className="mb-3">
                            <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                                <span>{scan.current_stage || 'Processing'}</span>
                                <span>{scan.progress}%</span>
                            </div>
                            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-primary-500 to-purple-500 transition-all duration-300"
                                    style={{ width: `${scan.progress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {/* Findings Summary */}
                    {scan.findings && (
                        <div className="flex items-center space-x-4 text-xs">
                            {['critical', 'high', 'medium', 'low'].map((severity) => {
                                const count = scan.findings?.[severity] || 0
                                if (count === 0) return null
                                return (
                                    <div key={severity} className="flex items-center space-x-1">
                                        <div className={`w-2 h-2 rounded-full ${getSeverityColor(severity)}`} />
                                        <span className="text-gray-400">{count}</span>
                                    </div>
                                )
                            })}
                        </div>
                    )}

                    {/* Timestamp */}
                    <div className="flex items-center space-x-1 text-xs text-gray-500 mt-2">
                        <Clock className="w-3 h-3" />
                        <span>{formatDate(scan.started_at || new Date().toISOString())}</span>
                    </div>
                </div>
            ))}
        </div>
    )
}
