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

REQUEST_MESSAGE = "Request {}, name={}, url={}"
START_MESSAGE = "Start bloodaxe, number_of_concurrent_flows={}, duration={} seconds"
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
            req = await client.get(url, params=params, timeout=timeout, headers=headers)
            req.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_get_request, exc={exc}")

    return req.json()


async def make_delete_request(url, timeout, params=None, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            req = await client.delete(url, params=params, timeout=timeout, headers=headers)
            req.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_delete_request, exc={exc}")

    return req.json()


async def make_put_request(url, data, timeout, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            req = await client.put(url, data=json.dumps(data), timeout=timeout, headers=headers)
            req.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_put_request, exc={exc}")

    return req.json()


async def make_patch_request(url, data, timeout, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            req = await client.patch(url, data=json.dumps(data), timeout=timeout, headers=headers)
            req.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_patch_request, exc={exc}")

    return req.json()


async def make_post_request(url, data, timeout, headers=None, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            req = await client.post(url, data=json.dumps(data), timeout=timeout, headers=headers)
            req.raise_for_status()
    except HTTP_EXCEPTIONS as exc:
        raise FlowError(f"An error occurred when make_post_request, exc={exc}")

    return req.json()


async def make_request(url, method, *args, **kwargs):
    method = method.upper()
    try:
        func = eval(HTTP_METHODS_FUNC_MAPPING[method])
    except KeyError:
        raise FlowError(f"An error ocurred when make_request, invalid http method={method}")

    return await func(url, *args, **kwargs)


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


async def run_flow(toml_data):
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
            result = await make_request(**request)
            show_request_message(SUCCESS, request["name"], request["url"])
        except FlowError as exc:
            show_request_message(ERROR, request["name"], request["url"])
            current_flow.error = exc
            current_flow.success = False
            break

        if request.get("save_result"):
            context[request["name"]] = result

    current_flow.duration = time.time() - start_flow_time

    return current_flow


async def start(toml_data):
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

        results = await asyncio.gather(*[run_flow(toml_data) for _ in range(number_of_concurrent_flows)])

        flows += tuple(results)

    show_metrics(flows, elapsed_seconds)


@app.command()
def main(flow_config_file: Path):
    try:
        toml_data = toml.load(flow_config_file)
    except (TypeError, toml.TomlDecodeError):
        typer.echo("Invalid toml file")
    else:
        asyncio.run(start(toml_data))


if __name__ == "__main__":
    app()
