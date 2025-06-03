# backend/app/services/provider/provider_service_dep.py
from typing import Annotated
from fastapi import Depends
from app.services.provider.provider_service import ProviderService
from app.services.provider.provider_service_checker import ProviderServiceChecker

provider_service_checker = ProviderServiceChecker()
ProviderServiceDep = Annotated[ProviderService, Depends(provider_service_checker)]