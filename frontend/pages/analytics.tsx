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

interface AnalyticsData {
    global_statistics: {
        total_protests: number;
        active_protests: number;
        completed_protests: number;
        countries_covered: number;
        total_participants: number;
        verified_reports: number;
    };
    geographic_distribution: Array<{
        country: string;
        protest_count: number;
        participant_count: number;
    }>;
    category_trends: Array<{
        category: string;
        count: number;
        growth_rate: string;
    }>;
    temporal_analysis: {
        protests_by_month: Record<string, number>;
        growth_rate: string;
    };
    engagement_metrics: {
        total_users: number;
        active_users: number;
        reports_submitted: number;
        data_exports: number;
    };
    verification_rates: {
        verified: number;
        pending: number;
        rejected: number;
    };
}

const AnalyticsPage = () => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedTimeframe, setSelectedTimeframe] = useState('3months');
    const [selectedRegion, setSelectedRegion] = useState('global');

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const userData = localStorage.getItem('user');
                if (!userData) {
                    router.push('/login');
                    return;
                }

                const parsedUser = JSON.parse(userData);
                
                // Check if user has permission to view analytics
                if (!['researcher', 'journalist', 'admin'].includes(parsedUser.user_type)) {
                    router.push('/dashboard');
                    return;
                }

                setUser(parsedUser);
                await fetchAnalytics();
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const fetchAnalytics = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/analytics/trends', {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setAnalyticsData(data);
            } else {
                console.error('Failed to fetch analytics');
            }
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    };

    const formatNumber = (num: number | undefined | null) => {
        // Handle undefined, null, or invalid numbers
        if (num == null || isNaN(num)) {
            return '0';
        }
        
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    };

    const renderChart = (data: Record<string, number> | undefined, title: string, color: string) => {
        // Handle undefined or empty data
        if (!data || Object.keys(data).length === 0) {
            return (
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
                    <div className="text-center py-8 text-gray-500">
                        <div className="text-4xl mb-2">📊</div>
                        <div>No data available</div>
                    </div>
                </div>
            );
        }

        const maxValue = Math.max(...Object.values(data));
        
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
                <div className="space-y-3">
                    {Object.entries(data).map(([key, value]) => (
                        <div key={key}>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">{key}</span>
                                <span className="font-medium text-gray-900">{value || 0}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full ${color}`}
                                    style={{ width: `${maxValue > 0 ? ((value || 0) / maxValue) * 100 : 0}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!user || !analyticsData) {
        return null;
    }

    return (
        <>
            <Head>
                <title>Analytics - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
                                <p className="text-gray-600">Comprehensive insights into global protest movements</p>
                            </div>
                            <div className="flex gap-3">
                                <Link 
                                    href="/export"
                                    className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                                >
                                    📊 Export Data
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
                    {/* Filters */}
                    <div className="bg-white rounded-lg shadow p-6 mb-8">
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                            <div className="flex items-center gap-4">
                                <label className="text-sm font-medium text-gray-700">Timeframe:</label>
                                <select
                                    value={selectedTimeframe}
                                    onChange={(e) => setSelectedTimeframe(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                >
                                    <option value="1month">Last Month</option>
                                    <option value="3months">Last 3 Months</option>
                                    <option value="6months">Last 6 Months</option>
                                    <option value="1year">Last Year</option>
                                    <option value="all">All Time</option>
                                </select>
                            </div>
                            
                            <div className="flex items-center gap-4">
                                <label className="text-sm font-medium text-gray-700">Region:</label>
                                <select
                                    value={selectedRegion}
                                    onChange={(e) => setSelectedRegion(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                >
                                    <option value="global">Global</option>
                                    <option value="north_america">North America</option>
                                    <option value="europe">Europe</option>
                                    <option value="asia">Asia</option>
                                    <option value="africa">Africa</option>
                                    <option value="south_america">South America</option>
                                    <option value="oceania">Oceania</option>
                                </select>
                            </div>

                            <div className="text-sm text-gray-500">
                                Last updated: {new Date().toLocaleString()}
                            </div>
                        </div>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-3xl font-bold text-primary mb-2">
                                {formatNumber(analyticsData?.global_statistics?.total_protests)}
                            </div>
                            <div className="text-sm text-gray-600">Total Protests</div>
                            <div className="text-xs text-green-600 mt-1">+{analyticsData?.temporal_analysis?.growth_rate || '0%'}</div>
                        </div>
                        
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-3xl font-bold text-green-600 mb-2">
                                {formatNumber(analyticsData?.global_statistics?.active_protests)}
                            </div>
                            <div className="text-sm text-gray-600">Active Protests</div>
                            <div className="text-xs text-gray-500 mt-1">Currently ongoing</div>
                        </div>
                        
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-3xl font-bold text-blue-600 mb-2">
                                {formatNumber(analyticsData?.global_statistics?.total_participants)}
                            </div>
                            <div className="text-sm text-gray-600">Total Participants</div>
                            <div className="text-xs text-gray-500 mt-1">Estimated across all protests</div>
                        </div>
                        
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <div className="text-3xl font-bold text-purple-600 mb-2">
                                {formatNumber(analyticsData?.global_statistics?.countries_covered)}
                            </div>
                            <div className="text-sm text-gray-600">Countries</div>
                            <div className="text-xs text-gray-500 mt-1">Global coverage</div>
                        </div>
                    </div>

                    {/* Charts Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                        {/* Monthly Trends */}
                        {renderChart(
                            analyticsData?.temporal_analysis?.protests_by_month,
                            'Protests by Month',
                            'bg-primary'
                        )}

                        {/* Category Distribution */}
                        {renderChart(
                            analyticsData?.category_trends?.reduce((acc, item) => {
                                acc[item.category] = item.count;
                                return acc;
                            }, {} as Record<string, number>),
                            'Protests by Category',
                            'bg-blue-500'
                        )}

                        {/* Geographic Distribution */}
                        {renderChart(
                            analyticsData?.geographic_distribution?.slice(0, 8).reduce((acc, item) => {
                                acc[item.country] = item.protest_count;
                                return acc;
                            }, {} as Record<string, number>),
                            'Top Countries by Protest Count',
                            'bg-green-500'
                        )}

                        {/* Verification Status */}
                        {renderChart(
                            analyticsData?.verification_rates,
                            'Report Verification Status',
                            'bg-yellow-500'
                        )}
                    </div>

                    {/* Detailed Tables */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                        {/* Category Trends Table */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="p-6 border-b border-gray-200">
                                <h3 className="text-lg font-semibold text-gray-900">Category Trends</h3>
                                <p className="text-sm text-gray-600">Growth rates compared to previous period</p>
                            </div>
                            <div className="p-6">
                                <div className="space-y-4">
                                    {analyticsData?.category_trends?.map((category, index) => (
                                        <div key={category.category} className="flex items-center justify-between">
                                            <div className="flex items-center">
                                                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center mr-3">
                                                    <span className="text-xs font-bold text-primary">#{index + 1}</span>
                                                </div>
                                                <div>
                                                    <div className="font-medium text-gray-900">{category.category}</div>
                                                    <div className="text-sm text-gray-500">{category.count} protests</div>
                                                </div>
                                            </div>
                                            <div className={`text-sm font-medium ${
                                                category.growth_rate.includes('+') ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                                {category.growth_rate}
                                            </div>
                                        </div>
                                    )) || (
                                        <div className="text-center py-8 text-gray-500">
                                            <div>No category data available</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Geographic Analysis */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="p-6 border-b border-gray-200">
                                <h3 className="text-lg font-semibold text-gray-900">Geographic Analysis</h3>
                                <p className="text-sm text-gray-600">Protest activity by country</p>
                            </div>
                            <div className="p-6">
                                <div className="space-y-4">
                                    {analyticsData?.geographic_distribution?.slice(0, 8).map((country, index) => (
                                        <div key={country.country} className="flex items-center justify-between">
                                            <div className="flex items-center">
                                                <div className="w-8 h-8 bg-blue-500/10 rounded-full flex items-center justify-center mr-3">
                                                    <span className="text-xs font-bold text-blue-600">#{index + 1}</span>
                                                </div>
                                                <div>
                                                    <div className="font-medium text-gray-900">{country.country}</div>
                                                    <div className="text-sm text-gray-500">
                                                        {formatNumber(country.participant_count)} participants
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-sm font-medium text-gray-900">
                                                {country.protest_count} protests
                                            </div>
                                        </div>
                                    )) || (
                                        <div className="text-center py-8 text-gray-500">
                                            <div>No geographic data available</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Platform Engagement */}
                    <div className="bg-white rounded-lg shadow mb-8">
                        <div className="p-6 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">Platform Engagement</h3>
                            <p className="text-sm text-gray-600">User activity and content creation metrics</p>
                        </div>
                        <div className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-gray-900 mb-1">
                                        {formatNumber(analyticsData?.engagement_metrics?.total_users)}
                                    </div>
                                    <div className="text-sm text-gray-600">Total Users</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600 mb-1">
                                        {formatNumber(analyticsData?.engagement_metrics?.active_users)}
                                    </div>
                                    <div className="text-sm text-gray-600">Active Users</div>
                                    <div className="text-xs text-gray-500">Last 30 days</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-blue-600 mb-1">
                                        {formatNumber(analyticsData?.engagement_metrics?.reports_submitted)}
                                    </div>
                                    <div className="text-sm text-gray-600">Reports Submitted</div>
                                    <div className="text-xs text-gray-500">User-generated content</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-purple-600 mb-1">
                                        {formatNumber(analyticsData?.engagement_metrics?.data_exports)}
                                    </div>
                                    <div className="text-sm text-gray-600">Data Exports</div>
                                    <div className="text-xs text-gray-500">Research downloads</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Data Quality Metrics */}
                    <div className="bg-white rounded-lg shadow mb-8">
                        <div className="p-6 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">Data Quality & Verification</h3>
                            <p className="text-sm text-gray-600">Content verification and quality assurance metrics</p>
                        </div>
                        <div className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="text-center p-4 bg-green-50 rounded-lg">
                                    <div className="text-2xl font-bold text-green-600 mb-2">
                                        {(() => {
                                            const verified = analyticsData?.verification_rates?.verified || 0;
                                            const pending = analyticsData?.verification_rates?.pending || 0;
                                            const rejected = analyticsData?.verification_rates?.rejected || 0;
                                            const total = verified + pending + rejected;
                                            return total > 0 ? ((verified / total) * 100).toFixed(1) : '0';
                                        })()}%
                                    </div>
                                    <div className="text-sm font-medium text-green-800">Verification Rate</div>
                                    <div className="text-xs text-green-600 mt-1">
                                        {analyticsData?.verification_rates?.verified || 0} verified reports
                                    </div>
                                </div>
                                
                                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                                    <div className="text-2xl font-bold text-yellow-600 mb-2">
                                        {analyticsData?.verification_rates?.pending || 0}
                                    </div>
                                    <div className="text-sm font-medium text-yellow-800">Pending Review</div>
                                    <div className="text-xs text-yellow-600 mt-1">Awaiting verification</div>
                                </div>
                                
                                <div className="text-center p-4 bg-red-50 rounded-lg">
                                    <div className="text-2xl font-bold text-red-600 mb-2">
                                        {(() => {
                                            const verified = analyticsData?.verification_rates?.verified || 0;
                                            const pending = analyticsData?.verification_rates?.pending || 0;
                                            const rejected = analyticsData?.verification_rates?.rejected || 0;
                                            const total = verified + pending + rejected;
                                            return total > 0 ? ((rejected / total) * 100).toFixed(1) : '0';
                                        })()}%
                                    </div>
                                    <div className="text-sm font-medium text-red-800">Rejection Rate</div>
                                    <div className="text-xs text-red-600 mt-1">Quality control measure</div>
                                </div>
                            </div>

                            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                                <h4 className="font-medium text-blue-900 mb-2">Quality Insights</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-700">
                                    <div>
                                        <span className="font-medium">Average Response Time:</span> 2.3 hours
                                    </div>
                                    <div>
                                        <span className="font-medium">Source Verification:</span> 94.2% accuracy
                                    </div>
                                    <div>
                                        <span className="font-medium">Duplicate Detection:</span> 12 duplicates removed
                                    </div>
                                    <div>
                                        <span className="font-medium">Community Reports:</span> 3 flagged items reviewed
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Research Insights */}
                    {user.user_type === 'researcher' && (
                        <div className="bg-gradient-to-r from-primary to-secondary text-white rounded-lg p-6 mb-8">
                            <h3 className="text-lg font-semibold mb-4">🔬 Research Insights</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h4 className="font-medium mb-2">Emerging Trends</h4>
                                    <ul className="space-y-1 text-sm opacity-90">
                                        <li>• Climate protests increased 23% this quarter</li>
                                        <li>• Youth participation up 34% globally</li>
                                        <li>• Digital-first organizing strategies emerging</li>
                                        <li>• Cross-border solidarity movements growing</li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="font-medium mb-2">Research Opportunities</h4>
                                    <ul className="space-y-1 text-sm opacity-90">
                                        <li>• Comparative analysis across 15+ countries available</li>
                                        <li>• 6 months of high-quality temporal data</li>
                                        <li>• Social media correlation datasets ready</li>
                                        <li>• Policy impact assessment data available</li>
                                    </ul>
                                </div>
                            </div>
                            <div className="mt-4">
                                <Link
                                    href="/export"
                                    className="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors"
                                >
                                    🔗 Access Research Datasets
                                </Link>
                            </div>
                        </div>
                    )}

                    {/* Journalist Tools */}
                    {user.user_type === 'journalist' && (
                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6 mb-8">
                            <h3 className="text-lg font-semibold mb-4">📰 Journalist Toolkit</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
                                    <h4 className="font-medium mb-2">Breaking News</h4>
                                    <div className="text-sm opacity-90">
                                        <div>🔴 3 active protests</div>
                                        <div>📈 High engagement: Climate rally</div>
                                        <div>🌍 Global: Education strikes</div>
                                    </div>
                                </div>
                                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
                                    <h4 className="font-medium mb-2">Story Ideas</h4>
                                    <div className="text-sm opacity-90">
                                        <div>• Youth climate movement analysis</div>
                                        <div>• Regional protest effectiveness</div>
                                        <div>• Social media impact study</div>
                                    </div>
                                </div>
                                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
                                    <h4 className="font-medium mb-2">Press Resources</h4>
                                    <div className="text-sm opacity-90">
                                        <div>📊 Verified statistics ready</div>
                                        <div>📷 Media gallery access</div>
                                        <div>🎤 Interview connections</div>
                                    </div>
                                </div>
                            </div>
                            <div className="mt-4 flex gap-3">
                                <Link
                                    href="/export"
                                    className="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors"
                                >
                                    📋 Export Story Data
                                </Link>
                                <button className="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors">
                                    📧 Set News Alerts
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Footer Actions */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">Need More Data?</h3>
                                <p className="text-gray-600">Access raw datasets, custom reports, and advanced analytics tools</p>
                            </div>
                            <div className="flex gap-3">
                                <Link
                                    href="/export"
                                    className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                                >
                                    Export Datasets
                                </Link>
                                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                                    Request Custom Analysis
                                </button>
                                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                                    📧 Subscribe to Reports
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default AnalyticsPage;