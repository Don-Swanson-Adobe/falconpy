# test_uber_api_complete.py
# This class tests the uber class

import json
import os
import sys
import pytest
import datetime
import hashlib
# Import our sibling src folder into the path
sys.path.append(os.path.abspath('src'))
# flake8: noqa=E402
# pylint: disable=C0103
# Classes to test - manually imported from our sibling folder
from falconpy import APIHarness
# Import perform_request from _util so we can test generating 405's directly
from falconpy._util import perform_request, force_default


AllowedResponses = [200, 400, 401, 404, 405, 415, 418, 429]

if "DEBUG_API_ID" in os.environ and "DEBUG_API_SECRET" in os.environ:
    config = {}
    config["falcon_client_id"] = os.getenv("DEBUG_API_ID")
    config["falcon_client_secret"] = os.getenv("DEBUG_API_SECRET")
    if "DEBUG_API_BASE_URL" in os.environ:
        config["falcon_base_url"] = os.getenv("DEBUG_API_BASE_URL")
    else:
        config["falcon_base_url"] = "us1"
else:
    cur_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists('%s/test.config' % cur_path):
        with open('%s/test.config' % cur_path, 'r') as file_config:
            config = json.loads(file_config.read())
    else:
        sys.exit(1)

falcon = APIHarness(
    client_id=config["falcon_client_id"],
    client_secret=config["falcon_client_secret"],
    base_url=config["falcon_base_url"]
    )


