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
        organization?: string;
    };
}

interface ExportJob {
    export_id: string;
    estimated_records: number;
    download_url: string;
    expires_at: string;
}

const ExportPage = () => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isExporting, setIsExporting] = useState(false);
    const [exportMessage, setExportMessage] = useState('');
    const [currentExport, setCurrentExport] = useState<ExportJob | null>(null);
    const [exportHistory, setExportHistory] = useState<ExportJob[]>([]);
    
    const [exportConfig, setExportConfig] = useState({
        type: 'protests',
        format: 'csv',
        date_range: '3months',
        custom_start_date: '',
        custom_end_date: '',
        categories: [] as string[],
        countries: [] as string[],
        status_filter: 'all',
        include_metadata: true,
        include_media_urls: true,
        include_user_data: false
    });

    const exportTypes = [
        { value: 'protests', label: 'Protest Data', description: 'Complete protest information, locations, and metadata' },
        { value: 'posts', label: 'User Posts', description: 'Social media posts and user-generated content' },
        { value: 'analytics', label: 'Analytics Summary', description: 'Aggregated statistics and trends' },
        { value: 'geographic', label: 'Geographic Data', description: 'Location-based protest distribution' },
        { value: 'temporal', label: 'Temporal Analysis', description: 'Time-series data for trend analysis' }
    ];

    const formats = [
        { value: 'csv', label: 'CSV', description: 'Comma-separated values (Excel compatible)' },
        { value: 'json', label: 'JSON', description: 'JavaScript Object Notation (developer friendly)' },
        { value: 'xlsx', label: 'Excel', description: 'Microsoft Excel format with multiple sheets' }
    ];

    const dateRanges = [
        { value: 'week', label: 'Last Week' },
        { value: 'month', label: 'Last Month' },
        { value: '3months', label: 'Last 3 Months' },
        { value: '6months', label: 'Last 6 Months' },
        { value: 'year', label: 'Last Year' },
        { value: 'all', label: 'All Time' },
        { value: 'custom', label: 'Custom Range' }
    ];

    const categories = [
        'Environmental', 'Human Rights', 'Labor Rights', 'Racial Justice',
        'Gender Equality', 'Economic Justice', 'Political Reform', 'Education',
        'Healthcare', 'Climate Change', 'Immigration', 'LGBTQ+ Rights',
        'Criminal Justice Reform', 'Anti-War'
    ];

    const countries = [
        'United States', 'Canada', 'United Kingdom', 'Germany', 'France',
        'Spain', 'Italy', 'Australia', 'Japan', 'South Korea', 'Brazil',
        'Mexico', 'India', 'South Africa', 'Nigeria'
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
                
                // Check if user has permission to export data
                if (!['researcher', 'journalist', 'admin'].includes(parsedUser.user_type)) {
                    router.push('/dashboard');
                    return;
                }

                setUser(parsedUser);
                
                // Load export history from localStorage for demo
                const history = localStorage.getItem('export_history');
                if (history) {
                    setExportHistory(JSON.parse(history));
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const handleConfigChange = (field: string, value: any) => {
        setExportConfig({
            ...exportConfig,
            [field]: value
        });
    };

    const handleArrayFieldChange = (field: 'categories' | 'countries', value: string) => {
        const currentArray = exportConfig[field];
        const updatedArray = currentArray.includes(value)
            ? currentArray.filter(item => item !== value)
            : [...currentArray, value];
        
        setExportConfig({
            ...exportConfig,
            [field]: updatedArray
        });
    };

    const handleExport = async () => {
        setIsExporting(true);
        setExportMessage('');

        try {
            const response = await fetch('http://localhost:5000/api/export/csv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(exportConfig),
                credentials: 'include'
            });

            const result = await response.json();

            if (response.ok) {
                setCurrentExport(result);
                setExportMessage('Export initiated successfully! Your download will be ready shortly.');
                
                // Add to history
                const newHistory = [result, ...exportHistory].slice(0, 10);
                setExportHistory(newHistory);
                localStorage.setItem('export_history', JSON.stringify(newHistory));
            } else {
                setExportMessage(result.error || 'Failed to initiate export. Please try again.');
            }
        } catch (error) {
            console.error('Export error:', error);
            setExportMessage('Network error. Please try again.');
        } finally {
            setIsExporting(false);
        }
    };

    const handleDownload = async (exportId: string) => {
        try {
            const response = await fetch(`http://localhost:5000/api/export/download/${exportId}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const csvContent = await response.text();
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `protest_data_${exportId}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                alert('Download failed. The export may have expired.');
            }
        } catch (error) {
            console.error('Download error:', error);
            alert('Download failed. Please try again.');
        }
    };

    const getEstimatedRecords = () => {
        // Mock estimation based on config
        let base = 150;
        if (exportConfig.type === 'posts') base = 450;
        if (exportConfig.date_range === 'week') base = Math.floor(base * 0.1);
        if (exportConfig.date_range === 'month') base = Math.floor(base * 0.3);
        if (exportConfig.categories.length > 0) base = Math.floor(base * 0.6);
        if (exportConfig.countries.length > 0) base = Math.floor(base * 0.4);
        return base;
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
                <title>Export Data - Global Protest Tracker</title>
            </Head>

            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="bg-white shadow">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Export Data</h1>
                                <p className="text-gray-600">Download protest data for research and analysis</p>
                            </div>
                            <div className="flex gap-3">
                                <Link 
                                    href="/analytics"
                                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                >
                                    📊 View Analytics
                                </Link>
                                <Link 
                                    href="/dashboard"
                                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                >
                                    ← Back to Dashboard
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Export Configuration */}
                        <div className="lg:col-span-2">
                            <div className="bg-white rounded-lg shadow">
                                <div className="p-6 border-b border-gray-200">
                                    <h3 className="text-lg font-semibold text-gray-900">Export Configuration</h3>
                                    <p className="text-sm text-gray-600">Configure your data export parameters</p>
                                </div>
                                
                                <div className="p-6 space-y-6">
                                    {/* Data Type Selection */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-3">
                                            Data Type *
                                        </label>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                            {exportTypes.map((type) => (
                                                <label
                                                    key={type.value}
                                                    className={`relative border rounded-lg p-4 cursor-pointer hover:border-primary ${
                                                        exportConfig.type === type.value 
                                                            ? 'border-primary bg-primary/5' 
                                                            : 'border-gray-300'
                                                    }`}
                                                >
                                                    <input
                                                        type="radio"
                                                        name="type"
                                                        value={type.value}
                                                        checked={exportConfig.type === type.value}
                                                        onChange={(e) => handleConfigChange('type', e.target.value)}
                                                        className="sr-only"
                                                    />
                                                    <div>
                                                        <div className="font-medium text-sm">{type.label}</div>
                                                        <div className="text-xs text-gray-500 mt-1">{type.description}</div>
                                                    </div>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Format Selection */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-3">
                                            Export Format *
                                        </label>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                            {formats.map((format) => (
                                                <label
                                                    key={format.value}
                                                    className={`relative border rounded-lg p-4 cursor-pointer hover:border-primary ${
                                                        exportConfig.format === format.value 
                                                            ? 'border-primary bg-primary/5' 
                                                            : 'border-gray-300'
                                                    }`}
                                                >
                                                    <input
                                                        type="radio"
                                                        name="format"
                                                        value={format.value}
                                                        checked={exportConfig.format === format.value}
                                                        onChange={(e) => handleConfigChange('format', e.target.value)}
                                                        className="sr-only"
                                                    />
                                                    <div>
                                                        <div className="font-medium text-sm">{format.label}</div>
                                                        <div className="text-xs text-gray-500 mt-1">{format.description}</div>
                                                    </div>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Date Range */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-3">
                                            Date Range *
                                        </label>
                                        <select
                                            value={exportConfig.date_range}
                                            onChange={(e) => handleConfigChange('date_range', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                        >
                                            {dateRanges.map(range => (
                                                <option key={range.value} value={range.value}>{range.label}</option>
                                            ))}
                                        </select>
                                        
                                        {exportConfig.date_range === 'custom' && (
                                            <div className="grid grid-cols-2 gap-4 mt-3">
                                                <div>
                                                    <label className="block text-xs text-gray-600 mb-1">Start Date</label>
                                                    <input
                                                        type="date"
                                                        value={exportConfig.custom_start_date}
                                                        onChange={(e) => handleConfigChange('custom_start_date', e.target.value)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs text-gray-600 mb-1">End Date</label>
                                                    <input
                                                        type="date"
                                                        value={exportConfig.custom_end_date}
                                                        onChange={(e) => handleConfigChange('custom_end_date', e.target.value)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Categories Filter */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-3">
                                            Categories (Optional)
                                        </label>
                                        <p className="text-xs text-gray-600 mb-3">Leave empty to include all categories</p>
                                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-40 overflow-y-auto">
                                            {categories.map(category => (
                                                <label
                                                    key={category}
                                                    className="flex items-center text-sm cursor-pointer hover:bg-gray-50 p-2 rounded"
                                                >
                                                    <input
                                                        type="checkbox"
                                                        checked={exportConfig.categories.includes(category)}
                                                        onChange={() => handleArrayFieldChange('categories', category)}
                                                        className="mr-2"
                                                    />
                                                    {category}
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Countries Filter */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-3">
                                            Countries (Optional)
                                        </label>
                                        <p className="text-xs text-gray-600 mb-3">Leave empty to include all countries</p>
                                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto">
                                            {countries.map(country => (
                                                <label
                                                    key={country}
                                                    className="flex items-center text-sm cursor-pointer hover:bg-gray-50 p-2 rounded"
                                                >
                                                    <input
                                                        type="checkbox"
                                                        checked={exportConfig.countries.includes(country)}
                                                        onChange={() => handleArrayFieldChange('countries', country)}
                                                        className="mr-2"
                                                    />
                                                    {country}
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Advanced Options */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-3">
                                            Advanced Options
                                        </label>
                                        <div className="space-y-3">
                                            <label className="flex items-center text-sm">
                                                <input
                                                    type="checkbox"
                                                    checked={exportConfig.include_metadata}
                                                    onChange={(e) => handleConfigChange('include_metadata', e.target.checked)}
                                                    className="mr-2"
                                                />
                                                Include metadata and source information
                                            </label>
                                            <label className="flex items-center text-sm">
                                                <input
                                                    type="checkbox"
                                                    checked={exportConfig.include_media_urls}
                                                    onChange={(e) => handleConfigChange('include_media_urls', e.target.checked)}
                                                    className="mr-2"
                                                />
                                                Include media URLs and attachments
                                            </label>
                                            {user.user_type === 'admin' && (
                                                <label className="flex items-center text-sm">
                                                    <input
                                                        type="checkbox"
                                                        checked={exportConfig.include_user_data}
                                                        onChange={(e) => handleConfigChange('include_user_data', e.target.checked)}
                                                        className="mr-2"
                                                    />
                                                    Include anonymized user data (Admin only)
                                                </label>
                                            )}
                                        </div>
                                    </div>

                                    {/* Export Message */}
                                    {exportMessage && (
                                        <div className={`p-4 rounded-lg ${
                                            exportMessage.includes('successfully') 
                                                ? 'bg-green-50 text-green-700 border border-green-200' 
                                                : 'bg-red-50 text-red-700 border border-red-200'
                                        }`}>
                                            {exportMessage}
                                        </div>
                                    )}

                                    {/* Current Export Status */}
                                    {currentExport && (
                                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                            <h4 className="font-medium text-blue-900 mb-2">Export Ready!</h4>
                                            <div className="text-sm text-blue-700 space-y-1">
                                                <div>Export ID: {currentExport.export_id}</div>
                                                <div>Records: {currentExport.estimated_records.toLocaleString()}</div>
                                                <div>Expires: {new Date(currentExport.expires_at).toLocaleString()}</div>
                                            </div>
                                            <button
                                                onClick={() => handleDownload(currentExport.export_id)}
                                                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                                            >
                                                📥 Download Now
                                            </button>
                                        </div>
                                    )}

                                    {/* Export Button */}
                                    <div className="flex justify-end">
                                        <button
                                            onClick={handleExport}
                                            disabled={isExporting}
                                            className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {isExporting ? (
                                                <div className="flex items-center">
                                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                    Preparing Export...
                                                </div>
                                            ) : (
                                                'Generate Export'
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Sidebar */}
                        <div className="lg:col-span-1 space-y-6">
                            {/* Export Preview */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Preview</h3>
                                
                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Data Type:</span>
                                        <span className="font-medium">{exportTypes.find(t => t.value === exportConfig.type)?.label}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Format:</span>
                                        <span className="font-medium">{exportConfig.format.toUpperCase()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Date Range:</span>
                                        <span className="font-medium">{dateRanges.find(r => r.value === exportConfig.date_range)?.label}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Categories:</span>
                                        <span className="font-medium">
                                            {exportConfig.categories.length === 0 ? 'All' : exportConfig.categories.length}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Countries:</span>
                                        <span className="font-medium">
                                            {exportConfig.countries.length === 0 ? 'All' : exportConfig.countries.length}
                                        </span>
                                    </div>
                                    <div className="pt-3 border-t border-gray-200">
                                        <div className="flex justify-between font-medium">
                                            <span className="text-gray-900">Estimated Records:</span>
                                            <span className="text-primary">{getEstimatedRecords().toLocaleString()}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Usage Guidelines */}
                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                                <h3 className="text-sm font-semibold text-yellow-900 mb-3">📋 Usage Guidelines</h3>
                                <ul className="text-xs text-yellow-800 space-y-2">
                                    <li>• Data is provided for research and journalistic purposes</li>
                                    <li>• Please cite "Global Protest Tracker" in publications</li>
                                    <li>• Respect privacy - no personal information included</li>
                                    <li>• Downloads expire after 24 hours</li>
                                    <li>• Maximum 5 exports per day per user</li>
                                </ul>
                            </div>

                            {/* Quick Export Presets */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Presets</h3>
                                <div className="space-y-2">
                                    <button
                                        onClick={() => setExportConfig({
                                            ...exportConfig,
                                            type: 'protests',
                                            date_range: 'month',
                                            categories: ['Climate Change', 'Environmental'],
                                            format: 'csv'
                                        })}
                                        className="w-full text-left p-3 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5"
                                    >
                                        <div className="font-medium text-sm">Climate Protests</div>
                                        <div className="text-xs text-gray-500">Last month's environmental protests</div>
                                    </button>
                                    
                                    <button
                                        onClick={() => setExportConfig({
                                            ...exportConfig,
                                            type: 'protests',
                                            date_range: '3months',
                                            countries: ['United States'],
                                            format: 'xlsx'
                                        })}
                                        className="w-full text-left p-3 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5"
                                    >
                                        <div className="font-medium text-sm">US Protests Q2</div>
                                        <div className="text-xs text-gray-500">3-month US protest data</div>
                                    </button>
                                    
                                    <button
                                        onClick={() => setExportConfig({
                                            ...exportConfig,
                                            type: 'analytics',
                                            date_range: 'year',
                                            format: 'json'
                                        })}
                                        className="w-full text-left p-3 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5"
                                    >
                                        <div className="font-medium text-sm">Annual Analytics</div>
                                        <div className="text-xs text-gray-500">Yearly trends and statistics</div>
                                    </button>
                                </div>
                            </div>

                            {/* Export History */}
                            {exportHistory.length > 0 && (
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Exports</h3>
                                    <div className="space-y-3">
                                        {exportHistory.slice(0, 5).map((export_item) => (
                                            <div key={export_item.export_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                                <div>
                                                    <div className="font-medium text-sm text-gray-900">
                                                        {export_item.export_id}
                                                    </div>
                                                    <div className="text-xs text-gray-500">
                                                        {export_item.estimated_records.toLocaleString()} records
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => handleDownload(export_item.export_id)}
                                                    className="text-primary hover:text-primary/80 text-sm font-medium"
                                                >
                                                    📥 Download
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Data Samples */}
                    <div className="mt-8 bg-white rounded-lg shadow">
                        <div className="p-6 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">Data Sample Preview</h3>
                            <p className="text-sm text-gray-600">Example of what your export will contain</p>
                        </div>
                        
                        <div className="p-6">
                            {exportConfig.type === 'protests' && (
                                <div className="overflow-x-auto">
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-3 py-2 text-left font-medium text-gray-900">Title</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-900">Location</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-900">Categories</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-900">Date</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-900">Participants</th>
                                                <th className="px-3 py-2 text-left font-medium text-gray-900">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            <tr>
                                                <td className="px-3 py-2 text-gray-900">Climate Action Rally</td>
                                                <td className="px-3 py-2 text-gray-600">Atlanta, GA</td>
                                                <td className="px-3 py-2 text-gray-600">Environmental</td>
                                                <td className="px-3 py-2 text-gray-600">2024-08-05</td>
                                                <td className="px-3 py-2 text-gray-600">450</td>
                                                <td className="px-3 py-2 text-gray-600">Planned</td>
                                            </tr>
                                            <tr>
                                                <td className="px-3 py-2 text-gray-900">Education Funding March</td>
                                                <td className="px-3 py-2 text-gray-600">Atlanta, GA</td>
                                                <td className="px-3 py-2 text-gray-600">Education</td>
                                                <td className="px-3 py-2 text-gray-600">2024-08-17</td>
                                                <td className="px-3 py-2 text-gray-600">750</td>
                                                <td className="px-3 py-2 text-gray-600">Planned</td>
                                            </tr>
                                            <tr>
                                                <td className="px-3 py-2 text-gray-500" colSpan={6}>
                                                    + {getEstimatedRecords() - 2} more records...
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {exportConfig.type === 'analytics' && (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <h4 className="font-medium text-gray-900 mb-2">Sample Analytics Data:</h4>
                                        <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto">
{`{
  "total_protests": 150,
  "active_protests": 12,
  "categories": {
    "Environmental": 18,
    "Labor Rights": 12,
    "Human Rights": 10
  },
  "geographic_distribution": [
    {
      "country": "United States",
      "protest_count": 45,
      "participant_count": 12500
    }
  ]
}`}
                                        </pre>
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-gray-900 mb-2">Includes:</h4>
                                        <ul className="text-sm text-gray-600 space-y-1">
                                            <li>• Global statistics and trends</li>
                                            <li>• Category breakdowns</li>
                                            <li>• Geographic distribution</li>
                                            <li>• Temporal analysis</li>
                                            <li>• Engagement metrics</li>
                                            <li>• Data quality indicators</li>
                                        </ul>
                                    </div>
                                </div>
                            )}

                            {exportConfig.type === 'geographic' && (
                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Geographic Data Sample:</h4>
                                    <div className="text-sm text-gray-600 space-y-2">
                                        <div>• Protest locations with precise coordinates</div>
                                        <div>• Country, state/region, and city breakdown</div>
                                        <div>• Population-adjusted protest density</div>
                                        <div>• Cross-border movement correlations</div>
                                        <div>• Geographic clustering analysis</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
                        <div className="flex items-start">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-blue-800">Data Ethics & Attribution</h3>
                                <div className="mt-2 text-sm text-blue-700">
                                    <p className="mb-2">
                                        This data is provided for research, journalistic, and educational purposes. 
                                        By downloading, you agree to:
                                    </p>
                                    <ul className="list-disc list-inside space-y-1">
                                        <li>Cite "Global Protest Tracker" as your data source</li>
                                        <li>Use data responsibly and ethically</li>
                                        <li>Respect privacy and anonymization measures</li>
                                        <li>Share findings that benefit social justice research</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default ExportPage;