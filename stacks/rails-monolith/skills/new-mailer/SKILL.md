---
name: new-mailer
description: Generate an ActionMailer with preview, i18n, and spec file
---

# /new-mailer

## What This Does

Generates an ActionMailer for sending transactional emails, including:
- Mailer class with email methods
- Email views (HTML and text)
- Mailer preview for development testing
- I18n translation files
- RSpec spec with email content tests

## Usage

```
/new-mailer User                       # Creates UserMailer
/new-mailer Order                      # Creates OrderMailer
/new-mailer Admin::Report              # Creates Admin::ReportMailer
```

## How It Works

1. **Read reference patterns.** Load mailer patterns from:
   - `skills/new-mailer/references/mailer-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine mailer name and actions.** Parse the argument and infer:
   - Mailer class name (e.g., `UserMailer`)
   - Common email actions based on context (welcome, notification, etc.)
   - File paths for all generated files

3. **Generate the mailer file.** Create the mailer with:
   - `frozen_string_literal: true`
   - `ApplicationMailer` inheritance
   - Email methods with `@user` and other instance variables
   - Proper subject with I18n
   - `mail` call with `to:` and `subject:`

4. **Generate email views.** Create both HTML and text templates:
   - `app/views/<mailer>/<action>.html.erb`
   - `app/views/<mailer>/<action>.text.erb`

5. **Generate mailer preview.** Create preview class:
   - `test/mailers/previews/<mailer>_preview.rb` or
   - `spec/mailers/previews/<mailer>_preview.rb`

6. **Generate I18n translations.** Add to locale files:
   - `config/locales/mailers.en.yml`

7. **Generate spec file.** Create the spec with:
   - Delivery tests
   - Content tests for subject, body, recipients
   - Attachment tests if applicable

8. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/mailers/<path>.rb spec/mailers/<path>_spec.rb
   bundle exec rspec spec/mailers/<path>_spec.rb
   ```

9. **Report results.** Show generated files and preview URL.

## Generated Files

```
app/mailers/<mailer_name>.rb
app/views/<mailer_name>/welcome.html.erb
app/views/<mailer_name>/welcome.text.erb
spec/mailers/<mailer_name>_spec.rb
spec/mailers/previews/<mailer_name>_preview.rb
config/locales/mailers.en.yml (appended)
```

## Example Output

For `/new-mailer User`:

**Mailer:** `app/mailers/user_mailer.rb`
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
end
```

**View:** `app/views/user_mailer/welcome.html.erb`

**Preview:** `spec/mailers/previews/user_mailer_preview.rb`
```ruby
# frozen_string_literal: true

# Preview user emails at http://localhost:3000/rails/mailers/user_mailer
class UserMailerPreview < ActionMailer::Preview
  def welcome
    UserMailer.welcome(User.first || FactoryBot.build(:user))
  end

  def password_reset
    UserMailer.password_reset(User.first || FactoryBot.build(:user))
  end
end
```

## Rules

- Inherit from `ApplicationMailer`
- Use I18n for all subject lines and email copy
- Always provide both HTML and text versions
- Use `deliver_later` (not `deliver_now`) in application code
- Create previews for visual testing in development
- Test email content, not just delivery
- Use layouts for consistent email styling
