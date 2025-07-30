'use client';

import React, { useState } from 'react';
import {
  ComposableMap,
  Geographies,
  Geography,
  type GeoFeature,
} from 'react-simple-maps';

const WorldMap: React.FC = () => {
  const [hoveredCountry, setHoveredCountry] = useState<string>('');
  const [clickedCountry, setClickedCountry] = useState<string>('');

  // TopoJSON data source - reliable public CDN
  const geoUrl = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

  const getCountryName = (geo: GeoFeature): string => {
    return geo.properties.NAME || 
           geo.properties.name || 
           geo.properties.NAME_EN || 
           'Unknown Country';
  };

  const handleMouseEnter = (geo: GeoFeature) => {
    const countryName = getCountryName(geo);
    setHoveredCountry(countryName);
  };

  const handleMouseLeave = () => {
    setHoveredCountry('');
  };

  const handleClick = (geo: GeoFeature) => {
    const countryName = getCountryName(geo);
    setClickedCountry(countryName);
    alert(`You clicked on: ${countryName}`);
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Map Container */}
        <div className="relative bg-blue-50">
          <ComposableMap
            projection="geoMercator"
            projectionConfig={{
              scale: 130,
              center: [0, 20],
            }}
            width={1000}
            height={500}
            className="w-full h-auto"
          >
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo: GeoFeature) => {
                  const countryName = getCountryName(geo);
                  const isHovered = hoveredCountry === countryName;
                  
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      onMouseEnter={() => handleMouseEnter(geo)}
                      onMouseLeave={handleMouseLeave}
                      onClick={() => handleClick(geo)}
                      style={{
                        default: {
                          fill: isHovered ? '#3b82f6' : '#e5e7eb',
                          stroke: '#9ca3af',
                          strokeWidth: 0.5,
                          outline: 'none',
                          transition: 'all 0.2s ease-in-out',
                        },
                        hover: {
                          fill: '#3b82f6',
                          stroke: '#1d4ed8',
                          strokeWidth: 1,
                          outline: 'none',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease-in-out',
                        },
                        pressed: {
                          fill: '#1e40af',
                          stroke: '#1e3a8a',
                          strokeWidth: 1,
                          outline: 'none',
                        },
                      }}
                    />
                  );
                })
              }
            </Geographies>
          </ComposableMap>
        </div>

        {/* Country Display Section */}
        <div className="bg-gray-50 p-6 border-t">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Country Information
            </h3>
            <div className="min-h-[60px] flex items-center justify-center">
              {hoveredCountry ? (
                <div className="bg-white rounded-lg px-6 py-3 shadow-md border transform transition-all duration-200">
                  <p className="text-xl font-medium text-blue-600">
                    Currently hovering: <span className="font-bold text-blue-800">{hoveredCountry}</span>
                  </p>
                </div>
              ) : (
                <p className="text-gray-500 italic">
                  Hover over a country to see its name
                </p>
              )}
            </div>
            
            {clickedCountry && (
              <div className="mt-4 bg-blue-50 rounded-lg p-4 border border-blue-200 transform transition-all duration-200">
                <p className="text-sm text-blue-800">
                  Last clicked country: <span className="font-semibold">{clickedCountry}</span>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
        <h4 className="font-semibold text-gray-800 mb-2">How to use:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• <strong>Hover</strong> over any country to see it highlight and display its name below</li>
          <li>• <strong>Click</strong> on any country to see an alert with the country name</li>
          <li>• The map uses a 2D Mercator projection for accurate geographical representation</li>
          <li>• The map is fully responsive and works on all device sizes</li>
        </ul>
      </div>
    </div>
  );
};

export default WorldMap;
