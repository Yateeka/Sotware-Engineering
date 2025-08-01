import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface Protest {
    id: string;
    title: string;
    description: string;
    location: {
        type: string;
        coordinates: [number, number];
    };
    location_description: string;
    city: string;
    state: string;
    country: string;
    categories: string[];
    start_date: string;
    end_date: string;
    status: 'planned' | 'ongoing' | 'completed';
    verification_status: string;
    visibility: string;
    featured: boolean;
    organizers: string[];
    participant_count: number;
    data_quality_score: number;
    trending_score: number;
    engagement_metrics: {
        views: number;
        bookmarks: number;
        follows: number;
        shares: number;
    };
    created_at: string;
    updated_at: string;
    is_bookmarked?: boolean;
    is_following?: boolean;
    related_posts?: any[];
}

interface User {
    user_type: string;
}

const ProtestDetailPage = () => {
    const router = useRouter();
    const { id } = router.query;
    const [protest, setProtest] = useState<Protest | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    useEffect(() => {
        if (id) {
            fetchProtestDetail();
        }
    }, [id]);

    useEffect(() => {
        // Check user authentication
        const userData = localStorage.getItem('user');
        if (userData) {
            setUser(JSON.parse(userData));
        }
    }, []);

    const fetchProtestDetail = async () => {
        try {
            const response = await fetch(`http://localhost:5000/api/protests/${id}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setProtest(data);
            } else {
                // Fallback demo data
                setProtest({
                    id: id as string,
                    title: 'Atlanta Climate Action Rally',
                    description: 'Join hundreds of Atlantans demanding climate action from city council. We\'re calling for renewable energy investments and carbon neutrality by 2030. This rally will feature speakers from environmental organizations, local politicians, and community leaders who are committed to making Atlanta a leader in sustainable urban development.\n\nWe will be advocating for specific policy changes including increased funding for public transportation, incentives for renewable energy adoption, and stricter emissions standards for local businesses. The event will include educational booths, live music, and opportunities to connect with local environmental groups.',
                    location: {
                        type: 'Point',
                        coordinates: [-84.3880, 33.7490]
                    },
                    location_description: 'Atlanta City Hall, 55 Trinity Ave SW, Atlanta, GA 30303',
                    city: 'Atlanta',
                    state: 'Georgia',
                    country: 'United States',
                    categories: ['Environmental', 'Climate Change', 'Local Politics'],
                    start_date: '2024-08-05T14:00:00',
                    end_date: '2024-08-05T18:00:00',
                    status: 'planned',
                    verification_status: 'verified',
                    visibility: 'public',
                    featured: true,
                    organizers: ['Georgia Climate Justice Alliance', 'Atlanta Environmental Coalition', 'Students for Sustainability'],
                    participant_count: 450,
                    data_quality_score: 0.95,
                    trending_score: 0.88,
                    engagement_metrics: {
                        views: 1250,
                        bookmarks: 89,
                        follows: 156,
                        shares: 67
                    },
                    created_at: '2024-07-20T10:30:00',
                    updated_at: '2024-07-30T14:15:00',
                    is_bookmarked: false,
                    is_following: false,
                    related_posts: [
                        {
                            id: '1',
                            user_id: 'user_1',
                            content: 'Excited to see so many Atlantans coming together for climate action! This is what democracy looks like. #ClimateJustice #Atlanta',
                            created_at: '2024-07-29T16:30:00',
                            engagement: { likes: 23, comments: 5, shares: 8 }
                        },
                        {
                            id: '2',
                            user_id: 'user_2',
                            content: 'Just registered for the climate rally! Can\'t wait to make our voices heard. Carpooling available from Decatur - DM me!',
                            created_at: '2024-07-28T11:45:00',
                            engagement: { likes: 12, comments: 3, shares: 2 }
                        }
                    ]
                });
            }
        } catch (error) {
            console.error('Failed to fetch protest details:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleBookmark = async () => {
        if (!user) {
            router.push('/login');
            return;
        }

        setActionLoading('bookmark');
        try {
            const method = protest?.is_bookmarked ? 'DELETE' : 'POST';
            const url = protest?.is_bookmarked 
                ? `http://localhost:5000/api/bookmarks/${id}`
                : 'http://localhost:5000/api/bookmarks';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: method === 'POST' ? JSON.stringify({ protest_id: id }) : undefined,
                credentials: 'include'
            });

            if (response.ok && protest) {
                setProtest({
                    ...protest,
                    is_bookmarked: !protest.is_bookmarked,
                    engagement_metrics: {
                        ...protest.engagement_metrics,
                        bookmarks: protest.engagement_metrics.bookmarks + (protest.is_bookmarked ? -1 : 1)
                    }
                });
            }
        } catch (error) {
            console.error('Bookmark action failed:', error);
        } finally {
            setActionLoading(null);
        }
    };

    const handleFollow = async () => {
        if (!user) {
            router.push('/login');
            return;
        }

        setActionLoading('follow');
        try {
            const method = protest?.is_following ? 'DELETE' : 'POST';
            const url = protest?.is_following 
                ? `http://localhost:5000/api/follows/${id}`
                : 'http://localhost:5000/api/follows';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: method === 'POST' ? JSON.stringify({ protest_id: id }) : undefined,
                credentials: 'include'
            });

            if (response.ok && protest) {
                setProtest({
                    ...protest,
                    is_following: !protest.is_following,
                    engagement_metrics: {
                        ...protest.engagement_metrics,
                        follows: protest.engagement_metrics.follows + (protest.is_following ? -1 : 1)
                    }
                });
            }
        } catch (error) {
            console.error('Follow action failed:', error);
        } finally {
            setActionLoading(null);
        }
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

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatDuration = (startDate: string, endDate: string) => {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffInHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
        return `${diffInHours} hours`;
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!protest) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-900 mb-4">Protest Not Found</h1>
                    <p className="text-gray-600 mb-6">The protest you're looking for doesn't exist or has been removed.</p>
                    <Link href="/search" className="bg-primary text-white px-6 py-3 rounded-lg hover:bg-primary/90">
                        Browse Protests
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>{protest.title} - Global Protest Tracker</title>
                <meta name="description" content={protest.description.substring(0, 160)} />
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header Image/Banner */}
                <div className="bg-gradient-to-r from-primary to-secondary h-64 relative">
                    <div className="absolute inset-0 bg-black/20"></div>
                    <div className="absolute bottom-0 left-0 right-0 p-8">
                        <div className="max-w-7xl mx-auto">
                            <div className="flex items-center gap-4 mb-4">
                                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium text-white ${getStatusColor(protest.status)}`}>
                                    {protest.status.toUpperCase()}
                                </span>
                                {protest.featured && (
                                    <span className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-yellow-400 text-yellow-900">
                                        ⭐ Featured
                                    </span>
                                )}
                                {protest.verification_status === 'verified' && (
                                    <span className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                                        ✓ Verified
                                    </span>
                                )}
                            </div>
                            <h1 className="text-4xl font-bold text-white mb-2">{protest.title}</h1>
                            <p className="text-xl text-white/90">{protest.location_description}</p>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Main Content */}
                        <div className="lg:col-span-2">
                            {/* Navigation */}
                            <div className="mb-6">
                                <Link href="/search" className="text-primary hover:text-primary/80 text-sm">
                                    ← Back to Search
                                </Link>
                            </div>

                            {/* Description */}
                            <div className="bg-white rounded-lg shadow p-6 mb-6">
                                <h2 className="text-xl font-semibold text-gray-900 mb-4">About This Protest</h2>
                                <div className="prose prose-gray max-w-none">
                                    {protest.description.split('\n').map((paragraph, index) => (
                                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                                            {paragraph}
                                        </p>
                                    ))}
                                </div>
                            </div>

                            {/* Organizers */}
                            <div className="bg-white rounded-lg shadow p-6 mb-6">
                                <h2 className="text-xl font-semibold text-gray-900 mb-4">Organizers</h2>
                                <div className="space-y-2">
                                    {protest.organizers.map((organizer, index) => (
                                        <div key={index} className="flex items-center">
                                            <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center mr-3">
                                                <span className="text-primary font-semibold text-sm">
                                                    {organizer.split(' ').map(word => word[0]).join('').substring(0, 2)}
                                                </span>
                                            </div>
                                            <span className="text-gray-900 font-medium">{organizer}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Related Posts */}
                            {protest.related_posts && protest.related_posts.length > 0 && (
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Community Updates</h2>
                                    <div className="space-y-4">
                                        {protest.related_posts.map((post) => (
                                            <div key={post.id} className="border-l-4 border-primary/20 pl-4 py-2">
                                                <p className="text-gray-700 mb-2">{post.content}</p>
                                                <div className="flex items-center justify-between text-sm text-gray-500">
                                                    <span>{new Date(post.created_at).toLocaleDateString()}</span>
                                                    <div className="flex gap-4">
                                                        <span>👍 {post.engagement.likes}</span>
                                                        <span>💬 {post.engagement.comments}</span>
                                                        <span>🔄 {post.engagement.shares}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Sidebar */}
                        <div className="lg:col-span-1">
                            {/* Action Buttons */}
                            <div className="bg-white rounded-lg shadow p-6 mb-6 sticky top-6">
                                <div className="space-y-3">
                                    <button
                                        onClick={handleBookmark}
                                        disabled={actionLoading === 'bookmark'}
                                        className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                                            protest.is_bookmarked
                                                ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        } ${actionLoading === 'bookmark' ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    >
                                        {actionLoading === 'bookmark' ? (
                                            <span className="flex items-center justify-center">
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                                                Processing...
                                            </span>
                                        ) : (
                                            <>🔖 {protest.is_bookmarked ? 'Bookmarked' : 'Bookmark'}</>
                                        )}
                                    </button>

                                    <button
                                        onClick={handleFollow}
                                        disabled={actionLoading === 'follow'}
                                        className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                                            protest.is_following
                                                ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        } ${actionLoading === 'follow' ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    >
                                        {actionLoading === 'follow' ? (
                                            <span className="flex items-center justify-center">
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                                                Processing...
                                            </span>
                                        ) : (
                                            <>👁️ {protest.is_following ? 'Following' : 'Follow Updates'}</>
                                        )}
                                    </button>

                                    <button className="w-full py-3 px-4 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors">
                                        📤 Share Event
                                    </button>

                                    {user?.user_type === 'activist' || user?.user_type === 'ngo_worker' ? (
                                        <Link
                                            href="/submit-report"
                                            className="w-full py-3 px-4 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition-colors text-center block"
                                        >
                                            📝 Submit Report
                                        </Link>
                                    ) : null}
                                </div>
                            </div>

                            {/* Event Details */}
                            <div className="bg-white rounded-lg shadow p-6 mb-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Details</h3>
                                <div className="space-y-4">
                                    <div>
                                        <div className="text-sm font-medium text-gray-500 mb-1">📅 Start Date</div>
                                        <div className="text-gray-900">{formatDate(protest.start_date)}</div>
                                    </div>
                                    
                                    <div>
                                        <div className="text-sm font-medium text-gray-500 mb-1">⏰ Duration</div>
                                        <div className="text-gray-900">{formatDuration(protest.start_date, protest.end_date)}</div>
                                    </div>

                                    <div>
                                        <div className="text-sm font-medium text-gray-500 mb-1">📍 Location</div>
                                        <div className="text-gray-900">{protest.location_description}</div>
                                        <div className="text-sm text-gray-500 mt-1">
                                            {protest.location.coordinates[1].toFixed(4)}, {protest.location.coordinates[0].toFixed(4)}
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-sm font-medium text-gray-500 mb-1">👥 Expected Participants</div>
                                        <div className="text-gray-900 font-semibold">{protest.participant_count.toLocaleString()}</div>
                                    </div>

                                    <div>
                                        <div className="text-sm font-medium text-gray-500 mb-1">🏷️ Categories</div>
                                        <div className="flex flex-wrap gap-2">
                                            {protest.categories.map((category) => (
                                                <span key={category} className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-sm font-medium">
                                                    {category}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Engagement Stats */}
                            <div className="bg-white rounded-lg shadow p-6 mb-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-blue-600">{protest.engagement_metrics.views}</div>
                                        <div className="text-sm text-gray-600">Views</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-yellow-600">{protest.engagement_metrics.bookmarks}</div>
                                        <div className="text-sm text-gray-600">Bookmarks</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-green-600">{protest.engagement_metrics.follows}</div>
                                        <div className="text-sm text-gray-600">Followers</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-purple-600">{protest.engagement_metrics.shares}</div>
                                        <div className="text-sm text-gray-600">Shares</div>
                                    </div>
                                </div>
                            </div>

                            {/* Quality Indicators */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Quality</h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">Data Quality</span>
                                        <div className="flex items-center">
                                            <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                                                <div 
                                                    className="bg-green-500 h-2 rounded-full" 
                                                    style={{ width: `${protest.data_quality_score * 100}%` }}
                                                ></div>
                                            </div>
                                            <span className="text-sm font-medium">{Math.round(protest.data_quality_score * 100)}%</span>
                                        </div>
                                    </div>

                                    <div className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">Trending Score</span>
                                        <div className="flex items-center">
                                            <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                                                <div 
                                                    className="bg-blue-500 h-2 rounded-full" 
                                                    style={{ width: `${protest.trending_score * 100}%` }}
                                                ></div>
                                            </div>
                                            <span className="text-sm font-medium">{Math.round(protest.trending_score * 100)}%</span>
                                        </div>
                                    </div>

                                    <div className="pt-3 border-t border-gray-200">
                                        <div className="text-xs text-gray-500">
                                            <div>Created: {new Date(protest.created_at).toLocaleDateString()}</div>
                                            <div>Updated: {new Date(protest.updated_at).toLocaleDateString()}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default ProtestDetailPage;