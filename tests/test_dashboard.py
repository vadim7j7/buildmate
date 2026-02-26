"""Tests for dashboard installation: services.json rendering and install flow."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import compose_stacks
from lib.renderer import render_all


class TestServicesJsonRendering:
    """Test that render_all with dashboard=True generates correct services_config."""

    def test_rails_services_config(self):
        composed = compose_stacks(["rails"])
        output = render_all(composed, dashboard=True)

        assert output.services_config is not None
        services = output.services_config["services"]
        assert len(services) == 1
        assert services[0]["id"] == "rails"
        assert "rails" in services[0]["command"].lower()

    def test_nextjs_services_config(self):
        composed = compose_stacks(["nextjs"])
        output = render_all(composed, dashboard=True)

        assert output.services_config is not None
        services = output.services_config["services"]
        assert len(services) == 1
        assert services[0]["id"] == "nextjs"

    def test_fastapi_services_config(self):
        composed = compose_stacks(["fastapi"])
        output = render_all(composed, dashboard=True)

        assert output.services_config is not None
        services = output.services_config["services"]
        assert len(services) == 1
        assert services[0]["id"] == "fastapi"
        assert "uvicorn" in services[0]["command"]

    def test_dashboard_false_no_services(self):
        composed = compose_stacks(["rails"])
        output = render_all(composed, dashboard=False)

        assert output.services_config is None

    def test_multi_stack_services(self):
        composed = compose_stacks(["rails", "nextjs"])
        output = render_all(composed, dashboard=True)

        assert output.services_config is not None
        services = output.services_config["services"]
        assert len(services) == 2
        ids = {s["id"] for s in services}
        assert ids == {"rails", "nextjs"}

    def test_scraping_no_services(self):
        """Scraping stack has no dev_server, so no services_config."""
        composed = compose_stacks(["scraping"])
        output = render_all(composed, dashboard=True)

        # Scraping has no dev_server in verification
        assert output.services_config is None

    def test_services_config_structure(self):
        """Verify the shape of each service entry."""
        composed = compose_stacks(["rails"])
        output = render_all(composed, dashboard=True)

        svc = output.services_config["services"][0]
        assert "id" in svc
        assert "name" in svc
        assert "command" in svc
        assert "cwd" in svc
        assert "port" in svc


class TestDashboardDefault:
    """Test that dashboard=False (default) leaves services_config as None."""

    def test_default_no_dashboard(self):
        composed = compose_stacks(["rails"])
        output = render_all(composed)
        assert output.services_config is None

    def test_services_config_survives_render(self):
        """Ensure services_config is properly set after full render pipeline."""
        composed = compose_stacks(["fastapi"])
        output = render_all(composed, dashboard=True)

        assert output.services_config is not None
        assert isinstance(output.services_config, dict)
        assert "services" in output.services_config
        assert isinstance(output.services_config["services"], list)
