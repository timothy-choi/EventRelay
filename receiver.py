from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    print("\n=== RECEIVED WEBHOOK ===")
    print(body)

    headers = dict(req.headers)
    print("\nHeaders:")
    for k, v in headers.items():
        if k.lower().startswith("x-hookhub"):
            print(f"{k}: {v}")

    return {"status": "ok"}