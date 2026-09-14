from pydantic import BaseModel, Field
from typing import Optional, List, Dict

money_pattern = r"^\d+\.\d{2}$"
fx_pattern = r"^\d+\.\d{4}$"

class LoginIn(BaseModel):
    email: str
    password: str

class EmployeeIn(BaseModel):
    id: Optional[str] = None
    name: str
    national_id: Optional[str] = None
    hire_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    base_currency: str = Field(pattern=r"^(SDG|USD|SAR|AED)$")
    base_salary: str = Field(pattern=money_pattern, examples=["1400.00"])
    allowances: str = Field(pattern=money_pattern, examples=["220.00"])
    nsif_eligible: str = Field(pattern=r"^[YN]$")
    bank_account: Optional[str] = None
    bank_code: Optional[str] = None

class FXLockIn(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    rates: Dict[str, str]  # {"USD":"2610.5000", ...} S9(5)V9(4)

class PayrollRunCreate(BaseModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-09"])
    fx_snapshot: Optional[Dict[str, str]] = None
    statutory_version: str = "v2026.09"
    employee_ids: Optional[List[str]] = None  # if None, all tenant employees

class PayrollLineOut(BaseModel):
    emp_id: str
    gross: str
    nsif_emp: str
    nsif_co: str
    taxable: str
    pit: str
    net: str

class StatutoryIn(BaseModel):
    version: str
    nsif_emp: str = "0.08"
    nsif_co: str = "0.17"
    tax_free: str = "50000.00"
    tiers_json: str
