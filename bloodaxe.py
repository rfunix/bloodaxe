import asyncio
import copy
import json
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import toml
import typer
from httpx._exceptions import ConnectTimeout, HTTPError, NetworkError, ReadTimeout
from jinja2 import Template
from tabulate import tabulate

HTTP_METHODS_FUNC_MAPPING = {
    "GET": "make_get_request",
    "POST": "make_post_request",
    "PUT": "make_put_request",
    "PATCH": "make_patch_request",
    "DELETE": "make_delete_request",
}

SUCCESS = typer.style("success", fg=typer.colors.GREEN, bold=True)
ERROR = typer.style("error", fg=typer.colors.RED, bold=True)
FLOW_ERROR = typer.style("FlowError", bg=typer.colors.RED, fg=typer.colors.WHITE, bold=True)

REQUEST_MESSAGE = "Request {}, name={}, url={}"
START_MESSAGE = "Start bloodaxe, number_of_concurrent_flows={}, duration={} seconds"
RESPONSE_DATA_CHECK_FAILED_MESSAGE = "Failed to response check, request={}, " "expected data={}, received={}"
RESPONSE_STATUS_CODE_CHECK_FAILED_MESSAGE = (
    "Failed to status_code check, request={}, " "expected status_code={}, received={}"
)
SECONDS_MASK = "{0:.2f}"
DEFAULT_TIMEOUT = 10

TABLE_HEADERS = [
    "Total success flows",
    "Total error flows",
    "Total flows",
    "Mean time",
    "Standard deviation",
    "Total time",
]

HTTP_EXCEPTIONS = (HTTPError, NetworkError, ReadTimeout, ConnectTimeout)

app = typer.Typer()


class FlowError(Exception):
    pass


@dataclass
class Flow:
    duration: float = 0
    error: FlowError = None
    success: bool = True


def show_request_message(status, name, url):
    message = REQUEST_MESSAGE.format(status, name, url)
    typer.echo(message)


def replace_with_template(context, data):
    if isinstance(data, dict):
        data = json.dumps(data)

    template = Template(data)

    return template.render(**context)


async def make_get_request(url, timeout, params=None, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=timeout, headers=headers)
            resp.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_get_request, exc={exc}")

    return resp


async def make_delete_request(url, timeout, params=None, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, params=params, timeout=timeout, headers=headers)
            resp.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_delete_request, exc={exc}")

    return resp


