# Rails File Upload Patterns

File upload patterns using Active Storage with S3.

---

## 1. Active Storage Setup

### Gemfile

```ruby
gem 'aws-sdk-s3', require: false
gem 'image_processing', '~> 1.2'
```

### Configuration

```yaml
# config/storage.yml
local:
  service: Disk
  root: <%= Rails.root.join("storage") %>

amazon:
  service: S3
  access_key_id: <%= ENV['AWS_ACCESS_KEY_ID'] %>
  secret_access_key: <%= ENV['AWS_SECRET_ACCESS_KEY'] %>
  region: <%= ENV['AWS_REGION'] %>
  bucket: <%= ENV['AWS_BUCKET'] %>
  public: false
```

```ruby
# config/environments/production.rb
config.active_storage.service = :amazon
```

---

## 2. Model with Attachments

```ruby
# frozen_string_literal: true

class User < ApplicationRecord
  has_one_attached :avatar do |attachable|
    attachable.variant :thumb, resize_to_limit: [100, 100]
    attachable.variant :medium, resize_to_limit: [300, 300]
  end

  validates :avatar, content_type: ['image/png', 'image/jpeg', 'image/webp'],
                     size: { less_than: 5.megabytes }
end

class Post < ApplicationRecord
  has_one_attached :featured_image do |attachable|
    attachable.variant :card, resize_to_fill: [400, 300]
    attachable.variant :hero, resize_to_limit: [1200, 600]
  end

  has_many_attached :attachments

  validates :featured_image, content_type: ['image/png', 'image/jpeg', 'image/webp'],
                              size: { less_than: 10.megabytes }
  validates :attachments, content_type: ['application/pdf', 'image/png', 'image/jpeg'],
                          size: { less_than: 25.megabytes },
                          limit: { max: 10 }
end
```

---

## 3. Custom Validator

```ruby
# frozen_string_literal: true

# Validates Active Storage attachments.
#
# @example
#   validates :avatar, content_type: ['image/png', 'image/jpeg'],
#                      size: { less_than: 5.megabytes }
#
class AttachmentValidator < ActiveModel::EachValidator
  def validate_each(record, attribute, value)
    return unless value.attached?

    validate_content_type(record, attribute, value)
    validate_size(record, attribute, value)
    validate_limit(record, attribute, value)
  end

  private

  def validate_content_type(record, attribute, value)
    return unless options[:content_type]

    allowed = Array(options[:content_type])
    attachments = value.is_a?(ActiveStorage::Attached::Many) ? value.blobs : [value.blob]

    attachments.each do |blob|
      unless allowed.include?(blob.content_type)
        record.errors.add(attribute, :invalid_content_type,
                          allowed: allowed.join(', '))
      end
    end
  end

  def validate_size(record, attribute, value)
    return unless options[:size]

    max_size = options[:size][:less_than]
    attachments = value.is_a?(ActiveStorage::Attached::Many) ? value.blobs : [value.blob]

    attachments.each do |blob|
      if blob.byte_size > max_size
        record.errors.add(attribute, :file_too_large,
                          max: ActiveSupport::NumberHelper.number_to_human_size(max_size))
      end
    end
  end

  def validate_limit(record, attribute, value)
    return unless options[:limit] && value.is_a?(ActiveStorage::Attached::Many)

    max = options[:limit][:max]
    if value.blobs.size > max
      record.errors.add(attribute, :too_many_files, max: max)
    end
  end
end
```

---

## 4. Direct Upload Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    class DirectUploadsController < ApplicationController
      def create
        blob = ActiveStorage::Blob.create_before_direct_upload!(
          **blob_params.merge(service_name: ActiveStorage::Blob.service.name)
        )

        render json: {
          signed_id: blob.signed_id,
          direct_upload: {
            url: blob.service_url_for_direct_upload,
            headers: blob.service_headers_for_direct_upload
          }
        }
      end

      private

      def blob_params
        params.require(:blob).permit(:filename, :byte_size, :checksum, :content_type)
      end
    end
  end
end
```

---

## 5. File Upload Service

```ruby
# frozen_string_literal: true

module Files
  class UploadService < ApplicationService
    ALLOWED_CONTENT_TYPES = {
      avatar: %w[image/jpeg image/png image/webp],
      document: %w[application/pdf],
      image: %w[image/jpeg image/png image/webp image/gif]
    }.freeze

    MAX_SIZES = {
      avatar: 5.megabytes,
      document: 25.megabytes,
      image: 10.megabytes
    }.freeze

    def initialize(record:, attachment_name:, file:, type: :image)
      @record = record
      @attachment_name = attachment_name
      @file = file
      @type = type
    end

    def call
      return failure(:no_file) unless file.present?
      return failure(:invalid_content_type) unless valid_content_type?
      return failure(:file_too_large) unless valid_size?

      record.public_send(attachment_name).attach(file)

      if record.save
        success(url: url_for_attachment)
      else
        failure(:save_failed, errors: record.errors.full_messages)
      end
    end

    private

    attr_reader :record, :attachment_name, :file, :type

    def valid_content_type?
      ALLOWED_CONTENT_TYPES[type].include?(file.content_type)
    end

    def valid_size?
      file.size <= MAX_SIZES[type]
    end

    def url_for_attachment
      attachment = record.public_send(attachment_name)
      Rails.application.routes.url_helpers.url_for(attachment)
    end
  end
