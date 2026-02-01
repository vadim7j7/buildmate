# Controller Examples

Production-ready controller examples demonstrating RESTful patterns, strong params,
concerns, before_actions, and presenter integration.

---

## Example 1: Standard CRUD Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    # Manages profile CRUD operations for the authenticated user.
    class ProfilesController < BaseController
      before_action :authenticate_user!
      before_action :set_profile, only: %i[show update destroy]

      # GET /api/v1/profiles
      #
      # @return [JSON] paginated list of profiles with metadata
      def index
        profiles = current_user.profiles
          .includes(:company, :skills)
          .page(params[:page])
          .per(params[:per_page] || 25)

        render json: {
          profiles: ProfilePresenter.new(profiles).call,
          meta: pagination_meta(profiles)
        }
      end

      # GET /api/v1/profiles/:id
      #
      # @return [JSON] single profile
      def show
        render json: ProfilePresenter.new(@profile).call
      end

      # POST /api/v1/profiles
      #
      # @return [JSON] created profile or validation errors
      def create
        profile = current_user.profiles.build(profile_params)

        if profile.save
          render json: ProfilePresenter.new(profile).call, status: :created
        else
          render json: { errors: profile.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # PATCH /api/v1/profiles/:id
      #
      # @return [JSON] updated profile or validation errors
      def update
        if @profile.update(profile_params)
          render json: ProfilePresenter.new(@profile).call
        else
          render json: { errors: @profile.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/profiles/:id
      #
      # @return [void] 204 No Content
      def destroy
        @profile.destroy!
        head :no_content
      end

      private

      def set_profile
        @profile = current_user.profiles.find(params[:id])
      end

      def profile_params
        params.require(:profile).permit(
          :name, :email, :bio, :company_id, :active,
          skill_ids: []
        )
      end
    end
  end
end
```

---

## Example 2: Controller with Search and Filtering

```ruby
# frozen_string_literal: true

module Api
  module V1
    # Provides search and filtering for candidate profiles.
    class CandidatesController < BaseController
      before_action :authenticate_user!

      # GET /api/v1/candidates
      #
      # @param q [String] search query (searches name and email)
      # @param status [String] filter by status (active, inactive, archived)
      # @param company_id [Integer] filter by company
      # @param sort [String] sort order (name, recent, relevance)
      # @return [JSON] filtered and paginated candidates
      def index
        candidates = Candidates::SearchQuery.new(
          params:,
          scope: accessible_candidates
        ).call.page(params[:page]).per(25)

        render json: {
          candidates: CandidatePresenter.new(candidates).call,
          meta: pagination_meta(candidates)
        }
      end

      # GET /api/v1/candidates/:id
      def show
        candidate = accessible_candidates.find(params[:id])
        render json: CandidatePresenter.new(candidate).call
      end

      private

      def accessible_candidates
        current_user.organization.candidates.includes(:company, :skills, :experiences)
      end
    end
  end
end
```

---

## Example 3: Controller with Concerns

```ruby
# frozen_string_literal: true

module Api
  module V1
    # Manages company resources with bulk operations support.
    class CompaniesController < BaseController
      include Paginatable
      include BulkActionable

      before_action :authenticate_user!
      before_action :set_company, only: %i[show update destroy]
      before_action :authorize_admin!, only: %i[create destroy bulk_update]

      # GET /api/v1/companies
      def index
        companies = Company
          .includes(:profiles)
          .search(params[:q])
          .page(params[:page])
          .per(params[:per_page] || 25)

        render json: {
          companies: CompanyPresenter.new(companies).call,
          meta: pagination_meta(companies)
        }
      end

      # GET /api/v1/companies/:id
      def show
        render json: CompanyPresenter.new(@company).call
      end

      # POST /api/v1/companies
      def create
        company = Company.new(company_params)

        if company.save
          render json: CompanyPresenter.new(company).call, status: :created
        else
          render json: { errors: company.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # PATCH /api/v1/companies/:id
      def update
        if @company.update(company_params)
          render json: CompanyPresenter.new(@company).call
        else
          render json: { errors: @company.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/companies/:id
      def destroy
        @company.destroy!
        head :no_content
      end

      # PATCH /api/v1/companies/bulk_update
      def bulk_update
        results = bulk_action(Company, params[:ids]) do |company|
          company.update!(company_params)
        end

        render json: { updated: results[:success], errors: results[:errors] }
      end

      private

      def set_company
        @company = Company.find(params[:id])
      end

      def company_params
        params.require(:company).permit(:name, :domain, :industry, :size)
      end

      def authorize_admin!
        head :forbidden unless current_user.admin?
      end
    end
  end
end
```

---

## Example 4: Nested Resource Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    # Manages experiences nested under a profile.
    class ExperiencesController < BaseController
      before_action :authenticate_user!
      before_action :set_profile
      before_action :set_experience, only: %i[show update destroy]

      # GET /api/v1/profiles/:profile_id/experiences
      def index
        experiences = @profile.experiences
          .includes(:company)
          .order(start_date: :desc)

        render json: ExperiencePresenter.new(experiences).call
      end

      # POST /api/v1/profiles/:profile_id/experiences
      def create
        experience = @profile.experiences.build(experience_params)

        if experience.save
          render json: ExperiencePresenter.new(experience).call, status: :created
        else
          render json: { errors: experience.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # PATCH /api/v1/profiles/:profile_id/experiences/:id
      def update
        if @experience.update(experience_params)
          render json: ExperiencePresenter.new(@experience).call
        else
          render json: { errors: @experience.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/profiles/:profile_id/experiences/:id
      def destroy
        @experience.destroy!
        head :no_content
      end

      private

      def set_profile
        @profile = current_user.profiles.find(params[:profile_id])
      end

      def set_experience
        @experience = @profile.experiences.find(params[:id])
      end

      def experience_params
        params.require(:experience).permit(
          :title, :company_id, :description, :start_date, :end_date, :current
        )
      end
    end
  end
end
```

---

## BaseController

```ruby
# frozen_string_literal: true

module Api
  module V1
    # Base controller for all V1 API endpoints.
    class BaseController < ApplicationController
      include Paginatable

      rescue_from ActiveRecord::RecordNotFound, with: :not_found
      rescue_from ActiveRecord::RecordInvalid, with: :unprocessable_entity
      rescue_from ActionController::ParameterMissing, with: :bad_request

      private

      def not_found
        render json: { error: 'Record not found' }, status: :not_found
      end

      def unprocessable_entity(exception)
        render json: { errors: exception.record.errors.full_messages },
               status: :unprocessable_entity
      end

      def bad_request(exception)
        render json: { error: exception.message }, status: :bad_request
      end
    end
  end
end
```

---

## Route Examples

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :profiles do
        resources :experiences, only: %i[index create update destroy]
      end
      resources :companies
      resources :candidates, only: %i[index show]
    end
  end
end
```
