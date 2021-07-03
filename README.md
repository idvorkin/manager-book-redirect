
# The manager book redirect

### Why

I'd like to share links to [the manager book](https://idvork.in/the-manager-book), and have the url preview title match the header name.  The preview title is set from the meta tage `og:title`.

The manager book is a markdown file hosted on Jekyll, a static web site. This means it can only set `og:title` statically.

Conveniently, markdown table of contents changes headers to fragments. So if you have a `### Section title` that would be encoded as `https://base-url#section-title`.

So if we have a service that converts a query parameter to  HTML page with a dynamic `og:title`, and then does a redirect to the fragment.

To set the title dynamically, I need to have a server based solution which sets the URL based on a parameter. That's what this simple azure function does.

###  Deployment  + Usage

This webservice is deployed at https://manager-book.azurewebsites.net/topic to use it, you pass a path of topic, and a paramater of `t`, e.g.  https://manager-book.azurewebsites.net/topic?t=what-are-a-managers-responsibilities and it will turn the fragment into a `og:title` and redirect to the fragment.



