'use client';
import React from 'react';
import Link from 'next/link';

const navItems = [
  { href: '/', label: 'Home', icon: '/nav/home.svg' },
  { href: '/search', label: 'Search', icon: '/nav/search.svg' },
  { href: '/feed', label: 'Explore', icon: '/nav/explore.svg' },
  { href: '/messages', label: 'Messages', icon: '/nav/message.svg' },
  { href: '/likes', label: 'Likes', icon: '/nav/heart.svg' },
  { href: '/create', label: 'Create', icon: '/nav/create.svg' },
  { href: '/profile', label: 'Profile', icon: '/nav/profile.svg', isProfile: true },
];

const Navigation = () => {
  const mainNavItems = navItems.filter(item => !item.isProfile);
  const profileItem = navItems.find(item => item.isProfile);

  return (
    <nav className="fixed left-0 top-0 w-20 bg-primary min-h-screen flex flex-col items-center py-6 shadow-lg z-40">
      {/* Logo */}
      <div className="mb-6">
        <img
          src="/logo/protest.svg"
          alt="Global Protest Tracker"
          className="w-8 h-8 object-contain invert"
        />
      </div>

      {/* Logo Divider */}
      <div className="w-8 h-px bg-white/20 mb-8"></div>

      {/* Main Navigation Links */}
      <div className="flex flex-col items-center justify-evenly flex-1 w-full">
        {mainNavItems.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className="relative group flex items-center justify-center w-12 h-12 hover:bg-secondary rounded-xl transition"
          >
            <div className={`${href === '/feed' ? 'w-8 h-8' : 'w-6 h-6'} flex items-center justify-center`}>
              <img
                src={icon}
                alt={label}
                className={`${href === '/feed' ? 'w-8 h-8' : 'w-6 h-6'} aspect-square object-contain object-center invert`}
                style={{ display: 'block' }}
              />
            </div>
            
            {/* Tooltip */}
            <span className="absolute left-24 whitespace-nowrap bg-black text-white text-xs px-3 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              {label}
            </span>
          </Link>
        ))}
      </div>

      {/* Divider */}
      <div className="w-8 h-px bg-white/20 mb-6"></div>

      {/* Profile Link */}
      {profileItem && (
        <div className="mb-4">
          <Link
            href={profileItem.href}
            className="relative group flex items-center justify-center w-12 h-12 hover:bg-secondary rounded-xl transition"
          >
            <div className="w-6 h-6 flex items-center justify-center">
              <img
                src={profileItem.icon}
                alt={profileItem.label}
                className="w-6 h-6 aspect-square object-contain object-center rounded-full bg-white p-1"
                style={{ display: 'block' }}
              />
            </div>
            
            {/* Tooltip */}
            <span className="absolute left-24 whitespace-nowrap bg-black text-white text-xs px-3 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              {profileItem.label}
            </span>
          </Link>
        </div>
      )}
    </nav>
  );
};

export default Navigation;