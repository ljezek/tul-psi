# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Base URL must be set at build time for Vite
ARG VITE_BASE_URL=/projects/
ENV VITE_BASE_URL=$VITE_BASE_URL
RUN npm run build

# Serve stage
FROM nginx:alpine
# Copy the built files
COPY --from=build /app/dist /usr/share/nginx/html/projects
# Custom Nginx config to support React Router (SPA) and path-based serving
RUN echo 'server { \
    listen 80; \
    location /projects/ { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /projects/index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
