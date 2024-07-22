from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from datetime import datetime

from ado_wrapper.utils import from_ado_date_string, requires_initialisation


if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #


@dataclass
class PersonalAccessToken:
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/security/permissions/has-permissions-batch?view=azure-devops-rest-7.1"""

    display_name: str
    valid_from: datetime = field(repr=False)
    valid_to: datetime
    scope: str
    access_id: str
    user_id: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "PersonalAccessToken":
        return cls(
            data["displayName"], from_ado_date_string(data["validFrom"]), from_ado_date_string(data["validTo"]),
            data["scope"], data["accessId"], data["userId"],  # fmt: skip
        )

    # @classmethod
    # def create_personal_access_token(cls, ado_client: "AdoClient", display_name: str) -> "PersonalAccessToken":
    #     requires_initialisation(ado_client)
    #     PAYLOAD = {
    #         "contributionIds": ["ms.vss-token-web.personal-access-token-issue-session-token-provider"],
    #         "dataProviderContext": {
    #             "properties": {
    #                 "displayName": display_name,
    #                 "validTo": "2024-07-15T17:04:05.555Z",
    #                 "scope": "app_token",
    #                 "targetAccounts": ["org_id"],
    #                 "sourcePage": {
    #                     "url": f"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens",
    #                     "routeId":"ms.vss-admin-web.user-admin-hub-route",
    #                     "routeValues": {
    #                         "adminPivot": "tokens",
    #                         "controller": "ContributedPage",
    #                         "action": "Execute",
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #     # {"contributionIds":["ms.vss-token-web.personal-access-token-issue-session-token-provider"],"dataProviderContext":{"properties":{"displayName":"123456789","validTo":"2024-07-16T17:18:07.998Z","scope":"app_token","targetAccounts":["org_id"],
    #     headers = {"Accept": "application/json;api-version=5.0-preview.1;excludeUrls=true;enumsAsNumbers=true;msDateFormat=true;noArrayWrap=true"}
    #     headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    #     request = ado_client.session.post(
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery",  # ?api-version=5.0-preview.1
    #         headers=headers,
    #         json=PAYLOAD,
    #     ).json()
    #     print(request["dataProviderExceptions"]["ms.vss-token-web.personal-access-token-issue-session-token-provider"]["message"])
    #     return cls.from_request_payload(request)
    #     # {"contributionIds":["ms.vss-token-web.personal-access-token-issue-session-token-provider"],"dataProviderContext":{"properties":{"displayName":"Temp 123","validTo":"2024-08-13T17:16:16.800Z","scope":"app_token","targetAccounts":["org_id"],"sourcePage":{"url":"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens","routeId":"ms.vss-admin-web.user-admin-hub-route","routeValues":{"adminPivot":"tokens","controller":"ContributedPage","action":"Execute","}}}}}

    @classmethod
    def get_access_tokens(
        cls, ado_client: "AdoClient", include_different_orgs: bool = False, include_expired_tokens: bool = False
    ) -> list["PersonalAccessToken"]:  # fmt: skip
        # Sun, 14 Jul 2024 18:14:24 GMT
        requires_initialisation(ado_client)
        now = datetime.now()
        page_request_timestamp = f"{DAYS_OF_WEEK[now.weekday()]}, {now.day} {MONTHS[now.month-1]} {now.year} {now.hour}:{now.minute}:{now.second:02} GMT"  # fmt: skip
        request = ado_client.session.get(
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/Token/SessionTokens?displayFilterOption=1&createdByOption=3&sortByOption=2&isSortAscending=true&startRowNumber=1&pageSize=1000&pageRequestTimeStamp={page_request_timestamp}&api-version=5.0-preview.1"
        ).json()
        return [cls.from_request_payload(x) for x in request["sessionTokens"]
                if (include_expired_tokens or from_ado_date_string(x["validTo"]) > datetime.now())
                and (include_different_orgs or x["targetAccounts"] == [ado_client.ado_org_id])]  # fmt: skip

    @classmethod
    def get_access_token_by_name(cls, ado_client: "AdoClient", display_name: str) -> "PersonalAccessToken | None":
        requires_initialisation(ado_client)
        return [x for x in cls.get_access_tokens(ado_client, include_different_orgs=True, include_expired_tokens=True)
                if x.display_name == display_name][0]  # fmt: skip

    # @staticmethod
    # def revoke_personal_access_token(ado_client: "AdoClient", pat_id: str) -> None:
    #     requires_initialisation(ado_client)
    #     pass

    # @cls
    # def regenerate_personal_access_token(cls, ado_client: "AdoClient", token_name: str) -> str:
    #     """Regenerates a PAT and returns the new token"""
    #     requires_initialisation(ado_client)
    #     token: PersonalAccessToken = cls.get_access_token_by_name(ado_client, token_name)
    #     PAYLOAD = {
    #         "contributionIds": ["ms.vss-token-web.personal-access-token-issue-session-token-provider"],
    #         "dataProviderContext": {
    #             "properties": {
    #                 "clientId": "00000000-0000-0000-0000-000000000000",
    #                 "accessId": token.access_id,
    #                 "authorizationId": "",
    #                 "hostAuthorizationId": "00000000-0000-0000-0000-000000000000",
    #                 "userId": token.user_id,
    #                 "validFrom": "2024-07-13T16:07:59.646Z",
    #                 "validTo": "2024-08-13T17:54:02.433Z",
    #                 "displayName": token.display_name,
    #                 "scope": token.scope,
    #                 "targetAccounts": [ado_client.ado_org.organisation_id],
    #                 "token": None,
    #                 "alternateToken": None,
    #                 "isValid": True,
    #                 "isPublic": False,
    #                 "publicData": None,
    #                 "source": None,
    #                 "claims": None,
    #                 "sourcePage": {
    #                     "url": f"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens",
    #                     "routeId": "ms.vss-admin-web.user-admin-hub-route",
    #                     "routeValues": {
    #                         "adminPivot": "tokens",
    #                         "controller": "ContributedPage",
    #                         "action":"Execute",
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #     request = ado_client.session.post(
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview.1",
    #         json=PAYLOAD,
    #     ).json()
    #     print(request["dataProviderExceptions"]["ms.vss-token-web.personal-access-token-issue-session-token-provider"]["message"])
    #     return ""
    #     new_token: str = request["dataProviders"]["ms.vss-token-web.personal-access-token-issue-session-token-provider"]["token"]
    #     print(new_token)
    #     return new_token


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #
