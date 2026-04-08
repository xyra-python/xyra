## 2024-04-08 - Lazy Initialize Response Headers
**Learning:** Response.headers previously instantiated a CIMultiDict (Headers) per request, which caused significant overhead. Initializing this on-demand using a property avoids dictionary allocations for simple plain text/JSON endpoints that don't set custom headers.
**Action:** Always lazy load expensive objects in hot paths like the request/response lifecycle.
