import statistics

import asynctest
import pytest
import toml
import typer
from tabulate import tabulate

from bloodaxe import (
    HTTP_EXCEPTIONS,
    REQUEST_MESSAGE,
    SECONDS_MASK,
    START_MESSAGE,
    TABLE_HEADERS,
    FlowError,
    bloodaxe,
    make_api_context,
    make_get_request,
    make_post_request,
    make_request,
    replace_with_template,
    run_flow,
    show_metrics,
    show_request_message,
    start,
)


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


@pytest.mark.asyncio
async def test_make_request_with_flow_error():
    expected_error_message = "An error ocurred when make_request, invalid http method=test"
    with pytest.raises(FlowError, match=expected_error_message):
        await make_request("any_url", method="test")


def test_make_api_info_context(api_info):
    context = make_api_context(api_info)

    assert context == {"test_api": {"base_url": api_info[0]["base_url"]}}


@pytest.mark.asyncio
@pytest.mark.usefixtures("mocked_echo")
async def test_run_flow(httpserver, toml_data, get_user_response, post_user_response):
    toml_data["api"][0]["base_url"] = f"http://{httpserver.host}:{httpserver.port}"
    httpserver.expect_request("/users/1", method="GET").respond_with_json(get_user_response)
    httpserver.expect_request("/users/", method="POST").respond_with_json(post_user_response)

    flow_result = await run_flow(toml_data)

    assert flow_result.error is None
    assert flow_result.success is True
    assert flow_result.duration > 0


@pytest.mark.asyncio
@pytest.mark.usefixtures("mocked_echo")
async def test_run_flow_with_flow_error(httpserver, toml_data, get_user_response, post_user_response):
    toml_data["api"][0]["base_url"] = f"http://{httpserver.host}:{httpserver.port}"
    httpserver.expect_request("/users/1", method="GET").respond_with_json(get_user_response, status=500)

    flow_result = await run_flow(toml_data)

    assert type(flow_result.error) == FlowError
    assert flow_result.success is False
    assert flow_result.duration > 0


def test_show_metrics(mocker, mocked_echo, flows):
    mean_time = statistics.mean([flow.duration for flow in flows if flow.success])
    standard_deviation = statistics.stdev([flow.duration for flow in flows if flow.success])
    total_time = sum([flow.duration for flow in flows if flow.success])
    expected_row = [
        len([flow for flow in flows if flow.success]),
        len([flow for flow in flows if not flow.success]),
        len(flows),
        SECONDS_MASK.format(round(mean_time, 2)),
        SECONDS_MASK.format(round(standard_deviation, 2)),
        SECONDS_MASK.format(round(total_time, 2)),
    ]
    expected_tabulate = tabulate([expected_row], headers=TABLE_HEADERS)
    mocked_echo_calls = (mocker.call("\n"), mocker.call(expected_tabulate))

    show_metrics(flows, total_time)

    mocked_echo.assert_has_calls(mocked_echo_calls)


@pytest.mark.asyncio
async def test_start(
    mocker, httpserver, toml_data, mocked_echo, mocked_secho, get_user_response, post_user_response
):
    mock_show_metrics = mocker.patch("bloodaxe.show_metrics")
    httpserver.expect_request("/users/1", method="GET").respond_with_json(get_user_response)
    httpserver.expect_request("/users/", method="POST").respond_with_json(post_user_response)
    toml_data["api"][0]["base_url"] = f"http://{httpserver.host}:{httpserver.port}"
    duration = toml_data["configs"]["duration"]
    number_of_concurrent_flows = number_of_concurrent_flows = toml_data["configs"][
        "number_of_concurrent_flows"
    ]

    await start(toml_data)

    mocked_secho.assert_called_with(
        START_MESSAGE.format(number_of_concurrent_flows, duration),
        fg=typer.colors.CYAN,
        underline=True,
        bold=True,
    )

    mock_show_metrics.assert_called()


def test_bloodaxe(mocker, toml_data):
    mocked_start = mocker.patch("bloodaxe.start")
    mocked_toml_load = mocker.patch("bloodaxe.toml.load")
    mocked_toml_load.return_value = toml_data

    bloodaxe("any_path")

    mocked_toml_load.assert_called_with("any_path")
    mocked_start.assert_called_with(toml_data)


@pytest.mark.parametrize("exception", [(TypeError,), (toml.TomlDecodeError,)])
def test_bloodaxe_with_type_error(exception, mocker, mocked_echo):
    mocked_toml_load = mocker.patch("bloodaxe.toml.load")
    mocked_toml_load.side_effect = exception
    expected_error_message = "Invalid toml file"

    bloodaxe("any_path")

    mocked_echo.assert_called_with(expected_error_message)
