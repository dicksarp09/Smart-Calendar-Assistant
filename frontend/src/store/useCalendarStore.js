import { create } from 'zustand'
import api from '../services/api'
import websocketService from '../services/websocket'

const useCalendarStore = create((set, get) => ({
  // WebSocket connection
  isWsConnected: false,
  // Events state
  events: [],
  isLoading: false,
  error: null,
  
  // Chat state
  messages: [],
  isAgentLoading: false,
  
  // Modal state
  isModalOpen: false,
  selectedEvent: null,
  modalMode: 'create', // 'create' | 'edit' | 'delete'
  
  // Set events
  setEvents: (events) => set({ events }),
  
  // Add event
  addEvent: async (eventData) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/events', eventData)
      if (response.data.status === 'conflict') {
        return { 
          success: false, 
          conflict: true, 
          conflicts: response.data.conflicts,
          suggestion: response.data.suggestion
        }
      }
      const newEvent = response.data.event
      set(state => ({
        events: [...state.events, {
          id: newEvent.id,
          title: newEvent.summary,
          start: new Date(newEvent.start),
          end: new Date(newEvent.end),
          description: newEvent.description
        }],
        isLoading: false
      }))
      return { success: true }
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to create event', isLoading: false })
      return { success: false, error: error.message }
    }
  },
  
  // Update event
  updateEvent: async (eventId, eventData) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.put(`/events/${eventId}`, {
        event_id: eventId,
        ...eventData
      })
      const updatedEvent = response.data.event
      set(state => ({
        events: state.events.map(e => 
          e.id === eventId ? {
            ...e,
            title: updatedEvent.summary,
            start: new Date(updatedEvent.start),
            end: new Date(updatedEvent.end),
            description: updatedEvent.description
          } : e
        ),
        isLoading: false
      }))
      return { success: true }
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to update event', isLoading: false })
      return { success: false, error: error.message }
    }
  },
  
  // Remove event
  removeEvent: async (eventId) => {
    set({ isLoading: true, error: null })
    try {
      await api.delete(`/events/${eventId}`)
      set(state => ({
        events: state.events.filter(e => e.id !== eventId),
        isLoading: false
      }))
      return { success: true }
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to delete event', isLoading: false })
      return { success: false, error: error.message }
    }
  },
  
  // Fetch events
  fetchEvents: async () => {
    set({ isLoading: true, error: null })
    try {
      // Force bypass cache by adding a timestamp parameter
      const response = await api.get('/events?_t=' + Date.now())
      const events = response.data.events.map(event => ({
        id: event.id,
        title: event.summary,
        start: new Date(event.start),
        end: new Date(event.end),
        description: event.description
      }))
      set({ events, isLoading: false })
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to fetch events', isLoading: false })
    }
  },
  
  // Chat actions
  addMessage: (message, role = 'user') => {
    set(state => ({
      messages: [...state.messages, {
        id: Date.now(),
        content: message,
        role,
        timestamp: new Date()
      }]
    }))
  },
  
  sendToAgent: async (message) => {
    const { messages } = get()
    
    // Add user message
    get().addMessage(message, 'user')
    
    set({ isAgentLoading: true })
    
    try {
      // Convert messages to conversation history format
      const conversation_history = messages.slice(-10).map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }))
      
      const response = await api.post('/agent', {
        message,
        conversation_history
      })
      
      const data = response.data
      
      // Add assistant response
      set(state => ({
        messages: [...state.messages, {
          id: Date.now(),
          content: data.response,
          role: 'assistant',
          timestamp: new Date()
        }],
        isAgentLoading: false
      }))
      
      // If events were modified, refresh the calendar from server
      if (data.action_taken === 'create_event' || data.action_taken === 'update_event') {
        // Refresh events from the server
        get().fetchEvents()
      } else if (data.events && data.events.length > 0) {
        const events = data.events.map(event => ({
          id: event.id,
          title: event.summary,
          start: new Date(event.start),
          end: new Date(event.end),
          description: event.description
        }))
        set({ events })
      }
      
      return data
    } catch (error) {
      set({ isAgentLoading: false })
      get().addMessage('Sorry, I encountered an error processing your request.', 'assistant')
      return { error: error.message }
    }
  },
  
  // Modal actions
  openModal: (mode = 'create', event = null) => {
    set({
      isModalOpen: true,
      modalMode: mode,
      selectedEvent: event
    })
  },
  
  closeModal: () => {
    set({
      isModalOpen: false,
      selectedEvent: null,
      modalMode: 'create'
    })
  },
  
  // Clear chat
  clearChat: () => set({ messages: [] }),

  // WebSocket methods
  connectWebSocket: (userId) => {
    websocketService.connect(userId);
    
    // Set up event listeners
    websocketService.onEventUpdate((data) => {
      const { action, event } = data;
      
      if (action === 'created') {
        // New event created - add to state
        set(state => ({
          events: [...state.events, {
            id: event.id,
            title: event.summary,
            start: new Date(event.start),
            end: new Date(event.end),
            description: event.description
          }]
        }));
      } else if (action === 'updated') {
        // Event updated - update in state
        set(state => ({
          events: state.events.map(e => 
            e.id === event.id ? {
              ...e,
              title: event.summary,
              start: new Date(event.start),
              end: new Date(event.end),
              description: event.description
            } : e
          )
        }));
      } else if (action === 'deleted') {
        // Event deleted - remove from state
        set(state => ({
          events: state.events.filter(e => e.id !== event.id)
        }));
      }
    });
    
    websocketService.on('connected', () => {
      set({ isWsConnected: true });
    });
    
    websocketService.on('disconnected', () => {
      set({ isWsConnected: false });
    });
  },
  
  disconnectWebSocket: () => {
    websocketService.disconnect();
    set({ isWsConnected: false });
  }
}))

export default useCalendarStore
