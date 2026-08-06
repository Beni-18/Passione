# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
# Run clean install bypassing peer-dep warnings
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build

# Stage 2: Serve the built application with Nginx (unprivileged)
FROM nginxinc/nginx-unprivileged:1.27.3-alpine

# Copy built files from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html/

EXPOSE 8080