class TestUber:
    def uberCCAWS_GetAWSSettings(self):
        if falcon.command("GetAWSSettings")["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_QueryAWSAccounts(self):
        if falcon.command("QueryAWSAccounts", parameters={"limit": 1})["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_GetAWSAccounts(self):
        try:
            id_lookup = falcon.command("QueryAWSAccounts", parameters={"limit": 1})
            if id_lookup["body"]["resources"]:
                id_list = id_lookup["body"]["resources"][0]["id"]
            else:
                id_list = "123456789012"
            if falcon.command("GetAWSAccounts", ids=id_list)["status_code"] in AllowedResponses:
                return True
            else:
                return False
        except KeyError:
            pytest.skip("Workflow-related error, skipping")
            return True

    def uberCCAWS_VerifyAWSAccountAccess(self):
        try:
            id_list = falcon.command("QueryAWSAccounts", parameters={"limit": 1})["body"]["resources"][0]["id"]
            if falcon.command("VerifyAWSAccountAccess", ids=id_list)["status_code"] in AllowedResponses:
                return True
            else:
                return False
        except KeyError:
            pytest.skip("Workflow-related error, skipping")
            return True

    # Intentionally specifying this incorrectly to test the failure code path
    @force_default(defaults=["params"], default_types=[""])
    def uberCCAWS_QueryAWSAccountsForIDs(self, params: dict = None):
        if falcon.command("QueryAWSAccountsForIDs", parameters=params)["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_TestUploadDownload(self):
        FILENAME = "tests/testfile.png"
        fmt = '%Y-%m-%d %H:%M:%S'
        stddate = datetime.datetime.now().strftime(fmt)
        sdtdate = datetime.datetime.strptime(stddate, fmt)
        sdtdate = sdtdate.timetuple()
        jdate = sdtdate.tm_yday
        jdate = "{}{}".format(stddate.replace("-", "").replace(":", "").replace(" ", ""), jdate)
        SOURCE = "%s_source.png" % jdate
        TARGET = "tests/%s_target.png" % jdate
        PAYLOAD = open(FILENAME, 'rb').read()
        response = falcon.command('UploadSampleV3', file_name=SOURCE, data=PAYLOAD, content_type="application/octet-stream")
        try:
            if response["status_code"] == 429:
                pytest.skip("Rate limit hit")
            if response["body"]["resources"]:
                sha = response["body"]["resources"][0]["sha256"]
            else:
                pytest.skip("Rate limit hit")
            response = falcon.command("GetSampleV3", ids=sha)
            try:
                open(TARGET, 'wb').write(response)
            except TypeError:
                return True
            buf = 65536
            hash1 = hashlib.sha256()
            with open(FILENAME, 'rb') as f:
                while True:
                    data = f.read(buf)
                    if not data:
                        break
                    hash1.update(data)
            hash1 = hash1.hexdigest()
            hash2 = hashlib.sha256()
            with open(TARGET, 'rb') as f:
                while True:
                    data = f.read(buf)
                    if not data:
                        break
                    hash2.update(data)
            hash2 = hash2.hexdigest()
            if os.path.exists(TARGET):
                os.remove(TARGET)
            _ = falcon.command("DeleteSampleV3", ids=sha)
            if hash1 == hash2:
                return True
            else:
                return False
        except KeyError:
            # Flaky
            pytest.skip("Workflow-related error, skipping")
            return True

    def uberCCAWS_GenerateError(self):
        if falcon.command("QueryAWSAccounts", partition=0)["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_GenerateInvalidPayload(self):
        if falcon.command("refreshActiveStreamSession", partition=9,
                          parameters={"action_name": "refresh_active_stream_session"})["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_OverrideAndHeader(self):
        if falcon.command(override="GET,/cloud-connect-aws/combined/accounts/v1",
                          headers={"Nothing": "Special"})["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberContainer_TestBodyIDsPayload(self):
        successful = False
        if falcon.command("GetDeviceDetails", ids="12345678")["status_code"] in AllowedResponses:
            successful = True

        return successful

    def uberCCAWS_TestMSSP(self):
        if falcon.command("QueryDetects", limit=1)["status_code"] == 429:
            pytest.skip("Rate limit hit")
        falcon.creds["member_cid"] = "1234567890ABCDEFG"
        if not falcon.authenticate():
            falcon.creds.pop("member_cid")
            return True
        else:
            falcon.creds.pop("member_cid")
            return False

    def uberCCAWS_BadMethod(self):
        if falcon.command(action="", override="BANANA,/cloud-connect-aws/combined/accounts/v1",
                          headers={"Nothing": "Special"})["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_BadCommand(self):
        if falcon.command(action="IWantTheImpossible", parameters={"limit": 1})["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_GenerateServerError(self):
        if falcon.command("GetAWSAccounts", ids="123", data=['Kerash!'])["status_code"] == 500:
            return True
        else:
            return False

    @force_default(defaults=["params"])  # Intentionally specifying this incorrectly to test the failure code path
    def uberCCHosts_GenerateActionNameError(self, params: dict = None):
        if falcon.command("PerformActionV2",
                          parameters=params,
                          body={},
                          action_name="Squish"
                          )["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_GenerateInvalidOperationIDError(self):
        if perform_request(method="FETCH", endpoint="/somewhere/interesting")["status_code"] in AllowedResponses:
            return True
        else:
            return False

    # Token revocation is returning a 200 regardless of the token we send.
    # Changed to client ID on 08.02.21 - jshcodes@CrowdStrike
    def uberCCAWS_GenerateTokenError(self):
        #hold_token = falcon.token
        #falcon.token = "I am a bad token!"
        hold_id = falcon.creds["client_id"]
        falcon.creds["client_id"] = "Gonna Crash"
        if not falcon.deauthenticate():
            falcon.creds["client_id"] = hold_id
            return True
        else:
            falcon.creds["client_id"] = hold_id
            return False

    def uberCCAWS_BadAuthentication(self):
        falcon = APIHarness()
        if falcon.command("QueryAWSAccounts", parameters={"limit": 1})["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uberCCAWS_DisableSSLVerify(self):
        falcon = APIHarness(
            creds={
                "client_id": config["falcon_client_id"],
                "client_secret": config["falcon_client_secret"]
            }, ssl_verify=False, base_url=config["falcon_base_url"]
        )
        if falcon.command("QueryAWSAccounts", parameters={"limit": 1})["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uber_test_invalid_reserved_word_payload(self):
        params = {
            filter:"hostname:'falconpy-unit-testing'"
        }
        if falcon.command("QueryDevicesByFilter", parameters=params)["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def uber_test_distinct_field(self):
        if falcon.command("querySensorUpdateKernelsDistinct", distinct_field="flavor")["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def test_GetAWSSettings(self):
        assert self.uberCCAWS_GetAWSSettings() is True

    def test_reserved_words(self):
        assert self.uber_test_invalid_reserved_word_payload() is True

    def test_distinct_field(self):
        assert self.uber_test_distinct_field() is True

    def test_QueryAWSAccounts(self):
        assert self.uberCCAWS_QueryAWSAccounts() is True

    @pytest.mark.skipif(falcon.command("QueryAWSAccounts",
                        parameters={"limit": 1})["status_code"] == 429, reason="API rate limit reached")
    def test_GetAWSAccounts(self):
        assert self.uberCCAWS_GetAWSAccounts() is True

    def test_QueryAWSAccountsForIDs(self):
        assert self.uberCCAWS_QueryAWSAccountsForIDs() is True

    def test_UploadDownload(self):
        assert self.uberCCAWS_TestUploadDownload() is True

    def test_GenerateError(self):
        assert self.uberCCAWS_GenerateError() is True

    def test_GenerateInvalidPayload(self):
        assert self.uberCCAWS_GenerateInvalidPayload() is True

    def test_BadCommand(self):
        assert self.uberCCAWS_BadCommand() is True

    def test_OverrideAndHeader(self):
        # Also check token auto-renewal
        falcon.token_expiration = 0
        assert self.uberCCAWS_OverrideAndHeader() is True

    def test_PreferredDefaultLookup(self):
        assert bool(
            falcon.command("report_executions_download_get", ids="1234567890")["status_code"] in AllowedResponses
        ) is True

    def test_ContainerBodyIDPayload(self):
        assert self.uberContainer_TestBodyIDsPayload() is True

    def test_GenerateActionNameError(self):
        assert self.uberCCHosts_GenerateActionNameError(params=None) is True

    def test_GenerateInvalidOperationIDError(self):
        assert self.uberCCAWS_GenerateInvalidOperationIDError() is True

    def test_BadMethod(self):
        assert self.uberCCAWS_BadMethod() is True

    def test_GenerateServerError(self):
        assert self.uberCCAWS_GenerateServerError() is True

    def test_TestMSSP(self):
        assert self.uberCCAWS_TestMSSP() is True

    def test_GenerateTokenError(self):
        assert self.uberCCAWS_GenerateTokenError() is True

    def test_BadAuthentication(self):
        assert self.uberCCAWS_BadAuthentication() is True

    @pytest.mark.filterwarnings("ignore:Unverified HTTPS request is being made.*")
    def test_DisableSSLVerify(self):
        assert self.uberCCAWS_DisableSSLVerify() is True
