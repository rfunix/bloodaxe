import asynctest
import pytest

from bloodaxe import (
    HTTP_EXCEPTIONS,
    REQUEST_MESSAGE,
    FlowError,
    make_get_request,
    make_post_request,
    make_request,
    replace_with_template,
    show_request_message,
)


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
def flow_url():
    return "http://test-url.com/teste/"


@pytest.fixture
def response():
    return {"name": "Ragnar", "age": 33}


@pytest.fixture
def context(flow_name, response):
    return {f"{flow_name}": response}


@pytest.fixture
def mocked_echo(mocker):
    mock_echo = mocker.patch("bloodaxe.typer.echo")
    return mock_echo


def test_show_request_message(mocked_echo, flow_status, flow_name, flow_url):
    expected_message = REQUEST_MESSAGE.format(flow_status, flow_name, flow_url)

    show_request_message(flow_status, flow_name, flow_url)

    mocked_echo.assert_called_with(expected_message)


def test_replace_with_template_with_str_data(context):
    data = "age {{ req_test.age }}"
    expected_data = "age 33"

    assert replace_with_template(context, data) == expected_data


@pytest.mark.asyncio
async def test_make_get_request(httpserver, response):
    httpserver.expect_request("/teste/").respond_with_json(response)

    request_response = await make_get_request(httpserver.url_for("/teste/"))

    assert request_response == response


@pytest.mark.asyncio
@asynctest.patch("bloodaxe.httpx.AsyncClient")
@pytest.mark.parametrize("exception", [(exception,) for exception in HTTP_EXCEPTIONS])
async def test_make_get_request_raise_flow_error(mocked_httpx_client, flow_url, exception):
    mocked_httpx_client.return_value.__aenter__.return_value.get = asynctest.CoroutineMock(
        side_effect=exception
    )

    with pytest.raises(FlowError):
        await make_get_request(flow_url)

    mocked_httpx_client.return_value.__aenter__.return_value.get.assert_called_with(flow_url)


@pytest.mark.asyncio
async def test_make_post_request(httpserver, response):
    httpserver.expect_request("/test/").respond_with_json(response)

    request_response = await make_post_request(httpserver.url_for("/test/"), data={})

    assert request_response == response


@pytest.mark.asyncio
@asynctest.patch("bloodaxe.httpx.AsyncClient")
@pytest.mark.parametrize("exception", [(exception,) for exception in HTTP_EXCEPTIONS])
async def test_make_post_request_raise_flow_error(mocked_httpx_client, flow_url, exception):
    mocked_httpx_client.return_value.__aenter__.return_value.post = asynctest.CoroutineMock(
        side_effect=exception
    )

    with pytest.raises(FlowError):
        await make_post_request(flow_url, data={})

    mocked_httpx_client.return_value.__aenter__.return_value.post.assert_called_with(flow_url, data={})


@pytest.mark.asyncio
async def test_make_request(httpserver, flow_http_method, response):
    httpserver.expect_request("/test/").respond_with_json(response)

    request_response = await make_request(httpserver.url_for("/test/"), flow_http_method)

    assert request_response == response
