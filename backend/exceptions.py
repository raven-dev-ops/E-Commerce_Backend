from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, ValidationError) and response is not None:
        formatted_errors = []
        if isinstance(response.data, list):
            for error in response.data:
                formatted_errors.append(
                    {
                        "field": None,
                        "message": str(error),
                        "code": getattr(error, "code", ""),
                    }
                )
        elif isinstance(response.data, dict):
            for field, errors in response.data.items():
                if isinstance(errors, (list, tuple)):
                    for error in errors:
                        formatted_errors.append(
                            {
                                "field": field,
                                "message": str(error),
                                "code": getattr(error, "code", ""),
                            }
                        )
                else:
                    formatted_errors.append(
                        {
                            "field": field,
                            "message": str(errors),
                            "code": getattr(errors, "code", ""),
                        }
                    )
        response.data = {"errors": formatted_errors}
    return response
