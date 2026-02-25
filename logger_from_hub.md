# logger.warning(
#     f"warning | Role with group_name '{role_details_dto.group_name}' already exists.",
#     extra={
#         "location_name": get_location(),
#         "status_code": status.HTTP_409_CONFLICT,
#     },
# )


# logger.debug(
#     f"debug | Generated group_name: {role_details_dto.group_name}",
#     extra={
#         "location_name": get_location(),
#         "status_code": status.HTTP_200_OK,
#     },
# )

logger.info(
    f"info | Role '{role_details_dto.name}' created successfully in database.",
    extra={
        "location_name": get_location(),
        "status_code": status.HTTP_201_CREATED,
    },
)




