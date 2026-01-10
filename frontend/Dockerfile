FROM nginx:alpine

# Copy custom nginx configuration
COPY ../nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend files
COPY index.html /usr/share/nginx/html/

# Expose port
EXPOSE 1919

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
