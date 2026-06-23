import re
import os
import pandas as pd
# pyrefly: ignore [missing-import]
import pdfplumber

def clean_amount(val):
    """
    Cleans a string representation of an amount into a float.
    Handles currency symbols, commas, and negative numbers in parentheses (e.g., (100.00) -> -100.00).
    """
    if val is None or not isinstance(val, str):
        return 0.0
    val = val.strip()
    if not val:
        return 0.0
    
    # Check for negative in parentheses
    is_negative = False
    if val.startswith('(') and val.endswith(')'):
        is_negative = True
        val = val[1:-1]
    elif val.startswith('-'):
        is_negative = True
        val = val[1:]
    
    # Remove currency symbols and commas
    val = re.sub(r'[^\d\.]', '', val)
    
    try:
        amount = float(val)
        return -amount if is_negative else amount
    except ValueError:
        return 0.0

def parse_date(date_str):
    """
    Attempts to normalize different date formats into YYYY-MM-DD.
    Returns an empty string if the string is not a valid date.
    """
    if not date_str:
        return ""
    date_str = date_str.strip()
    
    # Check if the string has any digits. If not, it can't be a date
    if not any(char.isdigit() for char in date_str):
        return ""
        
    # Let's try pandas parsing
    try:
        parsed_dt = pd.to_datetime(date_str, errors='coerce')
        if not pd.isna(parsed_dt):
            # Ensure the year is reasonable (e.g. between 1990 and 2080)
            if 1990 <= parsed_dt.year <= 2080:
                return parsed_dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    
    return ""


