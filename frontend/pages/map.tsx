import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import Link from 'next/link';

// TypeScript declarations for global properties
declare global {
    interface Window {
        L: any;
        selectMarker?: (markerId: string) => void;
    }
}

interface MapMarker {
    id: string;
    title: string;
    coordinates: [number, number];
    city: string;
    state: string;
    country: string;
    categories: string[];
    status: 'planned' | 'ongoing' | 'completed';
    participant_count: number;
    start_date: string;
    featured: boolean;
    verification_status: string;
}

interface MapData {
    markers: MapMarker[];
    center: [number, number];
    zoom: number;
}

const MapPage = () => {
    const [mapData, setMapData] = useState<MapData | null>(null);
    const [selectedMarker, setSelectedMarker] = useState<MapMarker | null>(null);
    const [filters, setFilters] = useState({
        status: 'all',
        category: 'all',
        country: 'all'
    });
    const [isLoading, setIsLoading] = useState(true);
    const [showFilters, setShowFilters] = useState(false);
    const mapRef = useRef<any>(null);
    const mapInstanceRef = useRef<any>(null);
    const markersLayerRef = useRef<any>(null);

    // Load Leaflet dynamically to avoid SSR issues
    useEffect(() => {
        const loadLeaflet = async () => {
            if (typeof window !== 'undefined') {
                // Load Leaflet CSS
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css';
                document.head.appendChild(link);

                // Load Leaflet JS
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
                script.onload = () => {
                    initializeMap();
                };
                document.head.appendChild(script);
            }
        };

        loadLeaflet();
        fetchMapData();

        return () => {
            // Cleanup map on unmount
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
            }
        };
    }, []);

    const fetchMapData = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/protests/map-data');
            const data = await response.json();
            
            // The backend returns the data in the correct format already
            // Just need to make sure coordinates are in the right order for Leaflet
            const processedData = {
                ...data,
                markers: data.markers.map((marker: any) => ({
                    ...marker,
                    // Ensure coordinates are [lng, lat] for our component logic
                    coordinates: marker.coordinates
                }))
            };
            
            setMapData(processedData);
            console.log('Map data loaded:', processedData);
        } catch (error) {
            console.error('Failed to fetch map data:', error);
            // Fallback data for demo
            setMapData({
                markers: [
                    {
                        id: '1',
                        title: 'Atlanta Climate Action Rally',
                        coordinates: [-84.3880, 33.7490],
                        city: 'Atlanta',
                        state: 'Georgia',
                        country: 'United States',
                        categories: ['Environmental', 'Climate Change'],
                        status: 'planned',
                        participant_count: 450,
                        start_date: '2024-08-05T14:00:00',
                        featured: true,
                        verification_status: 'verified'
                    },
                    {
                        id: '2',
                        title: 'March for Public Education Funding',
                        coordinates: [-84.3963, 33.7490],
                        city: 'Atlanta',
                        state: 'Georgia',
                        country: 'United States',
                        categories: ['Education', 'Labor Rights'],
                        status: 'planned',
                        participant_count: 750,
                        start_date: '2024-08-17T10:00:00',
                        featured: true,
                        verification_status: 'verified'
                    },
                    {
                        id: '3',
                        title: 'Savannah Port Workers Strike',
                        coordinates: [-81.0912, 32.0835],
                        city: 'Savannah',
                        state: 'Georgia',
                        country: 'United States',
                        categories: ['Labor Rights'],
                        status: 'ongoing',
                        participant_count: 890,
                        start_date: '2024-07-25T06:00:00',
                        featured: true,
                        verification_status: 'verified'
                    },
                    {
                        id: '4',
                        title: 'NYC Housing Rights Rally',
                        coordinates: [-73.9903, 40.7359],
                        city: 'New York',
                        state: 'New York',
                        country: 'United States',
                        categories: ['Housing Rights'],
                        status: 'planned',
                        participant_count: 3200,
                        start_date: '2024-08-15T14:00:00',
                        featured: false,
                        verification_status: 'verified'
                    },
                    {
                        id: '5',
                        title: 'Los Angeles Climate March',
                        coordinates: [-118.2437, 34.0522],
                        city: 'Los Angeles',
                        state: 'California',
                        country: 'United States',
                        categories: ['Environmental'],
                        status: 'completed',
                        participant_count: 5600,
                        start_date: '2024-07-22T10:00:00',
                        featured: false,
                        verification_status: 'verified'
                    },
                    {
                        id: '6',
                        title: 'Washington DC Climate March',
                        coordinates: [-77.0369, 38.9072],
                        city: 'Washington',
                        state: 'District of Columbia',
                        country: 'United States',
                        categories: ['Environmental'],
                        status: 'planned',
                        participant_count: 15000,
                        start_date: '2024-08-25T14:00:00',
                        featured: true,
                        verification_status: 'verified'
                    }
                ],
                center: [-84.3880, 33.7490],
                zoom: 8
            });
        } finally {
            setIsLoading(false);
        }
    };

    const initializeMap = () => {
        if (typeof window !== 'undefined' && window.L && mapRef.current && !mapInstanceRef.current) {
            // Initialize the map
            mapInstanceRef.current = window.L.map(mapRef.current, {
                center: [33.7490, -84.3880], // Atlanta coordinates (lat, lng)
                zoom: 6,
                zoomControl: false // We'll add custom controls
            });

            // Add tile layer (OpenStreetMap)
            window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(mapInstanceRef.current);

            // Add custom zoom controls
            window.L.control.zoom({
                position: 'topright'
            }).addTo(mapInstanceRef.current);

            // Initialize markers layer
            markersLayerRef.current = window.L.layerGroup().addTo(mapInstanceRef.current);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ongoing':
                return '#10b981'; // green-500
            case 'planned':
                return '#3b82f6'; // blue-500
            case 'completed':
                return '#6b7280'; // gray-500
            default:
                return '#6b7280';
        }
    };

    const getMarkerSize = (participantCount: number) => {
        if (participantCount > 5000) return 20;
        if (participantCount > 1000) return 16;
        if (participantCount > 500) return 12;
        return 8;
    };

    const createCustomIcon = (marker: MapMarker) => {
        const size = getMarkerSize(marker.participant_count);
        const color = getStatusColor(marker.status);
        
        return window.L.divIcon({
            className: 'custom-marker',
            html: `
                <div style="
                    width: ${size}px;
                    height: ${size}px;
                    background-color: ${color};
                    border: 2px solid white;
                    border-radius: 50%;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    position: relative;
                    ${marker.status === 'ongoing' ? 'animation: pulse 2s infinite;' : ''}
                ">
                    ${marker.featured ? '<div style="position: absolute; top: -4px; right: -4px; width: 8px; height: 8px; background-color: #fbbf24; border: 1px solid white; border-radius: 50%;"></div>' : ''}
                </div>
                <style>
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); opacity: 1; }
                        50% { transform: scale(1.2); opacity: 0.7; }
                    }
                </style>
            `,
            iconSize: [size, size],
            iconAnchor: [size/2, size/2]
        });
    };

    const updateMarkers = () => {
        if (!mapInstanceRef.current || !markersLayerRef.current || !mapData) return;

        // Clear existing markers
        markersLayerRef.current.clearLayers();

        // Filter markers
        const filteredMarkers = mapData.markers.filter(marker => {
            if (filters.status !== 'all' && marker.status !== filters.status) return false;
            if (filters.category !== 'all' && !marker.categories.includes(filters.category)) return false;
            if (filters.country !== 'all' && marker.country !== filters.country) return false;
            return true;
        });

        // Add filtered markers to map
        filteredMarkers.forEach(marker => {
            const markerInstance = window.L.marker(
                [marker.coordinates[1], marker.coordinates[0]], // Leaflet uses [lat, lng]
                { icon: createCustomIcon(marker) }
            );

            // Create popup content
            const popupContent = `
                <div class="p-4 max-w-xs">
                    <h3 class="font-semibold text-gray-900 mb-2">${marker.title}</h3>
                    <div class="space-y-2 text-sm">
                        <div>
                            <span class="text-gray-500">Location:</span>
                            <span class="ml-1">${marker.city}, ${marker.state}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Status:</span>
                            <span class="ml-1 px-2 py-1 rounded text-xs text-white" style="background-color: ${getStatusColor(marker.status)}">${marker.status.toUpperCase()}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Participants:</span>
                            <span class="ml-1 font-semibold">${marker.participant_count.toLocaleString()}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Date:</span>
                            <span class="ml-1">${new Date(marker.start_date).toLocaleDateString()}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Categories:</span>
                            <div class="mt-1">
                                ${marker.categories.map(cat => `<span class="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mr-1">${cat}</span>`).join('')}
                            </div>
                        </div>
                    </div>
                    <button onclick="window.selectMarker('${marker.id}')" class="mt-3 w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 text-sm">
                        View Details
                    </button>
                </div>
            `;

            markerInstance.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'custom-popup'
            });

            markerInstance.on('click', () => {
                setSelectedMarker(marker);
            });

            markersLayerRef.current.addLayer(markerInstance);
        });
    };

    // Add global function for popup button clicks
    useEffect(() => {
        if (typeof window !== 'undefined') {
            window.selectMarker = (markerId: string) => {
                const marker = mapData?.markers.find(m => m.id === markerId);
                if (marker) {
                    setSelectedMarker(marker);
                }
            };
        }

        return () => {
            if (typeof window !== 'undefined') {
                delete window.selectMarker;
            }
        };
    }, [mapData]);

    // Update markers when data or filters change
    useEffect(() => {
        if (mapData && mapInstanceRef.current) {
            updateMarkers();
        }
    }, [mapData, filters]);

    const filteredMarkers = mapData?.markers.filter(marker => {
        if (filters.status !== 'all' && marker.status !== filters.status) return false;
        if (filters.category !== 'all' && !marker.categories.includes(filters.category)) return false;
        if (filters.country !== 'all' && marker.country !== filters.country) return false;
        return true;
    }) || [];

    const uniqueCategories = [...new Set(mapData?.markers.flatMap(m => m.categories) || [])];
    const uniqueCountries = [...new Set(mapData?.markers.map(m => m.country) || [])];

    const centerOnLocation = (lat: number, lng: number, zoom?: number) => {
        if (mapInstanceRef.current) {
            mapInstanceRef.current.setView([lat, lng], zoom || mapInstanceRef.current.getZoom());
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading interactive map...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>Interactive Protest Map - Global Protest Tracker</title>
                <meta name="description" content="Interactive map showing protests and social movements worldwide" />
            </Head>

            <div className="h-screen flex flex-col bg-gray-100">
                {/* Header */}
                <div className="bg-white shadow-sm border-b border-gray-200 px-4 py-3 z-10">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-xl font-semibold text-gray-900">Global Protest Map</h1>
                            <p className="text-sm text-gray-600">
                                {filteredMarkers.length} protests • Interactive Map
                            </p>
                        </div>
                        
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowFilters(!showFilters)}
                                className="flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                            >
                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.414A1 1 0 013 6.586V4z" />
                                </svg>
                                Filters {showFilters ? '↑' : '↓'}
                            </button>
                            
                            <Link 
                                href="/"
                                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                            >
                                ← Back to Home
                            </Link>
                        </div>
                    </div>

                    {/* Filters */}
                    {showFilters && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                                    <select
                                        value={filters.status}
                                        onChange={(e) => setFilters({...filters, status: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="all">All Statuses</option>
                                        <option value="planned">Planned</option>
                                        <option value="ongoing">Ongoing</option>
                                        <option value="completed">Completed</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                                    <select
                                        value={filters.category}
                                        onChange={(e) => setFilters({...filters, category: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="all">All Categories</option>
                                        {uniqueCategories.map(category => (
                                            <option key={category} value={category}>{category}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                                    <select
                                        value={filters.country}
                                        onChange={(e) => setFilters({...filters, country: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="all">All Countries</option>
                                        {uniqueCountries.map(country => (
                                            <option key={country} value={country}>{country}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="mt-3 flex justify-between items-center">
                                <span className="text-sm text-gray-600">
                                    Showing {filteredMarkers.length} of {mapData?.markers.length} protests
                                </span>
                                <button
                                    onClick={() => setFilters({status: 'all', category: 'all', country: 'all'})}
                                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                                >
                                    Clear all filters
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Map Container */}
                <div className="flex-1 relative">
                    <div 
                        ref={mapRef} 
                        className="w-full h-full"
                        style={{ minHeight: '400px' }}
                    />

                    {/* Quick Navigation */}
                    <div className="absolute bottom-4 right-4 flex gap-2 z-[1000]">
                        <button 
                            onClick={() => centerOnLocation(33.7490, -84.3880, 10)}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-700 text-sm font-medium transition-all duration-200 hover:shadow-xl"
                        >
                            📍 Atlanta
                        </button>
                        <button 
                            onClick={() => centerOnLocation(39.8283, -98.5795, 5)}
                            className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg shadow-lg hover:bg-gray-50 text-sm font-medium transition-all duration-200 hover:shadow-xl"
                        >
                            🇺🇸 USA
                        </button>
                        <button 
                            onClick={() => centerOnLocation(20, 0, 3)}
                            className="bg-gray-700 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-gray-800 text-sm font-medium transition-all duration-200 hover:shadow-xl"
                        >
                            🌍 World
                        </button>
                    </div>

                    {/* Legend */}
                    <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-xl p-4 max-w-xs z-[1000] border">
                        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                            <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                            Map Legend
                        </h3>
                        <div className="space-y-2">
                            <div className="flex items-center">
                                <div className="w-4 h-4 bg-blue-500 rounded-full mr-3 shadow-sm"></div>
                                <span className="text-xs text-gray-700 font-medium">Planned</span>
                            </div>
                            <div className="flex items-center">
                                <div className="w-4 h-4 bg-green-500 rounded-full mr-3 shadow-sm relative">
                                    <div className="absolute inset-0 rounded-full border border-green-400 animate-ping"></div>
                                </div>
                                <span className="text-xs text-gray-700 font-medium">Ongoing</span>
                            </div>
                            <div className="flex items-center">
                                <div className="w-4 h-4 bg-gray-500 rounded-full mr-3 shadow-sm"></div>
                                <span className="text-xs text-gray-700 font-medium">Completed</span>
                            </div>
                            <div className="border-t border-gray-200 pt-2 mt-2">
                                <div className="flex items-center mb-1">
                                    <div className="w-3 h-3 bg-yellow-400 rounded-full mr-3"></div>
                                    <span className="text-xs text-gray-600">Featured Event</span>
                                </div>
                                <div className="text-xs text-gray-500">
                                    • Click markers for details<br/>
                                    • Marker size = participants<br/>
                                    • Drag map to explore
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Selected Marker Details Panel */}
                    {selectedMarker && (
                        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-2xl p-6 max-w-sm z-[1000] border border-gray-200">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="text-lg font-semibold text-gray-900 pr-4 leading-tight">
                                    {selectedMarker.title}
                                </h3>
                                <button
                                    onClick={() => setSelectedMarker(null)}
                                    className="text-gray-400 hover:text-gray-600 flex-shrink-0 p-1 hover:bg-gray-100 rounded"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <span 
                                        className="inline-block px-3 py-1 rounded-full text-xs font-medium text-white"
                                        style={{ backgroundColor: getStatusColor(selectedMarker.status) }}
                                    >
                                        {selectedMarker.status.toUpperCase()}
                                    </span>
                                    {selectedMarker.featured && (
                                        <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                            ⭐ Featured
                                        </span>
                                    )}
                                </div>

                                <div className="grid grid-cols-1 gap-3">
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1 font-medium">📍 LOCATION</div>
                                        <div className="text-sm text-gray-900">
                                            {selectedMarker.city}, {selectedMarker.state}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {selectedMarker.coordinates[1].toFixed(4)}, {selectedMarker.coordinates[0].toFixed(4)}
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-xs text-gray-500 mb-1 font-medium">📅 DATE</div>
                                        <div className="text-sm text-gray-900">
                                            {new Date(selectedMarker.start_date).toLocaleDateString('en-US', {
                                                weekday: 'short',
                                                month: 'short',
                                                day: 'numeric',
                                                year: 'numeric'
                                            })}
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-xs text-gray-500 mb-1 font-medium">👥 PARTICIPANTS</div>
                                        <div className="text-sm font-semibold text-gray-900">
                                            {selectedMarker.participant_count.toLocaleString()}
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <div className="text-xs text-gray-500 mb-2 font-medium">🏷️ CATEGORIES</div>
                                    <div className="flex flex-wrap gap-1">
                                        {selectedMarker.categories.map((category) => (
                                            <span key={category} className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                                                {category}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <div className="text-xs text-gray-500 mb-1 font-medium">✅ VERIFICATION</div>
                                    <div className="flex items-center">
                                        {selectedMarker.verification_status === 'verified' ? (
                                            <>
                                                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                </svg>
                                                <span className="text-green-700 text-sm font-medium">Verified</span>
                                            </>
                                        ) : (
                                            <>
                                                <svg className="w-4 h-4 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                                </svg>
                                                <span className="text-yellow-700 text-sm font-medium">Pending Verification</span>
                                            </>
                                        )}
                                    </div>
                                </div>

                                <div className="pt-3 border-t border-gray-200">
                                    <Link 
                                        href={`/protest/${selectedMarker.id}`}
                                        className="block w-full bg-blue-600 text-white text-center py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                                    >
                                        View Full Details →
                                    </Link>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Bottom Stats Bar */}
                <div className="bg-white border-t border-gray-200 px-4 py-3 z-10">
                    <div className="flex justify-between items-center text-sm">
                        <div className="flex gap-6">
                            <div className="flex items-center">
                                <div className="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
                                <span className="text-gray-600">Total:</span>
                                <span className="font-semibold text-gray-900 ml-1">{mapData?.markers.length}</span>
                            </div>
                            <div className="flex items-center">
                                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                                <span className="text-gray-600">Active:</span>
                                <span className="font-semibold text-green-600 ml-1">
                                    {mapData?.markers.filter(m => m.status === 'ongoing').length}
                                </span>
                            </div>
                            <div className="flex items-center">
                                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                                <span className="text-gray-600">Planned:</span>
                                <span className="font-semibold text-blue-600 ml-1">
                                    {mapData?.markers.filter(m => m.status === 'planned').length}
                                </span>
                            </div>
                            <div className="flex items-center">
                                <div className="w-3 h-3 bg-yellow-400 rounded-full mr-2"></div>
                                <span className="text-gray-600">Featured:</span>
                                <span className="font-semibold text-yellow-600 ml-1">
                                    {mapData?.markers.filter(m => m.featured).length}
                                </span>
                            </div>
                        </div>

                        <div className="text-gray-500 text-xs">
                            🗺️ Interactive Map • 📍 Click markers for details • 🔍 Use filters to explore
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default MapPage;