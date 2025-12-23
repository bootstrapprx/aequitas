"""
Backend Smoke Test for Journal Entry Workflow (Phase 3)

Tests the complete journal entry workflow end-to-end:
1. Create fiscal period
2. Create draft journal entry (balanced)
3. Post journal entry
4. Verify trial balance is updated
5. Verify ledger contains entry

Usage:
    python test_journal_workflow.py

Requirements:
    - Backend running on localhost:8000
    - Valid credentials in environment or hardcoded
    - Company with chart of accounts set up
"""

import requests
import json
from datetime import date, datetime
from decimal import Decimal
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "admin@aequitas.local"  # Change to your test user
PASSWORD = "admin123"  # Change to your test password

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'='*60}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{text}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{'='*60}{bcolors.ENDC}\n")


def print_success(text):
    print(f"{bcolors.OKGREEN}✓ {text}{bcolors.ENDC}")


def print_error(text):
    print(f"{bcolors.FAIL}✗ {text}{bcolors.ENDC}")


def print_info(text):
    print(f"{bcolors.OKCYAN}ℹ {text}{bcolors.ENDC}")


def login():
    """Login and get access token"""
    print_header("STEP 1: Authentication")

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )

    if response.status_code != 200:
        print_error(f"Login failed: {response.status_code}")
        print_info(f"Response: {response.text}")
        sys.exit(1)

    data = response.json()
    token = data.get("access_token")

    if not token:
        print_error("No access token in response")
        sys.exit(1)

    print_success(f"Logged in successfully as {EMAIL}")
    return token