def parse_csv_statement(file_path):
    """
    Parses a CSV bank statement. Detects header row, maps columns, and extracts transactions.
def parse_dataframe_statement(df_raw):
    """
    Parses a pandas DataFrame representation of a bank statement (from CSV or Excel).
    Detects header row, maps columns, extracts transactions, and joins wrapped descriptions.
    """
    transactions = []
    header_idx = -1
    col_mapping = {}
    
    # Heuristics for column headers
    header_keywords = {
        'date': ['date', 'trans', 'post', 'value'],
        'description': ['desc', 'detail', 'particular', 'memo', 'transaction', 'payee'],
        'debit': ['debit', 'withdrawal', 'charge', 'amount out', 'payment', 'paid out'],
        'credit': ['credit', 'deposit', 'amount in', 'receipt', 'paid in'],
        'amount': ['amount', 'value'],
        'balance': ['balance', 'bal', 'running']
    }
    
    # Find the header row
    for idx, row in df_raw.iterrows():
        row_str = [str(x).lower() for x in row.values]
        matches = 0
        temp_mapping = {}
        
        for col_name, keywords in header_keywords.items():
            for i, val in enumerate(row_str):
                if any(kw in val for kw in keywords):
                    temp_mapping[col_name] = i
                    matches += 1
                    break
        
        # If we match at least date and description, and (debit or amount or balance), it's likely the header
        if 'date' in temp_mapping and 'description' in temp_mapping and \
           ('debit' in temp_mapping or 'amount' in temp_mapping or 'balance' in temp_mapping):
            header_idx = idx
            col_mapping = temp_mapping
            break
            
    if header_idx == -1:
        # Default fallback mapping if no header is found:
        # Let's guess: col 0 = date, col 1 = desc, col 2 = amount, col 3 = balance
        col_mapping = {'date': 0, 'description': 1, 'amount': 2, 'balance': 3}
        start_row = 0
    else:
        start_row = header_idx + 1

    # Extract transactions
    for idx in range(start_row, len(df_raw)):
        row = df_raw.iloc[idx]
        
        # Check if row is empty
        if row.isna().all():
            continue
            
        # Get raw values
        raw_date = str(row.iloc[col_mapping['date']]) if 'date' in col_mapping and col_mapping['date'] < len(row) else ''
        raw_desc = str(row.iloc[col_mapping['description']]) if 'description' in col_mapping and col_mapping['description'] < len(row) else ''
        
        # Determine Debit / Credit / Amount
        debit = 0.0
        credit = 0.0
        
        if 'debit' in col_mapping and col_mapping['debit'] < len(row):
            debit = clean_amount(str(row.iloc[col_mapping['debit']]))
        if 'credit' in col_mapping and col_mapping['credit'] < len(row):
            credit = clean_amount(str(row.iloc[col_mapping['credit']]))
            
        if 'amount' in col_mapping and col_mapping['amount'] < len(row):
            amt = clean_amount(str(row.iloc[col_mapping['amount']]))
            if 'debit' not in col_mapping and 'credit' not in col_mapping:
                if amt < 0:
                    debit = abs(amt)
                else:
                    credit = amt
        
        balance = 0.0
        if 'balance' in col_mapping and col_mapping['balance'] < len(row):
            balance = clean_amount(str(row.iloc[col_mapping['balance']]))
            
        # Standardize date
        clean_dt = parse_date(raw_date)
        
        # Filter out rows that are summaries or non-transactions (like empty descriptions or dates)
        if not clean_dt or raw_date.lower().strip() in ['date', 'nan', 'null', '']:
            # If description exists, it might be a multi-line description wrap
            if raw_desc and raw_desc.lower() not in ['nan', 'description', ''] and len(transactions) > 0:
                # Skip typical metadata or summary footer lines
                skip_patterns = [
                    r'^page \d+$', r'^statement of account$', r'^balance forward$', 
                    r'^starting balance$', r'^ending balance$', r'^subtotal$',
                    r'^total deposits$', r'^total withdrawals$', r'^totals$', r'^total$'
                ]
                check_date = raw_date.lower().strip()
                check_desc = raw_desc.lower().strip()
                if not any(re.match(pattern, check_date) or re.match(pattern, check_desc) for pattern in skip_patterns):
                    transactions[-1]['description'] += " " + raw_desc.strip()
            continue
            
        transactions.append({
            'date': clean_dt,
            'description': raw_desc.strip() if raw_desc else '',
            'debit': debit,
            'credit': credit,
            'balance': balance,
            'raw_row_idx': idx
        })
        
    return pd.DataFrame(transactions)

def parse_csv_statement(file_path):
    """
    Parses a CSV bank statement. Detects header row, maps columns, and extracts transactions.
    """
    # Load all lines of the CSV
    try:
        df_raw = pd.read_csv(file_path, header=None)
    except Exception as e:
        # Retry with different encodings or separators if needed
        df_raw = pd.read_csv(file_path, header=None, encoding='latin1')
    return parse_dataframe_statement(df_raw)

def parse_excel_statement(file_path):
    """
    Parses an Excel (.xlsx) bank statement.
    """
    try:
        df_raw = pd.read_excel(file_path, header=None)
    except Exception as e:
        raise ValueError(f"Failed parsing Excel statement: {str(e)}")
    return parse_dataframe_statement(df_raw)

def parse_pdf_statement(file_path):
    """
    Parses a PDF bank statement.
    Uses pdfplumber to extract words with horizontal/vertical coordinates,
    clusters them into lines, identifies table headers, aligns columns,
    and merges wrapped description rows.
    """
    transactions = []
    
    header_keywords = {
        'date': ['date', 'trans date', 'post date', 'value date'],
        'description': ['description', 'transaction details', 'activity', 'particulars', 'memo', 'details'],
        'debit': ['debit', 'withdrawal', 'charge', 'amount out', 'payment', 'paid out'],
        'credit': ['credit', 'deposit', 'amount in', 'receipt', 'paid in'],
        'amount': ['amount'],
        'balance': ['balance', 'running balance', 'ledger balance']
    }
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract words with coordinates
            words = page.extract_words()
            if not words:
                continue
                
            # Group words into lines based on vertical tolerance
            # Bounding box coordinates: x0, x1, top, bottom
            lines = []
            current_line = []
            last_top = None
            
            # Sort words by top position first, then x0
            words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
            
            for w in words_sorted:
                if last_top is None:
                    last_top = w['top']
                    current_line.append(w)
                elif abs(w['top'] - last_top) < 3.5:  # Tolerance for words on same line
                    current_line.append(w)
                else:
                    lines.append(current_line)
                    current_line = [w]
                    last_top = w['top']
            if current_line:
                lines.append(current_line)
                
            # Sort words in each line horizontally (by x0)
            for i in range(len(lines)):
                lines[i] = sorted(lines[i], key=lambda w: w['x0'])
                
            # Detect header column ranges
            header_ranges = {}
            header_detected = False
            
            for line_idx, line in enumerate(lines):
                line_str = " ".join([w['text'].lower() for w in line])
                
                # Check if this line looks like a header line
                date_match = any(any(kw in w['text'].lower() for kw in header_keywords['date']) for w in line)
                desc_match = any(any(kw in w['text'].lower() for kw in header_keywords['description']) for w in line)
                amt_match = any(any(kw in w['text'].lower() for kw in header_keywords[k]) for k in ['debit', 'credit', 'amount', 'balance'] for w in line)
                
                if date_match and desc_match and amt_match:
                    # Found a header line!
                    header_detected = True
                    
                    # Compute horizontal bounding box for each column based on word indices matching keywords
                    for col_name, keywords in header_keywords.items():
                        col_words = []
                        for w in line:
                            w_txt = w['text'].lower()
                            if any(kw in w_txt for kw in keywords):
                                col_words.append(w)
                        if col_words:
                            min_x = min(w['x0'] for w in col_words)
                            max_x = max(w['x1'] for w in col_words)
                            header_ranges[col_name] = (min_x, max_x)
                    break
            
            # If no header detected on this page, fall back to heuristics or use the header from previous pages
            # If we don't have header ranges yet, we'll try to find columns by x0 distribution
            if not header_detected and page_num > 0 and header_ranges:
                # Reuse header ranges from previous page
                header_detected = True
            
            # If we still don't have header ranges, try a general layout analysis
            if not header_ranges:
                # We can't align via header coordinates, let's fall back to split spacing or simple token extraction
                # We'll build a default layout estimate based on typical layout
                # Page width is usually around 612 (letter width in points) or 595 (A4)
                w_page = page.width
                header_ranges = {
                    'date': (0, w_page * 0.15),
                    'description': (w_page * 0.15, w_page * 0.55),
                    'debit': (w_page * 0.55, w_page * 0.70),
                    'credit': (w_page * 0.70, w_page * 0.85),
                    'balance': (w_page * 0.85, w_page)
                }

            # Map line items into standard columns based on coordinate ranges
            for line_idx, line in enumerate(lines):
                # Skip header lines
                line_str = " ".join([w['text'].lower() for w in line])
                is_header = any(all(kw in w['text'].lower() for kw in kws) for col, kws in header_keywords.items() for w in line if len(w['text']) > 2)
                
                # Check if it has any date or currency pattern
                has_date = any(re.match(r'^\d{1,2}[/\-]\d{1,2}', w['text']) or re.match(r'^[A-Za-z]{3}\s+\d{1,2}', w['text']) or re.match(r'^\d{4}-\d{2}-\d{2}', w['text']) for w in line)
                has_amount = any(re.search(r'\d+\.\d{2}', w['text']) for w in line)
                
                # Reconstruct columns by sorting words into slots based on horizontal coordinates
                col_contents = {col: [] for col in header_ranges.keys()}
                
                # Sort words in this line into the closest column range
                for w in line:
                    assigned_col = None
                    min_dist = float('inf')
                    
                    # Find which header range the word fits best
                    for col_name, (x0, x1) in header_ranges.items():
                        # Word coordinates
                        wx0, wx1 = w['x0'], w['x1']
                        
                        # Check direct overlap
                        if wx0 >= x0 - 5 and wx1 <= x1 + 5:
                            assigned_col = col_name
                            break
                        # Otherwise calculate distance to column center or bounds
                        col_center = (x0 + x1) / 2
                        w_center = (wx0 + wx1) / 2
                        dist = abs(w_center - col_center)
                        
                        # Distance to column boundaries
                        if wx1 < x0:
                            dist = x0 - wx1
                        elif wx0 > x1:
                            dist = wx0 - x1
                        else:
                            dist = 0
                            
                        if dist < min_dist:
                            min_dist = dist
                            assigned_col = col_name
                    
                    if assigned_col:
                        col_contents[assigned_col].append(w)
                
                # Clean columns text
                date_val = " ".join([w['text'] for w in sorted(col_contents.get('date', []), key=lambda w: w['x0'])])
                desc_val = " ".join([w['text'] for w in sorted(col_contents.get('description', []), key=lambda w: w['x0'])])
                debit_val = " ".join([w['text'] for w in sorted(col_contents.get('debit', []), key=lambda w: w['x0'])])
                credit_val = " ".join([w['text'] for w in sorted(col_contents.get('credit', []), key=lambda w: w['x0'])])
                amount_val = " ".join([w['text'] for w in sorted(col_contents.get('amount', []), key=lambda w: w['x0'])])
                balance_val = " ".join([w['text'] for w in sorted(col_contents.get('balance', []), key=lambda w: w['x0'])])

                # Check if this row is valid
                clean_dt = parse_date(date_val)
                
                # Check for table transaction conditions
                if clean_dt and (debit_val or credit_val or amount_val or balance_val or has_amount):
                    # We have a new transaction row!
                    debit = clean_amount(debit_val)
                    credit = clean_amount(credit_val)
                    
                    if amount_val and debit == 0.0 and credit == 0.0:
                        amt = clean_amount(amount_val)
                        # Decide if positive is credit and negative is debit
                        # Check header label of amount to see if it implies credit/debit
                        # Otherwise if sign is negative, it's debit
                        if amt < 0:
                            debit = abs(amt)
                        else:
                            credit = amt
                            
                    balance = clean_amount(balance_val)
                    
                    transactions.append({
                        'date': clean_dt,
                        'description': desc_val.strip(),
                        'debit': debit,
                        'credit': credit,
                        'balance': balance,
                        'raw_row_idx': len(transactions)
                    })
                else:
                    # No transaction date / amounts found. 
                    # If there's description and we have a preceding transaction, it could be a wrapped description.
                    # Verify it's not a header, page number or summary footer.
                    desc_strip = desc_val.strip()
                    if desc_strip and not clean_dt and len(transactions) > 0:
                        # Skip typical metadata lines
                        skip_patterns = [
                            r'^page \d+$', r'^statement of account$', r'^balance forward$', 
                            r'^starting balance$', r'^ending balance$', r'^subtotal$',
                            r'^total deposits$', r'^total withdrawals$'
                        ]
                        if not any(re.match(pattern, desc_strip.lower()) for pattern in skip_patterns):
                            transactions[-1]['description'] += " " + desc_strip
                            
                            # Also, if this wrapped row contains a balance or amount that belongs to the previous transaction:
                            if balance_val and transactions[-1]['balance'] == 0.0:
                                transactions[-1]['balance'] = clean_amount(balance_val)
                            if debit_val and transactions[-1]['debit'] == 0.0:
                                transactions[-1]['debit'] = clean_amount(debit_val)
                            if credit_val and transactions[-1]['credit'] == 0.0:
                                transactions[-1]['credit'] = clean_amount(credit_val)
                                
    return pd.DataFrame(transactions)

def parse_statement(file_path):
    """
    Main entry point. Detects file format by magic bytes (or extension fallback)
    and routes to the appropriate parser.
    """
    # Read the first 4 bytes for format signature verification
    magic = b""
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(4)
    except Exception:
        pass
        
    if magic.startswith(b"PK\x03\x04"):
        return parse_excel_statement(file_path)
    elif magic.startswith(b"%PDF"):
        return parse_pdf_statement(file_path)
    else:
        # Fallback based on extension or default to CSV
        _, ext = os.path.splitext(file_path.lower())
        if ext == '.pdf':
            return parse_pdf_statement(file_path)
        elif ext == '.xlsx':
            return parse_excel_statement(file_path)
        else:
            # Default fallback: parse as CSV
            return parse_csv_statement(file_path)
