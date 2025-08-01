'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

// Mock user context (replace with actual auth context)
interface User {
    id: string;
    username: string;
    user_type: string;
    profile: {
        first_name: string;
        last_name: string;
    };
}

// Mock hook for auth state
const useAuth = () => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Simulate checking auth state
        const checkAuth = async () => {
            try {
                // In real app, this would check session/token
                const userData = localStorage.getItem('user');
                if (userData) {
                    setUser(JSON.parse(userData));
                }
            } catch (error) {
                console.error('Auth check failed:', error);
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, []);

    return { user, isLoading, setUser };
};

const Navigation = () => {
    const router = useRouter();
    const { user, isLoading } = useAuth();
    const [isExpanded, setIsExpanded] = useState(false);

    // Base navigation items (always visible)
    const baseNavItems = [
        { href: '/', label: 'Home', icon: '/nav/home.svg' },
        { href: '/map', label: 'Map', icon: '/nav/explore.svg' }
    ];

    // Authentication items
    const authItems = user ? [
        { href: '/dashboard', label: 'Dashboard', icon: '/nav/dashboard.svg' },
        { href: '/search', label: 'Search', icon: '/nav/search.svg' }
    ] : [
        { href: '/login', label: 'Login', icon: '/nav/login.svg' },
        { href: '/register', label: 'Register', icon: '/nav/register.svg' }
    ];

    // User type specific navigation
    const getUserTypeItems = () => {
        if (!user) return [];

        const commonItems = [
            { href: '/profile', label: 'Profile', icon: '/nav/profile.svg' }
        ];

        switch (user.user_type) {
            case 'citizen':
                return [
                    { href: '/bookmarks', label: 'Bookmarks', icon: '/nav/bookmarks.svg' },
                    { href: '/follows', label: 'Following', icon: '/nav/follow.svg' },
                    ...commonItems
                ];

            case 'activist':
            case 'ngo_worker':
                return [
                    { href: '/submit-report', label: 'Submit Report', icon: '/nav/create.svg' },
                    { href: '/my-reports', label: 'My Reports', icon: '/nav/reports.svg' },
                    { href: '/bookmarks', label: 'Bookmarks', icon: '/nav/bookmarks.svg' },
                    ...commonItems
                ];

            case 'journalist':
            case 'researcher':
                return [
                    { href: '/analytics', label: 'Analytics', icon: '/nav/analytics.svg' },
                    { href: '/export', label: 'Export Data', icon: '/nav/export.svg' },
                    { href: '/bookmarks', label: 'Bookmarks', icon: '/nav/bookmarks.svg' },
                    ...commonItems
                ];

            case 'admin':
            case 'moderator':
                return [
                    { href: '/admin', label: 'Admin Panel', icon: '/nav/admin.svg' },
                    { href: '/analytics', label: 'Analytics', icon: '/nav/analytics.svg' },
                    { href: '/bookmarks', label: 'Bookmarks', icon: '/nav/bookmarks.svg' },
                    ...commonItems
                ];

            default:
                return commonItems;
        }
    };

    // Combine all navigation items
    const allNavItems = [
        ...baseNavItems,
        ...authItems,
        ...getUserTypeItems()
    ];

    const isActive = (href: string) => {
        if (href === '/') {
            return router.pathname === '/';
        }
        return router.pathname.startsWith(href);
    };

    const handleLogout = async () => {
        try {
            // Call logout API
            await fetch('/api/auth/logout', { method: 'POST' });
            
            // Clear local storage
            localStorage.removeItem('user');
            
            // Redirect to home
            router.push('/');
            
            // Reload to reset state
            window.location.reload();
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    if (isLoading) {
        return (
            <nav className="fixed left-0 top-0 w-20 bg-primary min-h-screen flex flex-col py-6 shadow-lg z-50">
                <div className="animate-pulse">
                    <div className="mb-6 px-6 flex items-center">
                        <div className="w-8 h-8 bg-white/20 rounded"></div>
                    </div>
                </div>
            </nav>
        );
    }

    return (
        <nav 
            className="fixed left-0 top-0 w-20 hover:w-56 bg-primary min-h-screen flex flex-col py-6 shadow-lg z-50 transition-all duration-300 ease-in-out group"
            onMouseEnter={() => setIsExpanded(true)}
            onMouseLeave={() => setIsExpanded(false)}
        >
            {/* Logo */}
            <div className="mb-6 px-6 flex items-center">
                <img
                    src="/logo/protest.svg"
                    alt="Global Protest Tracker"
                    className="w-8 h-8 object-contain invert flex-shrink-0"
                />
                <span className="ml-3 text-white font-semibold text-lg opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap overflow-hidden">
                    Protest Tracker
                </span>
            </div>

            {/* Logo Divider */}
            <div className="w-8 h-px bg-white/20 mb-8 mx-6 group-hover:w-44 transition-all duration-300"></div>

            {/* Main Navigation Links */}
            <div className="flex flex-col flex-1 w-full px-6 space-y-2">
                {allNavItems.map(({ href, label, icon }) => (
                    <Link
                        key={href}
                        href={href}
                        className={`flex items-center w-full h-12 rounded-xl transition-all duration-200 px-3 ${
                            isActive(href)
                                ? 'bg-secondary text-white'
                                : 'hover:bg-secondary/70 text-white/80 hover:text-white'
                        }`}
                    >
                        <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                            <img
                                src={icon}
                                alt={label}
                                className="w-6 h-6 aspect-square object-contain object-center invert"
                                style={{ display: 'block' }}
                            />
                        </div>
                        
                        {/* Text Label */}
                        <span className="ml-4 text-white font-medium opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap overflow-hidden">
                            {label}
                        </span>
                    </Link>
                ))}
            </div>

            {/* User Section */}
            {user && (
                <>
                    {/* Divider */}
                    <div className="w-8 h-px bg-white/20 mb-6 mx-6 group-hover:w-44 transition-all duration-300"></div>

                    {/* User Info */}
                    <div className="mb-4 px-6">
                        <div className="flex items-center w-full h-12 px-3">
                            <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                                <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center">
                                    <span className="text-primary text-xs font-bold">
                                        {user.profile.first_name?.[0] || user.username[0].toUpperCase()}
                                    </span>
                                </div>
                            </div>
                            
                            <div className="ml-4 opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap overflow-hidden">
                                <div className="text-white font-medium text-sm">
                                    {user.profile.first_name} {user.profile.last_name}
                                </div>
                                <div className="text-white/60 text-xs capitalize">
                                    {user.user_type.replace('_', ' ')}
                                </div>
                            </div>
                        </div>

                        {/* Logout Button */}
                        <button
                            onClick={handleLogout}
                            className="flex items-center w-full h-10 hover:bg-secondary/70 rounded-xl transition-all duration-200 px-3 mt-2"
                        >
                            <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                </svg>
                            </div>
                            
                            <span className="ml-4 text-white/80 font-medium text-sm opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap overflow-hidden">
                                Logout
                            </span>
                        </button>
                    </div>
                </>
            )}
        </nav>
    );
};

export default Navigation;