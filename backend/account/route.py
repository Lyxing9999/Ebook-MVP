from fastapi import Body, Path, Query
from fastapi.responses import JSONResponse
from database.db import accounts_collection
from bson import ObjectId
from typing import List, Dict, Union

from fastapi import APIRouter
router = APIRouter(prefix="/facebook", tags=["Accounts"])
# -------------------------------
# CREATE
# -------------------------------


@router.post("/save_account")
async def save_accounts(accounts: Union[Dict, List[Dict]] = Body(...)):
    """
    Accepts either a single account dict or a list of accounts.
    """
    if isinstance(accounts, dict):
        accounts = [accounts]  # wrap single account into list

    saved = []
    errors = []

    for account in accounts:
        if "username" not in account or "password" not in account:
            errors.append({"account": account, "error": "Missing username or password"})
            continue

        account["status"] = account.get("status", "normal")
        existing = await accounts_collection.find_one({"username": account["username"]})
        if existing:
            errors.append({"account": account, "error": "Username already exists"})
            continue

        result = await accounts_collection.insert_one(account)
        saved.append({"username": account["username"], "id": str(result.inserted_id)})

    return {"success": True, "saved": saved, "errors": errors}

# -------------------------------
# READ (all or single)
# -------------------------------
@router.get("/get_accounts")
async def get_accounts(limit: int = Query(100, le=1000)):
    accounts = await accounts_collection.find().to_list(length=limit)
    # Convert ObjectId to str
    for acc in accounts:
        acc["_id"] = str(acc["_id"])
    return accounts

@router.get("/get_account/{account_id}")
async def get_account(account_id: str = Path(...)):
    account = await accounts_collection.find_one({"_id": ObjectId(account_id)})
    if not account:
        return JSONResponse({"error": "Account not found"}, status_code=404)
    account["_id"] = str(account["_id"])
    return account


# -------------------------------
# UPDATE (full replace)
# -------------------------------
@router.put("/update_account/{account_id}")
async def update_account(account_id: str, updated: dict = Body(...)):
    result = await accounts_collection.replace_one({"_id": ObjectId(account_id)}, updated)
    if result.matched_count == 0:
        return JSONResponse({"error": "Account not found"}, status_code=404)
    return {"success": True}


# -------------------------------
# PATCH (partial update)
# -------------------------------
@router.patch("/patch_account/{account_id}")
async def patch_account(account_id: str, updated: dict = Body(...)):
    result = await accounts_collection.update_one(
        {"_id": ObjectId(account_id)},
        {"$set": updated}
    )
    if result.matched_count == 0:
        return JSONResponse({"error": "Account not found"}, status_code=404)
    return {"success": True}


# -------------------------------
# DELETE
# -------------------------------
@router.delete("/delete_account/{account_id}")
async def delete_account(account_id: str):
    result = await accounts_collection.delete_one({"_id": ObjectId(account_id)})
    if result.deleted_count == 0:
        return JSONResponse({"error": "Account not found"}, status_code=404)
    return {"success": True}