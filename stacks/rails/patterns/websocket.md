# Rails WebSocket Patterns

Real-time communication patterns using Action Cable.

---

## 1. Action Cable Setup

### Cable Configuration

```ruby
# config/cable.yml
development:
  adapter: redis
  url: redis://localhost:6379/1

test:
  adapter: test

production:
  adapter: redis
  url: <%= ENV['REDIS_URL'] %>
  channel_prefix: myapp_production
```

### Application Cable

```ruby
# app/channels/application_cable/connection.rb
# frozen_string_literal: true

module ApplicationCable
  class Connection < ActionCable::Connection::Base
    identified_by :current_user

    def connect
      self.current_user = find_verified_user
    end

    private

    def find_verified_user
      if (user = User.find_by(id: decoded_token['sub']))
        user
      else
        reject_unauthorized_connection
      end
    end

    def decoded_token
      token = request.params[:token] || request.headers['Authorization']&.split(' ')&.last
      JWT.decode(token, Rails.application.secret_key_base, true, algorithm: 'HS256').first
    rescue JWT::DecodeError
      reject_unauthorized_connection
    end
  end
end
```

---

## 2. Channel Patterns

### User Channel (Private)

```ruby
# frozen_string_literal: true

class UserChannel < ApplicationCable::Channel
  def subscribed
    stream_for current_user
  end

  def unsubscribed
    stop_all_streams
  end
end

# Broadcast to user
UserChannel.broadcast_to(user, {
  type: 'notification',
  data: { message: 'You have a new message' }
})
```

### Room Channel (Group)

```ruby
# frozen_string_literal: true

class RoomChannel < ApplicationCable::Channel
  def subscribed
    @room = Room.find(params[:room_id])

    return reject unless can_access?(@room)

    stream_for @room
    broadcast_user_joined
  end

  def unsubscribed
    broadcast_user_left if @room
  end

  def speak(data)
    message = @room.messages.create!(
      user: current_user,
      content: data['message']
    )

    RoomChannel.broadcast_to(@room, {
      type: 'message',
      data: MessageSerializer.new(message).as_json
    })
  end

  def typing
    RoomChannel.broadcast_to(@room, {
      type: 'typing',
      data: { user_id: current_user.id, name: current_user.name }
    })
  end

  private

  def can_access?(room)
    room.users.include?(current_user)
  end

  def broadcast_user_joined
    RoomChannel.broadcast_to(@room, {
      type: 'user_joined',
      data: { user_id: current_user.id, name: current_user.name }
    })
  end

  def broadcast_user_left
    RoomChannel.broadcast_to(@room, {
      type: 'user_left',
      data: { user_id: current_user.id }
    })
  end
end
```

### Presence Channel

```ruby
# frozen_string_literal: true

class PresenceChannel < ApplicationCable::Channel
  def subscribed
    stream_from 'presence'
    update_presence(:online)
    broadcast_presence_list
  end

  def unsubscribed
    update_presence(:offline)
    broadcast_presence_list
  end

  def update_status(data)
    update_presence(data['status'].to_sym)
    broadcast_presence_list
  end

  private

  def update_presence(status)
    Redis.current.hset(
      'user_presence',
      current_user.id,
      { status: status, last_seen: Time.current }.to_json
    )

    if status == :offline
      Redis.current.hdel('user_presence', current_user.id)
    end
  end

  def broadcast_presence_list
    presence = Redis.current.hgetall('user_presence').transform_values { |v| JSON.parse(v) }
    ActionCable.server.broadcast('presence', { type: 'presence_update', data: presence })
  end
end
```

---

## 3. Broadcasting from Models

```ruby
# frozen_string_literal: true

class Message < ApplicationRecord
  belongs_to :room
  belongs_to :user

  after_create_commit :broadcast_message
  after_update_commit :broadcast_update
  after_destroy_commit :broadcast_deletion

  private

  def broadcast_message
    RoomChannel.broadcast_to(room, {
      type: 'message',
      data: MessageSerializer.new(self).as_json
    })
  end

  def broadcast_update
    RoomChannel.broadcast_to(room, {
      type: 'message_updated',
      data: MessageSerializer.new(self).as_json
    })
  end

  def broadcast_deletion
    RoomChannel.broadcast_to(room, {
      type: 'message_deleted',
      data: { id: id }
    })
  end
end
```

---

## 4. Background Job Broadcasting

```ruby
# frozen_string_literal: true

class NotifyUserJob < ApplicationJob
  queue_as :default

  def perform(user_id, notification_data)
    user = User.find(user_id)

    UserChannel.broadcast_to(user, {
      type: 'notification',
      data: notification_data
    })
  end
end

# Usage
NotifyUserJob.perform_later(user.id, {
  title: 'New follower',
  message: "#{follower.name} started following you",
  url: profile_path(follower)
})
```

---

## 5. Rate Limiting

