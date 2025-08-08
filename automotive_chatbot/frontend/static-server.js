const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const PUBLIC_DIR = path.join(__dirname, 'public');

console.log('🚀 Starting CleverCompanion Static Server...');
console.log(`📁 Serving from: ${PUBLIC_DIR}`);

// MIME types for proper content serving
const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject'
};

const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    
    // Enable CORS for all requests
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // Handle preflight requests
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    // Parse URL and determine file path
    let urlPath = req.url;
    if (urlPath === '/') {
        urlPath = '/clevercompanion.html'; // Default to main page
    }
    
    let filePath = path.join(PUBLIC_DIR, urlPath);
    
    // Security check - prevent directory traversal
    if (!filePath.startsWith(PUBLIC_DIR)) {
        res.writeHead(403, { 'Content-Type': 'text/plain' });
        res.end('403 Forbidden - Access denied');
        return;
    }
    
    // Get file extension and MIME type
    const extname = String(path.extname(filePath)).toLowerCase();
    const mimeType = mimeTypes[extname] || 'application/octet-stream';
    
    // Try to read and serve the file
    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                // File not found - try adding .html extension
                if (!extname && !filePath.endsWith('.html')) {
                    const htmlPath = filePath + '.html';
                    fs.readFile(htmlPath, (htmlError, htmlContent) => {
                        if (htmlError) {
                            // Still not found - return 404
                            res.writeHead(404, { 'Content-Type': 'text/html' });
                            res.end(`
                                <!DOCTYPE html>
                                <html>
                                <head><title>404 - Page Not Found</title></head>
                                <body>
                                    <h1>404 - Page Not Found</h1>
                                    <p>The requested file <code>${req.url}</code> was not found.</p>
                                    <p>Available pages:</p>
                                    <ul>
                                        <li><a href="/clevercompanion.html">CleverCompanion Main Page</a></li>
                                        <li><a href="/dashboard.html">Admin Dashboard</a></li>
                                    </ul>
                                </body>
                                </html>
                            `);
                        } else {
                            // Found with .html extension
                            res.writeHead(200, { 'Content-Type': 'text/html' });
                            res.end(htmlContent, 'utf-8');
                        }
                    });
                } else {
                    // File not found and no .html fallback
                    res.writeHead(404, { 'Content-Type': 'text/html' });
                    res.end(`
                        <!DOCTYPE html>
                        <html>
                        <head><title>404 - Page Not Found</title></head>
                        <body>
                            <h1>404 - Page Not Found</h1>
                            <p>The requested file <code>${req.url}</code> was not found.</p>
                            <p>Available pages:</p>
                            <ul>
                                <li><a href="/clevercompanion.html">CleverCompanion Main Page</a></li>
                                <li><a href="/dashboard.html">Admin Dashboard</a></li>
                            </ul>
                        </body>
                        </html>
                    `);
                }
            } else {
                // Server error
                console.error('Server error:', error);
                res.writeHead(500, { 'Content-Type': 'text/plain' });
                res.end('500 Internal Server Error: ' + error.code);
            }
        } else {
            // File found and read successfully
            res.writeHead(200, { 'Content-Type': mimeType });
            res.end(content, 'utf-8');
        }
    });
});

// Start the server
server.listen(PORT, 'localhost', () => {
    console.log('');
    console.log('🎉 CleverCompanion Static Server is running!');
    console.log('');
    console.log('📱 Access Points:');
    console.log(`   🌐 Main Page:    http://localhost:${PORT}/`);
    console.log(`   🌐 Main Page:    http://localhost:${PORT}/clevercompanion.html`);
    console.log(`   📊 Dashboard:    http://localhost:${PORT}/dashboard.html`);
    console.log(`   🔧 Widget JS:    http://localhost:${PORT}/clevercompanion-widget.js`);
    console.log(`   🎨 Widget CSS:   http://localhost:${PORT}/clevercompanion-widget.css`);
    console.log('');
    console.log('✅ Server ready to accept connections!');
    console.log('');
});

// Handle server errors
server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`❌ Port ${PORT} is already in use!`);
        console.error('   Try killing existing processes:');
        console.error('   npm run kill-ports');
        console.error('   Or use a different port.');
    } else {
        console.error('❌ Server error:', err);
    }
    process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down server...');
    server.close(() => {
        console.log('✅ Server closed successfully');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM, shutting down...');
    server.close(() => {
        console.log('✅ Server closed successfully');
        process.exit(0);
    });
}); 