import React from 'react';
import WorldMap from '../components/WorldMap';

const MapPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900 text-center">
            Interactive World Map
          </h1>
          <p className="text-gray-600 text-center mt-2">
            Explore countries around the world with our interactive 2D map
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <WorldMap />
      </div>

      {/* Footer */}
      <div className="bg-gray-50 border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <p className="text-center text-sm text-gray-500">
            Built with React, Next.js, and react-simple-maps • Data from World Atlas TopoJSON
          </p>
        </div>
      </div>
    </div>
  );
};

export default MapPage;
