import logging

import azure.functions as func
from . import shared


def main(f: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    logging.info(f.url)
    return func.HttpResponse(
        body=get_html_for_redirect(f), status_code=200, mimetype="text/html"
    )


def get_html_for_redirect(req: func.HttpRequest):
    param1 = req.route_params.get("page")
    param2 = req.route_params.get("topic")
    return shared.get_html_for_redirect(param1, param2)
