import pytest

from ado_wrapper.client import AdoClient
from ado_wrapper.resources.service_endpoint import ServiceEndpoint

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()


class TestServiceEndpoints:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project, state_file_name="tests/test_state.state")

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        service_endpoint = ServiceEndpoint.from_request_payload(
            {
                "data": {},
                "id": "123",
                "name": "test-service-endpoint",
                "type": "github",
                "url": "https://github.com",
                "createdBy": {"displayName": "test-user", "uniqueName": "test-user", "id": "123"},
                "description": "test-description",
                "authorization": {"parameters": {"AccessToken": None}, "scheme": "Token"},
                "isShared": False,
                "isOutdated": False,
                "isReady": True,
                "owner": "Library",
                "serviceEndpointProjectReferences": [
                    {
                        "projectReference": {"id": "456", "name": "test-project"},
                        "name": "test-service-endpoint",
                        "description": "test-description",
                    }
                ],
            }
        )
        assert isinstance(service_endpoint, ServiceEndpoint)
        assert service_endpoint.service_endpoint_id == "123"
        assert service_endpoint.name == "test-service-endpoint"
        assert service_endpoint.url == "https://github.com"
        assert service_endpoint.is_ready
        assert not service_endpoint.is_shared
        assert service_endpoint.to_json() == ServiceEndpoint.from_json(service_endpoint.to_json()).to_json()


    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        service_endpoint = ServiceEndpoint.create(
            self.ado_client, "ado_wrapper-test-service-endpoint", "github", "https://github.com", "test-user", "test-password"
        )
        assert isinstance(service_endpoint, ServiceEndpoint)
        service_endpoint.delete(self.ado_client)

    @pytest.mark.update
    @pytest.mark.wip
    def test_update(self) -> None:
        pass
        # service_endpoint = ServiceEndpoint.create(
        #     self.ado_client, "ado_wrapper-test-service-endpoint-for-update", "github", "https://github.com", "test-user", "test-password"
        # )
        # # =====
        # service_endpoint.update(self.ado_client, "name", "ado_wrapper-test-service-endpoint-for-update-renamed")
        # assert service_endpoint.name == "ado_wrapper-test-service-endpoint-for-update-renamed"  # Test instance attribute is updated
        # # =====
        # fetched_service_endpoint = ServiceEndpoint.get_by_id(self.ado_client, service_endpoint.service_endpoint_id)
        # assert fetched_service_endpoint.name == "ado_wrapper-test-service-endpoint-for-update-renamed"
        # # =====
        # service_endpoint.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        service_endpoint_created = ServiceEndpoint.create(
            self.ado_client, "ado_wrapper-test-service-endpoint-get-by-id", "github", "https://github.com", "test-user", "test-password"
        )
        service_endpoint = ServiceEndpoint.get_by_id(self.ado_client, service_endpoint_created.service_endpoint_id)
        assert service_endpoint.service_endpoint_id == service_endpoint_created.service_endpoint_id
        service_endpoint_created.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        service_endpoints = ServiceEndpoint.get_all(self.ado_client)
        assert len(service_endpoints) > 10
        assert all(isinstance(service_endpoint, ServiceEndpoint) for service_endpoint in service_endpoints)

    def test_get_by_name(self) -> None:
        service_endpoint_created = ServiceEndpoint.create(
            self.ado_client, "ado_wrapper-test-service-endpoint-get-by-name", "github", "https://github.com", "test-user", "test-password"
        )
        service_endpoint = ServiceEndpoint.get_by_name(self.ado_client, "ado_wrapper-test-service-endpoint-get-by-name")
        assert service_endpoint.name == service_endpoint_created.name
        assert service_endpoint.service_endpoint_id == service_endpoint_created.service_endpoint_id
        service_endpoint_created.delete(self.ado_client)
