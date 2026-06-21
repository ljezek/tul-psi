# Static SPA build, served by nginx. Built once per environment from the same commit:
# the VITE_* build args differ between prod and dev (base path, API URL, cookie name), so
# the frontend image carries its environment baked in. The edge proxy strips the public
# base prefix (e.g. /projects or /dev/projects) before forwarding, so nginx serves from
# the document root and the SPA fallback handles client-side routing.
#
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Per-environment configuration, baked at build time by Vite.
ARG VITE_BASE_URL=/projects/
ARG VITE_API_URL=
ARG VITE_APP_ENV=prod
ARG VITE_XSRF_COOKIE_NAME=XSRF-TOKEN
ENV VITE_BASE_URL=$VITE_BASE_URL \
    VITE_API_URL=$VITE_API_URL \
    VITE_APP_ENV=$VITE_APP_ENV \
    VITE_XSRF_COOKIE_NAME=$VITE_XSRF_COOKIE_NAME
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# SPA fallback. The edge proxy has already stripped the public base prefix, so assets and
# routes resolve from the document root.
RUN printf 'server {\n\
    listen 80;\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
