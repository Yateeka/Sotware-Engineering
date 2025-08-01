import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface SearchResult {
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
    is_bookmarked?: boolean;
    is_following?: boolean;
}

interface SearchParams {
    q: string;
    category: string;
    location: string;
    date_from: string;
    date_to: string;
    status: string;
}

const SearchPage = () => {
    const router = useRouter();
    const [searchParams, setSearchParams] = useState<SearchParams>({
        q: '',
        category: '',
        location: '',
        date_from: '',
        date_to: '',
        status: ''
    });
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
    const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

    useEffect(() => {
        // Check authentication status
        const userData = localStorage.getItem('user');
        if (!userData) {
            router.push('/login');
            return;
        }
        setIsAuthenticated(true);

        // Get query from URL if exists
        const urlQuery = router.query.q as string;
        if (urlQuery) {
            setSearchParams(prev => ({ ...prev, q: urlQuery }));
            performSearch({ ...searchParams, q: urlQuery });
        }
    }, [router.query]);

    const categories = [
        'Environmental', 'Labor Rights', 'Human Rights', 'Racial Justice',
        'Education', 'Healthcare', 'Housing Rights', 'Gender Equality',
        'Immigration Rights', 'LGBTQ+ Rights', 'Climate Change'
    ];

    const performSearch = async (params: SearchParams = searchParams) => {
        if (!params.q && !params.category && !params.location) {
            return;
        }

        setIsLoading(true);
        setHasSearched(true);

        try {
            const searchQuery = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value) searchQuery.append(key, value);
            });

            const response = await fetch(`http://localhost:5000/api/protests/search?${searchQuery}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setSearchResults(data.results || []);
            } else if (response.status === 401) {
                router.push('/login');
            } else {
                console.error('Search failed');
                setSearchResults([]);
            }
        } catch (error) {
            console.error('Search error:', error);
            setSearchResults([]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        performSearch();
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setSearchParams({
            ...searchParams,
            [e.target.name]: e.target.value
        });
    };

    const clearFilters = () => {
        setSearchParams({
            q: '',
            category: '',
            location: '',
            date_from: '',
            date_to: '',
            status: ''
        });
        setSearchResults([]);
        setHasSearched(false);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
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

    const handleBookmark = async (protestId: string) => {
        try {
            const response = await fetch('http://localhost:5000/api/bookmarks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ protest_id: protestId }),
                credentials: 'include'
            });

            if (response.ok) {
                setSearchResults(results =>
                    results.map(result =>
                        result.id === protestId
                            ? { ...result, is_bookmarked: true }
                            : result
                    )
                );
            }
        } catch (error) {
            console.error('Bookmark failed:', error);
        }
    };

    const handleFollow = async (protestId: string) => {
        try {
            const response = await fetch('http://localhost:5000/api/follows', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ protest_id: protestId }),
                credentials: 'include'
            });

            if (response.ok) {
                setSearchResults(results =>
                    results.map(result =>
                        result.id === protestId
                            ? { ...result, is_following: true }
                            : result
                    )
                );
            }
        } catch (error) {
            console.error('Follow failed:', error);
        }
    };

    if (!isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>Search Protests - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow-sm border-b">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Search Protests</h1>
                                <p className="text-gray-600">Find protests, movements, and demonstrations worldwide</p>
                            </div>
                            <Link 
                                href="/dashboard"
                                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                            >
                                ← Back to Dashboard
                            </Link>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {/* Search Form */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* Main Search Bar */}
                            <div className="relative">
                                <input
                                    type="text"
                                    name="q"
                                    value={searchParams.q}
                                    onChange={handleInputChange}
                                    placeholder="Search by keywords, organization, or topic..."
                                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                />
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="absolute right-2 top-2 bg-primary text-white px-4 py-1 rounded-lg hover:bg-primary/90 disabled:opacity-50"
                                >
                                    {isLoading ? 'Searching...' : 'Search'}
                                </button>
                            </div>

                            {/* Quick Filters */}
                            <div className="flex flex-wrap gap-3">
                                <select
                                    name="category"
                                    value={searchParams.category}
                                    onChange={handleInputChange}
                                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                >
                                    <option value="">All Categories</option>
                                    {categories.map(cat => (
                                        <option key={cat} value={cat}>{cat}</option>
                                    ))}
                                </select>

                                <input
                                    type="text"
                                    name="location"
                                    value={searchParams.location}
                                    onChange={handleInputChange}
                                    placeholder="Location (city, state, country)"
                                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                />

                                <select
                                    name="status"
                                    value={searchParams.status}
                                    onChange={handleInputChange}
                                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                >
                                    <option value="">All Statuses</option>
                                    <option value="planned">Planned</option>
                                    <option value="ongoing">Ongoing</option>
                                    <option value="completed">Completed</option>
                                </select>

                                <button
                                    type="button"
                                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                                >
                                    Advanced Filters
                                </button>

                                {(searchParams.q || searchParams.category || searchParams.location) && (
                                    <button
                                        type="button"
                                        onClick={clearFilters}
                                        className="px-3 py-2 text-red-600 hover:text-red-800 text-sm"
                                    >
                                        Clear All
                                    </button>
                                )}
                            </div>

                            {/* Advanced Filters */}
                            {showAdvancedFilters && (
                                <div className="border-t pt-4 mt-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Date From
                                            </label>
                                            <input
                                                type="date"
                                                name="date_from"
                                                value={searchParams.date_from}
                                                onChange={handleInputChange}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Date To
                                            </label>
                                            <input
                                                type="date"
                                                name="date_to"
                                                value={searchParams.date_to}
                                                onChange={handleInputChange}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </form>
                    </div>

                    {/* Results Header */}
                    {hasSearched && (
                        <div className="flex justify-between items-center mb-6">
                            <div>
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Search Results ({searchResults.length})
                                </h2>
                                {searchParams.q && (
                                    <p className="text-gray-600">Results for "{searchParams.q}"</p>
                                )}
                            </div>

                            <div className="flex items-center gap-3">
                                <span className="text-sm text-gray-600">View:</span>
                                <button
                                    onClick={() => setViewMode('list')}
                                    className={`p-2 rounded ${viewMode === 'list' ? 'bg-primary text-white' : 'bg-gray-200 text-gray-600'}`}
                                >
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                                    </svg>
                                </button>
                                <button
                                    onClick={() => setViewMode('grid')}
                                    className={`p-2 rounded ${viewMode === 'grid' ? 'bg-primary text-white' : 'bg-gray-200 text-gray-600'}`}
                                >
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 6.707 6.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Loading State */}
                    {isLoading && (
                        <div className="text-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                            <p className="text-gray-600">Searching protests...</p>
                        </div>
                    )}

                    {/* Search Results */}
                    {!isLoading && hasSearched && (
                        <>
                            {searchResults.length === 0 ? (
                                <div className="text-center py-12">
                                    <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                    <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
                                    <p className="text-gray-600 mb-4">
                                        Try adjusting your search terms or filters
                                    </p>
                                    <button
                                        onClick={clearFilters}
                                        className="text-primary hover:text-primary/80"
                                    >
                                        Clear all filters
                                    </button>
                                </div>
                            ) : (
                                <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
                                    {searchResults.map((result) => (
                                        <div
                                            key={result.id}
                                            className={`bg-white rounded-lg shadow hover:shadow-lg transition-shadow ${
                                                viewMode === 'list' ? 'p-6' : 'p-4'
                                            }`}
                                        >
                                            <div className="flex justify-between items-start mb-3">
                                                <div className="flex items-center gap-2">
                                                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(result.status)}`}>
                                                        {result.status.toUpperCase()}
                                                    </span>
                                                    {result.featured && (
                                                        <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                            ⭐ Featured
                                                        </span>
                                                    )}
                                                </div>
                                                <span className="text-sm text-gray-500">
                                                    {formatDate(result.start_date)}
                                                </span>
                                            </div>

                                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                                <Link href={`/protest/${result.id}`} className="hover:text-primary">
                                                    {result.title}
                                                </Link>
                                            </h3>

                                            <p className="text-gray-600 mb-3 line-clamp-2">
                                                {result.description}
                                            </p>

                                            <p className="text-sm text-gray-500 mb-3">
                                                📍 {result.location_description}
                                            </p>

                                            <div className="flex flex-wrap gap-2 mb-4">
                                                {result.categories.slice(0, 3).map((category) => (
                                                    <span key={category} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                                                        {category}
                                                    </span>
                                                ))}
                                                {result.categories.length > 3 && (
                                                    <span className="text-xs text-gray-500">+{result.categories.length - 3} more</span>
                                                )}
                                            </div>

                                            <div className="flex justify-between items-center">
                                                <span className="text-sm text-gray-500">
                                                    👥 {result.participant_count.toLocaleString()} participants
                                                </span>

                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleBookmark(result.id)}
                                                        disabled={result.is_bookmarked}
                                                        className={`p-2 rounded text-sm ${
                                                            result.is_bookmarked 
                                                                ? 'bg-yellow-100 text-yellow-700' 
                                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                                        }`}
                                                        title={result.is_bookmarked ? 'Bookmarked' : 'Bookmark'}
                                                    >
                                                        🔖
                                                    </button>
                                                    <button
                                                        onClick={() => handleFollow(result.id)}
                                                        disabled={result.is_following}
                                                        className={`p-2 rounded text-sm ${
                                                            result.is_following 
                                                                ? 'bg-blue-100 text-blue-700' 
                                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                                        }`}
                                                        title={result.is_following ? 'Following' : 'Follow'}
                                                    >
                                                        👁️
                                                    </button>
                                                    <Link
                                                        href={`/protest/${result.id}`}
                                                        className="px-3 py-2 bg-primary text-white rounded text-sm hover:bg-primary/90"
                                                    >
                                                        View
                                                    </Link>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}

                    {/* Initial State */}
                    {!hasSearched && !isLoading && (
                        <div className="text-center py-12">
                            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">Search for Protests</h3>
                            <p className="text-gray-600 mb-6">
                                Use the search bar above to find protests by keywords, location, or category
                            </p>

                            {/* Quick Search Suggestions */}
                            <div className="max-w-md mx-auto">
                                <h4 className="text-sm font-medium text-gray-700 mb-3">Popular searches:</h4>
                                <div className="flex flex-wrap gap-2 justify-center">
                                    {['Atlanta', 'Climate Change', 'Labor Rights', 'Education', 'Healthcare'].map(suggestion => (
                                        <button
                                            key={suggestion}
                                            onClick={() => {
                                                setSearchParams(prev => ({ ...prev, q: suggestion }));
                                                performSearch({ ...searchParams, q: suggestion });
                                            }}
                                            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default SearchPage;