import { useState, useEffect } from 'react';

interface CreateFormData {
  type: 'protest' | 'event' | 'article' | 'post';
  title: string;
  description: string;
  location: string;
  date?: string;
  startTime?: string;
  endTime?: string;
  tags: string[];
  expectedParticipants?: string;
  contactInfo: string;
  imageUrl?: string;
  additionalDetails: string;
  isPublic: boolean;
  allowComments: boolean;
  sendNotifications: boolean;
}

interface ValidationErrors {
  [key: string]: string;
}

const Create: React.FC = () => {
  const [formData, setFormData] = useState<CreateFormData>({
    type: 'protest',
    title: '',
    description: '',
    location: '',
    date: '',
    startTime: '',
    endTime: '',
    tags: [],
    expectedParticipants: '',
    contactInfo: '',
    imageUrl: '',
    additionalDetails: '',
    isPublic: true,
    allowComments: true,
    sendNotifications: false
  });

  const [currentTag, setCurrentTag] = useState<string>('');
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [previewMode, setPreviewMode] = useState<boolean>(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState<boolean>(false);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'protest':
        return '✊';
      case 'event':
        return '📅';
      case 'article':
        return '📄';
      case 'post':
        return '💬';
      default:
        return '🔖';
    }
  };

  const getTypeDescription = (type: string) => {
    switch (type) {
      case 'protest':
        return 'Organize a peaceful demonstration or rally';
      case 'event':
        return 'Create a community event or gathering';
      case 'article':
        return 'Share an informative article or news piece';
      case 'post':
        return 'Make a general post or announcement';
      default:
        return '';
    }
  };

  const handleInputChange = (field: keyof CreateFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleAddTag = () => {
    if (currentTag.trim() && !formData.tags.includes(currentTag.trim().toLowerCase())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, currentTag.trim().toLowerCase()]
      }));
      setCurrentTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    }

    if ((formData.type === 'protest' || formData.type === 'event') && !formData.date) {
      newErrors.date = 'Date is required for protests and events';
    }

    if (!formData.contactInfo.trim()) {
      newErrors.contactInfo = 'Contact information is required';
    }

    if (formData.tags.length === 0) {
      newErrors.tags = 'At least one tag is required';
    }

    // Validate image URL format if provided
    if (formData.imageUrl && !isValidUrl(formData.imageUrl)) {
      newErrors.imageUrl = 'Please enter a valid image URL';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidUrl = (string: string): boolean => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Show success message
      setShowSuccessMessage(true);
      
      // Reset form after successful submission
      setTimeout(() => {
        setFormData({
          type: 'protest',
          title: '',
          description: '',
          location: '',
          date: '',
          startTime: '',
          endTime: '',
          tags: [],
          expectedParticipants: '',
          contactInfo: '',
          imageUrl: '',
          additionalDetails: '',
          isPublic: true,
          allowComments: true,
          sendNotifications: false
        });
        setShowSuccessMessage(false);
        setPreviewMode(false);
      }, 3000);
      
    } catch (error) {
      console.error('Error submitting form:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCurrentDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  return (
    <div className="min-h-screen bg-background" style={{ marginLeft: '16px' }}>
      {/* Header */}
      <div className="bg-primary shadow-sm">
        <div className="px-4 py-8">
          <h1 className="text-4xl font-bold text-white mb-2">Create Content</h1>
          <p className="text-white text-opacity-80">
            Share protests, events, articles, and posts with the community
          </p>
        </div>
      </div>

      {/* Success Message */}
      {showSuccessMessage && (
        <div className="px-4 py-4">
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">Success! Your content has been created and will be reviewed before publishing.</span>
          </div>
        </div>
      )}

      <div className="px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Content Type Selection */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold text-primary mb-4">What would you like to create?</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {(['protest', 'event', 'article', 'post'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => handleInputChange('type', type)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    formData.type === type
                      ? 'border-primary bg-secondary'
                      : 'border-gray-200 hover:border-primary hover:bg-gray-50'
                  }`}
                >
                  <div className="text-3xl mb-2">{getTypeIcon(type)}</div>
                  <h3 className="font-semibold text-primary capitalize mb-1">{type}</h3>
                  <p className="text-sm text-gray-600">{getTypeDescription(type)}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Main Form */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {/* Form Navigation */}
            <div className="bg-gray-50 px-6 py-4 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-primary">
                  {getTypeIcon(formData.type)} Create {formData.type.charAt(0).toUpperCase() + formData.type.slice(1)}
                </h2>
                <div className="flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={() => setPreviewMode(!previewMode)}
                    className="px-4 py-2 text-primary border border-primary rounded-lg hover:bg-primary hover:text-white transition-colors"
                  >
                    {previewMode ? '📝 Edit' : '👁️ Preview'}
                  </button>
                </div>
              </div>
            </div>

            {!previewMode ? (
              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                {/* Basic Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="lg:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Title *
                    </label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      placeholder={`Enter ${formData.type} title...`}
                      className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none ${
                        errors.title ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location *
                    </label>
                    <input
                      type="text"
                      value={formData.location}
                      onChange={(e) => handleInputChange('location', e.target.value)}
                      placeholder="Enter location..."
                      className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none ${
                        errors.location ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {errors.location && <p className="text-red-500 text-sm mt-1">{errors.location}</p>}
                  </div>

                  {(formData.type === 'protest' || formData.type === 'event') && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Date *
                      </label>
                      <input
                        type="date"
                        value={formData.date}
                        onChange={(e) => handleInputChange('date', e.target.value)}
                        min={getCurrentDate()}
                        className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none ${
                          errors.date ? 'border-red-500' : 'border-gray-300'
                        }`}
                      />
                      {errors.date && <p className="text-red-500 text-sm mt-1">{errors.date}</p>}
                    </div>
                  )}
                </div>

                {/* Time Fields for Events/Protests */}
                {(formData.type === 'protest' || formData.type === 'event') && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Start Time
                      </label>
                      <input
                        type="time"
                        value={formData.startTime}
                        onChange={(e) => handleInputChange('startTime', e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        End Time
                      </label>
                      <input
                        type="time"
                        value={formData.endTime}
                        onChange={(e) => handleInputChange('endTime', e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Expected Participants
                      </label>
                      <input
                        type="text"
                        value={formData.expectedParticipants}
                        onChange={(e) => handleInputChange('expectedParticipants', e.target.value)}
                        placeholder="e.g., 100+, 500-1000"
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                      />
                    </div>
                  </div>
                )}

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description *
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder={`Describe your ${formData.type} in detail...`}
                    rows={4}
                    className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-vertical ${
                      errors.description ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description}</p>}
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tags * (Press Enter to add)
                  </label>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {formData.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="bg-secondary text-primary px-3 py-1 rounded-full text-sm font-medium flex items-center"
                      >
                        #{tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-2 text-primary hover:text-red-500"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <input
                    type="text"
                    value={currentTag}
                    onChange={(e) => setCurrentTag(e.target.value)}
                    onKeyPress={handleTagKeyPress}
                    placeholder="Add tags (e.g., climate, activism, community)"
                    className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none ${
                      errors.tags ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.tags && <p className="text-red-500 text-sm mt-1">{errors.tags}</p>}
                </div>

                {/* Contact Information */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact Information *
                  </label>
                  <textarea
                    value={formData.contactInfo}
                    onChange={(e) => handleInputChange('contactInfo', e.target.value)}
                    placeholder="Provide contact details (email, phone, social media, etc.)"
                    rows={3}
                    className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-vertical ${
                      errors.contactInfo ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.contactInfo && <p className="text-red-500 text-sm mt-1">{errors.contactInfo}</p>}
                </div>

                {/* Image URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Image URL (optional)
                  </label>
                  <input
                    type="url"
                    value={formData.imageUrl}
                    onChange={(e) => handleInputChange('imageUrl', e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none ${
                      errors.imageUrl ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.imageUrl && <p className="text-red-500 text-sm mt-1">{errors.imageUrl}</p>}
                  {formData.imageUrl && isValidUrl(formData.imageUrl) && (
                    <div className="mt-3">
                      <img
                        src={formData.imageUrl}
                        alt="Preview"
                        className="max-w-xs max-h-32 object-cover rounded-lg border"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                </div>

                {/* Additional Details */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Additional Details (optional)
                  </label>
                  <textarea
                    value={formData.additionalDetails}
                    onChange={(e) => handleInputChange('additionalDetails', e.target.value)}
                    placeholder="Any additional information, requirements, or special instructions..."
                    rows={3}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-vertical"
                  />
                </div>

                {/* Settings */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-primary mb-4">Settings</h3>
                  <div className="space-y-4">
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={formData.isPublic}
                        onChange={(e) => handleInputChange('isPublic', e.target.checked)}
                        className="w-4 h-4 text-primary focus:ring-primary border-gray-300 rounded"
                      />
                      <span className="text-gray-700">Make this content public (visible to everyone)</span>
                    </label>
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={formData.allowComments}
                        onChange={(e) => handleInputChange('allowComments', e.target.checked)}
                        className="w-4 h-4 text-primary focus:ring-primary border-gray-300 rounded"
                      />
                      <span className="text-gray-700">Allow comments and discussions</span>
                    </label>
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={formData.sendNotifications}
                        onChange={(e) => handleInputChange('sendNotifications', e.target.checked)}
                        className="w-4 h-4 text-primary focus:ring-primary border-gray-300 rounded"
                      />
                      <span className="text-gray-700">Send me notifications about this content</span>
                    </label>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="border-t pt-6">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      * All content will be reviewed before being published
                    </p>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="bg-primary text-white px-8 py-3 rounded-lg hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Creating...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          Create {formData.type.charAt(0).toUpperCase() + formData.type.slice(1)}
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            ) : (
              /* Preview Mode */
              <div className="p-6">
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3 flex-1">
                      <span className="text-3xl">{getTypeIcon(formData.type)}</span>
                      <div className="flex-1">
                        <h3 className="text-2xl font-semibold text-primary mb-2">{formData.title || 'Untitled'}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            {formData.location || 'No location specified'}
                          </span>
                          {formData.date && (
                            <span className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {new Date(formData.date).toLocaleDateString()}
                            </span>
                          )}
                          {formData.expectedParticipants && (
                            <span className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                              </svg>
                              {formData.expectedParticipants}
                            </span>
                          )}
                        </div>
                        {(formData.startTime || formData.endTime) && (
                          <div className="text-sm text-gray-600 mb-2">
                            Time: {formData.startTime || 'TBD'} - {formData.endTime || 'TBD'}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {formData.imageUrl && isValidUrl(formData.imageUrl) && (
                    <div className="mb-4">
                      <img
                        src={formData.imageUrl}
                        alt="Content preview"
                        className="w-full max-h-64 object-cover rounded-lg"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                  )}

                  <p className="text-gray-700 mb-4 leading-relaxed">
                    {formData.description || 'No description provided'}
                  </p>

                  {formData.additionalDetails && (
                    <div className="mb-4 p-4 bg-white rounded border">
                      <h4 className="font-medium text-primary mb-2">Additional Details:</h4>
                      <p className="text-gray-700">{formData.additionalDetails}</p>
                    </div>
                  )}

                  <div className="mb-4 p-4 bg-white rounded border">
                    <h4 className="font-medium text-primary mb-2">Contact Information:</h4>
                    <p className="text-gray-700 whitespace-pre-line">{formData.contactInfo || 'No contact information provided'}</p>
                  </div>

                  <div className="flex flex-wrap items-center justify-between">
                    <div className="flex flex-wrap gap-2 mb-2 md:mb-0">
                      {formData.tags.length > 0 ? (
                        formData.tags.map((tag, index) => (
                          <span key={index} className="bg-secondary text-primary px-3 py-1 rounded-full text-sm font-medium">
                            #{tag}
                          </span>
                        ))
                      ) : (
                        <span className="text-gray-500 text-sm">No tags added</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{formData.isPublic ? '🌍 Public' : '🔒 Private'}</span>
                      <span>{formData.allowComments ? '💬 Comments allowed' : '🚫 No comments'}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Create;
