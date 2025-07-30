'use client';

import React, { useState } from 'react';
import {
  ComposableMap,
  Geographies,
  Geography,
  type GeoFeature,
} from 'react-simple-maps';

interface SimpleWorldMapProps {
  onCountryClick?: (countryName: string) => void;
  onCountryHover?: (countryName: string) => void;
  onCountryLeave?: () => void;
}

const SimpleWorldMap: React.FC<SimpleWorldMapProps> = ({ 
  onCountryClick, 
  onCountryHover, 
  onCountryLeave 
}) => {
  const [hoveredCountry, setHoveredCountry] = useState<string>('');

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
    if (onCountryHover) {
      onCountryHover(countryName);
    }
  };

  const handleMouseLeave = () => {
    setHoveredCountry('');
    if (onCountryLeave) {
      onCountryLeave();
    }
  };

  const handleClick = (geo: GeoFeature) => {
    const countryName = getCountryName(geo);
    if (onCountryClick) {
      onCountryClick(countryName);
    } else {
      alert(`You clicked on: ${countryName}`);
    }
  };

  return (
    <div className="relative w-full h-full">
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{
          scale: 140,
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
                      fill: isHovered ? '#4a7c59' : '#c8d5b9',
                      stroke: '#4a7c59',
                      strokeWidth: 0.5,
                      outline: 'none',
                      transition: 'all 0.2s ease-in-out',
                    },
                    hover: {
                      fill: '#4a7c59',
                      stroke: '#2d4a35',
                      strokeWidth: 1,
                      outline: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease-in-out',
                    },
                    pressed: {
                      fill: '#2d4a35',
                      stroke: '#1a2d21',
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
  );
};

export default SimpleWorldMap;
