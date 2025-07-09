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

  const getStatusColor = (status: Protest['status']) => {
    switch (status) {
      case 'ongoing':
        return 'bg-[#4a7c59] text-white';
      case 'ended':
        return 'bg-[#81a989] text-white';
      case 'planned':
        return 'bg-[#c8d5b9] text-[#4a7c59]';
      default:
        return 'bg-gray-200 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-[#c8d5b9]">
      {/* Hero Section */}
      <section className="py-20 px-8 bg-[#4a7c59]">
        <img src="/assets/Earth.png" alt="Hero Map" />
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div className="p-6">
              <div className="text-4xl font-bold mb-2 text-[#4a7c59]">1,247</div>
              <div className="text-gray-600">Total Events Tracked</div>
            </div>
            <div className="p-6">
              <div className="text-4xl font-bold mb-2 text-[#81a989]">89</div>
              <div className="text-gray-600">Countries Covered</div>
            </div>
            <div className="p-6">
              <div className="text-4xl font-bold mb-2 text-[#4a7c59]">23</div>
              <div className="text-gray-600">Active Today</div>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Protests */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold mb-8 text-center text-[#4a7c59]">Recent Protests</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {recentProtests.map((protest) => (
              <div
                key={protest.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-[#4a7c59]">{protest.title}</h3>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                      protest.status
                    )}`}
                  >
                    {protest.status}
                  </span>
                </div>
                <div className="space-y-2 text-gray-600">
                  <div className="flex items-center">
                    <span className="font-medium">Location:</span>
                    <span className="ml-2">{protest.location}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="font-medium">Date:</span>
                    <span className="ml-2">
                      {new Date(protest.date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span className="font-medium">Participants:</span>
                    <span className="ml-2">{protest.participants}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;