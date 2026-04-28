from artificial_u.integrations import aws_clients


def setup_function():
    aws_clients.get_boto3_session.cache_clear()
    aws_clients.get_s3_client.cache_clear()
    aws_clients.get_cloudwatch_client.cache_clear()


def teardown_function():
    aws_clients.get_boto3_session.cache_clear()
    aws_clients.get_s3_client.cache_clear()
    aws_clients.get_cloudwatch_client.cache_clear()


def test_get_s3_client_reuses_matching_session_and_client(monkeypatch):
    sessions = []

    class FakeSession:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.client_calls = []
            sessions.append(self)

        def client(self, service_name, **kwargs):
            client = {"service_name": service_name, "kwargs": kwargs, "session": self}
            self.client_calls.append(client)
            return client

    monkeypatch.setattr(aws_clients.boto3.session, "Session", FakeSession)

    client_1 = aws_clients.get_s3_client(
        endpoint_url="http://minio:9000",
        region_name="us-east-1",
        aws_access_key_id="access",
        aws_secret_access_key="secret",
        signature_version="s3v4",
    )
    client_2 = aws_clients.get_s3_client(
        endpoint_url="http://minio:9000",
        region_name="us-east-1",
        aws_access_key_id="access",
        aws_secret_access_key="secret",
        signature_version="s3v4",
    )

    assert client_1 is client_2
    assert len(sessions) == 1
    assert len(sessions[0].client_calls) == 1
    assert sessions[0].kwargs == {
        "region_name": "us-east-1",
        "aws_access_key_id": "access",
        "aws_secret_access_key": "secret",
    }
    assert client_1["service_name"] == "s3"
    assert client_1["kwargs"]["endpoint_url"] == "http://minio:9000"


def test_get_s3_client_reuses_session_across_distinct_s3_clients(monkeypatch):
    sessions = []

    class FakeSession:
        def __init__(self, **kwargs):
            sessions.append(self)

        def client(self, service_name, **kwargs):
            return {"service_name": service_name, "kwargs": kwargs, "session": self}

    monkeypatch.setattr(aws_clients.boto3.session, "Session", FakeSession)

    client_1 = aws_clients.get_s3_client(
        endpoint_url="http://minio-a:9000",
        region_name="us-east-1",
        aws_access_key_id="access",
        aws_secret_access_key="secret",
        signature_version="s3v4",
    )
    client_2 = aws_clients.get_s3_client(
        endpoint_url="http://minio-b:9000",
        region_name="us-east-1",
        aws_access_key_id="access",
        aws_secret_access_key="secret",
        signature_version="s3v4",
    )

    assert client_1 is not client_2
    assert client_1["session"] is client_2["session"]
    assert len(sessions) == 1
