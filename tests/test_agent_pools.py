from datetime import datetime

import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.agent_pools import AgentPool
from tests.setup_client import setup_client


class TestAgentPool:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        agent_pool = AgentPool.from_request_payload(
            {
                "id": "123",
                "agentCloudId": "456",
                "name": "test-agent-pool",
                "size": 10,
                "targetSize": None,
                "autoSize": None,
                "autoUpdate": True,
                "autoProvision": False,
                "isHosted": False,
                "scope": "a00000aa-a0a0-00aa-a000-0aa00a0aa00a",
                "createdOn": "2024-01-01T01:01:01.001Z",
                "createdBy": {"displayName": "created_by_user", "uniqueName": "Created By User", "id": "123"},
            }
        )
        assert isinstance(agent_pool, AgentPool)
        assert agent_pool.agent_pool_id == "123"
        assert agent_pool.agent_cloud_id == "456"
        assert agent_pool.name == "test-agent-pool"
        assert agent_pool.pool_size == 10
        assert agent_pool.target_size is None
        assert agent_pool.auto_size is None
        assert agent_pool.auto_update
        assert not agent_pool.auto_provision
        assert not agent_pool.is_hosted
        assert agent_pool.scope == "a00000aa-a0a0-00aa-a000-0aa00a0aa00a"
        assert isinstance(agent_pool.created_on, datetime)

        assert agent_pool.to_json() == AgentPool.from_json(agent_pool.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        agent_pool = AgentPool.create(self.ado_client, "ado_wrapper-test-agent-pool", None, True, True, True, False, 10, None)
        agent_pool.delete(self.ado_client)

    # @pytest.mark.skip(reason="This test is flakey, and randomly fails, even with no changes")
    # @pytest.mark.update
    # def test_update(self) -> None:
    #     # Variable group updating is quite flakey, and randomly fails, even with no changes
    #     agent_pool = AgentPool.create(self.ado_client, "ado_wrapper-test-for-update", "my_description", {"a": "b"})
    #     changed_variables = {"b": "c"}
    #     # =====
    #     agent_pool.update(self.ado_client, "variables", changed_variables)  # For some reason, this only sometimes works
    #     assert agent_pool.variables == changed_variables
    #     # =====
    #     fetch_agent_pool = AgentPool.get_by_id(self.ado_client, agent_pool.agent_pool_id)
    #     assert fetch_agent_pool.variables == changed_variables
    #     # =====
    #     agent_pool.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        agent_pool_created = AgentPool.create(self.ado_client, "ado_wrapper_test_agent_pool", None, True, True, True, False, 1, 1)
        agent_pool = AgentPool.get_by_id(self.ado_client, agent_pool_created.agent_pool_id)
        assert agent_pool_created.agent_pool_id == agent_pool.agent_pool_id
        agent_pool_created.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        agent_pools = AgentPool.get_all(self.ado_client)
        assert len(agent_pools) >= 1
        assert all(isinstance(agent_pool, AgentPool) for agent_pool in agent_pools)

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        agent_pool_created = AgentPool.create(self.ado_client, "ado_wrapper-test-for-get-by-name")
        agent_pool = AgentPool.get_by_name(self.ado_client, agent_pool_created.name)
        agent_pool_created.delete(self.ado_client)
        assert agent_pool is not None
        assert agent_pool.agent_pool_id == agent_pool_created.agent_pool_id
        assert agent_pool.name == agent_pool_created.name


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
