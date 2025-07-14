import React, { useState } from 'react';

const Profile: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');

  const userData = {
    name: 'Alex Johnson',
    username: '@alexj_activist',
    location: 'New York, NY',
    joinDate: 'March 2023',
    bio: 'Human rights advocate and community organizer. Passionate about social justice and environmental protection.',
    stats: {
      protestsAttended: 23,
      postsShared: 156,
      followersCount: 2847,
      followingCount: 1205
    },
    badges: [
      { name: 'Veteran Activist', icon: '🏅', description: 'Attended 20+ protests' },
      { name: 'Community Leader', icon: '👥', description: 'Organized 5+ events' },
      { name: 'Climate Warrior', icon: '🌱', description: 'Active in environmental causes' }
    ],
    recentActivity: [
      {
        id: 1,
        type: 'attended',
        event: 'Climate Action Rally',
        location: 'Central Park, NY',
        date: '2024-07-10',
        icon: '📢'
      },
      {
        id: 2,
        type: 'shared',
        event: 'Labor Rights Update',
        location: 'Detroit, MI',
        date: '2024-07-08',
        icon: '📤'
      },
      {
        id: 3,
        type: 'organized',
        event: 'Community Food Drive',
        location: 'Brooklyn, NY',
        date: '2024-07-05',
        icon: '🎯'
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="pt-20 px-4 max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          {/* Profile Header */}
          <div className="relative">
            <div className="h-48 w-full bg-secondary" />
            <div className="absolute -bottom-16 left-8">
              <div className="w-32 h-32 rounded-full border-4 border-white flex items-center justify-center text-4xl font-bold text-white bg-primary">
                AJ
              </div>
            </div>
          </div>

          <div className="pt-20 pb-8 px-8">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h1 className="text-3xl font-bold text-charcoal-dark">{userData.name}</h1>
                <p className="text-gray-600">{userData.username}</p>
                <p className="text-sm text-gray-500 mt-1">
                  📍 {userData.location} • Joined {userData.joinDate}
                </p>
              </div>
              <button
                className="px-6 py-2 text-white rounded-lg bg-primary transition-colors"
              >
                Edit Profile
              </button>
            </div>

            <p className="text-stone-dark mb-6">{userData.bio}</p>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-6 mb-6">
              {[
                ['Protests Attended', userData.stats.protestsAttended],
                ['Posts Shared', userData.stats.postsShared],
                ['Followers', userData.stats.followersCount.toLocaleString()],
                ['Following', userData.stats.followingCount.toLocaleString()],
              ].map(([label, value]) => (
                <div key={label} className="text-center">
                  <div className="text-2xl font-bold text-accent-dark">{value}</div>
                  <div className="text-sm text-primary">{label}</div>
                </div>
              ))}
            </div>

            {/* Badges */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-accent-dark mb-3">Achievements</h3>
              <div className="flex flex-wrap gap-4">
                {userData.badges.map((badge, index) => (
                  <div key={index} className="flex items-center gap-2 bg-background px-3 py-2 rounded-lg">
                    <span className="text-xl">{badge.icon}</span>
                    <div>
                      <div className="font-medium text-accent-dark">{badge.name}</div>
                      <div className="text-xs text-gray-600">{badge.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          {['overview', 'activity', 'posts', 'events'].map((tab) => (
            <button
              key={tab}
              className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'bg-primary text-white'
                  : 'bg-transparent text-primary border border-primary hover:bg-moss-medium hover:text-white'
              }`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-md p-6">
          {activeTab === 'overview' && (
            <div>
              <h3 className="text-xl font-semibold text-accent-dark mb-4">Recent Activity</h3>
              <div className="space-y-4">
                {userData.recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center gap-4 p-4 bg-background rounded-lg">
                    <span className="text-2xl">{activity.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium text-charcoal-dark">
                        {activity.type === 'attended'
                          ? 'Attended'
                          : activity.type === 'shared'
                          ? 'Shared'
                          : 'Organized'}{' '}
                        {activity.event}
                      </div>
                      <div className="text-sm text-gray-600">
                        {activity.location} • {activity.date}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div>
              <h3 className="text-xl font-semibold text-accent-dark mb-4">All Activity</h3>
              <p className="text-gray-600">Comprehensive activity history will be displayed here.</p>
            </div>
          )}

          {activeTab === 'posts' && (
            <div>
              <h3 className="text-xl font-semibold text-accent-dark mb-4">Your Posts</h3>
              <p className="text-gray-600">Your shared posts and updates will be displayed here.</p>
            </div>
          )}

          {activeTab === 'events' && (
            <div>
              <h3 className="text-xl font-semibold text-accent-dark mb-4">Events</h3>
              <p className="text-gray-600">Events you've organized or plan to attend will be displayed here.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;