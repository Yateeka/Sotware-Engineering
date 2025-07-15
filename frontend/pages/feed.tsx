import React from 'react';

const posts = Array(4).fill({
  username: 'User name',
  content:
    'India has witnessed approximately 843 protest events this month, according to aggregated reports from regional monitoring sources and civil society networks.',
  replies: 31,
  retweets: 82,
  likes: 606,
  views: '19K',
});

const Feed: React.FC = () => {
  return (
    <div className="flex p-25 bg-background">
      {/* Feed Section */}
      <div className="w-2/3 p-10 space-y-4 bg-secondary">
        {/* What's Happening */}
        <div className="bg-white p-4 rounded-lg">
          <div className="flex items-start space-x-2">
            <div className="bg-white rounded-full w-10 h-10" />
            <input
              type="text"
              placeholder="What's happening?"
              className="w-full p-2 rounded-lg border border-gray-300"
            />
          </div>
          <div className="flex justify-between items-center mt-2">
            <div className="flex space-x-2 text-gray-600">
              <span>📷</span>
              <span>🎥</span>
              <span>📊</span>
              <span>😊</span>
              <span>📅</span>
              <span>📍</span>
            </div>
            <button className="bg-secondary text-black px-4 py-1 rounded">POST</button>
          </div>
        </div>

        {/* Posts */}
        {posts.map((post, index) => (
          <div
            key={index}
            className="flex p-4 rounded-lg bg-white"
          >
            <div className="bg-white rounded-full w-10 h-10 mr-4" />
            <div>
              <p className="font-semibold">{post.username}</p>
              <p className="text-sm text-gray-600">{post.content}</p>
              <div className="flex space-x-4 mt-2 text-gray-600 text-sm">
                <span>💬 {post.replies}</span>
                <span>🔁 {post.retweets}</span>
                <span>❤️ {post.likes}</span>
                <span>📊 {post.views}</span>
                <span>🔖</span>
                <span>↗️</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sidebar */}
      <div className="w-1/3 p-4">
        {/* Trending */}
        <div className="bg-accent-dark text-accent-light p-4 rounded-lg mb-4">
          <h3 className="font-bold mb-2">What's happening</h3>
          <ul className="space-y-2 text-sm">
            <li>⚾ Cardinals at Cubs - Live</li>
            <li>Chris Richards +USINT +GoldCup (2.58K+)</li>
            <li>American Party (116K posts)</li>
            <li>Zain (5,553 posts)</li>
            <li>Kristl Neern (5.5K posts)</li>
          </ul>
        </div>

        {/* Who to Follow */}
        <div className="bg-accent-dark text-accent-light p-4 rounded-lg">
          <h3 className="font-bold mb-2">Who to follow</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between items-center">
              <span>Donald Trump</span>
              <button className="bg-primary text-accent-dark px-2 rounded">Follow</button>
            </li>
            <li className="flex justify-between items-center">
              <span>CNN Politics</span>
              <button className="bg-primary text-accent-dark px-2 rounded">Follow</button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Feed;