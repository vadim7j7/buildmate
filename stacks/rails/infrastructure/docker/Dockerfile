# syntax=docker/dockerfile:1

# Multi-stage build for Ruby on Rails

ARG RUBY_VERSION=3.3
FROM ruby:${RUBY_VERSION}-slim AS base

WORKDIR /rails

# Set production environment
ENV RAILS_ENV="production" \
    BUNDLE_DEPLOYMENT="1" \
    BUNDLE_PATH="/usr/local/bundle" \
    BUNDLE_WITHOUT="development:test"

# Install base packages
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    curl \
    libpq5 \
    libjemalloc2 \
    libvips && \
    rm -rf /var/lib/apt/lists /var/cache/apt/archives

# ============================================
# Build stage
# ============================================
FROM base AS build

# Install build dependencies
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    build-essential \
    git \
    libpq-dev \
    pkg-config && \
    rm -rf /var/lib/apt/lists /var/cache/apt/archives

# Install gems
COPY Gemfile Gemfile.lock ./
RUN bundle install && \
    rm -rf ~/.bundle/ "${BUNDLE_PATH}"/ruby/*/cache "${BUNDLE_PATH}"/ruby/*/bundler/gems/*/.git && \
    bundle exec bootsnap precompile --gemfile

# Copy application code
COPY . .

# Precompile bootsnap code for faster boot times
RUN bundle exec bootsnap precompile app/ lib/

# Precompile assets for production (if using assets)
# RUN SECRET_KEY_BASE_DUMMY=1 ./bin/rails assets:precompile

# ============================================
# Production stage
# ============================================
FROM base

# Copy built artifacts
COPY --from=build /usr/local/bundle /usr/local/bundle
COPY --from=build /rails /rails

# Create non-root user for security
RUN useradd rails --create-home --shell /bin/bash && \
    chown -R rails:rails db log storage tmp
USER rails:rails

# Configure jemalloc for better memory management
ENV LD_PRELOAD="libjemalloc.so.2" \
    MALLOC_CONF="dirty_decay_ms:1000,narenas:2,background_thread:true"

# Entrypoint prepares database
ENTRYPOINT ["/rails/bin/docker-entrypoint"]

# Start the server
EXPOSE 3000
CMD ["./bin/rails", "server", "-b", "0.0.0.0"]
