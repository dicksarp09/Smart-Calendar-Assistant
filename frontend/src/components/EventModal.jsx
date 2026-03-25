import React, { useState, useEffect } from 'react'
import useCalendarStore from '../store/useCalendarStore'

const EventModal = () => {
  const { 
    isModalOpen, 
    selectedEvent, 
    modalMode, 
    closeModal, 
    addEvent, 
    updateEvent, 
    removeEvent 
  } = useCalendarStore()

  const [formData, setFormData] = useState({
    summary: '',
    description: '',
    start_time: '',
    end_time: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (modalMode === 'edit' && selectedEvent) {
      setFormData({
        summary: selectedEvent.title || '',
        description: selectedEvent.description || '',
        start_time: formatDateTimeLocal(selectedEvent.start),
        end_time: formatDateTimeLocal(selectedEvent.end)
      })
    } else if (modalMode === 'create' && selectedEvent) {
      setFormData({
        summary: '',
        description: '',
        start_time: formatDateTimeLocal(selectedEvent.start),
        end_time: formatDateTimeLocal(selectedEvent.end)
      })
    }
  }, [modalMode, selectedEvent])

  const formatDateTimeLocal = (date) => {
    const d = new Date(date)
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const eventData = {
        summary: formData.summary,
        description: formData.description,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }

      let result
      if (modalMode === 'create') {
        result = await addEvent(eventData)
      } else if (modalMode === 'edit') {
        result = await updateEvent(selectedEvent.id, eventData)
      }

      if (result?.conflict) {
        setError(`Time conflict! ${result.suggestion}`)
        setIsSubmitting(false)
        return
      }

      if (result?.success) {
        closeModal()
      } else {
        setError(result?.error || 'An error occurred')
      }
    } catch (err) {
      setError(err.message)
    }

    setIsSubmitting(false)
  }

  const handleDelete = async () => {
    if (!selectedEvent?.id) return
    
    setIsSubmitting(true)
    const result = await removeEvent(selectedEvent.id)
    
    if (result.success) {
      closeModal()
    } else {
      setError(result.error)
    }
    
    setIsSubmitting(false)
  }

  if (!isModalOpen) return null

  return (
    <div className="modal-overlay" onClick={closeModal}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>
          {modalMode === 'create' && 'Create Event'}
          {modalMode === 'edit' && 'Edit Event'}
          {modalMode === 'delete' && 'Delete Event'}
        </h2>

        {modalMode === 'delete' ? (
          <div>
            <p>Are you sure you want to delete "{selectedEvent?.title}"?</p>
            <div className="form-actions">
              <button 
                type="button" 
                className="button button-secondary"
                onClick={closeModal}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="button button-danger"
                onClick={handleDelete}
                disabled={isSubmitting}
              >
                Delete
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && (
              <div style={{ 
                color: '#ef4444', 
                fontSize: '0.875rem', 
                marginBottom: '1rem',
                padding: '0.5rem',
                backgroundColor: '#fee2e2',
                borderRadius: '0.25rem'
              }}>
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="summary">Title</label>
              <input
                type="text"
                id="summary"
                name="summary"
                value={formData.summary}
                onChange={handleChange}
                required
                placeholder="Event title"
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="3"
                placeholder="Event description (optional)"
              />
            </div>

            <div className="form-group">
              <label htmlFor="start_time">Start</label>
              <input
                type="datetime-local"
                id="start_time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="end_time">End</label>
              <input
                type="datetime-local"
                id="end_time"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="button button-secondary"
                onClick={closeModal}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="button button-primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Saving...' : (modalMode === 'create' ? 'Create' : 'Save')}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default EventModal
