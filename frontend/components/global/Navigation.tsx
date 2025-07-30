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
    <nav className="fixed left-0 top-0 w-20 hover:w-56 bg-primary min-h-screen flex flex-col py-6 shadow-lg z-50 transition-all duration-300 ease-in-out group">
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
      <div className="flex flex-col justify-evenly flex-1 w-full px-6 space-y-2">
        {mainNavItems.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center w-full h-12 hover:bg-secondary rounded-xl transition-all duration-200 px-3"
          >
            <div className={`${href === '/feed' ? 'w-8 h-8' : 'w-6 h-6'} flex items-center justify-center flex-shrink-0`}>
              <img
                src={icon}
                alt={label}
                className={`${href === '/feed' ? 'w-8 h-8' : 'w-6 h-6'} aspect-square object-contain object-center invert`}
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

      {/* Divider */}
      <div className="w-8 h-px bg-white/20 mb-6 mx-6 group-hover:w-44 transition-all duration-300"></div>

      {/* Profile Link */}
      {profileItem && (
        <div className="mb-4 px-6">
          <Link
            href={profileItem.href}
            className="flex items-center w-full h-12 hover:bg-secondary rounded-xl transition-all duration-200 px-3"
          >
            <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
              <img
                src={profileItem.icon}
                alt={profileItem.label}
                className="w-6 h-6 aspect-square object-contain object-center rounded-full bg-white p-1"
                style={{ display: 'block' }}
              />
            </div>
            
            {/* Text Label */}
            <span className="ml-4 text-white font-medium opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap overflow-hidden">
              {profileItem.label}
            </span>
          </Link>
        </div>
      )}
    </nav>
  );
};

export default Navigation;