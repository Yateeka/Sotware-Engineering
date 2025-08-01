import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface User {
    id: string;
    username: string;
    user_type: string;
    profile: {
        first_name: string;
        last_name: string;
    };
}

interface SystemHealth {
    system_status: string;
    uptime: string;
    database_status: string;
    api_response_time: string;
    active_users: number;
    data_collection_status: string;
    last_data_sync: string;
    storage_usage: string;
    memory_usage: string;
}

interface ModerationItem {
    id: string;
    content_type: string;
    content_id: string;
    title: string;
    description: string;
    priority: 'low' | 'medium' | 'high';
    status: 'pending' | 'approved' | 'rejected';
    reported_by: string;
    created_at: string;
}

interface ModerationQueue {
    queue: ModerationItem[];
    total_pending: number;
    high_priority: number;
    medium_priority: number;
}

const AdminPanel = () => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
    const [moderationQueue, setModerationQueue] = useState<ModerationQueue | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'moderation' | 'users' | 'system'>('overview');
    const [actionMessage, setActionMessage] = useState('');

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const userData = localStorage.getItem('user');
                if (!userData) {
                    router.push('/login');
                    return;
                }

                const parsedUser = JSON.parse(userData);
                
                // Check if user has admin permissions
                if (!['admin', 'moderator'].includes(parsedUser.user_type)) {
                    router.push('/dashboard');
                    return;
                }

                setUser(parsedUser);
                await Promise.all([
                    fetchSystemHealth(),
                    fetchModerationQueue()
                ]);
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const fetchSystemHealth = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/admin/system/health', {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setSystemHealth(data);
            } else {
                console.error('Failed to fetch system health');
            }
        } catch (error) {
            console.error('Error fetching system health:', error);
        }
    };

    const fetchModerationQueue = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/admin/moderation/queue', {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setModerationQueue(data);
            } else {
                console.error('Failed to fetch moderation queue');
            }
        } catch (error) {
            console.error('Error fetching moderation queue:', error);
        }
    };

    const handleModerationAction = async (itemId: string, action: 'approve' | 'reject') => {
        try {
            // Simulate API call
            setActionMessage(`Item ${itemId} ${action}d successfully`);
            
            // Update local state
            if (moderationQueue) {
                const updatedQueue = moderationQueue.queue.map(item => 
                    item.id === itemId 
                        ? { ...item, status: action === 'approve' ? 'approved' : 'rejected' as const }
                        : item
                );
                setModerationQueue({
                    ...moderationQueue,
                    queue: updatedQueue,
                    total_pending: updatedQueue.filter(item => item.status === 'pending').length
                });
            }
            
            setTimeout(() => setActionMessage(''), 3000);
        } catch (error) {
            console.error('Moderation action failed:', error);
            setActionMessage('Action failed. Please try again.');
        }
    };

    const getPriorityBadge = (priority: string) => {
        const priorityConfig = {
            low: { bg: 'bg-gray-100', text: 'text-gray-800' },
            medium: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
            high: { bg: 'bg-red-100', text: 'text-red-800' }
        };

        const config = priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.medium;

        return (
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
                {priority.charAt(0).toUpperCase() + priority.slice(1)}
            </span>
        );
    };

    const getStatusIcon = (status: string) => {
        if (status === 'healthy' || status === 'connected' || status === 'running') {
            return <span className="text-green-500">✓</span>;
        }
        if (status === 'warning') {
            return <span className="text-yellow-500">⚠</span>;
        }
        return <span className="text-red-500">✕</span>;
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!user || !systemHealth) {
        return null;
    }

    return (
        <>
            <Head>
                <title>Admin Panel - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
                                <p className="text-gray-600">System administration and content moderation</p>
                            </div>
                            <div className="flex gap-3">
                                <Link 
                                    href="/analytics"
                                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                >
                                    📊 View Analytics
                                </Link>
                                <Link 
                                    href="/dashboard"
                                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                >
                                    ← Back to Dashboard
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {/* Navigation Tabs */}
                    <div className="bg-white rounded-lg shadow mb-8">
                        <div className="border-b border-gray-200">
                            <nav className="-mb-px flex space-x-8 px-6">
                                {[
                                    { id: 'overview', label: 'Overview', icon: '📊' },
                                    { id: 'moderation', label: 'Moderation', icon: '🛡️', badge: moderationQueue?.total_pending },
                                    { id: 'users', label: 'Users', icon: '👥' },
                                    { id: 'system', label: 'System', icon: '⚙️' }
                                ].map((tab) => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                        className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                                            activeTab === tab.id
                                                ? 'border-primary text-primary'
                                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }`}
                                    >
                                        <span className="mr-2">{tab.icon}</span>
                                        {tab.label}
                                        {tab.badge && tab.badge > 0 && (
                                            <span className="ml-2 bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full">
                                                {tab.badge}
                                            </span>
                                        )}
                                    </button>
                                ))}
                            </nav>
                        </div>
                    </div>

                    {/* Action Message */}
                    {actionMessage && (
                        <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">
                            {actionMessage}
                        </div>
                    )}

                    {/* Tab Content */}
                    {activeTab === 'overview' && (
                        <div className="space-y-8">
                            {/* System Status Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="flex items-center justify-center mb-2">
                                        {getStatusIcon(systemHealth.system_status)}
                                        <span className="ml-2 text-lg font-semibold text-gray-900">System</span>
                                    </div>
                                    <div className="text-sm text-gray-600">{systemHealth.system_status}</div>
                                    <div className="text-xs text-gray-500 mt-1">Uptime: {systemHealth.uptime}</div>
                                </div>
                                
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="flex items-center justify-center mb-2">
                                        {getStatusIcon(systemHealth.database_status)}
                                        <span className="ml-2 text-lg font-semibold text-gray-900">Database</span>
                                    </div>
                                    <div className="text-sm text-gray-600">{systemHealth.database_status}</div>
                                    <div className="text-xs text-gray-500 mt-1">Response: {systemHealth.api_response_time}</div>
                                </div>
                                
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-primary mb-2">{systemHealth.active_users}</div>
                                    <div className="text-sm text-gray-600">Active Users</div>
                                    <div className="text-xs text-gray-500 mt-1">Currently online</div>
                                </div>
                                
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="flex items-center justify-center mb-2">
                                        {getStatusIcon(systemHealth.data_collection_status)}
                                        <span className="ml-2 text-lg font-semibold text-gray-900">Data Sync</span>
                                    </div>
                                    <div className="text-sm text-gray-600">{systemHealth.data_collection_status}</div>
                                    <div className="text-xs text-gray-500 mt-1">
                                        Last: {new Date(systemHealth.last_data_sync).toLocaleTimeString()}
                                    </div>
                                </div>
                            </div>

                            {/* Quick Actions */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                            {/* Quick Actions */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                    <button
                                        onClick={() => setActiveTab('moderation')}
                                        className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left"
                                    >
                                        <div className="text-lg mb-2">🛡️</div>
                                        <div className="font-medium">Review Queue</div>
                                        <div className="text-sm text-gray-500">{moderationQueue?.total_pending} pending</div>
                                    </button>
                                    
                                    <button
                                        onClick={() => fetchSystemHealth()}
                                        className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left"
                                    >
                                        <div className="text-lg mb-2">🔄</div>
                                        <div className="font-medium">Refresh Data</div>
                                        <div className="text-sm text-gray-500">Update all metrics</div>
                                    </button>
                                    
                                    <button className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left">
                                        <div className="text-lg mb-2">📧</div>
                                        <div className="font-medium">Send Alerts</div>
                                        <div className="text-sm text-gray-500">Notify users</div>
                                    </button>
                                    
                                    <button className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left">
                                        <div className="text-lg mb-2">🔐</div>
                                        <div className="font-medium">Backup Data</div>
                                        <div className="text-sm text-gray-500">System backup</div>
                                    </button>
                                </div>
                            </div>

                            {/* Recent Activity */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center">
                                            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                                                <span className="text-green-600 text-sm">✓</span>
                                            </div>
                                            <div>
                                                <div className="font-medium text-sm">Protest report verified</div>
                                                <div className="text-xs text-gray-500">Atlanta Climate Rally - 5 minutes ago</div>
                                            </div>
                                        </div>
                                        <span className="text-xs text-gray-400">5:42 PM</span>
                                    </div>
                                    
                                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center">
                                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                                                <span className="text-blue-600 text-sm">👤</span>
                                            </div>
                                            <div>
                                                <div className="font-medium text-sm">New user registered</div>
                                                <div className="text-xs text-gray-500">Journalist from CNN - 12 minutes ago</div>
                                            </div>
                                        </div>
                                        <span className="text-xs text-gray-400">5:35 PM</span>
                                    </div>
                                    
                                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center">
                                            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                                                <span className="text-yellow-600 text-sm">⚠</span>
                                            </div>
                                            <div>
                                                <div className="font-medium text-sm">Content flagged for review</div>
                                                <div className="text-xs text-gray-500">User report needs moderation - 18 minutes ago</div>
                                            </div>
                                        </div>
                                        <span className="text-xs text-gray-400">5:29 PM</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'moderation' && moderationQueue && (
                        <div className="space-y-6">
                            {/* Moderation Stats */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-yellow-600">{moderationQueue.total_pending}</div>
                                    <div className="text-sm text-gray-600">Total Pending</div>
                                </div>
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-red-600">{moderationQueue.high_priority}</div>
                                    <div className="text-sm text-gray-600">High Priority</div>
                                </div>
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-orange-600">{moderationQueue.medium_priority}</div>
                                    <div className="text-sm text-gray-600">Medium Priority</div>
                                </div>
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-green-600">
                                        {moderationQueue.queue.filter(item => item.status === 'approved').length}
                                    </div>
                                    <div className="text-sm text-gray-600">Approved Today</div>
                                </div>
                            </div>

                            {/* Moderation Queue */}
                            <div className="bg-white rounded-lg shadow">
                                <div className="p-6 border-b border-gray-200">
                                    <h3 className="text-lg font-semibold text-gray-900">Moderation Queue</h3>
                                    <p className="text-sm text-gray-600">Review and moderate flagged content</p>
                                </div>
                                
                                <div className="divide-y divide-gray-200">
                                    {moderationQueue.queue.filter(item => item.status === 'pending').length > 0 ? (
                                        moderationQueue.queue.filter(item => item.status === 'pending').map((item) => (
                                            <div key={item.id} className="p-6">
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-3 mb-2">
                                                            <h4 className="text-lg font-medium text-gray-900">{item.title}</h4>
                                                            {getPriorityBadge(item.priority)}
                                                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                                                {item.content_type.replace('_', ' ')}
                                                            </span>
                                                        </div>
                                                        
                                                        <p className="text-gray-600 mb-3">{item.description}</p>
                                                        
                                                        <div className="flex items-center gap-4 text-sm text-gray-500">
                                                            <span>📅 {new Date(item.created_at).toLocaleString()}</span>
                                                            <span>🚩 Reported by: {item.reported_by}</span>
                                                            <span>🆔 Content ID: {item.content_id}</span>
                                                        </div>
                                                    </div>
                                                    
                                                    <div className="ml-6 flex flex-col gap-2">
                                                        <button
                                                            onClick={() => handleModerationAction(item.id, 'approve')}
                                                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                                                        >
                                                            ✓ Approve
                                                        </button>
                                                        <button
                                                            onClick={() => handleModerationAction(item.id, 'reject')}
                                                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                                                        >
                                                            ✕ Reject
                                                        </button>
                                                        <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                                                            👁️ Review
                                                        </button>
                                                    </div>
                                                </div>

                                                {item.priority === 'high' && (
                                                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                                                        <div className="flex items-center">
                                                            <span className="text-red-600 mr-2">⚠️</span>
                                                            <span className="text-sm font-medium text-red-800">High Priority Review Required</span>
                                                        </div>
                                                        <p className="text-sm text-red-700 mt-1">
                                                            This content has been flagged as potentially harmful or requiring immediate attention.
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        ))
                                    ) : (
                                        <div className="p-12 text-center">
                                            <div className="text-gray-400 text-4xl mb-4">✨</div>
                                            <h3 className="text-lg font-medium text-gray-900 mb-2">All Clear!</h3>
                                            <p className="text-gray-600">No items pending moderation at this time.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'users' && (
                        <div className="space-y-6">
                            {/* User Stats */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-blue-600">2,847</div>
                                    <div className="text-sm text-gray-600">Total Users</div>
                                </div>
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-green-600">156</div>
                                    <div className="text-sm text-gray-600">Active Today</div>
                                </div>
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-yellow-600">23</div>
                                    <div className="text-sm text-gray-600">Pending Verification</div>
                                </div>
                                <div className="bg-white rounded-lg shadow p-6 text-center">
                                    <div className="text-2xl font-bold text-purple-600">12</div>
                                    <div className="text-sm text-gray-600">New This Week</div>
                                </div>
                            </div>

                            {/* User Management */}
                            <div className="bg-white rounded-lg shadow">
                                <div className="p-6 border-b border-gray-200">
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <h3 className="text-lg font-semibold text-gray-900">User Management</h3>
                                            <p className="text-sm text-gray-600">Manage user accounts and permissions</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                placeholder="Search users..."
                                                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                            />
                                            <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                                                Search
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="p-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        <div className="p-4 border border-gray-200 rounded-lg">
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="font-medium">Pending Verifications</div>
                                                <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">23</span>
                                            </div>
                                            <p className="text-sm text-gray-600 mb-3">Users awaiting account verification</p>
                                            <button className="w-full px-3 py-2 bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100">
                                                Review Queue
                                            </button>
                                        </div>
                                        
                                        <div className="p-4 border border-gray-200 rounded-lg">
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="font-medium">Role Changes</div>
                                                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">5</span>
                                            </div>
                                            <p className="text-sm text-gray-600 mb-3">Requests for role upgrades</p>
                                            <button className="w-full px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">
                                                Review Requests
                                            </button>
                                        </div>
                                        
                                        <div className="p-4 border border-gray-200 rounded-lg">
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="font-medium">Suspended Accounts</div>
                                                <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">2</span>
                                            </div>
                                            <p className="text-sm text-gray-600 mb-3">Temporarily suspended users</p>
                                            <button className="w-full px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100">
                                                Manage Suspensions
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'system' && systemHealth && (
                        <div className="space-y-6">
                            {/* System Performance */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">System Performance</h3>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600">API Response Time</span>
                                            <span className="font-medium text-green-600">{systemHealth.api_response_time}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600">Memory Usage</span>
                                            <span className="font-medium text-blue-600">{systemHealth.memory_usage}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600">Storage Usage</span>
                                            <span className="font-medium text-yellow-600">{systemHealth.storage_usage}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600">System Uptime</span>
                                            <span className="font-medium text-green-600">{systemHealth.uptime}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-white rounded-lg shadow p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Collection</h3>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600">Collection Status</span>
                                            <span className="flex items-center">
                                                {getStatusIcon(systemHealth.data_collection_status)}
                                                <span className="ml-2 font-medium">{systemHealth.data_collection_status}</span>
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600">Last Sync</span>
                                            <span className="font-medium">{new Date(systemHealth.last_data_sync).toLocaleTimeString()}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600">Database Status</span>
                                            <span className="flex items-center">
                                                {getStatusIcon(systemHealth.database_status)}
                                                <span className="ml-2 font-medium">{systemHealth.database_status}</span>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* System Controls */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Controls</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                    <button className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left">
                                        <div className="text-lg mb-2">🔄</div>
                                        <div className="font-medium">Restart Services</div>
                                        <div className="text-sm text-gray-500">Restart background processes</div>
                                    </button>
                                    
                                    <button className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left">
                                        <div className="text-lg mb-2">📊</div>
                                        <div className="font-medium">Force Data Sync</div>
                                        <div className="text-sm text-gray-500">Manually trigger data collection</div>
                                    </button>
                                    
                                    <button className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left">
                                        <div className="text-lg mb-2">🗄️</div>
                                        <div className="font-medium">Database Backup</div>
                                        <div className="text-sm text-gray-500">Create system backup</div>
                                    </button>
                                    
                                    <button className="p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 text-left">
                                        <div className="text-lg mb-2">🧹</div>
                                        <div className="font-medium">Clear Cache</div>
                                        <div className="text-sm text-gray-500">Clear system cache</div>
                                    </button>
                                </div>
                            </div>

                            {/* Logs Preview */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-lg font-semibold text-gray-900">Recent System Logs</h3>
                                    <button className="text-primary hover:text-primary/80 text-sm font-medium">
                                        View All Logs →
                                    </button>
                                </div>
                                
                                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                                    <div className="space-y-1">
                                        <div>[2024-07-30 17:42:33] INFO: Data collection completed successfully</div>
                                        <div>[2024-07-30 17:42:31] INFO: Processing 127 new protest reports</div>
                                        <div>[2024-07-30 17:42:28] INFO: GDELT API sync started</div>
                                        <div>[2024-07-30 17:41:55] INFO: User authentication: researcher@university.edu</div>
                                        <div>[2024-07-30 17:41:22] INFO: Database connection established</div>
                                        <div>[2024-07-30 17:40:18] WARN: Rate limit approached for NewsAPI</div>
                                        <div>[2024-07-30 17:39:45] INFO: Protest verification completed: ID #1847</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default AdminPanel;