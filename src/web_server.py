"""Embedded web server for hybrid Qt + Web UI"""
from flask import Flask, jsonify, render_template_string
from threading import Thread
import logging

# Disable Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class WebServer:
    """Embedded Flask web server for gallery and other views"""
    
    def __init__(self, api_client, port=5555):
        self.api_client = api_client
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()
        self.server_thread = None
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>ImaLink Web UI</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background: #f5f5f5;
                        }
                        h1 { color: #333; }
                        .links {
                            display: flex;
                            gap: 20px;
                            margin-top: 30px;
                        }
                        .link-card {
                            background: white;
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            text-decoration: none;
                            color: #333;
                            transition: transform 0.2s;
                        }
                        .link-card:hover {
                            transform: translateY(-4px);
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        }
                    </style>
                </head>
                <body>
                    <h1>🌐 ImaLink Web UI</h1>
                    <p>Local web server running on port {{ port }}</p>
                    
                    <div class="links">
                        <a href="/gallery" class="link-card">
                            <h2>📷 Gallery</h2>
                            <p>Browse photos with full HTML/CSS</p>
                        </a>
                        <a href="/api/photos" class="link-card">
                            <h2>🔌 API</h2>
                            <p>Test API endpoints</p>
                        </a>
                    </div>
                </body>
                </html>
            """, port=self.port)
        
        @self.app.route('/gallery')
        def gallery():
            """Full HTML/CSS/JS gallery view"""
            return render_template_string(GALLERY_TEMPLATE)
        
        @self.app.route('/api/photos')
        def api_photos():
            """Proxy to backend API"""
            try:
                response = self.api_client.get_photos(limit=200)
                return jsonify(response)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/import-sessions')
        def api_import_sessions():
            """Proxy to backend API"""
            try:
                response = self.api_client.get_import_sessions(limit=100)
                return jsonify(response)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def start(self):
        """Start the web server in a background thread"""
        if self.server_thread and self.server_thread.is_alive():
            return  # Already running
        
        def run_server():
            self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print(f"✅ Web server started on http://127.0.0.1:{self.port}")
    
    def get_url(self, path=''):
        """Get URL for a path"""
        return f"http://127.0.0.1:{self.port}{path}"


# Gallery HTML Template with full functionality
GALLERY_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photo Gallery - ImaLink</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        header {
            margin-bottom: 30px;
        }
        
        h1 {
            color: #333;
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            align-items: center;
        }
        
        select, button {
            padding: 10px 20px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button {
            background: #667eea;
            color: white;
            font-weight: bold;
        }
        
        button:hover {
            background: #764ba2;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .stats {
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
            font-size: 18px;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            animation: fadeIn 0.5s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .photo-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .photo-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 12px 24px rgba(0,0,0,0.2);
        }
        
        .photo-image {
            width: 100%;
            height: 250px;
            object-fit: cover;
            background: linear-gradient(45deg, #f0f0f0 25%, #e0e0e0 25%, #e0e0e0 50%, #f0f0f0 50%, #f0f0f0 75%, #e0e0e0 75%, #e0e0e0);
            background-size: 20px 20px;
        }
        
        .photo-info {
            padding: 15px;
            background: linear-gradient(to bottom, #f8f9fa, white);
        }
        
        .photo-filename {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .photo-hash {
            font-size: 11px;
            color: #999;
            font-family: 'Courier New', monospace;
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        /* Modal for photo detail */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.active {
            display: flex;
        }
        
        .modal-content {
            max-width: 90%;
            max-height: 90%;
            position: relative;
        }
        
        .modal-image {
            max-width: 100%;
            max-height: 90vh;
            border-radius: 8px;
        }
        
        .modal-close {
            position: absolute;
            top: -40px;
            right: 0;
            color: white;
            font-size: 36px;
            cursor: pointer;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📷 Photo Gallery</h1>
            <p style="color: #666;">Web-based UI with full HTML/CSS/JavaScript</p>
        </header>
        
        <div class="controls">
            <label>Import Session:</label>
            <select id="sessionFilter">
                <option value="">All sessions</option>
            </select>
            <button onclick="loadPhotos()">🔄 Refresh</button>
        </div>
        
        <div class="stats" id="stats">Loading...</div>
        
        <div id="gallery" class="loading">
            Loading photos...
        </div>
    </div>
    
    <div class="modal" id="modal" onclick="closeModal()">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <img class="modal-image" id="modalImage" />
        </div>
    </div>
    
    <script>
        let photos = [];
        let sessions = [];
        
        // Load import sessions
        async function loadSessions() {
            try {
                const response = await fetch('/api/import-sessions');
                const data = await response.json();
                sessions = data.data || [];
                
                const select = document.getElementById('sessionFilter');
                select.innerHTML = '<option value="">All sessions</option>';
                
                sessions.forEach(session => {
                    const option = document.createElement('option');
                    option.value = session.id;
                    option.textContent = session.description || `Session ${session.id}`;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading sessions:', error);
            }
        }
        
        // Load photos
        async function loadPhotos() {
            const gallery = document.getElementById('gallery');
            gallery.className = 'loading';
            gallery.innerHTML = 'Loading photos...';
            
            try {
                const response = await fetch('/api/photos');
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                photos = data.data || [];
                
                // Debug: Log first photo structure
                if (photos.length > 0) {
                    console.log('Sample photo data:', photos[0]);
                    console.log('Available fields:', Object.keys(photos[0]));
                }
                
                displayPhotos(photos);
            } catch (error) {
                console.error('Error loading photos:', error);
                gallery.className = 'error';
                gallery.innerHTML = `Error loading photos: ${error.message}`;
            }
        }
        
        // Display photos
        function displayPhotos(photoList) {
            const gallery = document.getElementById('gallery');
            const stats = document.getElementById('stats');
            
            if (photoList.length === 0) {
                gallery.className = 'loading';
                gallery.innerHTML = '<p>No photos found. Import some photos to see them here.</p>';
                stats.textContent = 'No photos';
                return;
            }
            
            stats.textContent = `Showing ${photoList.length} photo(s)`;
            
            gallery.className = 'gallery';
            gallery.innerHTML = photoList.map((photo, index) => {
                const hothash = photo.photo_hothash || photo.hothash || `photo-${index}`;
                const filename = photo.filename || photo.original_filename || 'Unknown';
                const hotpreview = photo.hotpreview_base64 || photo.hotpreview || '';
                
                return `
                    <div class="photo-card" onclick="showPhotoDetail('${hothash}')">
                        <img class="photo-image" 
                             src="data:image/jpeg;base64,${hotpreview}" 
                             alt="${filename}"
                             loading="lazy"
                             onerror="this.style.display='none'" />
                        <div class="photo-info">
                            <div class="photo-filename" title="${filename}">
                                ${filename}
                            </div>
                            <div class="photo-hash">${hothash.substring(0, 16)}...</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        // Show photo detail modal
        function showPhotoDetail(hothash) {
            const photo = photos.find(p => 
                (p.photo_hothash === hothash) || 
                (p.hothash === hothash)
            );
            
            if (!photo) {
                console.warn('Photo not found:', hothash);
                return;
            }
            
            const modal = document.getElementById('modal');
            const modalImage = document.getElementById('modalImage');
            
            // Get hotpreview with fallbacks
            const hotpreview = photo.hotpreview_base64 || photo.hotpreview || '';
            if (hotpreview) {
                modalImage.src = `data:image/jpeg;base64,${hotpreview}`;
                modal.classList.add('active');
            } else {
                console.warn('No preview available for photo:', hothash);
            }
        }
        
        // Close modal
        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }
        
        // Filter by session
        document.getElementById('sessionFilter').addEventListener('change', (e) => {
            const sessionId = e.target.value;
            if (!sessionId) {
                displayPhotos(photos);
            } else {
                const filtered = photos.filter(p => p.import_session_id == sessionId);
                displayPhotos(filtered);
            }
        });
        
        // Initialize
        loadSessions();
        loadPhotos();
    </script>
</body>
</html>
"""
