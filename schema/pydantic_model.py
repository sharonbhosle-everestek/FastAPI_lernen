from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Optional, Literal


    # "P001": {
    #     "name": "Ananya Verma",
    #     "city": "Guwahati",
    #     "age": 28,
    #     "gender": "female",
    #     "height": 1.65,
    #     "weight": 90.0,
    #     "bmi": 33.06,
    #     "verdict": "Obese"
    # },

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="Enter patient id", examples=["P001", "P002"])]
    name: Annotated[str, Field(..., description="Enter Name of the patient", max_length=40)]
    city: Annotated[str, Field(..., description="Enter city where patient is from")]
    age: Annotated[int, Field(..., gt=0, lt=120, description="age of patient")]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='enter the gender of the patient')]
    height: Annotated[float, Field(..., gt = 0, lt= 2, description="enter height in meters")]
    weight: Annotated[float, Field(..., gt = 0, lt= 150, description="enter weight in kgs")]


    @computed_field
    @property
    def compute_bmi(self) -> float:
        return round(self.weight / (self.height * self.height), 2)


    @computed_field
    @property
    def decide_verdict(self) -> str:
        if self.compute_bmi < 18.5:
            return "Underweight"
        elif self.compute_bmi < 25:
            return "Normal weight"
        elif self.compute_bmi < 30:
            return "Overweight"
        else:
            return "Obese"
        

class Patient_update(BaseModel):
    name: Annotated[Optional[str], Field(None, description="Enter Name of the patient", max_length=40)]
    city: Annotated[Optional[str], Field(None, description="Enter city where patient is from")]
    age: Annotated[Optional[int], Field(None, gt=0, lt=120, description="age of patient")]
    gender: Annotated[Optional[Literal['male', 'female', 'others']], Field(..., description='enter the gender of the patient')]
    height: Annotated[Optional[float], Field(None, gt = 0, lt= 2, description="enter height in meters")]
    weight: Annotated[Optional[float], Field(None, gt = 0, lt= 150, description="enter weight in kgs")]


class Patient_create(BaseModel):
    name: Annotated[str, Field(..., description="Response packet checking name")]
    age: Annotated[int, Field(..., description="age for Response packet")]
    weight: Annotated[float, Field(..., description="Patient weight")]
    # weight: Annotated[str, Field(res = lambda x:"Control while you can" if x < 100 else "God will save you", description="Patient weight")]
    bmi : Annotated[float, Field(..., description="Computed BMI")]




