from flask import Flask, jsonify, request
from base_model import movefile_cache, add_to_movefile_cache

app = Flask(__name__)

@app.route("/")
def getMoves():
    args = request.args.to_dict()
    moves = movefile_cache.get(args.get('filename'), None)
    if moves is None:
        moves = add_to_movefile_cache(args.get('filename'))
    return jsonify(moves[args.get('state_string')])

if __name__ == "__main__":
    app.run(processes=10)

