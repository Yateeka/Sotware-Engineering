import { useState, useEffect } from 'react';
import SimpleWorldMap from '../components/SimpleWorldMap';

interface Protest {
  id: number;
  title: string;
  location: string;
  date: string;
  participants: string;
  status: 'ongoing' | 'ended' | 'planned';
}

interface CountryInfo {
  name: string;
  population?: string;
  capital?: string;
  recentEvents?: string[];
  activeProtests?: number;
  lastUpdated?: string;
}

const Home: React.FC = () => {
  const [recentProtests, setRecentProtests] = useState<Protest[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<CountryInfo | null>(null);
  const [showCountryDialog, setShowCountryDialog] = useState(false);
  const [hoveredCountry, setHoveredCountry] = useState<string>('');

  // Sample country data - in a real app, this would come from an API
  const getCountryInfo = (countryName: string): CountryInfo => {
    const countryData: { [key: string]: CountryInfo } = {
      'United States of America': {
        name: 'United States',
        population: '331 million',
        capital: 'Washington, D.C.',
        recentEvents: ['Climate Action March in NYC', 'Workers Rights Rally in California'],
        activeProtests: 12,
        lastUpdated: '2 hours ago'
      },
      'Germany': {
        name: 'Germany',
        population: '83 million',
        capital: 'Berlin',
        recentEvents: ['Environmental Protest in Berlin', 'Student Demonstration in Munich'],
        activeProtests: 5,
        lastUpdated: '4 hours ago'
      },
      'United Kingdom': {
        name: 'United Kingdom',
        population: '67 million',
        capital: 'London',
        recentEvents: ['Anti-War Protest in London', 'Healthcare Workers Strike'],
        activeProtests: 8,
        lastUpdated: '1 hour ago'
      },
      'France': {
        name: 'France',
        population: '68 million',
        capital: 'Paris',
        recentEvents: ['General Strike in Paris', 'Student Protests in Lyon'],
        activeProtests: 15,
        lastUpdated: '30 minutes ago'
      },
      'Brazil': {
        name: 'Brazil',
        population: '215 million',
        capital: 'Brasília',
        recentEvents: ['Amazon Protection Rally', 'Indigenous Rights March'],
        activeProtests: 7,
        lastUpdated: '3 hours ago'
      }
    };

    return countryData[countryName] || {
      name: countryName,
      population: 'Data not available',
      capital: 'Unknown',
      recentEvents: ['No recent events tracked'],
      activeProtests: 0,
      lastUpdated: 'Never'
    };
  };

  const handleCountryClick = (countryName: string) => {
    const countryInfo = getCountryInfo(countryName);
    setSelectedCountry(countryInfo);
    setShowCountryDialog(true);
  };

  const handleCountryHover = (countryName: string) => {
    setHoveredCountry(countryName);
  };

  const handleCountryLeave = () => {
    setHoveredCountry('');
  };

  const closeDialog = () => {
    setShowCountryDialog(false);
    setSelectedCountry(null);
  };

  useEffect(() => {
    setRecentProtests([
      {
        id: 1,
        title: "Climate Action March",
        location: "New York, USA",
        date: "2024-03-15",
        participants: "10,000+",
        status: "ended"
      },
      {
        id: 2,
        title: "Workers Rights Demonstration",
        location: "Berlin, Germany",
        date: "2024-03-18",
        participants: "5,000+",
        status: "ongoing"
      },
      {
        id: 3,
        title: "Anti-War Protest",
        location: "London, UK",
        date: "2024-03-20",
        participants: "15,000+",
        status: "planned"
      }
    ]);
  }, []);
  useEffect(() => {
    setRecentProtests([
      {
        id: 1,
        title: "Climate Action March",
        location: "New York, USA",
        date: "2024-03-15",
        participants: "10,000+",
        status: "ended"
      },
      {
        id: 2,
        title: "Workers Rights Demonstration",
        location: "Berlin, Germany",
        date: "2024-03-18",
        participants: "5,000+",
        status: "ongoing"
      },
      {
        id: 3,
        title: "Anti-War Protest",
        location: "London, UK",
        date: "2024-03-20",
        participants: "15,000+",
        status: "planned"
      }
    ]);
  }, []);

  return (
    <div className="w-full h-full min-h-screen bg-secondary relative">
      {/* Country Information Dialog */}
      {showCountryDialog && selectedCountry && (
        <div className="fixed top-0 right-0 z-40 w-96 h-full bg-white shadow-2xl transform transition-transform duration-300 ease-in-out">
          <div className="p-6 h-full overflow-y-auto">
            {/* Dialog Header */}
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-primary">{selectedCountry.name}</h2>
              <button
                onClick={closeDialog}
                className="text-gray-500 hover:text-gray-700 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
              >
                ×
              </button>
            </div>

            {/* Country Basic Info */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Country Information</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Capital:</span>
                  <span className="font-medium">{selectedCountry.capital}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Population:</span>
                  <span className="font-medium">{selectedCountry.population}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Active Protests:</span>
                  <span className="font-medium text-primary">{selectedCountry.activeProtests}</span>
                </div>
              </div>
            </div>

            {/* Recent Events */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Recent Events</h3>
              <div className="space-y-3">
                {selectedCountry.recentEvents?.map((event, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-gray-800">{event}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Status Indicators */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Status</h3>
              <div className="flex items-center space-x-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${selectedCountry.activeProtests && selectedCountry.activeProtests > 0 ? 'bg-red-500' : 'bg-green-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {selectedCountry.activeProtests && selectedCountry.activeProtests > 0 ? 'Active Events' : 'No Active Events'}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                Last updated: {selectedCountry.lastUpdated}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full bg-primary text-white py-2 px-4 rounded-lg hover:bg-opacity-90 transition-colors text-sm">
                  View All Events
                </button>
                <button className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors text-sm">
                  Subscribe to Updates
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="flex items-center justify-center h-screen bg-primary relative">
        {/* Dynamic Title - Shows Global Tracker or Country Name */}
        <div className="absolute bottom-6 left-10 z-50 bg-white bg-opacity-90 px-6 py-3 rounded-lg shadow-md transition-all duration-300">
          {hoveredCountry ? (
            <div>
              <h1 className="text-primary font-bold text-xl tracking-wide">
                {hoveredCountry}
              </h1>
              <div className="text-xs text-primary text-opacity-70 mt-1">
                Click to view details
              </div>
            </div>
          ) : (
            <div>
              <h1 className="text-primary font-bold text-xl tracking-wide">
                Global Protest Tracker
              </h1>
              <div className="text-xs text-primary text-opacity-70 mt-1">
                Hover on a country to explore • Click for details
              </div>
            </div>
          )}
        </div>
        
        <div className="w-full h-auto">
          <SimpleWorldMap 
            onCountryClick={handleCountryClick}
            onCountryHover={handleCountryHover}
            onCountryLeave={handleCountryLeave}
          />
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div className="p-6">
              <div className="text-4xl font-bold mb-2 text-primary">1,247</div>
              <div className="text-gray-600">Total Events Tracked</div>
            </div>
            <div className="p-6">
              <div className="text-4xl font-bold mb-2 text-accent-light">89</div>
              <div className="text-gray-600">Countries Covered</div>
            </div>
            <div className="p-6">
              <div className="text-4xl font-bold mb-2 text-primary">23</div>
              <div className="text-gray-600">Active Today</div>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Protests */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold mb-8 text-center text-primary">Recent Protests</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-semibold text-primary">Climate Action March</h3>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-accent-light text-white">
                  ended
                </span>
              </div>
              <div className="space-y-2 text-gray-600">
                <div className="flex items-center">
                  <span className="font-medium">Location:</span>
                  <span className="ml-2">New York, USA</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Date:</span>
                  <span className="ml-2">
                    {new Date("2024-03-15").toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Participants:</span>
                  <span className="ml-2">10,000+</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-semibold text-primary">Workers Rights Demonstration</h3>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-primary text-white">
                  ongoing
                </span>
              </div>
              <div className="space-y-2 text-gray-600">
                <div className="flex items-center">
                  <span className="font-medium">Location:</span>
                  <span className="ml-2">Berlin, Germany</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Date:</span>
                  <span className="ml-2">
                    {new Date("2024-03-18").toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Participants:</span>
                  <span className="ml-2">5,000+</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-semibold text-primary">Anti-War Protest</h3>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-secondary text-primary">
                  planned
                </span>
              </div>
              <div className="space-y-2 text-gray-600">
                <div className="flex items-center">
                  <span className="font-medium">Location:</span>
                  <span className="ml-2">London, UK</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Date:</span>
                  <span className="ml-2">
                    {new Date("2024-03-20").toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Participants:</span>
                  <span className="ml-2">15,000+</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;