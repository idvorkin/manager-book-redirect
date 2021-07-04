
# The manager book redirect

### Why

I'd like to share links to [the manager book](https://idvork.in/the-manager-book), and have the url preview title match the header name.  The preview title is set from the meta tage `og:title`.

The manager book is a markdown file hosted on Jekyll, a static web site. This means it can only set `og:title` statically.

Conveniently, markdown table of contents changes headers to anchors. So if you have a `### Section title` that would be encoded as `https://base-url#section-title`.

So if we have a service that converts a query parameter to  HTML page with a dynamic `og:title`, and then does a redirect to the anchors.

To set the title dynamically, I need to have a server based solution which sets the URL based on a parameter. That's what this simple azure function does.

###  Deployment  + Usage

This webservice is deployed at https://manager-book.azurewebsites.net/topic to use it, you pass a path of topic, and a paramater of `t`, e.g.  https://manager-book.azurewebsites.net/topic?t=what-are-a-managers-responsibilities and it will turn the anchors into a `og:title` and redirect to the anchor.

### Utilities

* This is an azure function, which ends up with cold starts, to avoid run [keepwarm.sh](https://github.com/idvorkin/manager-book-redirect/blob/master/keepwarm.sh) in the background
* You need to modify the copied URL from the manager book, which you can do with this oneliner in my [zshrc](https://github.com/idvorkin/Settings/commit/239ba34ccf0ca79c2e6e7c961ca94ebaa9972fbb):
    * `alias mb="pbpaste | sed  's!idvork.in/the-manager-book#!manager-book.azurewebsites.net/!' | pbcopy"`



### Design
![UML rendered](https://www.plantuml.com/plantuml/proxy?idx=0&format=svg&src=https://raw.githubusercontent.com/idvorkin/manager-book-redirect/master/system-design.puml&c=1)
