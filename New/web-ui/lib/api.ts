import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

const api = axios.create({
    baseURL: API_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Types
export interface ScanRequest {
    target_url: string
    contract_address?: string
    chain?: string
}

export interface ScanStatus {
    scan_id: string
    status: 'pending' | 'running' | 'completed' | 'failed'
    progress: number
    current_stage?: string
    target_url?: string
    contract_address?: string
    findings?: Record<string, number>
    results?: Record<string, any>
    error?: string
    started_at?: string
    completed_at?: string
    duration_seconds?: number
}

export interface Finding {
    id: string
    title: string
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
    confidence: string
    description: string
    impact?: string
    recommendation?: string
    location?: string
    source?: string
}

export interface AgentHealth {
    status: string
    service: string
    details?: any
}

// API Functions
export const scanAPI = {
    // Start a new scan
    startScan: async (data: ScanRequest): Promise<ScanStatus> => {
        const response = await api.post('/scan', data)
        return response.data
    },

    // Get scan status
    getScanStatus: async (scanId: string): Promise<ScanStatus> => {
        const response = await api.get(`/scan/${scanId}`)
        return response.data
    },

    // List all scans
    listScans: async (): Promise<ScanStatus[]> => {
        try {
            const response = await api.get('/scans')
            // Ensure response.data is an array
            return Array.isArray(response.data) ? response.data : []
        } catch (error) {
            console.error('Failed to fetch scans:', error)
            return [] // Return empty array on error
        }
    },

    // Cancel a scan
    cancelScan: async (scanId: string): Promise<void> => {
        await api.post(`/scan/${scanId}/cancel`)
    },
}

export const agentAPI = {
    // Get health status of all agents
    getAgentsHealth: async (): Promise<Record<string, AgentHealth>> => {
        const agents = [
            { name: 'orchestrator', port: 8001 },
            { name: 'llm-router', port: 8000 },
            { name: 'recon-agent', port: 8002 },
            { name: 'static-agent', port: 8003 },
            { name: 'fuzzing-agent', port: 8004 },
            { name: 'monitoring-agent', port: 8005 },
            { name: 'triage-agent', port: 8006 },
            { name: 'reporting-agent', port: 8007 },
        ]

        const healthChecks = await Promise.allSettled(
            agents.map(async (agent) => {
                try {
                    const response = await axios.get(
                        `http://localhost:${agent.port}/health`,
                        { timeout: 5000 }
                    )
                    return { name: agent.name, data: response.data }
                } catch (error) {
                    return {
                        name: agent.name,
                        data: { status: 'unhealthy', service: agent.name },
                    }
                }
            })
        )

        const result: Record<string, AgentHealth> = {}
        healthChecks.forEach((check, index) => {
            if (check.status === 'fulfilled') {
                result[check.value.name] = check.value.data
            } else {
                result[agents[index].name] = {
                    status: 'error',
                    service: agents[index].name,
                }
            }
        })

        return result
    },

    // Get LLM router models
    getModels: async (): Promise<any> => {
        const response = await axios.get('http://localhost:8000/models')
        return response.data
    },

    // Get LLM router health
    getLLMRouterHealth: async (): Promise<any> => {
        const response = await axios.get('http://localhost:8000/health')
        return response.data
    },
}

export const reportsAPI = {
    // Get report content
    getReport: async (scanId: string, type: 'immunefi' | 'hackenproof' | 'json'): Promise<string> => {
        const response = await api.get(`/reports/${scanId}/${type}`)
        return response.data
    },

    // Download report
    downloadReport: (scanId: string, type: string) => {
        window.open(`${API_URL}/reports/${scanId}/${type}/download`, '_blank')
    },
}

export const metricsAPI = {
    // Get dashboard metrics
    getDashboardMetrics: async (): Promise<any> => {
        const response = await api.get('/metrics/dashboard')
        return response.data
    },

    // Get Prometheus metrics
    getPrometheusMetrics: async (): Promise<string> => {
        const response = await axios.get('http://localhost:9090/api/v1/query_range', {
            params: {
                query: 'up',
                start: Math.floor(Date.now() / 1000) - 3600,
                end: Math.floor(Date.now() / 1000),
                step: 60,
            },
        })
        return response.data
    },
}

export default api
