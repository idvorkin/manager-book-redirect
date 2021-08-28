# See test strategy @
# https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=azurecli-linux%2Capplication-level#unit-testing

import unittest
import shared


def test_no_param():
    shared.get_html_for_redirect(None, None)


def test_anchor_only():
    shared.get_html_for_redirect("anchor-1", None)


def test_page_anchor():
    shared.get_html_for_redirect("page-1", "achor-1")
