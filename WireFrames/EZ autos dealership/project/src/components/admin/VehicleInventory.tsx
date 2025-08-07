import React, { useState, useEffect } from 'react';
import { Plus, Search, Edit2, Trash2, Car, Eye, DollarSign } from 'lucide-react';
import { getVehicles, createVehicle, updateVehicle, deleteVehicle } from '../../lib/api';
import { Vehicle } from '../../types';

const VehicleInventory: React.FC = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [formData, setFormData] = useState({
    make: '',
    model: '',
    year: new Date().getFullYear(),
    price: '',
    mileage: '',
    fuel_type: 'Gasoline',
    transmission: 'Automatic',
    color: '',
    image_url: '',
    description: '',
    featured: false,
    status: 'available',
    vin: '',
    engine: '',
    drivetrain: 'FWD',
    exterior_color: '',
    interior_color: '',
    mpg_city: '',
    mpg_highway: '',
    features: ''
  });

  const statuses = ['All', 'available', 'sold', 'pending', 'maintenance'];
  const fuelTypes = ['Gasoline', 'Diesel', 'Electric', 'Hybrid'];
  const transmissions = ['Automatic', 'Manual', 'CVT'];
  const drivetrains = ['FWD', 'RWD', 'AWD', '4WD'];

  useEffect(() => {
    fetchVehicles();
  }, []);

  const fetchVehicles = async () => {
    try {
      const data = await getVehicles();
      setVehicles(data);
    } catch (error) {
      console.error('Error fetching vehicles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const vehicleData = {
        ...formData,
        year: parseInt(formData.year.toString()),
        price: parseFloat(formData.price),
        mileage: parseInt(formData.mileage),
        mpg_city: formData.mpg_city ? parseInt(formData.mpg_city) : undefined,
        mpg_highway: formData.mpg_highway ? parseInt(formData.mpg_highway) : undefined,
        features: formData.features ? formData.features.split(',').map(f => f.trim()) : []
      };

      if (editingVehicle) {
        await updateVehicle(editingVehicle.id, vehicleData);
        setEditingVehicle(null);
      } else {
        await createVehicle(vehicleData);
        setShowAddModal(false);
      }
      
      resetForm();
      fetchVehicles();
    } catch (error) {
      console.error('Error saving vehicle:', error);
      alert('Error saving vehicle. Please try again.');
    }
  };

  const handleEdit = (vehicle: Vehicle) => {
    setEditingVehicle(vehicle);
    setFormData({
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year,
      price: vehicle.price.toString(),
      mileage: vehicle.mileage.toString(),
      fuel_type: vehicle.fuel_type || vehicle.fuelType || 'Gasoline',
      transmission: vehicle.transmission,
      color: vehicle.color,
      image_url: vehicle.image_url || vehicle.imageUrl || '',
      description: vehicle.description,
      featured: vehicle.featured,
      status: vehicle.status || 'available',
      vin: vehicle.vin || '',
      engine: vehicle.engine || '',
      drivetrain: vehicle.drivetrain || 'FWD',
      exterior_color: vehicle.exterior_color || vehicle.color,
      interior_color: vehicle.interior_color || '',
      mpg_city: vehicle.mpg_city?.toString() || '',
      mpg_highway: vehicle.mpg_highway?.toString() || '',
      features: vehicle.features?.join(', ') || ''
    });
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this vehicle?')) {
      try {
        await deleteVehicle(id);
        fetchVehicles();
      } catch (error) {
        console.error('Error deleting vehicle:', error);
        alert('Error deleting vehicle. Please try again.');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      make: '',
      model: '',
      year: new Date().getFullYear(),
      price: '',
      mileage: '',
      fuel_type: 'Gasoline',
      transmission: 'Automatic',
      color: '',
      image_url: '',
      description: '',
      featured: false,
      status: 'available',
      vin: '',
      engine: '',
      drivetrain: 'FWD',
      exterior_color: '',
      interior_color: '',
      mpg_city: '',
      mpg_highway: '',
      features: ''
    });
  };

  const filteredVehicles = vehicles.filter(vehicle => {
    const matchesSearch = 
      vehicle.make.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.year.toString().includes(searchTerm) ||
      (vehicle.vin && vehicle.vin.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = selectedStatus === 'All' || vehicle.status === selectedStatus;
    
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading vehicles...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Vehicle Inventory</h2>
        <div className="flex gap-4">
          <select
            className="border border-gray-300 rounded-md px-3 py-2"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            {statuses.map(status => (
              <option key={status} value={status}>
                {status === 'All' ? 'All Status' : status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search vehicles..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            <Plus size={20} />
            Add Vehicle
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Vehicle
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Details
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Price
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredVehicles.map((vehicle) => (
              <tr key={vehicle.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <img
                      className="h-16 w-24 object-cover rounded-md mr-4"
                      src={vehicle.image_url || vehicle.imageUrl}
                      alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
                    />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {vehicle.year} {vehicle.make} {vehicle.model}
                      </div>
                      <div className="text-sm text-gray-500">
                        VIN: {vehicle.vin || 'Not specified'}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {vehicle.mileage.toLocaleString()} miles
                  </div>
                  <div className="text-sm text-gray-500">
                    {vehicle.fuel_type || vehicle.fuelType} • {vehicle.transmission}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    ${vehicle.price.toLocaleString()}
                  </div>
                  {vehicle.featured && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Featured
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    vehicle.status === 'available' ? 'bg-green-100 text-green-800' :
                    vehicle.status === 'sold' ? 'bg-red-100 text-red-800' :
                    vehicle.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {vehicle.status || 'available'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button 
                    onClick={() => window.open(`/vehicle/${vehicle.id}`, '_blank')}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                    title="View Vehicle"
                  >
                    <Eye size={18} />
                  </button>
                  <button 
                    onClick={() => handleEdit(vehicle)}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                    title="Edit Vehicle"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button 
                    onClick={() => handleDelete(vehicle.id)}
                    className="text-red-600 hover:text-red-900"
                    title="Delete Vehicle"
                  >
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredVehicles.length === 0 && (
        <div className="text-center py-12">
          <Car size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 text-lg">No vehicles found</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
          >
            Add Your First Vehicle
          </button>
        </div>
      )}

      {/* Add/Edit Vehicle Modal */}
      {(showAddModal || editingVehicle) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingVehicle ? 'Edit Vehicle' : 'Add New Vehicle'}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Basic Information */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Make *</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.make}
                    onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Model *</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.model}
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Year *</label>
                  <input
                    type="number"
                    min="1900"
                    max={new Date().getFullYear() + 1}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.year}
                    onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Price *</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Mileage *</label>
                  <input
                    type="number"
                    min="0"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.mileage}
                    onChange={(e) => setFormData({ ...formData, mileage: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Fuel Type</label>
                  <select
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.fuel_type}
                    onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value })}
                  >
                    {fuelTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Transmission</label>
                  <select
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.transmission}
                    onChange={(e) => setFormData({ ...formData, transmission: e.target.value })}
                  >
                    {transmissions.map(trans => (
                      <option key={trans} value={trans}>{trans}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Color *</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.color}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">VIN</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.vin}
                    onChange={(e) => setFormData({ ...formData, vin: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Engine</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.engine}
                    onChange={(e) => setFormData({ ...formData, engine: e.target.value })}
                    placeholder="e.g., 2.0L Turbo"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Drivetrain</label>
                  <select
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.drivetrain}
                    onChange={(e) => setFormData({ ...formData, drivetrain: e.target.value })}
                  >
                    {drivetrains.map(drive => (
                      <option key={drive} value={drive}>{drive}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <select
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  >
                    {statuses.slice(1).map(status => (
                      <option key={status} value={status}>
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">City MPG</label>
                  <input
                    type="number"
                    min="0"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.mpg_city}
                    onChange={(e) => setFormData({ ...formData, mpg_city: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Highway MPG</label>
                  <input
                    type="number"
                    min="0"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.mpg_highway}
                    onChange={(e) => setFormData({ ...formData, mpg_highway: e.target.value })}
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Image URL</label>
                  <input
                    type="url"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.image_url}
                    onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                    placeholder="https://example.com/image.jpg"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Features (comma-separated)</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={formData.features}
                    onChange={(e) => setFormData({ ...formData, features: e.target.value })}
                    placeholder="Navigation, Leather Seats, Sunroof"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    rows={3}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Detailed description of the vehicle..."
                  />
                </div>

                <div className="md:col-span-2 flex items-center">
                  <input
                    type="checkbox"
                    id="featured"
                    checked={formData.featured}
                    onChange={(e) => setFormData({ ...formData, featured: e.target.checked })}
                    className="mr-2"
                  />
                  <label htmlFor="featured" className="text-sm text-gray-700">Featured Vehicle</label>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setEditingVehicle(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingVehicle ? 'Update Vehicle' : 'Add Vehicle'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleInventory;