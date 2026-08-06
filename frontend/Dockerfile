# Static serve only — the frontend has no build step or server logic.
# Unprivileged variant: runs as non-root by default, listens on 8080.
FROM nginxinc/nginx-unprivileged:1.27.3-alpine

COPY index.html app.js styles.css /usr/share/nginx/html/

EXPOSE 8080
