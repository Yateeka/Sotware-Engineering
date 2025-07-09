import Link from 'next/link';
import { useRouter } from 'next/router';

const Navigation: React.FC = () => {
  const router = useRouter();
  const isActive = (path: string) => router.pathname === path;

  const navLink = (href: string, label: string) => (
    <Link
      href={href}
      className={`text-white px-4 py-2 rounded transition-colors duration-200 ${
        isActive(href) ? 'bg-[#81a989]' : 'hover:bg-[#c8d5b9]'
      }`}
    >
      {label}
    </Link>
  );

  return (
    <nav className="fixed top-0 w-full z-50 px-4 py-3 bg-[#4a7c59]">
      <div className="flex items-center gap-8">
        <h1 className="text-white text-xl font-bold mr-auto">
          Global Protest Tracker
        </h1>
        {navLink('/', 'Home')}
        {navLink('/feed', 'Feed')}
        {navLink('/profile', 'Profile')}
      </div>
    </nav>
  );
};

export default Navigation;