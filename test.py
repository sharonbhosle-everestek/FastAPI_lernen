from main import load_all, save_all, Patient, Patient_update

request = {
    "id": "P001",
    "weight": 98,
    "city": "mumbai"
}

data = load_all()

# print(type(data))

existing_data = data[request['id']]



print(existing_data)

for key, value in request.items():
    if key == 'id':
        continue
    else:
        existing_data[key] = value

print(existing_data)

updated_data_pydantic = Patient(**existing_data)
updated_data_pydantic.model_dump(exclude='id')

