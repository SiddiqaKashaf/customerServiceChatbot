# Frontend Integration Guide

This guide explains how to integrate your React frontend with the RAG chatbot backend.

## Backend Configuration

### Current Setup
- **Backend URL**: `http://localhost:5001` (or your deployed URL)
- **Main Endpoint**: `/api/chat`
- **CORS**: Enabled for all origins
- **Content-Type**: `application/json`

### Frontend Environment Variables

Update your frontend `.env` file:

```env
VITE_API_URL=http://localhost:5001/api
```

## API Integration

### Chat Request Format

Your frontend is already configured correctly. The backend expects:

```javascript
const response = await fetch(`${API_BASE_URL}/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: messageText,
    conversation_id: conversationId // optional
  })
});
```

### Response Format

The backend returns:

```javascript
{
  message_id: "unique-id",
  conversation_id: "conversation-id", 
  response: "AI response text",
  confidence: 0.85, // 0.0 to 1.0
  sources: [
    {
      title: "Document Title",
      similarity: 0.75,
      category: "products" // optional
    }
  ],
  context_used: true,
  timestamp: "2025-07-10T05:55:05.342875",
  suggested_responses: [
    "Follow-up question 1",
    "Follow-up question 2"
  ],
  intent: "products" // detected intent
}
```

## Frontend Enhancements

### 1. Display Confidence Levels

Update your confidence display logic:

```javascript
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'bg-green-500'
  if (confidence >= 0.6) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getConfidenceText = (confidence) => {
  if (confidence >= 0.8) return 'High'
  if (confidence >= 0.6) return 'Medium'
  return 'Low'
}
```

### 2. Show Sources

Add source information display:

```javascript
{message.sources && message.sources.length > 0 && (
  <div className="mt-2 text-xs text-gray-500">
    <span className="font-medium">Sources: </span>
    {message.sources.map((source, idx) => (
      <span key={idx} className="mr-2">
        {source.title} ({Math.round(source.similarity * 100)}%)
      </span>
    ))}
  </div>
)}
```

### 3. Enhanced Suggested Responses

The backend provides contextual suggestions:

```javascript
{suggestedResponses.length > 0 && (
  <div className="mt-4 flex flex-wrap gap-2">
    {suggestedResponses.map((suggestion, idx) => (
      <button
        key={idx}
        onClick={() => sendMessage(suggestion)}
        className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200"
      >
        {suggestion}
      </button>
    ))}
  </div>
)}
```

### 4. Intent-Based UI

Customize UI based on detected intent:

```javascript
const getIntentIcon = (intent) => {
  switch(intent) {
    case 'pricing': return '💰'
    case 'support': return '🛠️'
    case 'products': return '📦'
    case 'greeting': return '👋'
    case 'farewell': return '👋'
    default: return '💬'
  }
}
```

## Error Handling

### Backend Error Responses

```javascript
// Error response format
{
  error: "Error message",
  message: "User-friendly message"
}
```

### Frontend Error Handling

```javascript
try {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: messageText, conversation_id: conversationId })
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();
  
  if (data.error) {
    throw new Error(data.message || data.error);
  }

  // Handle successful response
  
} catch (error) {
  console.error('Chat error:', error);
  
  const errorMessage = {
    id: Date.now().toString(),
    role: 'assistant',
    content: "I apologize, but I'm having trouble connecting to the server. Please check your connection and try again.",
    timestamp: new Date().toISOString(),
    confidence: 0.0,
    sources: [],
    isError: true
  };
  
  setMessages(prev => [...prev, errorMessage]);
}
```

## Advanced Features

### 1. Document Upload

Add document upload functionality:

```javascript
const uploadDocuments = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  try {
    const response = await fetch(`${API_BASE_URL}/upload-documents`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    console.log('Upload result:', result);
  } catch (error) {
    console.error('Upload error:', error);
  }
};
```

### 2. Knowledge Base Status

Check knowledge base status:

```javascript
const getKnowledgeBaseStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/knowledge-base/status`);
    const status = await response.json();
    console.log('KB Status:', status);
  } catch (error) {
    console.error('Status error:', error);
  }
};
```

