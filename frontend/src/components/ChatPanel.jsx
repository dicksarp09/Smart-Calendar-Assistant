import React, { useState, useRef, useEffect } from 'react'
import useCalendarStore from '../store/useCalendarStore'

const suggestions = [
  "What's on my calendar today?",
  "Schedule a meeting tomorrow at 3pm",
  "Find me a free slot this week",
  "Show my weekly overview",
  "Book a 1-hour meeting next week"
]

const ChatPanel = ({ isOpen, onToggle }) => {
  const { messages, sendToAgent, isAgentLoading, clearChat } = useCalendarStore()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isAgentLoading) return

    const message = input.trim()
    setInput('')
    await sendToAgent(message)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e)
    }
  }

  const handleSuggestionClick = async (suggestion) => {
    setInput(suggestion)
    await sendToAgent(suggestion)
  }

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <>
      {/* Mobile toggle button */}
      <button className="chat-toggle" onClick={onToggle}>
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </button>
      
      <div className={`chat-panel ${isOpen ? 'open' : ''}`}>
        <div className="chat-header">
          <div>
            <h2>AI Assistant</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Ask me anything about your calendar
            </p>
          </div>
          {messages.length > 0 && (
            <button 
              onClick={clearChat}
              style={{
                fontSize: '0.75rem',
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              Clear
            </button>
          )}
        </div>
        
        <div className="chat-messages">
          {messages.length === 0 && (
            <div style={{ 
              textAlign: 'center', 
              color: 'var(--text-secondary)', 
              padding: '1rem',
              fontSize: '0.875rem'
            }}>
              <p style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>👋</p>
              <p style={{ fontWeight: '500', marginBottom: '0.5rem' }}>Hi! I'm your AI Calendar Assistant.</p>
              <p style={{ marginBottom: '1rem' }}>Try asking:</p>
            </div>
          )}
          
          {/* Quick suggestions */}
          {messages.length === 0 && (
            <div style={{ padding: '0 1rem 1rem' }}>
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestionClick(suggestion)}
                  disabled={isAgentLoading}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: '0.625rem 0.875rem',
                    marginBottom: '0.5rem',
                    fontSize: '0.8125rem',
                    background: 'var(--surface-color)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    color: 'var(--text-primary)',
                    transition: 'all 0.2s',
                  }}
                  onMouseOver={(e) => {
                    e.target.style.borderColor = 'var(--primary-color)'
                    e.target.style.background = 'var(--primary-50)'
                  }}
                  onMouseOut={(e) => {
                    e.target.style.borderColor = 'var(--border-color)'
                    e.target.style.background = 'var(--surface-color)'
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
          
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.role}`}
            >
              <div>{message.content}</div>
              <div className="message-time">
                {formatTime(message.timestamp)}
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {isAgentLoading && (
            <div className="message assistant">
              <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
                <span style={{ 
                  width: '8px', 
                  height: '8px', 
                  background: 'var(--text-secondary)',
                  borderRadius: '50%',
                  animation: 'bounce 1s infinite'
                }} />
                <span style={{ 
                  width: '8px', 
                  height: '8px', 
                  background: 'var(--text-secondary)',
                  borderRadius: '50%',
                  animation: 'bounce 1s infinite 0.1s'
                }} />
                <span style={{ 
                  width: '8px', 
                  height: '8px', 
                  background: 'var(--text-secondary)',
                  borderRadius: '50%',
                  animation: 'bounce 1s infinite 0.2s'
                }} />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        <form className="chat-input-container" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-input"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isAgentLoading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!input.trim() || isAgentLoading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </form>
      </div>
    </>
  )
}

export default ChatPanel
