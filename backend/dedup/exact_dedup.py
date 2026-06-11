import hashlib

def exact_deduplicate(dataframe, text_columns=['title', 'body']):
    """
    Remove exact duplicates based on a combined hash of given columns.
    Returns deduplicated DataFrame and mask.
    """
    def compute_hash(row):
        combined = ''.join(str(row[col]) for col in text_columns if row.get(col))
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    dataframe['_hash'] = dataframe.apply(compute_hash, axis=1)
    mask = ~dataframe.duplicated(subset='_hash', keep='first')
    deduped = dataframe[mask].drop(columns=['_hash'])
    return deduped, mask