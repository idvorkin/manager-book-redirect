import logging

import azure.functions as func


def main(f: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    return func.HttpResponse(
            body = get_html(f),
            status_code=200,
            mimetype='text/html'
    )

def get_html(req: func.HttpRequest):
    fragment = req.params.get("t")
    if not fragment:
        fragment = "the-manager-book"

    title = fragment.replace('-',' ').capitalize()
    description = "Igor's book of management"
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <!-- Open Graph
        https://stackoverflow.com/questions/19778620/provide-an-image-for-whatsapp-link-sharing
    -->
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta name="description" content="{description}" />
    <meta property="og:url" content="https://idvork.in/the-manager-book#{fragment}" />
    <meta property="og:image"
        content="https://github.com/idvorkin/blob/raw/master/idvorkin-manager-book-1200-628.png" />

<!-- Icons -->
    <link rel="apple-touch-icon" sizes="180x180"
    href="https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-180-180.png" />
    <link rel="icon" type="image/png" sizes="32x32"
    href="https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-32-32.png" />
</head>
<body>
    <script> 
        window.location.href = "https://idvork.in/the-manager-book#{fragment}";
    </script>
    Redirector:
    {req.params}
</body>
</html>
"""
    return html