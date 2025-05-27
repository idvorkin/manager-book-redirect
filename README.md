# The manager book redirect


**NOTE:**  This used to be done with azure funtions. That's FaaS which is great, but if you're doing FaaS, I highly recommend using the much simpler modal. I'm starting that in 2024-04-20.



---

**NOTE** This used to only redirect to the manager book (thus the name). Now it redirects to any page on the blog


## Why

I'd like to share links to [my blog ](https://idvork.in/), and have the url preview have a title match the header name. (The title is set from the meta tage `og:title`.)

But, the blog is markdown file hosted on Jekyll, a static web site. This means the manager book can only set `og:title` statically.

## How

### Markdown save time

Conveniently, markdown editors create a table of contents by changing headers to anchors. So if you have a `### Section title` that would be encoded as `https://base-url#section-title`.

### Browser Runtime

We can make a service that converts a path to  an HTML page with a dynamic `og:title`, and then does a redirect to the path.

![UML rendered](https://www.plantuml.com/plantuml/proxy?idx=0&format=svg&src=https://raw.githubusercontent.com/idvorkin/manager-book-redirect/master/system-design.puml&c=1)



### Copy URL time

You need to modify the copied URL from the manager book, which you can do with this oneliner in my [zshrc](https://github.com/idvorkin/Settings/commit/239ba34ccf0ca79c2e6e7c961ca94ebaa9972fbb):

`alias mb="pbpaste | sed  's!idvork.in/!idvorkin.azurewebsites.net/!'| sed 's!#!/!' | pbcopy`


###  Deployment  + Hosting

This webservice is deployed to an azure function at  https://idvorkin.azurewebsites.net  via git hook.  Include a path to be converted to the title and anchor link.

Pushing to main deploys to https://manager-book-dev.azurewebsites.net

Pushing to deploy-prod deploys to  https://idvorkin.azurewebsites.net

### Keep warm scirpt

Becauses this is an azure function, it has cold starts, to avoid these, run [keepwarm.sh](https://github.com/idvorkin/manager-book-redirect/blob/master/keepwarm.sh) in the background


## Development Setup

This project uses `just` as a command runner and `uv` for Python environment and package management. Pre-commit hooks are configured for automated linting and formatting.

### Initial Setup

1.  Ensure you have `just` and `uv` installed.
    *   `just`: See [installation instructions](https://github.com/casey/just#installation).
    *   `uv`: See [installation instructions](https://github.com/astral-sh/uv#installation).
2.  Set up the Python virtual environment and install dependencies:
    ```bash
    just install
    ```
3.  Activate the virtual environment:
    ```bash
    source .venv/bin/activate
    ```
4.  Install pre-commit hooks:
    ```bash
    pre-commit install
    ```

### Running Tests

*   To run all tests:
    ```bash
    just test
    ```
*   To run fast tests (typically a subset, used by pre-commit):
    ```bash
    just fast-test
    ```

### Pre-commit Hooks

Pre-commit hooks are configured to automatically lint and format code using tools like Ruff (Python), Biome (JSON), and Prettier (Markdown/HTML). These hooks will run automatically when you commit changes. You can also run them manually on all files:
```bash
pre-commit run --all-files
```