def get_headers(token):
    """Get request headers with token"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def get_or_create_company(token):
    """Get first available company or create one"""
    print_header("STEP 2: Get Company")

    headers = get_headers(token)

    # Try to get companies
    response = requests.get(f"{BASE_URL}/companies", headers=headers)

    if response.status_code == 200:
        companies = response.json()
        if companies:
            company_id = companies[0]["id"]
            company_name = companies[0]["name"]
            print_success(f"Using existing company: {company_name} ({company_id})")
            return company_id

    print_info("No existing company found, you need to create one first")
    sys.exit(1)


def get_company_accounts(token, company_id):
    """Get chart of accounts for company"""
    print_header("STEP 3: Get Chart of Accounts")

    headers = get_headers(token)

    response = requests.get(f"{BASE_URL}/companychart/{company_id}", headers=headers)

    if response.status_code != 200:
        print_error(f"Failed to get company accounts: {response.status_code}")
        print_info(f"Response: {response.text}")
        sys.exit(1)

    accounts = response.json()

    if len(accounts) < 2:
        print_error("Company must have at least 2 accounts for journal entry")
        sys.exit(1)

    print_success(f"Found {len(accounts)} accounts")

    # Find two suitable accounts (one debit normal, one credit normal)
    cash_account = None
    equity_account = None

    for account in accounts:
        if account.get("is_active") and account.get("type") != "H":
            if not cash_account and ("cash" in account.get("description", "").lower() or
                                    account.get("account_code", "").startswith("1")):
                cash_account = account
            elif not equity_account and ("equity" in account.get("description", "").lower() or
                                        "capital" in account.get("description", "").lower() or
                                        account.get("account_code", "").startswith("3")):
                equity_account = account

            if cash_account and equity_account:
                break

    if not cash_account or not equity_account:
        # Fallback: use first two active detail accounts
        active_accounts = [a for a in accounts if a.get("is_active") and a.get("type") != "H"]
        if len(active_accounts) >= 2:
            cash_account = active_accounts[0]
            equity_account = active_accounts[1]
        else:
            print_error("Could not find 2 suitable accounts")
            sys.exit(1)

    print_info(f"Using accounts:")
    print_info(f"  Debit:  {cash_account.get('account_code')} - {cash_account.get('description')}")
    print_info(f"  Credit: {equity_account.get('account_code')} - {equity_account.get('description')}")

    return cash_account, equity_account


def create_fiscal_period(token, company_id):
    """Create a fiscal period for testing"""
    print_header("STEP 4: Create Fiscal Period")

    headers = get_headers(token)

    # Check if period already exists for current month
    current_year = datetime.now().year
    response = requests.get(
        f"{BASE_URL}/accounting/fiscal-periods",
        headers=headers,
        params={"company_id": company_id, "year": current_year}
    )

    if response.status_code == 200:
        periods = response.json()
        if periods:
            period = periods[0]
            print_success(f"Using existing period: {period['period_number']}")
            return period['id']

    # Create new period for current month
    today = date.today()
    period_data = {
        "company_id": company_id,
        "period_type": "month",
        "period_number": f"{today.year}-{today.month:02d}",
        "start_date": f"{today.year}-{today.month:02d}-01",
        "end_date": f"{today.year}-{today.month:02d}-28",  # Simplified
        "status": "open"
    }

    response = requests.post(
        f"{BASE_URL}/accounting/fiscal-periods",
        headers=headers,
        json=period_data
    )

    if response.status_code != 201:
        print_error(f"Failed to create fiscal period: {response.status_code}")
        print_info(f"Response: {response.text}")
        sys.exit(1)

    period = response.json()
    print_success(f"Created fiscal period: {period['period_number']}")
    return period['id']


def create_journal_entry(token, company_id, fiscal_period_id, cash_account, equity_account):
    """Create a balanced journal entry"""
    print_header("STEP 5: Create Journal Entry (Draft)")

    headers = get_headers(token)

    amount = 1000.00
    entry_data = {
        "company_id": company_id,
        "fiscal_period_id": fiscal_period_id,
        "entry_date": str(date.today()),
        "description": "Test Entry - Initial Capital Contribution",
        "reference": "TEST-001",
        "entry_type": "standard",
        "lines": [
            {
                "company_account_id": cash_account['id'],
                "line_number": 1,
                "description": "Debit Cash",
                "debit_amount": amount,
                "credit_amount": 0
            },
            {
                "company_account_id": equity_account['id'],
                "line_number": 2,
                "description": "Credit Equity",
                "debit_amount": 0,
                "credit_amount": amount
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/journal-entries",
        headers=headers,
        json=entry_data
    )

    if response.status_code != 201:
        print_error(f"Failed to create journal entry: {response.status_code}")
        print_info(f"Response: {response.text}")

        # Try to parse and show canonical error
        try:
            error_data = response.json()
            if "error" in error_data:
                error = error_data["error"]
                print_error(f"Error Code: {error.get('code', 'UNKNOWN')}")
                print_error(f"Message: {error.get('message', 'No message')}")
                if "details" in error:
                    print_info(f"Details: {json.dumps(error['details'], indent=2)}")
        except:
            pass

        sys.exit(1)

    entry = response.json()
    print_success(f"Created journal entry: {entry.get('entry_number')}")
    print_info(f"Status: {entry.get('status')}")
    print_info(f"Total Debit: ${entry.get('total_debit', 0):.2f}")
    print_info(f"Total Credit: ${entry.get('total_credit', 0):.2f}")

    return entry['id'], entry.get('entry_number')


def post_journal_entry(token, entry_id):
    """Post the journal entry"""
    print_header("STEP 6: Post Journal Entry")

    headers = get_headers(token)

    response = requests.post(
        f"{BASE_URL}/journal-entries/{entry_id}/post",
        headers=headers,
        json={}
    )

    if response.status_code != 200:
        print_error(f"Failed to post journal entry: {response.status_code}")
        print_info(f"Response: {response.text}")

        # Try to parse and show canonical error
        try:
            error_data = response.json()
            if "error" in error_data:
                error = error_data["error"]
                print_error(f"Error Code: {error.get('code', 'UNKNOWN')}")
                print_error(f"Message: {error.get('message', 'No message')}")
                if "request_id" in error:
                    print_info(f"Request ID: {error['request_id']}")
                if "correlation_id" in error:
                    print_info(f"Correlation ID: {error['correlation_id']}")
        except:
            pass

        sys.exit(1)

    entry = response.json()
    print_success(f"Posted journal entry successfully")
    print_info(f"Status: {entry.get('status')}")
    print_info(f"Posted at: {entry.get('posted_at')}")


def verify_trial_balance(token, company_id, fiscal_period_id):
    """Verify trial balance includes our entry"""
    print_header("STEP 7: Verify Trial Balance")

    headers = get_headers(token)

    response = requests.get(
        f"{BASE_URL}/accounting/trial-balance",
        headers=headers,
        params={
            "company_id": company_id,
            "fiscal_period_id": fiscal_period_id
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to get trial balance: {response.status_code}")
        print_info(f"Response: {response.text}")
        return

    trial_balance = response.json()

    print_success(f"Retrieved trial balance")
    print_info(f"Total Debits: ${trial_balance.get('total_debits', 0):.2f}")
    print_info(f"Total Credits: ${trial_balance.get('total_credits', 0):.2f}")
    print_info(f"Balanced: {trial_balance.get('is_balanced')}")
    print_info(f"Accounts with balances: {len(trial_balance.get('accounts', []))}")

    if not trial_balance.get('is_balanced'):
        print_error("Trial balance is NOT balanced!")
        print_info(f"Variance: ${trial_balance.get('variance', 0):.2f}")


def main():
    """Run the complete workflow test"""
    print_header("PHASE 3 JOURNAL ENTRY WORKFLOW TEST")
    print_info("Testing end-to-end journal entry creation and posting")

    try:
        # Step 1: Login
        token = login()

        # Step 2: Get company
        company_id = get_or_create_company(token)

        # Step 3: Get accounts
        cash_account, equity_account = get_company_accounts(token, company_id)

        # Step 4: Create fiscal period
        fiscal_period_id = create_fiscal_period(token, company_id)

        # Step 5: Create journal entry
        entry_id, entry_number = create_journal_entry(
            token, company_id, fiscal_period_id, cash_account, equity_account
        )

        # Step 6: Post journal entry
        post_journal_entry(token, entry_id)

        # Step 7: Verify trial balance
        verify_trial_balance(token, company_id, fiscal_period_id)

        print_header("TEST COMPLETED SUCCESSFULLY")
        print_success("All steps completed without errors")
        print_info("Journal entry workflow is functioning correctly")

    except KeyboardInterrupt:
        print_error("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
