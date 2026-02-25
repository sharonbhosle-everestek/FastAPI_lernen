import requests, json

# api_url = "https://dev-hub.everestek.com/dashboard/selfView"
# api_url = "https://pokeapi.co/api/v2/pokemon/ditto"
# api_url = "https://pokeapi.co/api/v2/language/9"
# api_url = "https://pokeapi.co/api/v2/berry/1"
api_url = "https://pokeapi.co/api/v2/pokemon/pikachu"

response = requests.get(api_url)
# print(response.headers.get("Authorization", "found_nothing"))

# print(response.headers)
# try:
#     json_resp = response.json()
#     print(json_resp)
# except Exception as e:
#     print("Exception: ")
#     print(response)
json_response = response.json()
print(json_response)


with open("pokemon.json", "w") as f:
    json.dump(json_response, f)