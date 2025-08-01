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
        location: string;
    };
    verified: boolean;
}

interface DashboardData {
    user_profile: {
        name: string;
        location: string;
        user_type: string;
        verified: boolean;
    };
    [key: string]: any;
}

const Dashboard = () => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                // Check if user is logged in
                const userData = localStorage.getItem('user');
                if (!userData) {
                    router.push('/login');
                    return;
                }

                const user = JSON.parse(userData);
                setUser(user);

                // Fetch dashboard data
                const response = await fetch(`http://localhost:5000/api/dashboard/${user.user_type}`, {
                    credentials: 'include'
                });

                if (response.ok) {
                    const data = await response.json();
                    setDashboardData(data);
                } else {
                    console.error('Failed to fetch dashboard data');
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const formatUserType = (userType: string) => {
        return userType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    const renderCitizenDashboard = () => (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Welcome Card */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    Welcome back, {dashboardData?.user_profile.name}!
                </h2>
                <p className="text-gray-600 mb-4">
                    Stay updated on protests and movements in {dashboardData?.user_profile.location} and beyond.
                </p>
                <div className="flex gap-4">
                    <Link href="/map" className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90">
                        Explore Map
                    </Link>
                    <Link href="/search" className="border border-primary text-primary px-4 py-2 rounded-lg hover:bg-primary/10">
                        Search Protests
                    </Link>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Activity</h3>
                <div className="space-y-3">
                    <div className="flex justify-between">
                        <span className="text-gray-600">Bookmarks</span>
                        <span className="font-semibold">{dashboardData?.bookmarked_protests || 0}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-600">Following</span>
                        <span className="font-semibold">{dashboardData?.followed_protests || 0}</span>
                    </div>
                    <Link href="/bookmarks" className="block text-primary hover:text-primary/80 text-sm">
                        View all bookmarks →
                    </Link>
                </div>
            </div>

            {/* Nearby Protests */}
            <div className="lg:col-span-3 bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Protests Near You</h3>
                {dashboardData?.nearby_protests?.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {dashboardData?.nearby_protests?.slice(0, 3).map((protest: any) => (
                            <div key={protest.id} className="border border-gray-200 rounded-lg p-4 hover:border-primary cursor-pointer">
                                <h4 className="font-medium text-gray-900 mb-2">{protest.title}</h4>
                                <p className="text-sm text-gray-600 mb-2">📍 {protest.location_description}</p>
                                <div className="flex gap-2 mb-2">
                                    {protest.categories.slice(0, 2).map((cat: string) => (
                                        <span key={cat} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                                            {cat}
                                        </span>
                                    ))}
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-gray-500">{protest.status}</span>
                                    <Link href={`/protest/${protest.id}`} className="text-primary text-sm hover:text-primary/80">
                                        View Details
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-500">No nearby protests found. <Link href="/map" className="text-primary">Explore the map</Link> to discover movements.</p>
                )}
            </div>
        </div>
    );

    const renderActivistDashboard = () => (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Action Items */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Action Items</h2>
                {dashboardData?.action_items?.length > 0 ? (
                    <div className="space-y-3">
                        {dashboardData?.action_items?.map((item: string, index: number) => (
                            <div key={index} className="flex items-center p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <div className="w-2 h-2 bg-yellow-500 rounded-full mr-3"></div>
                                <span className="text-gray-800">{item}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-500">No pending action items.</p>
                )}
                <div className="mt-4 flex gap-3">
                    <Link href="/submit-report" className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90">
                        Submit Report
                    </Link>
                    <Link href="/my-reports" className="border border-primary text-primary px-4 py-2 rounded-lg hover:bg-primary/10">
                        View Reports
                    </Link>
                </div>
            </div>

            {/* Activist Stats */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Impact</h3>
                <div className="space-y-4">
                    <div className="text-center">
                        <div className="text-2xl font-bold text-primary">{dashboardData?.organized_protests || 0}</div>
                        <div className="text-sm text-gray-600">Protests Organized</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{dashboardData?.reports_submitted || 0}</div>
                        <div className="text-sm text-gray-600">Reports Submitted</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{dashboardData?.network_size || 0}</div>
                        <div className="text-sm text-gray-600">Network Connections</div>
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="lg:col-span-3 bg-gradient-to-r from-primary to-secondary text-white rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Link href="/submit-report" className="bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition-colors">
                        <div className="text-2xl mb-2">📝</div>
                        <div className="font-medium">Submit Report</div>
                        <div className="text-sm opacity-90">Document new protest</div>
                    </Link>
                    <Link href="/map" className="bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition-colors">
                        <div className="text-2xl mb-2">🗺️</div>
                        <div className="font-medium">View Map</div>
                        <div className="text-sm opacity-90">Explore global movements</div>
                    </Link>
                    <Link href="/search" className="bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition-colors">
                        <div className="text-2xl mb-2">🔍</div>
                        <div className="font-medium">Search</div>
                        <div className="text-sm opacity-90">Find specific protests</div>
                    </Link>
                    <Link href="/bookmarks" className="bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition-colors">
                        <div className="text-2xl mb-2">🔖</div>
                        <div className="font-medium">Bookmarks</div>
                        <div className="text-sm opacity-90">Your saved protests</div>
                    </Link>
                </div>
            </div>
        </div>
    );

    const renderResearcherDashboard = () => (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Research Overview */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Research Dashboard</h2>
                <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">{dashboardData?.recent_exports || 0}</div>
                        <div className="text-sm text-gray-600">Data Exports</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">{dashboardData?.data_quality_score || 94.2}%</div>
                        <div className="text-sm text-gray-600">Data Quality</div>
                    </div>
                </div>
                <div className="flex gap-3">
                    <Link href="/analytics" className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90">
                        View Analytics
                    </Link>
                    <Link href="/export" className="border border-primary text-primary px-4 py-2 rounded-lg hover:bg-primary/10">
                        Export Data
                    </Link>
                </div>
            </div>

            {/* Research Alerts */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Research Alerts</h3>
                <div className="space-y-3">
                    <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                        <div className="font-medium text-orange-800">New Dataset Available</div>
                        <div className="text-sm text-orange-600">Q2 2024 protest data ready</div>
                    </div>
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="font-medium text-blue-800">Trending Topic</div>
                        <div className="text-sm text-blue-600">Climate protests up 23%</div>
                    </div>
                </div>
            </div>

            {/* Trending Stories */}
            <div className="lg:col-span-3 bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trending Research Topics</h3>
                {dashboardData?.trending_stories?.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {dashboardData?.trending_stories?.map((story: string, index: number) => (
                            <div key={index} className="p-4 border border-gray-200 rounded-lg hover:border-primary cursor-pointer">
                                <h4 className="font-medium text-gray-900 mb-2">{story}</h4>
                                <div className="text-sm text-gray-500">Click to explore data</div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-500">No trending topics available.</p>
                )}
            </div>
        </div>
    );

    const renderAdminDashboard = () => (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* System Status */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
                <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                        <div className="text-lg font-bold text-green-600">{dashboardData?.system_health || 'Operational'}</div>
                        <div className="text-sm text-gray-600">System Health</div>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                        <div className="text-lg font-bold text-blue-600">{dashboardData?.active_users_today || 156}</div>
                        <div className="text-sm text-gray-600">Active Users</div>
                    </div>
                    <div className="text-center p-3 bg-yellow-50 rounded-lg">
                        <div className="text-lg font-bold text-yellow-600">{dashboardData?.pending_moderation || 5}</div>
                        <div className="text-sm text-gray-600">Pending Moderation</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                        <div className="text-lg font-bold text-purple-600">{dashboardData?.verification_queue || 12}</div>
                        <div className="text-sm text-gray-600">Verification Queue</div>
                    </div>
                </div>
            </div>

            {/* Quick Admin Actions */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Admin Actions</h3>
                <div className="space-y-3">
                    <Link href="/admin" className="block w-full bg-primary text-white text-center py-2 rounded-lg hover:bg-primary/90">
                        Admin Panel
                    </Link>
                    <Link href="/analytics" className="block w-full border border-primary text-primary text-center py-2 rounded-lg hover:bg-primary/10">
                        System Analytics
                    </Link>
                    <Link href="/admin/moderation" className="block w-full border border-gray-300 text-gray-700 text-center py-2 rounded-lg hover:bg-gray-50">
                        Moderation Queue
                    </Link>
                </div>
            </div>
        </div>
    );

    const renderDashboardContent = () => {
        if (!dashboardData || !user) return null;

        switch (user.user_type) {
            case 'citizen':
                return renderCitizenDashboard();
            case 'activist':
            case 'ngo_worker':
                return renderActivistDashboard();
            case 'journalist':
            case 'researcher':
                return renderResearcherDashboard();
            case 'admin':
            case 'moderator':
                return renderAdminDashboard();
            default:
                return renderCitizenDashboard();
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!user) {
        return null; // Will redirect to login
    }

    return (
        <>
            <Head>
                <title>Dashboard - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">
                                    {formatUserType(user.user_type)} Dashboard
                                </h1>
                                <p className="text-gray-600">
                                    Welcome back, {user.profile.first_name}! 
                                    {user.verified && (
                                        <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                            ✓ Verified
                                        </span>
                                    )}
                                </p>
                            </div>
                            <div className="text-right">
                                <div className="text-sm text-gray-500">📍 {user.profile.location}</div>
                                <div className="text-xs text-gray-400">Last login: {new Date().toLocaleDateString()}</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Dashboard Content */}
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {renderDashboardContent()}
                </div>
            </div>
        </>
    );
};

export default Dashboard;