import React, { useState, useEffect } from 'react';
import { Calendar, Clock, User, Phone, Car, CheckCircle, XCircle, AlertCircle, Filter } from 'lucide-react';

const Appointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchPhone, setSearchPhone] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(null);

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    confirmed: 'bg-green-100 text-green-800 border-green-200',
    cancelled: 'bg-red-100 text-red-800 border-red-200',
    completed: 'bg-blue-100 text-blue-800 border-blue-200'
  };

  const statusIcons = {
    pending: AlertCircle,
    confirmed: CheckCircle,
    cancelled: XCircle,
    completed: CheckCircle
  };

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      let url = '/api/appointments/';
      const params = new URLSearchParams();
      
      if (statusFilter) {
        params.append('status', statusFilter);
      }
      
      if (params.toString()) {
        url += '?' + params.toString();
      }
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setAppointments(data.appointments);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch appointments');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const searchByPhone = async () => {
    if (!searchPhone.trim()) {
      fetchAppointments();
      return;
    }
    
    try {
      setLoading(true);
      const response = await fetch(`/api/appointments/customer/${encodeURIComponent(searchPhone)}`);
      const data = await response.json();
      
      if (data.success) {
        setAppointments(data.appointments);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch customer appointments');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateAppointmentStatus = async (appointmentId, newStatus) => {
    try {
      setUpdatingStatus(appointmentId);
      const response = await fetch(`/api/appointments/${appointmentId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update the appointment in the local state
        setAppointments(prev => prev.map(apt => 
          apt.appointment_id === appointmentId 
            ? { ...apt, status: newStatus }
            : apt
        ));
      } else {
        setError(data.error || 'Failed to update appointment status');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setUpdatingStatus(null);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [statusFilter]);

  const formatDateTime = (dateTimeStr) => {
    try {
      const date = new Date(dateTimeStr);
      return {
        date: date.toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'short', 
          day: 'numeric' 
        }),
        time: date.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit' 
        })
      };
    } catch {
      return { date: 'Invalid Date', time: '' };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading appointments...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Appointment Management</h1>
          <p className="mt-2 text-gray-600">View and manage customer appointments</p>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Status Filter */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Filter className="inline w-4 h-4 mr-1" />
                Filter by Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="confirmed">Confirmed</option>
                <option value="cancelled">Cancelled</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            {/* Phone Search */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Phone className="inline w-4 h-4 mr-1" />
                Search by Phone
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchPhone}
                  onChange={(e) => setSearchPhone(e.target.value)}
                  placeholder="Enter customer phone number"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={searchByPhone}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Search
                </button>
                <button
                  onClick={() => {
                    setSearchPhone('');
                    fetchAppointments();
                  }}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <XCircle className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Appointments List */}
        <div className="space-y-4">
          {appointments.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No appointments found</h3>
              <p className="text-gray-600">
                {searchPhone ? 'No appointments found for this phone number.' : 'No appointments match your current filters.'}
              </p>
            </div>
          ) : (
            appointments.map((appointment) => {
              const StatusIcon = statusIcons[appointment.status] || AlertCircle;
              const dateTime = formatDateTime(appointment.appointment_datetime);
              
              return (
                <div key={appointment._id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                    {/* Appointment Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-4">
                        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${statusColors[appointment.status]}`}>
                          <StatusIcon className="w-4 h-4 mr-1" />
                          {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                        </div>
                        <span className="text-sm text-gray-500">ID: {appointment.appointment_id}</span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="flex items-center text-gray-700">
                          <User className="w-4 h-4 mr-2 text-gray-500" />
                          <div>
                            <p className="font-medium">{appointment.customer_name}</p>
                            <p className="text-sm text-gray-500">Customer</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center text-gray-700">
                          <Phone className="w-4 h-4 mr-2 text-gray-500" />
                          <div>
                            <p className="font-medium">{appointment.customer_phone}</p>
                            <p className="text-sm text-gray-500">Phone</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center text-gray-700">
                          <Calendar className="w-4 h-4 mr-2 text-gray-500" />
                          <div>
                            <p className="font-medium">{dateTime.date}</p>
                            <p className="text-sm text-gray-500">Date</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center text-gray-700">
                          <Clock className="w-4 h-4 mr-2 text-gray-500" />
                          <div>
                            <p className="font-medium">{dateTime.time}</p>
                            <p className="text-sm text-gray-500">Time</p>
                          </div>
                        </div>
                      </div>
                      
                      {appointment.service_type && (
                        <div className="mt-4 flex items-center text-gray-700">
                          <Car className="w-4 h-4 mr-2 text-gray-500" />
                          <div>
                            <p className="font-medium">{appointment.service_type}</p>
                            <p className="text-sm text-gray-500">Service Type</p>
                          </div>
                        </div>
                      )}
                      
                      {appointment.notes && (
                        <div className="mt-4">
                          <p className="text-sm text-gray-600">
                            <strong>Notes:</strong> {appointment.notes}
                          </p>
                        </div>
                      )}
                    </div>
                    
                    {/* Status Actions */}
                    <div className="mt-4 lg:mt-0 lg:ml-6">
                      <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-700">Update Status:</label>
                        <div className="flex flex-wrap gap-2">
                          {['pending', 'confirmed', 'cancelled', 'completed'].map((status) => (
                            <button
                              key={status}
                              onClick={() => updateAppointmentStatus(appointment.appointment_id, status)}
                              disabled={appointment.status === status || updatingStatus === appointment.appointment_id}
                              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                                appointment.status === status
                                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
                              } ${updatingStatus === appointment.appointment_id ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                              {updatingStatus === appointment.appointment_id ? 'Updating...' : status.charAt(0).toUpperCase() + status.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
        
        {/* Summary */}
        {appointments.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(
                appointments.reduce((acc, apt) => {
                  acc[apt.status] = (acc[apt.status] || 0) + 1;
                  return acc;
                }, {})
              ).map(([status, count]) => (
                <div key={status} className="text-center">
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full ${statusColors[status]} mb-2`}>
                    <span className="text-lg font-bold">{count}</span>
                  </div>
                  <p className="text-sm font-medium text-gray-900">{status.charAt(0).toUpperCase() + status.slice(1)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Appointments;