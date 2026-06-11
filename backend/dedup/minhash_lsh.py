from datasketch import MinHash, MinHashLSH
import numpy as np

def shingle(text, k=5):
    """Convert text into set of k-shingles."""
    if not text:
        return set()
    text = text.lower()
    return set(text[i:i+k] for i in range(len(text)-k+1))

def near_deduplicate(bodies, threshold=0.8, num_perm=128):
    """
    Returns a boolean mask indicating which documents to keep (False for near-duplicates).
    Uses MinHash + LSH.
    """
    if len(bodies) == 0:
        return np.array([], dtype=bool)

    # Create MinHash objects
    minhashes = []
    for body in bodies:
        m = MinHash(num_perm=num_perm)
        for sh in shingle(body):
            m.update(sh.encode('utf8'))
        minhashes.append(m)

    # Build LSH index
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    for idx, m in enumerate(minhashes):
        lsh.insert(idx, m)

    # Mark duplicates: if a document is a duplicate of an earlier one, discard it
    keep = np.ones(len(bodies), dtype=bool)
    seen = set()
    for idx, m in enumerate(minhashes):
        candidates = lsh.query(m)
        # Check if any candidate with smaller index is a true near-duplicate
        for cand in candidates:
            if cand < idx and cand not in seen:
                # Compute actual Jaccard if needed (optional)
                jaccard = minhashes[cand].jaccard(m)
                if jaccard >= threshold:
                    keep[idx] = False
                    break
        if keep[idx]:
            seen.add(idx)
    return keep