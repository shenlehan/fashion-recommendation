import { useState, useEffect } from 'react';
import { getUserWardrobe, uploadClothingItem, deleteClothingItem } from '../services/api';
import './Wardrobe.css';

function Wardrobe({ user }) {
  const [wardrobe, setWardrobe] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    name: '',
    file: null
  });

  useEffect(() => {
    fetchWardrobe();
  }, [user.id]);

  const fetchWardrobe = async () => {
    try {
      setLoading(true);
      const items = await getUserWardrobe(user.id);
      setWardrobe(items);
      setError('');
    } catch (err) {
      setError('Failed to load wardrobe');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    setUploadForm({
      ...uploadForm,
      file: e.target.files[0]
    });
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadForm.file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('name', uploadForm.name || uploadForm.file.name);

      await uploadClothingItem(user.id, formData);
      setUploadForm({ name: '', file: null });
      setShowUploadForm(false);
      fetchWardrobe(); // Refresh wardrobe
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload item');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm('Are you sure you want to delete this item?')) {
      return;
    }

    try {
      await deleteClothingItem(itemId);
      fetchWardrobe(); // Refresh wardrobe
    } catch (err) {
      setError('Failed to delete item');
    }
  };

  return (
    <div className="wardrobe-container">
      <div className="wardrobe-header">
        <h1>My Wardrobe</h1>
        <button
          className="btn-primary"
          onClick={() => setShowUploadForm(!showUploadForm)}
        >
          {showUploadForm ? 'Cancel' : '+ Add Item'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showUploadForm && (
        <div className="upload-form">
          <h2>Upload Clothing Item</h2>
          <form onSubmit={handleUploadSubmit}>
            <div className="form-group">
              <label htmlFor="name">Item Name</label>
              <input
                type="text"
                id="name"
                value={uploadForm.name}
                onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                placeholder="e.g., Blue Denim Jacket"
                disabled={uploading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="file">Upload Image *</label>
              <input
                type="file"
                id="file"
                accept="image/*"
                onChange={handleFileChange}
                required
                disabled={uploading}
              />
              {uploadForm.file && (
                <p className="file-preview">Selected: {uploadForm.file.name}</p>
              )}
            </div>

            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading ? 'Uploading...' : 'Upload Item'}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading wardrobe...</div>
      ) : wardrobe.length === 0 ? (
        <div className="empty-wardrobe">
          <p>Your wardrobe is empty. Start by adding your first clothing item!</p>
        </div>
      ) : (
        <div className="wardrobe-grid">
          {wardrobe.map((item) => (
            <div key={item.id} className="wardrobe-item">
              <div className="item-image">
                {item.image_path ? (
                  <img
                    src={`http://localhost:8000/${item.image_path}`}
                    alt={item.name}
                  />
                ) : (
                  <div className="no-image">No Image</div>
                )}
              </div>
              <div className="item-details">
                <h3>{item.name}</h3>
                <div className="item-info">
                  <span className="badge">{item.category || 'Unknown'}</span>
                  {item.color && <span className="badge color">{item.color}</span>}
                </div>
                {item.season && <p className="season">Season: {item.season}</p>}
                {item.material && <p className="material">Material: {item.material}</p>}
                <button
                  className="btn-delete"
                  onClick={() => handleDelete(item.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Wardrobe;
