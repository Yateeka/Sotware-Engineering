import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface User {
    id: string;
    username: string;
    user_type: string;
    profile: {
        first_name: string;
        last_name: string;
    };
}

const SubmitReportPage = () => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitMessage, setSubmitMessage] = useState('');
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        location: {
            coordinates: [0, 0],
            description: ''
        },
        categories: [] as string[],
        urgency: 'medium',
        protestType: 'peaceful',
        estimatedParticipants: '',
        startDate: '',
        endDate: '',
        organizers: '',
        mediaUrls: ['']
    });

    const categories = [
        'Environmental',
        'Human Rights',
        'Labor Rights',
        'Racial Justice',
        'Gender Equality',
        'Economic Justice',
        'Political Reform',
        'Education',
        'Healthcare',
        'Climate Change',
        'Immigration',
        'LGBTQ+ Rights',
        'Criminal Justice Reform',
        'Anti-War',
        'Other'
    ];

    const urgencyLevels = [
        { value: 'low', label: 'Low', description: 'Standard reporting' },
        { value: 'medium', label: 'Medium', description: 'Moderate attention needed' },
        { value: 'high', label: 'High', description: 'Urgent - requires immediate attention' },
        { value: 'critical', label: 'Critical', description: 'Emergency situation' }
    ];

    const protestTypes = [
        { value: 'peaceful', label: 'Peaceful Demonstration' },
        { value: 'march', label: 'March/Parade' },
        { value: 'rally', label: 'Rally/Speech' },
        { value: 'sit_in', label: 'Sit-in' },
        { value: 'vigil', label: 'Vigil' },
        { value: 'strike', label: 'Strike' },
        { value: 'boycott', label: 'Boycott' },
        { value: 'occupation', label: 'Occupation' },
        { value: 'other', label: 'Other' }
    ];

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const userData = localStorage.getItem('user');
                if (!userData) {
                    router.push('/login');
                    return;
                }

                const parsedUser = JSON.parse(userData);
                
                // Check if user has permission to submit reports
                if (!['activist', 'ngo_worker', 'journalist', 'admin'].includes(parsedUser.user_type)) {
                    router.push('/dashboard');
                    return;
                }

                setUser(parsedUser);
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        
        if (name === 'locationDescription') {
            setFormData({
                ...formData,
                location: {
                    ...formData.location,
                    description: value
                }
            });
        } else {
            setFormData({
                ...formData,
                [name]: value
            });
        }
    };

    const handleCategoryChange = (category: string) => {
        const updatedCategories = formData.categories.includes(category)
            ? formData.categories.filter(c => c !== category)
            : [...formData.categories, category];
        
        setFormData({
            ...formData,
            categories: updatedCategories
        });
    };

    const handleMediaUrlChange = (index: number, value: string) => {
        const updatedUrls = [...formData.mediaUrls];
        updatedUrls[index] = value;
        setFormData({
            ...formData,
            mediaUrls: updatedUrls
        });
    };

    const addMediaUrl = () => {
        setFormData({
            ...formData,
            mediaUrls: [...formData.mediaUrls, '']
        });
    };

    const removeMediaUrl = (index: number) => {
        const updatedUrls = formData.mediaUrls.filter((_, i) => i !== index);
        setFormData({
            ...formData,
            mediaUrls: updatedUrls
        });
    };

    const getCurrentLocation = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    setFormData({
                        ...formData,
                        location: {
                            ...formData.location,
                            coordinates: [position.coords.longitude, position.coords.latitude]
                        }
                    });
                },
                (error) => {
                    console.error('Error getting location:', error);
                    alert('Unable to get current location. Please enter manually.');
                }
            );
        } else {
            alert('Geolocation is not supported by this browser.');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (formData.categories.length === 0) {
            setSubmitMessage('Please select at least one category.');
            return;
        }

        setIsSubmitting(true);
        setSubmitMessage('');

        try {
            const response = await fetch('http://localhost:5000/api/reports', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
                credentials: 'include'
            });

            const result = await response.json();

            if (response.ok) {
                setSubmitMessage('Report submitted successfully! Thank you for contributing to the platform.');
                // Reset form
                setFormData({
                    title: '',
                    description: '',
                    location: { coordinates: [0, 0], description: '' },
                    categories: [],
                    urgency: 'medium',
                    protestType: 'peaceful',
                    estimatedParticipants: '',
                    startDate: '',
                    endDate: '',
                    organizers: '',
                    mediaUrls: ['']
                });
                
                // Redirect to reports page after delay
                setTimeout(() => {
                    router.push('/my-reports');
                }, 2000);
            } else {
                setSubmitMessage(result.error || 'Failed to submit report. Please try again.');
            }
        } catch (error) {
            console.error('Submit error:', error);
            setSubmitMessage('Network error. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!user) {
        return null;
    }

    return (
        <>
            <Head>
                <title>Submit Report - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Submit Protest Report</h1>
                                <p className="text-gray-600">Document a protest or social movement</p>
                            </div>
                            <Link 
                                href="/dashboard"
                                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                            >
                                ← Back to Dashboard
                            </Link>
                        </div>
                    </div>
                </div>

                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {/* Info Banner */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                        <div className="flex items-start">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-blue-800">Report Guidelines</h3>
                                <div className="mt-2 text-sm text-blue-700">
                                    <ul className="list-disc list-inside space-y-1">
                                        <li>Provide accurate and verifiable information</li>
                                        <li>Include specific location details and timestamps</li>
                                        <li>Add multiple media sources when possible</li>
                                        <li>Reports are reviewed before publication</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Form */}
                    <div className="bg-white rounded-lg shadow">
                        <form onSubmit={handleSubmit} className="p-6 space-y-6">
                            {/* Basic Information */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="md:col-span-2">
                                        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                                            Protest Title *
                                        </label>
                                        <input
                                            type="text"
                                            id="title"
                                            name="title"
                                            required
                                            value={formData.title}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                            placeholder="e.g., Climate Action Rally for Clean Energy"
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="protestType" className="block text-sm font-medium text-gray-700 mb-1">
                                            Protest Type *
                                        </label>
                                        <select
                                            id="protestType"
                                            name="protestType"
                                            required
                                            value={formData.protestType}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                        >
                                            {protestTypes.map(type => (
                                                <option key={type.value} value={type.value}>
                                                    {type.label}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div>
                                        <label htmlFor="urgency" className="block text-sm font-medium text-gray-700 mb-1">
                                            Urgency Level *
                                        </label>
                                        <select
                                            id="urgency"
                                            name="urgency"
                                            required
                                            value={formData.urgency}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                        >
                                            {urgencyLevels.map(level => (
                                                <option key={level.value} value={level.value}>
                                                    {level.label} - {level.description}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div className="mt-6">
                                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                                        Description *
                                    </label>
                                    <textarea
                                        id="description"
                                        name="description"
                                        required
                                        rows={4}
                                        value={formData.description}
                                        onChange={handleInputChange}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                        placeholder="Provide detailed information about the protest, including context, demands, and current status..."
                                    />
                                </div>
                            </div>

                            {/* Categories */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Categories *</h3>
                                <p className="text-sm text-gray-600 mb-3">Select all relevant categories (at least one required)</p>
                                
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                    {categories.map(category => (
                                        <label
                                            key={category}
                                            className={`relative border rounded-lg p-3 cursor-pointer hover:border-primary ${
                                                formData.categories.includes(category) 
                                                    ? 'border-primary bg-primary/5' 
                                                    : 'border-gray-300'
                                            }`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={formData.categories.includes(category)}
                                                onChange={() => handleCategoryChange(category)}
                                                className="sr-only"
                                            />
                                            <div className="text-sm font-medium">{category}</div>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            {/* Location */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Location Information</h3>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="md:col-span-2">
                                        <label htmlFor="locationDescription" className="block text-sm font-medium text-gray-700 mb-1">
                                            Location Description *
                                        </label>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                id="locationDescription"
                                                name="locationDescription"
                                                required
                                                value={formData.location.description}
                                                onChange={handleInputChange}
                                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                placeholder="e.g., Centennial Olympic Park, Atlanta, GA"
                                            />
                                            <button
                                                type="button"
                                                onClick={getCurrentLocation}
                                                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                                            >
                                                📍 Use Current
                                            </button>
                                        </div>
                                        {formData.location.coordinates[0] !== 0 && (
                                            <p className="mt-1 text-xs text-green-600">
                                                ✓ GPS coordinates captured: {formData.location.coordinates[1].toFixed(4)}, {formData.location.coordinates[0].toFixed(4)}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Event Details */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Details</h3>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
                                            Start Date & Time
                                        </label>
                                        <input
                                            type="datetime-local"
                                            id="startDate"
                                            name="startDate"
                                            value={formData.startDate}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
                                            End Date & Time (if known)
                                        </label>
                                        <input
                                            type="datetime-local"
                                            id="endDate"
                                            name="endDate"
                                            value={formData.endDate}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="estimatedParticipants" className="block text-sm font-medium text-gray-700 mb-1">
                                            Estimated Participants
                                        </label>
                                        <input
                                            type="number"
                                            id="estimatedParticipants"
                                            name="estimatedParticipants"
                                            value={formData.estimatedParticipants}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                            placeholder="e.g., 500"
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="organizers" className="block text-sm font-medium text-gray-700 mb-1">
                                            Organizers (if known)
                                        </label>
                                        <input
                                            type="text"
                                            id="organizers"
                                            name="organizers"
                                            value={formData.organizers}
                                            onChange={handleInputChange}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                            placeholder="e.g., Climate Action Network"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Media URLs */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Media Sources (Optional)</h3>
                                <p className="text-sm text-gray-600 mb-3">Add links to photos, videos, news articles, or social media posts</p>
                                
                                {formData.mediaUrls.map((url, index) => (
                                    <div key={index} className="flex gap-2 mb-3">
                                        <input
                                            type="url"
                                            value={url}
                                            onChange={(e) => handleMediaUrlChange(index, e.target.value)}
                                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                            placeholder="https://example.com/photo.jpg or https://twitter.com/user/status/..."
                                        />
                                        {formData.mediaUrls.length > 1 && (
                                            <button
                                                type="button"
                                                onClick={() => removeMediaUrl(index)}
                                                className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                                            >
                                                ✕
                                            </button>
                                        )}
                                    </div>
                                ))}
                                
                                <button
                                    type="button"
                                    onClick={addMediaUrl}
                                    className="text-primary hover:text-primary/80 text-sm font-medium"
                                >
                                    + Add another media URL
                                </button>
                            </div>

                            {/* Submit Message */}
                            {submitMessage && (
                                <div className={`p-4 rounded-lg ${
                                    submitMessage.includes('successfully') || submitMessage.includes('Thank you')
                                        ? 'bg-green-50 text-green-700 border border-green-200' 
                                        : 'bg-red-50 text-red-700 border border-red-200'
                                }`}>
                                    {submitMessage}
                                </div>
                            )}

                            {/* Submit Button */}
                            <div className="flex justify-end gap-4 pt-6 border-t">
                                <Link
                                    href="/dashboard"
                                    className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                                >
                                    Cancel
                                </Link>
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSubmitting ? (
                                        <div className="flex items-center">
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            Submitting...
                                        </div>
                                    ) : (
                                        'Submit Report'
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </>
    );
};

export default SubmitReportPage;