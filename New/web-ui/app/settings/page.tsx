'use client'

import { useState } from 'react'
import { Settings as SettingsIcon, Save, Cpu, Bell, Shield } from 'lucide-react'
import { motion } from 'framer-motion'

export default function SettingsPage() {
    const [settings, setSettings] = useState({
        defaultChain: 'ethereum',
        llmPreference: 'auto',
        notificationsEnabled: true,
        slackWebhook: '',
        githubToken: '',
        claudeApiKey: '',
    })

    const [saved, setSaved] = useState(false)

    const handleSave = () => {
        // In a real app, this would save to backend
        localStorage.setItem('web3_hunter_settings', JSON.stringify(settings))
        setSaved(true)
        setTimeout(() => setSaved(false), 3000)
    }

    return (
        <div className="space-y-8 max-w-4xl">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold gradient-text mb-2">Settings</h1>
                <p className="text-gray-400">Configure your Web3 Hunter preferences</p>
            </div>

            {/* LLM Configuration */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card-hover"
            >
                <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center">
                        <Cpu className="w-5 h-5 text-primary-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-white">LLM Configuration</h2>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Default LLM Strategy
                        </label>
                        <select
                            value={settings.llmPreference}
                            onChange={(e) => setSettings({ ...settings, llmPreference: e.target.value })}
                            className="input"
                        >
                            <option value="auto">Auto (Hybrid - Recommended)</option>
                            <option value="local-only">Local Only (Ollama)</option>
                            <option value="cloud-only">Cloud Only (Claude)</option>
                        </select>
                        <p className="mt-1 text-xs text-gray-500">
                            Auto uses local models for fast tasks and Claude for complex reasoning
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Claude API Key
                        </label>
                        <input
                            type="password"
                            value={settings.claudeApiKey}
                            onChange={(e) => setSettings({ ...settings, claudeApiKey: e.target.value })}
                            placeholder="sk-ant-xxxxx"
                            className="input"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            Required for cloud-based reasoning and report finalization
                        </p>
                    </div>
                </div>
            </motion.div>

            {/* Scan Defaults */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="card-hover"
            >
                <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-success-500/20 rounded-lg flex items-center justify-center">
                        <Shield className="w-5 h-5 text-success-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-white">Scan Defaults</h2>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Default Blockchain
                        </label>
                        <select
                            value={settings.defaultChain}
                            onChange={(e) => setSettings({ ...settings, defaultChain: e.target.value })}
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
                </div>
            </motion.div>

            {/* Notifications */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="card-hover"
            >
                <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                        <Bell className="w-5 h-5 text-purple-400" />
                    </div>
                    <h2 className="text-2xl font-semibold text-white">Notifications</h2>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-white font-medium">Enable Notifications</p>
                            <p className="text-sm text-gray-400">Receive alerts for completed scans</p>
                        </div>
                        <button
                            onClick={() => setSettings({ ...settings, notificationsEnabled: !settings.notificationsEnabled })}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${settings.notificationsEnabled ? 'bg-primary-500' : 'bg-gray-600'
                                }`}
                        >
                            <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${settings.notificationsEnabled ? 'translate-x-6' : 'translate-x-1'
                                    }`}
                            />
                        </button>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Slack Webhook URL
                        </label>
                        <input
                            type="url"
                            value={settings.slackWebhook}
                            onChange={(e) => setSettings({ ...settings, slackWebhook: e.target.value })}
                            placeholder="https://hooks.slack.com/services/..."
                            className="input"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            GitHub Personal Access Token
                        </label>
                        <input
                            type="password"
                            value={settings.githubToken}
                            onChange={(e) => setSettings({ ...settings, githubToken: e.target.value })}
                            placeholder="ghp_xxxxx"
                            className="input"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            For creating private issues with scan results
                        </p>
                    </div>
                </div>
            </motion.div>

            {/* Save Button */}
            <div className="flex items-center justify-end space-x-4">
                {saved && (
                    <motion.span
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-success-400 text-sm"
                    >
                        Settings saved successfully!
                    </motion.span>
                )}
                <button
                    onClick={handleSave}
                    className="btn-primary flex items-center space-x-2"
                >
                    <Save className="w-4 h-4" />
                    <span>Save Settings</span>
                </button>
            </div>
        </div>
    )
}
