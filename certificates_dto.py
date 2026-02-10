from pydantic import BaseModel
from typing import Optional

class Certification(BaseModel):
    id: Optional[str]
    resource_id: Optional[str]
    name: Optional[str]
    # level: Optional[CertificationEnum]
    validation_date: Optional[str]

def dto_2_db_convert(certification_dto: Certification):

    print("====")
    db_resource_certifications_list = []
    for certification in certification_dto:
        json_certifications = certification.dict()
        print(json_certifications, type(json_certifications))
    #     db_resource_certifications = db.ResourceCertification(**json_certifications)
    #     db_resource_certifications.resource_id = resource_id
    #     db_resource_certifications_list.append(db_resource_certifications)
    # return db_resource_certifications_list

# dto_2_db_convert(Certification(*))