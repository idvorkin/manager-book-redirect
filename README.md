
# The manager book redirect

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
