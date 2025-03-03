FROM node:18-alpine
WORKDIR /app

# Copy only package.json first
COPY package.json ./
RUN npm install  # Install dependencies inside the container

# Copy the rest of your project files
COPY . ./

EXPOSE 8001
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "8001"]
