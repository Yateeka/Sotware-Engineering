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
  return (
    <nav className="fixed left-0 top-0 w-20 bg-primary min-h-screen flex flex-col items-center py-6 shadow-lg z-40">
      {/* Logo */}
      <div className="mb-10">
        <img
          src="/logo/protest.svg"
          alt="Global Protest Tracker"
          className="w-8 h-8 object-contain invert"
        />
      </div>

      {/* Navigation Links */}
      <div className="flex flex-col items-center gap-8 w-full">
        {navItems.map(({ href, label, icon, isProfile }) => (
          <Link
            key={href}
            href={href}
            className="relative group flex items-center justify-center w-12 h-12 hover:bg-secondary rounded-xl transition"
          >
            <div className="w-6 h-6 flex items-center justify-center">
              <img
                src={icon}
                alt={label}
                className={`w-6 h-6 aspect-square object-contain object-center ${isProfile ? 'rounded-full bg-white p-1' : 'invert'
                  }`}
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
    </nav>
  );
};

export default Navigation;