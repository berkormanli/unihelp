import fastapi

from src.api.dependencies.repository import get_repository
from src.models.schemas.account import AccountInCreate, AccountInLogin, AccountInResponse, AccountWithToken, VerificationCodeModel, AccountInSwaggerAuth
from src.repository.crud.account import AccountCRUDRepository
from src.securities.authorizations.jwt import jwt_generator
from src.utilities.exceptions.database import EntityAlreadyExists
from src.utilities.exceptions.http.exc_400 import (
    http_400_exc_bad_verification_code,
    http_400_exc_bad_verification_request,
    http_exc_400_credentials_bad_signin_request,
    http_exc_400_credentials_bad_signup_request,
)
from src.utilities.exceptions.http.exc_404 import http_404_exc_id_not_found_request

router = fastapi.APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/signup",
    name="auth:signup",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def signup(
    account_create: AccountInCreate,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountInResponse:
    try:
        await account_repo.is_username_taken(username=account_create.username)
        await account_repo.is_email_taken(email=account_create.email)
        new_account = await account_repo.create_account(account_create=account_create)
        access_token = jwt_generator.generate_access_token(account=new_account)

    except EntityAlreadyExists:
        raise await http_exc_400_credentials_bad_signup_request()

    
    return AccountInResponse(
        id=new_account.id,
        authorizedAccount=AccountWithToken(
            token=access_token,
            username=new_account.username,
            email=new_account.email,  # type: ignore
            isVerified=new_account.is_verified,
            isActive=new_account.is_active,
            isLoggedIn=new_account.is_logged_in,
            createdAt=new_account.created_at,
            updatedAt=new_account.updated_at,
        ),
    )

@router.post("/verify/{account_id}", response_model=AccountInResponse)
async def verify_account(
    account_id: int,
    verification_code: VerificationCodeModel,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
):
    account = await account_repo.read_account_by_id(account_id)

    if not account:
        raise await http_404_exc_id_not_found_request(account_id)

    if account.is_verified:
        #raise HTTPException(status_code=400, detail="Account already verified")
        raise await http_400_exc_bad_verification_request()

    if account.verification_code != verification_code.code:
        raise await http_400_exc_bad_verification_code()

    # Mark the account as verified
    await account_repo.verify_account(account_id)

    # Generate access token for the verified account
    access_token = jwt_generator.generate_access_token(account=account)

    return AccountInResponse(
        id=account.id,
        authorizedAccount=AccountWithToken(
            token=access_token,
            username=account.username,
            email=account.email,
            isVerified=account.is_verified,
            isActive=account.is_active,
            isLoggedIn=account.is_logged_in,
            createdAt=account.created_at,
            updatedAt=account.updated_at,
        ),
    )

@router.get("/verify/{token}")
async def verify_with_link(
    token: str,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
):
    try:
        account_id = jwt_generator.verify_verification_token(token)

        # Verify the account
        await account_repo.verify_account(account_id)

        # Generate a new access token for the now verified user
        account = await account_repo.read_account_by_id(account_id)
        access_token = jwt_generator.generate_access_token(account=account)

        # Redirect to homepage with the access token (you might need a different approach for your frontend)
        response = fastapi.responses.RedirectResponse(url="/")  # Replace with your homepage URL
        response.set_cookie(key="access_token", value=access_token, httponly=True)  # Set the cookie for the frontend
        return response

    except Exception as e:
        raise await http_400_exc_bad_verification_code() # Add a link version of the exception.

@router.post(
    path="/signin",
    name="auth:signin",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_202_ACCEPTED,
)
async def signin(
    account_login: AccountInLogin,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountInResponse:
    try:
        db_account = await account_repo.read_user_by_password_authentication(account_login=account_login)

    except Exception:
        raise await http_exc_400_credentials_bad_signin_request()

    access_token = jwt_generator.generate_access_token(account=db_account)

    return AccountInResponse(
        id=db_account.id,
        authorizedAccount=AccountWithToken(
            token=access_token,
            username=db_account.username,
            email=db_account.email,  # type: ignore
            avatar=db_account.avatar,
            isVerified=db_account.is_verified,
            isActive=db_account.is_active,
            isLoggedIn=db_account.is_logged_in,
            createdAt=db_account.created_at,
            updatedAt=db_account.updated_at,
        ),
    )

@router.post(
    path="/signinswagger",
    name="auth:signinswagger",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_202_ACCEPTED,
)
async def signin(
    form_data: fastapi.security.OAuth2PasswordRequestForm = fastapi.Depends(),
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountInResponse:
    try:
        # Convert form data to account login model
        print(form_data.username, form_data.password, form_data.client_id)
        account_login = AccountInSwaggerAuth(
            username=form_data.username,  # Swagger UI sends username field
            password=form_data.password
        )
        db_account = await account_repo.read_user_by_password_authentication_swagger(account_login=account_login)

    except Exception:
        raise await http_exc_400_credentials_bad_signin_request()

    access_token = jwt_generator.generate_access_token(account=db_account)

    return AccountInResponse(
        id=db_account.id,
        authorizedAccount=AccountWithToken(
            token=access_token,
            username=db_account.username,
            email=db_account.email,
            isVerified=db_account.is_verified,
            isActive=db_account.is_active,
            isLoggedIn=db_account.is_logged_in,
            createdAt=db_account.created_at,
            updatedAt=db_account.updated_at,
        ),
    )
