from pydantic import BaseModel, Field, EmailStr, AnyUrl, field_validator
from typing import List, Dict, Annotated, Optional


class Patient(BaseModel):
    name : Annotated[str, Field(max_length=50, default="default name", description="PLease enter name of the person not more than 50 characters", examples=["sharon", "chintamani"])]
    age : Annotated[int, Field(gt=0, lt=100, strict=True, description="enter the valid age between 0 - 100", examples=23)]
    is_married : Annotated[bool, Field(default=False, description="Enter the marital status of the person here")]
    interests: Annotated[Optional[List[str]], Field(default=None, max_length=2, description="List your interests if any")]
    check : Annotated[Optional[str], Field(default="check for default")]
    contact_details : Dict[str, str]
    email: EmailStr
    website : Annotated[AnyUrl, Field(strict=True)]

    
    @field_validator("email")
    @classmethod #classmethod means we can call it on the class itself not on the object e.g Patient.check_email()
    def check_email(cls, val):
        valid_domain = ["hdfc.com", "icici.com"]

        if val.split('@')[-1] not in valid_domain:
            raise ValueError("The email provided has an invalid domain")
        return val
    
    @field_validator("name")
    @classmethod
    def format_name(cls, name):
        return name.capitalize()
    

    @field_validator("age", mode="after")
    @classmethod
    def check_age(cls, age):
        if not (0 < age < 100) : 
            raise ValueError("age is unrealistic")
        return age
    
    # field validators apne aap call ho jaate hain jab model ka object banta hai, just like model validators, so no need to call them explicitly. constructor mein bhi call nahi karna padta. ye constructor ke andar hi call ho jaate hain.
    

def print_something(obj : Patient):
    print("Printing the data here: ")
    print(f"name: {obj.name}")
    print(f"age: {obj.age}, typr : {type(obj.age)}")
    print(f"marital status: {obj.is_married}")
    print(f"interests: {obj.interests}")
    print(f"dummy_field: {obj.check}")
    print(f"contact details: {obj.contact_details}, {type(obj.contact_details)}")
    print(f"Email: {obj.email}")
    print(f"Website: {obj.website}")

data = {
    "name":"sharon",
    "age":23,
    "is_married":True,
    # "interests": ["reading", "music"],
    "contact_details": {
        "email": "sharon.bhosle@everestek.com"
    },
    "email": "sharon.bhosle@hdfc.com",
    "website": "https://www.google.com"
}

p1 = Patient(**data)
print_something(p1)
