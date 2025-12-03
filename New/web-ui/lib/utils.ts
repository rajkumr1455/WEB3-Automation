import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
    return new Date(date).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

export function formatDuration(ms: number): string {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)

    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`
    } else {
        return `${seconds}s`
    }
}

export function getSeverityColor(severity: string): string {
    switch (severity.toLowerCase()) {
        case 'critical':
            return 'text-danger-400 bg-danger-500/20 border-danger-500/30'
        case 'high':
            return 'text-warning-400 bg-warning-500/20 border-warning-500/30'
        case 'medium':
            return 'text-primary-400 bg-primary-500/20 border-primary-500/30'
        case 'low':
            return 'text-success-400 bg-success-500/20 border-success-500/30'
        default:
            return 'text-gray-400 bg-gray-500/20 border-gray-500/30'
    }
}

export function getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
        case 'healthy':
        case 'connected':
        case 'completed':
            return 'text-success-400 bg-success-500/20'
        case 'running':
        case 'pending':
            return 'text-primary-400 bg-primary-500/20'
        case 'failed':
        case 'error':
        case 'unhealthy':
            return 'text-danger-400 bg-danger-500/20'
        default:
            return 'text-gray-400 bg-gray-500/20'
    }
}
