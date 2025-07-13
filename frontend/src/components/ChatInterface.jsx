import { useState, useRef, useEffect } from 'react'
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
  RotateCcw
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [suggestedResponses, setSuggestedResponses] = useState([])
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const lastMessageRef = useRef(null)

  // Initial suggestion messages
  const initialSuggestions = [
    "What are your pricing plans?",
    "How can I contact you?",
    "Tell me about your tech services",
    "What are your payment terms?"
  ]

  // Scroll to the start of the last message (top of bubble)
  useEffect(() => {
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [messages, isLoading])

  useEffect(() => {
    // Add welcome message and set initial suggestions
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI customer service assistant. I'm here to help you with any questions about our products, services, pricing, or technical support. How can I assist you today?",
      timestamp: new Date().toISOString(),
      confidence: 1.0,
      sources: []
    }])
    setSuggestedResponses(initialSuggestions)
  }, [])

  const sendMessage = async (messageText = inputValue) => {
    if (!messageText.trim() || isLoading) return

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setSuggestedResponses([])

    // Focus/select the input after sending
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus()
        inputRef.current.select && inputRef.current.select()
      }
    }, 0)

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          conversation_id: conversationId
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()

      const botMessage = {
        id: data.message_id || Date.now().toString(),
        role: 'assistant',
        content: data.response,
        timestamp: data.timestamp,
        confidence: data.confidence,
        sources: data.sources || [],
        contextUsed: data.context_used
      }

      setMessages(prev => [...prev, botMessage])
      setConversationId(data.conversation_id)
      setSuggestedResponses(data.suggested_responses || [])

      // Focus/select the input after bot reply
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus()
          inputRef.current.select && inputRef.current.select()
        }
      }, 0)

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: "I apologize, but I'm having trouble connecting to the server. Please check your connection and try again.",
        timestamp: new Date().toISOString(),
        confidence: 0.0,
        sources: [],
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearConversation = () => {
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI customer service assistant. I'm here to help you with any questions about our products, services, pricing, or technical support. How can I assist you today?",
      timestamp: new Date().toISOString(),
      confidence: 1.0,
      sources: []
    }])
    setConversationId(null)
    setSuggestedResponses(initialSuggestions)
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus()
        inputRef.current.select && inputRef.current.select()
      }
    }, 0)
  }

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content)
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Helper to get user initials
  const getUserInitials = () => 'U'; // You can make this dynamic if you have user info

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 font-sans">
      <div className="w-full max-w-[600px] h-[95vh] flex flex-col bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/30 overflow-hidden">
        {/* Modern Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white relative">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            <div className="flex-1">
              <div className="text-lg font-semibold tracking-tight">TechCorp Assistant</div>
              <div className="text-xs text-blue-100 font-medium">
                AI-Powered Support <span className="ml-2 text-white/80">• built by Siddiqa Kashaf</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-xs text-blue-100">Live</span>
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
        <div className="flex-1 overflow-hidden bg-gradient-to-b from-blue-50/30 to-white/50">
          <ScrollArea className="h-full px-2 sm:px-6 py-4 sm:py-6">
            <div className="flex flex-col gap-4">
              <AnimatePresence>
                {messages.map((message, idx) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                    className={`group flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    ref={idx === messages.length - 1 ? lastMessageRef : null}
                  >
                    <div className={`relative flex flex-col max-w-[85%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`flex items-end gap-3`}>
                        {/* Modern Avatar */}
                        {message.role === 'assistant' && (
                          <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
                            <Bot className="h-5 w-5 text-white" />
                          </div>
                        )}
                        {/* Modern Message Bubble */}
                        <div
                          className={`relative rounded-2xl border transition-all duration-300 px-5 py-3 text-sm font-normal whitespace-pre-line break-words shadow-lg ${message.role === 'user'
                            ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white border-blue-400/30'
                            : message.isError
                              ? 'bg-red-50/90 text-red-900 border-red-200/50'
                              : 'bg-white/95 text-gray-800 border-gray-200/50 backdrop-blur-sm'
                            } group-hover:shadow-xl group-hover:scale-[1.02] focus-within:shadow-xl focus-within:scale-[1.02]`}
                          tabIndex={0}
                          aria-label={message.role === 'user' ? 'Your message' : 'Bot message'}
                        >
                          {/* Message Text */}
                          <div className="block text-sm leading-relaxed">
                            <div className="prose prose-sm max-w-none text-inherit">
                              <ReactMarkdown>{message.content}</ReactMarkdown>
                            </div>
                          </div>
                          {/* Minimal Controls */}
                          <div className="absolute -bottom-8 right-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-7 w-7 p-0 hover:bg-blue-50 active:scale-95 rounded-full" aria-label="Copy message" onClick={() => copyMessage(message.content)}>
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                      {/* Minimal Timestamp */}
                      <span className="text-xs text-gray-400 mt-2 ml-12">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {/* Modern Typing Indicator */}
              {isLoading && (
                <div className="flex items-center gap-3 mt-2">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex items-center gap-1 bg-white/90 rounded-2xl px-4 py-2 shadow-lg">
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                    <span className="text-xs text-gray-600 ml-3 font-medium">Thinking...</span>
                  </div>
                </div>
              )}
            </div>
            <div ref={messagesEndRef} />
          </ScrollArea>
        </div>
        {/* Modern Suggested Responses */}
        {suggestedResponses.length > 0 && (
          <div className="px-2 sm:px-6 py-2 sm:py-4 bg-gradient-to-r from-blue-50/80 to-indigo-50/80 border-t border-blue-200/50 backdrop-blur-sm">
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestedResponses.map((suggestion, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  className="rounded-full border-blue-300/50 text-blue-700 hover:bg-blue-100/80 hover:border-blue-400/50 transition-all duration-200 text-xs font-medium px-4 py-2"
                  onClick={() => sendMessage(suggestion)}
                  disabled={isLoading}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}
        {/* Modern Input Area (sticky for mobile) */}
        <div className="px-2 sm:px-6 py-2 sm:py-4 bg-white/95 border-t border-blue-200/50 backdrop-blur-sm sticky bottom-0 z-10">
          <form onSubmit={e => { e.preventDefault(); sendMessage(); }} className="flex items-center gap-2 sm:gap-3">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about TechCorp Solutions..."
              disabled={isLoading}
              className="flex-1 rounded-2xl px-5 py-3 text-sm border-blue-300/50 focus:border-blue-500 focus:ring-blue-500/20 shadow-sm bg-white/90 backdrop-blur-sm"
              aria-label="Type your message here"
            />
            <motion.button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="rounded-2xl px-5 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold shadow-lg text-sm transition-all duration-200 active:scale-95"
              aria-label="Send message"
              whileTap={{ scale: 0.92 }}
            >
              <Send className="h-4 w-4" />
            </motion.button>
          </form>
        </div>
      </div>
    </div>
  )
}



