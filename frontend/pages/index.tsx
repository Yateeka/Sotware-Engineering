import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';

// Mock data types
interface Protest {
    id: string;
    title: string;
    location_description: string;
    categories: string[];
    participant_count: number;
    status: 'planned' | 'ongoing' | 'completed';
    start_date: string;
    coordinates: [number, number];
}

interface GlobalStats {
    total_protests: number;
    active_protests: number;
    countries_covered: number;
    total_participants?: number;
}

const LandingPage = () => {
    const [featuredProtests, setFeaturedProtests] = useState<Protest[]>([]);
    const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [showSearchPrompt, setShowSearchPrompt] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Fetch featured protests and global stats
        const fetchData = async () => {
            try {
                const [protestsRes, statsRes] = await Promise.all([
                    fetch('http://localhost:5000/api/protests/featured'),
                    fetch('http://localhost:5000/api/public/statistics')
                ]);

                const protestsData = await protestsRes.json();
                const statsData = await statsRes.json();

                setFeaturedProtests(protestsData.protests || []);
                setGlobalStats(statsData);
            } catch (error) {
                console.error('Failed to fetch data:', error);
                // Set fallback data for demo
                setFeaturedProtests([
                    {
                        id: '1',
                        title: 'Atlanta Climate Action Rally',
                        location_description: 'Atlanta City Hall, Atlanta, GA',
                        categories: ['Environmental', 'Climate Change'],
                        participant_count: 450,
                        status: 'planned',
                        start_date: '2024-08-05T14:00:00',
                        coordinates: [-84.3880, 33.7490]
                    },
                    {
                        id: '2',
                        title: 'March for Public Education Funding',
                        location_description: 'Georgia State Capitol, Atlanta, GA',
                        categories: ['Education', 'Labor Rights'],
                        participant_count: 750,
                        status: 'planned',
                        start_date: '2024-08-17T10:00:00',
                        coordinates: [-84.3963, 33.7490]
                    }
                ]);
                setGlobalStats({
                    total_protests: 60,
                    active_protests: 15,
                    countries_covered: 12,
                    total_participants: 45000
                });
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleSearchAttempt = () => {
        setShowSearchPrompt(true);
        setTimeout(() => setShowSearchPrompt(false), 3000);
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ongoing':
                return 'bg-green-500';
            case 'planned':
                return 'bg-blue-500';
            case 'completed':
                return 'bg-gray-500';
            default:
                return 'bg-gray-500';
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>Global Protest Tracker - Monitoring Social Movements Worldwide</title>
                <meta name="description" content="Track protests, social movements, and civic actions happening around the world. Stay informed about demonstrations for human rights, climate action, and social justice." />
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Hero Section */}
                <section className="bg-gradient-to-r from-primary to-secondary text-white py-20">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center">
                            <h1 className="text-4xl md:text-6xl font-bold mb-6">
                                Global Protest Tracker
                            </h1>
                            <p className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto opacity-90">
                                Monitoring social movements and civic actions worldwide. 
                                Stay informed about demonstrations for human rights, climate action, and social justice.
                            </p>

                            {/* Search Bar (Demo - Shows Auth Required) */}
                            <div className="max-w-2xl mx-auto mb-8">
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder="Search protests by location, issue, or organization..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        onClick={handleSearchAttempt}
                                        className="w-full px-6 py-4 text-lg rounded-full text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-4 focus:ring-white/30"
                                    />
                                    <button 
                                        onClick={handleSearchAttempt}
                                        className="absolute right-2 top-2 bg-primary text-white px-6 py-2 rounded-full hover:bg-primary/90 transition-colors"
                                    >
                                        Search
                                    </button>
                                </div>

                                {/* Search Auth Prompt */}
                                {showSearchPrompt && (
                                    <div className="mt-4 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg p-4">
                                        <p className="text-white/90 mb-3">
                                            🔒 Please log in to access search functionality
                                        </p>
                                        <div className="flex gap-3 justify-center">
                                            <Link 
                                                href="/login"
                                                className="bg-white text-primary px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
                                            >
                                                Login
                                            </Link>
                                            <Link 
                                                href="/register"
                                                className="bg-transparent border border-white text-white px-4 py-2 rounded-lg font-medium hover:bg-white/10 transition-colors"
                                            >
                                                Register
                                            </Link>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Call to Action */}
                            <div className="flex flex-col sm:flex-row gap-4 justify-center">
                                <Link 
                                    href="/register"
                                    className="bg-white text-primary px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
                                >
                                    Join the Movement
                                </Link>
                                <Link 
                                    href="/map"
                                    className="bg-transparent border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors"
                                >
                                    View Global Map
                                </Link>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Global Statistics */}
                {globalStats && (
                    <section className="bg-white py-16">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                            <div className="text-center mb-12">
                                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                                    Global Impact
                                </h2>
                                <p className="text-lg text-gray-600">
                                    Real-time data on social movements worldwide
                                </p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-primary mb-2">
                                        {globalStats.total_protests.toLocaleString()}
                                    </div>
                                    <div className="text-gray-600">Total Protests Tracked</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-green-600 mb-2">
                                        {globalStats.active_protests}
                                    </div>
                                    <div className="text-gray-600">Currently Active</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-blue-600 mb-2">
                                        {globalStats.countries_covered}
                                    </div>
                                    <div className="text-gray-600">Countries Covered</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-purple-600 mb-2">
                                        {globalStats.total_participants?.toLocaleString() || '45K+'}
                                    </div>
                                    <div className="text-gray-600">Total Participants</div>
                                </div>
                            </div>
                        </div>
                    </section>
                )}

                {/* Featured Protests */}
                <section className="bg-gray-50 py-16">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-bold text-gray-900 mb-4">
                                Featured Protests
                            </h2>
                            <p className="text-lg text-gray-600">
                                Major demonstrations and movements happening now
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {featuredProtests.slice(0, 6).map((protest) => (
                                <div key={protest.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                                    <div className="p-6">
                                        <div className="flex items-center justify-between mb-3">
                                            <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(protest.status)}`}>
                                                {protest.status.toUpperCase()}
                                            </span>
                                            <span className="text-sm text-gray-500">
                                                {formatDate(protest.start_date)}
                                            </span>
                                        </div>

                                        <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                            {protest.title}
                                        </h3>
                                        
                                        <p className="text-gray-600 mb-3">
                                            📍 {protest.location_description}
                                        </p>

                                        <div className="flex flex-wrap gap-2 mb-4">
                                            {protest.categories.map((category) => (
                                                <span key={category} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
                                                    {category}
                                                </span>
                                            ))}
                                        </div>

                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-gray-500">
                                                👥 {protest.participant_count.toLocaleString()} participants
                                            </span>
                                            <Link 
                                                href={`/protest/${protest.id}`}
                                                className="text-primary hover:text-primary/80 font-medium"
                                            >
                                                Learn More →
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="text-center mt-12">
                            <Link 
                                href="/map"
                                className="inline-block bg-primary text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary/90 transition-colors"
                            >
                                View All Protests on Map
                            </Link>
                        </div>
                    </div>
                </section>

                {/* Call to Action Section */}
                <section className="bg-primary text-white py-16">
                    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                        <h2 className="text-3xl font-bold mb-6">
                            Ready to Get Involved?
                        </h2>
                        <p className="text-xl mb-8 opacity-90">
                            Join thousands of citizens, activists, journalists, and researchers using our platform 
                            to stay informed and take action on issues that matter.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                            <div className="text-center">
                                <div className="text-4xl mb-4">👥</div>
                                <h3 className="text-xl font-semibold mb-2">Citizens</h3>
                                <p className="opacity-90">Stay informed about local and global movements</p>
                            </div>
                            <div className="text-center">
                                <div className="text-4xl mb-4">✊</div>
                                <h3 className="text-xl font-semibold mb-2">Activists</h3>
                                <p className="opacity-90">Organize, report, and amplify your cause</p>
                            </div>
                            <div className="text-center">
                                <div className="text-4xl mb-4">📊</div>
                                <h3 className="text-xl font-semibold mb-2">Researchers</h3>
                                <p className="opacity-90">Access data and analytics on social movements</p>
                            </div>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Link 
                                href="/register"
                                className="bg-white text-primary px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
                            >
                                Create Account
                            </Link>
                            <Link 
                                href="/login"
                                className="bg-transparent border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors"
                            >
                                Sign In
                            </Link>
                        </div>
                    </div>
                </section>

                {/* Quick Features Section */}
                <section className="bg-white py-16">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-bold text-gray-900 mb-4">
                                Why Use Global Protest Tracker?
                            </h2>
                            <p className="text-lg text-gray-600">
                                Comprehensive tools for understanding and participating in social movements
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                            <div className="text-center">
                                <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Real-Time Tracking</h3>
                                <p className="text-gray-600">Live updates on protests and demonstrations worldwide</p>
                            </div>

                            <div className="text-center">
                                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Global Coverage</h3>
                                <p className="text-gray-600">Comprehensive data from cities and countries worldwide</p>
                            </div>

                            <div className="text-center">
                                <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Verified Information</h3>
                                <p className="text-gray-600">Fact-checked reports from trusted sources and eyewitnesses</p>
                            </div>

                            <div className="text-center">
                                <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Instant Alerts</h3>
                                <p className="text-gray-600">Get notified about protests and movements you care about</p>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </>
    );
};

export default LandingPage;