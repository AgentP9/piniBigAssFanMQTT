FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend files
COPY frontend/index.html /usr/share/nginx/html/
COPY frontend/manifest.json /usr/share/nginx/html/
COPY frontend/sw.js /usr/share/nginx/html/
COPY frontend/favicon.ico /usr/share/nginx/html/
COPY frontend/icons /usr/share/nginx/html/icons/

# Expose port
EXPOSE 1919

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
