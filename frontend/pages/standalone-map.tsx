import React from 'react';
import WorldMap from '../components/WorldMap';

const StandaloneMapPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Interactive 2D World Map
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Explore the world with our interactive map built with React, Next.js, and react-simple-maps. 
            Hover over countries to see them highlight and click to get more information.
          </p>
        </div>
        
        <WorldMap />
        
        <div className="mt-12 bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-semibold">1</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">2D Mercator Projection</h3>
                <p className="text-gray-600 text-sm">Flat, accurate representation of the world</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-semibold">2</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Interactive Hover Effects</h3>
                <p className="text-gray-600 text-sm">Countries scale and highlight on hover</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-semibold">3</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Click Actions</h3>
                <p className="text-gray-600 text-sm">Alert displays with country name when clicked</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-semibold">4</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Real-time Country Display</h3>
                <p className="text-gray-600 text-sm">Shows hovered country name below the map</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-semibold">5</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Fully Responsive</h3>
                <p className="text-gray-600 text-sm">Works perfectly on all device sizes</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-semibold">6</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">React Hooks</h3>
                <p className="text-gray-600 text-sm">Uses useState for state management</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StandaloneMapPage;
