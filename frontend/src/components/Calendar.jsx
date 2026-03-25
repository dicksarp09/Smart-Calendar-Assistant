import React, { useEffect, useCallback, useMemo, useState } from 'react'
import { Calendar as BigCalendar, dateFnsLocalizer } from 'react-big-calendar'
import format from 'date-fns/format'
import parse from 'date-fns/parse'
import startOfWeek from 'date-fns/startOfWeek'
import getDay from 'date-fns/getDay'
import enUS from 'date-fns/locale/en-US'
import useCalendarStore from '../store/useCalendarStore'

// Setup localizer for react-big-calendar
const locales = { 'en-US': enUS }

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales
})

// Event category colors
const eventColors = {
  work: '#3b82f6',
  personal: '#10b981',
  meeting: '#8b5cf6',
  focus: '#f59e0b',
  default: '#4f46e5'
}

const Calendar = () => {
  const { events, fetchEvents, openModal, isLoading } = useCalendarStore()

  useEffect(() => {
    fetchEvents()
  }, [])

  // Handle event selection
  const handleSelectEvent = useCallback((event) => {
    openModal('edit', event)
  }, [openModal])

  // Handle slot selection (creating new event)
  const handleSelectSlot = useCallback(({ start, end }) => {
    openModal('create', { start, end })
  }, [openModal])

  // Handle event drop/paste
  const handleEventDrop = useCallback(({ event, start, end }) => {
    useCalendarStore.getState().updateEvent(event.id, {
      start_time: start,
      end_time: end,
      summary: event.title,
      description: event.description
    })
  }, [])

  // Convert events to react-big-calendar format
  const calendarEvents = useMemo(() => {
    return events.map(event => {
      const start = new Date(event.start)
      const end = new Date(event.end)
      // Force end to be after start (fix for zero-length events)
      if (end.getTime() <= start.getTime()) {
        end.setTime(start.getTime() + 60 * 60 * 1000) // Add 1 hour
      }
      return {
        id: event.id,
        title: event.title || event.summary,
        start: start,
        end: end,
        description: event.description,
        allDay: false
      }
    })
  }, [events])

  // Event style with colors
  const eventStyleGetter = useCallback((event) => {
    return {
      style: {
        backgroundColor: '#4f46e5',
        borderRadius: '4px',
        opacity: 0.9,
        color: 'white',
        border: '0px'
      }
    }
  }, [])

  return (
    <div className="calendar-wrapper">
      {isLoading && events.length === 0 ? (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%',
          color: 'var(--text-secondary)'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              width: '40px', 
              height: '40px', 
              border: '3px solid var(--border-color)',
              borderTopColor: 'var(--primary-color)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 1rem'
            }} />
            <p>Loading calendar...</p>
          </div>
        </div>
      ) : (
        <BigCalendar
          localizer={localizer}
          events={calendarEvents}
          startAccessor="start"
          endAccessor="end"
          style={{ height: '100%' }}
          onSelectEvent={handleSelectEvent}
          onSelectSlot={handleSelectSlot}
          onEventDrop={handleEventDrop}
          onEventResize={handleEventDrop}
          selectable
          resizable
          eventPropGetter={eventStyleGetter}
          views={['month', 'week', 'day']}
          defaultView="week"
          step={30}
          showMultiDayTimes
          min={new Date(2024, 0, 1, 0, 0)}
          max={new Date(2024, 0, 2, 0, 0)}
        />
      )}
    </div>
  )
}

export default Calendar
