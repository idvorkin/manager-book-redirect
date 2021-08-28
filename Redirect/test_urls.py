# See test strategy @
# https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=azurecli-linux%2Capplication-level#unit-testing

import shared


def test_sanity_no_param():
    shared.get_html_for_redirect(None, None)


def test_sanity_anchor_only():
    shared.get_html_for_redirect("anchor-1", None)


def test_sanity_page_anchor():
    shared.get_html_for_redirect("page-1", "achor-1")


def test_sanity_page_anchor_inlined():
    # NOTE azure functions don't get access to the anchor tag :(
    shared.get_html_for_redirect("page-1#anchor1", None)


def test_no_param():
    title, page, anchor = shared.param_remap_legacy(None, None)
    assert page == "manager-book"
    assert anchor == ""


def test_anchor_only():
    title, page, anchor = shared.param_remap_legacy("anchor-1", None)
    assert page == "manager-book"
    assert anchor == "anchor-1"


def test_page_anchor():
    title, page, anchor = shared.param_remap_legacy("page-1", "anchor-1")
    assert page == "page-1"
    assert anchor == "anchor-1"
    assert title == "Anchor 1 (Page 1)"


def test_page_anchor_inlined():
    # Not azure functions can't get access to the tag (WTF?)
    title, page, anchor = shared.param_remap_legacy("page-1#anchor-1", None)
    # assert page == "page-1"
    # assert anchor == "anchor-1"
    # assert title == "Anchor 1 (Page 1)"
