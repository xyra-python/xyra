
import socketify
import asyncio
import sys

def run_server():
    app = socketify.App()

    async def handler(res, req):
        try:
            method = req.get_method() # Should work
            await asyncio.sleep(0.1)

            # Try accessing req after await
            url = req.get_url()
            res.write_status(200)
            res.end(f"Method: {method}, URL: {url}")
        except Exception as e:
            # We can't easily log here if stdout is captured but let's try
            sys.stderr.write(f"Error after await: {e}\n")
            try:
                res.write_status(500)
                res.end(str(e))
            except:
                pass

    app.get("/", handler)
    app.listen(3002, lambda config: print("Listening on 3002"))
    app.run()

if __name__ == "__main__":
    run_server()
