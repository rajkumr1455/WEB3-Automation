'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    Home,
    Search,
    Shield,
    Zap,
    Eye,
    Filter,
    FileText,
    Activity,
    Settings,
    Github,
    Cpu,
    Globe,
    FileCheck,
    Wrench,
    Radio
} from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Address Scan', href: '/address-scan', icon: Globe },
    { name: 'Guardrail', href: '/guardrail', icon: Shield },
    { name: 'Validator', href: '/validator', icon: FileCheck },
    { name: 'ML-Ops', href: '/mlops', icon: Activity },
    { name: 'Signatures', href: '/signatures', icon: Shield },
    { name: 'Remediator', href: '/remediator', icon: Wrench },
    { name: 'Indexer', href: '/indexer', icon: Radio },
    { name: 'Reconnaissance', href: '/recon', icon: Search },
    { name: 'Static Analysis', href: '/static-analysis', icon: Shield },
    { name: 'Fuzzing', href: '/fuzzing', icon: Zap },
    { name: 'Monitoring', href: '/monitoring', icon: Eye },
    { name: 'Triage', href: '/triage', icon: Filter },
    { name: 'Reports', href: '/reports', icon: FileText },
    { name: 'Agents', href: '/agents', icon: Activity },
    { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Navigation() {
    const pathname = usePathname()

    return (
        <nav className="fixed left-0 top-0 h-screen w-64 glassmorphism border-r border-white/10 flex flex-col">
            {/* Logo */}
            <div className="p-6 border-b border-white/10">
                <div className="flex items-center space-x-3">
                    <div className="relative">
                        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-500 rounded-lg flex items-center justify-center">
                            <Shield className="w-6 h-6 text-white" />
                        </div>
                        <div className="absolute -top-1 -right-1 w-3 h-3 bg-success-500 rounded-full border-2 border-gray-900 animate-pulse" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-white">Web3 Hunter</h1>
                        <p className="text-xs text-gray-400">Bug Bounty AI</p>
                    </div>
                </div>
            </div>

            {/* Navigation Links */}
            <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1 scrollbar-hide">
                {navigation.map((item) => {
                    const isActive = pathname === item.href
                    const Icon = item.icon

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={clsx(
                                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group',
                                isActive
                                    ? 'bg-primary-500/20 text-primary-300 border border-primary-500/30'
                                    : 'text-gray-400 hover:bg-white/5 hover:text-white border border-transparent'
                            )}
                        >
                            <Icon className={clsx(
                                'w-5 h-5 transition-transform duration-200',
                                isActive ? 'text-primary-400' : 'group-hover:scale-110'
                            )} />
                            <span className="font-medium">{item.name}</span>
                        </Link>
                    )
                })}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/10">
                <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center space-x-2">
                        <Cpu className="w-4 h-4" />
                        <span>Ollama + Claude</span>
                    </div>
                    <a
                        href="https://github.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-white transition-colors"
                    >
                        <Github className="w-4 h-4" />
                    </a>
                </div>
            </div>
        </nav>
    )
}