async def make_put_request(url, data, timeout, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(url, data=data, timeout=timeout, headers=headers)
            resp.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_put_request, exc={exc}")

    return resp


async def make_patch_request(url, data, timeout, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(url, data=data, timeout=timeout, headers=headers)
            resp.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_patch_request, exc={exc}")

    return resp


async def make_post_request(url, data, timeout, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=data, timeout=timeout, headers=headers)
            resp.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_post_request, exc={exc}")

    return resp


def check_response_data(request_name, data, expected_data, context):
    expected_data = json.loads(replace_with_template(context, expected_data))
    error_msg = RESPONSE_DATA_CHECK_FAILED_MESSAGE.format(request_name, expected_data, data)

    try:
        assert data == expected_data
    except AssertionError:
        raise FlowError(error_msg)


def check_response_status_code(request_name, status_code, expected_status_code):
    error_msg = RESPONSE_STATUS_CODE_CHECK_FAILED_MESSAGE.format(
        request_name, expected_status_code, status_code
    )
    try:
        assert status_code == expected_status_code
    except AssertionError:
        raise FlowError(error_msg)


def check_response(request_name, data, status_code, context, response_check=None):
    if response_check.get("data"):
        check_response_data(request_name, data, response_check["data"], context)
    if response_check.get("status_code"):
        check_response_status_code(request_name, status_code, response_check["status_code"])


async def make_request(context, name, url, method, response_check=None, *args, **kwargs):
    method = method.upper()
    try:
        func = eval(HTTP_METHODS_FUNC_MAPPING[method])
    except KeyError:
        raise FlowError(f"An error ocurred when make_request, invalid http method={method}")

    resp = await func(url, *args, **kwargs)
    data = resp.json()
    status_code = resp.status_code

    if response_check:
        check_response(name, data, status_code, context, response_check)

    return data


def show_metrics(flows, total_time):
    success_flows = [flow for flow in flows if flow.success]
    error_flows = [flow for flow in flows if flow.error]
    mean_time = 0
    standard_deviation = 0

    if len(success_flows) > 1:
        mean_time = statistics.mean([flow.duration for flow in success_flows])
        standard_deviation = statistics.stdev([flow.duration for flow in success_flows])

    row = [
        len(success_flows),
        len(error_flows),
        len(flows),
        SECONDS_MASK.format(round(mean_time, 2)),
        SECONDS_MASK.format(round(standard_deviation, 2)),
        SECONDS_MASK.format(round(total_time, 2)),
    ]

    typer.echo("\n")
    typer.echo(tabulate([row], headers=TABLE_HEADERS))


def from_file(file_path):
    with open(file_path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid json file, file={file_path}")

        return data


def generate_request_data(context, data):
    if data.get("from_file"):
        data = from_file(data.get("from_file"))

    return json.loads(replace_with_template(context, data))


def generate_request_headers(context, headers):
    return json.loads(replace_with_template(context, headers))


def generate_request_params(context, params):
    return json.loads(replace_with_template(context, params))


def make_api_context(api_info):
    context = {}
    for api in api_info:
        context[api["name"]] = {"base_url": api["base_url"]}

        env_vars = api.get("envvars", {})
        for key, value in env_vars.items():
            context[api["name"]][key] = os.environ[value]

    return context


async def run_flow(toml_data, verbose):
    flow_config = copy.deepcopy(toml_data)
    context = make_api_context(flow_config.get("api")) or {}
    start_flow_time = time.time()
    current_flow = Flow()

    for request in flow_config["request"]:
        request["timeout"] = request.get("timeout") or DEFAULT_TIMEOUT
        request["url"] = replace_with_template(context, request["url"])

        if request.get("data"):
            request["data"] = generate_request_data(context, request["data"])

        if request.get("params"):
            request["params"] = generate_request_params(context, request["params"])

        if request.get("headers"):
            request["headers"] = generate_request_headers(context, request["headers"])

        try:
            result = await make_request(context, **request)
            show_request_message(SUCCESS, request["name"], request["url"])
        except FlowError as exc:
            show_request_message(ERROR, request["name"], request["url"])
            current_flow.error = exc
            current_flow.success = False
            if verbose:
                typer.secho(f"{FLOW_ERROR}: {exc}")
            break

        if request.get("save_result"):
            context[request["name"]] = result

    current_flow.duration = time.time() - start_flow_time

    return current_flow


async def start(toml_data, verbose):
    flows = tuple()
    duration = toml_data["configs"]["duration"]
    number_of_concurrent_flows = toml_data["configs"]["number_of_concurrent_flows"]

    typer.secho(
        START_MESSAGE.format(number_of_concurrent_flows, duration),
        fg=typer.colors.CYAN,
        underline=True,
        bold=True,
    )

    start_time = time.time()
    while True:
        elapsed_seconds = time.time() - start_time

        if elapsed_seconds >= duration:
            break

        results = await asyncio.gather(
            *[run_flow(toml_data, verbose) for _ in range(number_of_concurrent_flows)]
        )

        flows += tuple(results)

    show_metrics(flows, elapsed_seconds)


@app.command()
def main(flow_config_file: Path, verbose: bool = False):
    try:
        toml_data = toml.load(flow_config_file)
    except (TypeError, toml.TomlDecodeError):
        typer.echo("Invalid toml file")
    else:
        asyncio.run(start(toml_data, verbose))


if __name__ == "__main__":
    app()
