FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the project files
COPY . ./

# Build the app
RUN npm run build

# Final image - just nginx serving static files
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80