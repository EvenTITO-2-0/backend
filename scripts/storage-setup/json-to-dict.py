import json

with open("./eventito-key.json", "r") as file:
    credentials_json = json.loads(file.read())
    credentials_string = json.dumps(credentials_json)

print(credentials_string)