end
```

---

## 6. Image Processing

```ruby
# frozen_string_literal: true

module Files
  class ImageProcessorService < ApplicationService
    def initialize(blob:, transformations:)
      @blob = blob
      @transformations = transformations
    end

    def call
      processed = blob.variant(transformations).processed
      success(variant: processed)
    rescue ActiveStorage::InvariableError
      failure(:not_an_image)
    rescue MiniMagick::Error => e
      failure(:processing_failed, error: e.message)
    end

    private

    attr_reader :blob, :transformations
  end
end

# Usage
Files::ImageProcessorService.call(
  blob: user.avatar.blob,
  transformations: { resize_to_limit: [800, 800], format: :webp }
)
```

---

## 7. Signed URLs

```ruby
# frozen_string_literal: true

class AttachmentSerializer
  def initialize(attachment)
    @attachment = attachment
  end

  def as_json
    return nil unless attachment.attached?

    {
      url: signed_url,
      filename: attachment.filename.to_s,
      content_type: attachment.content_type,
      byte_size: attachment.byte_size,
      variants: variants
    }
  end

  private

  attr_reader :attachment

  def signed_url
    Rails.application.routes.url_helpers.rails_blob_url(
      attachment,
      disposition: 'inline',
      expires_in: 1.hour
    )
  end

  def variants
    return {} unless attachment.representable?

    {
      thumb: variant_url(:thumb),
      medium: variant_url(:medium)
    }
  end

  def variant_url(name)
    Rails.application.routes.url_helpers.rails_representation_url(
      attachment.variant(name),
      expires_in: 1.hour
    )
  end
end
```

---

## 8. Bulk Upload

```ruby
# frozen_string_literal: true

module Api
  module V1
    class BulkUploadsController < ApplicationController
      def create
        results = params[:files].map do |file|
          upload_result(file)
        end

        successful = results.select { |r| r[:success] }
        failed = results.reject { |r| r[:success] }

        render json: {
          successful: successful,
          failed: failed,
          total: results.size,
          success_count: successful.size,
          failure_count: failed.size
        }
      end

      private

      def upload_result(file)
        blob = ActiveStorage::Blob.create_and_upload!(
          io: file,
          filename: file.original_filename,
          content_type: file.content_type
        )

        {
          success: true,
          filename: file.original_filename,
          signed_id: blob.signed_id,
          url: url_for(blob)
        }
      rescue StandardError => e
        {
          success: false,
          filename: file.original_filename,
          error: e.message
        }
      end
    end
  end
end
```

---

## 9. Cleanup Job

```ruby
# frozen_string_literal: true

class CleanupUnattachedBlobsJob < ApplicationJob
  queue_as :low

  def perform
    # Delete blobs that are not attached to any record
    # and were created more than 24 hours ago
    ActiveStorage::Blob
      .unattached
      .where('created_at < ?', 24.hours.ago)
      .find_each(&:purge_later)
  end
end
```

---

## 10. Testing Uploads

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe User do
  describe 'avatar' do
    let(:user) { create(:user) }

    it 'attaches an avatar' do
      user.avatar.attach(
        io: File.open(Rails.root.join('spec/fixtures/files/avatar.jpg')),
        filename: 'avatar.jpg',
        content_type: 'image/jpeg'
      )

      expect(user.avatar).to be_attached
    end

    it 'validates content type' do
      user.avatar.attach(
        io: File.open(Rails.root.join('spec/fixtures/files/document.pdf')),
        filename: 'document.pdf',
        content_type: 'application/pdf'
      )

      expect(user).not_to be_valid
      expect(user.errors[:avatar]).to include('has an invalid content type')
    end

    it 'validates file size' do
      user.avatar.attach(
        io: StringIO.new('x' * 10.megabytes),
        filename: 'large.jpg',
        content_type: 'image/jpeg'
      )

      expect(user).not_to be_valid
      expect(user.errors[:avatar]).to include('is too large')
    end
  end
end

# spec/support/active_storage.rb
RSpec.configure do |config|
  config.after(:each) do
    FileUtils.rm_rf(ActiveStorage::Blob.service.root)
  end
end
```
