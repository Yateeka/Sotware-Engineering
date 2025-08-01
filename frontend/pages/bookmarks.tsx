import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface BookmarkedProtest {
    id: string;
    title: string;
    description: string;
    location_description: string;
    categories: string[];
    status: 'planned' | 'ongoing' | 'completed';
    start_date: string;
    participant_count: number;
    verification_status: string;
    featured: boolean;
    bookmarked_at: string;
    is_bookmarked: boolean;
    is_following: boolean;
}

const BookmarksPage = () => {
    const router = useRouter();
    const [bookmarks, setBookmarks] = useState<BookmarkedProtest[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [sortBy, setSortBy] = useState<'date_added' | 'protest_date' | 'title'>('date_added');
    const [filterStatus, setFilterStatus] = useState<'all' | 'planned' | 'ongoing' | 'completed'>('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const userData = localStorage.getItem('user');
                if (!userData) {
                    router.push('/login');
                    return;
                }

                await fetchBookmarks();
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            }
        };

        checkAuth();
    }, [router]);

    const fetchBookmarks = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/bookmarks', {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setBookmarks(data.bookmarks || []);
            } else if (response.status === 401) {
                router.push('/login');
            } else {
                // Fallback demo data
                setBookmarks([
                    {
                        id: '1',
                        title: 'Atlanta Climate Action Rally',
                        description: 'Join hundreds of Atlantans demanding climate action from city council. We\'re calling for renewable energy investments and carbon neutrality by 2030.',
                        location_description: 'Atlanta City Hall, 55 Trinity Ave SW, Atlanta, GA',
                        categories: ['Environmental', 'Climate Change'],
                        status: 'planned',
                        start_date: '2024-08-05T14:00:00',
                        participant_count: 450,
                        verification_status: 'verified',
                        featured: true,
                        bookmarked_at: '2024-07-28T10:30:00',
                        is_bookmarked: true,
                        is_following: false
                    },
                    {
                        id: '2',
                        title: 'March for Public Education Funding',
                        description: 'Georgia teachers and parents march to the State Capitol demanding increased education funding and teacher pay raises.',
                        location_description: 'Georgia State Capitol, 206 Washington St SW, Atlanta, GA',
                        categories: ['Education', 'Labor Rights'],
                        status: 'planned',
                        start_date: '2024-08-17T10:00:00',
                        participant_count: 750,
                        verification_status: 'verified',
                        featured: true,
                        bookmarked_at: '2024-07-25T15:45:00',
                        is_bookmarked: true,
                        is_following: true
                    },
                    {
                        id: '3',
                        title: 'Justice for Community - Police Reform Rally',
                        description: 'Community members gather at Centennial Olympic Park to call for police accountability and criminal justice reform in Atlanta.',
                        location_description: 'Centennial Olympic Park, 265 Park Ave W NW, Atlanta, GA',
                        categories: ['Racial Justice', 'Criminal Justice Reform'],
                        status: 'completed',
                        start_date: '2024-07-27T14:00:00',
                        participant_count: 650,
                        verification_status: 'verified',
                        featured: false,
                        bookmarked_at: '2024-07-20T09:15:00',
                        is_bookmarked: true,
                        is_following: false
                    }
                ]);
            }
        } catch (error) {
            console.error('Failed to fetch bookmarks:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const removeBookmark = async (protestId: string) => {
        try {
            const response = await fetch(`http://localhost:5000/api/bookmarks/${protestId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (response.ok) {
                setBookmarks(bookmarks.filter(bookmark => bookmark.id !== protestId));
            }
        } catch (error) {
            console.error('Failed to remove bookmark:', error);
        }
    };

    const toggleFollow = async (protestId: string) => {
        try {
            const bookmark = bookmarks.find(b => b.id === protestId);
            if (!bookmark) return;

            const response = await fetch('http://localhost:5000/api/follows', {
                method: bookmark.is_following ? 'DELETE' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ protest_id: protestId }),
                credentials: 'include'
            });

            if (response.ok) {
                setBookmarks(bookmarks.map(b =>
                    b.id === protestId ? { ...b, is_following: !b.is_following } : b
                ));
            }
        } catch (error) {
            console.error('Failed to toggle follow:', error);
        }
    };

    // Filter and sort bookmarks
    const filteredBookmarks = bookmarks
        .filter(bookmark => {
            if (filterStatus !== 'all' && bookmark.status !== filterStatus) return false;
            if (searchQuery && !bookmark.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
                !bookmark.categories.some(cat => cat.toLowerCase().includes(searchQuery.toLowerCase()))) return false;
            return true;
        })
        .sort((a, b) => {
            switch (sortBy) {
                case 'date_added':
                    return new Date(b.bookmarked_at).getTime() - new Date(a.bookmarked_at).getTime();
                case 'protest_date':
                    return new Date(a.start_date).getTime() - new Date(b.start_date).getTime();
                case 'title':
                    return a.title.localeCompare(b.title);
                default:
                    return 0;
            }
        });

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
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatRelativeDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
        
        if (diffInDays === 0) return 'Today';
        if (diffInDays === 1) return 'Yesterday';
        if (diffInDays < 7) return `${diffInDays} days ago`;
        if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
        return formatDate(dateString);
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
                <title>My Bookmarks - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">My Bookmarks</h1>
                                <p className="text-gray-600">
                                    {filteredBookmarks.length} of {bookmarks.length} bookmarked protests
                                </p>
                            </div>
                            <div className="flex gap-3">
                                <Link 
                                    href="/search"
                                    className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                                >
                                    + Find More Protests
                                </Link>
                                <Link 
                                    href="/dashboard"
                                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                >
                                    ← Dashboard
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {/* Filters and Search */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            {/* Search */}
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Search Bookmarks
                                </label>
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search by title or category..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                />
                            </div>

                            {/* Filter by Status */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Filter by Status
                                </label>
                                <select
                                    value={filterStatus}
                                    onChange={(e) => setFilterStatus(e.target.value as any)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                >
                                    <option value="all">All Statuses</option>
                                    <option value="planned">Planned</option>
                                    <option value="ongoing">Ongoing</option>
                                    <option value="completed">Completed</option>
                                </select>
                            </div>

                            {/* Sort by */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Sort by
                                </label>
                                <select
                                    value={sortBy}
                                    onChange={(e) => setSortBy(e.target.value as any)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                >
                                    <option value="date_added">Date Added</option>
                                    <option value="protest_date">Protest Date</option>
                                    <option value="title">Title A-Z</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Bookmarks List */}
                    {filteredBookmarks.length === 0 ? (
                        <div className="text-center py-12">
                            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">
                                {searchQuery || filterStatus !== 'all' ? 'No matching bookmarks' : 'No bookmarks yet'}
                            </h3>
                            <p className="text-gray-600 mb-4">
                                {searchQuery || filterStatus !== 'all' 
                                    ? 'Try adjusting your search or filters'
                                    : 'Start bookmarking protests to keep track of events you\'re interested in'
                                }
                            </p>
                            <Link 
                                href="/search"
                                className="inline-block bg-primary text-white px-6 py-3 rounded-lg hover:bg-primary/90"
                            >
                                Discover Protests
                            </Link>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {filteredBookmarks.map((bookmark) => (
                                <div key={bookmark.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            {/* Header */}
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex items-center gap-3">
                                                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(bookmark.status)}`}>
                                                        {bookmark.status.toUpperCase()}
                                                    </span>
                                                    {bookmark.featured && (
                                                        <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                            ⭐ Featured
                                                        </span>
                                                    )}
                                                    {bookmark.is_following && (
                                                        <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                            👁️ Following
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-xs text-gray-500">
                                                    Bookmarked {formatRelativeDate(bookmark.bookmarked_at)}
                                                </div>
                                            </div>

                                            {/* Title and Description */}
                                            <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                                <Link href={`/protest/${bookmark.id}`} className="hover:text-primary">
                                                    {bookmark.title}
                                                </Link>
                                            </h3>
                                            
                                            <p className="text-gray-600 mb-3 line-clamp-2">
                                                {bookmark.description}
                                            </p>

                                            {/* Location and Date */}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                                <div className="flex items-center text-sm text-gray-600">
                                                    <svg className="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                                    </svg>
                                                    {bookmark.location_description}
                                                </div>
                                                <div className="flex items-center text-sm text-gray-600">
                                                    <svg className="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                    </svg>
                                                    {formatDate(bookmark.start_date)}
                                                </div>
                                            </div>

                                            {/* Categories and Participants */}
                                            <div className="flex items-center justify-between">
                                                <div className="flex flex-wrap gap-2">
                                                    {bookmark.categories.slice(0, 3).map((category) => (
                                                        <span key={category} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                                                            {category}
                                                        </span>
                                                    ))}
                                                    {bookmark.categories.length > 3 && (
                                                        <span className="text-xs text-gray-500">+{bookmark.categories.length - 3} more</span>
                                                    )}
                                                </div>
                                                <div className="text-sm text-gray-500">
                                                    👥 {bookmark.participant_count.toLocaleString()} participants
                                                </div>
                                            </div>
                                        </div>

                                        {/* Actions */}
                                        <div className="ml-6 flex flex-col gap-2">
                                            <button
                                                onClick={() => toggleFollow(bookmark.id)}
                                                className={`px-3 py-2 rounded text-sm font-medium ${
                                                    bookmark.is_following
                                                        ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                                }`}
                                                title={bookmark.is_following ? 'Unfollow' : 'Follow for updates'}
                                            >
                                                {bookmark.is_following ? '👁️ Following' : '👁️ Follow'}
                                            </button>
                                            
                                            <button
                                                onClick={() => removeBookmark(bookmark.id)}
                                                className="px-3 py-2 bg-red-100 text-red-700 rounded text-sm font-medium hover:bg-red-200"
                                                title="Remove bookmark"
                                            >
                                                🗑️ Remove
                                            </button>
                                            
                                            <Link
                                                href={`/protest/${bookmark.id}`}
                                                className="px-3 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary/90 text-center"
                                            >
                                                View Details
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default BookmarksPage;