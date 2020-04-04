import pytest

from bloodaxe import Flow, FlowError


@pytest.fixture
def flows():
    return (
        Flow(duration=1.0, error=None, success=True),
        Flow(duration=2.0, error=None, success=True),
        Flow(duration=3.0, error=None, success=True),
        Flow(duration=4.0, error=None, success=True),
        Flow(duration=5.0, error=FlowError("teste error"), success=False),
    )


@pytest.fixture
def toml_data():
    return {
        "configs": {"number_of_concurrent_flows": 1, "duration": 1},
        "api": [
            {"name": "user_api", "base_url": "http://localhost:46549", "envvars": {"client_id": "CLIENT_ID"}}
        ],
        "request": [
            {
                "name": "get_user",
                "url": "{{ user_api.base_url }}/users/1",
                "method": "GET",
                "save_result": True,
                "params": {"name": "Bjorn"},
                "headers": {"Content-type": "application/json"},
            },
            {
                "name": "create_new_user",
                "url": "{{  user_api.base_url }}/users/",
                "method": "POST",
                "data": {
                    "firstname": "{{ get_user.firstname }} test",
                    "lastname": "{{ get_user.lastname}} test",
                    "status": "{{ get_user.status }} test",
                },
                "response_check": {
                    "data": {
                        "firstname": "{{ get_user.firstname }} test",
                        "lastname": "{{ get_user.lastname }} test",
                        "status": "{{ get_user.status }} test",
                    }
                },
            },
            {
                "name": "update_user",
                "url": "{{  user_api.base_url }}/users/",
                "method": "PUT",
                "data": {
                    "firstname": "{{ get_user.firstname }} testx",
                    "lastname": "{{ get_user.lastname }} testx",
                    "status": "{{ get_user.status }} testx",
                },
            },
            {
                "name": "partial_update_user",
                "url": "{{  user_api.base_url }}/users/",
                "method": "PATCH",
                "data": {
                    "firstname": "{{ get_user.firstname }} testz",
                    "lastname": "{{ get_user.lastname }} testz",
                },
            },
            {
                "name": "delete_user",
                "url": "{{ user_api.base_url }}/users/1",
                "method": "DELETE",
                "save_result": True,
                "params": {"name": "Ivar"},
                "headers": {"Content-type": "application/json"},
            },
        ],
    }


@pytest.fixture
def flow_status():
    return "SUCCESS"


@pytest.fixture
def flow_http_method():
    return "GET"


@pytest.fixture
def flow_name():
    return "req_test"


@pytest.fixture
def response():
    return {"name": "Ragnar", "age": 33}


@pytest.fixture
def context(flow_name, response):
    return {f"{flow_name}": response}


@pytest.fixture
def api_info():
    return [{"name": "test_api", "base_url": "http://test-url.com"}]


@pytest.fixture
def flow_url(api_info):
    return f"{api_info[0]['base_url']}/teste/"


@pytest.fixture
def mocked_echo(mocker):
    mock_echo = mocker.patch("bloodaxe.typer.echo")
    return mock_echo


@pytest.fixture
def mocked_secho(mocker):
    mock_secho = mocker.patch("bloodaxe.typer.secho")
    return mock_secho


@pytest.fixture
def get_user_response():
    return {"firstname": "Arnfinn", "lastname": "Bjornsson", "status": "active"}


@pytest.fixture
def post_user_response(get_user_response):
    return {
        "firstname": f"{get_user_response['firstname']} test",
        "lastname": f"{get_user_response['lastname']} test",
        "status": f"{get_user_response['status']} test",
    }
