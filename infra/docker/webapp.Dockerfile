# syntax=docker/dockerfile:1.6

# Optional frontend build stage. If a Node.js project exists in apps/admin,
# it will be built and served via Nginx. Otherwise a placeholder static page
# is generated so the container still starts successfully.

FROM node:20-alpine AS builder
WORKDIR /app
COPY apps/admin /app/apps/admin
WORKDIR /app/apps/admin
RUN if [ -f package.json ]; then \
      npm install && npm run build; \
    else \
      mkdir -p dist && \
      printf '<!DOCTYPE html>\n<html lang="en">\n<head><meta charset="utf-8"><title>Boost Admin</title></head>\n<body><h1>Boost Admin UI</h1><p>Build artifacts were not found. Provide a frontend project in apps/admin.</p></body>\n</html>' > dist/index.html; \
    fi

FROM nginx:1.27-alpine AS runner
COPY --from=builder /app/apps/admin/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
