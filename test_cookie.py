from http.cookies import SimpleCookie
c = SimpleCookie()
c.load("csrf_token=good; csrf_token=bad")
print(c["csrf_token"].value)
