from pydantic import BaseModel

class Address(BaseModel):
    city: str
    state: str
    pincode: str

class Patient(BaseModel):
    name: str
    age: int
    address: Address

my_address = {
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001"
}

my_patient = {
    "name": "John Doe",
    "age": 30,
    "address": my_address
}

address = Address(**my_address)
p1 = Patient(**my_patient)

print(p1.address.city)
print(p1.name)
print(address.state)


# abhi hum serialization k baare mein bhi dekhte hain
print("Serialized Patient Model: (❁´◡`❁)")
print(f"p1.model_dump() == {p1.model_dump()}") # ye dictionary return karega
print(f"p1.model_dump_json() == {p1.model_dump_json()}") # ye json string return karega 

# agar json ko export karna ho to
with open("patient_data.json", "w") as f:
    f.write(p1.model_dump_json())

# agar dictionary ko export karna ho to
with open("patient_data.txt", "w") as f:
    f.write(str(p1.model_dump()))

print("_________________________________\n\n")

# agar koi value ko include/exclude karna ho to
print("Serialized Patient Model with Exclusions: (❁´◡`❁)")    
print(f"\np1.model_dump(exclude={'address'}) == {p1.model_dump(exclude={'address'})}")
print(f"\np1.model_dump(include={'name', 'age'}) == {p1.model_dump(include={'name', 'age'})}")

print("_________________________________")

# agar nested model mein se koi value ko include/exclude karna ho to
print("\n\nSerialized Patient Model with Nested Exclusions: (❁´◡`❁)")    
print("\np1.model_dump(exclude={'address': ['pincode']}) ==", p1.model_dump(exclude={'address': ['pincode']}))
print("\np1.model_dump(include={'address': {'city', 'state'}}) == ", p1.model_dump(include={'address': {'city', 'state'}}))
