FROM node:20-alpine
WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies and verify vite is installed
RUN npm install && npm ls vite

# Copy the rest of your project files
COPY . ./

EXPOSE 8001

# Use the dev script defined in package.json
CMD ["npm", "run", "dev"]
