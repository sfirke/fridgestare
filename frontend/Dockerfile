FROM node:22-alpine

WORKDIR /app

# Copy the lockfile and install from it. Without this the image resolved fresh
# versions on every build, so what ran in Compose could drift from CI.
COPY frontend/package.json frontend/package-lock.json /app/
RUN npm ci

COPY frontend /app

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
