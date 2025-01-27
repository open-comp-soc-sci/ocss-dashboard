FROM node:18-alpine
WORKDIR /app

COPY . ./
RUN npm init -y && npm install react react-dom vite @vitejs/plugin-react

EXPOSE 8001
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "8001"]
