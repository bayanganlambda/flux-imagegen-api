from flask import Flask, send_file, request
from io import BytesIO
from nightcafe import NightCafe

app = Flask(__name__)
provider = NightCafe()

@app.route("/create", methods=["GET"])
def create(): 
    if request.method == "GET": 
        prompt = request.values.get("prompt")
        show = request.values.get("show", default=0, type=int)

        if not prompt: 
            return "no prompt specified!" 
        
        if show < 0 or show > 1: 
            return "show image value must be value between 1 (yes) or 0 (no)"
        
        if show: 
            result = provider.create(prompt)
            img = BytesIO(result)
            return send_file(img, mimetype="image/jpeg")
        
        result = provider.create(prompt, return_url=True)
        return result

@app.route("/", methods=["GET"])
def index(): 
    return "hello world!"
    
if __name__ == "__main__": 
    app.run()