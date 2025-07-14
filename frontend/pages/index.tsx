import { useState, useEffect } from 'react';

interface Protest {
  id: number;
  title: string;
  location: string;
  date: string;
  participants: string;
  status: 'ongoing' | 'ended' | 'planned';
}

const Home: React.FC = () => {
  const [recentProtests, setRecentProtests] = useState<Protest[]>([]);

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
    <div className="w-full h-full min-h-screen bg-secondary">
      {/* Hero Section */}
      <section className="flex items-center justify-center h-screen bg-primary">
        <img
          src="/assets/Earth.png"
          alt="Hero Map"
          className="w-[93%] h-auto"
        />
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