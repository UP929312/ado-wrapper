from requests.auth import HTTPBasicAuth

class AdoClient:
    def __init__(self, ado_email: str, ado_pat: str, ado_org: str, ado_project: str) -> None:
        self.auth = HTTPBasicAuth(ado_email, ado_pat)
        self.ado_org = ado_org
        self.ado_project = ado_project
