"""CMS Fee Schedule API endpoints"""

import csv
import io
import time
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.models.user_fee_schedule import SavedCodeList, UserFeeScheduleUpload, UserFeeScheduleLineItem
from app.schemas.fee_schedule import (
    PriceResponse,
    SearchResponse,
    SearchResult,
    YearsResponse,
    LocalitiesResponse,
    LocalityInfo,
    ConversionFactorResponse,
    ContractAnalysisRequest,
    ContractAnalysisResponse,
    SavedCodeListCreate,
    SavedCodeListUpdate,
    SavedCodeListResponse,
    SavedCodeListsResponse,
    SavedCodeListItem,
)
from app.middleware.api_key import verify_api_key_with_usage
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import check_rate_limit
from app.services.usage_service import log_api_request
from app.services.fee_schedule_service import FeeScheduleService

router = APIRouter()


# ============================================================================
# Public Fee Schedule Endpoints (API Key required)
# ============================================================================

@router.get("/price", response_model=PriceResponse)
async def get_price(
    code: str = Query(..., description="CPT or HCPCS code (e.g., 99213)"),
    zip: str = Query(..., description="5-digit ZIP code"),
    year: int = Query(2025, description="Fee schedule year"),
    modifier: Optional[str] = Query(None, description="Modifier (TC, 26, etc.)"),
    setting: str = Query("non_facility", description="'facility' or 'non_facility'"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Get Medicare price for a CPT/HCPCS code at a specific location.

    This is the main endpoint for looking up Medicare reimbursement rates.
    The price is calculated using:
    - RVUs (Relative Value Units) for the code
    - GPCIs (Geographic Practice Cost Indices) for the location
    - Annual Conversion Factor

    Formula: [(Work RVU * Work GPCI) + (PE RVU * PE GPCI) + (MP RVU * MP GPCI)] * CF
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        service = FeeScheduleService(db)
        result = service.get_price(
            hcpcs_code=code,
            zip_code=zip,
            year=year,
            modifier=modifier,
            setting=setting
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Code {code} not found in {year} fee schedule"
            )

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/price",
            method="GET",
            query_params={"code": code, "zip": zip, "year": year},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return PriceResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/price",
            method="GET",
            query_params={"code": code, "zip": zip, "year": year},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=SearchResponse)
async def search_codes(
    query: str = Query(..., description="Search by code or description"),
    year: int = Query(2025, description="Fee schedule year"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Search fee schedule by CPT/HCPCS code or description.

    Supports:
    - Exact code match (e.g., "99213")
    - Code prefix match (e.g., "992")
    - Description keyword search (e.g., "office visit")
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        service = FeeScheduleService(db)
        results = service.search_codes(
            query=query,
            year=year,
            limit=limit,
            offset=offset
        )

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/search",
            method="GET",
            query_params={"query": query, "year": year, "limit": limit},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return SearchResponse(
            query=query,
            year=year,
            count=len(results),
            results=[SearchResult(**r) for r in results]
        )

    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/search",
            method="GET",
            query_params={"query": query, "year": year, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locality", response_model=LocalityInfo)
async def get_locality_by_zip(
    zip: str = Query(..., description="5-digit ZIP code"),
    year: int = Query(2025, description="Fee schedule year"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Get CMS locality and GPCI values for a ZIP code.

    GPCIs (Geographic Practice Cost Indices) adjust Medicare payments
    based on regional cost differences.
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        service = FeeScheduleService(db)
        result = service.get_locality_from_zip(zip_code=zip, year=year)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No locality found for ZIP code {zip}"
            )

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/locality",
            method="GET",
            query_params={"zip": zip, "year": year},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return LocalityInfo(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/localities", response_model=LocalitiesResponse)
async def list_localities(
    year: int = Query(2025, description="Fee schedule year"),
    state: Optional[str] = Query(None, description="Filter by state (2-letter code)"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    List all CMS localities with GPCI values.

    Optionally filter by state.
    """
    api_key, user = api_key_data

    await check_rate_limit(api_key, user)

    service = FeeScheduleService(db)
    localities = service.get_localities(year=year, state=state)

    return LocalitiesResponse(
        year=year,
        state=state,
        count=len(localities),
        localities=[LocalityInfo(**loc) for loc in localities]
    )


@router.get("/years", response_model=YearsResponse)
async def get_available_years(
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Get list of years with available fee schedule data.
    """
    api_key, user = api_key_data

    await check_rate_limit(api_key, user)

    service = FeeScheduleService(db)
    years = service.get_available_years()

    return YearsResponse(years=years)


@router.get("/conversion-factor", response_model=ConversionFactorResponse)
async def get_conversion_factor(
    year: int = Query(2025, description="Fee schedule year"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Get the Medicare conversion factor for a given year.

    The conversion factor converts total RVUs to dollar amounts.
    """
    api_key, user = api_key_data

    await check_rate_limit(api_key, user)

    service = FeeScheduleService(db)
    cf = service.get_conversion_factor(year=year)

    if not cf:
        raise HTTPException(
            status_code=404,
            detail=f"Conversion factor not found for year {year}"
        )

    return ConversionFactorResponse(year=year, conversion_factor=cf)


# ============================================================================
# Contract Analyzer Endpoints (Requires User Auth)
# ============================================================================

@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    request: ContractAnalysisRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Analyze a fee schedule against Medicare baseline.

    Upload a list of CPT codes with contracted rates to see:
    - Which codes are below Medicare rates ("Red Flags")
    - Variance from Medicare for each code
    - Total revenue impact if volumes are provided
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        service = FeeScheduleService(db)

        # Convert request to format expected by service
        codes_with_rates = [
            {
                "code": item.code,
                "rate": item.rate,
                "volume": item.volume,
                "description": item.description
            }
            for item in request.codes
        ]

        result = service.analyze_fee_schedule(
            codes_with_rates=codes_with_rates,
            zip_code=request.zip_code,
            year=request.year,
            setting=request.setting
        )

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/analyze",
            method="POST",
            query_params={"codes_count": len(request.codes), "zip": request.zip_code},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return ContractAnalysisResponse(**result)

    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/analyze",
            method="POST",
            query_params={"codes_count": len(request.codes)},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/upload", response_model=ContractAnalysisResponse)
async def analyze_contract_csv(
    file: UploadFile = File(..., description="CSV file with CPT codes and rates"),
    zip_code: str = Query(..., description="ZIP code for location-based pricing"),
    year: int = Query(2025, description="CMS year to compare against"),
    setting: str = Query("non_facility", description="'facility' or 'non_facility'"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file for contract analysis.

    CSV format (with header row):
    - code: CPT/HCPCS code (required)
    - rate: Contracted rate (required)
    - volume: Annual volume (optional, for revenue impact)
    - description: Code description (optional)

    Example CSV:
    ```
    code,rate,volume
    99213,85.00,500
    99214,120.00,200
    ```
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        # Read and parse CSV file
        content = await file.read()
        decoded = content.decode('utf-8-sig')  # Handle BOM
        reader = csv.DictReader(io.StringIO(decoded))

        codes_with_rates = []
        for row in reader:
            code = row.get('code', row.get('CPT', row.get('HCPCS', ''))).strip()
            rate_str = row.get('rate', row.get('price', row.get('contracted_rate', '0')))
            volume_str = row.get('volume', row.get('annual_volume', ''))
            description = row.get('description', '').strip()

            if not code:
                continue

            try:
                rate = float(rate_str.replace('$', '').replace(',', ''))
            except (ValueError, AttributeError):
                continue

            volume = None
            if volume_str:
                try:
                    volume = int(float(volume_str.replace(',', '')))
                except (ValueError, AttributeError):
                    pass

            codes_with_rates.append({
                "code": code,
                "rate": rate,
                "volume": volume,
                "description": description
            })

        if not codes_with_rates:
            raise HTTPException(
                status_code=400,
                detail="No valid codes found in CSV file"
            )

        # Perform analysis
        service = FeeScheduleService(db)
        result = service.analyze_fee_schedule(
            codes_with_rates=codes_with_rates,
            zip_code=zip_code,
            year=year,
            setting=setting
        )

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/fee-schedule/analyze/upload",
            method="POST",
            query_params={"codes_count": len(codes_with_rates), "zip": zip_code, "filename": file.filename},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return ContractAnalysisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


# ============================================================================
# Saved Code Lists Endpoints (Requires User Auth - JWT)
# ============================================================================

@router.get("/lists", response_model=SavedCodeListsResponse)
async def get_saved_lists(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all saved code lists for the current user.
    """
    lists = db.query(SavedCodeList).filter(
        SavedCodeList.user_id == user.id
    ).order_by(SavedCodeList.created_at.desc()).all()

    return SavedCodeListsResponse(
        count=len(lists),
        lists=[
            SavedCodeListResponse(
                id=str(lst.id),
                name=lst.name,
                description=lst.description,
                codes=[SavedCodeListItem(**c) for c in (lst.codes or [])],
                created_at=lst.created_at.isoformat(),
                updated_at=lst.updated_at.isoformat()
            )
            for lst in lists
        ]
    )


@router.post("/lists", response_model=SavedCodeListResponse)
async def create_saved_list(
    data: SavedCodeListCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new saved code list.
    """
    lst = SavedCodeList(
        user_id=user.id,
        name=data.name,
        description=data.description,
        codes=[c.dict() for c in data.codes]
    )
    db.add(lst)
    db.commit()
    db.refresh(lst)

    return SavedCodeListResponse(
        id=str(lst.id),
        name=lst.name,
        description=lst.description,
        codes=[SavedCodeListItem(**c) for c in (lst.codes or [])],
        created_at=lst.created_at.isoformat(),
        updated_at=lst.updated_at.isoformat()
    )


@router.get("/lists/{list_id}", response_model=SavedCodeListResponse)
async def get_saved_list(
    list_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific saved code list.
    """
    lst = db.query(SavedCodeList).filter(
        SavedCodeList.id == list_id,
        SavedCodeList.user_id == user.id
    ).first()

    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    return SavedCodeListResponse(
        id=str(lst.id),
        name=lst.name,
        description=lst.description,
        codes=[SavedCodeListItem(**c) for c in (lst.codes or [])],
        created_at=lst.created_at.isoformat(),
        updated_at=lst.updated_at.isoformat()
    )


@router.put("/lists/{list_id}", response_model=SavedCodeListResponse)
async def update_saved_list(
    list_id: str,
    data: SavedCodeListUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a saved code list.
    """
    lst = db.query(SavedCodeList).filter(
        SavedCodeList.id == list_id,
        SavedCodeList.user_id == user.id
    ).first()

    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    if data.name is not None:
        lst.name = data.name
    if data.description is not None:
        lst.description = data.description
    if data.codes is not None:
        lst.codes = [c.dict() for c in data.codes]

    db.commit()
    db.refresh(lst)

    return SavedCodeListResponse(
        id=str(lst.id),
        name=lst.name,
        description=lst.description,
        codes=[SavedCodeListItem(**c) for c in (lst.codes or [])],
        created_at=lst.created_at.isoformat(),
        updated_at=lst.updated_at.isoformat()
    )


@router.delete("/lists/{list_id}")
async def delete_saved_list(
    list_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a saved code list.
    """
    lst = db.query(SavedCodeList).filter(
        SavedCodeList.id == list_id,
        SavedCodeList.user_id == user.id
    ).first()

    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    db.delete(lst)
    db.commit()

    return {"message": "List deleted successfully"}
