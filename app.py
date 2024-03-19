from flask import app, Flask, request
from agent_call import agent_executor

app = Flask(__name__)


@app.route("/predict", methods=["POST"])
def predict():
    query = request.get_json()["query"]
    output = agent_executor.invoke({"input": query})
    return output["output"]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
