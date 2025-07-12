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
    <div className="min-h-screen bg-gray-100">
      <div className="pt-20 px-4 max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          {/* Profile Header */}
          <div className="relative">
            <div className="h-48 w-full bg-[#c8d5b9]" />
            <div className="absolute -bottom-16 left-8">
              <div className="w-32 h-32 rounded-full border-4 border-white flex items-center justify-center text-4xl font-bold text-white bg-[#4a7c59]">
                AJ
              </div>
            </div>
          </div>

          <div className="pt-20 pb-8 px-8">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{userData.name}</h1>
                <p className="text-gray-600">{userData.username}</p>
                <p className="text-sm text-gray-500 mt-1">
                  📍 {userData.location} • Joined {userData.joinDate}
                </p>
              </div>
              <button
                className="px-6 py-2 text-white rounded-lg bg-[#4a7c59] transition-colors hover:bg-[#81a989]"
              >
                Edit Profile
              </button>
            </div>

            <p className="text-gray-700 mb-6">{userData.bio}</p>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-6 mb-6">
              {[
                ['Protests Attended', userData.stats.protestsAttended],
                ['Posts Shared', userData.stats.postsShared],
                ['Followers', userData.stats.followersCount.toLocaleString()],
                ['Following', userData.stats.followingCount.toLocaleString()],
              ].map(([label, value]) => (
                <div key={label} className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{value}</div>
                  <div className="text-sm text-[#6b8f71]">{label}</div>
                </div>
              ))}
            </div>

            {/* Badges */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Achievements</h3>
              <div className="flex flex-wrap gap-4">
                {userData.badges.map((badge, index) => (
                  <div key={index} className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg">
                    <span className="text-xl">{badge.icon}</span>
                    <div>
                      <div className="font-medium text-gray-900">{badge.name}</div>
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
                  ? 'bg-[#4a7c59] text-white'
                  : 'bg-transparent text-[#4a7c59] border border-[#4a7c59] hover:bg-[#81a989] hover:text-white'
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
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h3>
              <div className="space-y-4">
                {userData.recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                    <span className="text-2xl">{activity.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
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
              <h3 className="text-xl font-semibold text-gray-900 mb-4">All Activity</h3>
              <p className="text-gray-600">Comprehensive activity history will be displayed here.</p>
            </div>
          )}

          {activeTab === 'posts' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Your Posts</h3>
              <p className="text-gray-600">Your shared posts and updates will be displayed here.</p>
            </div>
          )}

          {activeTab === 'events' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Events</h3>
              <p className="text-gray-600">Events you've organized or plan to attend will be displayed here.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
