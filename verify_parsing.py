import os
import pandas as pd
from parser import parse_statement
from reconciler import reconcile_statement
from exporter import export_to_excel

def generate_mock_messy_csv(file_path):
    """
    Creates a messy CSV bank statement with typical layout irregularities:
    - Metadata rows before transactions
    - Repeating header rows mid-page
    - Shifted column values
    - Multi-line description wrapping
    - A math discrepancy (an intentional typo or gap)
    """
    data = [
        ["FIRST NATIONAL BANK", "", "", "", "", ""],
        ["Statement Period: 2026-06-01 to 2026-06-30", "", "", "", "", ""],
        ["Account Number: *******1234", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        # Table Header
        ["Date", "Description", "Debit", "Credit", "Amount", "Balance"],
        # Valid Row 1
        ["2026-06-01", "Starting Balance Forward", "", "", "", "1000.00"],
        # Valid Row 2
        ["2026-06-02", "GROCERY STORE SAFEWAY", "45.50", "", "-45.50", "954.50"],
        # Wrapped description (Row 3 & Row 4)
        ["2026-06-03", "DIRECT DEP PAYROLL", "", "1500.00", "1500.00", "2454.50"],
        ["", "Company ID: 99882233", "", "", "", ""],
        # Shifted Columns (Row 5 - Date and desc merged, balance shifted left or similar)
        ["2026-06-05", "ELECTRIC UTILITY COMCAST", "120.00", "", "", "2334.50"],
        # Repeating Header in the middle of page 2 simulation
        ["", "", "", "", "", ""],
        ["Date", "Description", "Debit", "Credit", "Amount", "Balance"],
        ["", "PAGE 2 OF 3", "", "", "", ""],
        # Mismatch Row (Row 6 - Let's inject a math error. Actual balance is 2000, but math says 2334.50 - 50 + 0 = 2284.50. This simulates a missed transaction!)
        ["2026-06-10", "RETAIL PURCHASE AMAZON", "50.00", "", "-50.00", "2000.00"],
        # Valid Row 7 (Should reconcile relative to new balance 2000.00)
        ["2026-06-12", "DINING OUT CAFE", "15.00", "", "-15.00", "1985.00"],
        ["2026-06-15", "INTEREST PAYMENT", "", "2.50", "2.50", "1987.50"],
        # Summary footer
        ["", "", "", "", "", ""],
        ["TOTALS", "Total Activity Summary", "230.50", "1502.50", "", "1987.50"]
    ]
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, header=False, index=False)
    print(f"Generated mock messy statement at: {file_path}")

def run_verification():
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    mock_csv_path = os.path.join(workspace_dir, "mock_messy_statement.csv")
    output_excel_path = os.path.join(workspace_dir, "reconciled_mock_statement.xlsx")
    
    # 1. Generate test statement
    generate_mock_messy_csv(mock_csv_path)
    
    print("\n--- Phase 1: Parsing Irregular Columns ---")
    df_parsed = parse_statement(mock_csv_path)
    print("Parsed DataFrame:")
    print(df_parsed)
    
    print("\n--- Phase 2: Mathematical Reconciliation Check ---")
    df_reconciled, summary = reconcile_statement(df_parsed)
    print("\nReconciliation Summary Details:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
        
    print("\nReconciled DataFrame Rows:")
    print(df_reconciled[['date', 'description', 'debit', 'credit', 'balance', 'expected_balance', 'discrepancy', 'reconciled']])
    
    print("\n--- Phase 3: Compiling Styled Excel File ---")
    export_to_excel(df_reconciled, summary, output_excel_path)
    print(f"Styled Excel workbook exported to: {output_excel_path}")
    
    # Clean up mock csv
    if os.path.exists(mock_csv_path):
        os.remove(mock_csv_path)
        
    # Check assertions
    assert len(df_parsed) > 0, "No transactions parsed!"
    assert summary['discrepancies_count'] == 1, "Expected exactly 1 reconciliation discrepancy (AMAZON row)."
    assert os.path.exists(output_excel_path), "Excel output file was not generated!"
    print("\nVerification Passed Successfully!")

if __name__ == "__main__":
    run_verification()
