import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

const RegisterPage = () => {
    const router = useRouter();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        firstName: '',
        lastName: '',
        userType: 'citizen',
        location: '',
        organization: ''
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const userTypes = [
        {
            id: 'citizen',
            name: 'Concerned Citizen',
            description: 'Stay informed about local and global movements',
            features: ['View protests', 'Bookmark events', 'Follow updates', 'Export basic data']
        },
        {
            id: 'activist',
            name: 'Activist',
            description: 'Organize and participate in social movements',
            features: ['Submit protest reports', 'Upload media', 'Coordinate actions', 'All citizen features']
        },
        {
            id: 'ngo_worker',
            name: 'NGO Worker',
            description: 'Advocate for causes and coordinate campaigns',
            features: ['Submit verified reports', 'Organizational tools', 'Campaign coordination', 'Enhanced visibility']
        },
        {
            id: 'journalist',
            name: 'Journalist',
            description: 'Cover social movements and access press features',
            features: ['Press credentials', 'Advanced data exports', 'Media upload rights', 'Priority verification']
        },
        {
            id: 'researcher',
            name: 'Academic Researcher',
            description: 'Study social movements with comprehensive data access',
            features: ['Bulk data exports', 'Historical analysis', 'Advanced analytics', 'Research partnerships']
        }
    ];

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        setError('');
        setSuccess('');
    };

    const validateForm = () => {
        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return false;
        }
        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters long');
            return false;
        }
        if (!formData.email.includes('@')) {
            setError('Please enter a valid email address');
            return false;
        }
        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateForm()) return;
        
        setIsLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:5000/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess('Registration successful! Please check your email to verify your account.');
                // Redirect to login after a delay
                setTimeout(() => {
                    router.push('/login');
                }, 2000);
            } else {
                setError(data.error || 'Registration failed');
            }
        } catch (error) {
            setError('Network error. Please try again.');
            console.error('Registration error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const selectedUserType = userTypes.find(type => type.id === formData.userType);

    return (
        <>
            <Head>
                <title>Register - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
                <div className="sm:mx-auto sm:w-full sm:max-w-md">
                    <div className="text-center">
                        <img
                            src="/logo/protest.svg"
                            alt="Global Protest Tracker"
                            className="mx-auto h-12 w-12"
                        />
                        <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                            Create your account
                        </h2>
                        <p className="mt-2 text-sm text-gray-600">
                            Or{' '}
                            <Link href="/login" className="font-medium text-primary hover:text-primary/80">
                                sign in to existing account
                            </Link>
                        </p>
                    </div>
                </div>

                <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-2xl">
                    <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                        <form className="space-y-6" onSubmit={handleSubmit}>
                            {/* User Type Selection */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-3">
                                    Account Type
                                </label>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {userTypes.map((type) => (
                                        <label
                                            key={type.id}
                                            className={`relative border rounded-lg p-4 cursor-pointer hover:border-primary ${
                                                formData.userType === type.id 
                                                    ? 'border-primary bg-primary/5' 
                                                    : 'border-gray-300'
                                            }`}
                                        >
                                            <input
                                                type="radio"
                                                name="userType"
                                                value={type.id}
                                                checked={formData.userType === type.id}
                                                onChange={handleInputChange}
                                                className="sr-only"
                                            />
                                            <div>
                                                <div className="font-medium text-sm">{type.name}</div>
                                                <div className="text-xs text-gray-500 mt-1">{type.description}</div>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                                
                                {/* Selected User Type Features */}
                                {selectedUserType && (
                                    <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                                        <h4 className="text-sm font-medium text-blue-900 mb-2">
                                            {selectedUserType.name} Features:
                                        </h4>
                                        <ul className="text-sm text-blue-700 space-y-1">
                                            {selectedUserType.features.map((feature, index) => (
                                                <li key={index} className="flex items-center">
                                                    <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                    </svg>
                                                    {feature}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>

                            {/* Personal Information */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">
                                        First Name
                                    </label>
                                    <input
                                        id="firstName"
                                        name="firstName"
                                        type="text"
                                        required
                                        value={formData.firstName}
                                        onChange={handleInputChange}
                                        className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                        placeholder="John"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">
                                        Last Name
                                    </label>
                                    <input
                                        id="lastName"
                                        name="lastName"
                                        type="text"
                                        required
                                        value={formData.lastName}
                                        onChange={handleInputChange}
                                        className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                        placeholder="Doe"
                                    />
                                </div>
                            </div>

                            {/* Account Information */}
                            <div>
                                <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                                    Username
                                </label>
                                <input
                                    id="username"
                                    name="username"
                                    type="text"
                                    required
                                    value={formData.username}
                                    onChange={handleInputChange}
                                    className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                    placeholder="johndoe123"
                                />
                            </div>

                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    required
                                    value={formData.email}
                                    onChange={handleInputChange}
                                    className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                    placeholder="john@example.com"
                                />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                        Password
                                    </label>
                                    <input
                                        id="password"
                                        name="password"
                                        type="password"
                                        required
                                        value={formData.password}
                                        onChange={handleInputChange}
                                        className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                        placeholder="••••••••"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                                        Confirm Password
                                    </label>
                                    <input
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        type="password"
                                        required
                                        value={formData.confirmPassword}
                                        onChange={handleInputChange}
                                        className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>

                            {/* Additional Information */}
                            <div>
                                <label htmlFor="location" className="block text-sm font-medium text-gray-700">
                                    Location
                                </label>
                                <input
                                    id="location"
                                    name="location"
                                    type="text"
                                    value={formData.location}
                                    onChange={handleInputChange}
                                    className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                    placeholder="Atlanta, GA (optional)"
                                />
                            </div>

                            {(formData.userType === 'ngo_worker' || formData.userType === 'journalist' || formData.userType === 'researcher') && (
                                <div>
                                    <label htmlFor="organization" className="block text-sm font-medium text-gray-700">
                                        Organization
                                    </label>
                                    <input
                                        id="organization"
                                        name="organization"
                                        type="text"
                                        value={formData.organization}
                                        onChange={handleInputChange}
                                        className="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                                        placeholder={
                                            formData.userType === 'journalist' ? 'News Organization' :
                                            formData.userType === 'researcher' ? 'University/Institution' :
                                            'NGO/Organization'
                                        }
                                    />
                                </div>
                            )}

                            {error && (
                                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                                    {error}
                                </div>
                            )}

                            {success && (
                                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
                                    {success}
                                </div>
                            )}

                            <div>
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? (
                                        <div className="flex items-center">
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            Creating account...
                                        </div>
                                    ) : (
                                        'Create Account'
                                    )}
                                </button>
                            </div>

                            <div className="text-xs text-gray-500">
                                By creating an account, you agree to our{' '}
                                <a href="#" className="text-primary hover:text-primary/80">Terms of Service</a>
                                {' '}and{' '}
                                <a href="#" className="text-primary hover:text-primary/80">Privacy Policy</a>.
                            </div>
                        </form>

                        {/* Back to Home */}
                        <div className="mt-6 text-center">
                            <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
                                ← Back to Home
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default RegisterPage;