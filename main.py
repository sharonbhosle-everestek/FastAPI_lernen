from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
import json
import logging
from schema.pydantic_model import Patient, Patient_update, Patient_create


app = FastAPI()


def load_all():
    with open("patients.json", 'r') as f:
        data = json.load(f)
    return data


def save_all(data):
    with open("patients.json", "w") as f:
        json.dump(data, f)


@app.get("/")
def home():
    return {
        "message": "Welcome Sharon to your FAST-API server !!!"
    }


@app.get("/health")
def health_check():
    return {
        "status" : "OK"
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


@app.post("/create", response_model=Patient_create)
def add_patient(patient: Patient):
    # check whether patient present , if yes then throw error 
    data = load_all()

    if patient.id in data:
        raise HTTPException(400, detail={"message": f"Patient {patient.id} already present in the DB"})
    
        # if no then add patient in the json
    data[patient.id] = patient.model_dump(exclude=patient.id, exclude_computed_fields=False)

        # save the json file
    save_all(data=data)

    return JSONResponse(content={
        "message": f"Created patient {patient.id} successfully with verdict {patient.decide_verdict}", 
        "pydantic_response": f"{patient.weight}, {patient.compute_bmi}, {patient.weight}"                         }, status_code=201)

    
@app.put('/edit/{patient_id}')
def update_patient(patient_id : str, patient_update: Patient_update):
    pass
    # load karo saare json ka data and check whether patient is present or not 
    data = load_all()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail={
            "message": f"{patient_id} not present in the DB"
        })
    
    # if yes then uska value json se dict mein lao 
    existing_patient_data = data[patient_id]
    # jo data user ne bheja hai usko bhi dict mein lao 
    updated_patient_data = patient_update.model_dump(exclude_unset=True)

    # data update karo dict mein add save karo json mein 
    for key, value in updated_patient_data.items():
        existing_patient_data[key] = value

    existing_patient_data['id'] = patient_id
    pateint_pydantic_obj = Patient(**existing_patient_data)
    
    existing_patient_data = pateint_pydantic_obj.model_dump(exclude={'id'}, exclude_computed_fields=False)

    data[patient_id] = existing_patient_data


    # store / save data in json 
    save_all(data)

    return JSONResponse(status_code=200, content={'message': f'pateint {patient_id} updated successfully'})


@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    # check if patient in json
    data = load_all()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail={'message': f'patient {patient_id} not in DB'}) 

    # if yes then load data and delete
    del data[patient_id]

    # save data 
    save_all(data)

    # return response
    return JSONResponse(status_code=200, content={'message': f'patient {patient_id} deleted succesfully'})

from fastapi import Request
@app.get("/req")
def get_request_packet(req: Request):
    return JSONResponse(status_code=200, 
                        content= {
                            "reuest": f"{req}",
                            "req.base_url": f"{req.url}",
                            "req._url": f"{req._url}",
                            "req.headers.get(Authorizartion)": req.headers.get("user-agent")
                        })