```ruby
# frozen_string_literal: true

class RateLimitedChannel < ApplicationCable::Channel
  RATE_LIMIT = 10 # messages per window
  RATE_WINDOW = 60 # seconds

  def speak(data)
    return reject_rate_limited unless within_rate_limit?

    increment_message_count
    process_message(data)
  end

  private

  def within_rate_limit?
    message_count < RATE_LIMIT
  end

  def message_count
    Redis.current.get(rate_limit_key).to_i
  end

  def increment_message_count
    key = rate_limit_key
    Redis.current.multi do |multi|
      multi.incr(key)
      multi.expire(key, RATE_WINDOW)
    end
  end

  def rate_limit_key
    "rate_limit:#{current_user.id}:#{self.class.name}"
  end

  def reject_rate_limited
    transmit({ type: 'error', message: 'Rate limit exceeded' })
  end
end
```

---

## 6. API Endpoint for WebSocket URL

```ruby
# frozen_string_literal: true

module Api
  module V1
    class WebsocketController < ApplicationController
      def config
        render json: {
          url: ActionCable.server.config.url,
          token: generate_ws_token
        }
      end

      private

      def generate_ws_token
        JWT.encode(
          { sub: current_user.id, exp: 1.hour.from_now.to_i },
          Rails.application.secret_key_base,
          'HS256'
        )
      end
    end
  end
end
```

---

## 7. Service Object for Broadcasting

```ruby
# frozen_string_literal: true

module Realtime
  class BroadcastService < ApplicationService
    def initialize(channel:, stream:, event_type:, data:)
      @channel = channel
      @stream = stream
      @event_type = event_type
      @data = data
    end

    def call
      channel.broadcast_to(stream, payload)
      success
    rescue StandardError => e
      failure(:broadcast_failed, error: e.message)
    end

    private

    attr_reader :channel, :stream, :event_type, :data

    def payload
      {
        type: event_type,
        data: data,
        timestamp: Time.current.iso8601
      }
    end
  end
end

# Usage
Realtime::BroadcastService.call(
  channel: RoomChannel,
  stream: room,
  event_type: 'message',
  data: message_data
)
```

---

## 8. Testing Channels

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe RoomChannel, type: :channel do
  let(:user) { create(:user) }
  let(:room) { create(:room, users: [user]) }

  before do
    stub_connection current_user: user
  end

  describe '#subscribed' do
    it 'subscribes to the room stream' do
      subscribe(room_id: room.id)

      expect(subscription).to be_confirmed
      expect(subscription).to have_stream_for(room)
    end

    it 'rejects subscription without access' do
      other_room = create(:room)

      subscribe(room_id: other_room.id)

      expect(subscription).to be_rejected
    end
  end

  describe '#speak' do
    before { subscribe(room_id: room.id) }

    it 'creates a message and broadcasts it' do
      expect {
        perform :speak, message: 'Hello!'
      }.to change(Message, :count).by(1)
        .and have_broadcasted_to(room).with(hash_including(type: 'message'))
    end
  end
end

RSpec.describe 'RoomChannel integration', type: :system do
  let(:user) { create(:user) }
  let(:room) { create(:room, users: [user]) }

  before do
    driven_by :selenium_chrome_headless
    sign_in user
  end

  it 'receives messages in real-time' do
    visit room_path(room)

    # Simulate another user sending a message
    other_user = create(:user)
    room.users << other_user
    room.messages.create!(user: other_user, content: 'Hello from other user!')

    expect(page).to have_content('Hello from other user!')
  end
end
```

---

## 9. Connection Health Check

```ruby
# frozen_string_literal: true

class HeartbeatChannel < ApplicationCable::Channel
  HEARTBEAT_INTERVAL = 30.seconds

  def subscribed
    stream_from "heartbeat_#{current_user.id}"
    start_heartbeat
  end

  def unsubscribed
    stop_heartbeat
  end

  def pong
    update_last_seen
  end

  private

  def start_heartbeat
    @heartbeat_timer = every(HEARTBEAT_INTERVAL) do
      transmit({ type: 'ping' })
    end
  end

  def stop_heartbeat
    @heartbeat_timer&.cancel
  end

  def update_last_seen
    current_user.touch(:last_seen_at)
  end

  def every(interval, &block)
    Thread.new do
      loop do
        sleep interval
        block.call
      end
    end
  end
end
```

---

## 10. Scaling Considerations

```ruby
# config/initializers/action_cable.rb

# Use Redis for pub/sub across multiple servers
Rails.application.config.action_cable.mount_path = '/cable'

# Configure allowed origins
Rails.application.config.action_cable.allowed_request_origins = [
  /https:\/\/.*\.example\.com/,
  'http://localhost:3000'
]

# Configure connection timeout
Rails.application.config.action_cable.worker_pool_size = ENV.fetch('CABLE_POOL_SIZE', 4).to_i

# Health check endpoint
Rails.application.config.action_cable.health_check_path = '/cable/health'
```
