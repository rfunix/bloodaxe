import json
import statistics
from unittest.mock import patch

import asynctest
import pytest
import toml
import typer
from tabulate import tabulate

from bloodaxe import (
    DEFAULT_TIMEOUT,
    HTTP_EXCEPTIONS,
    REQUEST_MESSAGE,
    RESPONSE_DATA_CHECK_FAILED_MESSAGE,
    RESPONSE_STATUS_CODE_CHECK_FAILED_MESSAGE,
    SECONDS_MASK,
    START_MESSAGE,
    TABLE_HEADERS,
    FlowError,
    check_response_data,
    check_response_status_code,
    from_file,
    generate_request_data,
    generate_request_headers,
    generate_request_params,
    main,
    make_api_context,
    make_delete_request,
    make_get_request,
    make_patch_request,
    make_post_request,
    make_put_request,
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

    request_response = await make_get_request(httpserver.url_for("/teste/"), timeout=DEFAULT_TIMEOUT)

    assert request_response.json() == response
    assert request_response.status_code == 200


@pytest.mark.asyncio
@asynctest.patch("bloodaxe.httpx.AsyncClient")
@pytest.mark.parametrize("exception", [(exception,) for exception in HTTP_EXCEPTIONS])
async def test_make_get_request_raise_flow_error(mocked_httpx_client, flow_url, exception):
    mocked_httpx_client.return_value.__aenter__.return_value.get = asynctest.CoroutineMock(
        side_effect=exception
    )

    params = {"name": "Ivy"}
    headers = {"Authorization": "token"}

    with pytest.raises(FlowError):
        await make_get_request(flow_url, params=params, timeout=DEFAULT_TIMEOUT, headers=headers)

    mocked_httpx_client.return_value.__aenter__.return_value.get.assert_called_with(
        flow_url, params=params, timeout=DEFAULT_TIMEOUT, headers=headers
    )


@pytest.mark.asyncio
async def test_make_delete_request(httpserver, response):
    httpserver.expect_request("/teste/").respond_with_json(response)

    request_response = await make_delete_request(httpserver.url_for("/teste/"), timeout=DEFAULT_TIMEOUT)

    assert request_response.json() == response
    assert request_response.status_code == 200


@pytest.mark.asyncio
@asynctest.patch("bloodaxe.httpx.AsyncClient")
@pytest.mark.parametrize("exception", [(exception,) for exception in HTTP_EXCEPTIONS])
async def test_make_delete_request_raise_flow_error(mocked_httpx_client, flow_url, exception):
    mocked_httpx_client.return_value.__aenter__.return_value.delete = asynctest.CoroutineMock(
        side_effect=exception
    )

    params = {"name": "Ivy"}
    headers = {"Authorization": "token"}

    with pytest.raises(FlowError):
        await make_delete_request(flow_url, params=params, timeout=DEFAULT_TIMEOUT, headers=headers)

    mocked_httpx_client.return_value.__aenter__.return_value.delete.assert_called_with(
        flow_url, params=params, timeout=DEFAULT_TIMEOUT, headers=headers
    )


@pytest.mark.asyncio
async def test_make_post_request(httpserver, response):
    httpserver.expect_request("/test/").respond_with_json(response)

    request_response = await make_post_request(httpserver.url_for("/test/"), data={}, timeout=DEFAULT_TIMEOUT)

    assert request_response.json() == response
    assert request_response.status_code == 200


@pytest.mark.asyncio
@asynctest.patch("bloodaxe.httpx.AsyncClient")
@pytest.mark.parametrize("exception", [(exception,) for exception in HTTP_EXCEPTIONS])
async def test_make_post_request_raise_flow_error(mocked_httpx_client, flow_url, exception):
    mocked_httpx_client.return_value.__aenter__.return_value.post = asynctest.CoroutineMock(
        side_effect=exception
    )
    data = {"name": "lagertha"}
    headers = {"Authorization": "token"}

    with pytest.raises(FlowError):
        await make_post_request(flow_url, data=data, timeout=DEFAULT_TIMEOUT, headers=headers)

    mocked_httpx_client.return_value.__aenter__.return_value.post.assert_called_with(
        flow_url, data=data, timeout=DEFAULT_TIMEOUT, headers=headers
    )


@pytest.mark.asyncio
async def test_make_put_request(httpserver, response):
    httpserver.expect_request("/test/").respond_with_json(response)

    request_response = await make_put_request(httpserver.url_for("/test/"), data={}, timeout=DEFAULT_TIMEOUT)

    assert request_response.json() == response
    assert request_response.status_code == 200


@pytest.mark.asyncio
@asynctest.patch("bloodaxe.httpx.AsyncClient")
@pytest.mark.parametrize("exception", [(exception,) for exception in HTTP_EXCEPTIONS])
async def test_make_put_request_raise_flow_error(mocked_httpx_client, flow_url, exception):
    mocked_httpx_client.return_value.__aenter__.return_value.put = asynctest.CoroutineMock(
        side_effect=exception
    )
    data = {"name": "lagertha"}
    headers = {"Authorization": "token"}

    with pytest.raises(FlowError):
        await make_put_request(flow_url, data=data, timeout=DEFAULT_TIMEOUT, headers=headers)

    mocked_httpx_client.return_value.__aenter__.return_value.put.assert_called_with(
        flow_url, data=data, timeout=DEFAULT_TIMEOUT, headers=headers
    )


@pytest.mark.asyncio
async def test_make_patch_request(httpserver, response):
    httpserver.expect_request("/test/").respond_with_json(response)

    request_response = await make_patch_request(
        httpserver.url_for("/test/"), data={}, timeout=DEFAULT_TIMEOUT
    )

    assert request_response.json() == response
    assert request_response.status_code == 200


@pytest.mark.asyncio
@asynctest.patch("bloodaxe.httpx.AsyncClient")
@pytest.mark.parametrize("exception", [(exception,) for exception in HTTP_EXCEPTIONS])
async def test_make_patch_request_raise_flow_error(mocked_httpx_client, flow_url, exception):
    mocked_httpx_client.return_value.__aenter__.return_value.patch = asynctest.CoroutineMock(
        side_effect=exception
    )
    data = {"name": "lagertha"}
    headers = {"Authorization": "token"}

    with pytest.raises(FlowError):
        await make_patch_request(flow_url, data=data, timeout=DEFAULT_TIMEOUT, headers=headers)

    mocked_httpx_client.return_value.__aenter__.return_value.patch.assert_called_with(
        flow_url, data=data, timeout=DEFAULT_TIMEOUT, headers=headers
    )


@pytest.mark.asyncio
async def test_make_request(httpserver, flow_http_method, response, context):
    httpserver.expect_request("/test/").respond_with_json(response)

    request_response = await make_request(
        context, "req_name", httpserver.url_for("/test/"), flow_http_method, timeout=DEFAULT_TIMEOUT
    )

    assert request_response == response


@pytest.mark.asyncio
async def test_make_request_with_flow_error(context):
    expected_error_message = "An error ocurred when make_request, invalid http method=TEST"
    with pytest.raises(FlowError, match=expected_error_message):
        await make_request(context, "any_request", "any_url", method="test")


def test_make_api_info_context(api_info):
    context = make_api_context(api_info)

    assert context == {"test_api": {"base_url": api_info[0]["base_url"]}}


@pytest.mark.asyncio
@pytest.mark.usefixtures("mocked_echo")
async def test_run_flow(httpserver, toml_data, get_user_response, post_user_response):
    toml_data["api"][0]["base_url"] = f"http://{httpserver.host}:{httpserver.port}"
    httpserver.expect_request("/users/1", method="GET").respond_with_json(get_user_response)
    httpserver.expect_request("/users/1", method="DELETE").respond_with_json(get_user_response)
    httpserver.expect_request("/users/", method="POST").respond_with_json(post_user_response)
    httpserver.expect_request("/users/", method="PATCH").respond_with_json(post_user_response)
    httpserver.expect_request("/users/", method="PUT").respond_with_json(post_user_response)

    flow_result = await run_flow(toml_data, verbose=False)

    assert flow_result.error is None
    assert flow_result.success is True
    assert flow_result.duration > 0


@pytest.mark.asyncio
@pytest.mark.usefixtures("mocked_echo")
async def test_run_flow_with_flow_error(httpserver, toml_data, get_user_response, post_user_response):
    toml_data["api"][0]["base_url"] = f"http://{httpserver.host}:{httpserver.port}"
    httpserver.expect_request("/users/1", method="GET").respond_with_json(get_user_response, status=500)

    flow_result = await run_flow(toml_data, verbose=False)

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

    await start(toml_data, verbose=False)

    mocked_secho.assert_called_with(
        START_MESSAGE.format(number_of_concurrent_flows, duration),
        fg=typer.colors.CYAN,
        underline=True,
        bold=True,
    )

    mock_show_metrics.assert_called()


def test_main(mocker, toml_data):
    mocked_start = mocker.patch("bloodaxe.start")
    mocked_toml_load = mocker.patch("bloodaxe.toml.load")
    mocked_toml_load.return_value = toml_data

    main("any_path")

    mocked_toml_load.assert_called_with("any_path")
    mocked_start.assert_called_with(toml_data, False)


@pytest.mark.parametrize("exception", [(TypeError,), (toml.TomlDecodeError,)])
def test_main_with_type_error(exception, mocker, mocked_echo):
    mocked_toml_load = mocker.patch("bloodaxe.toml.load")
    mocked_toml_load.side_effect = exception
    expected_error_message = "Invalid toml file"

    main("any_path")

    mocked_echo.assert_called_with(expected_error_message)


def test_from_file(mocker):
    json_data = {"name": "eric bloodaxe"}
    file_path = "teste.json"
    mock_json_load = mocker.patch("bloodaxe.json.loads")
    mock_json_load.return_value = json_data

    with patch("builtins.open", mocker.mock_open()) as mock_file:
        data = from_file(file_path)

    assert data == json_data
    mock_json_load.assert_called()
    mock_file.assert_called_with(file_path)


def test_from_file_with_json_decode_error(mocker):
    file_path = "teste.json"
    expected_error_message = f"Invalid json file, file={file_path}"
    mock_json_load = mocker.patch("bloodaxe.json.loads")
    mock_json_load.side_effect = json.JSONDecodeError("error", "\n\n", 1)

    with patch("builtins.open", mocker.mock_open()) as mock_file:
        with pytest.raises(ValueError, match=expected_error_message):
            from_file(file_path)

    mock_json_load.assert_called()
    mock_file.assert_called_with(file_path)


def test_generate_request_data(mocker, toml_data, context):
    context["get_user"] = {"firstname": "Freydis", "Lastname": "Eriksdottir", "status": "active"}
    context["user_api"] = {"base_url": "any_url"}
    data = toml_data["request"][1]["data"]
    expected_request_data = json.loads(replace_with_template(context, data))

    request_data = generate_request_data(context, data)

    assert request_data == expected_request_data


def test_generate_request_data_with_from_file(mocker, toml_data, context):
    context["get_user"] = {"firstname": "Freydis", "Lastname": "Eriksdottir", "status": "active"}
    context["user_api"] = {"base_url": "any_url"}
    data = toml_data["request"][1]["data"]
    expected_request_data = json.loads(replace_with_template(context, data))
    mock_from_file = mocker.patch("bloodaxe.from_file")
    mock_from_file.return_value = data
    file_path = "teste.json"
    from_file_data = {"from_file": file_path}

    request_data = generate_request_data(context, from_file_data)

    assert request_data == expected_request_data
    mock_from_file.assert_called_with(file_path)


def test_generate_request_params():
    context = {"viking_api": {"name": "Harald"}}
    params = {"name": "{{ viking_api.name }}"}
    expected_params = json.loads(replace_with_template(context, params))

    request_params = generate_request_params(context, params)

    assert request_params == expected_params


def test_generate_request_headers():
    context = {"viking_api": {"token": "token_value"}}
    headers = {"Authorization": "{{ viking_api.token }}"}
    expected_headers = {"Authorization": "token_value"}

    request_headers = generate_request_headers(context, headers)

    assert request_headers == expected_headers


def test_check_response_data():
    context = {}
    request_name = "test_req"
    data = {"name": "test"}
    expected_data = data

    check_response_data(request_name, data, expected_data, context)


def test_check_response_data_with_flow_error():
    context = {}
    request_name = "test_req"
    data = {"name": "test"}
    expected_data = data.copy()
    expected_data["name"] = "other_name"

    error_msg = RESPONSE_DATA_CHECK_FAILED_MESSAGE.format(request_name, expected_data, data)

    with pytest.raises(FlowError, match=error_msg):
        check_response_data(request_name, data, expected_data, context)


def test_check_response_status_code():
    request_name = "test_req"
    status_code = 201
    expected_status_code = status_code

    check_response_status_code(request_name, status_code, expected_status_code)


def test_check_response_status_code_with_flow_error():
    request_name = "test_req"
    status_code = 201
    expected_status_code = 200

    error_msg = RESPONSE_STATUS_CODE_CHECK_FAILED_MESSAGE.format(
        request_name, expected_status_code, status_code
    )

    with pytest.raises(FlowError, match=error_msg):
        check_response_status_code(request_name, status_code, expected_status_code)