### 3. Conversation Analytics

Track conversation metrics:

```javascript
const trackConversationMetrics = (message, response) => {
  // Track user satisfaction, response time, etc.
  const metrics = {
    messageLength: message.length,
    responseTime: Date.now() - startTime,
    confidence: response.confidence,
    intent: response.intent,
    sourcesUsed: response.sources.length
  };
  
  // Send to analytics service
  console.log('Conversation metrics:', metrics);
};
```

## Testing Integration

### 1. Test Different Message Types

```javascript
const testMessages = [
  "Hello!", // Greeting
  "What services do you offer?", // Products
  "What are your pricing plans?", // Pricing  
  "How can I get support?", // Support
  "What's the weather like?", // Irrelevant
  "Goodbye!" // Farewell
];

// Test each message type
testMessages.forEach(async (message, index) => {
  setTimeout(async () => {
    console.log(`Testing: ${message}`);
    // Send message and log response
  }, index * 2000);
});
```

### 2. Test Conversation Flow

```javascript
const testConversationFlow = async () => {
  let conversationId = null;
  
  const messages = [
    "Hello!",
    "What services do you offer?", 
    "Tell me about pricing",
    "What's included in the Enterprise plan?",
    "Thank you!"
  ];
  
  for (const message of messages) {
    const response = await sendTestMessage(message, conversationId);
    conversationId = response.conversation_id;
    console.log(`Q: ${message}`);
    console.log(`A: ${response.response}`);
    console.log(`Confidence: ${response.confidence}`);
    console.log('---');
  }
};
```

## Performance Optimization

### 1. Request Debouncing

```javascript
import { debounce } from 'lodash';

const debouncedSendMessage = debounce(async (message) => {
  // Send message logic
}, 300);
```

### 2. Response Caching

```javascript
const responseCache = new Map();

const getCachedResponse = (message) => {
  const cacheKey = message.toLowerCase().trim();
  return responseCache.get(cacheKey);
};

const setCachedResponse = (message, response) => {
  const cacheKey = message.toLowerCase().trim();
  responseCache.set(cacheKey, response);
};
```

### 3. Loading States

```javascript
const [isLoading, setIsLoading] = useState(false);
const [typingIndicator, setTypingIndicator] = useState(false);

const sendMessage = async (messageText) => {
  setIsLoading(true);
  setTypingIndicator(true);
  
  try {
    // Send message
  } finally {
    setIsLoading(false);
    setTypingIndicator(false);
  }
};
```

## Deployment Considerations

### 1. Environment Configuration

```javascript
// config.js
export const API_CONFIG = {
  development: {
    baseURL: 'http://localhost:5001/api',
    timeout: 10000
  },
  production: {
    baseURL: 'https://your-backend-domain.com/api',
    timeout: 15000
  }
};

export const getApiConfig = () => {
  return API_CONFIG[process.env.NODE_ENV] || API_CONFIG.development;
};
```

### 2. CORS Configuration

Ensure your backend CORS settings match your frontend domain:

```python
# In your backend
CORS(app, origins=[
  "http://localhost:3000",  # Development
  "https://your-frontend-domain.com"  # Production
])
```

### 3. Health Checks

Add health check endpoint monitoring:

```javascript
const checkBackendHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
};
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Check backend CORS configuration
2. **Network Timeouts**: Increase timeout values
3. **Large Responses**: Implement response streaming
4. **Memory Issues**: Clear old conversation data

### Debug Mode

Enable debug logging:

```javascript
const DEBUG = process.env.NODE_ENV === 'development';

const debugLog = (message, data) => {
  if (DEBUG) {
    console.log(`[Chat Debug] ${message}:`, data);
  }
};
```

---

Your frontend is already well-structured and should work seamlessly with this backend. The main changes needed are updating the API URL to point to the backend server (port 5001) and optionally enhancing the UI to display the additional information provided by the backend (confidence, sources, intent, etc.).

