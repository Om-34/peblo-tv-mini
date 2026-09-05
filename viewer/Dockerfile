FROM node:22-alpine AS build
WORKDIR /app
COPY viewer/package.json viewer/package-lock.json* ./
RUN npm install
COPY viewer/ .
RUN npm run build
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY viewer/nginx.conf /etc/nginx/conf.d/default.conf
