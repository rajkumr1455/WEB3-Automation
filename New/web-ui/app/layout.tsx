import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Navigation from '@/components/Navigation'
import { Providers } from './providers'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'Web3 Bounty Hunter - Security Automation Platform',
    description: 'Multi-agent Web3 security automation with hybrid AI',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <Providers>
                    <Navigation />
                    <main className="ml-64 p-8">
                        {children}
                    </main>
                    <Toaster
                        position="top-right"
                        toastOptions={{
                            duration: 4000,
                            style: {
                                background: '#1f2937',
                                color: '#f3f4f6',
                                border: '1px solid #374151',
                            },
                            success: {
                                iconTheme: {
                                    primary: '#10b981',
                                    secondary: '#fff',
                                },
                            },
                            error: {
                                iconTheme: {
                                    primary: '#ef4444',
                                    secondary: '#fff',
                                },
                            },
                        }}
                    />
                </Providers>
            </body>
        </html>
    )
}
