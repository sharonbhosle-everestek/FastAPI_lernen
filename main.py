from fastapi import FastAPI, Path, HTTPException, Query
import json
import logging

app = FastAPI()


def load_all():
    with open("patients.json", 'r') as f:
        data = json.load(f)
    return data


@app.get("/")
def hello():
    return {
        "message": "Welcome Sharon !!!"
    }


@app.get("/about")
def about():
    return {
        "message": "I am using CampusX website to learn FastAPI 😎..."
    }


@app.get("/view")
def view():
    return load_all()


# example of path parameter 
@app.get('/patient/{patient_id}')
def patient(patient_id : str = Path(..., description="Please enter the patient ID you are looking for ", examples="P001")):
    data = load_all()

    if patient_id in data:
        return {
            'message': 'patient found',
            'data': data[patient_id]
        }
    raise HTTPException(status_code=404, detail="Patient not found")


# example of Query parameter
@app.get('/sort')
def sorted_data(order_by : str = Query(..., description="Enter the attribute by which you want to sort"), descending : bool = Query(True, description="Enter False if want data in ascending order i.e smallest first else default is descending")):

    valid_attributes = ["height", "weight", "bmi"]

    if order_by not in valid_attributes:
        raise HTTPException(status_code=400, detail= f"Invalid attribute, please select from {valid_attributes}")
    
    # agar ascending field mein kuch galat daala toh kya karna hai ?? 
    # code here .... / if needed 

    data = load_all()

    sorted_data = sorted(data.values(), key = lambda x : x.get(order_by, 0), reverse=descending)
    logging.log(level=1, msg="some message from the logger")
    return sorted_data