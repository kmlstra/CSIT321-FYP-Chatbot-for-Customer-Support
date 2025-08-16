const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const PUBLIC_DIR = path.join(__dirname, 'public');

// Starting CleverCompanion Static Server
// Serving from public directory

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
    // Request logging removed
    
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
                // Server error
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
server.listen(PORT, '0.0.0.0', () => {
    // Server started successfully
    // Access points available:
    // - Main Page: http://localhost:PORT/
    // - Dashboard: http://localhost:PORT/dashboard.html
    // - Widget JS: http://localhost:PORT/clevercompanion-widget.js
});

// Handle server errors
server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        // Port is already in use
        // Try killing existing processes:
        // npm run kill-ports
        // Or use a different port.
    } else {
        // Server error
    }
    process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
    // Shutting down server
    server.close(() => {
        // Server closed successfully
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    // Received SIGTERM, shutting down
    server.close(() => {
        // Server closed successfully
        process.exit(0);
    });
});