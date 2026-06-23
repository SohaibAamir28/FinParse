import pandas as pd

def reconcile_statement(df):
    """
    Reconciles the running balance of the bank statement dataframe.
    Calculates Starting Balance - Debits + Credits (or + Debits - Credits depending on account convention)
    and verifies that it mathematically matches the running balance.
    
    Returns:
      reconciled_df: DataFrame with additional columns: 'expected_balance', 'discrepancy', 'reconciled'
      summary: dict containing starting_balance, ending_balance, total_debits, total_credits, and reconciliation_status
    """
    if df.empty:
        return df, {
            'starting_balance': 0.0,
            'ending_balance': 0.0,
            'total_debits': 0.0,
            'total_credits': 0.0,
            'is_reconciled': True,
            'discrepancies_count': 0
        }
        
    # Ensure numerical columns are floats
    df['debit'] = df['debit'].fillna(0.0).astype(float)
    df['credit'] = df['credit'].fillna(0.0).astype(float)
    df['balance'] = df['balance'].fillna(0.0).astype(float)
    
    # Auto-detect sign convention:
    # Asset Account (Checking/Savings): Balance = Prev_Balance - Debit + Credit
    # Liability Account (Credit Card): Balance = Prev_Balance + Debit - Credit (where debit increases debt)
    
    asset_matches = 0
    liability_matches = 0
    valid_comparisons = 0
    
    for i in range(1, len(df)):
        prev_bal = df.loc[i-1, 'balance']
        curr_bal = df.loc[i, 'balance']
        debit = df.loc[i, 'debit']
        credit = df.loc[i, 'credit']
        
        # Check if there is any movement
        if debit != 0.0 or credit != 0.0:
            valid_comparisons += 1
            # Option A (Asset account)
            if abs((prev_bal - debit + credit) - curr_bal) < 0.05:
                asset_matches += 1
            # Option B (Credit Card / Liability account)
            if abs((prev_bal + debit - credit) - curr_bal) < 0.05:
                liability_matches += 1
                
    # Determine convention. Default to Asset (Checking/Savings) if no data or tie
    is_liability = False
    if valid_comparisons > 0:
        if liability_matches > asset_matches:
            is_liability = True
            
    # Run the reconciliation with the selected convention
    reconciled_rows = []
    discrepancy_indices = []
    
    # Starting balance is the balance of the first row minus the first row's transaction amount
    # Or, if we assume the first row's balance is correct, we can start there.
    # Let's start with the balance of the first row, or if first row balance is missing, 0.0
    first_row_bal = df.loc[0, 'balance']
    first_row_debit = df.loc[0, 'debit']
    first_row_credit = df.loc[0, 'credit']
    
    if is_liability:
        # Prev_bal + debit - credit = curr_bal => Prev_bal = curr_bal - debit + credit
        starting_balance = first_row_bal - first_row_debit + first_row_credit
    else:
        # Prev_bal - debit + credit = curr_bal => Prev_bal = curr_bal + debit - credit
        starting_balance = first_row_bal + first_row_debit - first_row_credit
        
    expected_balance = starting_balance
    
    for idx, row in df.iterrows():
        debit = row['debit']
        credit = row['credit']
        actual_bal = row['balance']
        
        if is_liability:
            expected_balance = expected_balance + debit - credit
        else:
            expected_balance = expected_balance - debit + credit
            
        discrepancy = round(actual_bal - expected_balance, 2)
        reconciled = abs(discrepancy) < 0.05
        
        if not reconciled:
            # If the actual balance is non-zero, let's realign the expected balance to the actual balance
            # to prevent cascade errors on subsequent rows, while still flagging this row as mismatched.
            # This is a very common issue in bank statements: a skipped transaction causes a single line
            # jump but subsequent math might match the new balance.
            discrepancy_indices.append(idx)
            expected_balance = actual_bal
            
        reconciled_rows.append({
            'expected_balance': round(expected_balance, 2),
            'discrepancy': discrepancy,
            'reconciled': reconciled
        })
        
    reconciled_info = pd.DataFrame(reconciled_rows)
    df_reconciled = pd.concat([df, reconciled_info], axis=1)
    
    # Calculate summaries
    total_debits = df['debit'].sum()
    total_credits = df['credit'].sum()
    ending_balance = df.loc[len(df)-1, 'balance'] if not df.empty else starting_balance
    
    summary = {
        'starting_balance': round(starting_balance, 2),
        'ending_balance': round(ending_balance, 2),
        'total_debits': round(total_debits, 2),
        'total_credits': round(total_credits, 2),
        'net_cash_flow': round(total_credits - total_debits if not is_liability else total_debits - total_credits, 2),
        'is_reconciled': len(discrepancy_indices) == 0,
        'discrepancies_count': len(discrepancy_indices),
        'account_type': 'Liability (Credit Card)' if is_liability else 'Asset (Checking/Savings)',
        'discrepancy_indices': discrepancy_indices
    }
    
    return df_reconciled, summary
