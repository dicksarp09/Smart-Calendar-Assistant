import React, { useMemo } from 'react'
import useCalendarStore from '../store/useCalendarStore'

// Simple time grid calendar with proper event positioning
const TimeGridCalendar = () => {
  const { events, fetchEvents, openModal } = useCalendarStore()
  const [isRefreshing, setIsRefreshing] = React.useState(false)
  const [currentDate, setCurrentDate] = React.useState(new Date())
  const [view, setView] = React.useState('week') // 'day', 'week', 'month'
  
  React.useEffect(() => {
    fetchEvents()
  }, [fetchEvents])
  
  // Debug: log events when they change
  React.useEffect(() => {
    console.log('Current events:', events.map(e => ({ title: e.title, start: e.start, end: e.end })))
    console.log('Current view date:', currentDate)
    console.log('Current view:', view)
  }, [events, currentDate, view])
  
  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchEvents()
    setIsRefreshing(false)
  }
  
  // Navigation functions
  const goToToday = () => setCurrentDate(new Date())
  const goToPrev = () => {
    const newDate = new Date(currentDate)
    if (view === 'day') newDate.setDate(newDate.getDate() - 1)
    else if (view === 'week') newDate.setDate(newDate.getDate() - 7)
    else if (view === 'month') newDate.setMonth(newDate.getMonth() - 1)
    setCurrentDate(newDate)
  }
  const goToNext = () => {
    const newDate = new Date(currentDate)
    if (view === 'day') newDate.setDate(newDate.getDate() + 1)
    else if (view === 'week') newDate.setDate(newDate.getDate() + 7)
    else if (view === 'month') newDate.setMonth(newDate.getMonth() + 1)
    setCurrentDate(newDate)
  }
  
  // Generate hours for the day (0-23)
  const hours = Array.from({ length: 24 }, (_, i) => i)
  
  // Get events for a specific day
  const getEventsForDay = (dayEvents, date) => {
    return dayEvents.filter(event => {
      const eventDate = new Date(event.start)
      return eventDate.toDateString() === date.toDateString()
    })
  }
  
  // Calculate event position
  const getEventStyle = (event) => {
    const start = new Date(event.start)
    const end = new Date(event.end)
    
    // Minutes from midnight
    const startMinutes = start.getHours() * 60 + start.getMinutes()
    const endMinutes = end.getHours() * 60 + end.getMinutes()
    const duration = endMinutes - startMinutes
    
    // Each hour = 30px (reduced for better fit)
    const top = startMinutes / 2
    const height = Math.max(duration / 2, 20)
    
    return {
      top: `${top}px`,
      height: `${height}px`
    }
  }
  
  // Handle clicking on a time slot to create event
  const handleTimeSlotClick = (day, hour) => {
    const startTime = new Date(day)
    startTime.setHours(hour, 0, 0, 0)
    const endTime = new Date(day)
    endTime.setHours(hour + 1, 0, 0, 0)
    openModal('create', { start: startTime, end: endTime })
  }
  
  // Handle clicking on an event to edit
  const handleEventClick = (e, event) => {
    e.stopPropagation()
    openModal('edit', {
      id: event.id,
      title: event.title,
      start: event.start,
      end: event.end,
      description: event.description || ''
    })
  }
  
  // Get today's date
  const today = new Date()
  
  // Get view-specific dates
  const getViewDates = () => {
    const date = new Date(currentDate)
    if (view === 'day') {
      return { days: [date], title: date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }
    } else if (view === 'week') {
      const start = new Date(date)
      start.setDate(date.getDate() - date.getDay())
      const days = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(start)
        d.setDate(start.getDate() + i)
        return d
      })
      const end = new Date(start)
      end.setDate(start.getDate() + 6)
      const title = `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
      return { days, title }
    } else {
      // Month view
      const year = date.getFullYear()
      const month = date.getMonth()
      const firstDay = new Date(year, month, 1)
      const lastDay = new Date(year, month + 1, 0)
      const start = new Date(firstDay)
      start.setDate(firstDay.getDate() - firstDay.getDay())
      const days = []
      const current = new Date(start)
      while (current <= lastDay || days.length % 7 !== 0) {
        days.push(new Date(current))
        current.setDate(current.getDate() + 1)
      }
      const title = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
      return { days, title }
    }
  }
  
  const { days, title } = getViewDates()
  
  const calendarEvents = useMemo(() => {
    return events.map(event => ({
      id: event.id,
      title: event.title || event.summary,
      start: new Date(event.start),
      end: new Date(event.end)
    }))
  }, [events])
  
  const buttonStyle = {
    padding: '6px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    background: 'white',
    cursor: 'pointer',
    fontSize: '0.875rem'
  }
  
  return (
    <div className="time-grid-calendar">
      {/* Navigation Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid #e5e7eb',
        background: '#f9fafb'
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={goToToday} style={buttonStyle}>Today</button>
          <button onClick={goToPrev} style={buttonStyle}>←</button>
          <button onClick={goToNext} style={buttonStyle}>→</button>
        </div>
        <div style={{ fontWeight: 600, fontSize: '1.125rem' }}>{title}</div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button 
            onClick={handleRefresh}
            disabled={isRefreshing}
            style={{
              ...buttonStyle,
              background: isRefreshing ? '#9ca3af' : '#6b7280',
              color: 'white',
              border: 'none'
            }}
          >
            {isRefreshing ? '↻' : '↻'} Refresh
          </button>
          <button 
            onClick={() => openModal('create', { start: new Date(), end: new Date(Date.now() + 3600000) })}
            style={{
              ...buttonStyle,
              background: '#4f46e5',
              color: 'white',
              border: 'none',
              fontWeight: 600
            }}
          >
            + New Event
          </button>
          {['day', 'week', 'month'].map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              style={{
                ...buttonStyle,
                border: view === v ? '1px solid #4f46e5' : '1px solid #d1d5db',
                background: view === v ? '#4f46e5' : 'white',
                color: view === v ? 'white' : '#374151',
                textTransform: 'capitalize'
              }}
            >
              {v}
            </button>
          ))}
        </div>
      </div>
      
      {/* Calendar Grid */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        overflow: 'auto'
      }}>
        {/* Header Row - only show for day/week, not month */}
        {view !== 'month' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '60px repeat(7, 1fr)',
            borderBottom: '1px solid #e5e7eb',
            background: '#f9fafb',
            position: 'sticky',
            top: 0,
            zIndex: 10
          }}>
            <div style={{ padding: '12px', fontWeight: 600, color: '#6b7280' }}></div>
            {days.map(day => (
              <div key={day.toISOString()} style={{
                padding: '12px',
                textAlign: 'center',
                fontWeight: 600,
                color: day.toDateString() === today.toDateString() ? '#4f46e5' : '#111827'
              }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                    {day.toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div style={{ fontSize: '1rem' }}>{day.getDate()}</div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Time Grid */}
        <div style={{ display: 'flex', flex: 1 }}>
          {view === 'month' ? (
            // Month view - unified grid with date in each cell
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
              {/* Weekday header for month view */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(7, 1fr)',
                borderBottom: '1px solid #e5e7eb',
                background: '#f9fafb'
              }}>
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} style={{
                    padding: '8px',
                    textAlign: 'center',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    color: '#6b7280'
                  }}>{day}</div>
                ))}
              </div>
              {/* Calendar cells */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', flex: 1 }}>
                {days.map(day => {
                  const dayEvents = getEventsForDay(calendarEvents, day)
                  const isCurrentMonth = day.getMonth() === currentDate.getMonth()
                  const isToday = day.toDateString() === today.toDateString()
                  return (
                    <div 
                      key={day.toISOString()} 
                      onClick={() => {
                        setCurrentDate(new Date(day))
                        setView('day')
                      }}
                      style={{
                        minHeight: '80px',
                        borderRight: '1px solid #e5e7eb',
                        borderBottom: '1px solid #e5e7eb',
                        padding: '4px',
                        background: isToday ? '#eff6ff' : (isCurrentMonth ? 'white' : '#f9fafb'),
                        opacity: isCurrentMonth ? 1 : 0.6,
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column'
                      }}
                    >
                      {/* Date number */}
                      <div style={{
                        fontWeight: isToday ? 700 : 500,
                        fontSize: '0.875rem',
                        color: isToday ? '#4f46e5' : (isCurrentMonth ? '#111827' : '#9ca3af'),
                        marginBottom: '2px'
                      }}>{day.getDate()}</div>
                      {/* Events - clean display without time prefix */}
                      {dayEvents.slice(0, 3).map(event => (
                        <div 
                          key={event.id} 
                          onClick={(e) => handleEventClick(e, event)}
                          style={{
                            background: '#4f46e5',
                            color: 'white',
                            borderRadius: '2px',
                            padding: '1px 3px',
                            fontSize: '0.6rem',
                            marginBottom: '1px',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            cursor: 'pointer'
                          }}
                        >
                          {event.title}
                        </div>
                      ))}
                      {dayEvents.length > 3 && (
                        <div style={{ fontSize: '0.6rem', color: '#6b7280' }}>+{dayEvents.length - 3} more</div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ) : (
            // Day/Week view - time grid
            <>
              {/* Time column */}
              <div style={{
                width: '60px',
                flexShrink: 0,
                borderRight: '1px solid #e5e7eb',
                background: '#f9fafb'
              }}>
                {hours.map(hour => (
                  <div key={hour} style={{
                    height: '30px',
                    padding: '2px 4px',
                    fontSize: '0.65rem',
                    color: '#6b7280',
                    textAlign: 'right',
                    borderBottom: '1px solid #f3f4f6'
                  }}>
                    {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
                  </div>
                ))}
              </div>
              
              {/* Day columns */}
              {days.map(day => {
                const dayEvents = getEventsForDay(calendarEvents, day)
                return (
                  <div key={day.toISOString()} style={{
                    flex: 1,
                    position: 'relative',
                    borderRight: '1px solid #e5e7eb',
                    minWidth: '100px'
                  }}>
                    {/* Hour grid lines - clickable to create event */}
                    {hours.map(hour => (
                      <div 
                        key={hour} 
                        onClick={() => handleTimeSlotClick(day, hour)}
                        style={{
                          height: '30px',
                          borderBottom: '1px solid #f3f4f6',
                          cursor: 'pointer'
                        }}
                      />
                    ))}
                    
                    {/* Current time indicator */}
                    {day.toDateString() === today.toDateString() && (
                      <div style={{
                        position: 'absolute',
                        left: 0,
                        right: 0,
                        top: `${(today.getHours() * 60 + today.getMinutes()) / 2}px`,
                        height: '2px',
                        background: '#ef4444',
                        zIndex: 5,
                        pointerEvents: 'none'
                      }} />
                    )}
                    
                    {/* Events - clickable to edit */}
                    {dayEvents.map((event, idx) => {
                      const style = getEventStyle(event)
                      return (
                        <div
                          key={event.id}
                          onClick={(e) => handleEventClick(e, event)}
                          style={{
                            position: 'absolute',
                            left: '2px',
                            right: `${2 + idx * 15}px`,
                            ...style,
                            background: '#4f46e5',
                            borderRadius: '4px',
                            padding: '4px 6px',
                            color: 'white',
                            fontSize: '0.7rem',
                            overflow: 'hidden',
                            zIndex: 1,
                            cursor: 'pointer'
                          }}
                        >
                          <div style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {event.title}
                          </div>
                          <div style={{ fontSize: '0.6rem', opacity: 0.9 }}>
                            {event.start.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )
              })}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default TimeGridCalendar
