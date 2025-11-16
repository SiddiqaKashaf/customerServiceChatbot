import { useState, useRef, useEffect, useCallback, memo } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import {
  Send,
  Bot,
  User,
  MessageCircle,
  Sparkles,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Copy,
  RotateCcw,
  Mic,
  Paperclip
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Memoized Message Component
const Message = memo(({ message, copyMessage }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`group flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`relative flex flex-col max-w-[85%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
        <div className={`flex items-end gap-3`}>
          {message.role === 'assistant' && (
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center shadow-lg">
              <Bot className="h-5 w-5 text-white" />
            </div>
          )}
          <div
            className={`relative rounded-2xl border transition-all duration-300 px-5 py-3 text-sm font-normal whitespace-pre-line break-words shadow-lg ${message.role === 'user'
              ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white border-indigo-400/30'
              : message.isError
                ? 'bg-red-50/90 text-red-900 border-red-200/50'
                : 'bg-white/95 text-gray-800 border-gray-200/50 backdrop-blur-sm'
              } group-hover:shadow-xl`}
            tabIndex={0}
            aria-label={message.role === 'user' ? 'Your message' : 'Bot message'}
          >
            <div className="block text-sm leading-relaxed">
              <div className="prose prose-sm max-w-none text-inherit">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            </div>
            <div className="absolute -bottom-8 right-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-7 w-7 p-0 hover:bg-indigo-50 active:scale-95 rounded-full" 
                aria-label="Copy message" 
                onClick={() => copyMessage(message.content)}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
        <span className="text-xs text-gray-400 mt-2 ml-12">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </span>
      </div>
    </motion.div>
  )
});

// Typing Indicator Component
const TypingIndicator = () => (
  <div className="flex items-center gap-3 mt-2">
    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center shadow-lg">
      <Bot className="h-5 w-5 text-white" />
    </div>
    <div className="flex items-center gap-1 bg-white/90 rounded-2xl px-4 py-2 shadow-lg">
      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
      <span className="text-xs text-gray-600 ml-3 font-medium">Thinking...</span>
    </div>
  </div>
);

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [suggestedResponses, setSuggestedResponses] = useState([])
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Initial suggestion messages
  const initialSuggestions = [
    "What are your pricing plans?",
    "How can I contact you?",
    "Tell me about your tech services",
    "What are your payment terms?"
  ]

  // Optimized scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Initialize chat
  useEffect(() => {
    const welcomeMessage = {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI customer service assistant. I'm here to help you with any questions about our products, services, pricing, or technical support. How can I assist you today?",
      timestamp: new Date().toISOString(),
      confidence: 1.0,
      sources: []
    };
    
    setMessages([welcomeMessage]);
    setSuggestedResponses(initialSuggestions);
    
    // Focus input on initial load
    const timer = setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
    
    return () => clearTimeout(timer);
  }, [])

  // Memoized copy function
  const copyMessage = useCallback(async (content) => {
    try {
      await navigator.clipboard.writeText(content);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  }, []);

  // Send message handler
  const sendMessage = useCallback(async (messageText = inputValue) => {
    const trimmedText = messageText.trim();
    if (!trimmedText || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmedText,
      timestamp: new Date().toISOString()
    }

    // Optimized state updates
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setSuggestedResponses([]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmedText,
          conversation_id: conversationId
        })
      })

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();
      const botMessage = {
        id: data.message_id || Date.now().toString(),
        role: 'assistant',
        content: data.response,
        timestamp: data.timestamp || new Date().toISOString(),
        confidence: data.confidence,
        sources: data.sources || [],
        contextUsed: data.context_used
      }

      setMessages(prev => [...prev, botMessage]);
      setConversationId(data.conversation_id);
      setSuggestedResponses(data.suggested_responses || []);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "I apologize, but I'm having trouble connecting to the server. Please check your connection and try again.",
        timestamp: new Date().toISOString(),
        confidence: 0.0,
        sources: [],
        isError: true
      }
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, conversationId])

  // Keyboard handler
  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }, [sendMessage]);

  // Clear conversation
  const clearConversation = useCallback(() => {
    const welcomeMessage = {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI customer service assistant. I'm here to help you with any questions about our products, services, pricing, or technical support. How can I assist you today?",
      timestamp: new Date().toISOString(),
      confidence: 1.0,
      sources: []
    };
    
    setMessages([welcomeMessage]);
    setConversationId(null);
    setSuggestedResponses(initialSuggestions);
    
    // Focus input after clearing
    setTimeout(() => inputRef.current?.focus(), 0);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-indigo-50 to-purple-50 font-sans">
      <div className="w-full max-w-[600px] h-[95vh] flex flex-col bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/30 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-indigo-700 to-purple-700 text-white relative">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-teal-400 rounded-full animate-pulse"></div>
            <div className="flex-1">
              <div className="text-lg font-semibold tracking-tight flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-teal-300" />
                <span>TechCorp Assistant</span>
              </div>
              <div className="text-xs text-indigo-100 font-medium">
                AI-Powered Support <span className="mx-1">•</span> <span className="text-white/80">built by Siddiqa Kashaf</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-teal-400 rounded-full"></div>
            <span className="text-xs text-indigo-100">Online</span>
            <Button
              variant="ghost"
              size="icon"
              className="ml-2 text-white/80 hover:bg-white/10"
              aria-label="Clear chat"
              onClick={clearConversation}
            >
              <RotateCcw className="h-5 w-5" />
            </Button>
          </div>
        </div>
        
        {/* Messages Area */}
        <div className="flex-1 overflow-hidden bg-gradient-to-b from-indigo-50/20 via-white/30 to-white/50 relative">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xIC0xKSIgc3Ryb2tlPSJyZ2JhKDIyMSwgMjE2LCAyNDUsIDAuMSkiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTAgMGg2MHY2MEgweiIvPjwvZz48L2c+PC9zdmc+')] opacity-10"></div>
          <ScrollArea className="h-full px-2 sm:px-6 py-4 sm:py-6 relative">
            <div className="flex flex-col gap-4">
              <AnimatePresence initial={false}>
                {messages.map((message) => (
                  <Message 
                    key={message.id} 
                    message={message} 
                    copyMessage={copyMessage} 
                  />
                ))}
              </AnimatePresence>
              
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>
        
        {/* Suggested Responses */}
        {suggestedResponses.length > 0 && (
          <div className="px-2 sm:px-6 py-2 sm:py-4 bg-gradient-to-r from-indigo-50/80 to-purple-50/80 border-t border-indigo-200/50 backdrop-blur-sm">
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestedResponses.map((suggestion, idx) => (
                <motion.div
                  key={idx}
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-full border-indigo-300/50 text-indigo-700 hover:bg-indigo-100/80 hover:border-indigo-400/50 transition-all duration-200 text-xs font-medium px-4 py-2"
                    onClick={() => sendMessage(suggestion)}
                    disabled={isLoading}
                  >
                    {suggestion}
                  </Button>
                </motion.div>
              ))}
            </div>
          </div>
        )}
        
        {/* Input Area */}
        <div className="px-2 sm:px-6 py-2 sm:py-4 bg-white/95 border-t border-indigo-200/50 backdrop-blur-sm sticky bottom-0 z-10">
          <form 
            onSubmit={e => { 
              e.preventDefault(); 
              sendMessage(); 
            }} 
            className="flex items-center gap-2 sm:gap-3"
          >
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me anything about TechCorp Solutions..."
              disabled={isLoading}
              className="flex-1 rounded-2xl px-5 py-3 text-sm border-indigo-300/50 focus:border-indigo-500 focus:ring-indigo-500/20 shadow-sm bg-white/90 backdrop-blur-sm"
              aria-label="Type your message here"
            />
            
            <Button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="rounded-2xl px-5 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold shadow-lg text-sm transition-all duration-200"
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
          
          <div className="mt-2 text-center text-xs text-gray-400">
            Powered by AI • Responses may vary
          </div>
        </div>
      </div>
    </div>
  )
}