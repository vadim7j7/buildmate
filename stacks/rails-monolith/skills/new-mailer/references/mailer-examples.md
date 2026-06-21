# ActionMailer Examples

Reference examples for generating mailers.

## ApplicationMailer Base

```ruby
# frozen_string_literal: true

# Base mailer class that all mailers inherit from.
#
class ApplicationMailer < ActionMailer::Base
  default from: 'notifications@example.com'
  layout 'mailer'

  private

  # Helper to generate unsubscribe URL for email footers
  def unsubscribe_url(user)
    email_preferences_url(token: user.email_token)
  end
end
```

## UserMailer

```ruby
# frozen_string_literal: true

# Sends transactional emails to users.
#
# @example Send welcome email
#   UserMailer.welcome(@user).deliver_later
#
class UserMailer < ApplicationMailer
  # Sends a welcome email to a newly registered user.
  #
  # @param user [User] the user to welcome
  # @return [Mail::Message] the email message
  def welcome(user)
    @user = user
    @login_url = new_session_url

    mail(
      to: @user.email,
      subject: t('.subject', name: @user.name)
    )
  end

  # Sends a password reset email.
  #
  # @param user [User] the user requesting reset
  # @return [Mail::Message] the email message
  def password_reset(user)
    @user = user
    @reset_url = edit_password_reset_url(@user.password_reset_token)

    mail(
      to: @user.email,
      subject: t('.subject')
    )
  end

  # Sends email confirmation email.
  #
  # @param user [User] the user to confirm
  # @return [Mail::Message] the email message
  def email_confirmation(user)
    @user = user
    @confirmation_url = confirm_email_url(token: @user.confirmation_token)

    mail(
      to: @user.unconfirmed_email || @user.email,
      subject: t('.subject')
    )
  end
end
```

## OrderMailer with Attachments

```ruby
# frozen_string_literal: true

# Sends order-related emails to customers.
#
class OrderMailer < ApplicationMailer
  # Sends order confirmation with invoice PDF.
  #
  # @param order [Order] the completed order
  # @return [Mail::Message] the email message
  def confirmation(order)
    @order = order
    @user = order.user

    # Generate and attach invoice PDF
    invoice_pdf = InvoiceGenerator.call(order: order)
    attachments["invoice-#{order.number}.pdf"] = invoice_pdf

    mail(
      to: @user.email,
      subject: t('.subject', order_number: order.number)
    )
  end

  # Sends shipping notification.
  #
  # @param order [Order] the shipped order
  # @return [Mail::Message] the email message
  def shipped(order)
    @order = order
    @user = order.user
    @tracking_url = order.tracking_url

    mail(
      to: @user.email,
      subject: t('.subject', order_number: order.number)
    )
  end

  # Sends delivery confirmation.
  #
  # @param order [Order] the delivered order
  # @return [Mail::Message] the email message
  def delivered(order)
    @order = order
    @user = order.user
    @review_url = new_order_review_url(order)

    mail(
      to: @user.email,
      subject: t('.subject')
    )
  end
end
```

## HTML Email View

```erb
<!-- app/views/user_mailer/welcome.html.erb -->
<h1><%= t('.greeting', name: @user.name) %></h1>

<p><%= t('.intro') %></p>

<p>
  <%= link_to t('.cta'), @login_url, class: 'button' %>
</p>

<h2><%= t('.getting_started') %></h2>

<ul>
  <li><%= t('.step_1') %></li>
  <li><%= t('.step_2') %></li>
  <li><%= t('.step_3') %></li>
</ul>

<p><%= t('.signature') %></p>
```

## Text Email View

```erb
<%# app/views/user_mailer/welcome.text.erb %>
<%= t('.greeting', name: @user.name) %>

<%= t('.intro') %>

<%= t('.cta') %>: <%= @login_url %>

<%= t('.getting_started') %>

1. <%= t('.step_1') %>
2. <%= t('.step_2') %>
3. <%= t('.step_3') %>

<%= t('.signature') %>
```

## Mailer Layout

```erb
<!-- app/views/layouts/mailer.html.erb -->
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
      }
      .button {
        display: inline-block;
        padding: 12px 24px;
        background-color: #0066cc;
        color: white;
        text-decoration: none;
        border-radius: 4px;
      }
      .footer {
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #eee;
        font-size: 12px;
        color: #666;
      }
    </style>
  </head>
  <body>
    <%= yield %>

    <div class="footer">
      <p>&copy; <%= Date.current.year %> <%= Rails.application.config.app_name %></p>
    </div>
  </body>
</html>
```

## I18n Translations

```yaml
# config/locales/mailers.en.yml
en:
  user_mailer:
    welcome:
      subject: "Welcome to %{name}!"
      greeting: "Hello %{name},"
      intro: "Thank you for signing up. We're excited to have you!"
      cta: "Get Started"
      getting_started: "Here's how to get started:"
      step_1: "Complete your profile"
      step_2: "Explore the dashboard"
      step_3: "Connect with your team"
      signature: "Best regards,\nThe Team"
    password_reset:
      subject: "Password Reset Request"
    email_confirmation:
      subject: "Please confirm your email"

  order_mailer:
    confirmation:
      subject: "Order Confirmed: %{order_number}"
    shipped:
      subject: "Your order %{order_number} has shipped!"
    delivered:
      subject: "Your order has been delivered!"
```

## Mailer Preview

```ruby
# frozen_string_literal: true

# Preview user emails at http://localhost:3000/rails/mailers/user_mailer
class UserMailerPreview < ActionMailer::Preview
  def welcome
    user = User.first || FactoryBot.build(:user, name: 'Preview User')
    UserMailer.welcome(user)
  end

  def password_reset
    user = User.first || FactoryBot.build(:user, password_reset_token: 'abc123')
    UserMailer.password_reset(user)
  end

  def email_confirmation
    user = User.first || FactoryBot.build(:user, confirmation_token: 'xyz789')
    UserMailer.email_confirmation(user)
  end
end
```

## Mailer Spec

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe UserMailer do
  describe '#welcome' do
    let(:user) { create(:user, name: 'John Doe', email: 'john@example.com') }
    let(:mail) { described_class.welcome(user) }

    it 'renders the headers' do
      expect(mail.to).to eq(['john@example.com'])
      expect(mail.from).to eq(['notifications@example.com'])
      expect(mail.subject).to include('Welcome')
    end

    it 'renders the body with user name' do
      expect(mail.body.encoded).to include('John Doe')
    end

    it 'includes login URL' do
      expect(mail.body.encoded).to include(new_session_url)
    end

    it 'has both HTML and text parts' do
      expect(mail.parts.map(&:content_type)).to include(
        a_string_matching(/text\/html/),
        a_string_matching(/text\/plain/)
      )
    end
  end

  describe '#password_reset' do
    let(:user) { create(:user, password_reset_token: 'reset123') }
    let(:mail) { described_class.password_reset(user) }

    it 'includes reset URL with token' do
      expect(mail.body.encoded).to include('reset123')
    end
  end
end
```

## Spec with Delivery Test

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'User registration email' do
  it 'sends welcome email after registration' do
    expect {
      User.create!(email: 'new@example.com', password: 'password123')
    }.to have_enqueued_mail(UserMailer, :welcome)
  end

  it 'delivers the email' do
    user = create(:user)

    expect {
      UserMailer.welcome(user).deliver_now
    }.to change { ActionMailer::Base.deliveries.count }.by(1)
  end
end
```
