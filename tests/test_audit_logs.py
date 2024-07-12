pass
# import pytest

# from ado_wrapper.resources.audit_logs import AuditLog
# from tests.setup_client import setup_client  # fmt: skip


# class TestAuditLog:
#     def setup_method(self) -> None:
#         self.ado_client = setup_client()

#     @pytest.mark.from_request_payload
#     def test_from_request_payload(self) -> None:
#         audit_log = AuditLog.from_request_payload(
#             {
#                 'id': '999999999999999999;00000000-0000-0000-0000-000000000000;00000000-0000-0000-0000-000000000000',
#                 'correlationId': '00000000-0000-0000-0000-000000000000',
#                 'activityId': '00000000-0000-0000-0000-000000000000',
#                 'actorUserId': '00000000-0000-0000-0000-000000000000', # Same as above
#                 'actorClientId': '00000000-0000-0000-0000-000000000000',
#                 'actorUPN': 'first.last@example.com',
#                 'authenticationMechanism': 'PAT_Unscoped authorizationId:<32_char_uuid>',
#                 'timestamp': '2024-01-01T01:01:01.01Z',
#                 'scopeType': 'organization',
#                 'scopeDisplayName': '<org_name> (Organization)',
#                 'scopeId': '00000000-0000-0000-0000-000000000000',
#                 'projectId': '00000000-0000-0000-0000-000000000000',
#                 'projectName': None,
#                 'ipAddress': '128.128.128.128',
#                 'userAgent': 'VSServices/128.128.123456.0 (NetStandard; Linux 5.10.215-203.850.amzn2.x86_64 #1 SMP Tue Apr 23 20:32:19 UTC 2024) VstsAgentCore-l',
#                 'actionId': 'Library.AgentAdded',
#                 'data': {},
#                 'details': 'Added agent <agent_name> to pool <pool_name>.',
#                 'area': 'Library',
#                 'category': 'modify',
#                 'categoryDisplayName': 'Modify',
#                 'actorDisplayName': 'First Last',
#             }
#         )
#         assert audit_log.action_id == '999999999999999999;00000000-0000-0000-0000-000000000000;00000000-0000-0000-0000-000000000000'
#         # TO-DO Add more here

#     @pytest.mark.from_request_payload
#     def test_create_delete(self) -> None:
#         audit_logs = AuditLog.get_all_by_area(self.ado_client, "Library")
#         assert len(audit_logs) > 0
#         audit_logs = AuditLog.get_all_by_category(self.ado_client, "access")
#         assert len(audit_logs) > 0
#         audit_logs = AuditLog.get_all_by_scope_type(self.ado_client, "organization")
#         assert len(audit_logs) > 0
