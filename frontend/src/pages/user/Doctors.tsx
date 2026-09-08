import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Doctor, AppointmentCreate } from '../../types';

const SPECIALIZATIONS = [
  'Cardiology',
  'General Physician',
  'Dermatology',
  'Orthopedics',
  'Pediatrics',
  'Neurology',
];

const formatDays = (days: string): string => {
  if (!days) return 'N/A';
  const dayMap: Record<string, string> = {
    Mon: 'Monday',
    Tue: 'Tuesday',
    Wed: 'Wednesday',
    Thu: 'Thursday',
    Fri: 'Friday',
    Sat: 'Saturday',
    Sun: 'Sunday',
  };
  return days
    .split(',')
    .map((d) => dayMap[d.trim()] || d.trim())
    .join(', ');
};

const formatFee = (fee: number): string => {
  return `₹${Number(fee).toFixed(2)}`;
};

const getTodayStr = (): string => {
  const d = new Date();
  return d.toISOString().split('T')[0];
};

const Doctors: React.FC = () => {
  const navigate = useNavigate();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [specialization, setSpecialization] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [apptDate, setApptDate] = useState(getTodayStr());
  const [apptTime, setApptTime] = useState('');
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('cf_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchDoctors = async () => {
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (specialization) params.specialization = specialization;

      const res = await axios.get('/api/doctors', {
        headers: getAuthHeaders(),
        params,
      });

      const allDoctors: Doctor[] = Array.isArray(res.data)
        ? res.data
        : res.data.doctors || res.data.results || [];
      const activeDoctors = allDoctors.filter(
        (d) => d.status === 'active'
      );
      setDoctors(activeDoctors);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Please login to view doctors.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch doctors.');
      }
      setDoctors([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctors();
  }, []);

  useEffect(() => {
    fetchDoctors();
  }, [specialization]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDoctors();
  };

  const openBookingModal = (doctor: Doctor) => {
    setSelectedDoctor(doctor);
    setApptDate(getTodayStr());
    setApptTime('');
    setBookingError('');
    setBookingSuccess(false);
    setModalOpen(true);
  };

  const closeBookingModal = () => {
    setModalOpen(false);
    setSelectedDoctor(null);
  };

  const handleBookAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctor) return;

    setBookingError('');
    setBookingLoading(true);
    setBookingSuccess(false);

    try {
      const payload: AppointmentCreate = {
        doctor_id: selectedDoctor.id,
        appointment_date: apptDate,
        appointment_time: apptTime,
      };

      await axios.post('/api/appointments', payload, {
        headers: getAuthHeaders(),
      });

      setBookingSuccess(true);
      setTimeout(() => {
        closeBookingModal();
        navigate('/user/appointments');
      }, 1500);
    } catch (err: any) {
      setBookingError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          'Failed to book appointment.'
      );
    } finally {
      setBookingLoading(false);
    }
  };

  const getSpecializationColor = (spec: string): string => {
    const colors: Record<string, string> = {
      Cardiology: 'bg-red-100 text-red-800',
      'General Physician': 'bg-blue-100 text-blue-800',
      Dermatology: 'bg-pink-100 text-pink-800',
      Orthopedics: 'bg-yellow-100 text-yellow-800',
      Pediatrics: 'bg-green-100 text-green-800',
      Neurology: 'bg-purple-100 text-purple-800',
    };
    return colors[spec] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Find a Doctor</h1>
          <p className="mt-2 text-gray-600">
            Browse our experienced specialists and book an appointment
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <form onSubmit={handleSearchSubmit} className="flex-1">
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search doctors by name..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
              />
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </form>

          <select
            value={specialization}
            onChange={(e) => setSpecialization(e.target.value)}
            className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none bg-white min-w-[200px]"
          >
            <option value="">All Specializations</option>
            {SPECIALIZATIONS.map((spec) => (
              <option key={spec} value={spec}>
                {spec}
              </option>
            ))}
          </select>
        </div>

        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-gray-600">Loading doctors...</p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <svg
                className="w-5 h-5 text-red-500 mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-red-700 font-medium">{error}</span>
            </div>
          </div>
        )}

        {!loading && !error && doctors.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl shadow-sm">
            <svg
              className="w-16 h-16 text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No doctors found</h3>
            <p className="text-gray-500">Try adjusting your search or filter criteria</p>
          </div>
        )}

        {!loading && !error && doctors.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {doctors.map((doctor) => (
              <div
                key={doctor.id}
                className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-100 overflow-hidden flex flex-col"
              >
                <div className="p-6 flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-bold text-gray-900 leading-tight">
                      Dr. {doctor.full_name}
                    </h3>
                    <span
                      className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold ${getSpecializationColor(
                        doctor.specialization
                      )}`}
                    >
                      {doctor.specialization}
                    </span>
                  </div>

                  {doctor.qualification && (
                    <p className="text-sm text-gray-600 mb-2 flex items-center">
                      <svg
                        className="w-4 h-4 mr-1.5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path d="M12 14l9-5-9-5-9 5 9 5z" />
                        <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                      </svg>
                      {doctor.qualification}
                    </p>
                  )}

                  <p className="text-sm text-gray-600 mb-2 flex items-center">
                    <svg
                      className="w-4 h-4 mr-1.5 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                    {doctor.experience_years} year{doctor.experience_years !== 1 ? 's' : ''} experience
                  </p>

                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-500">Consultation Fee</span>
                      <span className="text-lg font-bold text-primary-700">
                        {formatFee(doctor.consultation_fee)}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3">
                    <div className="flex items-center text-sm text-gray-600 mb-1">
                      <svg
                        className="w-4 h-4 mr-1.5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                      <span className="font-medium">Days:</span>&nbsp;
                      <span>{formatDays(doctor.available_days)}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <svg
                        className="w-4 h-4 mr-1.5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      <span className="font-medium">Hours:</span>&nbsp;
                      <span>
                        {doctor.start_time || 'N/A'} - {doctor.end_time || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 border-t border-gray-100 bg-gray-50">
                  <button
                    onClick={() => openBookingModal(doctor)}
                    className="w-full py-2.5 px-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors"
                  >
                    Book Appointment
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {modalOpen && selectedDoctor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={closeBookingModal}
          />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md z-10">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Book Appointment</h2>
                <button
                  onClick={closeBookingModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              <div className="bg-primary-50 rounded-lg p-4 mb-6">
                <p className="font-semibold text-gray-900">Dr. {selectedDoctor.full_name}</p>
                <p className="text-sm text-gray-600">{selectedDoctor.specialization}</p>
                <p className="text-sm font-medium text-primary-700 mt-1">
                  Consultation Fee: {formatFee(selectedDoctor.consultation_fee)}
                </p>
              </div>

              {bookingSuccess ? (
                <div className="text-center py-6">
                  <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
                    <svg
                      className="w-8 h-8 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Appointment Booked!
                  </h3>
                  <p className="text-gray-600">Redirecting to your appointments...</p>
                </div>
              ) : (
                <form onSubmit={handleBookAppointment}>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Appointment Date
                    </label>
                    <input
                      type="date"
                      min={getTodayStr()}
                      value={apptDate}
                      onChange={(e) => setApptDate(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Appointment Time
                    </label>
                    <input
                      type="time"
                      value={apptTime}
                      onChange={(e) => setApptTime(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
                    />
                  </div>

                  {bookingError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                      <p className="text-red-700 text-sm">{bookingError}</p>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={bookingLoading}
                    className="w-full py-2.5 px-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {bookingLoading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        Booking...
                      </>
                    ) : (
                      'Confirm Booking'
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Doctors;
