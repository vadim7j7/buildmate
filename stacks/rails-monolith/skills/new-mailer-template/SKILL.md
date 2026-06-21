---
name: new-mailer-template
description: Generate ERB mailer view templates (HTML + text) for an existing mailer action
---

# /new-mailer-template

## What This Does

Creates HTML and plain-text mailer templates for an existing mailer action.
Sets up consistent layout (header, body, CTA, footer), uses `t('...')` for
copy, and generates a preview class for development.

Use this when the mailer class + action already exist and you need to author
or replace the rendered email.

## Usage

```
/new-mailer-template UserMailer welcome
/new-mailer-template OrderMailer receipt
/new-mailer-template DigestMailer weekly
```

## How It Works

### 1. Verify the Mailer Action Exists

```bash
grep -rn "def welcome" app/mailers/
```

If not, suggest running `/new-mailer` first.

### 2. Generate Templates

#### HTML: `app/views/user_mailer/welcome.html.erb`

```erb
<%# locals:
      user: User
%>

<%= render "shared/email_header" %>

<table role="presentation" class="email-body" cellpadding="0" cellspacing="0">
  <tr>
    <td>
      <h1><%= t('user_mailer.welcome.heading', name: user.first_name) %></h1>

      <p><%= t('user_mailer.welcome.intro') %></p>

      <p>
        <%= link_to t('user_mailer.welcome.cta'),
                    profile_url(user),
                    class: "email-button" %>
      </p>

      <p><%= t('user_mailer.welcome.signoff') %></p>
    </td>
  </tr>
</table>

<%= render "shared/email_footer" %>
```

#### Plain text: `app/views/user_mailer/welcome.text.erb`

```erb
<%# locals:
      user: User
%>

<%= t('user_mailer.welcome.heading', name: user.first_name) %>

<%= t('user_mailer.welcome.intro') %>

<%= t('user_mailer.welcome.cta') %>: <%= profile_url(user) %>

<%= t('user_mailer.welcome.signoff') %>

--
<%= t('app.name') %>
<%= unsubscribe_url %>
```

### 3. Generate the Mailer Preview

`spec/mailers/previews/user_mailer_preview.rb`:

```ruby
# frozen_string_literal: true

class UserMailerPreview < ActionMailer::Preview
  # http://localhost:3000/rails/mailers/user_mailer/welcome
  def welcome
    user = User.first || User.new(email: 'preview@example.com', first_name: 'Ada')
    UserMailer.with(user:).welcome
  end
end
```

### 4. Suggest i18n Keys

Print keys to add to `config/locales/en.yml`:

```yaml
en:
  user_mailer:
    welcome:
      subject: "Welcome to %{app_name}"
      heading: "Welcome, %{name}!"
      intro: "We're glad you're here. Start by setting up your profile."
      cta: "Set up your profile"
      signoff: "— The team"
```

### 5. Verify

```bash
# Open the preview in browser
bin/rails server
# Visit http://localhost:3000/rails/mailers/user_mailer/welcome
```

Or write a mailer spec:

```ruby
RSpec.describe UserMailer do
  let(:user) { create(:user, first_name: 'Ada') }

  describe '#welcome' do
    let(:mail) { described_class.with(user:).welcome }

    it 'sends to the user' do
      expect(mail.to).to eq([user.email])
    end

    it 'includes the heading' do
      expect(mail.body.encoded).to include('Welcome, Ada!')
    end

    it 'includes both HTML and text parts' do
      expect(mail.html_part).to be_present
      expect(mail.text_part).to be_present
    end
  end
end
```

## Rules

- ALWAYS provide BOTH `.html.erb` AND `.text.erb` versions
- Use **table-based layouts** for HTML emails — many clients ignore `<div>` styling and modern CSS
- Use `t('...')` for ALL copy — emails go through translation
- Render `_email_header` and `_email_footer` partials for consistent branding
- Use `*_url` (NOT `*_path`) — emails need absolute URLs
- Document the `locals:` contract at the top
- Generate a `Preview` class so designers can iterate without sending real emails
- Keep CSS inline or in a layout-level `<style>` block — many clients strip external CSS

## Common Pitfalls

- **Links break in production**: used `_path` instead of `_url`
- **Renders blank in Gmail**: too much CSS in `<head>` was stripped — inline critical styles
- **Translations fail**: missing keys in `config/locales/en.yml`
- **Text part missing**: spam filters penalize HTML-only emails

## Output

```
Created:
  app/views/user_mailer/welcome.html.erb
  app/views/user_mailer/welcome.text.erb
  spec/mailers/previews/user_mailer_preview.rb

Suggested i18n keys (config/locales/en.yml):
  en.user_mailer.welcome.subject
  en.user_mailer.welcome.heading
  en.user_mailer.welcome.intro
  en.user_mailer.welcome.cta

Preview at:
  http://localhost:3000/rails/mailers/user_mailer/welcome
```
