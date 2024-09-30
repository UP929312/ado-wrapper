from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from datetime import datetime

from ado_wrapper.resources.organisations import Organisation
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

    @classmethod
    def create_personal_access_token(cls, ado_client: "AdoClient", display_name: str) -> None:  # "PersonalAccessToken":
        requires_initialisation(ado_client)
        # PAYLOAD = {
        #     "contributionIds": ["ms.vss-token-web.personal-access-token-issue-session-token-provider"],
        #     "dataProviderContext": {
        #         "properties": {
        #             "displayName": display_name,
        #             "validTo": "2024-07-15T17:04:05.555Z",
        #             "scope": "app_token",
        #             "targetAccounts": [ado_client.ado_org_id],
        #             "sourcePage": {
        #                 "url": f"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens",
        #                 "routeId":"ms.vss-admin-web.user-admin-hub-route",
        #                 "routeValues": {
        #                     "adminPivot": "tokens",
        #                     "controller": "ContributedPage",
        #                     "action": "Execute",
        #                     "serviceHost": f"{ado_client.ado_org_id} ({ado_client.ado_org_name})",
        #                 }
        #             }
        #         }
        #     }
        # }
        # PAYLOAD = {"contributionIds":["ms.vss-token-web.personal-access-token-issue-session-token-provider"],"dataProviderContext":{"properties":{"displayName":"abcdef","validTo":"2024-07-30T20:14:44.342Z","scope":"app_token","targetAccounts":["b47671bd-f9c8-42ee-a446-4aa13c8ff99a"],"sourcePage":{"url": f"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens","routeId":"ms.vss-admin-web.user-admin-hub-route","routeValues":{"adminPivot":"tokens","controller":"ContributedPage","action":"Execute","serviceHost": f"{ado_client.ado_org_id} ({ado_client.ado_org_name})"}}}}}
        # {"contributionIds":["ms.vss-token-web.personal-access-token-issue-session-token-provider"],"dataProviderContext":{"properties":{"displayName":"aaabbb",   "validTo":"2024-07-30T12:42:17.617Z","scope":"app_token","targetAccounts":["{ado_client.ado_org_id}""],
        # "sourcePage":{"url":"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens","routeId":"ms.vss-admin-web.user-admin-hub-route","routeValues":{"adminPivot":"tokens","controller":"ContributedPage","action":"Execute","serviceHost":"{ado_client.ado_org_id} ({ado_client.ado_org_name})"}}}}}
        # headers = {
        #     "Accept": "application/json;api-version=5.0-preview.1;excludeUrls=true;enumsAsNumbers=true;msDateFormat=true;noArrayWrap=true",
        #     "Accept-Encoding": "gzip, deflate, br, zstd",
        #     "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        #     "Content-Type": "application/json",
        #     "Content-Length": "568",
        #     "Origin": "https://dev.azure.com",
        #     "Priority": "u=1, i",
        #     "Referer": f"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens",
        #     "Authorization": f"Bearer {AAD_AUTHENTICATION}",
        #     "Sec-Ch-Ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        #     "Sec-Ch-Ua-Mobile": "?0",
        #     "Sec-Ch-Ua-Platform": '"macOS"',
        #     "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        #     "X-Vss-Clientauthprovider": "MsalTokenProvider",
        #     "X-Vss-reauthenticationaction": "Suppress",
        #     "Content-Length": "566",
        #     "Cookie": f"VstsSession={VSTS_SESSION}; MSFPC={MSFPC}; __RequestVerificationToken={REQUEST_VERIFICATION_TOKEN}; UserAuthentication={USER_AUTHENTICATION}; HostAuthentication={HOST_AUTHENTICATION}; AadAuthentication={AAD_AUTHENTICATION}"
        # }
        # cookies = {
        #     "__RequestVerificationToken264dae6ea-4a7f-431d-a54f-526b36248f16": REQUEST_VERIFICATION_TOKEN_WITH_ID,
        #     "MicrosoftApplicationsTelemetryDeviceId": MICROSOFT_APPLICATION_TELEMENTRY_DEVICE_ID, "VstsSession": VSTS_SESSION, "__RequestVerificationToken": REQUEST_VERIFICATION_TOKEN,
        #     # Ones that change:
        #     "MSFPC": MSFPC, "UserAuthentication": USER_AUTHENTICATION, "HostAuthentication": HOST_AUTHENTICATION, "AadAuthentication":  AAD_AUTHENTICATION,
        # }
        # request = ado_client.session.post(
        #     f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery",  # ?api-version=5.0-preview.1
        #     headers=headers,
        #     json=PAYLOAD,
        #     cookies=cookies,
        # )
        # ssert request.status_code == 200
        # print(request.status_code)
        # print(request.json())
        # return None  # type: ignore
        # print("###", request["dataProviderExceptions"]["ms.vss-token-web.personal-access-token-issue-session-token-provider"]["message"], "###")
        # return cls.from_request_payload(request)
        # {"contributionIds":["ms.vss-token-web.personal-access-token-issue-session-token-provider"],"dataProviderContext":{"properties":{"displayName":"Temp 123","validTo":"2024-08-13T17:16:16.800Z","scope":"app_token","targetAccounts":["org_id"],"sourcePage":{"url":"https://dev.azure.com/{ado_client.ado_org_name}/_usersSettings/tokens","routeId":"ms.vss-admin-web.user-admin-hub-route","routeValues":{"adminPivot":"tokens","controller":"ContributedPage","action":"Execute","}}}}}

    @classmethod
    def get_access_tokens(
        cls, ado_client: "AdoClient", org_id: str | None = None, include_different_orgs: bool = False, include_expired_tokens: bool = False
    ) -> list["PersonalAccessToken"]:  # fmt: skip

        requires_initialisation(ado_client)
        now = datetime.now()
        # Sun, 14 Jul 2024 18:14:24 GMT
        page_request_timestamp = f"{DAYS_OF_WEEK[now.weekday()]}, {str(now.day):0>2} {MONTHS[now.month-1]} {now.year} {now.hour}:{now.minute}:{now.second:02} GMT"  # fmt: skip
        request = ado_client.session.get(
            f"https://vssps.dev.azure.com/{ado_client.ado_org_name}/_apis/Token/SessionTokens?displayFilterOption=1&createdByOption=3&sortByOption=2&isSortAscending=true&startRowNumber=1&pageSize=1000&pageRequestTimeStamp={page_request_timestamp}&api-version=5.0-preview.1"
        ).json()
        if org_id is None:
            org_id = Organisation.get_by_name(ado_client, ado_client.ado_org_name).organisation_id  # type: ignore[union-attr]
        return [cls.from_request_payload(x) for x in request["sessionTokens"]
                if (include_expired_tokens or from_ado_date_string(x["validTo"]) > datetime.now())
                and (include_different_orgs or x["targetAccounts"] == [org_id])]  # fmt: skip

    @classmethod
    def get_access_token_by_name(
        cls, ado_client: "AdoClient", display_name: str, org_id: str | None = None
    ) -> "PersonalAccessToken | None":
        return [x for x in cls.get_access_tokens(ado_client, org_id, include_different_orgs=True, include_expired_tokens=True)
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
    #     rint(request["dataProviderExceptions"]["ms.vss-token-web.personal-access-token-issue-session-token-provider"]["message"])
    #     return ""
    #     new_token: str = request["dataProviders"]["ms.vss-token-web.personal-access-token-issue-session-token-provider"]["token"]
    #     rint(new_token)
    #     return new_token


# ======================================================================================================= #
# ------------------------------------------------------------------------------------------------------- #
# ======================================================================================================= #
