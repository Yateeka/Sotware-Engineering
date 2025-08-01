import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface Report {
    id: string;
    title: string;
    description: string;
    verification_status: 'pending' | 'verified' | 'rejected';
    priority_level: 'low' | 'medium' | 'high' | 'critical';
    created_at: string;
    credibility_score: number;
}

interface User {
    id: string;
    username: string;
    user_type: string;
    profile: {
        first_name: string;
        last_name: string;
    };
}

const MyReportsPage = () => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [reports, setReports] = useState<Report[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'pending' | 'verified' | 'rejected'>('all');
    const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'priority' | 'status'>('newest');

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const userData = localStorage.getItem('user');
                if (!userData) {
                    router.push('/login');
                    return;
                }

                const parsedUser = JSON.parse(userData);
                
                // Check if user has permission to view reports
                if (!['activist', 'ngo_worker', 'journalist', 'admin'].includes(parsedUser.user_type)) {
                    router.push('/dashboard');
                    return;
                }

                setUser(parsedUser);
                await fetchReports();
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const fetchReports = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/reports/my-reports', {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setReports(data.reports);
            } else {
                console.error('Failed to fetch reports');
            }
        } catch (error) {
            console.error('Error fetching reports:', error);
        }
    };

    const getStatusBadge = (status: string) => {
        const statusConfig = {
            pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⏳' },
            verified: { bg: 'bg-green-100', text: 'text-green-800', icon: '✓' },
            rejected: { bg: 'bg-red-100', text: 'text-red-800', icon: '✕' }
        };

        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;

        return (
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
                {config.icon} {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        );
    };

    const getPriorityBadge = (priority: string) => {
        const priorityConfig = {
            low: { bg: 'bg-gray-100', text: 'text-gray-800' },
            medium: { bg: 'bg-blue-100', text: 'text-blue-800' },
            high: { bg: 'bg-orange-100', text: 'text-orange-800' },
            critical: { bg: 'bg-red-100', text: 'text-red-800' }
        };

        const config = priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.medium;

        return (
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
                {priority.charAt(0).toUpperCase() + priority.slice(1)}
            </span>
        );
    };

    const getCredibilityColor = (score: number) => {
        if (score >= 0.8) return 'text-green-600';
        if (score >= 0.6) return 'text-yellow-600';
        return 'text-red-600';
    };

    const filteredAndSortedReports = reports
        .filter(report => {
            if (filter === 'all') return true;
            return report.verification_status === filter;
        })
        .sort((a, b) => {
            switch (sortBy) {
                case 'newest':
                    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
                case 'oldest':
                    return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
                case 'priority':
                    const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
                    return priorityOrder[b.priority_level as keyof typeof priorityOrder] - 
                           priorityOrder[a.priority_level as keyof typeof priorityOrder];
                case 'status':
                    return a.verification_status.localeCompare(b.verification_status);
                default:
                    return 0;
            }
        });

    const getStatusCounts = () => {
        return {
            all: reports.length,
            pending: reports.filter(r => r.verification_status === 'pending').length,
            verified: reports.filter(r => r.verification_status === 'verified').length,
            rejected: reports.filter(r => r.verification_status === 'rejected').length,
        };
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!user) {
        return null;
    }

    const statusCounts = getStatusCounts();

    return (
        <>
            <Head>
                <title>My Reports - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">My Reports</h1>
                                <p className="text-gray-600">Track the status of your submitted protest reports</p>
                            </div>
                            <div className="flex gap-3">
                                <Link 
                                    href="/submit-report"
                                    className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                                >
                                    + Submit New Report
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
                    {/* Statistics Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-2xl font-bold text-gray-900">{statusCounts.all}</div>
                            <div className="text-sm text-gray-600">Total Reports</div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-2xl font-bold text-yellow-600">{statusCounts.pending}</div>
                            <div className="text-sm text-gray-600">Pending Review</div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-2xl font-bold text-green-600">{statusCounts.verified}</div>
                            <div className="text-sm text-gray-600">Verified</div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-2xl font-bold text-red-600">{statusCounts.rejected}</div>
                            <div className="text-sm text-gray-600">Rejected</div>
                        </div>
                    </div>

                    {/* Filters and Sort */}
                    <div className="bg-white rounded-lg shadow mb-6">
                        <div className="p-6 border-b border-gray-200">
                            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                                {/* Status Filter */}
                                <div className="flex items-center gap-4">
                                    <label className="text-sm font-medium text-gray-700">Filter by status:</label>
                                    <div className="flex gap-2">
                                        {(['all', 'pending', 'verified', 'rejected'] as const).map((status) => (
                                            <button
                                                key={status}
                                                onClick={() => setFilter(status)}
                                                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                                                    filter === status
                                                        ? 'bg-primary text-white'
                                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                                }`}
                                            >
                                                {status.charAt(0).toUpperCase() + status.slice(1)} 
                                                {status === 'all' ? ` (${statusCounts.all})` : ` (${statusCounts[status]})`}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Sort Options */}
                                <div className="flex items-center gap-4">
                                    <label className="text-sm font-medium text-gray-700">Sort by:</label>
                                    <select
                                        value={sortBy}
                                        onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                                        className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary"
                                    >
                                        <option value="newest">Newest First</option>
                                        <option value="oldest">Oldest First</option>
                                        <option value="priority">Priority</option>
                                        <option value="status">Status</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Reports List */}
                        <div className="divide-y divide-gray-200">
                            {filteredAndSortedReports.length > 0 ? (
                                filteredAndSortedReports.map((report) => (
                                    <div key={report.id} className="p-6 hover:bg-gray-50">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="text-lg font-semibold text-gray-900">
                                                        {report.title}
                                                    </h3>
                                                    {getStatusBadge(report.verification_status)}
                                                    {getPriorityBadge(report.priority_level)}
                                                </div>
                                                
                                                <p className="text-gray-600 mb-3 line-clamp-2">
                                                    {report.description}
                                                </p>
                                                
                                                <div className="flex items-center gap-4 text-sm text-gray-500">
                                                    <span>📅 {new Date(report.created_at).toLocaleDateString()}</span>
                                                    <span>📊 Credibility: 
                                                        <span className={`font-medium ml-1 ${getCredibilityColor(report.credibility_score)}`}>
                                                            {(report.credibility_score * 100).toFixed(0)}%
                                                        </span>
                                                    </span>
                                                    <span>🆔 ID: {report.id}</span>
                                                </div>
                                            </div>
                                            
                                            <div className="ml-4 flex flex-col gap-2">
                                                {report.verification_status === 'pending' && (
                                                    <div className="text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
                                                        Under Review
                                                    </div>
                                                )}
                                                {report.verification_status === 'verified' && (
                                                    <div className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                                                        Published
                                                    </div>
                                                )}
                                                {report.verification_status === 'rejected' && (
                                                    <div className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                                                        Needs Revision
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Status-specific information */}
                                        {report.verification_status === 'rejected' && (
                                            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                                                <h4 className="text-sm font-medium text-red-800 mb-1">Feedback:</h4>
                                                <p className="text-sm text-red-700">
                                                    Report requires additional verification or more detailed information. 
                                                    Please review and resubmit with supporting evidence.
                                                </p>
                                            </div>
                                        )}

                                        {report.verification_status === 'verified' && (
                                            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <h4 className="text-sm font-medium text-green-800">Report Verified & Published</h4>
                                                        <p className="text-sm text-green-700">Your report is now visible to all platform users.</p>
                                                    </div>
                                                    <button className="text-green-600 hover:text-green-800 text-sm font-medium">
                                                        View Public Page →
                                                    </button>
                                                </div>
                                            </div>
                                        )}

                                        {report.verification_status === 'pending' && (
                                            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                                <div className="flex items-center gap-2">
                                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                                                    <h4 className="text-sm font-medium text-yellow-800">Verification in Progress</h4>
                                                </div>
                                                <p className="text-sm text-yellow-700 mt-1">
                                                    Our team is reviewing your report. This typically takes 2-4 hours during business hours.
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <div className="p-12 text-center">
                                    <div className="text-gray-400 text-4xl mb-4">📋</div>
                                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                                        {filter === 'all' ? 'No reports submitted yet' : `No ${filter} reports`}
                                    </h3>
                                    <p className="text-gray-600 mb-4">
                                        {filter === 'all' 
                                            ? 'Start contributing to the platform by submitting your first protest report.'
                                            : `You don't have any ${filter} reports at this time.`}
                                    </p>
                                    {filter === 'all' && (
                                        <Link
                                            href="/submit-report"
                                            className="inline-flex items-center px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                                        >
                                            Submit Your First Report
                                        </Link>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Help Section */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                        <h3 className="text-lg font-semibold text-blue-900 mb-4">Report Status Guide</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    {getStatusBadge('pending')}
                                    <span className="font-medium text-blue-900">Pending</span>
                                </div>
                                <p className="text-sm text-blue-700">
                                    Your report is being reviewed by our verification team. We check facts, sources, and content quality.
                                </p>
                            </div>
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    {getStatusBadge('verified')}
                                    <span className="font-medium text-blue-900">Verified</span>
                                </div>
                                <p className="text-sm text-blue-700">
                                    Your report has been verified and published. It's now visible to all platform users and researchers.
                                </p>
                            </div>
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    {getStatusBadge('rejected')}
                                    <span className="font-medium text-blue-900">Rejected</span>
                                </div>
                                <p className="text-sm text-blue-700">
                                    Your report needs additional information or verification. Please review feedback and resubmit.
                                </p>
                            </div>
                        </div>
                        
                        <div className="mt-6 pt-4 border-t border-blue-200">
                            <h4 className="font-medium text-blue-900 mb-2">Tips for Better Reports:</h4>
                            <ul className="text-sm text-blue-700 space-y-1">
                                <li>• Include specific dates, times, and locations</li>
                                <li>• Add multiple credible sources and media links</li>
                                <li>• Provide detailed, factual descriptions</li>
                                <li>• Use appropriate categories and priority levels</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default MyReportsPage;