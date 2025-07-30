import { useState, useEffect } from 'react';

interface Message {
  id: number;
  senderId: number;
  receiverId: number;
  content: string;
  timestamp: string;
  isRead: boolean;
}

interface Contact {
  id: number;
  name: string;
  avatar: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  isOnline: boolean;
  role: 'organizer' | 'activist' | 'journalist' | 'citizen';
}

interface Conversation {
  contactId: number;
  messages: Message[];
}

const Messages: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [activeContact, setActiveContact] = useState<Contact | null>(null);
  const [conversations, setConversations] = useState<{ [key: number]: Message[] }>({});
  const [newMessage, setNewMessage] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Mock data - in a real app, this would come from an API
  const mockContacts: Contact[] = [
    {
      id: 1,
      name: 'Sarah Chen',
      avatar: '👩‍💼',
      lastMessage: 'The climate march organization is going well. We have 500+ confirmed attendees.',
      lastMessageTime: '2 minutes ago',
      unreadCount: 2,
      isOnline: true,
      role: 'organizer'
    },
    {
      id: 2,
      name: 'Marcus Johnson',
      avatar: '👨‍🎓',
      lastMessage: 'Thanks for sharing the protest guidelines. Very helpful!',
      lastMessageTime: '1 hour ago',
      unreadCount: 0,
      isOnline: true,
      role: 'activist'
    },
    {
      id: 3,
      name: 'Elena Rodriguez',
      avatar: '👩‍💻',
      lastMessage: 'I\'d like to interview some participants for my article.',
      lastMessageTime: '3 hours ago',
      unreadCount: 1,
      isOnline: false,
      role: 'journalist'
    },
    {
      id: 4,
      name: 'David Park',
      avatar: '👨‍🔬',
      lastMessage: 'The environmental data you requested is ready.',
      lastMessageTime: '1 day ago',
      unreadCount: 0,
      isOnline: false,
      role: 'activist'
    },
    {
      id: 5,
      name: 'Amara Okafor',
      avatar: '👩‍⚖️',
      lastMessage: 'Legal advice regarding peaceful assembly rights.',
      lastMessageTime: '2 days ago',
      unreadCount: 0,
      isOnline: true,
      role: 'organizer'
    }
  ];

  const mockConversations: { [key: number]: Message[] } = {
    1: [
      {
        id: 1,
        senderId: 1,
        receiverId: 0, // current user
        content: 'Hi! I\'m organizing the climate march next weekend. Are you interested in participating?',
        timestamp: '10:30 AM',
        isRead: true
      },
      {
        id: 2,
        senderId: 0,
        receiverId: 1,
        content: 'Absolutely! I\'ve been following environmental issues closely. What can I do to help?',
        timestamp: '10:35 AM',
        isRead: true
      },
      {
        id: 3,
        senderId: 1,
        receiverId: 0,
        content: 'Great! We need volunteers for registration and crowd management. Also, if you have social media experience, we could use help with promotion.',
        timestamp: '10:40 AM',
        isRead: true
      },
      {
        id: 4,
        senderId: 1,
        receiverId: 0,
        content: 'The climate march organization is going well. We have 500+ confirmed attendees.',
        timestamp: '2 minutes ago',
        isRead: false
      }
    ],
    2: [
      {
        id: 5,
        senderId: 0,
        receiverId: 2,
        content: 'Here are the protest guidelines we discussed. Please review them before the event.',
        timestamp: '9:15 AM',
        isRead: true
      },
      {
        id: 6,
        senderId: 2,
        receiverId: 0,
        content: 'Thanks for sharing the protest guidelines. Very helpful!',
        timestamp: '1 hour ago',
        isRead: true
      }
    ],
    3: [
      {
        id: 7,
        senderId: 3,
        receiverId: 0,
        content: 'I\'d like to interview some participants for my article.',
        timestamp: '3 hours ago',
        isRead: false
      }
    ]
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'organizer':
        return 'bg-primary text-white';
      case 'activist':
        return 'bg-secondary text-primary';
      case 'journalist':
        return 'bg-blue-100 text-blue-800';
      case 'citizen':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeContact) return;

    const message: Message = {
      id: Date.now(),
      senderId: 0, // current user
      receiverId: activeContact.id,
      content: newMessage.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isRead: false
    };

    setConversations(prev => ({
      ...prev,
      [activeContact.id]: [...(prev[activeContact.id] || []), message]
    }));

    setNewMessage('');
  };

  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    setContacts(mockContacts);
    setConversations(mockConversations);
    setActiveContact(mockContacts[0]);
  }, []);

  return (
    <div className="min-h-screen bg-background" style={{ marginLeft: '16px' }}>
      {/* Header */}
      <div className="bg-primary shadow-sm">
        <div className="px-4 py-8">
          <h1 className="text-4xl font-bold text-white mb-2">Messages</h1>
          <p className="text-white text-opacity-80">
            Connect with organizers, activists, and fellow participants
          </p>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex h-screen bg-background" style={{ height: 'calc(100vh - 140px)' }}>
        {/* Contacts Sidebar */}
        <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
          {/* Search Bar */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-3 mb-3">
              <h2 className="text-lg font-semibold text-gray-800 flex-1">Conversations</h2>
              <button className="bg-primary text-white p-2 rounded-full hover:bg-opacity-90 transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </button>
            </div>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Contacts List */}
          <div className="flex-1 overflow-y-auto">
            {filteredContacts.map((contact) => (
              <div
                key={contact.id}
                onClick={() => setActiveContact(contact)}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-secondary hover:bg-opacity-30 transition-colors ${
                  activeContact?.id === contact.id ? 'bg-secondary bg-opacity-50 border-l-4 border-l-primary' : ''
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="relative">
                    <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-xl">
                      {contact.avatar}
                    </div>
                    {contact.isOnline && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-white rounded-full"></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-semibold text-gray-900 truncate">{contact.name}</h3>
                      <div className="flex items-center space-x-2">
                        {contact.unreadCount > 0 && (
                          <span className="bg-primary text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
                            {contact.unreadCount}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">{contact.lastMessageTime}</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-600 truncate flex-1 mr-2">{contact.lastMessage}</p>
                      <span className={`text-xs px-2 py-1 rounded-full ${getRoleColor(contact.role)}`}>
                        {contact.role}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {activeContact ? (
            <>
              {/* Chat Header */}
              <div className="bg-white border-b border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-lg">
                        {activeContact.avatar}
                      </div>
                      {activeContact.isOnline && (
                        <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                      )}
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">{activeContact.name}</h2>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-1 rounded-full ${getRoleColor(activeContact.role)}`}>
                          {activeContact.role}
                        </span>
                        <span className="text-sm text-gray-500">
                          {activeContact.isOnline ? 'Online' : 'Offline'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                    </button>
                    <button className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {conversations[activeContact.id]?.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.senderId === 0 ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.senderId === 0
                          ? 'bg-primary text-white'
                          : 'bg-white text-gray-800 border'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <p className={`text-xs mt-1 ${
                        message.senderId === 0 ? 'text-white text-opacity-70' : 'text-gray-500'
                      }`}>
                        {message.timestamp}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Message Input */}
              <div className="bg-white border-t border-gray-200 p-4">
                <form onSubmit={handleSendMessage} className="flex space-x-3">
                  <button
                    type="button"
                    className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                  </button>
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Type your message..."
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={!newMessage.trim()}
                    className="flex-shrink-0 bg-primary text-white px-4 py-2 rounded-lg hover:bg-opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="text-6xl mb-4">💬</div>
                <h3 className="text-xl font-semibold text-gray-600 mb-2">Select a conversation</h3>
                <p className="text-gray-500">Choose someone to start messaging with</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Messages;
