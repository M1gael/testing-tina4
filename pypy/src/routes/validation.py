from tina4_python.core.router import post
try:
    from tina4_python.validator import Validator
except ImportError:
    Validator = None

# chapter 4: input validation
# testing declarative input validation and standardized error envelopes

@post("/chapter4/validate")
async def validate_user(request, response):
    # documentation discrepancy: Validator class and response.error() appear to be missing 
    # in this version of the framework (v3.2.0)
    
    if Validator is None:
        return response.json({"error": "Validator class not found in tina4_python.validator"}, 500)
    
    v = Validator(request.body)
    v.required("name").required("email").email("email").min_length("name", 2)

    if not v.is_valid():
        try:
            return response.error("VALIDATION_FAILED", v.errors()[0]["message"], 400)
        except AttributeError:
             return response.json({
                 "error": True, 
                 "code": "VALIDATION_FAILED", 
                 "message": v.errors()[0]["message"], 
                 "status": 400
             }, 400)

    return response.json({"message": "data is valid", "data": request.body})

@post("/chapter4/error")
async def test_error(request, response):
     # returning standardized error envelope via response.error()
     try:
         return response.error("TEST_CODE", "Test human message", 401)
     except AttributeError:
          return response.json({
               "error": True,
               "code": "TEST_CODE",
               "message": "Test human message",
               "status": 401,
               "note": "response.error() was not found"
          }, 401)
