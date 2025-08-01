import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface User {
    id: string;
    username: string;
    email: string;
    user_type: string;
    verified: boolean;
    email_verified: boolean;
    profile: {
        first_name: string;
        last_name: string;
        bio: string;
        location: string;
        organization?: string;
        preferred_language: string;
        timezone: string;
    };
    statistics: {
        login_count: number;
        reports_submitted: number;
        posts_created: number;
        bookmarks_count?: number;
        data_exports?: number;
        content_moderated?: number;
        protests_organized?: number;
    };
    created_at: string;
    last_login: string;
}

const ProfilePage = () => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [editData, setEditData] = useState({
        first_name: '',
        last_name: '',
        bio: '',
        location: '',
        organization: '',
        preferred_language: 'en',
        timezone: 'America/New_York'
    });
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState('');

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const userData = localStorage.getItem('user');
                if (!userData) {
                    router.push('/login');
                    return;
                }

                const parsedUser = JSON.parse(userData);
                
                // Fetch complete profile data
                const response = await fetch('http://localhost:5000/api/user/profile', {
                    credentials: 'include'
                });

                if (response.ok) {
                    const profileData = await response.json();
                    setUser(profileData);
                    setEditData(profileData.profile);
                } else {
                    // Fallback to localStorage data
                    setUser(parsedUser);
                    setEditData(parsedUser.profile || {});
                }
            } catch (error) {
                console.error('Failed to fetch profile:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const formatUserType = (userType: string) => {
        return userType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        setEditData({
            ...editData,
            [e.target.name]: e.target.value
        });
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveMessage('');

        try {
            const response = await fetch('http://localhost:5000/api/user/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ profile: editData }),
                credentials: 'include'
            });

            if (response.ok) {
                // Update user state
                if (user) {
                    const updatedUser = { ...user, profile: editData };
                    setUser(updatedUser);
                    localStorage.setItem('user', JSON.stringify(updatedUser));
                }
                setIsEditing(false);
                setSaveMessage('Profile updated successfully!');
                setTimeout(() => setSaveMessage(''), 3000);
            } else {
                setSaveMessage('Failed to update profile. Please try again.');
            }
        } catch (error) {
            console.error('Profile update failed:', error);
            setSaveMessage('Network error. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        if (user) {
            setEditData(user.profile);
        }
        setIsEditing(false);
        setSaveMessage('');
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
                <title>Profile - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
                                <p className="text-gray-600">Manage your account information and preferences</p>
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
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Profile Summary Card */}
                        <div className="lg:col-span-1">
                            <div className="bg-white rounded-lg shadow p-6">
                                <div className="text-center">
                                    {/* Avatar */}
                                    <div className="w-24 h-24 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
                                        <span className="text-2xl font-bold text-white">
                                            {user.profile.first_name?.[0] || user.username[0].toUpperCase()}
                                            {user.profile.last_name?.[0] || ''}
                                        </span>
                                    </div>

                                    <h2 className="text-xl font-semibold text-gray-900">
                                        {user.profile.first_name} {user.profile.last_name}
                                    </h2>
                                    <p className="text-gray-600">@{user.username}</p>
                                    
                                    <div className="mt-2 flex items-center justify-center gap-2">
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                            {formatUserType(user.user_type)}
                                        </span>
                                        {user.verified && (
                                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                ✓ Verified
                                            </span>
                                        )}
                                    </div>

                                    {user.profile.bio && (
                                        <p className="mt-4 text-sm text-gray-600 italic">
                                            "{user.profile.bio}"
                                        </p>
                                    )}

                                    <div className="mt-4 text-sm text-gray-500">
                                        <div>📍 {user.profile.location}</div>
                                        {user.profile.organization && (
                                            <div>🏢 {user.profile.organization}</div>
                                        )}
                                        <div>📅 Member since {new Date(user.created_at).toLocaleDateString()}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Activity Stats */}
                            <div className="bg-white rounded-lg shadow p-6 mt-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Stats</h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Total Logins</span>
                                        <span className="font-semibold">{user.statistics.login_count}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Posts Created</span>
                                        <span className="font-semibold">{user.statistics.posts_created}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Reports Submitted</span>
                                        <span className="font-semibold">{user.statistics.reports_submitted}</span>
                                    </div>
                                    {user.statistics.bookmarks_count !== undefined && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Bookmarks</span>
                                            <span className="font-semibold">{user.statistics.bookmarks_count}</span>
                                        </div>
                                    )}
                                    {user.statistics.data_exports !== undefined && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Data Exports</span>
                                            <span className="font-semibold">{user.statistics.data_exports}</span>
                                        </div>
                                    )}
                                    {user.statistics.content_moderated !== undefined && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Content Moderated</span>
                                            <span className="font-semibold">{user.statistics.content_moderated}</span>
                                        </div>
                                    )}
                                    {user.statistics.protests_organized !== undefined && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Protests Organized</span>
                                            <span className="font-semibold">{user.statistics.protests_organized}</span>
                                        </div>
                                    )}
                                </div>

                                <div className="mt-4 pt-4 border-t border-gray-200">
                                    <div className="text-xs text-gray-500">
                                        Last login: {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Profile Form */}
                        <div className="lg:col-span-2">
                            <div className="bg-white rounded-lg shadow">
                                {/* Form Header */}
                                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                                    <h3 className="text-lg font-semibold text-gray-900">Profile Information</h3>
                                    {!isEditing ? (
                                        <button
                                            onClick={() => setIsEditing(true)}
                                            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                                        >
                                            Edit Profile
                                        </button>
                                    ) : (
                                        <div className="flex gap-2">
                                            <button
                                                onClick={handleCancel}
                                                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                onClick={handleSave}
                                                disabled={isSaving}
                                                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
                                            >
                                                {isSaving ? 'Saving...' : 'Save Changes'}
                                            </button>
                                        </div>
                                    )}
                                </div>

                                {/* Success/Error Message */}
                                {saveMessage && (
                                    <div className={`mx-6 mt-4 p-3 rounded-lg ${
                                        saveMessage.includes('successfully') 
                                            ? 'bg-green-50 text-green-700 border border-green-200' 
                                            : 'bg-red-50 text-red-700 border border-red-200'
                                    }`}>
                                        {saveMessage}
                                    </div>
                                )}

                                {/* Form Content */}
                                <div className="p-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* First Name */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                First Name
                                            </label>
                                            {isEditing ? (
                                                <input
                                                    type="text"
                                                    name="first_name"
                                                    value={editData.first_name}
                                                    onChange={handleInputChange}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                />
                                            ) : (
                                                <div className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                                                    {user.profile.first_name || 'Not set'}
                                                </div>
                                            )}
                                        </div>

                                        {/* Last Name */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Last Name
                                            </label>
                                            {isEditing ? (
                                                <input
                                                    type="text"
                                                    name="last_name"
                                                    value={editData.last_name}
                                                    onChange={handleInputChange}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                />
                                            ) : (
                                                <div className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                                                    {user.profile.last_name || 'Not set'}
                                                </div>
                                            )}
                                        </div>

                                        {/* Username (Read-only) */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Username
                                            </label>
                                            <div className="w-full px-3 py-2 bg-gray-100 border border-gray-200 rounded-lg text-gray-500">
                                                {user.username} (cannot be changed)
                                            </div>
                                        </div>

                                        {/* Email (Read-only) */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Email
                                            </label>
                                            <div className="w-full px-3 py-2 bg-gray-100 border border-gray-200 rounded-lg text-gray-500 flex items-center justify-between">
                                                <span>{user.email}</span>
                                                {user.email_verified && (
                                                    <span className="text-green-600 text-sm">✓ Verified</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Location */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Location
                                            </label>
                                            {isEditing ? (
                                                <input
                                                    type="text"
                                                    name="location"
                                                    value={editData.location}
                                                    onChange={handleInputChange}
                                                    placeholder="City, State, Country"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                />
                                            ) : (
                                                <div className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                                                    {user.profile.location || 'Not set'}
                                                </div>
                                            )}
                                        </div>

                                        {/* Organization */}
                                        {(user.user_type === 'journalist' || user.user_type === 'researcher' || user.user_type === 'ngo_worker') && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Organization
                                                </label>
                                                {isEditing ? (
                                                    <input
                                                        type="text"
                                                        name="organization"
                                                        value={editData.organization || ''}
                                                        onChange={handleInputChange}
                                                        placeholder="Your organization"
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                    />
                                                ) : (
                                                    <div className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                                                        {user.profile.organization || 'Not set'}
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* Language */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Preferred Language
                                            </label>
                                            {isEditing ? (
                                                <select
                                                    name="preferred_language"
                                                    value={editData.preferred_language}
                                                    onChange={handleInputChange}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                >
                                                    <option value="en">English</option>
                                                    <option value="es">Español</option>
                                                    <option value="fr">Français</option>
                                                    <option value="de">Deutsch</option>
                                                    <option value="zh">中文</option>
                                                </select>
                                            ) : (
                                                <div className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                                                    {user.profile.preferred_language === 'en' ? 'English' : user.profile.preferred_language}
                                                </div>
                                            )}
                                        </div>

                                        {/* Timezone */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Timezone
                                            </label>
                                            {isEditing ? (
                                                <select
                                                    name="timezone"
                                                    value={editData.timezone}
                                                    onChange={handleInputChange}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                >
                                                    <option value="America/New_York">Eastern Time</option>
                                                    <option value="America/Chicago">Central Time</option>
                                                    <option value="America/Denver">Mountain Time</option>
                                                    <option value="America/Los_Angeles">Pacific Time</option>
                                                    <option value="UTC">UTC</option>
                                                </select>
                                            ) : (
                                                <div className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                                                    {user.profile.timezone}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Bio */}
                                    <div className="mt-6">
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Bio
                                        </label>
                                        {isEditing ? (
                                            <textarea
                                                name="bio"
                                                value={editData.bio}
                                                onChange={handleInputChange}
                                                rows={4}
                                                placeholder="Tell us about yourself..."
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                            />
                                        ) : (
                                            <div className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900 min-h-[100px]">
                                                {user.profile.bio || 'No bio provided'}
                                            </div>
                                        )}
                                    </div>

                                    {/* Account Type Info */}
                                    <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                                        <h4 className="text-sm font-semibold text-blue-900 mb-2">Account Type: {formatUserType(user.user_type)}</h4>
                                        <p className="text-sm text-blue-700">
                                            {user.user_type === 'citizen' && 'You can view protests, bookmark events, and follow updates.'}
                                            {user.user_type === 'activist' && 'You can submit reports, organize protests, and coordinate actions.'}
                                            {user.user_type === 'ngo_worker' && 'You can submit verified reports and use organizational tools.'}
                                            {user.user_type === 'journalist' && 'You have press credentials and advanced data export capabilities.'}
                                            {user.user_type === 'researcher' && 'You have access to bulk data exports and advanced analytics.'}
                                            {user.user_type === 'admin' && 'You have full system access and moderation capabilities.'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default ProfilePage;