from pydantic import BaseModel, model_validator, EmailStr, Field
from typing import List, Dict, Annotated, Optional

from main import patient

class Patient(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    age: int
    weight: float
    is_married: bool
    allergies: List[str]
    contact_details: Dict[str, str]

    @model_validator(mode='after')
    def check_emergency_contact(self):
        if (self.age < 18 or self.age > 58) and 'emergency' not in self.contact_details:
            print(" 👎 validation failed")
            raise ValueError('Patients in age range 18 - 58 must have a emergency contact ')
        # return model
        print(" 👍 validation successful --->", self, type(self.weight))

        return self

data = {
    "name": "sharon",
    # "email":"sharon.bhosle@ellume.com",
    "age": "36",
    "is_married" : "False",
    "weight": "100.34",
    "allergies": ["pollen", "bees"],
    "contact_details": {
        "email": "sharon.bhosle@gmail.com",
        "emergency": "2345678"
    }
}    

p1 = Patient(**data)