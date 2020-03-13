import asyncio
import json
import time
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

import httpx
import toml
import typer
from httpx._exceptions import NetworkError
from httpx.exceptions import HTTPError
from jinja2 import Template

HTTP_METHODS_FUNC_MAPPING = {"GET": "make_get_request", "POST": "make_post_request"}
SUCCESS = typer.style("success", fg=typer.colors.GREEN, bold=True)
ERROR = typer.style("error", fg=typer.colors.RED, bold=True)

REQUEST_MESSAGE = "Request {}, name={}, url={}"
START_MESSAGE = "Start bloodaxe, number_of_process={}, duration={} seconds"


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


async def make_get_request(url, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            r.raise_for_status()
    except (HTTPError, NetworkError) as exc:
        raise FlowError(f"An error occurred when make_get_request, exc={exc}")

    return r.json()


async def make_post_request(url, data, *args, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, data=json.loads(data))
            r.raise_for_status()
    except (HTTPError, NetworkError) as exc:
        raise FlowError(f"An error occurred when make_post_request, exc={exc}")

    return r.json()


async def make_request(url, method, *args, **kwargs):
    try:
        func = eval(HTTP_METHODS_FUNC_MAPPING[method])
    except KeyError:
        raise FlowError(f"An error ocurred when make_request, invalid http method={method}")

    return await func(url, *args, **kwargs)


def make_api_info_context(api_info):
    context = {}
    for api in api_info:
        context[api["name"]] = {"base_url": api["base_url"]}

    return context


async def flow(toml_data):
    context = make_api_info_context(toml_data.get("api")) or {}
    start_flow_time = time.time()
    current_flow = Flow()

    for request in toml_data["request"]:
        request["url"] = replace_with_template(context, request["url"])
        if request.get("data"):
            request["data"] = replace_with_template(context, request["data"])
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


def execute_flow(toml_data):
    result = asyncio.run(flow(toml_data))
    return result


def show_metrics(flows):
    success = len([flow for flow in flows if flow.success])
    errors = len([flow for flow in flows if flow.error])

    typer.echo(f"Total flows={len(flows)}, success={success}, errors={errors}")


def start(toml_data):
    flows = tuple()
    duration = toml_data["configs"]["duration"]
    number_of_process = toml_data["configs"]["number_of_process"]

    typer.secho(
        START_MESSAGE.format(number_of_process, duration), fg=typer.colors.CYAN, underline=True, bold=True
    )

    start_time = time.time()
    while True:
        elapsed_seconds = time.time() - start_time

        if elapsed_seconds >= duration:
            break

        with Pool(processes=number_of_process) as p:
            flows += tuple(p.map(execute_flow, [toml_data for _ in range(number_of_process)]))

    show_metrics(flows)


def bloodaxe(config_file: Path):
    try:
        toml_data = toml.load(config_file)
    except (TypeError, toml.TomlDecodeError):
        typer.echo("Invalid toml file")

    start(toml_data)


if __name__ == "__main__":
    typer.run(bloodaxe)
