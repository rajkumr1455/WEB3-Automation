'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { scanAPI, type ScanRequest } from '@/lib/api'
import { Loader2, Rocket } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ScanForm() {
    const [formData, setFormData] = useState<ScanRequest>({
        target_url: '',
        contract_address: '',
        chain: 'ethereum',
    })

    const router = useRouter()
    const queryClient = useQueryClient()

    const { mutate: startScan, isPending } = useMutation({
        mutationFn: (data: ScanRequest) => scanAPI.startScan(data),
        onSuccess: (data) => {
            toast.success(`Scan started successfully! ID: ${data.scan_id.slice(0, 8)}...`)
            queryClient.invalidateQueries({ queryKey: ['scans'] })
            setFormData({ target_url: '', contract_address: '', chain: 'ethereum' })

            // Navigate to scan detail page
            setTimeout(() => {
                router.push(`/scan/${data.scan_id}`)
            }, 500)
        },
        onError: (error: any) => {
            const errorMsg = error.response?.data?.detail || error.message || 'Failed to start scan'
            toast.error(errorMsg)
            console.error('Scan error:', error)
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!formData.target_url) return
        startScan(formData)
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                    Target Repository URL
                </label>
                <input
                    type="url"
                    value={formData.target_url}
                    onChange={(e) => setFormData({ ...formData, target_url: e.target.value })}
                    placeholder="https://github.com/org/repo"
                    className="input"
                    required
                />
                <p className="mt-1 text-xs text-gray-500">
                    GitHub URL of the smart contract repository
                </p>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                    Contract Address (Optional)
                </label>
                <input
                    type="text"
                    value={formData.contract_address}
                    onChange={(e) => setFormData({ ...formData, contract_address: e.target.value })}
                    placeholder="0x..."
                    className="input"
                />
                <p className="mt-1 text-xs text-gray-500">
                    Deployed contract address for live monitoring
                </p>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                    Blockchain
                </label>
                <select
                    value={formData.chain}
                    onChange={(e) => setFormData({ ...formData, chain: e.target.value })}
                    className="input"
                >
                    <option value="ethereum">Ethereum</option>
                    <option value="bsc">Binance Smart Chain</option>
                    <option value="polygon">Polygon</option>
                    <option value="arbitrum">Arbitrum</option>
                    <option value="optimism">Optimism</option>
                    <option value="avalanche">Avalanche</option>
                </select>
            </div>

            <button
                type="submit"
                disabled={isPending || !formData.target_url}
                className="btn-primary w-full flex items-center justify-center space-x-2"
            >
                {isPending ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Starting Scan...</span>
                    </>
                ) : (
                    <>
                        <Rocket className="w-5 h-5" />
                        <span>Launch Scan</span>
                    </>
                )}
            </button>
        </form>
    )
}
