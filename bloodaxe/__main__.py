import asyncio
import time
from multiprocessing import Pool

import click
import toml

HTTP_METHODS_FUNC_MAPPING = {"GET": "make_get_request", "POST": "make_post_request"}


@click.command()
@click.argument("config-file", default="example.toml", type=click.Path(exists=True))
def bloodaxe(config_file):
    try:
        toml_data = toml.load(config_file)
    except (TypeError, toml.TomlDecodeError):
        click.echo("Invalid toml file")

    running(toml_data)


async def make_get_request(url, *args, **kwargs):
    print("Call get")
    print(args)
    print(kwargs)

    return "GET"


async def make_post_request(url, data, *args, **kwargs):
    print("Call post")
    print(args)
    print(kwargs)

    return "POST"


async def make_request(url, method, *args, **kwargs):
    try:
        func = eval(HTTP_METHODS_FUNC_MAPPING[method])
    except KeyError:
        print("DEU RUIM KEY ERROR")

    return await func(url, *args, **kwargs)


def make_data(context, data):
    return data


async def flow(toml_data):
    context = []
    start_flow_time = time.time()

    for request in toml_data["requests"]:
        if request.get("data"):
            request["data"] = make_data(context, request["data"])

        result = await make_request(**request)

        if request.get("save_result"):
            context.append({request["name"]: result})

    flow_duration = time.time() - start_flow_time

    return flow_duration


def execute_flow(toml_data):
    result = asyncio.run(flow(toml_data))
    return result


def running(toml_data):
    duration = toml_data["configs"]["duration"]
    number_of_process = toml_data["configs"]["duration"]
    start_time = time.time()

    while True:
        elapsed_seconds = time.time() - start_time

        if elapsed_seconds >= duration:
            break

        with Pool(processes=number_of_process) as p:
            result = p.map(execute_flow, [toml_data for _ in range(number_of_process)])
            print(result)


if __name__ == "__main__":
    bloodaxe()
