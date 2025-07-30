import { useState, useEffect } from 'react';

interface LikedItem {
  id: number;
  type: 'protest' | 'event' | 'article' | 'post';
  title: string;
  location: string;
  date?: string;
  participants?: string;
  status?: 'ongoing' | 'ended' | 'planned';
  description: string;
  tags: string[];
  likedAt: string;
  author?: string;
  imageUrl?: string;
  engagement?: {
    likes: number;
    shares: number;
    comments: number;
  };
}

interface FilterOptions {
  type: string;
  status: string;
  timeframe: string;
}

const Likes: React.FC = () => {
  const [likedItems, setLikedItems] = useState<LikedItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<LikedItem[]>([]);
  const [filters, setFilters] = useState<FilterOptions>({
    type: 'all',
    status: 'all',
    timeframe: 'all'
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Mock data - in a real app, this would come from an API
  const mockLikedItems: LikedItem[] = [
    {
      id: 1,
      type: 'protest',
      title: 'Climate Action March',
      location: 'New York, USA',
      date: '2024-03-15',
      participants: '10,000+',
      status: 'ended',
      description: 'Large-scale climate action march demanding immediate action on global warming and environmental protection.',
      tags: ['climate', 'environment', 'activism'],
      likedAt: '2 hours ago',
      engagement: { likes: 1250, shares: 340, comments: 89 }
    },
    {
      id: 2,
      type: 'article',
      title: 'The Impact of Peaceful Protests on Policy Change',
      location: 'Online',
      description: 'An in-depth analysis of how peaceful protests have historically influenced government policy and social change.',
      tags: ['research', 'policy', 'activism'],
      likedAt: '1 day ago',
      author: 'Dr. Sarah Johnson',
      engagement: { likes: 892, shares: 156, comments: 23 }
    },
    {
      id: 3,
      type: 'event',
      title: 'Community Organizing Workshop',
      location: 'Berlin, Germany',
      date: '2024-04-20',
      status: 'planned',
      description: 'Learn effective strategies for community organizing and grassroots activism from experienced organizers.',
      tags: ['workshop', 'education', 'organizing'],
      likedAt: '3 days ago',
      engagement: { likes: 234, shares: 78, comments: 45 }
    },
    {
      id: 4,
      type: 'post',
      title: 'Indigenous Rights Rally Success',
      location: 'Ottawa, Canada',
      date: '2024-03-10',
      status: 'ended',
      description: 'Celebrating the successful rally that brought together 5,000+ supporters of indigenous rights and sovereignty.',
      tags: ['indigenous', 'rights', 'victory'],
      likedAt: '1 week ago',
      author: 'Maria Lightfoot',
      engagement: { likes: 567, shares: 234, comments: 67 }
    },
    {
      id: 5,
      type: 'protest',
      title: 'Workers Rights Demonstration',
      location: 'London, UK',
      date: '2024-03-25',
      participants: '8,000+',
      status: 'ongoing',
      description: 'Ongoing demonstration for fair wages, better working conditions, and workers\' rights protection.',
      tags: ['workers', 'rights', 'labor'],
      likedAt: '2 weeks ago',
      engagement: { likes: 1890, shares: 445, comments: 123 }
    },
    {
      id: 6,
      type: 'article',
      title: 'Digital Activism in the Modern Age',
      location: 'Online',
      description: 'Exploring how social media and digital platforms are transforming the landscape of modern activism.',
      tags: ['digital', 'technology', 'activism'],
      likedAt: '3 weeks ago',
      author: 'Tech for Good Collective',
      engagement: { likes: 445, shares: 89, comments: 34 }
    }
  ];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'protest':
        return '✊';
      case 'event':
        return '📅';
      case 'article':
        return '📄';
      case 'post':
        return '💬';
      default:
        return '🔖';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ongoing':
        return 'bg-primary text-white';
      case 'ended':
        return 'bg-gray-500 text-white';
      case 'planned':
        return 'bg-secondary text-primary';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleUnlike = (itemId: number) => {
    setLikedItems(prev => prev.filter(item => item.id !== itemId));
    setFilteredItems(prev => prev.filter(item => item.id !== itemId));
  };

  const applyFilters = () => {
    let filtered = [...likedItems];

    // Apply search filter
    if (searchQuery.trim()) {
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Apply type filter
    if (filters.type !== 'all') {
      filtered = filtered.filter(item => item.type === filters.type);
    }

    // Apply status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(item => item.status === filters.status);
    }

    // Apply timeframe filter
    if (filters.timeframe !== 'all') {
      const now = new Date();
      filtered = filtered.filter(item => {
        const likedDate = new Date(item.likedAt);
        switch (filters.timeframe) {
          case 'today':
            return now.toDateString() === likedDate.toDateString();
          case 'week':
            return (now.getTime() - likedDate.getTime()) <= 7 * 24 * 60 * 60 * 1000;
          case 'month':
            return (now.getTime() - likedDate.getTime()) <= 30 * 24 * 60 * 60 * 1000;
          default:
            return true;
        }
      });
    }

    setFilteredItems(filtered);
  };

  const clearFilters = () => {
    setFilters({ type: 'all', status: 'all', timeframe: 'all' });
    setSearchQuery('');
  };

  useEffect(() => {
    setLikedItems(mockLikedItems);
    setFilteredItems(mockLikedItems);
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchQuery, filters, likedItems]);

  return (
    <div className="min-h-screen bg-background" style={{ marginLeft: '16px' }}>
      {/* Header */}
      <div className="bg-primary shadow-sm">
        <div className="px-4 py-8">
          <h1 className="text-4xl font-bold text-white mb-2">Your Likes</h1>
          <p className="text-white text-opacity-80">
            Manage and revisit the protests, events, and content you've liked
          </p>
        </div>
      </div>

      {/* Search and Filters Section */}
      <div className="px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          {/* Search Bar */}
          <div className="mb-6">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search your liked items..."
                className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none text-lg"
              />
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
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
                <option value="article">Articles</option>
                <option value="post">Posts</option>
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Liked</label>
              <select
                value={filters.timeframe}
                onChange={(e) => setFilters({...filters, timeframe: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={clearFilters}
                className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                Clear Filters
              </button>
            </div>
          </div>

          {/* Results Summary */}
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>{filteredItems.length} liked items</span>
            <span>{likedItems.length} total likes</span>
          </div>
        </div>

        {/* Liked Items Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <span className="ml-4 text-gray-600">Loading your likes...</span>
          </div>
        ) : filteredItems.length > 0 ? (
          <div className="space-y-6">
            {filteredItems.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3 flex-1">
                      <span className="text-3xl">{getTypeIcon(item.type)}</span>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-xl font-semibold text-primary">{item.title}</h3>
                          {item.status && (
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(item.status)}`}>
                              {item.status}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            {item.location}
                          </span>
                          {item.date && (
                            <span className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {new Date(item.date).toLocaleDateString()}
                            </span>
                          )}
                          {item.participants && (
                            <span className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                              </svg>
                              {item.participants}
                            </span>
                          )}
                        </div>
                        {item.author && (
                          <p className="text-sm text-gray-600 mb-2">
                            by <span className="font-medium">{item.author}</span>
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">Liked {item.likedAt}</span>
                      <button
                        onClick={() => handleUnlike(item.id)}
                        className="p-2 text-red-500 hover:bg-red-50 rounded-full transition-colors"
                        title="Unlike"
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                        </svg>
                      </button>
                    </div>
                  </div>

                  <p className="text-gray-700 mb-4 leading-relaxed">{item.description}</p>

                  <div className="flex flex-wrap items-center justify-between">
                    <div className="flex flex-wrap gap-2 mb-2 md:mb-0">
                      {item.tags.map((tag, index) => (
                        <span key={index} className="bg-secondary text-primary px-3 py-1 rounded-full text-sm font-medium">
                          #{tag}
                        </span>
                      ))}
                    </div>
                    {item.engagement && (
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                          </svg>
                          {item.engagement.likes}
                        </span>
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684 3 3 0 010 2.684zm0 0a6.96 6.96 0 01-1.992-1.992c-.412-.509-.648-1.148-.648-1.83 0-.682.236-1.321.648-1.83C7.104 4.94 7.742 4.704 8.424 4.704c.682 0 1.32.236 1.83.648.509.412.746 1.148.746 1.83 0 .682-.237 1.321-.746 1.83a6.96 6.96 0 01-1.992 1.992zM15 10a3 3 0 00-3 3 3 3 0 003 3 3 3 0 003-3 3 3 0 00-3-3z" />
                          </svg>
                          {item.engagement.shares}
                        </span>
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                          </svg>
                          {item.engagement.comments}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">💔</div>
            <h3 className="text-xl font-semibold text-gray-600 mb-2">
              {searchQuery || Object.values(filters).some(f => f !== 'all') 
                ? 'No matching likes found' 
                : 'No likes yet'
              }
            </h3>
            <p className="text-gray-500 mb-4">
              {searchQuery || Object.values(filters).some(f => f !== 'all')
                ? 'Try adjusting your search or filters to find what you\'re looking for.'
                : 'Start exploring protests and events to build your collection of liked content.'
              }
            </p>
            {(searchQuery || Object.values(filters).some(f => f !== 'all')) && (
              <button
                onClick={clearFilters}
                className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-opacity-90 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Likes;
