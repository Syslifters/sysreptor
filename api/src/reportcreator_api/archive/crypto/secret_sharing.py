from Cryptodome.Protocol.SecretSharing import Shamir


SHAMIR_BLOCK_SIZE = 16


class ShamirLarge(Shamir):
    """
    Shamir's secret sharing scheme with support for secrets larger than 128 bit.
    Code taken from unmerged PR: https://github.com/Legrandin/pycryptodome/pull/593/files
    """

    @staticmethod
    def split_large(k, n, secret, ssss=False):
        """
        Wrapper for Shamir.split()
        when len(key) > SHAMIR_BLOCK_SIZE (16)
        """
        if not isinstance(secret, bytes):
            raise TypeError("Secret must be bytes")
        if len(secret) % SHAMIR_BLOCK_SIZE != 0:
            raise ValueError(f"Secret size must be a multiple of {SHAMIR_BLOCK_SIZE}")

        blocks = len(secret) // SHAMIR_BLOCK_SIZE
        shares = [b'' for _ in range(n)]
        for i in range(blocks):
            block_shares = Shamir.split(k, n,
                    secret[i*SHAMIR_BLOCK_SIZE:(i+1)*SHAMIR_BLOCK_SIZE], ssss)
            for j in range(n):
                shares[j] += block_shares[j][1]
        return [(i+1,shares[i]) for i in range(n)]

    @staticmethod
    def combine_large(shares, ssss=False):
        """
        Wrapper for Shamir.combine()
        when len(key) > SHAMIR_BLOCK_SIZE (16)
        """
        share_len = len(shares[0][1])
        for share in shares:
            if len(share[1]) % SHAMIR_BLOCK_SIZE:
                raise ValueError(f"Share #{share[0]} is not a multiple of {SHAMIR_BLOCK_SIZE}")
            if len(share[1]) != share_len:
                raise ValueError("Share sizes are inconsistent")
        blocks = share_len // SHAMIR_BLOCK_SIZE
        result = b''
        for i in range(blocks):
            block_shares = [
                    (int(idx), share[i*SHAMIR_BLOCK_SIZE:(i+1)*SHAMIR_BLOCK_SIZE]) 
                for idx, share in shares]
            result += Shamir.combine(block_shares, ssss)
        return result
