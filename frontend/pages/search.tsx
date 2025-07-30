import { useState, useEffect } from 'react';

interface SearchResult {
  id: number;
  type: 'protest' | 'event' | 'country';
  title: string;
  location: string;
  date?: string;
  participants?: string;
  status?: 'ongoing' | 'ended' | 'planned';
  description: string;
  tags: string[];
}

interface SearchFilters {
  type: string;
  status: string;
  location: string;
  dateRange: string;
}

const Search: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [filters, setFilters] = useState<SearchFilters>({
    type: 'all',
    status: 'all',
    location: 'all',
    dateRange: 'all'
  });
  const [showFilters, setShowFilters] = useState<boolean>(false);

  // Mock search data - in a real app, this would come from an API
  const mockSearchResults: SearchResult[] = [
    {
      id: 1,
      type: 'protest',
      title: 'Climate Action March',
      location: 'New York, USA',
      date: '2024-03-15',
      participants: '10,000+',
      status: 'ended',
      description: 'Large-scale climate action march demanding immediate action on global warming and environmental protection.',
      tags: ['climate', 'environment', 'activism']
    },
    {
      id: 2,
      type: 'protest',
      title: 'Workers Rights Demonstration',
      location: 'Berlin, Germany',
      date: '2024-03-18',
      participants: '5,000+',
      status: 'ongoing',
      description: 'Workers demanding better working conditions, fair wages, and improved labor rights.',
      tags: ['labor', 'rights', 'workers']
    },
    {
      id: 3,
      type: 'event',
      title: 'Peace Rally',
      location: 'London, UK',
      date: '2024-03-20',
      participants: '15,000+',
      status: 'planned',
      description: 'International peace rally calling for an end to conflicts and promotion of diplomatic solutions.',
      tags: ['peace', 'diplomacy', 'international']
    },
    {
      id: 4,
      type: 'protest',
      title: 'Student Strike for Education',
      location: 'Paris, France',
      date: '2024-03-22',
      participants: '8,000+',
      status: 'ongoing',
      description: 'Students protesting education budget cuts and demanding increased funding for universities.',
      tags: ['education', 'students', 'budget']
    },
    {
      id: 5,
      type: 'country',
      title: 'Brazil',
      location: 'South America',
      description: 'Recent protests include Amazon protection rallies and indigenous rights marches.',
      tags: ['amazon', 'indigenous', 'environment']
    }
  ];

  const performSearch = (query: string) => {
    setIsLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      if (!query.trim()) {
        setSearchResults([]);
      } else {
        const filtered = mockSearchResults.filter(result => 
          result.title.toLowerCase().includes(query.toLowerCase()) ||
          result.location.toLowerCase().includes(query.toLowerCase()) ||
          result.description.toLowerCase().includes(query.toLowerCase()) ||
          result.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
        );
        setSearchResults(filtered);
      }
      setIsLoading(false);
    }, 500);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(searchQuery);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'ongoing': return 'bg-primary text-white';
      case 'ended': return 'bg-gray-500 text-white';
      case 'planned': return 'bg-secondary text-primary';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'protest': return '✊';
      case 'event': return '📅';
      case 'country': return '🌍';
      default: return '📄';
    }
  };

  useEffect(() => {
    if (searchQuery.length > 2) {
      const debounceTimer = setTimeout(() => {
        performSearch(searchQuery);
      }, 300);
      return () => clearTimeout(debounceTimer);
    } else if (searchQuery.length === 0) {
      setSearchResults([]);
    }
  }, [searchQuery]);

  return (
    <div className="min-h-screen bg-background" style={{ marginLeft: '16px' }}>
      {/* Header */}
      <div className="bg-primary shadow-sm">
        <div className="px-4 py-8">
          <h1 className="text-4xl font-bold text-white mb-2">Search Global Events</h1>
          <p className="text-white text-opacity-80">
            Find protests, events, and country information from around the world
          </p>
        </div>
      </div>

      {/* Search Section */}
      <div className="px-4 py-8">
        {/* Search Form */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search for protests, events, countries, or topics..."
                    className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none text-lg"
                  />
                  <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={clearSearch}
                      className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-primary text-white px-6 py-3 rounded-lg hover:bg-opacity-90 transition-colors font-medium disabled:opacity-50"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowFilters(!showFilters)}
                  className="bg-gray-100 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                >
                  Filters
                </button>
              </div>
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <div className="border-t pt-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <select
                      value={filters.type}
                      onChange={(e) => setFilters({...filters, type: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="all">All Types</option>
                      <option value="protest">Protests</option>
                      <option value="event">Events</option>
                      <option value="country">Countries</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                    <select
                      value={filters.status}
                      onChange={(e) => setFilters({...filters, status: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="all">All Status</option>
                      <option value="ongoing">Ongoing</option>
                      <option value="planned">Planned</option>
                      <option value="ended">Ended</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <select
                      value={filters.location}
                      onChange={(e) => setFilters({...filters, location: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="all">All Locations</option>
                      <option value="america">Americas</option>
                      <option value="europe">Europe</option>
                      <option value="asia">Asia</option>
                      <option value="africa">Africa</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
                    <select
                      value={filters.dateRange}
                      onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="all">All Time</option>
                      <option value="today">Today</option>
                      <option value="week">This Week</option>
                      <option value="month">This Month</option>
                      <option value="year">This Year</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>

        {/* Search Results */}
        {searchQuery && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-primary">
                Search Results
                {searchResults.length > 0 && (
                  <span className="text-lg font-normal text-gray-600 ml-2">
                    ({searchResults.length} found)
                  </span>
                )}
              </h2>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                <span className="ml-4 text-gray-600">Searching...</span>
              </div>
            ) : searchResults.length > 0 ? (
              <div className="space-y-4">
                {searchResults.map((result) => (
                  <div key={result.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{getTypeIcon(result.type)}</span>
                        <div>
                          <h3 className="text-xl font-semibold text-primary">{result.title}</h3>
                          <p className="text-gray-600">{result.location}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-2">
                        {result.status && (
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(result.status)}`}>
                            {result.status}
                          </span>
                        )}
                        <span className="text-sm text-gray-500 capitalize">{result.type}</span>
                      </div>
                    </div>

                    <p className="text-gray-700 mb-4">{result.description}</p>

                    <div className="flex flex-wrap items-center justify-between">
                      <div className="flex flex-wrap gap-2 mb-2 md:mb-0">
                        {result.tags.map((tag, index) => (
                          <span key={index} className="bg-secondary text-primary px-2 py-1 rounded-full text-xs font-medium">
                            #{tag}
                          </span>
                        ))}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        {result.date && (
                          <span>📅 {new Date(result.date).toLocaleDateString()}</span>
                        )}
                        {result.participants && (
                          <span>👥 {result.participants}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-semibold text-gray-600 mb-2">No results found</h3>
                <p className="text-gray-500">
                  Try adjusting your search terms or filters to find what you're looking for.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Quick Search Suggestions */}
        {!searchQuery && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-primary mb-6">Popular Searches</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {['Climate Action', 'Workers Rights', 'Peace Rally', 'Student Protests', 'Environmental', 'Democracy'].map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => setSearchQuery(suggestion)}
                  className="text-left p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary hover:bg-opacity-5 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">🔥</span>
                    <div>
                      <div className="font-medium text-gray-800">{suggestion}</div>
                      <div className="text-sm text-gray-500">Popular topic</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
