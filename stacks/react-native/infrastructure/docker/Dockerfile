# syntax=docker/dockerfile:1

# React Native development container
# Note: Production builds use EAS Build, not Docker

ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    watchman \
    && rm -rf /var/lib/apt/lists/*

# Install Expo CLI globally
RUN npm install -g expo-cli eas-cli

# Create non-root user
RUN useradd -ms /bin/bash developer
RUN chown -R developer:developer /app

USER developer

# Copy package files
COPY --chown=developer:developer package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY --chown=developer:developer . .

# Expose Expo ports
# Metro bundler
EXPOSE 8081
# Expo DevTools
EXPOSE 19000
EXPOSE 19001
EXPOSE 19002

# Default command
CMD ["npm", "start"]
