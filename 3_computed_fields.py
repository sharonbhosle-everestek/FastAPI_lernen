from pydantic import BaseModel, EmailStr, computed_field
from typing import List, Dict

class Patient(BaseModel):
    name: str
    email: EmailStr
    age: int
    weight: float
    height: float
    is_married: bool
    allergies: List[str]
    contact_details: Dict[str, str]

    @computed_field
    @property   # property means we can access it like an attribute not like a method e.g obj.bmi()
    def bmi(self) -> float:
        height_in_meters = self.height / 100  # converting cm to meters
        bmi_value = self.weight / (height_in_meters ** 2)
        return round(bmi_value, 2)
    
data = {
    "name": "sharon",
    "email":"sharon.bhosle@ellume.com",
    "age": 36,
    "weight": 100.34,
    "height": 170.5,
    "is_married": False,
    "allergies": ["pollen", "bees"],
    "contact_details": {
        "phone": "1234567890",
        "emergency": "2345678"
    }
}    

p1 = Patient(**data)
print("Patient BMI is: ", p1.bmi)
print(p1.model_dump()) 