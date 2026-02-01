# Migration Examples

Production-ready migration examples demonstrating common patterns, safety practices,
and proper use of indices, constraints, and JSONB columns.

---

## Example 1: Add Column to Existing Table

```ruby
# frozen_string_literal: true

class AddRoleToProfiles < ActiveRecord::Migration[7.1]
  def change
    add_column :profiles, :role, :integer, default: 0, null: false
    add_index :profiles, :role
  end
end
```

### With Enum Mapping Comment

```ruby
# frozen_string_literal: true

# Role values: member (0), admin (1), owner (2)
class AddRoleToProfiles < ActiveRecord::Migration[7.1]
  def change
    add_column :profiles, :role, :integer, default: 0, null: false
    add_index :profiles, :role
  end
end
```

---

## Example 2: Create New Table

```ruby
# frozen_string_literal: true

class CreateExperiences < ActiveRecord::Migration[7.1]
  def change
    create_table :experiences do |t|
      t.references :profile, null: false, foreign_key: true, index: true
      t.references :company, foreign_key: true, index: true
      t.string :title, null: false
      t.text :description
      t.date :start_date, null: false
      t.date :end_date
      t.boolean :current, default: false, null: false
      t.timestamps
    end

    add_index :experiences, [:profile_id, :start_date]
  end
end
```

---

## Example 3: Add Index (Standard)

```ruby
# frozen_string_literal: true

class AddIndexToProfilesEmail < ActiveRecord::Migration[7.1]
  def change
    add_index :profiles, :email, unique: true
  end
end
```

### Composite Index

```ruby
# frozen_string_literal: true

class AddCompositeIndexToProfileSkills < ActiveRecord::Migration[7.1]
  def change
    add_index :profile_skills, [:profile_id, :skill_id], unique: true
  end
end
```

---

## Example 4: Add Index Concurrently (Large Tables)

For tables with millions of rows, add indices concurrently to avoid locking.

```ruby
# frozen_string_literal: true

class AddIndexToProfilesEmailConcurrently < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def change
    add_index :profiles, :email, unique: true, algorithm: :concurrently
  end
end
```

---

## Example 5: Add JSONB Column

```ruby
# frozen_string_literal: true

class AddMetadataToCompanies < ActiveRecord::Migration[7.1]
  def change
    add_column :companies, :metadata, :jsonb, default: {}, null: false
    add_index :companies, :metadata, using: :gin
  end
end
```

---

## Example 6: Add Foreign Key Column

```ruby
# frozen_string_literal: true

class AddCompanyToProfiles < ActiveRecord::Migration[7.1]
  def change
    add_reference :profiles, :company, foreign_key: true, index: true
  end
end
```

---

## Example 7: Remove Column (Reversible)

```ruby
# frozen_string_literal: true

class RemoveBioFromProfiles < ActiveRecord::Migration[7.1]
  def change
    remove_column :profiles, :bio, :text
  end
end
```

### Safe Column Removal (Two-Step Process)

**Step 1: Ignore the column (deploy first)**

```ruby
# app/models/profile.rb
class Profile < ApplicationRecord
  self.ignored_columns += ['legacy_bio']
end
```

**Step 2: Drop the column (after Step 1 is deployed)**

```ruby
# frozen_string_literal: true

class RemoveLegacyBioFromProfiles < ActiveRecord::Migration[7.1]
  def change
    safety_assured { remove_column :profiles, :legacy_bio, :text }
  end
end
```

---

## Example 8: Rename Column

```ruby
# frozen_string_literal: true

class RenameDescriptionToSummaryInExperiences < ActiveRecord::Migration[7.1]
  def change
    rename_column :experiences, :description, :summary
  end
end
```

---

## Example 9: Add Column with Backfill

For adding a NOT NULL column to a table with existing data:

```ruby
# frozen_string_literal: true

class AddStatusToImports < ActiveRecord::Migration[7.1]
  def change
    add_column :imports, :status, :integer

    reversible do |dir|
      dir.up do
        Import.update_all(status: 0)
      end
    end

    change_column_null :imports, :status, false
    change_column_default :imports, :status, 0
    add_index :imports, :status
  end
end
```

---

## Example 10: Create Join Table

```ruby
# frozen_string_literal: true

class CreateProfileSkills < ActiveRecord::Migration[7.1]
  def change
    create_table :profile_skills do |t|
      t.references :profile, null: false, foreign_key: true
      t.references :skill, null: false, foreign_key: true
      t.integer :proficiency, default: 1, null: false
      t.timestamps
    end

    add_index :profile_skills, [:profile_id, :skill_id], unique: true
  end
end
```

---

## Safety Patterns Summary

| Pattern | When to Use | Example |
|---------|-------------|---------|
| `null: false` with `default` | New required columns | `add_column :t, :col, :int, default: 0, null: false` |
| `algorithm: :concurrently` | Indices on large tables | `add_index :t, :col, algorithm: :concurrently` |
| `disable_ddl_transaction!` | With concurrent indices | Top of migration class |
| `foreign_key: true` | All reference columns | `t.references :user, foreign_key: true` |
| Two-step removal | Dropping columns in production | Ignore first, remove second deploy |
| `reversible` block | Data backfills | Wrap in `reversible { |dir| dir.up { } }` |
| GIN index | JSONB columns | `add_index :t, :col, using: :gin` |
