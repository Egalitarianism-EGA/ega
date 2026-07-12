// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2019 The Bitcoin Core developers
// Copyright (c) 2014-2019 The DigiByte Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef DIGIBYTE_PRIMITIVES_BLOCK_H
#define DIGIBYTE_PRIMITIVES_BLOCK_H

#include <primitives/transaction.h>
#include <serialize.h>
#include <uint256.h>
#include <util.h>

namespace Consensus { struct Params; }

/** EGA MultiShield-4 PoW — see docs/ega/design.md */
enum {
    ALGO_UNKNOWN = -1,
    ALGO_RANDOMX      = 0,   // modern CPU / laptop
    ALGO_VERTHASH     = 1,   // consumer GPU
    ALGO_YESPOWER_EGA = 2,   // phone / Pi / weak CPU
    ALGO_SCRYPT       = 3,   // hard door (ASIC / capital market; MultiShield security anchor)
    NUM_ALGOS_IMPL
};

#define NUM_ALGOS (NUM_ALGOS_IMPL)  // 4 algos (~25% MultiShield share each)

enum {
    BLOCK_VERSION_DEFAULT        = 2,

    // Algo field in nVersion bits 8-11 (DigiByte multi-algo layout)
    BLOCK_VERSION_ALGO           = (15 << 8),
    BLOCK_VERSION_RANDOMX        = (0 << 8),
    BLOCK_VERSION_SCRYPT         = (1 << 8),
    BLOCK_VERSION_VERTHASH       = (2 << 8),
    BLOCK_VERSION_YESPOWER_EGA   = (4 << 8),
};

std::string GetAlgoName(int Algo);

int GetAlgoByName(std::string strAlgo, int fallback);

inline int GetVersionForAlgo(int algo)
{
    switch(algo)
    {
        case ALGO_RANDOMX:
            return BLOCK_VERSION_RANDOMX;
        case ALGO_VERTHASH:
            return BLOCK_VERSION_VERTHASH;
        case ALGO_YESPOWER_EGA:
            return BLOCK_VERSION_YESPOWER_EGA;
        case ALGO_SCRYPT:
            return BLOCK_VERSION_SCRYPT;
        default:
            assert(false);
            return 0;
    }
}

uint32_t OdoKey(const Consensus::Params& params, uint32_t nTime);

class CBlockHeader
{
public:
    // header
    int32_t nVersion;
    uint256 hashPrevBlock;
    uint256 hashMerkleRoot;
    uint32_t nTime;
    uint32_t nBits;
    uint32_t nNonce;

    CBlockHeader()
    {
        SetNull();
    }

    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream& s, Operation ser_action) {
        READWRITE(this->nVersion);
        READWRITE(hashPrevBlock);
        READWRITE(hashMerkleRoot);
        READWRITE(nTime);
        READWRITE(nBits);
        READWRITE(nNonce);
    }

    void SetNull()
    {
        nVersion = 0;
        hashPrevBlock.SetNull();
        hashMerkleRoot.SetNull();
        nTime = 0;
        nBits = 0;
        nNonce = 0;
    }

    bool IsNull() const
    {
        return (nBits == 0);
    }

    inline void SetAlgo(int algo)
    {
        nVersion |= GetVersionForAlgo(algo);
    }

    int GetAlgo() const;

    uint256 GetHash() const;

    uint256 GetPoWAlgoHash(const Consensus::Params& params) const;

    int64_t GetBlockTime() const
    {
        return (int64_t)nTime;
    }
};


class CBlock : public CBlockHeader
{
public:
    // network and disk
    std::vector<CTransactionRef> vtx;

    // memory only
    mutable bool fChecked;

    CBlock()
    {
        SetNull();
    }

    CBlock(const CBlockHeader &header)
    {
        SetNull();
        *(static_cast<CBlockHeader*>(this)) = header;
    }

    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream& s, Operation ser_action) {
        READWRITEAS(CBlockHeader, *this);
        READWRITE(vtx);
    }

    void SetNull()
    {
        CBlockHeader::SetNull();
        vtx.clear();
        fChecked = false;
    }

    CBlockHeader GetBlockHeader() const
    {
        CBlockHeader block;
        block.nVersion       = nVersion;
        block.hashPrevBlock  = hashPrevBlock;
        block.hashMerkleRoot = hashMerkleRoot;
        block.nTime          = nTime;
        block.nBits          = nBits;
        block.nNonce         = nNonce;
        return block;
    }

    std::string ToString(const Consensus::Params& params) const;
};

struct CBlockLocator
{
    std::vector<uint256> vHave;

    CBlockLocator() {}

    explicit CBlockLocator(const std::vector<uint256>& vHaveIn) : vHave(vHaveIn) {}

    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream& s, Operation ser_action) {
        int nVersion = s.GetVersion();
        if (!(s.GetType() & SER_GETHASH))
            READWRITE(nVersion);
        READWRITE(vHave);
    }

    void SetNull()
    {
        vHave.clear();
    }

    bool IsNull() const
    {
        return vHave.empty();
    }
};

#endif // DIGIBYTE_PRIMITIVES_BLOCK_H
